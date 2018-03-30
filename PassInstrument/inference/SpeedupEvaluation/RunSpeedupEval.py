#!/usr/bin/env python3
import os, sys, signal
import multiprocessing
import subprocess as sp
import shutil
import shlex
import psutil
import time
import csv
import json
import pytz
from datetime import datetime

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

def KillPid(pid):
    '''
    kill the pid
    '''
    # This is the main reason why terminal will produce "Killed" msgs.
    os.kill(pid, signal.SIGKILL)

def ExecuteCmd(Cmd=""):
    p = sp.Popen(shlex.split(Cmd),
            stdin=sp.PIPE,
            stdout=sp.PIPE)
    out, err = p.communicate()
    p.wait()
    return p.returncode, out, err

def sigterm_handler(signo, frame):
    #kill all the children of pid and itself
    parent_pid = os.getpid()
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        child.kill()
    # kill itselt and remove pid file.("atexit.register")
    raise SystemExit(1)


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
    ParentPid = os.getpid()
    pid = os.fork()
    #signal.signal(signal.SIGTERM, sigterm_handler)
    if pid == 0:
        retList = Func(args)
        # Kill the timing thread
        KillPid(ParentPid)
    else:
        WaitSecs = 0
        WaitUnit = 1
        while True:
            rid, status = os.waitpid(pid, os.WNOHANG)
            if rid == 0 and status == 0:
                time.sleep(WaitUnit)
                WaitSecs += WaitUnit
            # The time depends on you =)
            if WaitSecs > LimitTime:
                print("Times up, bug!")
                KillProcesses(pid)
                isKilled = True
                retList.append(-1)
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
    cmd = Lit + " -q -j1 " + TestLoc[0]
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
    _, out, err = ExecuteCmd(Cmd=cmd[0])
    if err is None:
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
        """
        try:
        """
        os.chdir(targetRoot)
        # make clean
        os.system("make clean")
        # build
        try:
            cmd = "make -j{}".format(threadNum)
            print('------------------------------------')
            print("build cmd={}".format(cmd))
            isKilled, retList = LimitTimeExec(1500, workerExecCmd, cmd)
            if not isKilled and retList[0] == 0:
                isBuilt = True
            else:
                print("Killed or failed in build: {}".format(cmd))
        except Exception as e:
            print("{} build failed: {}".format(target, e))
        if isBuilt:
            # verify
            try:
                TestLoc = targetRoot + '/' + target + '.test'
                isKilled, retList = LimitTimeExec(300, workerRun, TestLoc)
                if not isKilled and retList[0] == 0:
                    # distribute pyactor
                    distributePyActor(targetRoot + '/' + target + '.test')
                    # run and extract cycles
                    isKilled, retList = LimitTimeExec(500, workerRun, TestLoc)
                    if not isKilled and retList[0] == 0:
                        # get cycles from "RecordTargetFilePath"
                        '''
                        ex.
                        log file format: /tmp/PredictionDaemon/worker-[n]/[BenchmarkName].usage
                        record path example:
                        /tmp/PredictionDaemon/worker-1/bmm.usage
                        e.g.
                        bmm; cpu-cycles | 5668022249; func | matmult | 0.997
                        '''
                        RecordTargetFilePath = '/tmp/PredictionDaemon/worker-' + WorkerID + '/' + target + '.usage'
                        with open(RecordTargetFilePath, 'r') as recFile:
                            info = recFile.read()
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
        """
        except Exception as e:
            print("{} unexpected failed: {}".format(target, e))
        """
    os.chdir(prevCwd)
    return RunCyclesDict

def runEval(TargetRoot, key, jsonPath):
    """
    TargetRoot: the root path in your test-suite/build
    return {"target": {key_1: first_time, key_2: second_time}}
    """
    # get all .test target
    Targets = getTargets(TargetRoot + '/SingleSource/Benchmarks')
    Targets.update(getTargets(TargetRoot + '/MultiSource/Benchmarks'))
    Targets.update(getTargets(TargetRoot + '/MultiSource/Applications'))
    #Targets = {"GlobalDataFlow-dbl":"/home/jrchang/workspace/llvm-thesis-inference/test-suite/build-worker-6/MultiSource/Benchmarks/TSVC/GlobalDataFlow-dbl"}
    # Build, verify and log run time
    WorkerID = TargetRoot[-1]
    retDict = Eval(Targets, 12, WorkerID)
    # record as file for logging
    date = datetime.now(pytz.timezone('Asia/Taipei')).strftime("%m-%d_%H-%M")
    Dir = "log-" + date
    os.makedirs(Dir)
    with open(Dir + '/' + jsonPath, 'w') as fp:
        json.dump(retDict, fp)
    return retDict


def readOriginalResults():
    loc = os.getenv("LLVM_THESIS_RandomHome", "Error")
    loc = loc + "/LLVMTestSuiteScript/GraphGen/output/newMeasurableStdBenchmarkMeanAndSigma"
    Orig_cycles_mean = {}
    Orig_cycles_sigma = {}
    with open(loc, 'r') as File:
        '''
        e.g.
        PAQ8p/paq8p; cpu-cycles-mean | 153224947840; cpu-cycles-sigma | 2111212874
        '''
        for line in File:
            elms = line.split(';')
            target = elms[0].split('/')[-1]
            mean = elms[1].split('|')[1].strip()
            sigma = elms[2].split('|')[1].strip()
            Orig_cycles_mean[target] = int(mean)
            Orig_cycles_sigma[target] = int(sigma)
    return Orig_cycles_mean, Orig_cycles_sigma


if __name__ == '__main__':
    print("Current implementation may not let you terminate this script by ctrl+c")
    print("This is due to the LimitTimeExec(), may be its \"child\" to continue to do the job.")
    print("You may see some output message like \"Killed\", that is normal.")
    print("The message are from the OS because we use signal to kill process.")
    for i in range(1):
        startTime = time.perf_counter()
        '''
        Measure the build time for ABC
        '''
        key_2 = "ABC"
        ABC_results = runEval("/home/jrchang/workspace/llvm-thesis-inference/test-suite/build-worker-6", key_2, "ABC_cycles_mean.json")

        '''
        If you already ran, just read the data.
        '''
        #ABC_results = json.load(open("ABC_cycles_mean.json"))
        # read data from previous results
        # we don't have to read the original data for every time
        '''
        Orig_cycles_mean, Orig_cycles_sigma = readOriginalResults()
        with open("Orig_cycles_mean.json", 'w') as fp:
            json.dump(Orig_cycles_mean, fp)
        with open("Orig_cycles_sigma.json", 'w') as fp:
            json.dump(Orig_cycles_sigma, fp)
        '''

        endTime = time.perf_counter()
        print("The evaluation procedure takse:{} mins".format((endTime - startTime)/60))
