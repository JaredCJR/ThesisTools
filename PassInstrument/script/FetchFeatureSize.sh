#!/bin/bash
source $LLVM_THESIS_InstrumentHome/script/Var.sh

LastLine=`awk '/./{line=$0} END{print line}' $Database/RewrittenLog`
# split line with "," and get the last feature ID
IFS=',' read -ra Line <<< "$LastLine"
Iter=0
FeatureSize=0
for i in "${Line[@]}";
do
  if [ $Iter = 2 ]; then
    FeatureSize=$(($i + 1))
  fi
  Iter=$(($Iter + 1))
done

echo $FeatureSize > $Database/FeatureSize
