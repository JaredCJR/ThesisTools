#!/usr/bin/env python3
import os, sys, signal
import threading
from queue import Queue
import Helpers as hp
import DPPO
import gym, gym_OptClang

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

def tfServer(WorkerID, IpcQueue):
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

    #TODO: restore model
    OptClangLoc = os.getenv('PPO_OptClang', "PPO_OptClang:not set")
    RelativeLogDir = 'test'
    ModelName = 'model.ckpt'
    # read json config
    Config = hp.LoadJsonConfig(OptClangLoc+'/config.json')
    # use the config to restore model
    ppo = RestoreModel(OptClangLoc, RelativeLogDir, ModelName, Config)

    # Main Loop
    while True:
        if not IpcQueue.empty():
            FeatureStr = IpcQueue.get()
            #TODO: use model to predict retPass
            #TODO: avoid pass repeating every 9 iters.
            retPass = 1 # FIXME
            # retPass must be integer
            IpcQueue.put(retPass, block=True, timeout=None)
