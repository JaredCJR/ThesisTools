#!/usr/bin/python3
import os
import sys
import random
import socket
import signal
import time
import Lib as lib

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
        loc = loc + "/GraphGen/output/MeasurableStdBenchmarkMeanAndSigma"
        retDict = {}
        with open(loc, "r") as stdFile:
            for line in stdFile:
                LineList = line.split(";")
                name = LineList[0].strip().split(".")[-1]
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
        EnvConnectInfo = EnvConnectInfo + "/training/EnvConnectInfo"
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
        return: string
        """
        if self.init == False:
            IP, Port = self.ReadEnvConnectInfo(WorkerID)
            self.EstablishTcpConnect(IP, Port)
            self.init = True
        fragments  = []
        while True:
            chunck = self.SOCKET.recv(1024)
            if not chunck:
                break
            fragments.append(chunck)
        return b"".join(fragments).decode('utf-8')

def sigint_handler(signum, frame):
    tcp = TcpClient()
    msg = "kill"
    for i in range(1,6): # from 1 to 5
        tcp.Send(WorkerID=i, Msg=msg)
    sys.exit(1)

if __name__ == '__main__':
    # register sigint handler
    signal.signal(signal.SIGINT, sigint_handler)
    prog = Programs()
    programDict = prog.getAvailablePrograms()
    keys = list(programDict.keys())
    tcp = TcpClient()
    #FIXME
    #for i in range(100):
    for key, value in programDict.items():
        workerID = 1
        start = time.time()
        # random choose a build target
        #target = random.choice(keys)
        target = key
        # get random 9 passes from 34 of them.
        #FIXME
        #passes = prog.genRandomPasses(34, 9)
        passes = ""
        # send to env-daemon
        msg = "target @ {} @ {}".format(target, passes)
        tcp.Send(WorkerID=workerID, Msg=msg)
        # get result
        retStr = tcp.Receive(WorkerID=workerID).strip()
        end = time.time()
        print("{} : {} : {}".format(target, retStr.strip(), end - start))
        if retStr == "Success":
            # get profiled data
            tcp.DestroyTcpConnection()
            tcp.Send(WorkerID=workerID, Msg="profiled @ {}".format(target))
            retStr = tcp.Receive(WorkerID=workerID)
            print(retStr.strip())
            # get features
            tcp.DestroyTcpConnection()
            tcp.Send(WorkerID=workerID, Msg="features")
            retStr = tcp.Receive(WorkerID=workerID)
            print(retStr.strip())
            print("----------------------------------------")
        tcp.DestroyTcpConnection()
    '''
    for name, info in programDict.items():
        print("{}: {}, {}".format(name, info[0], info[1]))
    '''
    '''
    for i in range(100):
        passes = prog.genRandomPasses(34, 9)
        print(passes)
    '''

