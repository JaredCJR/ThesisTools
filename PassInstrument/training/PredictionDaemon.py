#!/usr/bin/env python3
"""
Daemon
"""
import os
import sys
import atexit
import signal
from multiprocessing import Process
"""
TCP server lib
"""
import time
import socketserver
import socket
"""
Random Predictor
"""
import ServiceLib as sv
import re


class ResponseActor:
    """
    Input: "InputString" must be demangled function name
    """
    def RandomOrBestEcho(self, InputString, SenderIpString):
        Log = sv.LogService()
        retString = ""
        '''
        Gather Benchmark information
        '''
        msg = "Function:\"{}\"".format(InputString)
        InfoFile = open("/tmp/PredictionDaemon.info", "r")
        Info = InfoFile.read()
        InfoFile.close()
        lines = Info.splitlines()
        BenchmarkName = lines[0]
        BestSet = lines[1]
        FunctionList = lines[2:]
        '''
        Use random passes or best passes?
        '''
        Mode = ""
        UseRandomSet = False
        Skip = False
        InputString = InputString.strip()
        OrigInputString = InputString
        if InputString == "DecodeFailed-GetBestSet" or (not InputString):
            UseRandomSet = False
            Skip = True
        # C-style matching
        if InputString in FunctionList and not Skip:
            UseRandomSet = True
        # C++-style matching
        # perf cannot get argument information, but clang can.
        # We need to use regular exp. to match it.
        # This may match the wrong one, but that is okay.
        if UseRandomSet == False and (not Skip):
            try:
                # Replace all space in function name
                InputString = InputString.replace(' ', '')
                newFunctionList = []
                for func in FunctionList:
                    newFunctionList.append(func.replace(' ', ''))
                FunctionList = newFunctionList
                ReEscapedInput = re.escape(InputString)
                SearchTarget = ".*{func}.*".format(func=ReEscapedInput)
                r = re.compile(SearchTarget)
                reRetList = list(filter(r.search, FunctionList))
                if reRetList:
                    UseRandomSet = True
                else:
                    for func in FunctionList:
                        # In most cases, InputString has more information than perf profiled function.
                        if re.search(re.escape(func), InputString):
                            UseRandomSet = True
                            break
            except Exception as e:
                print("Exception: {}\n SearchTarget:\"{}\"\n".format(e, SearchTarget))
        # If the search result is not empty and not failed to decode, use random set.
        if UseRandomSet and not Skip:
            predictor = RG.FunctionLevelPredictor()
            SetList = predictor.RandomPassSet()
            for Pass in SetList:
                retString = retString + str(Pass) + " "
            Mode = "RandomSet"
        else:
            retString = BestSet
            Mode = "BestSet"
        # Convert list into string
        Log.recordFuncInfo("{}; set | {}; func | {}; mode | {}\n".format(BenchmarkName,
            retString, OrigInputString, Mode))
        return retString
    """
    Input: "InputString" must be demangled function name
    """
    def fooClangEcho(self, InputString, SenderIpString):
        Inputs = InputString.split('@')
        FuncName = Inputs[0]
        #FuncFeatures = Inputs[1]
        #print(FuncName)
        retString = ""
        Mode = "fooSet"
        return retString

    def fooEnvEcho(self, InputString, SenderIpString):
        #TODO
        retString = ""
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
            self.data = self.rfile.readline().strip()
            #print("{} wrote: {}".format(self.client_address[0], self.data.decode('utf-8')))
            actor = ResponseActor()
            try:
                Str = self.data.decode('utf-8')
            except Exception as e:
                Str = "DecodeFailed"
            #WriteContent = actor.RandomOrBestEcho(Str, self.client_address[0])
            WriteContent = actor.fooClangEcho(Str, self.client_address[0])
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
            self.data = self.rfile.read()
            #print("{} wrote: {}".format(self.client_address[0], self.data.decode('utf-8')))
            try:
                Str = self.data.decode('utf-8')
            except Exception as e:
                Str = "DecodeFailed"
            with open(DaemonIpcFileLoc, 'w') as IpcFile:
                IpcFile.write(Str)
                IpcFile.close()
            actor = ResponseActor()
            WriteContent = actor.fooEnvEcho(Str, self.client_address[0])
            #print(DaemonIpcFileLoc)
            '''
            Likewise, self.wfile is a file-like object used to write back
            to the client
            Only accept byte-object
            '''
            #self.wfile.write(WriteContent.encode('utf-8'))

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
            raise SystemExit(1)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def SetupClangServer(self, ClangHost="127.0.0.1", ClangPort=7521):
        sys.stdout.write('Daemon-Clang started with pid {}\n'.format(os.getpid()))
        '''
        If the port is opened, close it!
        '''
        server = tcpServer()
        sys.stdout.write('Clang-TCP server started with ip:{} port:{}\n'.format(ClangHost, ClangPort))
        server.CreateClangTcpServer(ClangHost, ClangPort)

    def SetupEnvServer(self, EnvHost="127.0.0.1", EnvPort=8521):
        sys.stdout.write('Daemon-Env started with pid {}\n'.format(os.getpid()))
        '''
        If the port is opened, close it!
        '''
        server = tcpServer()
        sys.stdout.write('Clang-Env server started with ip:{} port:{}\n'.format(EnvHost, EnvPort))
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
            # tcp server will block the process, we need two processes.
            if os.fork():
                # Create daemon for agent
                self.CreateDaemon(EnvDaemonName, EnvPidFile, EnvLogFile,
                        EnvHost, EnvPort)
            else:
                # Create daemon for clang
                self.CreateDaemon(ClangDaemonName, ClangPidFile, ClangLogFile, 
                        ClangHost, ClangPort)

        elif argv[1] == 'stop':
            ExitFlag = False
            # Stop Daemon-Clang
            if os.path.exists(ClangPidFile):
                with open(ClangPidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
            else:
                print(ClangDaemonName + ': Not running', file=sys.stderr)
                ExitFlag = True
            # Stop Daemon-Env
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
