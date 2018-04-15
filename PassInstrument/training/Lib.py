#!/usr/bin/env python3

import os, psutil, signal
import sys
import fcntl
import pytz
import time
from datetime import datetime
import multiprocessing
from multiprocessing import Queue
import subprocess, shlex
import atexit
import signal
import socketserver
import socket
import re
import shutil

def getTaipeiTime():
    return datetime.now(pytz.timezone('Asia/Taipei')).strftime("%m-%d_%H-%M")

def check_PidAlive(pid):
    """
    return True if the pid is still working
    return False if the pid id dead
    """
    if pid != None:
        try:
            if os.waitpid(pid, os.WNOHANG) == (0,0):
                return True
            else:
                return False
        except OSError:
            pass
    return False

def KillProcesses(pid):
    '''
    kill all the children of pid and itself
    '''
    parent_pid = pid
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child.kill()
    except Exception as e:
        print("Failed to KillProcesses with pid={}\n Skip it.".format(pid))
        return
    parent.kill()

def KillChildren(pid):
    '''
    kill all the children of the pid except itself
    '''
    parent_pid = pid
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception as e:
                pass
    except Exception as e:
        print("Failed to KillChildren with pid={}\nReasons:{}".format(pid, e))
        return

def KillPid(pid):
    '''
    kill the pid
    '''
    try:
        os.kill(pid, signal.SIGKILL)
    except Exception as e:
        print("KillPid() failed.\n reasons:{}".format(e))


def LimitTimeExec(LimitTime, Func, *args):
    """
    Input:
    1. LimitTime: is in the unit of secs.
    2. Func: must return a list that contains your return value
    3. args: pass into Func
    Return value:
    1. isKilled: killed by timing
    2. ret(int): from Func(args) to indicate success or not
    """
    ret = -1
    PrevWd = os.getcwd()
    isKilled = False
    WaitSecs = 0
    WaitUnit = 10
    ExecProc = multiprocessing.Process(target=Func, args=[args])
    # NOTE: SIGKILL will not kill the children
    # kill all its sub-process when parent is killed.
    ExecProc.daemon = True
    ExecProc.start()
    while True:
        date = getTaipeiTime()
        if ExecProc.is_alive():
            # log date to check liveness
            print("Alive at {}".format(date))
            time.sleep(WaitUnit)
            WaitSecs += WaitUnit
        else:
            # return the return code to indicate success or not
            ret = ExecProc.exitcode
            isKilled = False
            print("The command is finished at {} with exitcode={}, break.".format(date, ret))
            break
        if WaitSecs > LimitTime:
            if not ExecProc.is_alive():
                # if the work is done after the sleep
                continue
            # handle the processes twice, kill its children first
            KillChildren(ExecProc.pid)
            # with daemon flag, all children will be terminated
            ExecProc.terminate()
            KillPid(ExecProc.pid)
            # wait for a few secs
            ExecProc.join(10)
            if ExecProc.exitcode is None: # exitcode is None for unfinished proc.
                print("ExecProc.terminate() failed; Daemon handler exit.")
                sys.exit(0)
            isKilled = True
            ret = -1
            print("Achieve time limitation, kill it at {}.".format(getTaipeiTime()))
            break
    os.chdir(PrevWd)
    return isKilled, ret

