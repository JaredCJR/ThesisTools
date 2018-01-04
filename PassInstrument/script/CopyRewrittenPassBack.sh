#!/bin/bash
source $LLVM_THESIS_InstrumentHome/script/Var.sh

iter=0
for p in "${RewrittenPassArr[@]}"
do
  cp -f "${RewrittenPassArr[$iter]}" "${AbsPathPasses[$iter]}"
  echo "${AbsPathPasses[$iter]} is overwritten"
  iter=$iter+1
done

echo "Copy Done."
