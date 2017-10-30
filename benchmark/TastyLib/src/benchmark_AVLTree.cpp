#include "tastylib/util/io.h"
#include "tastylib/util/timer.h"
#include "tastylib/util/Random.h"
#include "tastylib/util/convert.h"
#include "tastylib/AVLTree.h"
#include <set>
#include <vector>
#include <string>

using namespace tastylib;
using std::multiset;
using std::vector;
using std::string;

int main() {
    printLn("Benchmark of AVLTree running...\n");
    {
        const int SIZE = 10000000;

        vector<int> vals;
        Random<> *random = Random<>::getInstance();

        multiset<int> stdTree;
        AVLTree<int> libTree;

        // Generate elements
        printLn("Generating " + toString(SIZE) + " elements to benchmark...");
        for (int i = 0; i < SIZE; ++i) {
            vals.push_back(random->nextInt(0, SIZE));
        }
        printLn("Finished.\n");

        {   // Benchmark insert()
            printLn("Benchmarking insert()...");
            printLn("Inserting " + toString(SIZE) + " elements into the tree...");
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE; ++i) {
                    stdTree.insert(vals[i]);
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE; ++i) {
                    libTree.insert(vals[i]);
                }
            });
            printLn("lib finished.");
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE) + " ms / "
                    + toString(libTime / SIZE) + " ms");
            printLn("Benchmark of insert() finished.\n");
        }

        {   // Benchmark find()/has()
            printLn("Benchmarking find()/has()...");
            printLn("Finding " + toString(SIZE) + " elements in the tree...");
            bool correct = true;
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE; ++i) {
                    if (stdTree.find(vals[i]) == stdTree.end()) {
                        correct = false;
                        break;
                    }
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE; ++i) {
                    if (!libTree.has(vals[i])) {
                        correct = false;
                        break;
                    }
                }
            });
            printLn("lib finished.");
            printLn("Correctness check: " + string(correct ? "pass" : "fail"));
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE) + " ms / "
                    + toString(libTime / SIZE) + " ms");
            printLn("Benchmark of find()/has() finished.\n");
        }

        {   // Benchmark remove()
            printLn("Benchmarking remove()...");
            printLn("Removing " + toString(SIZE) + " elements from the tree...");
            auto stdTime = timing([&]() {
                for (int i = 0; i < SIZE; ++i) {
                    stdTree.erase(vals[i]);
                }
            });
            printLn("std finished.");
            auto libTime = timing([&]() {
                for (int i = 0; i < SIZE; ++i) {
                    libTree.remove(vals[i]);
                }
            });
            printLn("lib finished.");
            printLn("Correctness check: " + string((stdTree.empty() && libTree.isEmpty()) ? "pass" : "fail"));
            printLn("Avg time of std VS TastyLib: " + toString(stdTime / SIZE) + " ms / "
                    + toString(libTime / SIZE) + " ms");
            printLn("Benchmark of remove() finished.\n");
        }
    }
    printLn("Benchmark of AVLTree finished.");
    checkMemoryLeaks();
    return 0;
}
