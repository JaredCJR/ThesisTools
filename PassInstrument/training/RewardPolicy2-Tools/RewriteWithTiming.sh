#!/bin/bash
LLVMHeaders=${LLVM_THESIS_HOME}/include/llvm
SystemHeaders=`cat SystemHeaders`
#AdditionalHeaders=${LLVM_THESIS_HOME}/lib/Transforms/InstCombine
Headers=$SystemHeaders" -I"$LLVMHeaders

#build
make -j4

input=test.c
#FIXME: cpp need "-std=c++11 " in $Headers
$LLVM_THESIS_InstrumentHome/training/RewardPolicy2-Tools/MeasuringFuncTime $input -- $Headers

echo "Rewritter Done."
