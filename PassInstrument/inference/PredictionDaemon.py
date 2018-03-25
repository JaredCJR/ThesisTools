#!/usr/bin/env python3
import os
import sys
import atexit
import signal
import multiprocessing
import time
import socketserver
import socket
import re
import shlex
import shutil
import psutil
import subprocess, threading
import Lib as lib
import tfServer
from queue import Queue
from multiprocessing import Process, Lock

def ExecuteCmd(WorkerID=1, Cmd="", Block=True):
    """
    return cmd's return code, STDOUT, STDERR
    """
    # Use taskset by default
    if Block:
        TrainLoc = os.getenv("LLVM_THESIS_TrainingHome", "Error")
        FullCmd = "taskset -c " + WorkerID + " " + Cmd
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
        global LitTestDict # { target-name: .test-loc }
        LitTestDict = {}
        for root, dirs, files in os.walk(TestSrc):
            for file in files:
                if file.endswith(".test"):
                    name = file[:-5]
                    path = os.path.join(root, file)
                    LitTestDict[name] = path

    def KillProcesses(self, pid):
        '''
        kill all the children of pid and itself
        '''
        parent_pid = pid
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

    def KillPid(self, pid):
        '''
        kill the pid
        '''
        os.kill(pid, signal.SIGKILL)

    def LimitTimeExec(self, LimitTime, Func, *args):
        """
        Input:
        1. LimitTime: is in the unit of secs.
        2. Func: must return a list that contains your return value
        3. args: pass into Func
        Return value:
        1. isKilled: killed by timing
        2. retList: from Func(args)
        """
        retList = []
        PrevWd = os.getcwd()
        isKilled = False
        ParentPid = os.getpid()
        pid = os.fork()
        if pid == 0:
            retList = Func(args)
            # kill the timing thread
            self.KillPid(ParentPid)
        else:
            WaitSecs = 0
            WaitUnit = 1
            while True:
                rid, status = os.waitpid(pid, os.WNOHANG)
                if rid == 0 and status == 0:
                    time.sleep(WaitUnit)
                    WaitSecs += WaitUnit
                # The time depends on you =)
                if WaitSecs > LimitTime:
                    self.KillProcesses(pid)
                    isKilled = True
                    retList.append(-1)
        os.chdir(PrevWd)
        return isKilled, retList

    def workerMake(self, args):
        """
        Input(tuple):
        [0]:WorkerID
        [1]:BuildTarget
        Return a list:
        [0]: a number that indicate status.
                0      --> build success
                others --> build failed
        """
        PrevWd = os.getcwd()
        WorkerID = args[0]
        BuildTarget = args[1]
        retList = []
        '''
        build
        '''
        llvmSrc = os.getenv("LLVM_THESIS_HOME", "Error")
        TestSrc = llvmSrc + "/test-suite/build-worker-" + WorkerID
        os.chdir(TestSrc)
        cmd = "make " + BuildTarget
        ret, _, _ = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
        retList.append(ret)
        return retList

    def make(self, WorkerID, BuildTarget):
        """
        return a number:
        0 --> build success
        others   --> build failed
        """
        isKilled, retList = self.LimitTimeExec(500, self.workerMake, WorkerID, BuildTarget)
        if isKilled or retList[0] != 0:
            return -1
        else:
            return 0

    def workerVerify(self, args):
        """
        Input(tuple):
        [0]:WorkerID
        [1]:TestLoc
        Return a list:
        [0]: a number that indicate status.
                0      --> build success
                others --> build failed
        """
        retList = []
        WorkerID = args[0]
        TestLoc = args[1]
        Lit = os.getenv("LLVM_THESIS_lit", "Error")
        if Lit == "Error":
            print("$LLVM_THESIS_lit not defined.", file=sys.stderr)
            sys.exit(1)
        cmd = Lit + " -q " + TestLoc
        _, out, err = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
        if out:
            retList.append(-1)
        else:
            retList.append(0)
        return retList

    def verify(self, WorkerID, TestLoc):
        """
        return a number:
        0 --> build success
        others   --> build failed
        """
        isKilled, retList = self.LimitTimeExec(500, self.workerVerify, WorkerID, TestLoc)
        if isKilled or retList[0] != 0:
            return -1
        else:
            return 0

    def distributePyActor(self, TestFilePath):
        Log = lib.LogService()
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
        # Rename the real elf
        shutil.move(ElfPath, NewElfPath)
        # Copy the feature-extractor
        shutil.copy2(PyActorLoc, ElfPath + ".py")
        # Copy the PyCaller
        if os.path.exists(PyCallerLoc) == True:
            shutil.copy2(PyCallerLoc, ElfPath)
        else:
            Log.err("Please \"$ make\" to get PyCaller in {}\n".format(PyCallerLoc))
            return

    def run(self, WorkerID, TestLoc):
        ret = self.verify(WorkerID, TestLoc)
        return ret