def ExecuteCmd(WorkerID=1, Cmd="", Block=True):
    """
    return cmd's return code, STDOUT, STDERR
    """
    # Use taskset by default
    if Block:
        '''
        The taskset configuration depends on the hardware.
        If your computer is other than 8700K, you must customized it.
        Current configuration:
        intel 8700K:
            Core 0 as the "benchmark scheduler"
            Core 1~5 as the "worker" to run programs.
            Core 6~11 are not "real core", they are hardware threads shared with Core 0~5.
        '''
        CpuWorker = str((int(WorkerID) % 5) + 1)
        TrainLoc = os.getenv("LLVM_THESIS_TrainingHome", "Error")
        FullCmd = "taskset -c " + CpuWorker + " " + Cmd
        #print(FullCmd)
        p = subprocess.Popen(shlex.split(FullCmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
        out, err = p.communicate()
        p.wait()
        return p.returncode, out, err
    else:
        print("TODO: non-blocking execute", file=sys.stderr)

class EnvBuilder:
    def CheckTestSuiteCmake(self, WorkerID):
        """
        return LitTestDict: { target-name: .test-loc }
        """
        llvmSrc = os.getenv("LLVM_THESIS_HOME", "Error")
        if llvmSrc == "Error":
            print("$LLVM_THESIS_HOME or not defined.", file=sys.stderr)
            sys.exit(1)
        TestSrc = llvmSrc + "/test-suite/build-worker-" + WorkerID
        PrevWd = os.getcwd()
        # if the cmake is not done, do it once.
        if not os.path.isdir(TestSrc):
            os.mkdir(TestSrc)
            os.chdir(TestSrc)
            '''
            ex.
            cmake -DCMAKE_C_COMPILER=/home/jrchang/workspace/llvm-thesis/build-release-gcc7-worker1/bin/clang -DCMAKE_CXX_COMPILER=/home/jrchang/workspace/llvm-thesis/build-release-gcc7-worker1/bin/clang++ ../
            '''
            cBinSrc = llvmSrc + "/build-release-gcc7-worker" + WorkerID + "/bin/clang"
            cxxBinSrc = cBinSrc + "++"
            cmd = "cmake -DCMAKE_C_COMPILER=" + cBinSrc + " -DCMAKE_CXX_COMPILER=" + cxxBinSrc + " ../"
            ret = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
            os.chdir(PrevWd)
            if ret != 0:
                print("cmake failed.", file=sys.stderr)
                sys.exit(1)
        # Build .test dict for verification and run
        LitTestDict = {}
        for root, dirs, files in os.walk(TestSrc):
            for file in files:
                if file.endswith(".test"):
                    name = file[:-5]
                    path = os.path.join(root, file)
                    LitTestDict[name] = path
        return LitTestDict

    def workerMake(self, args):
        """
        Input: args(tuple):
        [0]:WorkerID
        [1]:BuildTarget
        Return a int:
        a number that indicate status.
            0      --> build success
            others --> build failed
        """
        PrevWd = os.getcwd()
        WorkerID = args[0]
        BuildTarget = args[1]
        ret = -1
        '''
        build
        '''
        llvmSrc = os.getenv("LLVM_THESIS_HOME", "Error")
        TestSrc = llvmSrc + "/test-suite/build-worker-" + WorkerID
        os.chdir(TestSrc)
        cmd = "make " + BuildTarget
        ret, _, _ = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
        return ret

    def make(self, WorkerID, BuildTarget):
        """
        return a number:
        0 --> build success
        others   --> build failed
        """
        isKilled, ret = LimitTimeExec(900, self.workerMake, WorkerID, BuildTarget)
        if isKilled or ret != 0:
            return -1
        else:
            return 0
    def workerVerify(self, args):
        """
        Input(tuple):
        [0]:WorkerID
        [1]:TestLoc
        Return a int:
        a number that indicate status.
            0      --> build success
            others --> build failed
        """
        ret = -1
        WorkerID = args[0]
        TestLoc = args[1]
        Lit = os.getenv("LLVM_THESIS_lit", "Error")
        if Lit == "Error":
            print("$LLVM_THESIS_lit not defined.", file=sys.stderr)
            sys.exit(1)
        cmd = Lit + " -q " + TestLoc
        _, out, err = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
        if out:
            ret = -1
        else:
            ret = 0
        return ret

    def verify(self, WorkerID, TestLoc):
        """
        return a number:
        0 --> success and correct
        others   --> failed
        """
        isKilled, ret = LimitTimeExec(500, self.workerVerify, WorkerID, TestLoc)
        if isKilled or ret != 0:
            return -1
        else:
            return 0

    def distributePyActor(self, TestFilePath):
        """
        return 0 for success
        return -1 for failure.
        """
        Log = LogService()
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
        try:
            # Rename the real elf
            shutil.move(ElfPath, NewElfPath)
            # Copy the feature-extractor
            shutil.copy2(PyActorLoc, ElfPath + ".py")
        except Exception as e:
            print("distributePyActor() errors, Reasons:\n{}".format(e))
            return -1
        # Copy the PyCaller
        if os.path.exists(PyCallerLoc) == True:
            shutil.copy2(PyCallerLoc, ElfPath)
        else:
            Log.err("Please \"$ make\" to get PyCaller in {}\n".format(PyCallerLoc))
            return -1
        return 0 #success

    def run(self, WorkerID, TestLoc):
        ret = self.verify(WorkerID, TestLoc)
        return ret

class EnvResponseActor:
    def EnvEcho(self, BuildTarget, WorkerID, LitTestDict):
        """
        return "Success" or "Failed"
        """
        testLoc = LitTestDict[BuildTarget]
        retString = "Success"
        '''
        remove previous build and build again
        '''
        env = EnvBuilder()
        '''
        ex1. RUN: /llvm/test-suite/build-worker-1/SingleSource/Benchmarks/Dhrystone/dry
        ex2. RUN: cd /home/jrchang/workspace/llvm-thesis/test-suite/build-worker-1/MultiSource/Applications/sqlite3 ; /home/jrchang/workspace/llvm-thesis/test-suite/build-worker-1/MultiSource/Applications/sqlite3/sqlite3 -init /home/jrchang/workspace/llvm-thesis/test-suite/MultiSource/Applications/sqlite3/sqlite3rc :memory: < /home/jrchang/workspace/llvm-thesis/test-suite/MultiSource/Applications/sqlite3/commands
        '''
        with open(testLoc, "r") as file:
            fileCmd = file.readline()
            file.close()
        MultiCmdList = fileCmd.split(';')
        if len(MultiCmdList) == 1:
            # cases like ex1.
            BuiltBin = fileCmd.split()[1]
        else:
            # cases like ex2.
            BuiltBin = MultiCmdList[1].strip().split()[0]
        '''
        remove binary does not ensure it will be built again.
        Therefore, we must use "make clean"
        '''
        binName = BuiltBin.split('/')[-1]
        dirPath = BuiltBin[:-(len(binName) + 1)]
        prevWd = os.getcwd()
        '''
        print("fileCmd={}".format(fileCmd))
        print("BuiltBin={}".format(BuiltBin))
        print("dirPath={}".format(dirPath))
        print("binName={}".format(binName))
        '''
        os.chdir(dirPath)
        os.system("make clean")
        os.chdir(prevWd)

        # remove feature file
        FeatureFile = '/tmp/PredictionDaemon/worker-{}/features'.format(WorkerID)
        if os.path.exists(FeatureFile):
            os.remove(FeatureFile)

        '''
        build
        assuming the proper cmake is already done.
        '''
        ret = env.make(WorkerID, BuildTarget)
        if ret != 0:
            return "Failed"
        '''
        verify
        '''
        ret = env.verify(WorkerID, testLoc)
        if ret != 0:
            return "Failed"
        '''
        distribute PyActor
        '''
        ret = env.distributePyActor(testLoc)
        if ret != 0:
            return "Failed"
        '''
        run and extract performance
        The return value from env.run() can be ignored.
        We already use env.verify() to verify it.
        '''
        ret = env.run(WorkerID, testLoc)
        return retString



class LogService():
    def __init__(self):
        pass

    def outNotToFile(self, msg):
        print(msg, end="", file=sys.stdout)

    def FileWriter(self, path, msg):
        file = open(path, "a")
        fcntl.flock(file, fcntl.LOCK_EX)
        file.write(msg)
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()

    def out(self, msg):
        self.outNotToFile(msg)

    def err(self, msg):
        self.out(msg)
        #self.FileWriter("/tmp/PredictionDaemon.err", msg)

class ConnectInfoService():
    def getConnectDict(self, path):
        '''
        return Dict[WorkerID] = ["RemoteEnv-ip", "RemoteEnv-port"]
        '''
        Dict = {}
        with open(path, "r") as file:
            # skip the header line
            file.readline()
            for line in file:
                info = line.split(",")
                strippedInfo = []
                for subInfo in info:
                    strippedInfo.append(subInfo.strip())
                Dict[strippedInfo[0]] = [strippedInfo[1], strippedInfo[2]]
            file.close()
        return Dict

