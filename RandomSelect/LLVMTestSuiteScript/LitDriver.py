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
    def ExecCmd(self, cmd, ShellMode=False, NeedPrintStderr=True, SanityLog=False):
        Log = sv.LogService()
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
                Log.err(err.decode('utf-8'))
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

    def run(self, MailMsg=""):
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

        #remove ".test" file for those failed to pass sanity check in lit
        RmFailed = sv.BenchmarkNameService()
        RmFailed.RemoveSanityFailedTestDesc(Log.SanityFilePath)
        # Now, all the remained tests should be all reported as successful execution from lit

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



    def run(self):
        self.CleanAllResults()
        time = sv.TimeService()
        StartTime = time.GetCurrentLocalTime()
        #How many round do we need?
        round = 100
        for i in range(round):
            #Build(including cmake) and Execute
            lit = LitRunner()
            msg = "{}/{} Round.\n".format(i+1, round)
            lit.run(MailMsg=msg)

        EndTime = time.GetCurrentLocalTime()
        TotalTime = time.GetDeltaTimeInDate(StartTime, EndTime)

        mail = sv.EmailService()
        TimeMsg = "Start: {};\nEnd: {}\nTotal: {}\n\n".format(StartTime, EndTime, TotalTime)
        msg = TimeMsg + "Please save the results, if necessary.\n"
        mail.send(Subject="All {} Rounds Done.".format(round),
                Msg=msg)
        # Use LogService will cause TimeStamp choas
        print("Done All Rounds\n")


if __name__ == '__main__':
    driver = CommonDriver()
    driver.run()
