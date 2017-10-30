#ifndef TASTYLIB_SWAP_H_
#define TASTYLIB_SWAP_H_

#include "tastylib/internal/base.h"

TASTYLIB_NS_BEGIN

/*
Swap the values of two elements.
*/
template<typename T>
void swap(T &a, T &b) {
    T tmp = a;
    a = b;
    b = tmp;
}

TASTYLIB_NS_END

#endif