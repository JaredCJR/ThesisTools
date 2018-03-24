#!/usr/bin/env python3
import os, sys
import multiprocessing
import subprocess as sp
import shutil
import shlex
import time
import csv
import json

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

def Eval(TargetDict, threadNum):
    """
    TargetDict = {"target": "target root path"}
    threadNum: make -j[threadNum]
    return BuildTimeDict = {"target": build-time}
    """
    BuildTimeDict = {}
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
                startTime = time.perf_counter()
                p = sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr= sp.PIPE)
                out, err = p.communicate()
                p.wait()
                endTime = time.perf_counter()
                if err.decode('utf-8').strip() is "":
                    isBuilt = True
                    measuredTime = endTime - startTime
            except Exception as e:
                print("{} build failed: {}".format(target, e))
            if isBuilt:
                # verify
                try:
                    cmd = "{} -j{} -q {}.test".format(lit, CpuNum, target)
                    print("verify cmd={}".format(cmd))
                    p = sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr= sp.PIPE)
                    out, err = p.communicate()
                    p.wait()
                    if out.decode('utf-8').strip() is "" and err.decode('utf-8').strip() is "":
                        print("Verify successfully.")
                        print('------------------------------------')
                        print("{} use {} secs".format(target, measuredTime))
                        BuildTimeDict[target] = measuredTime
                    else:
                        BuildTimeDict[target] = 'Failed'
                except Exception as e:
                    print("{} verified failed: {}".format(target, e))
        except Exception as e:
            print("{} unexpected failed: {}".format(target, e))
    os.chdir(prevCwd)
    return BuildTimeDict

def runEval(TargetRoot, key_1, key_2, jsonPath):
    """
    TargetRoot: the root path in your test-suite/build
    return {"target": {key_1: first_time, key_2: second_time}}
    """
    # get all .test target in MultiSource/Application
    Targets = getMultiAppsTargets(TargetRoot)
    # Build, verify and log time
    # 1 thread
    BuildTimeDict_1 = Eval(Targets, 1)
    with open(key_1 + ".json", 'w') as js:
        json.dump(BuildTimeDict_1, js)
    # 12 thread
    BuildTimeDict_12 = Eval(Targets, 12) 
    with open(key_2 + ".json", 'w') as js:
        json.dump(BuildTimeDict_12, js)
    # combine the results
    retDict = {}
    for target, _time in BuildTimeDict_1.items():
        retDict[target] = {}
        retDict[target][key_1] = _time

    for target, _time in BuildTimeDict_12.items():
        if retDict.get(target) is None:
            retDict[target] = {}
        retDict[target][key_2] = _time
    with open(jsonPath, 'w') as js:
        json.dump(retDict, js)
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
    for i in range(10):
        startTime = time.perf_counter()
        '''
        Measure the build time for original clang
        '''
        key_1 = "Original-1-thread"
        key_2 = "Original-12-threads"
        Orig_results = runEval("/home/jrchang/workspace/llvm-official/test-suite/build/MultiSource/Applications", key_1, key_2, "Original.json")
        '''
        Measure the build time for ABC
        '''
        key_3 = "ABC-1-thread"
        key_4 = "ABC-12-threads"
        ABC_results = runEval("/home/jrchang/workspace/llvm-thesis-inference/test-suite/build-worker-6/MultiSource/Applications", key_3, key_4, "ABC.json")

        '''
        If you already ran, just read the data.
        '''
        #Orig_results = json.load(open("Original.json"))
        #ABC_results = json.load(open("ABC.json"))

        # Merge all results into csv-format file
        WriteToCsv("./data/buildEval_" + str(i) + ".csv", Orig_results, ABC_results, [key_1, key_2], [key_3, key_4])
        endTime = time.perf_counter()
        print("The evaluation procedure takse:{} mins".format((endTime - startTime)/60))
