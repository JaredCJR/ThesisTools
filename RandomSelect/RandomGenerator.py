#!/usr/bin/python3
from random import SystemRandom
import os
import random

class Candidate:
    def generator(self):
        return list(range(1, 34+1))

class RandomPick:
    def run(self, list, mean):
        res_list = []
        res_list.append(list[0])
        for num in list[1:]:
            if random.uniform(0, 1) < float(mean):
                res_list.append(num)
        return res_list

class Driver:
    InputSetLoc = None
    def __init__(self):
        self.InputSetLoc = os.getenv('LLVM_THESIS_RandomHome', '/tmp')
        self.InputSetLoc += '/InputSet' #relative path
    def run(self, mean):
        cand = Candidate()
        #l is the ordered candidates
        l = cand.generator() 
        cryptorand = SystemRandom()
        #shuffle it to create randomness
        cryptorand.shuffle(l)
        rand = RandomPick() 
        #pick at least one as candidate
        target_list = rand.run(l, mean)
        #shuffle to keep first does not always the same
        cryptorand.shuffle(target_list)
        """
        print(target_list)
        """

        #open file with buffering, text is not able to get rid of buffering
        file_loc = self.InputSetLoc
        RetList = ""
        target_file = open(file_loc, "w")
        for ps in target_list:
            target_file.write("%s " % ps)
            RetList += str(ps) + " "
        target_file.write("\n")
        target_file.close()
        """
        target_file = open(file_loc, "r")
        print(target_file.read())
        target_file.close()
        """
        return RetList


class FunctionLevelPredictor:
    def RandomPassSet():
        return "5 9 4 8 7"


if __name__ == '__main__':
    drv = Driver()
    mean = 0.05
    drv.run(mean)
