#!/usr/bin/python3
import os
import sys
from time import gmtime, strftime, localtime
from datetime import datetime, date, timedelta
import LitMimic as lm
import smtplib
import shutil
import time
import subprocess as sp
import shlex

class TimeService:
    DateTimeFormat = "%Y%m%d_%H-%M-%S"
    def GetCurrentLocalTime(self):
        return strftime(self.DateTimeFormat, localtime())

    def GetDeltaTimeInDate(self, prev, post):
        t1 = datetime.strptime(prev, self.DateTimeFormat)
        t2 = datetime.strptime(post, self.DateTimeFormat)
        delta = t2 - t1
        return delta

    def DelTimeStamp(self):
        ResultDir = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results')
        if not os.path.exists(ResultDir):
            os.makedirs(ResultDir)
        timeFile = ResultDir + "/TimeStamp"
        if os.path.isfile(timeFile):
            os.remove(timeFile)

class LogService():
    StderrFilePath = None
    StdoutFilePath = None
    RecordFilePath = None
    SanityFilePath = None
    ErrorSetFilePath = None
    time = None
    TimeStamp = None
    def __init__(self):
        self.TimeStamp = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results') + "/TimeStamp"
        if os.path.isfile(self.TimeStamp):
            #later enter
            with open(self.TimeStamp, 'r') as file:
                self.time = file.read()
                file.close()
        else:
            #first enter
            time = TimeService()
            self.time = time.GetCurrentLocalTime()
            with open(self.TimeStamp, 'w') as file:
                file.write(self.time)
                file.close()

        Loc = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results', "/tmp")
        if(Loc == "/tmp"):
            mail = drv.EmailService()
            mail.SignificantNotification(Msg="Log dir=\"{}\"\n".format(Loc))
        else:
            os.system("mkdir -p "+ Loc)

        self.StdoutFilePath = Loc + '/' + self.time + "_STDOUT"
        self.StderrFilePath = Loc + '/' + self.time + "_STDERR"
        self.RecordFilePath = Loc + '/' + self.time + "_Time"
        self.SanityFilePath = Loc + '/' + self.time + "_SanityCheck"
        self.ErrorSetFilePath = Loc + '/' + self.time + "_ErrorSet"

    def out(self, msg):
        print(msg, end="")
        #save to same file for every instance
        with open(self.StdoutFilePath, "a") as file:
            file.write(msg)
            file.close()

    def outNotToFile(self, msg):
        print(msg, end="")

    def err(self, msg):
        #save to same error file for every instance
        with open(self.StderrFilePath, "a") as file:
            file.write(msg)
            file.close()

    def record(self, msg):
        #save to same file for every instance
        with open(self.RecordFilePath, "a") as file:
            file.write(msg)
            file.close()

    def sanityLog(self, msg):
        #save to same file for every instance
        with open(self.SanityFilePath, "a") as file:
            file.write(msg)
            file.close()

    def ErrorSetLog(self, msg):
        #save to same file for every instance
        with open(self.ErrorSetFilePath, "a") as file:
            file.write(msg)
            file.close()

class EmailService:
    def send(self, Subject, Msg, To="jaredcjr.tw@gmail.com"):
        TO = To
        SUBJECT = Subject
        TEXT = Msg
        # Gmail Sign In
        gmail_sender = 'sslab.cs.nctu@gmail.com'
        gmail_passwd = '2018graduate'

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        BODY = '\r\n'.join(['To: %s' % TO,
                            'From: %s' % gmail_sender,
                            'Subject: %s' % SUBJECT,
                            '', TEXT])
        Log = LogService()
        try:
            server.sendmail(gmail_sender, [TO], BODY)
            Log.out('Email sent!\n')
        except:
            Log.out('Error sending mail\n')
            Log.err('Error sending mail\n')
        server.quit()

    def SignificantNotification(self, To="jaredcjr.tw@gmail.com", Msg=""):
        MailSubject = "LitDriver Notification."
        self.send(To=To, Subject=MailSubject, Msg=Msg)

class BenchmarkNameService:
    def ReplaceWithDash(self, str):
        ret = ""
        for c in str:
            if c != '/':
                ret += c
            else:
                ret += '>'
        return ret

    def GetFormalName(self, full_path):
        tests = lm.TargetBenchmarks()
        ret = full_path
        for RemoveWords in tests.TargetPathList:
            if ret.startswith(RemoveWords):
                ret = ret[len(RemoveWords):]
                break
        if ret.startswith("./"):
            ret = ret["./"]
        return self.ReplaceWithDash(ret)



