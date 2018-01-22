#!/usr/bin/python3
import os
import sys
import Lib as lib

class ConnectInfoInit():
    def setupIptables(self, IpDict):
        '''
        This only need to be executed once for every boot.
        Input: IpDict = {WorkerID: [Ip, Ports]}
        '''
        initFile = "/tmp/PassPrediction-Init"
        initIptablesMsg = "Iptables-Initialized\n"
        isInitialized = False
        if os.path.exists(initFile):
            # if already exist, check what is initialized.
            with open(initFile, "r") as file:
                for line in file:
                    if line == initIptablesMsg:
                        isInitialized = True
                        print("Iptables are already initialized.")
                        print("Your previous input does not apply to iptables, but the EnvConnectionInfo is generated.")
                        print("Remove \"{}\" and try again to apply to the iptables.".format(initFile))
                file.close()
        if isInitialized == False:
            # check for permission to manipulate iptables
            if os.getuid() != 0:
                print("Your iptables cannot be initialized due to the permission problem.")
                print("Try run this script with sudo again.")
                sys.exit(1)
            with open(initFile, "a") as file:
                for worker, IpPortList in IpDict.items():
                    inputCmd = "sudo iptables -A INPUT -p tcp --dport {} -j ACCEPT".format(IpPortList[1])
                    outputCmd = "sudo iptables -A OUTPUT -p tcp --dport {} -j ACCEPT".format(IpPortList[1])
                    os.system(inputCmd)
                    os.system(outputCmd)
                isInitialized = True
                file.write(initIptablesMsg);
                file.close()
        if isInitialized:
            print("Corresponding Ip and Ports in Iptables are set.")
            print("\"$ sudo iptables -L\" can check the results")

    def genEnvConnectInfo(self, EnvConInfoLoc, WorkerIpPortDict={"1":["127.0.0.1", "56021"]}):
        with open(EnvConInfoLoc, "w") as file:
            file.write("workerID, RemoteEnv-ip, RemoteEnv-port\n")
            for ID, IpPortList in WorkerIpPortDict.items():
                content = "{}, {}, {}\n".format(ID, IpPortList[0], IpPortList[1])
                file.write(content)
            file.close()
        with open(EnvConInfoLoc, 'r') as file:
            generated = file.read()
            file.close()
        print("The generated results are:\n\n{} \n".format(generated))

    def UserPrompt(self):
        print("Please input the Ip and Ports-range of RemoteEnv.")
        print("All of the computers using this framework should using the same connection config.")
        print("Ex. \n\n127.0.0.1, 56021, 1\n140.111.192.1, 5566, 2\ndone\n\n")
        print("This will generate the following tables:")
        print("workerID, RemoteEnv-ip, RemoteEnv-port")
        print("1, 127.0.0.1, 56021")
        print("2, 140.111.192.1, 5566")
        print("3, 140.111.192.1, 5567")
        print("The format is :")
        print("[ip], [port start number], [how many workers for this IP with the starting port number]")
        print("\nNow, it is your turn:")

        inputList = []
        while(True):
            Input = input()
            if Input == "done":
                break
            inputList.append(Input)
        WorkerConut = 1
        retDict = {}
        for line in inputList:
            lineList = line.split(',')
            strippedLineList = []
            for ele in lineList:
                strippedLineList.append(ele.strip())
            for idx in range(int(strippedLineList[2])):
                retDict[str(WorkerConut)] = [strippedLineList[0], str(int(strippedLineList[1]) + idx)]
                WorkerConut += 1
        return retDict


if __name__ == '__main__':
    con = ConnectInfoInit()
    EnvConInfoLoc = os.getcwd() + '/../Connection/EnvConnectInfo'
    UserInput = con.UserPrompt()
    con.genEnvConnectInfo(EnvConInfoLoc, UserInput)
    ConInfo = lib.ConnectInfoService()
    IpDict = ConInfo.getConnectDict(EnvConInfoLoc)
    con.setupIptables(IpDict)

