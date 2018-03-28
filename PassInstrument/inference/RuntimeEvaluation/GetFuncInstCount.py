#!/usr/bin/env python3
"""
** Written in 2018/3/28
I have collect the raw data in data/InstCount
The file end with "-InstCount" are the raw data, and 
the name before "-InstCount" are the name of directories 
in "test-suite/MultiSource/Applications"
Normally, you don't have to do this by yourself.
The processed data is stored as "CountStat.csv".
You should directly use it.

** Written in 2018/3/27
This script can gather the number of IR and the number of function in a programs.
However, you have to produce the raw data by yourself.

You must produce the analysis info by youself

e.g. (This may cause race condition, only accept $ make -j1)
Modify llvm/tools/clang/lit/CodeGen/BackendUtil.cpp by inserting
  std::error_code EC;
  llvm::raw_fd_ostream json("./InstCount", EC, sys::fs::F_Append);
  PrintStatisticsJSON(json);
  json.close();
"""

import json, os ,sys, csv

if __name__ == '__main__':
    infoFile = "/home/jrchang/workspace/llvm-official-test/test-suite/build/MultiSource/Applications/InstCountFiles"
    AllResultDict = {}
    with open(infoFile, 'r') as File:
        for line in File:
            '''
            Currently, my file contains something like:
            /home/jrchang/workspace/llvm-official-test/test-suite/build/MultiSource/Applications/sqlite3/InstCount
            ...

            search .test file in the same dir as the file "InstCount"
            '''
            Dir = os.path.dirname(os.path.realpath(line.strip()))
            for root, dirs, files in os.walk(Dir):
                for file in files:
                    if file.endswith(".test"):
                        target = file[:-5]
            AllResultDict[target] = {}
            with open(line.strip(), 'r') as MultiJsonFile:
                AllResultDict[target]['InstructionCount'] = 0
                AllResultDict[target]['FunctionCount'] = 0
                for jsonLine in MultiJsonFile:
                    StrippedLine = jsonLine.strip()
                    if StrippedLine.startswith("\"instcount.TotalInsts\":"):
                        instCount = int(StrippedLine.split(':')[1].strip().split(',')[0])
                        AllResultDict[target]['InstructionCount'] += instCount
                    elif StrippedLine.startswith("\"instcount.TotalFuncs\":"):
                        funcCount = int(StrippedLine.split(':')[1].strip().split(',')[0])
                        AllResultDict[target]['FunctionCount'] += funcCount

    fieldnames = ['target', 'InstructionCount', 'FunctionCount']
    writePath = "CountStat.csv"
    with open(writePath, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
    for target, counts in AllResultDict.items():
        with open(writePath, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            tmp = counts
            tmp['target'] = target
            writer.writerow(tmp)

