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

    //Pass redirected input
    int pFD[2];
    pipe(pFD);

    //Get return value
    const int RetFd0 = 512;
    const int RetFd1 = RetFd0 + 1;
    int retFD[2];
    pipe(retFD);

    //get stdin
    // don't skip the whitespace while reading
    std::cin >> std::noskipws;

    // use stream iterators to copy the stream to a string
    std::istream_iterator<char> it(std::cin);
    std::istream_iterator<char> end;
    std::string results_stdin(it, end);

    int pid=fork();
    if(pid == 0) {
        //child
        //STDIN
        close(pFD[1]); //close write
        dup2(pFD[0], STDIN_FILENO); // redirect stdin to child
        close(pFD[0]); //close read

        // return value
        close(retFD[0]); //close read
        dup2(retFD[1], RetFd0);
        close(retFD[1]); //close write

        execv(Cmd.c_str(), argv);
    }else {
        //parent
        close(pFD[0]);
        write(pFD[1], results_stdin.c_str(), results_stdin.length());
        close(pFD[1]);
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
