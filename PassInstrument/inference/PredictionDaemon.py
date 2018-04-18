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

    def EnvEcho(self, BuildTarget, WorkerID, LitTestDict):
        return lib.EnvResponseActor().EnvEcho(BuildTarget, WorkerID, LitTestDict)

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
            global LitTestDict
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
                WriteContent = actor.EnvEcho(BuildTarget, WorkerID, LitTestDict)
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
                time.sleep(1)
                # check cmake
                builder = lib.EnvBuilder()
                global LitTestDict
                LitTestDict = builder.CheckTestSuiteCmake(WorkerID)
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
