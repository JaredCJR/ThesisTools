#!/usr/bin/env python3
import os, sys, signal
import threading
from queue import Queue
import Helpers as hp
import DPPO
import gym, gym_OptClang
import numpy as np

def sigterm_handler(signo, frame):
    """
    Avoid inherent the sigterm_handler from the parent process.
    """
    raise SystemExit(1)

def RestoreModel(OptClangLoc, RelativeLogDir, ModelName, Config):
    ppo = DPPO.PPO(gym.make('OptClang-v0').unwrapped,
          OptClangLoc+'/'+RelativeLogDir, ModelName,
          isTraining="N", # This is not bool, is str
          EP_MAX=Config['WorkerParameters']['EP_MAX'],
          GAMMA=Config['WorkerParameters']['GAMMA'],
          A_LR=Config['RL_Parameters']['A_LR'],
          C_LR=Config['RL_Parameters']['C_LR'],
          ClippingEpsilon=Config['RL_Parameters']['ClippingEpsilon'],
          UpdateDepth=Config['RL_Parameters']['UpdateDepth'])
    return ppo

def ConvertToArray(FeatureStr):
    retVec = []
    for num in FeatureStr.split():
        retVec.append(int(num.split(',')[0]))
    array = np.asarray(retVec)
    return array

def ChoosePass(RL_ChooseAction_Func, state, PassHistory):
    """
    gym-OptClang and DPPO:   pass range --> 0~33
    Modified Clang:          pass range --> 1~34
    We need to add 1 to convert the range.
    """
    retPass = RL_ChooseAction_Func(state, PassHistory)
    #print("RL_ChooseAction_Func ret={}".format(retPass))
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
    RelativeLogDir = 'test'
    ModelName = 'model.ckpt'
    # read json config
    Config = hp.LoadJsonConfig(OptClangLoc+'/config.json')
    # use the config to restore model
    ppo = RestoreModel(OptClangLoc, RelativeLogDir, ModelName, Config)

    idx = 0
    PassHistory = {}
    # Main Loop
    while True:
        '''
        Assuming the tfServer only serve one function once a time.
        avoid repeated pass every 9 iters.
        '''
        if not IpcQueue_Features.empty():
            FeatureStr = IpcQueue_Features.get()
            '''
            use model to predict retPass
            retPass must be integer
            '''
            state = ConvertToArray(FeatureStr)
            retPass = ChoosePass(ppo.choose_action, state, PassHistory)
            IpcQueue_Pass.put(retPass, block=True, timeout=None)
            idx += 1
            if idx == 9:
                idx = 0
                PassHistory = {}
