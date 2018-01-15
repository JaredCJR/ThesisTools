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
        pass

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
        print(msg, file=sys.stderr)

    def record(self, msg):
        #save to same file for every instance
        self.FileWriter(self.RecordFilePath, msg)

    def recordTargetInfo(self, RecordTargetFilePath, msg):
        self.FileWriter(RecordTargetFilePath, msg)

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
        ret = full_path
        if ret.startswith("./"):
            ret = ret[len("./"):]
        return ret.split('/')[-1]

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
            # Remove the postfix ".py"
            elfPath = elfPath[:-3]
            RealElfPath = elfPath + ".OriElf"
            Cmd = RealElfPath + " " + self.Args
            # Get workerID
            buildPath = os.getenv('LLVM_THESIS_HOME', "Error")
            if buildPath == "Error":
                Log.err("$LLVM_THESIS_HOME is not defined.\n")
                sys.exit(1)
            buildPath = buildPath + '/test-suite/'
            # Get log file path
            tmp = elfPath
            # ex. /home/jrchang/workspace/llvm-thesis/test-suite/build-worker-1/path/to/elf
            WorkerID = tmp.replace(buildPath, '').split('/')[0].split('-')[2]
            BenchmarkName = BenchmarkNameService()
            #elfPath must be absolute path
            BenchmarkName = BenchmarkName.GetFormalName(elfPath)
            '''
            log file format: /tmp/PredictionDaemon/worker-[n]/[BenchmarkName]
            record path example:
            /tmp/PredictionDaemon/worker-1/dry
            '''
            TargetDir = '/tmp/PredictionDaemon/worker-' + WorkerID
            RecordTargetFilePath = TargetDir + '/' + BenchmarkName
            if not os.path.isdir(TargetDir):
                os.makedirs(TargetDir)
            elif os.path.exists(RecordTargetFilePath):
                os.remove(RecordTargetFilePath)
            # profile it!
            TotalTime = 0.0
            try:
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

            Cycles = int(cycleCount // LoopCount)
            LogCycles = "cpu-cycles | " + str(Cycles)
            FuncUsage = ""
            for Name, Usage in FuncDict.items():
                if Usage > 0.01: # Only record those > 1%
                    Usage = "{0:.3f}".format(Usage)
                    if Name.strip().endswith("@plt"):
                        continue
                    FuncUsage += "; func | {} | {}".format(Name, Usage)
            log_msg = BenchmarkName + "; " + LogCycles + FuncUsage + "\n"
            Log.recordTargetInfo(RecordTargetFilePath, log_msg)
