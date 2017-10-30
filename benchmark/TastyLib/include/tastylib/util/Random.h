#ifndef TASTYLIB_RANDOM_H_
#define TASTYLIB_RANDOM_H_

#include "tastylib/internal/base.h"
#include "tastylib/util/swap.h"
#include <random>
#include <ctime>

TASTYLIB_NS_BEGIN

/*
Random number generator.
*/
template<typename RandEngine = std::default_random_engine>
class Random {
public:
    /*
    Destructor.
    */
    ~Random() {}

    /*
    Return the only instance.
    */
    static Random<>* getInstance() {
        static Random<> instance;
        return &instance;
    }

    /*
    Return a random real number in the interval [min, max).
    */
    double nextDouble(const double min = 0, const double max = 1) {
        return std::uniform_real_distribution<double>(min, max)(engine);
    }

    /*
    Return a random integer in the interval [min, max].
    */
    template<typename Integer>
    Integer nextInt(const Integer min, const Integer max) {
        return std::uniform_int_distribution<Integer>(min, max)(engine);
    }

    /*
    Shuffle the elements in an array randomly.
    Reference: https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle.

    @param beg The iterator of the first element
    @param end The iterator of the element after the last element
    */
    template<typename RanIt>
    void shuffle(RanIt beg, RanIt end) {
        if (end - beg > 1) {
            std::size_t i = end - beg - 1;
            for (RanIt it = end - 1; it != beg; --it, --i) {
                swap(*it, *(beg + nextInt<decltype(i)>(0, i)));
            }
        }
    }
private:
    RandEngine engine;

    /*
    Initialize.
    */
    Random() : engine((unsigned)std::time(nullptr)) {}
};

TASTYLIB_NS_END

#endif
