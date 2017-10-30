#include "gtest/gtest.h"
#include "tastylib/LCS.h"
#include <string>

using namespace tastylib;
using std::string;

TEST(LCS, subsequence) {
    ASSERT_EQ((std::size_t)0, LCSubseq("", ""));
    ASSERT_EQ((std::size_t)4, LCSubseq("0x2x3x4x5", "a12345a"));
}

TEST(LCS, substring) {
    ASSERT_EQ((std::size_t)0, LCSubstr("", ""));
    ASSERT_EQ((std::size_t)1, LCSubstr("0x2x3x4x5", "a12345a"));
}