class ResponseActor:
    def ClangEcho(self, InputString, SenderIpString):
        """
        Input: "InputString" must be demangled function name
        """
        global GlobalIpcQueue_Features
        global GlobalIpcQueue_Pass
        global tfServerLock
        Inputs = InputString.split('@')
        FuncName = Inputs[0]
        FuncFeatures = Inputs[1]
        # lock to prevent race condition
        tfServerLock.acquire()
        GlobalIpcQueue_Features.put(InputString, block=True, timeout=None)
        Pass = GlobalIpcQueue_Pass.get(block=True, timeout=None)
        tfServerLock.release()
        return str(Pass)

    def EnvEcho(self, BuildTarget):
        """
        return "Success" or "Failed"
        """
        global WorkerID
        global LitTestDict
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
        dirPath = BuiltBin[:-(len(binName) + 1):]
        prevWd = os.getcwd()
        ##
        '''
        print("fileCmd={}".format(fileCmd))
        print("BuiltBin={}".format(BuiltBin))
        print("dirPath={}".format(dirPath))
        print("binName={}".format(binName))
        '''
        ##
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
        env.distributePyActor(testLoc)
        '''
        run and extract performance
        '''
        ret = env.run(WorkerID, testLoc)
        return retString

class tcpServer:
    def __init__(self):
        m = multiprocessing.Manager()
        '''
        Out worker use different process to isolate the resources,
        so we do not need mutex in this cases.
        '''
        self.GlobalIpcQueue_Features = m.Queue()
        self.GlobalIpcQueue_Pass = m.Queue()
        self.tfServerLock = Lock()

    class ClangTcpHandler(socketserver.StreamRequestHandler):
        def handle(self):
            global DaemonIpcFileLoc
            '''
            self.rfile is a file-like object created by the handler;
            we can now use e.g. readline() instead of raw recv() calls
            Get byte-object
            '''
            # This only read the first line.
            data = self.rfile.readline().strip()
            #print("{} wrote: {}".format(self.client_address[0], self.data.decode('utf-8')))
            try:
                Str = data.decode('utf-8')
            except Exception as e:
                Str = "DecodeFailed"
            actor = ResponseActor()
            WriteContent = actor.ClangEcho(Str, self.client_address[0])
            '''
            with open(DaemonIpcFileLoc, 'r') as IpcFile:
                WriteContent = IpcFile.read()
                IpcFile.close()
            '''
            '''
            self.wfile is a file-like object used to write back
            to the client
            Only accept byte-object
            '''
            self.wfile.write(WriteContent.encode('utf-8'))

    class EnvTcpHandler(socketserver.StreamRequestHandler):
        def writeMsgBack(self, WriteContent):
            '''
            self.wfile is a file-like object used to write back
            to the client
            Only accept byte-object
            '''
            WriteContent = WriteContent + '\n'
            self.wfile.write(WriteContent.encode('utf-8'))

        def handle(self):
            global DaemonIpcFileLoc
            global WorkerID
            '''
            self.rfile is a file-like object created by the handler;
            we can now use e.g. readline() instead of raw recv() calls
            Get byte-object
            '''
            data = self.rfile.readline()
            try:
                Str = data.decode('utf-8')
            except Exception as e:
                Str = "DecodeFailed"
            # Parse the decoded tcp input
            strList = Str.split('@')
            recvCmd = strList[0].strip()
            if recvCmd == "target":
                '''
                build, verify and run.
                Expect something like
                "target @ Shootout-C++-matrix @ 2 5 16 6 31 4 18 32 11"
                '''
                BuildTarget = strList[1].strip()
                Passes = strList[2].strip()
                with open(DaemonIpcFileLoc, 'w') as IpcFile:
                    IpcFile.write(Passes)
                    IpcFile.close()
                actor = ResponseActor()
                # build, verify, run.
                WriteContent = actor.EnvEcho(BuildTarget)
                PossibleRet = ["Success", "Failed"]
                if WriteContent not in PossibleRet:
                    self.writeMsgBack("EnvEcho Error!")
                else:
                    self.writeMsgBack(WriteContent)
            elif recvCmd == "kill":
                '''
                kill ourselves
                '''
                global EnvPidFile
                print("Received kill cmd.", file=sys.stderr)
                with open(EnvPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
            elif recvCmd == "profiled":
                '''
                send profiled data
                Cmd looks like: "profiled @ dry"
                '''
                target = strList[1].strip()
                targetLoc = "/tmp/PredictionDaemon/worker-{}/{}.usage".format(WorkerID, target)
                if not os.path.exists(targetLoc):
                    WriteContent = "ProfiledFileNotExists in {}".format(targetLoc)
                else:
                    with open(targetLoc, 'r') as file:
                        WriteContent = file.read().strip()
                        file.close()
                self.writeMsgBack(WriteContent)
            elif recvCmd == "features":
                '''
                send instrumented features from clang
                Cmd looks like: "features"
                '''
                featureLoc = "/tmp/PredictionDaemon/worker-{}/features".format(WorkerID)
                if not os.path.exists(featureLoc):
                    WriteContent = "FeaturesFileNotExists in {}".format(featureLoc)
                else:
                    with open(featureLoc, 'r') as file:
                        WriteContent = file.read().strip()
                        file.close()
                self.writeMsgBack(WriteContent)
    def CreateClangTcpServer(self, HOST, PORT, WorkerID):
        '''
        Create process for keeping the RL model
        thread will make the sigterm handler in that thread crash.
        '''
        global GlobalIpcQueue_Features
        global GlobalIpcQueue_Pass
        global tfServerLock
        GlobalIpcQueue_Features = self.GlobalIpcQueue_Features
        GlobalIpcQueue_Pass = self.GlobalIpcQueue_Pass
        tfServerLock = self.tfServerLock
        p = Process(target=tfServer.tfServer, args=(WorkerID,
            GlobalIpcQueue_Features, GlobalIpcQueue_Pass, ))
        p.start()
        # Make port reusable
        socketserver.TCPServer.allow_reuse_address = True
        # Create the server, binding to host on port
        server = socketserver.TCPServer((HOST, PORT), self.ClangTcpHandler)
        # Activate the server; this will keep running
        server.serve_forever()

    def CreateEnvTcpServer(self, HOST, PORT):
        # Make port reusable
        socketserver.TCPServer.allow_reuse_address = True
        # Create the server, binding to host on port
        server = socketserver.TCPServer((HOST, PORT), self.EnvTcpHandler)
        # Activate the server; this will keep running
        server.serve_forever()


class Daemon:
    def daemonize(self, PidFile, LogFile, *, stdin='/dev/null',
                                    stdout='/dev/null',
                                    stderr='/dev/null'):
        if os.path.exists(PidFile):
            raise RuntimeError('Already running')
        else:
            if os.path.exists(LogFile):
                os.remove(LogFile)

        # First fork (detaches from parent)
        try:
            if os.fork() > 0:
                raise SystemExit(0)   # Parent exit
        except OSError as e:
            raise RuntimeError('fork #1 failed.')

        os.chdir('/')
        os.umask(0)
        os.setsid()
        # Second fork (relinquish session leadership)
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as e:
            raise RuntimeError('fork #2 failed.')

        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()

        # Replace file descriptors for stdin, stdout, and stderr
        with open(stdin, 'rb', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open(stdout, 'wb', 0) as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
        with open(stderr, 'wb', 0) as f:
            os.dup2(f.fileno(), sys.stderr.fileno())

        # Write the PID file
        with open(PidFile,'w') as f:
            print(os.getpid(),file=f)

        # Arrange to have the PID file removed on exit/signal
        atexit.register(lambda: os.remove(PidFile))

        # Signal handler for termination (required)
        def sigterm_handler(signo, frame):
            #kill all the children of pid and itself
            parent_pid = os.getpid()
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                child.kill()
            # kill itselt and remove pid file.("atexit.register")
            try:
                raise SystemExit(1)
            except Exception as e:
                print('raise SystemExit(1) failed. remove myself manually.')
                os.remove(PidFile)
                os.kill(parent_pid)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def SetupClangServer(self, WorkerID, ClangHost="127.0.0.1", ClangPort=7521):
        sys.stdout.write('Clang-Daemon started with pid {}\n'.format(os.getpid()))
        sys.stdout.write('Clang-Daemon started with pid {}\n'.format(os.getpid()))
        '''
        If the port is opened, close it!
        '''
        server = tcpServer()
        sys.stdout.write('Clang-TCP server started with ip:{} port:{}\n'.format(ClangHost, ClangPort))
        server.CreateClangTcpServer(ClangHost, ClangPort, WorkerID)

    def SetupEnvServer(self, EnvHost="127.0.0.1", EnvPort=8521):
        sys.stdout.write('Env-Daemon started with pid {}\n'.format(os.getpid()))
        '''
        If the port is opened, close it!
        '''
        server = tcpServer()
        sys.stdout.write('Env-TCP server started with ip:{} port:{}\n'.format(EnvHost, EnvPort))
        server.CreateEnvTcpServer(EnvHost, EnvPort)

    def readConnectInfo(self):
        """
        return dict of connection info for clang and env
        """
        InstrumentHome = os.getenv("LLVM_THESIS_InstrumentHome", "Error")
        if InstrumentHome == "Error":
            sys.exit(1)
        ClangConnectInfo = InstrumentHome + "/Connection/ClangConnectInfo"
        EnvConnectInfo = InstrumentHome + "/Connection/EnvConnectInfo"
        cis = lib.ConnectInfoService()
        ClangConnectDict = cis.getConnectDict(ClangConnectInfo)
        EnvConnectDict = cis.getConnectDict(EnvConnectInfo)
        return ClangConnectDict, EnvConnectDict

    def CreateDaemon(self, DaemonName, PidFile, LogFile,
            Host, Port, WorkerID=None):
        try:
            self.daemonize(PidFile,
                      LogFile,
                      stdout=LogFile,
                      stderr=LogFile)
        except RuntimeError as e:
            print("{} daemonize failed. {}".format(DaemonName, e), file=sys.stderr)
            raise SystemExit(1)
        if DaemonName == "PredictionDaemon-Clang":
            self.SetupClangServer(WorkerID, Host, Port)
        elif DaemonName == "PredictionDaemon-Env":
            self.SetupEnvServer(Host, Port)
        else:
            print("Setup TCP server error.", file=sys.stderr)
            raise SystemExit(1)

    def run(self, argv):
        ClangDaemonName = "PredictionDaemon-Clang"
        EnvDaemonName = "PredictionDaemon-Env"
        ClangConnectDict, EnvConnectDict = self.readConnectInfo()

        if len(argv) != 3:
            print('Usage: {} [start|stop] [WorkerID]'.format(argv[0]), file=sys.stderr)
            raise SystemExit(1)

        global DaemonIpcFileLoc
        global WorkerID # WorkerID is a str
        global EnvPidFile
        WorkerID = argv[2]
        DaemonIpcFileLoc = "/tmp/PredictionDaemon-IPC-" + WorkerID
        ClangHost = ClangConnectDict[WorkerID][0]
        ClangPort = int(ClangConnectDict[WorkerID][1])
        EnvHost = EnvConnectDict[WorkerID][0]
        EnvPort = int(EnvConnectDict[WorkerID][1])
        ClangPidFile = '/tmp/' + ClangDaemonName + '-' + WorkerID + '.pid'
        ClangLogFile = '/tmp/' + ClangDaemonName + '-' + WorkerID + '.log'
        EnvPidFile = '/tmp/' + EnvDaemonName + '-' + WorkerID + '.pid'
        EnvLogFile = '/tmp/' + EnvDaemonName + '-' + WorkerID + '.log'

        print("WorkerID={}, Clang-Host={}, Clang-Port={}, Env-Host={}, Env-Port={}".format(WorkerID,
            ClangHost, ClangPort, EnvHost, EnvPort))

        if argv[1] == 'start':
            with open(DaemonIpcFileLoc, 'w') as IpcFile:
                # Write empty pass for the cmake check
                IpcFile.write("")
                IpcFile.close()
            # tcp server will block the process, we need two processes.
            if os.fork():
                # Create daemon for RL-env, Clang-Daemon shoud start first
                time.sleep(0.5)
                # check cmake
                builder = EnvBuilder()
                builder.CheckTestSuiteCmake(WorkerID)
                self.CreateDaemon(EnvDaemonName, EnvPidFile, EnvLogFile,
                        EnvHost, EnvPort)
            else:
                # Create daemon for clang
                self.CreateDaemon(ClangDaemonName, ClangPidFile, ClangLogFile,
                        ClangHost, ClangPort, WorkerID)

        elif argv[1] == 'stop':
            ExitFlag = False
            # Stop Clang-Daemon
            if os.path.exists(ClangPidFile):
                with open(ClangPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
                    print("{} is killed successfully".format(ClangDaemonName))
            else:
                print(ClangDaemonName + ': Not running', file=sys.stderr)
                ExitFlag = True
            # Stop Env-Daemon
            if os.path.exists(EnvPidFile):
                with open(EnvPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
                    print("{} is killed successfully".format(EnvDaemonName))
            else:
                print(EnvDaemonName + ': Not running', file=sys.stderr)
                ExitFlag = True

            if(ExitFlag):
                raise SystemExit(1)

        else:
            print('PredictionDaemon: Unknown command {!r}'.format(argv[1]), file=sys.stderr)
            raise SystemExit(1)

if __name__ == '__main__':
    daemon = Daemon()
    daemon.run(sys.argv)
