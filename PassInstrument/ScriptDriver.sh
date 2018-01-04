#!/bin/bash

RunTidy="bash $LLVM_THESIS_InstrumentHome/script/TidyAllPasses.sh"
RunRewritter="bash $LLVM_THESIS_InstrumentHome/script/InstrumentTidiedPasses.sh"
RunCopyBack="bash $LLVM_THESIS_InstrumentHome/script/CopyRewrittenPassBack.sh"

echo "Option 1. only need to be executed once and you may need to fix the output by yourself."
echo "Ex. Database/TidiedPasses/NewGVN.cpp line 2099 and 2100"
echo ""
echo "[Option]1. A clang-tidy wrapped script to help the rewritter run correctly."
echo "[Option]2. Run rewritter with clang-format to insert instrumentation APIs into the passes."
echo "[Option]3. Copy the rewritten passes back to your llvm source."
echo ""
echo "Please enter option:"

select opt in "1" "2" "3"; do
    case $opt in
        1 ) $RunTidy; break;;
        2 ) $RunRewritter; break;;
        3 ) $RunCopyBack; break;;
    esac
done
