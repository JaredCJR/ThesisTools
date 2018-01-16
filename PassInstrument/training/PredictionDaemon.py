#!/usr/bin/env python3
import os
import sys
import atexit
import signal
from multiprocessing import Process
import time
import socketserver
import socket
import ServiceLib as sv
import re
import shlex
import shutil
import psutil
import subprocess
import InstrumentServiceLib as sv

def ExecuteCmd(WorkerID=1, Cmd="", Block=True):
    """
    return cmd's return code, STDOUT, STDERR
    """
    # Use taskset by default
    if Block:
        TrainLoc = os.getenv("LLVM_THESIS_TrainingHome", "Error")
        FullCmd = "taskset -c " + WorkerID + " " + Cmd
        print(FullCmd)
        p = subprocess.Popen(shlex.split(FullCmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
        out, err = p.communicate()
        p.wait()
        return p.returncode, out, err
    else:
        #TODO
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


    def make(self, WorkerID, BuildTarget):
        """
        return 0 --> build success
        others   --> build failed
        """
        llvmSrc = os.getenv("LLVM_THESIS_HOME", "Error")
        TestSrc = llvmSrc + "/test-suite/build-worker-" + WorkerID
        PrevWd = os.getcwd()
        os.chdir(TestSrc)
        cmd = "make " + BuildTarget
        ret, _, _ = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
        os.chdir(PrevWd)
        return ret

    def verify(self, WorkerID, TestLoc):
        """
        return 0 --> build success
        others   --> build failed
        """
        Lit = os.getenv("LLVM_THESIS_lit", "Error")
        if Lit == "Error":
            print("$LLVM_THESIS_lit not defined.", file=sys.stderr)
            sys.exit(1)
        cmd = Lit + " -q " + TestLoc
        _, out, err = ExecuteCmd(WorkerID=WorkerID, Cmd=cmd, Block=True)
        if not out:
            ret = 0 # Success
        else:
            ret = -1 # Fail
        return ret

    def distributePyActor(self, TestFilePath):
        Log = sv.LogService()
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
            Log.err("NeedStdin = True\n")
        else:
            PyCallerLoc = InstrumentSrc + '/PyActor/WithoutStdin/PyCaller'
            PyActorLoc = InstrumentSrc + '/PyActor/WithoutStdin/MimicAndFeatureExtractor.py'
            Log.err("NeedStdin = False\n")
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
    def fooClangEcho(self, InputString, SenderIpString):
        """
        Input: "InputString" must be demangled function name
        """
        Inputs = InputString.split('@')
        FuncName = Inputs[0]
        #FuncFeatures = Inputs[1]
        #print(FuncName)
        retString = ""
        Mode = "fooSet"
        return retString

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
        assuming the proper cmake is already done.
        '''
        env = EnvBuilder()
        # ex. RUN: /llvm/test-suite/build-worker-1/SingleSource/Benchmarks/Dhrystone/dry
        with open(testLoc, "r") as file:
            fileCmd = file.readline()
            file.close()
        BuiltBin = fileCmd.split()[1]
        if os.path.exists(BuiltBin):
            os.remove(BuiltBin)
        ret = env.make(WorkerID, BuildTarget)
        if ret != 0:
            retString = "BuildFailed"
            return retString
        '''
        verify
        '''
        ret = env.verify(WorkerID, testLoc)
        if ret != 0:
            retString = "VerifyFailed"
            return retString
        '''
        distribute PyActor
        '''
        env.distributePyActor(testLoc)
        '''
        run and extract performance
        '''
        ret = env.verify(WorkerID, testLoc)
        return retString

class tcpServer:
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
            actor = ResponseActor()
            try:
                Str = data.decode('utf-8')
            except Exception as e:
                Str = "DecodeFailed"
            #WriteContent = actor.fooClangEcho(Str, self.client_address[0])
            with open(DaemonIpcFileLoc, 'r') as IpcFile:
                WriteContent = IpcFile.read()
                IpcFile.close()
            '''
            Likewise, self.wfile is a file-like object used to write back
            to the client
            Only accept byte-object
            '''
            self.wfile.write(WriteContent.encode('utf-8'))

    class EnvTcpHandler(socketserver.StreamRequestHandler):
        def handle(self):
            global DaemonIpcFileLoc
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
            '''
            Expect something like
            "target @ Shootout-C++-matrix @ 2 5 16 6 31 4 18 32 11"
            '''
            recvCmd = strList[0].strip()
            if recvCmd == "target":
                '''
                normal procedure
                '''
                BuildTarget = strList[1].strip()
                Passes = strList[2].strip()
                with open(DaemonIpcFileLoc, 'w') as IpcFile:
                    IpcFile.write(Passes)
                    IpcFile.close()
                actor = ResponseActor()
                # build, verify, run.
                WriteContent = actor.EnvEcho(BuildTarget) + "\n"
                '''
                Likewise, self.wfile is a file-like object used to write back
                to the client
                Only accept byte-object
                '''
                #print("Try to write: \"{}\" to \"{}\"".format(WriteContent, self.client_address[0]))
                self.wfile.write(WriteContent.encode('utf-8'))
            elif recvCmd == "kill":
                '''
                kill ourselves
                '''
                global EnvPidFile
                print("Received kill cmd.", file=sys.stderr)
                with open(EnvPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)

    def CreateClangTcpServer(self, HOST, PORT):
        # Make port reusable
        socketserver.TCPServer.allow_reuse_address = True
        # Create the server, binding to host on port
        server = socketserver.TCPServer((HOST, PORT), self.ClangTcpHandler)
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()

    def CreateEnvTcpServer(self, HOST, PORT):
        # Make port reusable
        socketserver.TCPServer.allow_reuse_address = True
        # Create the server, binding to host on port
        server = socketserver.TCPServer((HOST, PORT), self.EnvTcpHandler)
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
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
            raise SystemExit(1)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def SetupClangServer(self, ClangHost="127.0.0.1", ClangPort=7521):
        sys.stdout.write('Clang-Daemon started with pid {}\n'.format(os.getpid()))
        '''
        If the port is opened, close it!
        '''
        server = tcpServer()
        sys.stdout.write('Clang-TCP server started with ip:{} port:{}\n'.format(ClangHost, ClangPort))
        server.CreateClangTcpServer(ClangHost, ClangPort)

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
        ClangConnectDict = {}
        EnvConnectDict = {}
        InstrumentHome = os.getenv("LLVM_THESIS_InstrumentHome", "Error")
        if InstrumentHome == "Error":
            sys.exit(1)
        ClangConnectInfo = InstrumentHome + "/training/ClangConnectInfo"
        EnvConnectInfo = InstrumentHome + "/training/EnvConnectInfo"
        with open(ClangConnectInfo, "r") as file:
            file.readline()
            for line in file:
                info = line.split(",")
                ClangConnectDict[info[0]] = [info[1], info[2]]
            file.close()
        with open(EnvConnectInfo, "r") as file:
            file.readline()
            for line in file:
                info = line.split(",")
                EnvConnectDict[info[0]] = [info[1], info[2]]
            file.close()
        return ClangConnectDict, EnvConnectDict

    def CreateDaemon(self, DaemonName, PidFile, LogFile,
            Host, Port):
        try:
            self.daemonize(PidFile,
                      LogFile,
                      stdout=LogFile,
                      stderr=LogFile)
        except RuntimeError as e:
            print("{} daemonize failed. {}".format(DaemonName, e), file=sys.stderr)
            raise SystemExit(1)
        if DaemonName == "PredictionDaemon-Clang":
            self.SetupClangServer(Host, Port)
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
                time.sleep(1)
                # check cmake
                builder = EnvBuilder()
                builder.CheckTestSuiteCmake(WorkerID)
                self.CreateDaemon(EnvDaemonName, EnvPidFile, EnvLogFile,
                        EnvHost, EnvPort)
            else:
                # Create daemon for clang
                self.CreateDaemon(ClangDaemonName, ClangPidFile, ClangLogFile,
                        ClangHost, ClangPort)

        elif argv[1] == 'stop':
            ExitFlag = False
            # Stop Clang-Daemon
            if os.path.exists(ClangPidFile):
                with open(ClangPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
            else:
                print(ClangDaemonName + ': Not running', file=sys.stderr)
                ExitFlag = True
            # Stop Env-Daemon
            if os.path.exists(EnvPidFile):
                with open(EnvPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
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
