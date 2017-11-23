#!/usr/bin/python3
import LitMimic as lm
import ServiceLib as sv
import os
import sys
import glob
import multiprocessing
import shlex
import shutil
import subprocess as sp
import progressbar
import smtplib
import RandomGenerator as RG
from random import shuffle
import re
import time
import psutil
import signal

class LitRunner:
    def ExecCmd(self, cmd, ShellMode=False, NeedPrintStderr=True, SanityLog=False):
        Log = sv.LogService()
        err = None
        try:
            #Execute cmd
            p = sp.Popen(shlex.split(cmd), shell=ShellMode, stdout=sp.PIPE, stderr= sp.PIPE)
            out, err = p.communicate()
            p.wait()
            if out is not None:
                Log.out(out.decode('utf-8'))
                if SanityLog == True:
                    Log.sanityLog(out.decode('utf-8'))
            if err is not None:
                errMsg = err.decode('utf-8')
                Log.err(errMsg)
                ErrMatch = re.compile('make:.*Error')
                for line in errMsg.splitlines():
                    if ErrMatch.match(errMsg):
                        ps = PassSetService()
                        ps.RecordBuildFailedPassSet()
            if NeedPrintStderr and err is not None:
                Log.outNotToFile(err.decode('utf-8'))
        except Exception as e:
            Log.err("----------------------------------------------------------\n")
            Log.err("Exception= {}".format(str(e)) + "\n")
            Log.err("Command error: {}\n".format(cmd))
            if err:
                Log.err("Error Msg= {}\n".format(err.decode('utf-8')))
            Log.err("----------------------------------------------------------\n")

    def CmakeTestSuite(self):
        time = sv.TimeService()
        time.DelTimeStamp()
        pwd = os.getcwd()
        path = os.getenv('LLVM_THESIS_TestSuite', 'Err')
        if path == 'Err':
            sys.exit("Error with get env: $LLVM_THESIS_TestSuite\n")
        if os.path.exists(path):
            shutil.rmtree(path)

        os.makedirs(path)
        os.chdir(path)
        CmakeFile = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results') + "/CmakeLog"
        os.system("CC=clang CXX=clang++ cmake ../ | tee " + CmakeFile)
        os.chdir(pwd)
        Log = sv.LogService()
        Log.out("Cmake at {} and record to {}\n".format(path, CmakeFile))
        with open(CmakeFile, 'r') as file:
            Msg = file.read()
            file.close()
        Log.out(Msg)

    """
    execute list of *.test one after another with "lit"
    This should be thread-safe
    """
    def LitWorker(self, ListOfTest, CpuAffinity):
        Log = sv.LogService()
        lit = os.getenv('LLVM_THESIS_lit', "Error")
        if lit == "Error":
            Log.err("Please setup \"lit\" environment variable.\n")
            sys.exit("lit is unknown\n")
        '''
        pass tests in one command
        '''
        Tests = " "
        for test in ListOfTest:
            Tests += test + " "
        try:
            lit = lit + " -j1 -q "
            tasksetPrefix = "taskset -c {} ".format(CpuAffinity)
            cmd = tasksetPrefix + lit + Tests
            Log.out("Run:\n{}\n".format(cmd))
            self.ExecCmd(cmd, ShellMode=False, NeedPrintStderr=True)
        except Exception as e:
            Log.err("Why exception happedend in LitWorker?\n{}\n".format(e))

    """
    Input:
    1. Mode: see __main__
    2. InputBuiltList: usually, this will be "SuccessBuiltTestPath"
    3. TargetListLoc: The file that contains the benchmark name which you would like to run
    No Return Value: List is a mutable type, we direct modify the InputBuiltList
    """
    def PickTests(self, Mode, InputBuiltList)
        TargetLoc = ""
        KeepList = []
        benchmarkNameSV = sv.BenchmarkNameService()
        if Mode == "Random":
            TargetLoc = "./GraphGen/output/MeasurableStdBenchmarkMeanAndSigma"
        else if Mode == "Selected.SingleCore":
            TargetLoc = "./GraphGen/output/RemovedStdBenchmarkSigma"

        # Build list of measurable benchmarks
        with open(TargetLoc, 'r') as file:
            for line in file:
                Tuple = line.split(";")
                Name = Tuple[0].strip()
                newName = benchmarkNameSV.ReplaceAWithB(Name, '.', '/')
                newName += '.test'
                KeepList.append(newName)
            file.close()
        for test in InputBuiltList:
            ValidTest = False
            for keepIt in KeepList:
                if test.endswith(keepIt):
                    ValidTest = True
                    break
            if ValidTest == False:
                InputBuiltList.remove(test)
                Log.out("In {} Mode: remove {}\n".format(Mode, test))


    def run(self, Mode="Standard", MailMsg=""):
        time = sv.TimeService()

        #cmake
        self.CmakeTestSuite()
        #if you disable cmake, you need to enable the following line
        #time.DelTimeStamp()

        StartDateTime = time.GetCurrentLocalTime()
        Target = lm.TargetBenchmarks()
        Log = sv.LogService()

        #build target tests
        pwd = os.getcwd()
        #Remove the previous record
        RandomSetAllLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
        if os.path.isfile(RandomSetAllLoc):
            os.remove(RandomSetAllLoc)

        CoreNum = str(multiprocessing.cpu_count())
        for RootPath in Target.TargetPathList:
            #generate pass set
            rg_driver = RG.FileDriver()
            RetSet = rg_driver.run()
            #build
            os.chdir(RootPath)
            self.ExecCmd("make clean", ShellMode=True)
            BuildCmd = "make -j" + CoreNum
            Log.out("Build command = \n{}\n".format(BuildCmd))
            self.ExecCmd(BuildCmd, ShellMode=True, NeedPrintStderr=True)
            #record input set
            RandomSetAllLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
            with open(RandomSetAllLoc, "a") as file:
                file.write(RootPath + ", " + RetSet + "\n")
                file.close()

        os.chdir(pwd)

        #place the corresponding feature extractor
        actor = lm.LitMimic()
        SuccessBuiltTestPath = actor.run()

        #remove ".test" directories for those failed to pass sanity check in lit
        RmFailed = sv.PassSetService()
        FailedDirs = RmFailed.RemoveSanityFailedTestDesc(Log.SanityFilePath)
        # Now, all the remained tests should be all reported as successful execution from lit


        """
        Run lit in parallel
        """
        '''
        Set LitDriver only use Core 0
        '''
        os.system("taskset -p 0x01 {}".format(os.getpid()))

        '''
        Select the test that we want to run 
        '''
        if Mode != "Standard":
            self.PickTests(Mode, SuccessBuiltTestPath)

        '''
        Split test into multiple list,
        you need to know what is the physical core number and ID in your computer.
        '''
        if Mode == "Selected.SingleCore":
            SplitCount = 1
        else:
            SplitCount = 5

        SplitList = []
        shuffle(SuccessBuiltTestPath)
        step = int(len(SuccessBuiltTestPath) // SplitCount) + 1
        for i in range(SplitCount):
            SplitList.append(SuccessBuiltTestPath[i*step : (i+1)*step])

        '''
        Run lit in parallel
        '''
        workers = []
        for i in range(SplitCount):
            CpuAffinity = i + 7
            p = multiprocessing.Process(target=self.LitWorker, args=(SplitList[i], CpuAffinity))
            workers.append(p)
            p.start()
        Log.out("Waiting for {} workers...\n".format(SplitCount))
        '''
        Waiting for all workers
        '''
        count = 0
        for p in workers:
            count += 1
            p.join()
            Log.out("Get worker:{}\n".format(count))

        #calculate used time
        EndDateTime = time.GetCurrentLocalTime()
        DeltaDateTime = time.GetDeltaTimeInDate(StartDateTime, EndDateTime)

        #Send notification
        mail = sv.EmailService()
        MailSubject = "LitDriver One Round Done."
        Content = MailMsg + "\n\n\n"
        Content += "Start date time: " + StartDateTime + "\n"
        Content += "Finish date time: " + EndDateTime + "\n"
        Content += "Whole procedure takes \"{}\"\n".format(DeltaDateTime)
        Content += "-------------------------------------------------------\n"
        Content += "Sanity Msg:\n"
        try:
            with open(Log.SanityFilePath, 'r') as file:
                Content += file.read()
                file.close()
        except Exception as e:
            Content += "All Sanity passed in these build\n"

        Content += "-------------------------------------------------------\n"
        Content += "Error PassSet Msg:\n"
        try:
            with open(Log.ErrorSetFilePath, 'r') as file:
                Content += file.read()
                file.close()
        except Exception as e:
            Content += "All PassSet passed in these build\n"

        Content += "-------------------------------------------------------\n"
        Content += "Stdout Msg:\n"
        try:
            with open(Log.StdoutFilePath, 'r') as file:
                Content += file.read()
                file.close()
        except Exception as e:
            Content += "Read Stdout Exception={}\n".format(str(e))

        Content += "-------------------------------------------------------\n"
        Content += "Stderr Msg:\n"
        try:
            with open(Log.StderrFilePath, 'r') as file:
                Content += file.read()
                file.close()
        except Exception as e:
            Content += "Read Stderr Exception={}\n".format(str(e))
            Content += "\nUsually, this means no stderr\n"

        Content += "-------------------------------------------------------\n"
        Content += "Record Time Msg:\n"
        try:
            with open(Log.RecordFilePath, 'r') as file:
                Content += file.read()
                file.close()
        except Exception as e:
            Content += "Read Record Time Exception={}\n".format(str(e))
            Content += "Usually, this means something happens...\n"

        mail.send(Subject=MailSubject, Msg=Content)
        time.DelTimeStamp()


class CommonDriver:
    PID = 0
    def CleanAllResults(self):
        #If we use LogService, it will leave TimeStamp in the "results"
        #Therefore, we only use "print"
        response = "Yes, I want."
        print("Do you want to remove all the files in the \"results\" directory?")
        print("[Enter] \"{}\" to do this.".format(response))
        print("Other response will not remove the files.")
        answer = input("Your turn:\n")
        if answer == response:
            files = glob.glob('./results/*')
            for f in files:
                os.remove(f)
            print("The directory is clean now.")
        else:
            print("Leave it as usual.")
        print("Done.\n")

    def KillProcess(self, pid):
        #kill all the children of pid and itself
        parent_pid = pid
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

    def SIGINT_Handler(self):
        self.KillProcess(self.PID)
        sys.exit()

    def run(self, Mode, round=100):
        self.CleanAllResults()
        mail = sv.EmailService()
        ts = sv.TimeService()
        StartTime = ts.GetCurrentLocalTime()
        #How many round do we need?
        for i in range(round):
            self.PID = os.fork()
            #child
            if self.PID == 0:
                #Build(including cmake) and Execute
                lit = LitRunner()
                msg = "{}/{} Round.\n".format(i+1, round)
                lit.run(Mode, MailMsg=msg)
                #Let parent to go next round
                sys.exit()
            #parent
            else:
                WaitSecs = 0
                WaitUnit = 1
                signal.signal(signal.SIGINT, self.SIGINT_Handler)
                while True:
                    rid, status = os.waitpid(self.PID, os.WNOHANG)
                    if rid == 0 and status == 0:
                        time.sleep(WaitUnit)
                        WaitSecs += WaitUnit
                    else:
                        break
                    #This time depends one machine
                    if WaitSecs > 2700:
                        self.KillProcess(self.PID)
                        Log = sv.LogService()
                        Log.outNotToFile("Parent wait too long, abort this round.\n")
                        Log.err("Parent wait too long, abort this round.\n")
                        mail.SignificantNotification(Msg="Abort one round.\n")

        EndTime = ts.GetCurrentLocalTime()
        TotalTime = ts.GetDeltaTimeInDate(StartTime, EndTime)

        TimeMsg = "Start: {};\nEnd: {}\nTotal: {}\n\n".format(StartTime, EndTime, TotalTime)
        msg = TimeMsg + "Please save the results, if necessary.\n"
        mail.send(Subject="All {} Rounds Done.".format(round),
                Msg=msg)
        # Use LogService will cause TimeStamp choas
        print("Done All Rounds\n")


if __name__ == '__main__':
    '''
    Simpe argument parsing...
    I don't think this matters.
    '''
    print("Usage: $ ./LitDriver.py [Standard | Random | Selected.SingleCore]")
    Mode = "Standard"
    Candidate = ["Standard", "Random", "Selected.SingleCore"]
    if len(sys.argv) > 1:
        if sys.argv[1] not in Candidate:
            sys.exit("Wrong arguments.\n")
        Mode = sys.argv[1]
    print("LitDriver will start after 3 secs...")
    print("Mode=\"{}\"\n".format(Mode))
    time.sleep(3)

    driver = CommonDriver()
    driver.run(Mode, 100)
