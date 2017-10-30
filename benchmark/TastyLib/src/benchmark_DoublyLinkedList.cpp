#include "tastylib/util/io.h"
#include "tastylib/util/timer.h"
#include "tastylib/util/convert.h"
#include "tastylib/util/Random.h"
#include "tastylib/DoublyLinkedList.h"
#include <list>
#include <algorithm>

using namespace tastylib;
using std::string;
using std::list;

typedef DoublyLinkedList<int>::SizeType SizeType;

/*
If the contents of the two lists are the same, print
passing message. Otherwise print failing message.
*/
template<typename T>
void checkCorrect(const std::list<T> &stdList,
                  const DoublyLinkedList<T> &libList) {
    bool correct = true;
    if (stdList.size() != libList.getSize()) {
        correct = false;
    } else {
        auto it = stdList.begin();
        libList.traverse([&](const SizeType pos, const int &val) {
            UNUSED(pos);
            if (val != *it) {
                correct = false;
                return;
            }
            ++it;
        });
    }
    printLn("Correctness check: " + std::string(correct ? "pass" : "fail"));
}

int main() {
    printLn("Benchmark of DoublyLinkedList running...\n");
    {
        const int CASES_SORT = 10;
        const int SIZE_SORT = 5000000;
        const int SIZE_FIND = 100000;
        const int SIZE_OTHER = 40000000;

        Random<> *random = Random<>::getInstance();

        list<int> stdList;
        DoublyLinkedList<int> libList;

        {   // Benchmark insertFront()
            printLn("Benchmarking insertFront()...");
            printLn("Inserting " + toString(SIZE_OTHER) + " elements at the FRONT of the list...");
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    stdList.push_front(i);
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    libList.insertFront(i);
                }
            });
            printLn("lib finished.");
            checkCorrect(stdList, libList);
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE_OTHER) + " ms / "
                    + toString(libTime / SIZE_OTHER) + " ms");
            printLn("Benchmark of insertFront() finished.\n");
        }

        {   // Benchmark removeFront()
            printLn("Benchmarking removeFront()...");
            printLn("Removing " + toString(SIZE_OTHER) + " elements from the FRONT of the list...");
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    stdList.pop_front();
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    libList.removeFront();
                }
            });
            printLn("lib finished.");
            checkCorrect(stdList, libList);
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE_OTHER) + " ms / "
                    + toString(libTime / SIZE_OTHER) + " ms");
            printLn("Benchmark of removeFront() finished.\n");
        }

        {   // Benchmark insertBack()
            printLn("Benchmarking insertBack()...");
            printLn("Inserting " + toString(SIZE_OTHER) + " elements at the BACK of the list...");
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    stdList.push_back(i);
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    libList.insertBack(i);
                }
            });
            printLn("lib finished.");
            checkCorrect(stdList, libList);
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE_OTHER) + " ms / "
                    + toString(libTime / SIZE_OTHER) + " ms");
            printLn("Benchmark of insertBack() finished.\n");
        }

        {   // Benchmark removeBack()
            printLn("Benchmarking removeBack()...");
            printLn("Removing " + toString(SIZE_OTHER) + " elements from the BACK of the list...");
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    stdList.pop_back();
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE_OTHER; ++i) {
                    libList.removeBack();
                }
            });
            printLn("lib finished.");
            checkCorrect(stdList, libList);
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE_OTHER) + " ms / "
                    + toString(libTime / SIZE_OTHER) + " ms");
            printLn("Benchmark of removeBack() finished.\n");
        }

        {   // Benchmark find()
            printLn("Benchmarking find()...");

            // Generate random list contents
            printLn("Inserting " + toString(SIZE_FIND) + " random elements to the list...");
            for (int i = 0; i < SIZE_FIND; ++i) {
                int val = random->nextInt(0, SIZE_FIND << 2);
                stdList.push_back(val);
                libList.insertBack(val);
            }
            printLn("Finished.");

            // Find
            printLn("Finding " + toString(SIZE_FIND) + " elements...");
            unsigned dontCare = 0;  // Suppress compiler optimization
            auto stdTime = timing([&]() {
                auto it = stdList.begin();
                while (it != stdList.end()) {
                    auto pos = std::find(stdList.begin(), stdList.end(), *it);
                    UNUSED(pos);
                    ++dontCare;
                    ++it;
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                auto it = stdList.begin();
                while (it != stdList.end()) {
                    auto pos = libList.find(*it);
                    UNUSED(pos);
                    ++dontCare;
                    ++it;
                }
            });
            UNUSED(dontCare);
            printLn("lib finished.");
            checkCorrect(stdList, libList);
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE_FIND) + " ms / "
                    + toString(libTime / SIZE_FIND) + " ms");
            printLn("Benchmark of find() finished.\n");
        }

        {   // Benchmark sort()
            printLn("Benchmarking sort() for " + toString(CASES_SORT) + " cases...");
            double stdTot = 0, libTot = 0;
            for (int i = 0; i < CASES_SORT; ++i) {
                printLn("Case #" + toString(i + 1) + ":");
                stdList.clear();
                libList.clear();

                // Generate random list contents
                printLn("Inserting " + toString(SIZE_SORT) + " random elements to the list...");
                for (int i = 0; i < SIZE_SORT; ++i) {
                    int e = random->nextInt(0, SIZE_SORT - 1);
                    stdList.push_back(e);
                    libList.insertBack(e);
                }

                // Sort
                printLn("Sorting the list...");
                auto stdTime = timing([&]() {
                    stdList.sort();
                });
                printLn("std finished.");
                auto libTime = timing([&]() {
                    libList.sort();
                });
                printLn("lib finished.");
                stdTot += stdTime;
                libTot += libTime;
                checkCorrect(stdList, libList);
                printLn("Time of std VS TastyLib: " + toString(stdTime) + " ms / " + toString(libTime) + " ms\n");
            }
            printLn(toString(CASES_SORT) + " cases finished.");
            printLn("Avg time of std VS TastyLib: " + toString(stdTot / CASES_SORT) + " ms / "
                    + toString(libTot / CASES_SORT) + " ms");
            printLn("Benchmark of sort() finished.\n");
        }
    }
    printLn("Benchmark of DoublyLinkedList finished.");
    checkMemoryLeaks();
    return 0;
}
