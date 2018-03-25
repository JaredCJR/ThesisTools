#!/usr/bin/env python3
import os, sys
import multiprocessing
import subprocess as sp
import shutil
import shlex
import psutil
import time
import csv
import json

sys.path.append('/home/jrchang/workspace/gym-OptClang/gym_OptClang/envs/')
import RemoteWorker as rwork

def getTargets(path):
    """
    path: the root path for "test-suite" to search ".test" file
    """
    prog = rwork.Programs()
    AllTargetsDict = prog.getAvailablePrograms()
    ListOfAvailableTarget = list(AllTargetsDict.keys())
    # search all test target in Apps
    AppTargets = {}
    test_pattern = '.test'
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(test_pattern):
                # remove .test in the file name
                file = file[:-5]
                # filter out those are not in our consideration.
                if file in ListOfAvailableTarget:
                    AppTargets[file] = root
    return AppTargets

def distributePyActor(TestFilePath):
    # Does this benchmark need stdin?
    NeedStdin = False
    with open(TestFilePath, "r") as TestFile:
        for line in TestFile:
            if line.startswith("RUN:"):
                if line.find("<") != -1:
                    NeedStdin = True
                break
        TestFile.close()
    # Rename elf and copy actor
    ElfPath = TestFilePath.replace(".test", '')
    NewElfPath = ElfPath + ".OriElf"
    #based on "stdin" for to copy the right ones
    InstrumentSrc = os.getenv("LLVM_THESIS_InstrumentHome", "Error")
    if NeedStdin == True:
        PyCallerLoc = InstrumentSrc + '/PyActor/WithStdin/PyCaller'
        PyActorLoc = InstrumentSrc + '/PyActor/WithStdin/MimicAndFeatureExtractor.py'
    else:
        PyCallerLoc = InstrumentSrc + '/PyActor/WithoutStdin/PyCaller'
        PyActorLoc = InstrumentSrc + '/PyActor/WithoutStdin/MimicAndFeatureExtractor.py'
    # Rename the real elf
    shutil.move(ElfPath, NewElfPath)
    # Copy the feature-extractor
    shutil.copy2(PyActorLoc, ElfPath + ".py")
    # Copy the PyCaller
    if os.path.exists(PyCallerLoc) == True:
        shutil.copy2(PyCallerLoc, ElfPath)
    else:
        print("Please \"$ make\" to get PyCaller in {}\n".format(PyCallerLoc))
        return

def KillProcesses(pid):
    '''
    kill all the children of pid and itself
    '''
    parent_pid = pid
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()

def ExecuteCmd(Cmd=""):
    p = sp.Popen(shlex.split(Cmd),
            stdin=sp.PIPE,
            stdout=sp.PIPE)
    out, err = p.communicate()
    p.wait()
    return p.returncode, out, err

def LimitTimeExec(LimitTime, Func, *args):
    """
    Input:
    1. LimitTime: is in the unit of secs.
    2. Func: must return a list that contains your return value
    3. args: pass into Func
    Return value:
    1. isKilled: killed by timing
    2. retList: from Func(args)
    """
    retList = []
    PrevWd = os.getcwd()
    isKilled = False
    pid = os.fork()
    if pid == 0:
        retList = Func(args)
    else:
        WaitSecs = 0
        WaitUnit = 1
        while True:
            rid, status = os.waitpid(pid, os.WNOHANG)
            if rid == 0 and status == 0:
                time.sleep(WaitUnit)
                WaitSecs += WaitUnit
            else:
                break
            # The time depends on you =)
            if WaitSecs > LimitTime:
                KillProcesses(pid)
                isKilled = True
    os.chdir(PrevWd)
    return isKilled, retList

def workerRun(TestLoc):
    """
    Input: TestLoc
    Return a list:
    [0]: a number that indicate status.
            0      --> build success
            others --> build failed
    """
    retList = []
    Lit = os.getenv("LLVM_THESIS_lit", "Error")
    if Lit == "Error":
        print("$LLVM_THESIS_lit not defined.", file=sys.stderr)
        sys.exit(1)
    CpuNum = str(multiprocessing.cpu_count())
    cmd = Lit + " -q -j" + CpuNum + ' ' + TestLoc
    _, out, err = ExecuteCmd(Cmd=cmd)
    if out:
        retList.append(-1)
    else:
        retList.append(0)
    return retList

def workerExecCmd(cmd):
    """
    Input: Cmd
    Return a list:
    [0]: a number that indicate status.
            0      --> build success
            others --> build failed
    """
    retList = []
    _, out, err = ExecuteCmd(Cmd=cmd)

    if err.decode('utf-8').strip() is "":
        retList.append(0)
    else:
        retList.append(-1)
        print(err)
    return retList

