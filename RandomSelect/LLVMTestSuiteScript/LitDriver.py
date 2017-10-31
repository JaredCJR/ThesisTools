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

class LitRunner:
    def ExecCmd(self, cmd, ShellMode=False, NeedPrintStderr=True):
        Log = sv.LogService()
        try:
            #Execute cmd
            p = sp.Popen(shlex.split(cmd), shell=ShellMode, stdout=sp.PIPE, stderr= sp.PIPE)
            out, err = p.communicate()
            p.wait()
            if out is not None:
                Log.out(out.decode('utf-8'))
            if err is not None:
                Log.err(err.decode('utf-8'))
            if NeedPrintStderr and err is not None:
                Log.outNotToFile(err.decode('utf-8'))
        except Exception as e:
            Log.err("----------------------------------------------------------\n")
            Log.err("Exception= {}".format(str(e)) + "\n")
            Log.err("Command error: {}\n".format(cmd))
            if err is not None:
                Log.err("Error Msg= {}\n".format(err.decode('utf-8')))
            Log.err("----------------------------------------------------------\n")

    def run(self, MailMsg="", RandomMean=0.5):
        ResultDir = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results')
        if not os.path.exists(ResultDir):
            os.makedirs(ResultDir)
        timeFile = ResultDir + "/TimeStamp"
        if os.path.isfile(timeFile):
            os.remove(timeFile)

        time = sv.TimeService()
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
            rg_driver = RG.Driver()
            #mean should between 0~1
            RetSet = rg_driver.run(RandomMean)
            #build
            os.chdir(RootPath)
            self.ExecCmd("make clean", ShellMode=True)
            self.ExecCmd("make -j" + CoreNum, ShellMode=True,
                     NeedPrintStderr=True)
            #record input set
            RandomSetAllLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
            with open(RandomSetAllLoc, "a") as file:
                file.write(RootPath + ", " + RetSet + "\n")
                file.close()

        os.chdir(pwd)

        #place the corresponding feature extractor
        actor = lm.LitMimic()
        SuccessBuiltPath = actor.run()

        #execute it one after another with "lit"
        lit = os.getenv('LLVM_THESIS_lit', "Error")
        if lit == "Error":
            Log.err("Please setup \"lit\" environment variable.\n")
            sys.exit("lit is unknown\n")
        bar = progressbar.ProgressBar(redirect_stdout=True)
        for idx, LitTargetDir in enumerate(SuccessBuiltPath):
            os.chdir(LitTargetDir)
            cmd = lit + " -j1 -q ./"
            Log.out("Run: {}\n".format(LitTargetDir))
            bar.update((idx / len(SuccessBuiltPath)) * 100)
            self.ExecCmd(cmd, ShellMode=False, NeedPrintStderr=True)
        os.chdir(pwd)

        #calculate used time
        EndDateTime = time.GetCurrentLocalTime()
        DeltaDateTime = time.GetDeltaTimeInDate(StartDateTime, EndDateTime)

        #Remove failed records
        RmRec = sv.BenchmarkNameService()
        RmRec.RemoveFailureRecords(StdoutFile=Log.StdoutFilePath, RecordFile=Log.RecordFilePath)


        #Send notification
        mail = sv.EmailService()
        MailSubject = "LitDriver One Iteration Done."
        Content = MailMsg + "\n\n\n"
        Content += "Start date time: " + StartDateTime + "\n"
        Content += "Finish date time: " + EndDateTime + "\n"
        Content += "Whole procedure takes \"{}\"\n".format(DeltaDateTime)
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
            Content += "Usually, this means no stderr\n"

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
        Log.NewLogFiles()


class CommonDriver:
    def CleanAllResults(self):
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

    def CmakeTestSuite(self):
        pwd = os.getcwd()
        path = os.getenv('LLVM_THESIS_TestSuite', 'Err')
        if path == 'Err':
            sys.exit("Error with get env: $LLVM_THESIS_TestSuite\n")
        if os.path.exists(path):
            shutil.rmtree(path)

        os.makedirs(path)
        os.chdir(path)
        os.system("CC=clang CXX=clang++ cmake ../")
        os.chdir(pwd)
        print("Cmake at {}\n".format(path))


    def run(self):
        self.CleanAllResults()
        self.CmakeTestSuite()
        #How many iteration in one round?
        repeat = 25 #On Intel 8700K 4.3GHz, 25 is about one day.
        #How many round do we need?
        round = 4
        time = sv.TimeService()
        StartTime = time.GetCurrentLocalTime()
        for i in range(round):
            for j in range(repeat):
                #RandomMeanNumber
                mean = (j + 1) / (repeat + 1)
                #Build and Execute
                lit = LitRunner()
                msg = "{}/{} Iteration For {}/{} Round.\n".format(j+1, repeat, i+1, round)
                lit.run(MailMsg=msg, RandomMean=mean)


        EndTime = time.GetCurrentLocalTime()
        TotalTime = time.GetDeltaTimeInDate(StartTime, EndTime)

        mail = sv.EmailService()
        TimeMsg = "Start: {};\nEnd: {}\nTotal: {}\n\n".format(StartTime, EndTime, TotalTime)
        msg = TimeMsg + "Please save the results, if necessary.\n"
        mail.send(Subject="All {}x{} Iterations Done.".format(repeat, round),
                Msg=msg)
        print("Done All Rounds\n")


if __name__ == '__main__':
    driver = CommonDriver()
    driver.run()
