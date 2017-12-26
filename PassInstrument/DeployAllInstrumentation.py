#!/usr/bin/python3
import os
import sys
import shutil
import progressbar

class Instrumentation:
    # Realative path to 'llvm/lib/Transforms/'
    InputList = [ \
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
    def AddBraces(self, InputFile, OutputFile, LLVMInclude):
        os.system("clang-tidy -fix -config=\"{{Checks: \'readability-braces-around-statements\'}}\" {} -- -I{} -std=c++11 &> /dev/null".format(InputFile, LLVMInclude))
        os.system("clang-format -style=LLVM {} > {}".format(InputFile, OutputFile))

    def runRewriter(self, InputFile, OutputFile, LLVMInclude):
        '''
        The -I/path/to/lib must comes from compiler
        ex. $ gcc-7 -E -Wp,-v - < /dev/null
        '''
        os.system("./PassRewriter {} -- -std=c++11 -I/usr/lib/gcc/x86_64-linux-gnu/7/include -I/usr/local/include -I/usr/lib/gcc/x86_64-linux-gnu/7/include-fixed -I/usr/include/x86_64-linux-gnu -I/usr/include -I{} > {}".format(InputFile, LLVMInclude, OutputFile))

    def runAll(self):
        # Make sure the env exist.
        LLVMsrc = os.getenv('LLVM_THESIS_HOME')
        # Path for files
        BaseDir = '/tmp/PassInstrumentation'
        InputDir = BaseDir + '/input'
        OutputDir_ClangFormat = BaseDir + '/output-ClangFormat'
        OutputDir_Rewriter = BaseDir + '/output-Rewriter'
        LLVMInclude = LLVMsrc + '/include/llvm'
        # build dir tree
        if os.path.isdir(BaseDir):
            shutil.rmtree(BaseDir)
        os.makedirs(BaseDir)
        os.makedirs(InputDir)
        os.makedirs(OutputDir_ClangFormat)
        os.makedirs(OutputDir_Rewriter)
        # Time to rewrite them
        bar = progressbar.ProgressBar(max_value=len(self.InputList), redirect_stdout=True)
        i = 0
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
            self.AddBraces(InputFile, OutputFile_ClangFormat, LLVMInclude)
            # Rewrite it
            self.runRewriter(OutputFile_ClangFormat, OutputFile_Rewriter, LLVMInclude)
            # Copy back for testing
            os.system("cp {} {}".format(OutputFile_Rewriter, InputFile))
        print("All Done.")
            


if __name__ == '__main__':
    Instru = Instrumentation()
    Instru.runAll()