class PassSetService:
    def GetInputSetDict(self):
        #Use absolute path as key
        RandomSetAllLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
        InputSetDict = {}
        with open(RandomSetAllLoc, "r") as file:
            for line in file:
                Set = [x.strip() for x in line.split(',')]
                InputSetDict[Set[0]] = Set[1]
        return InputSetDict

    #expect path to be something like: "MultiSource/Benchmarks/tramp3d-v4"
    def GetInputSet(self, path):
        InputSetDict = self.GetInputSetDict()
        Path = [x.strip() for x in path.split('/')]
        BuildKey = os.getenv('LLVM_THESIS_TestSuite') + "/" + Path[0] + "/" + Path[1] + "/"
        return InputSetDict[BuildKey]

    def ReadCorrespondingSet(self, elfPath):
        RandomSetLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
        RandomSets = []
        try:
            with open(RandomSetLoc, "r") as file:
                for line in file:
                    RandomSets.append(line.split(","))
                file.close()

            RandomSet = "Error"
            for Set in RandomSets:
                if elfPath.startswith(Set[0]):
                    RandomSet = Set[1].strip()
            if RandomSet == "Error":
                mail = EmailService()
                mail.send(Subject="Error Logging PassSet", Msg="Check it:\n{}\n".format(elfPath))
        except:
            RandomSet = "Error"

        return RandomSet


    def RemoveSanityFailedTestDesc(self, SanityFile):
        Log = LogService()
        FailList = []
        TargetPrefix = "    test-suite :: "
        with open(SanityFile, 'r') as file:
            for line in file:
                if line.startswith(TargetPrefix) :
                    FailList.append(line[len(TargetPrefix):].strip())
            file.close()

        # Create InputSet dict
        InputSetDict = self.GetInputSetDict()
        LLVMTestSuiteBuildPath = os.getenv('LLVM_THESIS_TestSuite', "Error")
        #return the build failed dirs
        FailedDirs = []
        for test in FailList:
            RealPath = LLVMTestSuiteBuildPath + "/" + test
            DirPath = os.path.dirname(RealPath)
            if os.path.exists(DirPath) == True:
                Log.sanityLog("Remove: " + DirPath + "\n")
                shutil.rmtree(DirPath)
            else:
                Log.out("Try to remove {}, but it does not exists\n".format(DirPath))
            # Log the error set for the corresponding application
            Dirs = [dir.strip() for dir in test.split('/')]
            key = LLVMTestSuiteBuildPath + '/' + Dirs[0] + '/' + Dirs[1] + '/'
            ErrorSet = InputSetDict[key]
            FailedDirs.append(DirPath)
            Log.ErrorSetLog(test + ", " + ErrorSet + "\n")
        return FailedDirs

    def RecordBuildFailedPassSet(self):
        RandomSetLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSet"
        with open(RandomSetLoc, 'r') as file:
            set = file.read()
            file.close()
            Log = LogService()
            Log.ErrorSetLog("all, " + set + "\n")

    def WriteInputSet(self, Set=""):
        RandomSetLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSet"
        with open(RandomSetLoc, 'w') as file:
            file.write(Set)
            file.close()

class PyActorService:
    class Logger(LogService):
        #Should never print to stdout, "lit" will get unexpected output
        def out(self, msg):
            pass

    class Executor:
        Args = None
        def __init__(self, args):
            self.Args = args

        def run(self, elfPath, BoolWithStdin, realStdin=""):
            Log = PyActorService().Logger()
            #Remove the postfix ".py"
            elfPath = elfPath[:-3]
            RealElfPath = elfPath + ".OriElf"
            Cmd = RealElfPath + " " + self.Args
            TotalTime = 0.0
            #Make sure every benchmark execute at least "ThresholdTime"
            ThresholdTime = 0.1
            Repeat = 0.0
            try:
                DropLoc = os.getenv('LLVM_THESIS_RandomHome')
                os.system(DropLoc + "/LLVMTestSuiteScript/DropCache/drop")
                while True:
                    err = None
                    os.system(DropLoc + "/LLVMTestSuiteScript/DropCache/drop")
                    if BoolWithStdin == False: # without stdin
                        StartTime = time.perf_counter()
                        p = sp.Popen(shlex.split(Cmd), stdout = sp.PIPE, stderr= sp.PIPE)
                        out, err = p.communicate()
                        p.wait()
                        EndTime = time.perf_counter()
                    else: # with stdin
                        StartTime = time.perf_counter()
                        p = sp.Popen(shlex.split(Cmd), stdout = sp.PIPE, stderr = sp.PIPE, stdin = sp.PIPE)
                        out, err = p.communicate(input=realStdin)
                        p.wait()
                        EndTime = time.perf_counter()
                    ElapsedTime = EndTime - StartTime
                    TotalTime += ElapsedTime
                    Repeat += 1.0
                    if TotalTime > ThresholdTime:
                        break
            except Exception as ex:
                if err is not None:
                    Log.err(err.decode('utf-8'))
                else:
                    Log.err("Why exception happend, and err is None?\n")
                    Log.err(str(ex) + "\n")
                return

            #Output for "lit"
            if BoolWithStdin == False: # without stdin
                p = sp.Popen(shlex.split(Cmd))
            else: # with stdin
                p = sp.Popen(shlex.split(Cmd), stdin = sp.PIPE)
                p.communicate(input=realStdin)
            ReturnCode = p.wait()

            """
            Use pipe to pass return value
            """
            RetFd0 = 512
            RetFd1 = RetFd0 + 1
            os.write(RetFd0, str.encode(str(ReturnCode)))
            os.close(RetFd0)

            if ReturnCode < 0:
                Log.err("cmd: {}\n is killed by signal, ret={}\n".format(Cmd, ReturnCode))
                sys.exit()

            ss = PassSetService()
            RandomSet = ss.ReadCorrespondingSet(elfPath)

            BenchmarkName = BenchmarkNameService()
            BenchmarkName = BenchmarkName.GetFormalName(elfPath)
            LogTime = TotalTime / Repeat
            log_msg = BenchmarkName + ", " + RandomSet + ", " + str(LogTime) + "\n"
            Log.record(log_msg)
