#!/usr/bin/env python3
"""
This script split the available targets into training and validation set randomly.
"""

import Lib as lib
import random
import json

if __name__ == '__main__':
    WorkerID = "6"
    print("Change WorkerID to get the corresponding programs")
    print("Current WorkerID={}".format(WorkerID))
    builder = lib.EnvBuilder()
    LitTestDict = builder.CheckTestSuiteCmake(WorkerID)
    AllTargets = list(LitTestDict.keys())
    randomValidSet = random.sample(AllTargets, int(0.25 * len(AllTargets)))
    randomTrainSet = []
    for target in AllTargets:
        if target not in randomValidSet:
            randomTrainSet.append(target)
    '''
    write validation set to file
    '''
    with open("validationTargets.json", 'w') as outfile:
        json.dump(randomValidSet, outfile)
    '''
    write training set to file
    '''
    with open("trainingTargets.json", 'w') as outfile:
        json.dump(randomTrainSet, outfile)
    print("Done.")
