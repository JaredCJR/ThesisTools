#!/usr/bin/python3
import inspect
import os
import sys
import ServiceLib as sv


if __name__ == '__main__':
    actor = sv.PyActorService()
    realActor = actor.Executor(' '.join(str(arg) for arg in sys.argv[1:]))
    realActor.run(inspect.getfile(inspect.currentframe()), BoolWithStdin=False)
