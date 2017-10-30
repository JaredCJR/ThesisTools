#ifndef TASTYLIB_HASHTABLE_H_
#define TASTYLIB_HASHTABLE_H_

#include "tastylib/internal/base.h"
#include "tastylib/DoublyLinkedList.h"
#include <functional>
#include <vector>

TASTYLIB_NS_BEGIN

/*
A data structure that stores unique elements in no particular order,
and which allows for fast retrieval of individual elements based on
their values.

@param Value The type of the values stored in the hash table.
@param Pred  A binary predicate that checks if two values are equal.
             If pred(a, b) == true, then value 'a' and value 'b' are
             considered equal.
@param Hash  A unary functor that computes the hash value of an element.
*/
template<typename Value, typename Pred = std::equal_to<Value>,
         typename Hash = std::hash<Value>>
class HashTable {
public:
    typedef std::size_t SizeType;
    typedef std::vector<DoublyLinkedList<Value, Pred>> Container;

    /*
    Destructor.
    */
    ~HashTable() {
        delete buckets;
    }

    /*
    Initialize the hash table.

    @param n Expected buckets amount. In practice, the
             amount of buckets may be greater than 'n'.
    */
    HashTable(const SizeType n = MIN_BUCKET)
        : size(0), bucketNum(0), buckets(nullptr) {
        rehash(n);
    }

    /*
    Return the amount of elements in the hash table.
    */
    SizeType getSize() const {
        return size;
    }

    /*
    Return true if the hash table has no elements.
    */
    bool isEmpty() const {
        return size == 0;
    }

    /*
    Remove all elements from the hash table.
    */
    void clear() {
        size = 0;
        for (SizeType i = 0; i < bucketNum; ++i) {
            (*buckets)[i].clear();
        }
    }

    /*
    Check if a value is in the hash table.

    @param val The value to be checked
    */
    bool has(const Value &val) const {
        const auto &list = (*buckets)[hash(val)];
        return list.find(val) != -1;
    }


    /*
    Insert a value to the hash table. If the
    value exists, this function does nothing.

    @param val The value to be inserted
    */
    void insert(const Value &val) {
        auto &list = (*buckets)[hash(val)];
        if (list.find(val) == -1) {
            list.insertBack(val);
            ++size;
        }
    }

    /*
    Remove a value from the hash table. If the
    value doesn't exist, this function does nothing.

    @param val The value to be removed
    */
    void remove(const Value &val) {
        auto &list = (*buckets)[hash(val)];
        auto pos = list.find(val);
        if (pos != -1) {
            list.remove(pos);
            --size;
        }
    }

    /*
    Rehash the hash table.

    @param n Expected buckets amount. In practice, the
             amount of buckets may be greater than 'n'.
    */
    void rehash(const SizeType n) {
        size = 0;
        SizeType oldNum = bucketNum;
        bucketNum = MIN_BUCKET;
        while (bucketNum < n) {
            bucketNum <<= 1;
        }
        Container *oldBuckets = buckets;
        buckets = new Container(bucketNum);
        for (SizeType i = 0; i < oldNum; ++i) {
            const auto &list = (*oldBuckets)[i];
            list.traverse([&](const SizeType pos, const Value &val) {
                UNUSED(pos);
                insert(val);
            });
        }
        delete oldBuckets;
    }

private:
    static const SizeType MIN_BUCKET = 8;

    Hash hasher;

    SizeType size;
    SizeType bucketNum;
    Container *buckets;

    /*
    The function to compute the hash value of an element.

    @param val The element
    @return The hash value of the element
    */
    SizeType hash(const Value &val) const {
        return (SizeType)(hasher(val) & (bucketNum - 1));
    }
};

TASTYLIB_NS_END

#endif
