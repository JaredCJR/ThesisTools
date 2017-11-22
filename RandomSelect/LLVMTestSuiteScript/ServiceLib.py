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
import struct, fcntl

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
        self.RecordFilePath = Loc + '/' + self.time + "_Features"
        self.SanityFilePath = Loc + '/' + self.time + "_SanityCheck"
        self.ErrorSetFilePath = Loc + '/' + self.time + "_ErrorSet"

    def outNotToFile(self, msg):
        print(msg, end="")

    def FileWriter(self, path, msg):
        file = open(path, "a")
        fcntl.flock(file, fcntl.LOCK_EX)
        file.write(msg)
        fcntl.flock(file, fcntl.LOCK_UN)
        file.close()

    def out(self, msg):
        self.outNotToFile(msg)
        #save to same file for every instance
        self.FileWriter(self.StdoutFilePath, msg)

    def err(self, msg):
        #save to same error file for every instance
        self.FileWriter(self.StderrFilePath, msg)

    def record(self, msg):
        #save to same file for every instance
        self.FileWriter(self.RecordFilePath, msg)

    def sanityLog(self, msg):
        #save to same file for every instance
        self.FileWriter(self.SanityFilePath, msg)

    def ErrorSetLog(self, msg):
        #save to same file for every instance
        self.FileWriter(self.ErrorSetFilePath, msg)

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
    def ReplaceAWithB(self, str, A, B):
        ret = ""
        for c in str:
            if c != A:
                ret += c
            else:
                ret += B
        return ret

    def GetFormalName(self, full_path):
        tests = lm.TargetBenchmarks()
        ret = full_path
        for RemoveWords in tests.TargetPathList:
            if ret.startswith(RemoveWords):
                ret = ret[len(RemoveWords):]
                break
        if ret.startswith("./"):
            ret = ret[len("./"):]
        return self.ReplaceAWithB(ret, '/', '.')



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
                if not elfPath.startswith("./"):
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

        def RunCmd(self, Cmd, BoolWithStdin, realStdin):
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
            return out, err, ElapsedTime

        """
        arg *Features is a variable length list of features.
            ex. cpu-cycles, branch-misses, etc
        Return value: dict = {"feature name": number}
            ex. {"cpu-cycles": 12345}
        """
        def ExtractPerfStatFeatures(self, perfStatLoc, perfUtil, *Features):
            featureDict = {key: None for key in Features}
            if perfUtil == "stat":
                with open(perfStatLoc, "r") as file:
                    for line in file:
                        line = line.strip()
                        '''
                        ex.
                        Performance counter stats for './dry.OriElf' (20 runs):
                        1,000,994,867      cpu-cycles           ( +-  0.00% )
                        0.233008107 seconds time elapsed        ( +-  0.03% )
                        '''
                        if line:
                            RecFeature = line.split()
                            # if recorded feature in Features
                            if any(RecFeature[1] in f for f in Features):
                                featureDict[RecFeature[1]] = int(RecFeature[0].replace(',',''))
                    file.close()
            return featureDict

        """
        Return Function dict: {"functionName": usage in decimal}
        ex.
        case 1:
            51.89%  viterbi.OriElf  libc-2.23.so       [.] __memcpy_avx_unaligned
        case 2:
            23.32%  viterbi.OriElf  viterbi.OriElf     [.] dec_viterbi_F
        case 3:
            4.79%  functionobjects  functionobjects.OriElf  [.] std::__introsort_loop<double*, long, __gnu_cxx::__ops::_Iter_comp_iter<bool (*)(double, double)> >
        """
        def ExtractPerfRecordFeatures(self, Report, elfPath):
            FuncDict = {}
            for line in Report.splitlines():
                if (not line.startswith("#")) and line:
                    #split with unknown length of space, do not pass ' ' into split()
                    lineList = line.split()
                    if lineList[2].startswith(os.path.basename(elfPath)):
                        Percentage = lineList[0][:-1]
                        #case 2
                        FuncName = lineList[4]
                        #case 3
                        if len(lineList) > 5:
                            FullSubFeature = ""
                            for SubSubFeature in lineList[4:]:
                                FullSubFeature += SubSubFeature + " "
                            FuncName = FullSubFeature
                        FuncDict[FuncName] = float(Percentage)/100.0
            return FuncDict

        def run(self, elfPath, BoolWithStdin, realStdin=b""):
            Log = PyActorService().Logger()
            #Remove the postfix ".py"
            elfPath = elfPath[:-3]
            RealElfPath = elfPath + ".OriElf"
            Cmd = RealElfPath + " " + self.Args
            TotalTime = 0.0
            try:
                DropLoc = os.getenv('LLVM_THESIS_RandomHome')
                os.system(DropLoc + "/LLVMTestSuiteScript/DropCache/drop")
                err = None
                '''
                Record the fisrt run time to get function usage and repeat count
                '''
                # write to ram
                perfRecordLoc = "/dev/shm/" + os.path.basename(elfPath) + ".perfRecord"
                perfRecordPrefix = "perf record -e cpu-cycles:ppp --quiet --output=" + perfRecordLoc + " "
                out, err, _ = self.RunCmd(perfRecordPrefix + Cmd, BoolWithStdin, realStdin)
                '''
                Calculate the LoopCount
                Make sure every benchmark execute at least "ThresholdTime"
                '''
                out, err, ElapsedTime = self.RunCmd(Cmd, BoolWithStdin, realStdin)
                ThresholdTime = 10.0
                LoopCount = int(ThresholdTime // ElapsedTime)
                if LoopCount < 5:
                    LoopCount = 5
                '''
                Run with perf stat, which will repeat several times
                '''
                perfStatLoc = "/dev/shm/" + os.path.basename(elfPath) + ".perfStat"
                perfStatPrefix = "perf stat --output " +  perfStatLoc + " -e cpu-cycles" + " "
                cycleCount = 0
                for i in range(LoopCount):
                    out, err, _ = self.RunCmd(perfStatPrefix + Cmd, BoolWithStdin, realStdin)
                    featureDict = self.ExtractPerfStatFeatures(perfStatLoc, "stat", "cpu-cycles")
                    cycleCount += featureDict["cpu-cycles"]
                '''
                Extract Function-Level features
                '''
                perfReportCmd = "perf report --input=" + perfRecordLoc + " --stdio --force --hide-unresolved"
                p = sp.Popen(shlex.split(perfReportCmd), stdout = sp.PIPE, stderr= sp.PIPE)
                out, err = p.communicate()
                p.wait()
                Report = out.decode("utf-8")
                FuncDict = self.ExtractPerfRecordFeatures(Report, elfPath)

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
            RandomSet = "set | {}".format(RandomSet)

            BenchmarkName = BenchmarkNameService()
            #elfPath must be absolute path
            BenchmarkName = BenchmarkName.GetFormalName(elfPath)
            Cycles = int(cycleCount // LoopCount)
            LogCycles = "cpu-cycles | " + str(Cycles)
            FuncUsage = ""
            for Name, Usage in FuncDict.items():
                if Usage > 0.01: # Only record those > 1%
                    Usage = "{0:.3f}".format(Usage)
                    if Name.endswith("@plt"):
                        continue
                    FuncUsage += "; func | {} | {}".format(Name, Usage)
            log_msg = BenchmarkName + "; " + RandomSet + "; " + LogCycles + FuncUsage + "\n"
            Log.record(log_msg)
