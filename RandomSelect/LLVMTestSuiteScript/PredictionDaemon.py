#!/usr/bin/env python3
import os
import sys
import atexit
import signal
"""
TCP server lib
"""
import time
import socketserver
import socket
"""
Predictor
"""
import RandomGenerator as RG


class ResponseActor:
    def Echo(self, InputString, SenderIpString):
        retString = ""
        '''
        Random Prediction
        '''
        predictor = RG.FunctionLevelPredictor()
        SetList = predictor.RandomPassSet()
        # Convert list into string
        for Pass in SetList:
            retString = retString + str(Pass) + " "
        return retString

class tcpServer:
    class TCPHandler(socketserver.StreamRequestHandler):
        def handle(self):
            '''
            self.rfile is a file-like object created by the handler;
            we can now use e.g. readline() instead of raw recv() calls
            Get byte-object
            '''
            self.data = self.rfile.readline().strip()
            #print("{} wrote: {}".format(self.client_address[0], self.data.decode('utf-8')))
            actor = ResponseActor()
            WriteContent = actor.Echo(self.data.decode('utf-8'), self.client_address[0])
            '''
            Likewise, self.wfile is a file-like object used to write back
            to the client
            Only accept byte-object
            '''
            self.wfile.write(WriteContent.encode('utf-8'))
            #self.wfile.write(self.data.upper())

    def CreateTcpServer(self, HOST, PORT):
        # Make port reusable
        socketserver.TCPServer.allow_reuse_address = True
        # Create the server, binding to localhost on port
        server = socketserver.TCPServer((HOST, PORT), self.TCPHandler)
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()


class Daemon:
    def daemonize(self, pidfile, *, stdin='/dev/null',
                                    stdout='/dev/null',
                                    stderr='/dev/null'):

        if os.path.exists(pidfile):
            raise RuntimeError('Already running')

        # First fork (detaches from parent)
        try:
            if os.fork() > 0:
                raise SystemExit(0)   # Parent exit
        except OSError as e:
            raise RuntimeError('fork #1 failed.')

        os.chdir('/')
        os.umask(0)
        os.setsid()
        # Second fork (relinquish session leadership)
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as e:
            raise RuntimeError('fork #2 failed.')

        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()

        # Replace file descriptors for stdin, stdout, and stderr
        with open(stdin, 'rb', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open(stdout, 'wb', 0) as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
        with open(stderr, 'wb', 0) as f:
            os.dup2(f.fileno(), sys.stderr.fileno())

        # Write the PID file
        with open(pidfile,'w') as f:
            print(os.getpid(),file=f)

        # Arrange to have the PID file removed on exit/signal
        atexit.register(lambda: os.remove(pidfile))

        # Signal handler for termination (required)
        def sigterm_handler(signo, frame):
            raise SystemExit(1)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def main(self):
        sys.stdout.write('Daemon started with pid {}\n'.format(os.getpid()))
        Host = "127.0.0.1"
        Port = 7521
        '''
        If the port is opened, close it!
        '''

        server = tcpServer()
        sys.stdout.write('TCP server started with ip:{} port:{}\n'.format(Host, Port))
        server.CreateTcpServer(Host, Port)

    def run(self, argv):
        DaemonName = "PredictionDaemon"
        PidFile = '/tmp/' + DaemonName + '.pid'
        LogFile = '/tmp/' + DaemonName + '.log'

        if len(argv) != 2:
            print('Usage: {} [start|stop]'.format(argv[0]), file=sys.stderr)
            raise SystemExit(1)

        if argv[1] == 'start':
            try:
                self.daemonize(PidFile,
                          stdout=LogFile,
                          stderr=LogFile)
            except RuntimeError as e:
                print(e, file=sys.stderr)
                raise SystemExit(1)

            self.main()

        elif argv[1] == 'stop':
            if os.path.exists(PidFile):
                with open(PidFile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
            else:
                print(DaemonName + ':Not running', file=sys.stderr)
                raise SystemExit(1)

        else:
            print(DaemonName + ':Unknown command {!r}'.format(argv[1]), file=sys.stderr)
            raise SystemExit(1)

if __name__ == '__main__':
    daemon = Daemon()
    daemon.run(sys.argv)
