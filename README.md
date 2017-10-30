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
export LLVM_THESIS_RandomHome=$LLVM_THESIS_HOME/ThesisTools/random_select
export LLVM_THESIS_TestSuite=$LLVM_THESIS_HOME/test-suite/build
export LLVM_THESIS_Random_LLVMTestSuiteScript=$LLVM_THESIS_RandomHome/LLVMTestSuiteScript
export LLVM_THESIS_Random_LLVMTestSuite_Results=$LLVM_THESIS_Random_LLVMTestSuiteScript/results
export LLVM_THESIS_lit="$LLVM_THESIS_HOME/utils/lit/lit.py"
export PYTHONPATH=$LLVM_THESIS_Random_LLVMTestSuiteScript:$LLVM_THESIS_RandomHome:$PYTHONPATH
alias lit=$LLVM_THESIS_lit  #this lit is modified to read the above env
```


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
./LitDriver.py
```
