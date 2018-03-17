#!/bin/bash

# If failed, try again!
# Repeat it at least three times.
rm -rf /tmp/PredictionDaemon
rm -f /tmp/PredictionDaemon.err

worker=$1

echo "Make sure your environment variable are properly set. e.g. $LLVM_THESIS_HOME"

function RestartDaemon {
	rm -f /tmp/PredictionDaemon-Clang-$1.log
	rm -f /tmp/PredictionDaemon-Env-$1.log
	echo "========================================"
	python3 ./PredictionDaemon.py stop $1
	echo "========================================"
	python3 ./PredictionDaemon.py start $1
	echo "========================================"
}

if [ "$worker" == "all" ]; then
  for i in {1..5};
  do
    RestartDaemon $i
  done
else
    echo "Common Usage: $ ./DaemonStart.sh all"
    echo "If you only want to start single worker: $ ./DaemonStart.sh [ID in number]"
    RestartDaemon $worker
fi

