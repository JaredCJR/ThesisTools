#!/usr/bin/env python3
import os, sys, signal
import threading

def sigterm_handler(signo, frame):
    """
    Due  towe calltfServer 
    """
    raise SystemExit(1)

def tfServer(WorkerID):
    signal.signal(signal.SIGTERM, sigterm_handler)
    pid = os.getpid()
    print("tfServer initialzed with pid={} and WorkerID={}.".format(pid, WorkerID))
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

    # Main Loop
    while True:
        pass
    print("tfServer closed.")
