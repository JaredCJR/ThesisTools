#!/usr/bin/env python3
import os, sys, signal
import threading
from queue import Queue
import Helpers as hp
import PPPO
import gym, gym_OptClang
import numpy as np

def sigterm_handler(signo, frame):
    """
    Avoid inherent the sigterm_handler from the parent process.
    """
    raise SystemExit(1)

def RestoreModel(OptClangLoc, RelativeLogDir, ModelName, Config):
    ppo = PPPO.PPO(gym.make('OptClang-v0').unwrapped,
          OptClangLoc+'/'+RelativeLogDir, ModelName,
          isTraining="N", # This is not bool, is str
          EP_MAX=Config['WorkerParameters']['EP_MAX'],
          GAMMA=Config['WorkerParameters']['GAMMA'],
          A_LR=Config['RL_Parameters']['A_LR'],
          C_LR=Config['RL_Parameters']['C_LR'],
          L1Neurons=Config['RL_Parameters']['L1Neurons'],
          L2Neurons=Config['RL_Parameters']['L2Neurons'],
          ClippingEpsilon=Config['RL_Parameters']['ClippingEpsilon'],
          UpdateDepth=Config['RL_Parameters']['UpdateDepth'])
    return ppo

def ConvertToArray(FeatureStr):
    retVec = []
    for num in FeatureStr.split():
        retVec.append(int(num.split(',')[0]))
    array = np.asarray(retVec)
    return array

def DebugRecord(DebugRec, FuncName, retPass):
    """
    debugging only.
    You must remove the log file manually before validate
    """
    if FuncName not in DebugRec:
        DebugRec[FuncName] = []
    DebugRec[FuncName].append(str(retPass))
    if len(DebugRec[FuncName]) == 9:
        with open('/tmp/PassPrediction-debug-tfServer', 'a') as f:
            f.write(FuncName + ":")
            for pa in DebugRec[FuncName]:
                f.write(pa + ',')
            f.write('\n')
            f.close()
        DebugRec[FuncName] = []
        DebugRec.pop(FuncName, "None")


def ChoosePass(RL_ChooseAction_Func, State, FuncName, FunctionPassRec, DebugRec):
    """
    gym-OptClang and PPPO:   pass range --> 0~33
    Modified Clang:          pass range --> 1~34
    We need to add 1 to convert the range.
    """
    # create PassHistory for FuncName
    if FuncName not in FunctionPassRec:
        FunctionPassRec[FuncName] = {}
    # call agent to predict
    retPass = RL_ChooseAction_Func(State, FunctionPassRec[FuncName])
    '''
    # debugging purpose with tools/clang/lib/CodeGen/BackendUtil.cpp for race condition
    # e.g. The tcp port cannot serve multiple processes once a time.
    # It does not know which receiver is the right one.
    DebugRecord(DebugRec, FuncName, retPass+1)
    '''
    # if the pass meet the threshold, remove its history to keep memory.
    if len(FunctionPassRec[FuncName].keys()) == 9:
        FunctionPassRec.pop(FuncName, "None")
        #print("Last pass={}".format(retPass+1))
    return retPass + 1

def tfServer(WorkerID, IpcQueue_Features, IpcQueue_Pass):
    """
    Keep tensorflow model for use.
    Use environment var("PPO_OptClang") to set the dir of "PPO-OptClang"
    Set the var("ModelName") below to choose the trained model.
    """
    signal.signal(signal.SIGTERM, sigterm_handler)
    pid = os.getpid()
    print("tfServer initialzed with pid={} and WorkerID={}.".format(pid, WorkerID))
    # the pidFile is not necessary, but it can be used to check the process existence.
    pidFile = "/tmp/PredictionDaemon-tfServer-{}.pid".format(WorkerID)
    try:
        if os.path.exists(pidFile):
            with open(pidFile, 'r') as f:
                # the main process will kill tfServer, we do not need to do this here.
                #os.kill(int(f.read()), signal.SIGTERM)
                os.remove(pidFile)
                f.close()
    except Exception as e:
        print("Kill or remove previous tfServer pidFile failed:\n{}".format(e))
    with open(pidFile, 'w') as f:
        f.write(str(pid))

    '''
    restore RL model
    '''
    OptClangLoc = os.getenv('PPO_OptClang', "PPO_OptClang:not set")
    RelativeLogDir = 'inference-agent'
    ModelName = 'model.ckpt'
    # read json config
    Config = hp.LoadJsonConfig(OptClangLoc+'/config.json')
    # use the config to restore model
    ppo = RestoreModel(OptClangLoc, RelativeLogDir, ModelName, Config)
    # record the pass applied for each function
    FunctionPassRec = {}
    DebugRec = {}
    # Main Loop
    while True:
        '''
        Assuming the tfServer only serve one function once a time.
        avoid repeated pass every 9 iters.
        '''
        if not IpcQueue_Features.empty():
            FeatureStr = IpcQueue_Features.get()
            Inputs = FeatureStr.split('@')
            FuncName = Inputs[0].strip()
            FuncFeatures = Inputs[1].strip()
            '''
            use model to predict retPass
            retPass must be integer
            '''
            state = ConvertToArray(FuncFeatures)
            retPass = ChoosePass(ppo.choose_action, state, FuncName, FunctionPassRec, DebugRec)
            IpcQueue_Pass.put(retPass, block=True, timeout=None)
