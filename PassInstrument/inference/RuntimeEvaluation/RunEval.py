#!/usr/bin/env python3
import os, sys
import multiprocessing
import subprocess as sp
import shutil
import shlex
import time
import csv

sys.path.append('/home/jrchang/workspace/gym-OptClang/gym_OptClang/envs/')
import RemoteWorker as rwork

def getMultiAppsTargets(path):
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

def Eval(TargetDict, BuildTimeDict, threadNum):
    """
    TargetDict = {"target": "target root path"}
    BuildTimeDict = {"target": build-time} # this is used as inplace
    threadNum: make -j[threadNum]
    """
    prevCwd = os.getcwd()
    lit = os.getenv('LLVM_THESIS_lit', "Error")
    CpuNum = multiprocessing.cpu_count()
    for target, targetRoot in TargetDict.items():
        isCorrect = False
        try:
            os.chdir(targetRoot)
            # make clean
            os.system("make clean")
            # build
            startTime = time.perf_counter()
            os.system("taskset -c 0-{} make -j{}".format(threadNum-1, threadNum))
            endTime = time.perf_counter()
            measuredTime = endTime - startTime
            # verify
            try:
                cmd = "{} -j{} -q {}".format(lit, CpuNum, target)
                p = sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr= sp.PIPE)
                out, err = p.communicate()
                p.wait()
                if out is None and err is None:
                    isCorrect = True
            except Exception as e:
                print("{} verified failed: {}".format(target, e))
        except Exception as e:
            print("{} build failed: {}".format(target, e))
        if isCorrect:
            BuildTimeDict[target] = measuredTime        
    os.chdir(prevCwd)

def runEval(TargetRoot, key_1, key_2):
    """
    TargetRoot: the root path in your test-suite/build
    return {"target": {key_1: first_time, key_2: second_time}}
    """
    # get all .test target in MultiSource/Application
    Targets = getMultiAppsTargets(TargetRoot)
    # Build, verify and log time
    # 1 thread
    BuildTimeDict_1 = {}
    Eval(Targets, BuildTimeDict_1, 1)
    #print(BuildTimeDict_1)
    # 6 thread
    BuildTimeDict_6 = {}
    Eval(Targets, BuildTimeDict_6, 6) 
    #print(BuildTimeDict_6)
    # combine the results
    retDict = {}
    for target, _time in BuildTimeDict_1.items():
        retDict[target] = {}
        retDict[target][key_1] = _time

    for target, _time in BuildTimeDict_6.items():
        if retDict.get(target) is None:
            retDict[target] = {}
        retDict[target][key_2] = _time
    return retDict

def WriteToCsv(writePath, Dict1, Dict2, keys_1, keys_2):
    """
    Dict1 must contains all the "keys"
    """
    ResultDict = dict.fromkeys(list(Dict1.keys()), {})
    for key, _time in Dict1.items():
        ResultDict[key][keys_1[0]] = Dict1[keys_1[0]]
        ResultDict[key][keys_1[1]] = Dict1[keys_1[1]]
        ResultDict[key][keys_2[0]] = Dict1[keys_2[0]]
        ResultDict[key][keys_2[1]] = Dict1[keys_2[1]]
    # write ResultDict to csv
    with open(writePath, 'w') as csv_file:
        fieldnames = ['target', keys_1[0], keys_2[0], keys_1[1], keys_2[1]]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for target, times in ResultDict.items():
            times['target'] = target
            writer.writerow(times)
            print(times)



if __name__ == '__main__':
    startTime = time.perf_counter()
    '''
    Measure the build time for original clang
    '''
    key_1 = "Original-1-thread"
    key_2 = "Original-6-threads"
    Orig_results = runEval("/home/jrchang/workspace/llvm-official/test-suite/build/MultiSource/Applications", key_1, key_2)
    '''
    Measure the build time for ABC
    '''
    key_3 = "ABC-1-thread"
    key_4 = "ABC-6-threads"
    ABC_results = runEval("/home/jrchang/workspace/llvm-thesis-inference/test-suite/build-worker-6/MultiSource/Applications", key_3, key_4)
    # Merge all result into csv-format file
    WriteToCsv("./build.csv", Orig_results, ABC_results, [key_1, key_2], [key_3, key_4])
    endTime = time.perf_counter()
    print("The evaluation procedure takse:{} mins".format((endTime - startTime)/60))
