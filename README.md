How to clone:
=====================
```
cd llvm-source/
git clone [this-repo] THESIS
```

Add below environment variables to your .bashrc:
------------------------------------------------------

* OS: Ubuntu 16.04 64 bit

```
#if you want lit to get these env, you need to modify "llvm-thesis/utils/lit/lit/TestingConfig.py"
export LLVM_THESIS_HOME=$HOME/workspace/llvm-thesis
export LLVM_THESIS_RandomHome=$LLVM_THESIS_HOME/ThesisTools/RandomSelect
export LLVM_THESIS_InstrumentHome=$LLVM_THESIS_HOME/ThesisTools/PassInstrument
export LLVM_THESIS_TrainingHome=$LLVM_THESIS_InstrumentHome/training
export LLVM_THESIS_TestSuite=$LLVM_THESIS_HOME/test-suite/build
export LLVM_THESIS_Random_LLVMTestSuiteScript=$LLVM_THESIS_RandomHome/LLVMTestSuiteScript
export LLVM_THESIS_Random_LLVMTestSuite_Results=$LLVM_THESIS_Random_LLVMTestSuiteScript/results
export LLVM_THESIS_lit="$LLVM_THESIS_HOME/utils/lit/lit.py"
export PYTHONPATH=$LLVM_THESIS_Random_LLVMTestSuiteScript:$LLVM_THESIS_RandomHome:$PYTHONPATH
alias lit=$LLVM_THESIS_lit  #this lit is modified to read the above env

# Make sure $clang++ and $clang are using your build
export PATH=$LLVM_THESIS_HOME/build-release-gcc7/bin:$PATH
```

* How does these environment variable be gotten in PyActor?
    * You may want to take a look at `llvm/utils/lit/lit/TestingConfig.py`



How to use "LLVMTestSuiteScript"
------------------------------------------------------

* Assumption
  * test-suite is cloned at `llvm/test-suite`
  * Python 3 and related packages
    * For example:
      * pip3 install progressbar2
```
source ~/.bashrc
cd $LLVM_THESIS_Random_LLVMTestSuiteScript
cd PyActor/WithStdin
make
cd -
cd PyActor/WithoutStdin
make
cd -
cd DropCache/
cat README
(follow the README guide)

cd -
./LitDriver.py [Standard | Random | Selected.SingleCore | Random-FunctionLevel]
[
 "Standard" must with official Clang-5.0 |
 "Random" must with Benchmark-Level Thesis-Clang-5.0 |
 "Selected.SingleCore" must with official Clang-5.0 to show that proper multi-thread does not affect the experiments.
 "Random-FunctionLevel" must with Function-Level Thesis-Clang-5.0
]

```
* `Benchmark-Level Thesis-Clang-5.0` is the branch of `RandomSelect-BenchmarkLevel` in JaredCJR/llvm and JaredCJR/clang
* `Function-Level Thesis-Clang-5.0` is the branch of `RandomSelect-FunctionLevel` in JaredCJR/llvm and JaredCJR/clang
    * `$ ./PredictionDaemon.py start` and `$ ./PredictionDaemon.py stop` may be necessary.

* Both of two `Thesis-Clang-5.0` must use the branch `thesis_50` of JaredCJR/test-suite
* `ThesisTools` always need to be the latest version for all branches

If lit failed, how to see the program output message?
------------------------------------------------------------
* The original lit will remove the ".test.output" file.
  * The lit in our version already modified to leave it there for debugging.
```
cd llvm-source/test-suite/build/path-to-your-target-build/
lit XXX.test # run again to produce the error message
cat Output/XXX.test.out # This is what you want.
```
