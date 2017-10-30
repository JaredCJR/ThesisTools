#!/usr/bin/python3
import multiprocessing

class BenchmarkList:
    # numbers of random pass set execution
    repeat = 1 
    thread_num = multiprocessing.cpu_count() - 1
    DefaultBuild = "./DSOAO_Build.sh" + " " + str(thread_num)

    #CANNOT be called from outside
    def BenchmarkNameHelper(BenchmarkName, Cmd, Iteration, SubCmd, VerifyMsg):
        return [BenchmarkName + "-" + SubCmd, Cmd + " " + str(Iteration) + " " + SubCmd, VerifyMsg]

    """
    path is relative to "$LLVM_THESIS_RandomHome"
     ["directory path", "build command", [available benchmarks commands], "clean command"]
     [available benchmarks commands] can be split into three parts:
                                    ["label name", "commands", "expected last outputs"]
    """
    benchmark_build_run_list = [
        #Test
        ["../../benchmark/helloworld" ,"clang -O1 -o hello hello.c", [ ["hello", "./hello", "function 2"], ["ls","ls", "hello.c"], ] "rm hello"],

        #Botan
        ["../../benchmark/botan" , DefaultBuild, [ ["botan-all", "./botan-test", "all tests ok"], ], "make clean"],

        #cpp-serializers
        ["../../benchmark/cpp-serializers" , DefaultBuild, [ BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "thrift-binary", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "thrift-compact", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "protobuf", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "boost", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "msgpack", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "cereal", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "avro", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "capnproto", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "flatbuffers", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "yas", "milliseconds"), BenchmarkNameHelper("cpp-serializers", "./build/benchmark", 100000, "yas-compact", "milliseconds"), ], "rm -rf ./build"],

        #TastyLib
        ["../../benchmark/TastyLib" , DefaultBuild, [ ["TastyLib-benchmark_AVLTree", "./bin/benchmark_AVLTree", "finished."], ["TastyLib-benchmark_DoublyLinkedList", "./bin/benchmark_DoublyLinkedList", "finished."], ["TastyLib-benchmark_BinaryHeap", "./bin/benchmark_BinaryHeap", "finished."], ["TastyLib-benchmark_MD5", "./bin/benchmark_MD5", "finished."], ["TastyLib-benchmark_Sort", "./bin/benchmark_Sort", "finished."], ], "rm -rf ./build"],

        #LLVM test-suite special cases
        ["../../../test-suite/build/MultiSource/Benchmarks/mafft" , "/home/jrchang/workspace/llvm/DSOAO/benchmark/SpecialCases/mafft/DSOAO_Build.sh " + str(thread_num), [ ["mafft-pairlocalalign", "/home/jrchang/workspace/llvm/DSOAO/benchmark/SpecialCases/mafft/DSOAO_Run.sh", "-1.999, -0.099, -0.099"], ], "make clean"],
    ]

    def genList(self):
        return self.benchmark_build_run_list

    def getRepeat(self):
        return self.repeat

