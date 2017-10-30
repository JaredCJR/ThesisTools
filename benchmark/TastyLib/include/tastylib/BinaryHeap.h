#ifndef TASTYLIB_BINARYHEAP_H_
#define TASTYLIB_BINARYHEAP_H_

#include "tastylib/internal/base.h"
#include <functional>
#include <vector>
#include <stdexcept>

TASTYLIB_NS_BEGIN

/*
A heap data structure taking the form of a complete binary tree.

@param Value The type of the value stored in the heap
@param Pred  The type of the binary predicate to arrange tree the nodes.
             The heap ensures that for each node N in the tree,
             N.value == N.parent.value OR Pred(N.value, N.parent.value) == true.
             By default it uses operator '>=' as the predicate, which makes it
             a min-root heap.
*/
template<typename Value, typename Pred = std::greater_equal<Value>>
class BinaryHeap {
public:
    typedef std::vector<Value> Container;
    typedef typename Container::size_type SizeType;

    /*
    Destructor.
    */
    ~BinaryHeap() {}

    /*
    Default constructor.
    */
    BinaryHeap() : size(0), tree(1, 0) {}

    /*
    Build heap with a given array of values.
    */
    BinaryHeap(const Container &vals) : size(vals.size()), tree(vals) {
        tree.push_back(tree[0]);
        for (SizeType i = size / 2; i > 0; --i) {
            Value ele = tree[i];
            SizeType j, child;
            for (j = i; (j << 1) <= size; j = child) {
                child = j << 1;
                if (child < size && pred(tree[child], tree[child + 1])) {
                    ++child;
                }
                if (pred(tree[child], ele)) {
                    break;
                } else {
                    tree[j] = tree[child];
                }
            }
            tree[j] = ele;
        }
    }

    /*
    Return the amount of elements in the heap.
    */
    SizeType getSize() const {
        return size;
    }

    /*
    Return true if the heap has no elements.
    */
    bool isEmpty() const {
        return size == 0;
    }

    /*
    Clear the elements in the heap.
    */
    void clear() {
        size = 0;
    }

    /*
    Insert a new element to the heap.

    @param val The value of the element to be inserted
    */
    void push(const Value &val) {
        if (size + 1 == tree.size()) {  // The tree array is full
            tree.resize(tree.size() << 1);  // Expand space
        }
        // The new element percolates up in the heap
        SizeType i;
        for (i = ++size; i != 1 && !pred(val, tree[i >> 1]); i >>= 1) {
            tree[i] = tree[i >> 1];
        }
        tree[i] = val;
    }

    /*
    Return the root element of the heap.
    Precondition: The heap is non-empty.
    */
    Value top() const {
        return tree[1];
    }

    /*
    Remove the root element of the heap and maintain the nodes order.
    Precondition: The heap is non-empty.
    */
    void pop() {
        Value last = tree[size--];
        SizeType i, child;
        // The empty hole(root) percolates down in the heap
        for (i = 1; (i << 1) <= size; i = child) {
            child = i << 1;
            if (child != size && pred(tree[child], tree[child + 1])) {
                ++child;
            }
            if (pred(tree[child], last)) {
                break;
            } else {
                tree[i] = tree[child];
            }
        }
        tree[i] = last;
    }

private:
    SizeType size;
    Pred pred;

    /*
    Store the complete binary tree in an array named 'tree'.
    The first element is stored at tree[1]. The value of
    tree[0] has no use.

    For each node i in the tree:
    1. tree[2 * i] is the node value of its left child.
    2. tree[2 * i + 1] is the node value of its right child.
    3. tree[floor(i / 2)] is the node value if its parent node.
    */
    Container tree;
};

TASTYLIB_NS_END

#endif
