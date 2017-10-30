#!/usr/bin/python3
import RandomGenerator as RG
import shlex
import subprocess as sp
import os
import time
from time import gmtime, strftime
import BenchmarkList as BL

class Executer:
    bl = BL.BenchmarkList()
    benchmark_build_run_list = bl.genList()
    repeat = bl.getRepeat()
    def run(self):
        TestingStart = time.perf_counter()
        localtime = time.strftime("%m%d-%H:%M", time.localtime())
        prev_cwd = os.getcwd()
        os.system("mkdir -p results_time")
        Result_FileLoc = prev_cwd + "/results_time/result_" + localtime
        ErrorResult_FileLoc = Result_FileLoc + "_Error"
        Result_File = open(Result_FileLoc, "w")
        Result_File.close()
        for i in range(self.repeat):
            print("Iteration Start-----------------------------------------")
            #generate pass set
            rg_driver = RG.Driver()
            #mean should between 0~1
            mean = (i + 1) / (self.repeat + 1)
            rg_driver.run(mean)

            #build benchmarks for this pass set
            for build_bench in self.benchmark_build_run_list:
                cwd = prev_cwd + "/" + build_bench[0].rstrip()
                os.chdir(cwd)
                print("Build Start*******************************************")
                print("clean=\"{}\"".format(build_bench[3]))
                try:
                    p = sp.Popen(shlex.split(build_bench[3]))
                    p.wait()
                except:
                    print("Clean the previous built failed. Why?")
                    Result_FileErr.write("----------------------------------\n")
                    Result_FileErr = open(ErrorResult_FileLoc, "a")
                    Result_FileErr.write(
                            "Clean Error:\"{}\"\n".format(build_bench[3]))
                    Result_FileErr.write("----------------------------------\n")
                    Result_FileErr.close()
                    
                print("build=\"{}\"".format(build_bench[1]))
                try:
                    p = sp.Popen(shlex.split(build_bench[1]))
                    p.wait()
                except:
                    print("Build with this combination error.")
                    file_loc = RG.Driver().InputSetLoc
                    target_file = open(file_loc, "r")
                    print(target_file.read())
                    print("-------------------------")
                    Result_FileErr.write("----------------------------------\n")
                    Result_FileErr = open(ErrorResult_FileLoc, "a")
                    Result_FileErr.write(
                            "Build Error:\"{}\"\n".format(build_bench[1]))
                    Result_FileErr.write(
                            "Build with this combination error:\"{}\"\n".format(target_file.read()))
                    Result_FileErr.write("----------------------------------\n")
                    Result_FileErr.close()
                    target_file.close()
                    continue
                print("Build End*******************************************")
                #Run built benchmarks
                for run_single in build_bench[2]:
                    #run command
                    print("<<<<<<  RUN=\"{}\"  >>>>>>".format(run_single))
                    period = 0.0
                    try:
                        start_time = time.perf_counter()
                        out = None
                        err = None
                        p = sp.Popen(shlex.split(run_single[1]),stdout = sp.PIPE, stderr= sp.PIPE)
                        out, err = p.communicate()
                        p.wait()
                        end_time = time.perf_counter()
                        period = end_time - start_time
                        #Verify expected output, strip out the newline characters
                        if out.rstrip().endswith(run_single[2].rstrip().encode('utf-8')):
                            print("<<<<<<  Verify Success  >>>>>>")
                        else:
                            print("Verify Failed:")
                            print("stdout=\"{}\"\nstderr=\"{}\"".format(
                                out.decode('utf-8'),err.decode('utf-8')))
                            print("Expected Last stdout={}".format(run_single[2]))
                            raise Exception
                    except:
                        print("Run the benchmark={} failed".format(run_single))
                        Result_FileErr = open(ErrorResult_FileLoc, "a")
                        Result_FileErr.write("----------------------------------\n")
                        Result_FileErr.write("Run the benchmark={} failed\n".format(run_single))
                        if (out is not None) and (err is not None):
                            Result_FileErr.write("stdout=\"{}\"\n\n stderr=\"{}\"\n".format(out.decode('utf-8'),err.decode('utf-8')))
                        else:
                            Result_FileErr.write("stdout or stderr is None type\n")
                        Result_FileErr.write("----------------------------------\n")
                        Result_FileErr.close()
                        continue
                    Result_File = open(Result_FileLoc, "a")
                    file_loc = RG.Driver().InputSetLoc
                    target_file = open(file_loc, "r")
                    Result_File.write("{},{},{}\n".format(run_single[0].rstrip(),
                        target_file.read().rstrip(), period))
                    target_file.close()
                    Result_File.close()
                os.chdir(prev_cwd)
            print("Iteration End-----------------------------------------")
        #Print Finishing Results
        os.chdir(prev_cwd)
        print("Done. Results written to \"{}\"".format(Result_FileLoc))
        TestingEnd = time.perf_counter()
        TestingTime = TestingEnd-TestingStart
        hours, seconds =  TestingTime // 3600, TestingTime % 3600
        minutes, seconds = seconds // 60, seconds % 60
        print("Testing Total Time = {}:{}:{}".format(int(hours), int(minutes), int(seconds)))



if __name__ == '__main__':
    execute = Executer()
    execute.run()
