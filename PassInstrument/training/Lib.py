#!/usr/bin/python3

import os
import sys
import fcntl


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
        self.FileWriter("/tmp/PredictionDaemon.err", msg)

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

