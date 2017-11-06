#!/usr/bin/python3
"""
This file will replace the real elf with PyActor to extract features
"""
import os
import shutil
import shlex
import subprocess as sp
import LitDriver as drv
import ServiceLib as sv

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

#Singleton
class TargetBenchmarks(metaclass=Singleton):
    LLVMTestSuiteBuildPath = None
    TargetPathList = []
    SkipDirList = []

    def init(self):
        #The last character in BuiltPath must be '/'
        self.LLVMTestSuiteBuildPath = os.getenv('LLVM_THESIS_TestSuite', "Error")
        if self.LLVMTestSuiteBuildPath == "Error":
            Log = sv.LogService()
            Log.err("Please setup related environment variable.\n")
            return -1
        #Target dir lists, format: ["First level dir in BuiltPath", ["List of second level dir"]]
        SingleSource = ["SingleSource", ["Benchmarks", ]]
        MultiSource = ["MultiSource", ["Applications", "Benchmarks", ]]
        #Add all source together
        TargetDirLists = [SingleSource, MultiSource, ]
        TargetPathList = []
        for Dir in TargetDirLists:
            for SubDir in Dir[1]:
                path = self.LLVMTestSuiteBuildPath + "/" + Dir[0] + "/" + SubDir + "/"
                TargetPathList.append(path)
        self.TargetPathList = TargetPathList
        #Currently, the PyActor cannot handle it, and skip it.
        self.SkipDirList = ["MultiSource/Applications/ALAC/decode",
                   "MultiSource/Applications/ALAC/encode",
                   "MultiSource/Benchmarks/mafft",
                      ]
        return 0

    def __init__(self):
        ret = self.init()
        if ret == -1:
            sys.exit(-1)


class LitMimic:
    #Make sure that the elf already exists
    PyActorLoc_withStdin = "./PyActor/WithStdin/MimicAndFeatureExtractor.py"
    PyActorLoc_withoutStdin = "./PyActor/WithoutStdin/MimicAndFeatureExtractor.py"
    PyCallerLoc_withStdin = "./PyActor/WithStdin/PyCaller"
    PyCallerLoc_withoutStdin = "./PyActor/WithoutStdin/PyCaller"

    def run(self):
        target = TargetBenchmarks()
        Log = sv.LogService()
        SuccessBuiltPath = []
        for RootPath in target.TargetPathList:
            #Run lit in parallel in order to log the built sanity.
            LitExec = drv.LitRunner()
            CoreNum = str(multiprocessing.cpu_count())
            LitExec.ExecCmd("lit -q -j" + CoreNum + " " + RootPath, ShellMode=False, NeedPrintStderr=True, SanityLog=True)
            for root, dirs, files in os.walk(RootPath):
                for file in files:
                    test_pattern = '.test'
                    if file.endswith(test_pattern):
                        #Skip this dir?
                        SkipFlag = False
                        for skip in target.SkipDirList:
                            if root.endswith(skip):
                                Log.out("Skip dir={}\n".format(skip))
                                SkipFlag = True
                                break
                        if SkipFlag:
                            continue
                        #Does this benchmark need stdin?
                        NeedStdin = False
                        TestFilePath = os.path.join(os.path.abspath(root), file)
                        with open(TestFilePath, "r") as TestFile:
                            for line in TestFile:
                                if line.startswith("RUN:"):
                                    if line.find(" < ") != -1:
                                        NeedStdin = True
                        #Do what we want: rename elf and copy actor
                        ElfName = file.replace(test_pattern, '')
                        ElfPath = os.path.join(root, ElfName)
                        NewElfName = ElfName + ".OriElf"
                        NewElfPath = os.path.join(root, NewElfName)
                        #based on "stdin" for to copy the right ones
                        if NeedStdin == True:
                            PyCallerLoc = self.PyCallerLoc_withStdin
                            PyActorLoc = self.PyActorLoc_withStdin
                        else:
                            PyCallerLoc = self.PyCallerLoc_withoutStdin
                            PyActorLoc = self.PyActorLoc_withoutStdin
                        #if build success, copy it
                        if os.path.exists(ElfPath) == True:
                            #rename the real elf
                            shutil.move(ElfPath, NewElfPath)
                            #copy the feature-extractor
                            shutil.copy2(PyActorLoc, ElfPath + ".py")
                            #copy the PyCaller
                            if os.path.exists(PyCallerLoc) == True:
                                shutil.copy2(PyCallerLoc, ElfPath)
                                if root not in SuccessBuiltPath:
                                    SuccessBuiltPath.append(root)
                            else:
                                Log.err("Please \"$ make\" to get PyCaller in {}\n".format(PyCallerLoc))
                                return
                        else:
                            Log.err("This elf={} filed to build?\n".format(ElfPath))

        return SuccessBuiltPath




if __name__ == '__main__':
    actor = LitMimic()
    actor.run()


