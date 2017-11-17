#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string>
#include <iostream>
#include <istream>
#include <ostream>
#include <iterator>
#include <sys/wait.h>
#include <stdio.h>
#include <fstream>

int main(int argc, char* argv[])
{
    std::string Cmd = argv[0];
    char postfix[] = ".py";
    Cmd += postfix;

    //Get return value
    const int RetFd0 = 512;
    const int RetFd1 = RetFd0 + 1;
    int retFD[2];
    pipe(retFD);

    int pid=fork();
    if(pid == 0) {
        // child
        // return value
        close(retFD[0]); //close read
        dup2(retFD[1], RetFd0);
        close(retFD[1]); //close write

        execv(Cmd.c_str(), argv);
    }else {
        //parent
        waitpid(-1, NULL, 0);
        //return value
        close(retFD[1]); //close write
        dup2(retFD[0], RetFd1);
        close(retFD[0]); //close read
        // read return value
        std::string retStr(100, '\0');
        read(RetFd1, &retStr[0], 100);
        int ret = std::stoi(retStr);
        close(RetFd1);
        return ret;
    }
    return 0;
}
