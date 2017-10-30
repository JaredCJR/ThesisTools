#ifndef TASTYLIB_IO_H_
#define TASTYLIB_IO_H_

#include "tastylib/internal/base.h"
#include <iostream>

TASTYLIB_NS_BEGIN

/*
Print one line to terminal.
*/
template<typename T>
void printLn(const T &line) {
    std::cout << line << std::endl;
}

TASTYLIB_NS_END

#endif