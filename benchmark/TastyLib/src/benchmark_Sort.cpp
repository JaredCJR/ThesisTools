#include "tastylib/util/io.h"
#include "tastylib/util/timer.h"
#include "tastylib/util/Random.h"
#include "tastylib/util/convert.h"
#include "tastylib/Sort.h"
#include <algorithm>
#include <vector>
#include <string>

using namespace tastylib;
using std::string;
using std::vector;

int main() {
    printLn("Benchmark of Sort running...\n");
    {
        const int SIZE = 100000;
        const int CASES = 10;
        const int METHOD_NUM = 7;

        Random<> *random = Random<>::getInstance();

        // Total time cost of each sorting method
        vector<double> time(METHOD_NUM, 0);

        // Array of each sorting method
        vector<int *> method(METHOD_NUM, nullptr);
        for (int i = 0; i < METHOD_NUM; ++i) {
            method[i] = new int[SIZE];
        }

        // Running sorting cases
        printLn("Running " + toString(CASES) + " cases...\n");
        for (int i = 0; i < CASES; ++i) {
            printLn("Case #" + toString(i + 1) + ":");
            printLn("Preparing " + toString(SIZE) + " elements to sort...");
            for (int j = 0; j < SIZE; ++j) {
                int e = random->nextInt(0, SIZE);
                for (int k = 0; k < METHOD_NUM; ++k) {
                    method[k][j] = e;
                }
            }
            // Sort
            printLn("Sorting...");
            time[0] += timing([&]() {
                std::sort(method[0], method[0] + SIZE);
            });
            time[1] += timing([&]() {
                insertionSort(method[1], SIZE);
            });
            time[2] += timing([&]() {
                selectionSort(method[2], SIZE);
            });
            time[3] += timing([&]() {
                heapSort(method[3], SIZE);
            });
            time[4] += timing([&]() {
                quickSort(method[4], 0, SIZE - 1);
            });
            // Quick select
            unsigned k = random->nextInt(0, SIZE - 1);
            time[5] += timing([&]() {
                std::nth_element(method[5], method[5] + k, method[5] + SIZE);
            });
            time[6] += timing([&]() {
                quickSelect(method[6], 0, SIZE - 1, k);
            });
            printLn("Finished.");
            // Correctness check
            bool correct = true;
            for (int i = 0; i < METHOD_NUM - 2; ++i) {
                if (!std::is_sorted(method[i], method[i] + SIZE)) {
                    correct = false;
                    break;
                }
            }
            if (method[5][k] != method[6][k]) {
                correct = false;
            }
            printLn("Correctness check: " + string(correct ? "pass\n" : "fail\n"));
        }
        printLn(toString(CASES) + " cases finished.\n");
        printLn("Avg time cost:");
        printLn("       std::sort: " + toString(time[0] / CASES) + " ms");
        printLn("  insertion sort: " + toString(time[1] / CASES) + " ms");
        printLn("  selection sort: " + toString(time[2] / CASES) + " ms");
        printLn("       heap sort: " + toString(time[3] / CASES) + " ms");
        printLn("      quick sort: " + toString(time[4] / CASES) + " ms");
        printLn("std::nth_element: " + toString(time[5] / CASES) + " ms");
        printLn("    quick select: " + toString(time[6] / CASES) + " ms");

        // Free resources
        for (int i = 0; i < METHOD_NUM; ++i) {
            delete[] method[i];
            method[i] = nullptr;
        }
    }
    printLn("Benchmark of Sort finished.");
    checkMemoryLeaks();
    return 0;
}
