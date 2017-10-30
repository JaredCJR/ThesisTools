# TastyLib

TastyLib is a c++ library of data structures and algorithms. It is a header-only library, which means that you could just copy the `include/tastylib` directory to your project's include path and use it without caring about the issues related to link libraries.

## Build Status

| Linux | Windows | Coverage |
|:-----:|:-------:|:--------:|
|[![Build Status](https://travis-ci.org/chuyangliu/TastyLib.svg?branch=master)](https://travis-ci.org/chuyangliu/TastyLib)|[![Build status](https://ci.appveyor.com/api/projects/status/snba7lqd9fnx6kvt/branch/master?svg=true)](https://ci.appveyor.com/project/chuyangliu/tastylib/branch/master)|[![Coverage Status](https://coveralls.io/repos/github/chuyangliu/TastyLib/badge.svg?branch=master)](https://coveralls.io/github/chuyangliu/TastyLib?branch=master)|

## Outline

Contents below show the data structures and algorithms available in this project. Just click the links at the `name` column to see the details of their usages and benchmarks. All benchmarks are run with the `-O2` compiler flag under the `Release` version.

### Data Structures

| Name | Source | Benchmarked | Note | Reference |
|:----:|:------:|:-----------:|------|:---------:|
|[DoublyLinkedList](#doublylinkedlist)|[Unit test](./test/test_DoublyLinkedList.cpp)<br />[DoublyLinkedList.h](./include/tastylib/DoublyLinkedList.h)|Yes|A linked data structure that consists of a set of sequentially linked records. It also supports merge sort.|[Wikipedia](https://en.wikipedia.org/wiki/Doubly_linked_list)|
|[BinaryHeap](#binaryheap)|[Unit test](./test/test_BinaryHeap.cpp)<br />[BinaryHeap.h](./include/tastylib/BinaryHeap.h)|Yes|A heap data structure taking the form of a complete binary tree. A common way of implementing [priority queue](https://en.wikipedia.org/wiki/Priority_queue).|[Wikipedia](https://en.wikipedia.org/wiki/Binary_heap)|
|[HashTable](#hashtable)|[Unit test](./test/test_HashTable.cpp)<br />[HashTable.h](./include/tastylib/HashTable.h)|No|A data structure that stores unique elements in no particular order, and which allows for fast retrieval of individual elements based on their values. Similar to [std::unordered_set](http://www.cplusplus.com/reference/unordered_set/unordered_set).|[Wikipedia](https://en.wikipedia.org/wiki/Hash_table)|
|[AVLTree](#avltree)|[Unit test](./test/test_AVLTree.cpp)<br />[AVLTree.h](./include/tastylib/AVLTree.h)|Yes|A self-balancing binary search tree.|[Wikipedia](https://en.wikipedia.org/wiki/AVL_tree)|
|[Graph](#graph)|[Unit test](./test/test_Graph.cpp)<br />[Graph.h](./include/tastylib/Graph.h)|No|A data structure to implement the directed/undirected graph concepts from mathematics. It stores a graph in an adjacency list or matrix.|[Wikipedia](https://en.wikipedia.org/wiki/Graph_(abstract_data_type))|

### Algorithms

| Name | Source | Benchmarked | Note | Reference |
|:----:|:------:|:-----------:|------|:---------:|
|[MD5](#md5)|[Unit test](./test/test_MD5.cpp)<br />[MD5.h](./include/tastylib/MD5.h)|Yes|A widely used hash function producing a 128-bit hash value.|[Wikipedia](https://en.wikipedia.org/wiki/MD5)|
|[NPuzzle](#npuzzle)|[Unit test](./test/test_NPuzzle.cpp)<br />[NPuzzle.h](./include/tastylib/NPuzzle.h)|Yes|A classic searching problem solved with [A* search](https://en.wikipedia.org/wiki/A*_search_algorithm). A [GUI demo](https://github.com/stevennL/Puzzle) has been provided.|[Wikipedia](https://en.wikipedia.org/wiki/15_puzzle)|
|[Sort](#sort)|[Unit test](./test/test_Sort.cpp)<br />[Sort.h](./include/tastylib/Sort.h)|Yes|Including [insertion sort](https://en.wikipedia.org/wiki/Insertion_sort), [selection sort](https://en.wikipedia.org/wiki/Selection_sort), [heapsort](https://en.wikipedia.org/wiki/Heapsort), [quicksort](https://en.wikipedia.org/wiki/Quicksort), [quickselect](https://en.wikipedia.org/wiki/Quickselect). For [merge sort](https://en.wikipedia.org/wiki/Merge_sort), please refer to [DoublyLinkedList.sort()](#cost-in-theory).|[Wikipedia](https://en.wikipedia.org/wiki/Sorting_algorithm)|
|[Dijkstra](#dijkstra)|[Unit test](./test/test_Dijkstra.cpp)<br />[Dijkstra.h](./include/tastylib/Dijkstra.h)|No|An algorithm to find the shortest paths between vertices in a graph.|[Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)|
|[LCS](#lcs)|[Unit test](./test/test_LCS.cpp)<br />[LCS.h](./include/tastylib/LCS.h)|No|A dynamic programming solution to find the longest subsequence or substring common to two sequences.|[Wikipedia_substring](https://en.wikipedia.org/wiki/Longest_common_substring_problem) [Wikipedia_subsequence](https://en.wikipedia.org/wiki/Longest_common_subsequence_problem)|

## Installation

1. Install [CMake](https://cmake.org/download/).

2. Generate build files using the commands below:

    * Build benchmarks only

        ```bash
        $ mkdir build
        $ cd build
        $ cmake ..
        ```

    * Build benchmarks and unit tests

        ```bash
        $ mkdir build
        $ cd build
        $ git submodule init
        $ git submodule update
        $ cmake -DTASTYLIB_BUILD_TEST=ON ..
        ```

3. Build files will be generated in the `build` directory based on your operating system. Use them to build this project:

    | Linux | OS X | Windows |
    |:-----:|:----:|:-------:|
    |Makefile|Makefile|Visual Studio Project|

4. All executables will be generated in the `bin` directory. To run all unit tests together, use command below:

    ```bash
    $ ctest --verbose
    ```

## Details

### DoublyLinkedList

#### Usage

```c++
#include "tastylib/DoublyLinkedList.h"

using namespace tastylib;

int main() {
    DoublyLinkedList<int> list;

    auto isEmpty = list.isEmpty();  // isEmpty == true

    list.insertBack(1);   // List content: 1
    list.insertFront(2);  // List content: 2 1
    list.insert(1, 3);    // List content: 2 3 1
    list.insert(3, 4);    // List content: 2 3 1 4
    list.sort();          // List content: 1 2 3 4

    auto p1 = list.find(3);  // p1 == 2

    list.remove(p1);     // List content: 1 2 4
    list.removeFront();  // List content: 2 4
    list.removeBack();   // List content: 2

    auto p2 = list.find(3);  // p2 == -1

    auto size = list.getSize();  // size == 1

    return 0;
}
```

#### Benchmark

##### Cost in theory

| Operation | Time |
|:---------:|:----:|
|[insertFront()](./include/tastylib/DoublyLinkedList.h#L146)|O(1)|
|[removeFront()](./include/tastylib/DoublyLinkedList.h#L212)|O(1)|
|[insertBack()](./include/tastylib/DoublyLinkedList.h#L162)|O(1)|
|[removeBack()](./include/tastylib/DoublyLinkedList.h#L229)|O(1)|
|[insert()](./include/tastylib/DoublyLinkedList.h#L112)|O(n)|
|[remove()](./include/tastylib/DoublyLinkedList.h#L179)|O(n)|
|[find()](./include/tastylib/DoublyLinkedList.h#L94)|O(n)|
|[sort()](./include/tastylib/DoublyLinkedList.h#L246) (merge sort)|O(nlogn)|

##### Cost in practice

Source: [benchmark_DoublyLinkedList.cpp](./src/benchmark_DoublyLinkedList.cpp)

The program compares the time cost of `DoublyLinkedList` with `std::list`. When benchmarking `find()` and `sort()`, the size of the list is **100,000** and **5,000,000**, respectively. Here are the results under different environments:

###### Ubuntu 16.04 64-bit / g++ 5.4

| Operation | std::list | DoublyLinkedList |
|:---------:|:---------:|:----------------:|
|insertFront()|29 ns|26 ns|
|removeFront()|13 ns|12 ns|
|insertBack()|29 ns|27 ns|
|removeBack()|13 ns|12 ns|
|find()|157 µs|218 µs|
|sort()|3478 ms|3084 ms|

###### Windows 10 64-bit / Visual Studio 14 2015

| Operation | std::list | DoublyLinkedList |
|:---------:|:---------:|:----------------:|
|insertFront()|52 ns|51 ns|
|removeFront()|39 ns|44 ns|
|insertBack()|55 ns|48 ns|
|removeBack()|43 ns|47 ns|
|find()|214 µs|218 µs|
|sort()|3171 ms|2699 ms|

### BinaryHeap

#### Usage

```c++
#include "tastylib/BinaryHeap.h"
#include <vector>

using namespace tastylib;

int main() {
    BinaryHeap<int> heap1;  // Create a min-root heap

    auto isEmpty = heap1.isEmpty();  // isEmpty == true

    heap1.push(50);
    heap1.push(20);
    heap1.push(30);

    auto size1 = heap1.getSize();  // size1 == 3

    auto val1 = heap1.top();  // val1 == 20
    heap1.pop();
    auto val2 = heap1.top();  // val2 == 30
    heap1.pop();
    auto val3 = heap1.top();  // val3 == 50
    heap1.pop();

    auto size2 = heap1.getSize();  // size2 == 0

    vector<int> vals;
    vals.push_back(50);
    vals.push_back(20);
    vals.push_back(30);

    BinaryHeap<int> heap2(vals);  // Build heap using a vector

    auto size3 = heap2.getSize();  // size3 == 3

    auto val4 = heap2.top();  // val4 == 20
    heap2.pop();
    auto val5 = heap2.top();  // val5 == 30
    heap2.pop();
    auto val6 = heap2.top();  // val6 == 50
    heap2.pop();

    auto size4 = heap2.getSize();  // size4 == 0

    return 0;
}
```

#### Benchmark

##### Cost in theory

| Operation | Time |
|:---------:|:----:|
|[push()](./include/tastylib/BinaryHeap.h#L86)|O(logn)|
|[top()](./include/tastylib/BinaryHeap.h#L102)|O(1)|
|[pop()](./include/tastylib/BinaryHeap.h#L110)|O(logn)|
|[makeHeap()](./include/tastylib/BinaryHeap.h#L40)|O(n)|

##### Cost in practice

Source: [benchmark_BinaryHeap.cpp](./src/benchmark_BinaryHeap.cpp)

The program compares the time cost of `BinaryHeap` with `std::priority_queue` and `std::make_heap`. It calculates the average time cost of each operation. Here are the results under different environments:

###### Ubuntu 16.04 64-bit / g++ 5.4

| Operation | std::priority_queue / std::make_heap | BinaryHeap |
|:---------:|:------------------------------------:|:----------:|
|push()|18 ns|17 ns|
|pop()|259 ns|271 ns|
|makeHeap()|455 ms|434 ms|

###### Windows 10 64-bit / Visual Studio 14 2015

| Operation | std::priority_queue / std::make_heap | BinaryHeap |
|:---------:|:------------------------------------:|:----------:|
|push()|22 ns|21 ns|
|pop()|592 ns|267 ns|
|makeHeap()|430 ms|515 ms|

### HashTable

#### Usage

```c++
#include "tastylib/HashTable.h"
#include <string>

using namespace tastylib;

int main() {
    HashTable<std::string> table;

    auto isEmpty = table.isEmpty();  // isEmpty == true

    table.insert("Alice");
    table.insert("Darth");

    auto size1 = table.getSize();  // size1 == 2

    auto hasAlice = table.has("Alice");  // hasAlice == true
    auto hasDarth = table.has("Darth");  // hasDarth == true

    table.remove("Darth");

    hasAlice = table.has("Alice");  // hasAlice == true
    hasDarth = table.has("Darth");  // hasDarth == false

    auto size2 = table.getSize();  // size2 == 1

    return 0;
}
```

#### Benchmark

##### Cost in theory

| Operation | Time |
|:---------:|:----:|
|[insert()](./include/tastylib/HashTable.h#L88)|O(1)|
|[has()/find()](./include/tastylib/HashTable.h#L76)|O(1)|
|[remove()](./include/tastylib/HashTable.h#L102)|O(1)|
|[rehash()](./include/tastylib/HashTable.h#L117)|O(n)|

##### Cost in practice

Note that there are many different ways to implement the hash table. The MSVC compiler implements the `std::unordered_set` as a **dynamic** hash table, which means that its bucket amount changes dynamically when performing `insert()` and `remove()/erase()` operations (i.e., using [extendible hashing](https://en.wikipedia.org/wiki/Extendible_hashing) or [linear hashing](https://en.wikipedia.org/wiki/Linear_hashing)). While in TastyLib, for simplicity, the hash table is **static** so its bucket amount is fixed after initialized. Since different implementations have different pros and cons, it's hard to give a convincing benchmark result.

### AVLTree

#### Usage

```c++
#include "tastylib/AVLTree.h"
#include <string>

using namespace tastylib;

int main() {
    AVLTree<int> tree;

    auto isEmpty = tree.isEmpty();  // isEmpty == true

    tree.insert(1);
    tree.insert(2);
    tree.insert(3);
    tree.insert(3);

    std::string str1 = tree.preorder();   // str1 == "{2, 1, 3, 3}"
    std::string str2 = tree.inorder();    // str2 == "{1, 2, 3, 3}"
    std::string str3 = tree.postorder();  // str3 == "{1, 3, 3, 2}"

    auto size1 = tree.getSize();  // size1 == 4
    auto found1 = tree.has(3);    // found1 == true

    tree.remove(3);

    std::string str4 = tree.preorder();  // str4 == "{2, 1}"

    auto size2 = tree.getSize();  // size2 == 2
    auto found2 = tree.has(3);    // found2 == false

    return 0;
}
```

#### Benchmark

##### Cost in theory

| Operation | Time |
|:---------:|:----:|
|[find()](./include/tastylib/AVLTree.h#L191)|O(logn)|
|[insert()](./include/tastylib/AVLTree.h#L253)|O(logn)|
|[remove()](./include/tastylib/AVLTree.h#L287)|O(logn)|

##### Cost in practice

Source: [benchmark_AVLTree.cpp](./src/benchmark_AVLTree.cpp)

The program compares the time cost of `AVLTree` with `std::multiset`. It calculates the average time cost of each operation. Note that the `std::multiset` is implemented as a [red-black tree](https://en.wikipedia.org/wiki/Red%E2%80%93black_tree), which is faster than the AVL tree when performing `insert()` and `remove()` operations but slower when performing `find()`. Here are the results under different environments:

###### Ubuntu 16.04 64-bit / g++ 5.4

| Operation | std::multiset | AVLTree |
|:---------:|:-------------:|:-------:|
|find()|1274 ns|1012 ns|
|insert()|1218 ns|1429 ns|
|remove()|1272 ns|1549 ns|

###### Windows 10 64-bit / Visual Studio 14 2015

| Operation | std::multiset | AVLTree |
|:---------:|:-------------:|:-------:|
|find()|1077 ns|816 ns|
|insert()|1098 ns|1213 ns|
|remove()|1405 ns|1485 ns|

### Graph

#### Usage

```c++
#include "tastylib/Graph.h"
#include <string>

using namespace tastylib;

int main() {

    // Create a graph that has three vertices.
    // Each vertex stores a string object.
    Graph<std::string> graph(3);

    // Modify the string object in each vertex
    graph[0] = "I am vertex 0.";
    graph[1] = "I am vertex 1.";
    graph[2] = "I am vertex 2.";

    // Add edges
    graph.setWeight(0, 1, 10);
    graph.setWeight(0, 2, 20);
    graph.setWeight(1, 2, 30);

    // Get edge weights
    auto w0 = graph.getWeight(0, 1);  // w0 == 10
    auto w1 = graph.getWeight(0, 2);  // w1 == 20
    auto w2 = graph.getWeight(1, 2);  // w2 == 30

    // Get adjacent vertices
    auto n0 = graph.getNeighbors(0);  // n0 == [1, 2]
    auto n1 = graph.getNeighbors(1);  // n1 == [2]
    auto n2 = graph.getNeighbors(2);  // n2 == []

    return 0;
}
```

### MD5

#### Usage

```c++
#include "tastylib/MD5.h"

using namespace tastylib;

int main() {

    // hashedMsg == "2dabbfd553b67530e4892eb9481121fa",
    // which is the MD5 value of the message "TastyLib"
    std::string hashedMsg = MD5<>::getInstance()->hash("TastyLib");

    return 0;
}
```

#### Benchmark

Source: [benchmark_MD5.cpp](./src/benchmark_MD5.cpp)

The program uses the MD5 algorithm to hash a fixed message of 200 MB for several times and calculates the average time cost. Here are the results:

| Environment | Average Time |
|-------------|:------------:|
|Ubuntu 16.04 64-bit / g++ 5.4|834 ms|
|Windows 10 64-bit / Visual Studio 14 2015|1140 ms|

### NPuzzle

#### Usage

```c++
#include "tastylib/NPuzzle.h"

using namespace tastylib;

int main() {

    // The beginning node and the ending node of a 3*3 puzzle problem.
    // Number '0' indicates the empty grid and number '1-8' denote other eight grids.
    PuzzleNode<> beg({0, 2, 3, 1, 4, 5, 6, 7, 8}, 3, 3);
    PuzzleNode<> end({1, 2, 3, 4, 0, 5, 6, 7, 8}, 3, 3);

    // Solve the problem
    NPuzzle<> puzzle(beg, end);
    puzzle.solve();

    // List 'path' stores the move directions from the beginning node
    // to the ending node. Its contents must be [DOWN, RIGHT].
    std::list<Direction> path = puzzle.getPath();

    return 0;
}
```

#### Benchmark

Source: [benchmark_NPuzzle.cpp](./src/benchmark_NPuzzle.cpp)

The program solves `3*3`, `4*4`, `5*5` and `6*6` puzzle problems respectively and generates the information of overheads. Here are the outputs of the benchmark under different environments:

###### Ubuntu 16.04 64-bit / g++ 5.4

```
Benchmark of NPuzzle running...

Benchmarking 3*3 puzzle...
Beg: {1, 4, 3, 8, 6, 5, 2, 7, 0}
End: {5, 8, 2, 0, 4, 3, 6, 7, 1}
Searching...
Searched nodes: 278
     Time cost: 3 ms
    Efficiency: 72.245322 node/ms
   Path length: 69
Solution check: pass
Benchmark of 3*3 puzzle finished.

Benchmarking 4*4 puzzle...
Beg: {5, 15, 2, 14, 4, 11, 12, 7, 6, 10, 3, 8, 0, 9, 1, 13}
End: {6, 15, 14, 7, 11, 13, 10, 3, 4, 8, 12, 1, 0, 5, 2, 9}
Searching...
Searched nodes: 842
     Time cost: 12 ms
    Efficiency: 68.433030 node/ms
   Path length: 100
Solution check: pass
Benchmark of 4*4 puzzle finished.

Benchmarking 5*5 puzzle...
Beg: {1, 22, 7, 2, 3, 0, 15, 17, 14, 4, 12, 23, 21, 9, 10, 8, 13, 16, 19, 24, 20, 11, 5, 18, 6}
End: {6, 5, 10, 4, 14, 12, 2, 3, 8, 18, 7, 15, 0, 22, 21, 13, 1, 11, 16, 9, 19, 20, 23, 24, 17}
Searching...
Searched nodes: 3869
     Time cost: 51 ms
    Efficiency: 75.225541 node/ms
   Path length: 213
Solution check: pass
Benchmark of 5*5 puzzle finished.

Benchmarking 6*6 puzzle...
Beg: {15, 12, 3, 0, 11, 8, 26, 29, 25, 4, 28, 1, 14, 13, 30, 5, 16, 17, 18, 7, 24, 32, 10, 21, 27, 20, 34, 31, 22, 9, 19, 2, 33, 6, 23, 35}
End: {8, 6, 9, 7, 11, 10, 22, 27, 4, 19, 1, 5, 18, 12, 25, 3, 14, 16, 30, 2, 35, 13, 15, 23, 32, 24, 31, 34, 33, 0, 21, 20, 26, 29, 28, 17}
Searching...
Searched nodes: 93068
     Time cost: 1478 ms
    Efficiency: 62.968877 node/ms
   Path length: 588
Solution check: pass
Benchmark of 6*6 puzzle finished.

Benchmark of NPuzzle finished.
```

### Sort

#### Usage

```c++
#include "tastylib/Sort.h"

using namespace tastylib;

int main() {
    const unsigned n = 5;
    int arr[n] = {5, 4, 3, 2, 1};

    {   // Sort.
        // Aftering running each of the function below,
        // the array's content will be: [1, 2, 3, 4, 5]
        insertionSort(arr, n);
        selectionSort(arr, n);
        heapSort(arr, n);
        quickSort(arr, 0, n - 1);
    }

    {   // Find the kth smallest element.
        // After running the function below, the kth
        // smallest element will be stored at arr[k].
        int k = 1;  // Find the second smallest element
        quickSelect(arr, 0, n - 1, k);
    }

    return 0;
}
```

#### Benchmark

##### Cost in theory

| Operation | Time | Stable |
|:---------:|:----:|:------:|
|[insertionSort()](./include/tastylib/Sort.h#L18)|O(n^2)|Yes|
|[selectionSort()](./include/tastylib/Sort.h#L40)|O(n^2)|No|
|[heapSort()](./include/tastylib/Sort.h#L62)|O(nlogn)|No|
|[mergeSort()](#cost-in-theory)|O(nlogn)|Yes|
|[quickSort()](./include/tastylib/Sort.h#L110)|O(nlogn)|No|
|[quickSelect()](./include/tastylib/Sort.h#L144)|O(n)|-|

##### Cost in practice

Source: [benchmark_Sort.cpp](./src/benchmark_Sort.cpp)

The program calculates the average time cost to sort or find the kth element in an array of `100000` elements. Here are the results under different environments:

###### Ubuntu 16.04 64-bit / g++ 5.4

| Operation | Time |
|:---------:|:----:|
|std::sort()|6.77 ms|
|insertionSort()|1787.78 ms|
|selectionSort()|12297.26 ms|
|heapSort()|10.96 ms|
|quickSort()|7.15 ms|
|std::nth_element()|0.82 ms|
|quickSelect()|0.82 ms|

###### Windows 10 64-bit / Visual Studio 14 2015

| Operation | Time |
|:---------:|:----:|
|std::sort()|8.60 ms|
|insertionSort()|1197.20 ms|
|selectionSort()|4211.20 ms|
|heapSort()|11.10 ms|
|quickSort()|6.40 ms|
|std::nth_element()|0.80 ms|
|quickSelect()|0.90 ms|

### Dijkstra

#### Usage

```c++
#include "tastylib/Dijkstra.h"
#include <string>

using namespace tastylib;

int main() {
    DijkGraph<string> graph(3);  // Create a graph that has three vertices

    graph[0].val = "Alice";  // Vertex 0 denotes Alice's home
    graph[1].val = "Darth";  // Vertex 1 denotes Darth's home
    graph[2].val = "Bob";    // Vertex 2 denotes Bob' home

    graph.setWeight(0, 1, 5);   // Distance from Alice's home to Darth's is 5
    graph.setWeight(0, 2, 20);  // Distance from Alice's home to Bob's is 20
    graph.setWeight(1, 2, 5);   // Distance from Darth's home to Bob's is 5

    // Run Dijkstra's algorithm to compute the
    // shortest path from Alice's home to others'.
    dijkstra(graph, 0);

    // Now I know the minimum distance from Alice's home to Bob's home, which is 10.
    auto distToBob = graph[2].dist;  // distToBob == 10

    // I also know the minimum path to Bob's home is "0->1->2", namely "Alice->Darth->Bob".
    auto prev1 = graph[2].prev;      // prev1 == 1
    auto prev2 = graph[prev1].prev;  // prev2 == 0

    return 0;
}
```

### LCS

#### Usage

```c++
#include "tastylib/LCS.h"
#include <string>

using namespace tastylib;

int main() {

    // res1 == 4
    auto res1 = LCSubseq("0x2x3x4x5", "a12345a");

    // res2 == 1
    auto res2 = LCSubstr("0x2x3x4x5", "a12345a");

    return 0;
}
```

## License

See the [LICENSE](./LICENSE) file for license rights and limitations.
