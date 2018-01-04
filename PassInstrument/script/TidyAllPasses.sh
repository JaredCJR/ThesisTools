#!/bin/bash
source $LLVM_THESIS_InstrumentHome/script/Var.sh

# Cleanup
rm -rf $BackupDir $TidiedDir
mkdir -p $BackupDir $TidiedDir

# Backup passes
for p in "${AbsPathPasses[@]}"
do
  cp -f $p $BackupDir
  cp -f $p $TidiedDir
done

# Run tidy
for p in "${TidiedPassArr[@]}"
do
  bash $LLVM_THESIS_InstrumentHome/script/runTidy.sh $p
  echo "$p is tidied."
done

echo "Tidy Done."
echo "For Clang 5.0.1, clang-tidy has bugs."
echo "Please Fix NewGVN.cpp at line 2099 and 2100."
echo "The Semicolon is misplaced."
