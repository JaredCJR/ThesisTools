#!/bin/bash
source $LLVM_THESIS_InstrumentHome/script/Var.sh

LLVMHeaders=${LLVM_THESIS_HOME}/include/llvm
SystemHeaders=`cat ${LLVM_THESIS_InstrumentHome}/script/SystemHeaders`
AdditionalHeaders=${LLVM_THESIS_HOME}/lib/Transforms/InstCombine
Headers=$SystemHeaders" -I"$LLVMHeaders" -I"$AdditionalHeaders

echo "-------------------------------"
echo "Assume \"TidyAllPasses.sh\" is already done."
sleep 3
# Clear previous database(rewritten log)
rm -f $Database/database
rm -f $Database/FeatureSize

# Copy for instrumenting them.
rm -rf $RewrittenDir
cp -r $TidiedDir $RewrittenDir

cd $LLVM_THESIS_InstrumentHome

#build
make

# Rewrite them
for p in "${RewrittenPassArr[@]}"
do
  AllPasses=$AllPasses" "$p
done
$LLVM_THESIS_InstrumentHome/PassRewriter $AllPasses -- $Headers

# Insert header and format them
for p in "${RewrittenPassArr[@]}"
do
  sed -i '1i #include "llvm/PassPrediction/PassPrediction-Instrumentation.h"' $p
  clang-format -style=LLVM -i $p
  echo "$p is rewritten."
done


cd -

# Record feature size
bash $LLVM_THESIS_InstrumentHome/script/FetchFeatureSize.sh

echo "Rewritter Done."
