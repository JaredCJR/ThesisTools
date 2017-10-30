#!/bin/bash
default_thread=12
if [ -n "$1" ]; then
  thread=$1;
else
  thread=$default_thread;
fi

rm -rf ./build
prev_wd=$(pwd)
mkdir build && cd build
CC=clang CXX=clang++ cmake ../
make -j$thread
cd "$prev_wd"
