#!/usr/bin/env python3

import os, psutil, signal
import sys
import fcntl
import pytz
import time
from datetime import datetime
import multiprocessing
from multiprocessing import Queue
import subprocess, shlex

def getTaipeiTime():
    return datetime.now(pytz.timezone('Asia/Taipei')).strftime("%m-%d_%H-%M")

def check_PidAlive(pid):
    """
    return True if the pid is still working
    return False if the pid id dead
    """
    if pid != None:
        try:
            if os.waitpid(pid, os.WNOHANG) == (0,0):
                return True
            else:
                return False
        except OSError:
            pass
    return False

def KillProcesses(pid):
    '''
    kill all the children of pid and itself
    '''
    parent_pid = pid
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child.kill()
    except Exception as e:
        print("Failed to KillProcesses with pid={}\n Skip it.".format(pid))
        return
    parent.kill()

def KillChildren(pid):
    '''
    kill all the children of the pid except itself
    '''
    parent_pid = pid
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            try:
                child.kill()
            except Exception as e:
                pass
    except Exception as e:
        print("Failed to KillChildren with pid={}\nReasons:{}".format(pid, e))
        return

def KillPid(pid):
    '''
    kill the pid
    '''
    try:
        os.kill(pid, signal.SIGKILL)
    except Exception as e:
        print("KillPid() failed.\n reasons:{}".format(e))


def LimitTimeExec(LimitTime, Func, *args):
    """
    Input:
    1. LimitTime: is in the unit of secs.
    2. Func: must return a list that contains your return value
    3. args: pass into Func
    Return value:
    1. isKilled: killed by timing
    2. ret(int): from Func(args) to indicate success or not
    """
    ret = -1
    PrevWd = os.getcwd()
    isKilled = False
    WaitSecs = 0
    WaitUnit = 10
    ExecProc = multiprocessing.Process(target=Func, args=[args])
    # NOTE: SIGKILL will not kill the children
    # kill all its sub-process when parent is killed.
    ExecProc.daemon = True
    ExecProc.start()
    while True:
        date = getTaipeiTime()
        if ExecProc.is_alive():
            # log date to check liveness
            print("Alive at {}".format(date))
            time.sleep(WaitUnit)
            WaitSecs += WaitUnit
        else:
            # return the return code to indicate success or not
            ret = ExecProc.exitcode
            isKilled = False
            print("The command is finished at {} with exitcode={}, break.".format(date, ret))
            break
        if WaitSecs > LimitTime:
            if not ExecProc.is_alive():
                # if the work is done after the sleep
                continue
            # handle the processes twice, kill its children first
            KillChildren(ExecProc.pid)
            # with daemon flag, all children will be terminated
            ExecProc.terminate()
            KillPid(ExecProc.pid)
            # wait for a few secs
            ExecProc.join(10)
            if ExecProc.exitcode is None: # exitcode is None for unfinished proc.
                print("ExecProc.terminate() failed; Daemon handler exit.")
                sys.exit(0)
            isKilled = True
            ret = -1
            print("Achieve time limitation, kill it at {}.".format(getTaipeiTime()))
            break
    os.chdir(PrevWd)
    return isKilled, ret

def ExecuteCmd(WorkerID=1, Cmd="", Block=True):
    """
    return cmd's return code, STDOUT, STDERR
    """
    # Use taskset by default
    if Block:
        '''
        The taskset configuration depends on the hardware.
        If your computer is other than 8700K, you must customized it.
        Current configuration:
        intel 8700K:
            Core 0 as the "benchmark scheduler"
            Core 1~5 as the "worker" to run programs.
            Core 6~11 are not "real core", they are hardware threads shared with Core 0~5.
        '''
        CpuWorker = str((int(WorkerID) % 5) + 1)
        TrainLoc = os.getenv("LLVM_THESIS_TrainingHome", "Error")
        FullCmd = "taskset -c " + CpuWorker + " " + Cmd
        #print(FullCmd)
        p = subprocess.Popen(shlex.split(FullCmd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE)
        out, err = p.communicate()
        p.wait()
        return p.returncode, out, err
    else:
        print("TODO: non-blocking execute", file=sys.stderr)

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
        self.out(msg)
        #self.FileWriter("/tmp/PredictionDaemon.err", msg)

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

