#include <stdlib.h>
#include <string>
#include <stdio.h>
#include <fstream>

int main(int argc, char* argv[]) 
{
    char CmdBuffer[4096] = {};
    std::string cmd = argv[0];
    cmd += ".py";
    std::string retFileName = "./ReturnValue";
    system(("rm -f " + retFileName).c_str());

    for(int i = 1;i < argc; i++) {
        cmd += " ";
        cmd += argv[i];
    }
    system(cmd.c_str());

    //return value
    std::ifstream file;
    file.open(retFileName);
    if(file) {
        int ret;
        file >> ret;
        return ret;
    }
    return 0;
}
