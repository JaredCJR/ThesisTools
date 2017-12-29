#!/bin/bash
LLVMHeaders=${LLVM_THESIS_HOME}/include/llvm
SystemHeaders=`cat ${LLVM_THESIS_HOME}/ThesisTools/PassInstrument/script/SystemHeaders`
AdditionalHeaders=${LLVM_THESIS_HOME}/lib/Transforms/InstCombine

Headers=$SystemHeaders" -I"$LLVMHeaders" -I"$AdditionalHeaders
Input=$1

/usr/local/bin/clang-tidy -fix -config="{Checks: 'readability-braces-around-statements'}" $Input -- $Headers &> /dev/null
