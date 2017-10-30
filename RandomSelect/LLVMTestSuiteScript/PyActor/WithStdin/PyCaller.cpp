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
    std::string retFileName = "./ReturnValue";
    system(("rm -f " + retFileName).c_str());

    //Pass redirected input
    int pFD[2];
    pipe(pFD);

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
        close(pFD[1]); //close write
        dup2(pFD[0], STDIN_FILENO); // redirect stdin to child
        close(pFD[0]); //close read
        execv(Cmd.c_str(), argv);
    }else {
        //parent
        close(pFD[0]);
        write(pFD[1], results_stdin.c_str(), results_stdin.length());
        close(pFD[1]);
        waitpid(-1, NULL, 0);
        //return value
        std::ifstream file;
        file.open(retFileName);
        if(file) {
            int ret;
            file >> ret;
            return ret;
        }
    }
    return 0;
}