def Eval(TargetDict, threadNum, WorkerID):
    """
    TargetDict = {"target": "target root path"}
    threadNum: make -j[threadNum]
    return BuildTimeDict = {"target": run-time}
    """
    RunCyclesDict = {}
    prevCwd = os.getcwd()
    lit = os.getenv('LLVM_THESIS_lit', "Error")
    CpuNum = multiprocessing.cpu_count()
    for target, targetRoot in TargetDict.items():
        isBuilt = False
        measuredTime = 0
        try:
            os.chdir(targetRoot)
            # make clean
            os.system("make clean")
            # build
            try:
                cmd = "taskset -c 0-{} make -j{}".format(threadNum-1, threadNum)
                print('------------------------------------')
                print("build cmd={}".format(cmd))
                #startTime = time.perf_counter()
                isKilled, retList = LimitTimeExec(900, workerExecCmd, cmd)
                #endTime = time.perf_counter()
                if not isKilled and retList[0] == 0:
                    isBuilt = True
                    #measuredTime = endTime - startTime
            except Exception as e:
                print("{} build failed: {}".format(target, e))
            if isBuilt:
                # verify
                try:
                    isKilled, retList = LimitTimeExec(300, workerRun, TestLoc)
                    if not isKilled and retList[0] == 0:
                        # distribute pyactor
                        distributePyActor(targetRoot + '/' + target + '.test')
                        # run and extract cycles
                        isKilled, retList = LimitTimeExec(500, workerRun, TestLoc)
                        if not isKilled and retList[0] == 0::
                            # get cycles from "RecordTargetFilePath"
                            '''
                            ex.
                            log file format: /tmp/PredictionDaemon/worker-[n]/[BenchmarkName]
                            record path example:
                            /tmp/PredictionDaemon/worker-1/bmm.usage
                            e.g.
                            bmm; cpu-cycles | 5668022249; func | matmult | 0.997
                            '''
                            loc = '/tmp/PredictionDaemon/worker-' + WorkerID + '/' + target
                            with open(RecordTargetFilePath, 'r') as file:
                                info = file.read()
                            TotalCycles = info.split(';')[1].split('|')[1].strip()
                            RunCyclesDict[target] = int(TotalCycles)
                            print("Target={}, takes {} cycles".format(target, TotalCycles))
                        else:
                            print("Run too long, killed")
                            RunCyclesDict[target] = -1
                    else:
                        print("Verify failed.")
                        RunCyclesDict[target] = -1
                except Exception as e:
                    print("{} verified failed: {}".format(target, e))
        except Exception as e:
            print("{} unexpected failed: {}".format(target, e))
    os.chdir(prevCwd)
    return RunCyclesDict

def runEval(TargetRoot, key, jsonPath):
    """
    TargetRoot: the root path in your test-suite/build
    return {"target": {key_1: first_time, key_2: second_time}}
    """
    # get all .test target
    Targets = getTargets(TargetRoot + 'SingleSource/Benchmarks')
    Targets.update(getTargets(TargetRoot + 'MultiSource/Benchmarks'))
    Targets.update(getTargets(TargetRoot + 'MultiSource/Applications'))
    # Build, verify and log run time
    WorkerID = TargetRoot[-1]
    retDict = Eval(Targets, 12, WorkerID)
    # record as file for debugging
    with open(jsonPath, 'w') as fp:
        json.dump(retDict, fp)
    return retDict

def WriteToCsv(writePath, Dict1, Dict2, keys_1, keys_2):
    """
    Dict1 must contains all the "keys"
    """
    ResultDict = dict.fromkeys(list(Dict1.keys()), {})
    # write csv header
    fieldnames = ['target', keys_1[0], keys_2[0], keys_1[1], keys_2[1]]
    with open(writePath, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
    for key, _time in Dict1.items():
        if Dict1.get(key) is not None:
            if Dict1[key].get(keys_1[0]) is not None:
                ResultDict[key][keys_1[0]] = Dict1[key][keys_1[0]]
            else:
                print("target: {} missing {}".format(key, keys_1[0]))
                ResultDict[key][keys_1[0]] = -1

            if Dict1[key].get(keys_1[1]) is not None:
                ResultDict[key][keys_1[1]] = Dict1[key][keys_1[1]]
            else:
                print("target: {} missing {}".format(key, keys_1[1]))
                ResultDict[key][keys_1[1]] = -1
        else:
            print("target: {} missing {} and {}".format(key, keys_1[0],keys_1[1]))
            ResultDict[key][keys_1[0]] = -1
            ResultDict[key][keys_1[1]] = -1

        if Dict2.get(key) is not None:
            if Dict2[key].get(keys_2[0]) is not None:
                ResultDict[key][keys_2[0]] = Dict2[key][keys_2[0]]
            else:
                print("target: {} missing {}".format(key, keys_2[0]))
                ResultDict[key][keys_2[0]] = -1

            if Dict2[key].get(keys_2[1]) is not None:
                ResultDict[key][keys_2[1]] = Dict2[key][keys_2[1]]
            else:
                print("target: {} missing {}".format(key, keys_2[1]))
                ResultDict[key][keys_2[1]] = -1
        else:
            print("target: {} missing {} and {}".format(key, keys_2[0],keys_2[1]))
            ResultDict[key][keys_2[0]] = -1
            ResultDict[key][keys_2[1]] = -1
        # write ResultDict to csv
        with open(writePath, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            tmp = ResultDict[key]
            tmp['target'] = key
            writer.writerow(tmp)



if __name__ == '__main__':
    for i in range(2):
        startTime = time.perf_counter()
        '''
        Measure the build time for original clang
        '''
        key_1 = "Original"
        # build-worker-0 for designition compatiable in InstrumentServiceLib.py
        # must end with [WorkerID], not "/"
        Orig_results = runEval("/home/jrchang/workspace/llvm-official/test-suite/build-worker-0", key_1, "Original.json")
        '''
        Measure the build time for ABC
        '''
        key_2 = "ABC"
        ABC_results = runEval("/home/jrchang/workspace/llvm-thesis-inference/test-suite/build-worker-6", key_2, "ABC.json")

        '''
        If you already ran, just read the data.
        '''
        #Orig_results = json.load(open("Original.json"))
        #ABC_results = json.load(open("ABC.json"))

        # Merge all results into csv-format file
        #WriteToCsv("./data/runEval_" + str(i) + ".csv", Orig_results, ABC_results, [key_1, key_2], [key_3, key_4])
        endTime = time.perf_counter()
        print("The evaluation procedure takse:{} mins".format((endTime - startTime)/60))
