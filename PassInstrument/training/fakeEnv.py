#!/usr/bin/python3
import os
import sys
import random
import socket

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
        EnvConnectDict = {}
        with open(EnvConnectInfo, "r") as file:
            # skip first line
            file.readline()
            for line in file:                                                                                     
                info = line.split(",")
                EnvConnectDict[info[0]] = [info[1].strip(), info[2].strip()]                                                    
            file.close()
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
        # The buffer size may cause bugs?
        return self.SOCKET.recv(1024).decode('utf-8')

if __name__ == '__main__':
    prog = Programs()
    programDict = prog.getAvailablePrograms()
    keys = list(programDict.keys())
    tcp = TcpClient()
    for i in range(1):
        # random choose a build target
        target = random.choice(keys)
        # get random 9 passes from 34 of them.
        passes = prog.genRandomPasses(34, 9)
        # send to env-daemon
        msg = "{} @ {}".format(target, passes)
        #msg = "{} @ {}".format(target, "100")
        # NOTICE: WorkerID
        tcp.Send(WorkerID=1, Msg=msg)
        # get result
        retStatus = tcp.Receive(WorkerID=1)
        print(retStatus)
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

