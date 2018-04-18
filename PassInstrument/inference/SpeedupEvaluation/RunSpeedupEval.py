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
import Lib as lib

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



def Eval(TargetDict, threadNum, WorkerID):
    """
    TargetDict = {"target": "target root path"}
    threadNum: make -j[threadNum]
    return BuildTimeDict = {"target": run-time}
    """
    RunCyclesDict = {}
    prevCwd = os.getcwd()
    for target, targetRoot in TargetDict.items():
        isBuilt = False
        retStatus = lib.EnvResponseActor.EnvEcho(target, WorkerID, TargetDict)
        if retStatus == "Success":
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
            RunCyclesDict[target] = -1
    os.chdir(prevCwd)
    return RunCyclesDict

def runEval(TargetRoot, key, jsonPath):
    """
    TargetRoot: the root path in your test-suite/build
    return {"target": {key_1: first_time, key_2: second_time}}
    """
    '''
    # get all .test target
    Targets = getTargets(TargetRoot + '/SingleSource/Benchmarks')
    Targets.update(getTargets(TargetRoot + '/MultiSource/Benchmarks'))
    Targets.update(getTargets(TargetRoot + '/MultiSource/Applications'))
    #Targets = {"GlobalDataFlow-dbl":"/home/jrchang/workspace/llvm-thesis-inference/test-suite/build-worker-6/MultiSource/Benchmarks/TSVC/GlobalDataFlow-dbl"}
    '''
    # Build, verify and log run time
    builder = lib.EnvBuilder()
    LitTestDict = builder.CheckTestSuiteCmake(WorkerID)
    WorkerID = TargetRoot[-1]
    retDict = Eval(LitTestDict, 12, WorkerID)
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
    print("-------------------------------------------")
    print("Make sure your $$LLVM_THESIS_HOME point to the inference one.")
    print("-------------------------------------------")
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
