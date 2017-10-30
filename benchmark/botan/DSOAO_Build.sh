#!/bin/bash
default_thread=12
if [ -n "$1" ]; then
  thread=$1;
else
  thread=$default_thread;
fi

./configure.py --cc=clang
make -j$thread
