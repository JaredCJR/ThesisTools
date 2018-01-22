#!/usr/bin/python3
import os
import sys
import random
import socket
import signal
import time
import Lib as lib
from multiprocessing import Process, Manager, Lock

class Programs():
    def getAvailablePrograms(self):
        """
        return a dict of available "makefile target" in llvm test-suite
        {name:[cpu-cycles-mean, cpu-cycles-sigma]}
        """
        """
        Unwanted programs: Because of the bug in clang 5.0.1, not all of the
        programs in test-suite can apply the target passes. Therefore, we
        need to avoid them manually. This may change with the LLVM progress!
        """
        UnwantedTargets = ["tramp3d-v4", "spirit"]
        loc = os.getenv("LLVM_THESIS_Random_LLVMTestSuiteScript", "Error")
        if loc == "Error":
            sys.exit(1)
        # FIXME: if we re-measure the std-cycles, we should use the newer record.
        loc = loc + "/GraphGen/output/MeasurableStdBenchmarkMeanAndSigma"
        retDict = {}
        with open(loc, "r") as stdFile:
            for line in stdFile:
                LineList = line.split(";")
                '''
                In the newer version of LitDriver, we change the benchmakr naming strategies
                From "." to "/"
                '''
                #name = LineList[0].strip().split(".")[-1]
                name = LineList[0].strip().split("/")[-1]
                if name not in UnwantedTargets:
                    retDict[name] = [LineList[1].split("|")[1].strip(),
                            LineList[2].split("|")[1].strip()]
            stdFile.close()
        return retDict

    def genRandomPasses(self, TotalNum, TargetNum):
        """
        return a string of passes
        """
        FullSet = range(1, TotalNum + 1)
        FullSet = random.sample(FullSet, len(FullSet))
        SubSet = FullSet[:TargetNum]
        retString = ""
        for item in SubSet:
            retString = retString + str(item) + " "
        return retString

class TcpClient():
    SOCKET = None
    init = False
    def EstablishTcpConnect(self, IP, Port):
        if self.init == False:
            self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.SOCKET.connect((IP, Port))
            self.init = True

    def DestroyTcpConnection(self):
        if self.init == True:
            self.SOCKET.close()
            self.init = False

    def ReadEnvConnectInfo(self, WorkerID):
        """
        return IP(string), Port(number)
        """
        EnvConnectInfo = os.getenv("LLVM_THESIS_InstrumentHome", "Error")
        if EnvConnectInfo == "Error":
            print("$LLVM_THESIS_InstrumentHome is not defined.", file=sys.stderr)
            sys.exit(1)
        EnvConnectInfo = EnvConnectInfo + "/Connection/EnvConnectInfo"
        cis = lib.ConnectInfoService()
        EnvConnectDict = cis.getConnectDict(EnvConnectInfo)
        return EnvConnectDict[str(WorkerID)][0], int(EnvConnectDict[str(WorkerID)][1])

    def Send(self, WorkerID, Msg):
        """
        input format:
        WorkerID: number
        Msg: string
        """
        if self.init == False:
            IP, Port = self.ReadEnvConnectInfo(WorkerID)
            self.EstablishTcpConnect(IP, Port)
            self.init = True
        Msg = Msg + "\n"
        self.SOCKET.sendall(Msg.encode('utf-8'))

    def Receive(self, WorkerID):
        """
        Always disconnect after receiving.
        return: string
        """
        fragments  = []
        while True:
            chunck = self.SOCKET.recv(1024)
            if not chunck:
                break
            fragments.append(chunck)
        self.DestroyTcpConnection()
        return b"".join(fragments).decode('utf-8')

def sigint_handler(signum, frame):
    global maxWorkerNum
    tcp = TcpClient()
    msg = "kill"
    for i in range(1,maxWorkerNum + 1): # from 1 to maxWorkerNum
        tcp.Send(WorkerID=i, Msg=msg)
    sys.exit(1)

