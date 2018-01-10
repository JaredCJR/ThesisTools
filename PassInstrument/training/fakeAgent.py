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
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SOCKET.connect((IP, Port))

    def DestroyTcpConnection(self, IP, Port):
        self.SOCKET.close()

    def ReadAgentConnectInfo(self, WorkerID):
        """
        return IP(string), Port(number)
        """
        AgentConnectInfo = os.getenv("LLVM_THESIS_InstrumentHome", "Error")
        if AgentConnectInfo == "Error":
            print("$LLVM_THESIS_InstrumentHome is not defined.", file=sys.stderr)
            sys.exit(1)
        AgentConnectInfo = AgentConnectInfo + "/training/AgentConnectInfo"
        AgentConnectDict = {}
        # FIXME: the first line need to skip
        with open(AgentConnectInfo, "r") as file:
            file.readline()
            for line in file:                                                                                     
                info = line.split(",")
                AgentConnectDict[info[0]] = [info[1].strip(), info[2].strip()]                                                    
            file.close()
        return AgentConnectDict[str(WorkerID)][0], int(AgentConnectDict[str(WorkerID)][1])

    def Send(self, WorkerID, Msg):
        """
        input format:
        WorkerID: number
        Msg: string
        """
        if self.init == False:
            IP, Port = self.ReadAgentConnectInfo(WorkerID)
            self.EstablishTcpConnect(IP, Port)
            self.init = True
        self.SOCKET.send(Msg.encode('utf-8'))

if __name__ == '__main__':
    prog = Programs()
    programDict = prog.getAvailablePrograms()
    passes = prog.genRandomPasses(34, 9)
    '''
    for name, info in programDict.items():
        print("{}: {}, {}".format(name, info[0], info[1]))
    '''
    '''
    for i in range(100):
        passes = prog.genRandomPasses(34, 9)
        print(passes)
    '''
    tcp = TcpClient()
    tcp.Send(1, "fakeAgent test\nsecond line\nthird line =)\n")

