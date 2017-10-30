#ifndef TASTYLIB_SORT_H_
#define TASTYLIB_SORT_H_

#include "tastylib/internal/base.h"
#include "tastylib/util/swap.h"
#include "tastylib/BinaryHeap.h"
#include <functional>

TASTYLIB_NS_BEGIN

/*
The insertion sort algorithm to sort an unordered array.

@param arr The array to be sorted
@param n   The amount of elements in the array
*/
template<typename Ele, typename Pred = std::less<Ele>>
void insertionSort(Ele *const arr, const std::size_t n) {
    Pred pred;
    for (std::size_t i = 1; i < n; ++i) {
        if (!pred(arr[i - 1], arr[i])) {
            Ele tmp = arr[i];
            std::size_t j = i;
            while (j >= 1 && pred(tmp, arr[j - 1])) {
                arr[j] = arr[j - 1];
                --j;
            }
            arr[j] = tmp;
        }
    }
}

/*
The selection sort algorithm to sort an unordered array.

@param arr The array to be sorted
@param n   The amount of elements in the array
*/
template<typename Ele, typename Pred = std::less<Ele>>
void selectionSort(Ele *const arr, const std::size_t n) {
    Pred pred;
    for (std::size_t i = 0; i < n - 1; ++i) {
        std::size_t minOrMax = i;
        for (std::size_t k = i; k < n; ++k) {
            if (pred(arr[k], arr[minOrMax])) {
                minOrMax = k;
            }
        }
        if (minOrMax != i) {
            swap(arr[i], arr[minOrMax]);
        }
    }
}

/*
The heapsort algorithm to sort an unordered array.

@param arr The array to be sorted
@param n   The amount of elements in the array
*/
template<typename Ele, typename Pred = std::greater_equal<Ele>>
void heapSort(Ele *const arr, const std::size_t n) {
    BinaryHeap<Ele, Pred> heap;
    for (std::size_t i = 0; i < n; ++i) {
        heap.push(arr[i]);
    }
    for (std::size_t i = 0; i < n; ++i) {
        arr[i] = heap.top();
        heap.pop();
    }
}

/*
Return the pivot element in an array. This function is used in quickSort()
and quickSelect(). The algorithm is based on the median-of-three pivoting.
It ensures that after its execution, Pred(arr[left], arr[mid]) == true AND
Pred(arr[mid], arr[right]) == true. The pivot element will be stored at
arr[right - 1].

@param a     The array to be processed
@param left  The beginning index of the array to be processed
@param right The ending index of the array to be processed
@return      The pivot element
*/
template<typename Ele, typename Pred = std::less<Ele>>
Ele pivot(Ele *const arr, const std::size_t left, std::size_t right) {
    Pred pred;
    std::size_t mid = (left + right) / 2;
    if (pred(arr[mid], arr[left])) {
        swap(arr[mid], arr[left]);
    }
    if (pred(arr[right], arr[left])) {
        swap(arr[right], arr[left]);
    }
    if (pred(arr[right], arr[mid])) {
        swap(arr[right], arr[mid]);
    }
    swap(arr[mid], arr[right - 1]);  // Store pivot at arr[right - 1]
    return arr[right - 1];
}

/*
The quicksort algorithm to sort an unordered array.

@param arr   The array to be sorted
@param left  The beginning index of the array to be sorted
@param right The ending index of the array to be sorted
*/
template<typename Ele, typename Pred = std::less<Ele>>
void quickSort(Ele *const arr, const std::size_t left, const std::size_t right) {
    Pred pred;
    if (left + 10 <= right) {
        Ele p = pivot<Ele, Pred>(arr, left, right);
        std::size_t i = left, j = right - 1;
        while (true) {
            while (pred(arr[++i], p)) {}
            while (pred(p, arr[--j])) {}
            if (i < j) {
                swap(arr[i], arr[j]);
            } else {
                break;
            }
        }
        swap(arr[i], arr[right - 1]);  // Restore pivot
        quickSort<Ele, Pred>(arr, left, i - 1);
        quickSort<Ele, Pred>(arr, i + 1, right);
    } else {
        // Use insertion sort for small array
        insertionSort<Ele, Pred>(arr + left, right - left + 1);
    }
}

/*
The quickselect algorithm to find the kth smallest/biggest element
in an unordered array. After its execution, the kth element will be
stored at arr[k].

@param arr   The array to be processed
@param left  The beginning index of the array to be processed
@param right The ending index of the array to be processed
@param k     The kth element to find
*/
template<typename Ele, typename Pred = std::less<Ele>>
void quickSelect(Ele *const arr,
                 const std::size_t left,
                 const std::size_t right,
                 const std::size_t k) {
    Pred pred;
    if (left + 10 <= right) {
        Ele p = pivot<Ele, Pred>(arr, left, right);
        std::size_t i = left, j = right - 1;
        while (true) {
            while (pred(arr[++i], p)) {}
            while (pred(p, arr[--j])) {}
            if (i < j) {
                swap(arr[i], arr[j]);
            } else {
                break;
            }
        }
        swap(arr[i], arr[right - 1]);  // Restore pivot
        if (k < i) {
            quickSelect<Ele, Pred>(arr, left, i - 1, k);
        } else if (k > i) {
            quickSelect<Ele, Pred>(arr, i + 1, right, k);
        }
    } else {
        // Use insertion sort for small array
        insertionSort<Ele, Pred>(arr + left, right - left + 1);
    }
}

TASTYLIB_NS_END

#endif
