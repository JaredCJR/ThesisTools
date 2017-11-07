#!/usr/bin/python3
import inspect
import os
import sys
import shlex
import subprocess as sp
import time
from time import gmtime, strftime
import ServiceLib as sv


class Logger(sv.LogService):
    #Should never print to stdout, "lit" will get unexpected output
    def out(self, msg):
        pass

class Executer:
    Args = None
    Stdin = None
    def __init__(self, args, stdin):
        self.Args = args
        self.Stdin = stdin

    def run(self):
        Log = Logger()
        elfPath = inspect.getfile(inspect.currentframe())
        #Remove the postfix ".py"
        elfPath = elfPath[:-3]
        RealElfPath = elfPath + ".OriElf"
        Cmd = RealElfPath + " " + self.Args
        TimeList = []
        Repeat = 5
        try:
            for i in range(Repeat):
                err = None
                DropLoc = os.getenv('LLVM_THESIS_RandomHome')
                os.system(DropLoc + "/LLVMTestSuiteScript/DropCache/drop")
                StartTime = time.perf_counter()
                p = sp.Popen(shlex.split(Cmd), stdout = sp.PIPE, stderr = sp.PIPE, stdin = sp.PIPE)
                out, err = p.communicate(input=self.Stdin)
                p.wait()
                EndTime = time.perf_counter()
                TimeList.append(EndTime - StartTime)
        except Exception as ex:
            if err is not None:
                Log.err(err.decode('utf-8'))
            else:
                Log.err("Why exception happend, and err is None?\n")
                Log.err(str(ex) + "\n")
            return

        TimeList.sort()

        #Output for "lit"
        p = sp.Popen(shlex.split(Cmd), stdin = sp.PIPE)
        p.communicate(input=self.Stdin)
        ReturnCode = p.wait()
        with open("./ReturnValue", "w") as file:
            file.write(str(ReturnCode))
            file.close()

        ss = sv.PassSetService()
        RandomSet = ss.ReadCorrespondingSet(elfPath)

        BenchmarkName = sv.BenchmarkNameService()
        BenchmarkName = BenchmarkName.GetFormalName(elfPath)
        LogTime = TimeList[len(TimeList)//2]
        log_msg = BenchmarkName + ", " + RandomSet + ", " + str(LogTime) + "\n"
        Log.record(log_msg)


if __name__ == '__main__':
    #binary stdin
    stdin = sys.stdin.buffer.read()
    exec = Executer(' '.join(str(arg) for arg in sys.argv[1:]), stdin)
    exec.run()
