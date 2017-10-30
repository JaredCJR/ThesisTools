#include "tastylib/util/io.h"
#include "tastylib/util/timer.h"
#include "tastylib/util/convert.h"
#include "tastylib/MD5.h"

using namespace tastylib;
using std::string;

int main() {
    printLn("Benchmark of MD5 running...\n");
    {
        const int CASES = 10;
        const int SIZE = 200000000;

        // Generate benchmark message
        printLn("Generating a message of " + toString(SIZE) + " bytes(" + toString(SIZE / 1e6) + " MB)...");
        string msg;
        for (int i = 0; i < SIZE; ++i) {
            msg += "1";
        }
        printLn("Message generated.\n");

        {   // Benchmark hashing speed
            printLn("Running " + toString(CASES) + " cases...\n");
            double tot = 0;
            for (int i = 0; i < CASES; ++i) {
                printLn("Case #" + toString(i + 1) + ":");
                printLn("Running MD5 to hash the message...");
                auto time = timing([&]() {
                    auto hashed = MD5<>::getInstance()->hash(msg);
                    UNUSED(hashed);
                });
                printLn("Finished.");
                printLn("Elapsed time: " + toString(time) + " ms\n");
                tot += time;
            }
            printLn(toString(CASES) + " cases finished.\n");
            printLn("Average hash time: " + toString(tot / CASES) + " ms");
        }
    }
    printLn("\nBenchmark of MD5 finished.");
    checkMemoryLeaks();
    return 0;
}