class Worker():
    def freeRemoteWorker(self, SharedWorkerDict, WorkerLock, WorkerID):
        '''
        no return.
        Free the worker in SharedWorkerDict for the WorkerID.
        '''
        WorkerLock.acquire()
        # manipulate SharedWorkerDict inside the lock.
        SharedWorkerDict[WorkerID] = True
        WorkerLock.release()

    def hireRemoteWorker(self, SharedWorkerDict, WorkerLock):
        '''
        return an available remote WorkerID
        '''
        retID = None
        WorkerLock.acquire()
        # manipulate SharedWorkerDict inside the lock.
        while True:
            for ID, free in SharedWorkerDict.items():
                if free == True:
                    retID = ID
                    break
            if retID is not None:
                break
        SharedWorkerDict[retID] = False
        WorkerLock.release()
        return retID

    def EnvDoJob(self, SharedWorkerDict, WorkerLock, target, passes):
        '''
        return the build status
        Possible values:
        1. "Success"
        2. "Failed"
        3. empty string <-- This is caused by Python3 TCP library. 
           (May be fixed in newer library version.)
        '''
        tcp = TcpClient()
        # get remote-worker
        workerID = self.hireRemoteWorker(SharedWorkerDict, WorkerLock)
        runStart = time.perf_counter()
        # tell env-daemon to build, verify and run
        msg = "target @ {} @ {}".format(target, passes)
        tcp.Send(WorkerID=workerID, Msg=msg)
        retStatus = tcp.Receive(WorkerID=workerID).strip()
        runEnd = time.perf_counter()
        runTime = runEnd - runStart
        if retStatus == "Success":
            sendStart = time.perf_counter()
            # get profiled data
            tcp.Send(WorkerID=workerID, Msg="profiled @ {}".format(target))
            retProfiled = tcp.Receive(WorkerID=workerID).strip()
            # get features
            tcp.Send(WorkerID=workerID, Msg="features")
            retFeatures = tcp.Receive(WorkerID=workerID).strip()
            sendEnd = time.perf_counter()
            sendTime = sendEnd - sendStart
        self.freeRemoteWorker(SharedWorkerDict, WorkerLock, workerID)
        printMsg = "WorkerID: {}; Target: {}; Status: {}; \nProfileSize: {}; FeatureSize: {}; \nRun-Time: {}; Send-Time: {};".format(workerID, target, retStatus, len(retProfiled), len(retFeatures), runTime, sendTime)
        printMsg = printMsg + "\n--------------------------------------\n"
        print(printMsg)
        return retStatus

    def EnvWorker(self, SharedWorkerDict, WorkerLock):
        prog = Programs()
        programDict = prog.getAvailablePrograms()
        keys = list(programDict.keys())
        #for i in range(100):
        for key, value in programDict.items():
            # random choose a build target
            #target = random.choice(keys)
            target = key
            # get random 9 passes from 34 of them.
            #passes = prog.genRandomPasses(34, 9)
            passes = ""
            retStatus = self.EnvDoJob(SharedWorkerDict, WorkerLock, target, passes)
            while not retStatus:
                '''
                Encounter Python3 TCP connection error.
                (This may be fix by newer TCP library.)
                Try again until get meaningful messages.
                '''
                retStatus = self.EnvDoJob(SharedWorkerDict, WorkerLock, target, passes)

if __name__ == '__main__':
    global maxWorkerNum
    maxWorkerNum = 5
    # register sigint handler
    signal.signal(signal.SIGINT, sigint_handler)
    # create shared var
    manager = Manager()
    WorkerLock = Lock()
    '''
    [ WorkerID : True] --> This worker is available
    [ WorkerID : False] --> This worker is NOT available
    '''
    SharedWorkerDict = manager.dict()
    # WorkerID is a str
    for i in range(1, maxWorkerNum + 1):
        SharedWorkerDict[str(i)] = True
    procList = []
    worker = Worker()
    for i in range(1, maxWorkerNum + 1):
        p = Process(target=worker.EnvWorker, args=(SharedWorkerDict, WorkerLock))
        p.start()
        procList.append(p)
    for p in procList:
        p.join()
