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
    def __init__(self, args):
        self.Args = args

    def run(self):
        Log = Logger()
        elfPath = inspect.getfile(inspect.currentframe())
        #Remove the postfix ".py"
        elfPath = elfPath[:-3]
        RealElfPath = elfPath + ".OriElf"
        Cmd = RealElfPath + " " + self.Args
        TotalTime = 0.0
        #Make sure every benchmark execute at least "ThresholdTime"
        ThresholdTime = 5.0
        Repeat = 0.0
        try:
            while True:
                err = None
                DropLoc = os.getenv('LLVM_THESIS_RandomHome')
                os.system(DropLoc + "/LLVMTestSuiteScript/DropCache/drop")
                StartTime = time.perf_counter()
                p = sp.Popen(shlex.split(Cmd), stdout = sp.PIPE, stderr= sp.PIPE)
                out, err = p.communicate()
                p.wait()
                EndTime = time.perf_counter()
                ElapsedTime = EndTime - StartTime
                TotalTime += ElapsedTime
                Repeat += 1.0
                if TotalTime > ThresholdTime:
                    break
        except Exception as ex:
            if err is not None:
                Log.err(err.decode('utf-8'))
            else:
                Log.err("Why exception happend, and err is None?\n")
                Log.err(str(ex) + "\n")
            return

        TimeList.sort()

        #Output for "lit"
        p = sp.Popen(shlex.split(Cmd))
        ReturnCode = p.wait()
        with open("./ReturnValue", "w") as file:
            file.write(str(ReturnCode))
            file.close()
        if ReturnCode < 0:
            Log.err("cmd: {}\n is killed by signal, ret={}\n".format(Cmd, ReturnCode))
            sys.exit()

        ss = sv.PassSetService()
        RandomSet = ss.ReadCorrespondingSet(elfPath)

        BenchmarkName = sv.BenchmarkNameService()
        BenchmarkName = BenchmarkName.GetFormalName(elfPath)
        LogTime = TotalTime / Repeat
        log_msg = BenchmarkName + ", " + RandomSet + ", " + str(LogTime) + "\n"
        Log.record(log_msg)


if __name__ == '__main__':
    exec = Executer(' '.join(str(arg) for arg in sys.argv[1:]))
    exec.run()
