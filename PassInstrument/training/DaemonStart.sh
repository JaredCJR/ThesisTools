#!/bin/bash

# If failed, try again!
# Repeat it at least three times.
rm -rf /tmp/PredictionDaemon
rm -f /tmp/PredictionDaemon.err

worker=$1

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
    RestartDaemon $worker
fi

