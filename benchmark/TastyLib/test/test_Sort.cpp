#include "gtest/gtest.h"
#include "tastylib/Sort.h"
#include "tastylib/util/Random.h"
#include <algorithm>
#include <functional>

using namespace tastylib;

TEST(Sort, InsertionSort) {
    Random<> *random = Random<>::getInstance();
    const int n = 3000;
    int arr1[n], arr2[n];
    for (int i = 0; i < n; ++i) {
        arr1[i] = arr2[i] = random->nextInt(1, 10000);
    }
    std::sort(arr1, arr1 + n, std::greater<int>());
    insertionSort<int, std::greater<int>>(arr2, n);
    ASSERT_TRUE(std::is_sorted(arr1, arr1 + n, std::greater<int>()));
    ASSERT_TRUE(std::is_sorted(arr2, arr2 + n, std::greater<int>()));
    for (int i = 0; i < n; ++i) {
        ASSERT_EQ(arr1[i], arr2[i]);
    }
}

TEST(Sort, SelectionSort) {
    Random<> *random = Random<>::getInstance();
    const int n = 3000;
    int arr1[n], arr2[n];
    for (int i = 0; i < n; ++i) {
        arr1[i] = arr2[i] = random->nextInt(1, 10000);
    }
    std::sort(arr1, arr1 + n, std::greater<int>());
    selectionSort<int, std::greater<int>>(arr2, n);
    ASSERT_TRUE(std::is_sorted(arr1, arr1 + n, std::greater<int>()));
    ASSERT_TRUE(std::is_sorted(arr2, arr2 + n, std::greater<int>()));
    for (int i = 0; i < n; ++i) {
        ASSERT_EQ(arr1[i], arr2[i]);
    }
}

TEST(Sort, HeapSort) {
    Random<> *random = Random<>::getInstance();
    const int n = 3000;
    int arr1[n], arr2[n];
    for (int i = 0; i < n; ++i) {
        arr1[i] = arr2[i] = random->nextInt(1, 10000);
    }
    std::sort(arr1, arr1 + n, std::greater<int>());
    heapSort<int, std::less<int>>(arr2, n);
    ASSERT_TRUE(std::is_sorted(arr1, arr1 + n, std::greater<int>()));
    ASSERT_TRUE(std::is_sorted(arr2, arr2 + n, std::greater<int>()));
    for (int i = 0; i < n; ++i) {
        ASSERT_EQ(arr1[i], arr2[i]);
    }
}

TEST(Sort, QuickSort) {
    Random<> *random = Random<>::getInstance();
    const int n = 3000;
    int arr1[n], arr2[n];
    for (int i = 0; i < n; ++i) {
        arr1[i] = arr2[i] = random->nextInt(1, 10000);
    }
    std::sort(arr1, arr1 + n, std::greater<int>());
    quickSort<int, std::greater<int>>(arr2, 0, n - 1);
    ASSERT_TRUE(std::is_sorted(arr1, arr1 + n, std::greater<int>()));
    ASSERT_TRUE(std::is_sorted(arr2, arr2 + n, std::greater<int>()));
    for (int i = 0; i < n; ++i) {
        ASSERT_EQ(arr1[i], arr2[i]);
    }
}

TEST(Sort, QuickSelect) {
    Random<> *random = Random<>::getInstance();
    const int n = 3000;
    for (int i = 0; i < 5; ++i) {
        int arr1[n], arr2[n];
        for (int j = 0; j < n; ++j) {
            arr1[j] = arr2[j] = random->nextInt(1, 10000);
        }
        unsigned k = random->nextInt(0, n - 1);
        std::nth_element(arr1, arr1 + k, arr1 + n, std::greater<int>());
        quickSelect<int, std::greater<int>>(arr2, 0, n - 1, k);
        ASSERT_EQ(arr1[k], arr2[k]);
    }
}
