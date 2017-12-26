#!/usr/bin/python3
import os
import sys
import shutil
import progressbar
import subprocess
import shlex

class Instrumentation:
    # Realative path to 'llvm/lib/Transforms/'
    InputList = [ 
            'Instrumentation/PGOMemOPSizeOpt.cpp',
            'InstCombine/InstructionCombining.cpp',
            'Utils/SimplifyInstructions.cpp',
            'Utils/LowerSwitch.cpp',
            'Utils/Mem2Reg.cpp',
            'Scalar/BDCE.cpp',
            'Scalar/LoopDataPrefetch.cpp',
            'Scalar/ConstantHoisting.cpp',
            'Scalar/SROA.cpp',
            'Scalar/GVNSink.cpp',
            'Scalar/SCCP.cpp',
            'Scalar/Scalarizer.cpp',
            'Scalar/JumpThreading.cpp',
            'Scalar/NaryReassociate.cpp',
            'Scalar/MergedLoadStoreMotion.cpp',
            'Scalar/DeadStoreElimination.cpp',
            'Scalar/Sink.cpp',
            'Scalar/EarlyCSE.cpp',
            'Scalar/FlattenCFGPass.cpp',
            'Scalar/DCE.cpp',
            'Scalar/Reg2Mem.cpp',
            'Scalar/PlaceSafepoints.cpp',
            'Scalar/AlignmentFromAssumptions.cpp',
            'Scalar/PartiallyInlineLibCalls.cpp',
            'Scalar/ADCE.cpp',
            'Scalar/StraightLineStrengthReduce.cpp',
            'Scalar/GVN.cpp',
            'Scalar/TailRecursionElimination.cpp',
            'Scalar/NewGVN.cpp',
            'Scalar/GVNHoist.cpp',
            'Scalar/ConstantProp.cpp',
            'Scalar/Reassociate.cpp',
            'Scalar/MemCpyOptimizer.cpp',
            'Scalar/LowerExpectIntrinsic.cpp'
            ]
    TestInputList = [ 
            'Utils/LowerSwitch.cpp',
            ]

    def AddBraces(self, InputFile, OutputFile):
        os.system("./script/runTidy.sh {}".format(InputFile))
        os.system("clang-format -style=LLVM {} > {}".format(InputFile, OutputFile))

    def runRewriter(self, InputFile, OutputFile, Headers):
        '''
        The -I/path/to/lib must comes from compiler
        ex. $ clang -E -Wp,-v - < /dev/null
        '''
        os.system("./PassRewriter {} -- {} > {}".format(InputFile, Headers, OutputFile))

    def runAll(self):
        # Make sure the env exist.
        LLVMsrc = os.getenv('LLVM_THESIS_HOME')
        # Path for files
        BaseDir = '/tmp/PassInstrumentation'
        InputDir = BaseDir + '/input'
        OutputDir_ClangFormat = BaseDir + '/output-ClangFormat'
        OutputDir_Rewriter = BaseDir + '/output-Rewriter'
        LLVMInclude = LLVMsrc + '/include/llvm'
        LLVMAdditional = LLVMsrc + '/lib/Transforms/InstCombine'
        # build dir tree
        if os.path.isdir(BaseDir):
            shutil.rmtree(BaseDir)
        os.makedirs(BaseDir)
        os.makedirs(InputDir)
        os.makedirs(OutputDir_ClangFormat)
        os.makedirs(OutputDir_Rewriter)
        # headers for tidy and rewriter which use libtooling
        Headers = "-std=c++11 -I/usr/local/include -I/usr/local/lib/clang/5.0.1/include -I/usr/include/x86_64-linux-gnu -I/usr/include -I{} -I{}".format(LLVMInclude, LLVMAdditional)
        # Time to rewrite them
        bar = progressbar.ProgressBar(max_value=len(self.InputList), redirect_stdout=True)
        i = 0
        #for path in self.TestInputList:
        for path in self.InputList:
            # setup files related var
            AbsPath = LLVMsrc + '/lib/Transforms/' + path
            FileName = path.split('/')[-1]
            InputFile = InputDir + '/' + FileName
            OutputFile_ClangFormat = OutputDir_ClangFormat + '/' + FileName
            OutputFile_Rewriter = OutputDir_Rewriter + '/' + FileName
            # bar
            bar.update(i)
            i += 1
            # copy for rewriting
            os.system("cp {} {}".format(AbsPath, InputFile))
            # Make sure all braces are located properly
            self.AddBraces(InputFile, OutputFile_ClangFormat)
            # Rewrite it
            self.runRewriter(OutputFile_ClangFormat, OutputFile_Rewriter, Headers)
            # Copy back for testing
            os.system("cp {} {}".format(OutputFile_Rewriter, AbsPath))
        print("All Done.")
            


if __name__ == '__main__':
    Instru = Instrumentation()
    Instru.runAll()
