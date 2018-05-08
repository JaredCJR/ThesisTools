#!/bin/bash
LLVMHeaders=${LLVM_THESIS_HOME}/include/llvm
SystemHeaders=`cat SystemHeaders`
Headers=$SystemHeaders" -I"$LLVMHeaders

#build rewriter
make -j4

# Make sure your test-suite is on "RewardPolicy2" branch
TestSuiteBase=~/workspace/llvm-official-test/test-suite/
Candidate_1=SingleSource/Benchmarks/Dhrystone/
Candidate_2=SingleSource/Benchmarks/CoyoteBench
Candidate_3=MultiSource/Applications/oggenc
Candidate_4=MultiSource/Applications/sqlite3
Candidate_5=MultiSource/Applications/aha
#TODO: you have to assign the Candidate_x by yourself.
# Target root dir(source dir of c/cpp files)
input_dir=$TestSuiteBase$Candidate_5
# Gather all source files
C_SRC_LIST=`find $input_dir -type f -name '*.c' -printf '%p '`
CXX_SRC_LIST=`find $input_dir -type f -name '*.cpp' -printf '%p '`
# Get the header dir
ProgHeaders_DIR=$input_dir

for src in $C_SRC_LIST" "$CXX_SRC_LIST
do
    # this will rewrite the original file
    if [[ $src = *[!\ ]* ]] ; then
        # "\$src contains characters other than space"
        $LLVM_THESIS_InstrumentHome/training/RewardPolicy2-Tools/RewriteWithTimeApi $src -- $Headers" -I"$ProgHeaders_DIR
        # insert header, make sure you already run deployLib.sh
        sed -i '1i #include <thesis_api.h>' $src
    fi
done

echo "Rewritter done."
echo "Make sure you know what this script has done."
echo "Current rewriter for inseting APIs has bugs, and most of the bugs are for C++"
