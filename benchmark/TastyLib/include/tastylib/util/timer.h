#ifndef TASTYLIB_TIMER_H_
#define TASTYLIB_TIMER_H_

#include "tastylib/internal/base.h"
#include <ctime>
#include <functional>

TASTYLIB_NS_BEGIN

/*
Return elapsed time(in millisecond)
from the starting clock time.

@param start The starting clock time.
*/
inline double elapse(const std::clock_t start) {
    return 1000 * (clock() - start) / (double)CLOCKS_PER_SEC;
}

/*
Run a function and compute its execution time.

@param f The function to be run
@return  The execution time of the function.
*/
inline double timing(const std::function<void()> &f) {
    auto start = clock();
    f();
    return elapse(start);
}

TASTYLIB_NS_END

#endif