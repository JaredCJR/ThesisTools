#!/bin/bash
<<LoadingVars
Get several var: $Database, $BackupDir, $TidiedDir, $RewrittenDir
$PassesArr, $BaseNamePassArr, $AbsPathPasses
$TidiedPassArr, $RewrittenPassArr
LoadingVars

Database=$LLVM_THESIS_InstrumentHome/Database
BackupDir=$Database/OrigPasses
TidiedDir=$Database/TidiedPasses
RewrittenDir=$Database/RewrittenPasses

# Target Passes, path is relative to llvm/lib/Transform/
declare -a PassesArr=(
            "Instrumentation/PGOMemOPSizeOpt.cpp" 
            "InstCombine/InstructionCombining.cpp" 
            "Utils/SimplifyInstructions.cpp" 
            "Utils/LowerSwitch.cpp" 
            "Utils/Mem2Reg.cpp" 
            "Scalar/BDCE.cpp" 
            "Scalar/LoopDataPrefetch.cpp" 
            "Scalar/ConstantHoisting.cpp" 
            "Scalar/SROA.cpp" 
            "Scalar/GVNSink.cpp" 
            "Scalar/SCCP.cpp" 
            "Scalar/Scalarizer.cpp" 
            "Scalar/JumpThreading.cpp" 
            "Scalar/NaryReassociate.cpp" 
            "Scalar/MergedLoadStoreMotion.cpp" 
            "Scalar/DeadStoreElimination.cpp" 
            "Scalar/Sink.cpp" 
            "Scalar/EarlyCSE.cpp" 
            "Scalar/FlattenCFGPass.cpp" 
            "Scalar/DCE.cpp" 
            "Scalar/Reg2Mem.cpp" 
            "Scalar/PlaceSafepoints.cpp" 
            "Scalar/AlignmentFromAssumptions.cpp"
            "Scalar/PartiallyInlineLibCalls.cpp" 
            "Scalar/ADCE.cpp" 
            "Scalar/StraightLineStrengthReduce.cpp" 
            "Scalar/GVN.cpp" 
            "Scalar/TailRecursionElimination.cpp" 
            "Scalar/NewGVN.cpp" 
            "Scalar/GVNHoist.cpp" 
            "Scalar/ConstantProp.cpp" 
            "Scalar/Reassociate.cpp" 
            "Scalar/MemCpyOptimizer.cpp" 
            "Scalar/LowerExpectIntrinsic.cpp" 
            )
for p in "${PassesArr[@]}"
do
  BaseNamePassArr+=($(basename $p))
  AbsPathPasses+=($LLVM_THESIS_HOME/lib/Transforms/$p)
done

for p in "${BaseNamePassArr[@]}"
do
  TidiedPassArr+=($TidiedDir/$p)
  RewrittenPassArr+=($RewrittenDir/$p)
done

