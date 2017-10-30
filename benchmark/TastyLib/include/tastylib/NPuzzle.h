#ifndef TASTYLIB_NPUZZLE_H_
#define TASTYLIB_NPUZZLE_H_

#include "tastylib/internal/base.h"
#include "tastylib/util/Random.h"
#include "tastylib/util/swap.h"
#include "tastylib/HashTable.h"
#include "tastylib/BinaryHeap.h"
#include <vector>
#include <sstream>
#include <string>
#include <functional>
#include <list>
#include <math.h>

TASTYLIB_NS_BEGIN

/*
Definition of puzzle nodes.

@param Int Type of signed integer
*/
template<typename Int = short>
class PuzzleNode {
public:
    typedef std::vector<Int> Container;
    typedef typename Container::size_type SizeType;

    /*
    Definition of the move direction.
    */
    enum Direction {
        NONE,
        LEFT,
        UP,
        RIGHT,
        DOWN
    };

    /*
    Destructor.
    */
    ~PuzzleNode() {}

    /*
    Initialize the node. The node value is stored in an one-dimension array.
    For a 3*3 puzzle, the contents of the array must be like this:
    {1, 2, 3, 4, 5, 6, 7, 8, 0}, where number '0' indicates the the empty grid
    and number '1-8' denote other eight grids. The configuration is similar when
    the puzzle's size is 4*4, 5*5, etc.

    @param val_ The node value
    @param row_ The row amount
    @param col_ The column amount
    */
    PuzzleNode(const Container &val_, const SizeType row_, const SizeType col_)
        : val(val_), row(row_), col(col_) {
        for (SizeType i = 0; i < val.size(); ++i) {
            if (val[i] == 0) {
                emptyPos = i;
            }
        }
    }

    /*
    Return the node value.
    */
    const Container& getVal() const {
        return val;
    }

    /*
    Return the amount of rows.
    */
    SizeType getRowCount() const {
        return row;
    }

    /*
    Return the amount of columns.
    */
    SizeType getColCount() const {
        return col;
    }

    /*
    Return true if the empty grid can move one step along a given direction.

    @param d The given direction
    */
    bool canMove(const Direction d) const {
        switch (d) {
            case LEFT:
                return getCol(emptyPos) != 0;
            case UP:
                return getRow(emptyPos) != 0;
            case RIGHT:
                return getCol(emptyPos) != col - 1;
            case DOWN:
                return getRow(emptyPos) != row - 1;
            case NONE:
                return true;
            default:
                return false;
        }
    }

    /*
    Move the empty grid along a given direction

    @param d The given direction
    */
    void move(const Direction d) {
        SizeType goalPos = emptyPos;
        switch (d) {
            case LEFT:
                goalPos -= 1;
                break;
            case UP:
                goalPos -= col;
                break;
            case RIGHT:
                goalPos += 1;
                break;
            case DOWN:
                goalPos += col;
                break;
            case NONE:
            default:
                break;
        }
        if (emptyPos != goalPos) {
            swap(val[emptyPos], val[goalPos]);
            emptyPos = goalPos;
        }
    }

    /*
    Return the adjacent node at a given direction.
    Precondition: the current node can move along the given direction

    @param d The given direction
    */
    PuzzleNode* getNeighbor(const Direction d) const {
        PuzzleNode* n = new PuzzleNode(*this);
        n->move(d);
        return n;
    }

    /*
    Randomly rearrange the node value. The function ensures that a solution exists.
    */
    void shuffle() {
        Random<> *random = Random<>::getInstance();
        for (SizeType i = 0; i < SHUFFLE_TIMES; ++i) {
            Direction d = Direction(random->nextInt(1, 4));
            if (canMove(d)) {
                move(d);
            }
        }
    }

    /*
    Return the heuristic value to the destination node.

    @param des   The destination node
    @param index The index of each number in the destination node value array
    */
    SizeType heuristic(const PuzzleNode *const des, const std::vector<SizeType> &index) const {
        SizeType size = val.size();

        // Number of nodes which are in a wrong position
        SizeType wrong = 0;
        for (SizeType i = 0; i < size; ++i) {
            if (val[i] != des->val[i]) {
                ++wrong;
            }
        }

        // Distance to the destination
        SizeType manhatten = 0, geometric = 0;
        for (SizeType i = 0; i < size; ++i) {
            if (val[i]) {  // Escape value 0
                SizeType curR = getRow(i);
                SizeType curC = getCol(i);
                SizeType desR = getRow(index[val[i]]);
                SizeType desC = getCol(index[val[i]]);
                SizeType dR = curR > desR ? curR - desR : desR - curR;
                SizeType dC = curC > desC ? curC - desC : desC - curC;
                manhatten += dR + dC;
                geometric += (SizeType)(sqrt(dR * dR + dC * dC));
            }
        }

        return 5 * (1 * wrong + 2 * manhatten + 1 * geometric);
    }

    /*
    Return the hash value of the node.
    */
    SizeType hash() const {
        return std::hash<std::string>()(toString());
    }

    /*
    Return a string description of the node value.
    */
    std::string toString() const {
        std::ostringstream oss;
        oss << "{";
        for (SizeType i = 0; i < val.size(); ++i) {
            if (i) oss << ", ";
            oss << val[i];
        }
        oss << "}";
        return oss.str();
    }

    /*
    Return the direction of this node relelative to a given adjacent node.

    @param n The given adjacent node
    */
    Direction getDirectionTo(const PuzzleNode *const n) const {
        if (n) {
            Int offset = (Int)emptyPos - (Int)n->emptyPos;
            if (offset == -1) {
                return LEFT;
            } else if (offset == 1) {
                return RIGHT;
            } else if (offset == (Int)col) {
                return DOWN;
            } else if (offset == -(Int)col) {
                return UP;
            }
        }
        return NONE;
    }

    bool operator==(const PuzzleNode &n) const {
        return getVal() == n.getVal();
    }

    bool operator>=(const PuzzleNode &n) const {
        return getF() >= n.getF();
    }

    void setG(const SizeType g_) {
        g = g_;
    }

    void setH(const SizeType h_) {
        h = h_;
    }

    void setParent(PuzzleNode *p) {
        parent = p;
    }

    SizeType getG() const {
        return g;
    }

    SizeType getH() const {
        return h;
    }

    SizeType getF() const {
        return getG() + getH();
    }

    const PuzzleNode* getParent() const {
        return parent;
    }

private:
    static const SizeType SHUFFLE_TIMES = 1000;

    Container val;

    SizeType emptyPos = 0;
    SizeType row = 0;
    SizeType col = 0;

    SizeType g = 0;
    SizeType h = 0;
    PuzzleNode *parent = nullptr;

    /*
    Compute the row number according to a given index of one-dimension array.

    @param i The given index
    @return  The row number in interval [0, row - 1]
    */
    SizeType getRow(const SizeType i) const {
        return i / col;
    }

    /*
    Compute the column number according to a given index of one-dimension array.

    @param i The given index
    @return  The row number in interval [0, col - 1]
    */
    SizeType getCol(const SizeType i) const {
        return i % col;
    }
};

/*
Class to solve the n-puzzle problem.
@param Int Type of signed integer
*/
template<typename Int = short>
class NPuzzle {
public:
    typedef PuzzleNode<Int> Node;
    typedef typename Node::SizeType SizeType;
    typedef typename Node::Direction Direction;

    /*
    Destructor.
    */
    ~NPuzzle() {}

    /*
    Initialize the beginning node and the ending node.

    @param src_ The beginning node
    @param des_ The ending node
    */
    NPuzzle(const Node &beg_, const Node &end_)
        : beg(beg_), end(end_), closeList(1000000) {}

    /*
    Solve the problem using A* searching.
    */
    void solve() {
        std::vector<SizeType> index = buildIndex();
        searchCnt = 0;
        openList.push(&beg);
        while (!openList.isEmpty()) {
            Node *cur = nullptr;
            do {
                // Loop until the open list is empty or a node
                // that is not in the close list is found.
                cur = openList.top();
                openList.pop();
            } while (!openList.isEmpty() && closeList.has(cur));
            if (openList.isEmpty() && closeList.has(cur)) {
                // If all the nodes in the open list is in the
                // close list, then there is no available path
                // between the two nodes.
                return;
            }
            ++searchCnt;
            closeList.insert(cur);
            if (*cur == end) {
                buildPath(cur);
                freeResources();
                return;
            }
            for (Int i = 1; i < 5; ++i) {
                Direction d = Direction(i);
                if (cur->canMove(d)) {
                    Node *adj = cur->getNeighbor(d);
                    alloc.push_back(adj);
                    if (!closeList.has(adj)) {
                        adj->setParent(cur);
                        adj->setG(cur->getG() + 1);
                        adj->setH(adj->heuristic(&end, index));
                        openList.push(adj);
                    }
                }
            }
        }
    }

    /*
    Return the solution path.
    */
    const std::list<Direction>& getPath() const {
        return path;
    }

    /*
    Return the amount of nodes searched.
    */
    SizeType getSearchCount() const {
        return searchCnt;
    }

    /*
    Shuffle the beginning node.

    @return The beginning node shuffled
    */
    const Node& shuffleBeg() {
        beg.shuffle();
        return beg;
    }

    /*
    Shuffle the ending node.

    @return The ending node shuffled
    */
    const Node& shuffleEnd() {
        end.shuffle();
        return end;
    }

    void setBeg(const Node& beg_) {
        beg = beg_;
    }

    void setEnd(const Node& end_) {
        end = end_;
    }

    const Node& getBeg() const {
        return beg;
    }

    const Node& getEnd() const {
        return end;
    }

private:
    struct Equal {
        bool operator()(const Node *const &n1,
                        const Node *const &n2) const {
            return *n1 == *n2;
        }
    };

    struct GreaterEqual {
        bool operator()(const Node *const &n1,
                        const Node *const &n2) const {
            return *n1 >= *n2;
        }
    };

    struct Hash {
        SizeType operator()(const Node *const &n) const {
            return n->hash();
        }
    };

    Node beg;
    Node end;

    BinaryHeap<Node*, GreaterEqual> openList;
    HashTable<Node*, Equal, Hash> closeList;

    std::list<Direction> path;
    std::list<Node*> alloc;

    SizeType searchCnt = 0;

    /*
    Return the index of the grid numbers in the ending node value.
    */
    std::vector<SizeType> buildIndex() const {
        const auto &endVal = end.getVal();
        std::vector<SizeType> index(endVal.size());
        for (SizeType i = 0; i < endVal.size(); ++i) {
            index[endVal[i]] = i;
        }
        return index;
    }

    /*
    Build a path from the beginning node to the destination node.

    @param n The destination node
    */
    void buildPath(const Node *n) {
        path.clear();
        while (n) {
            auto parent = n->getParent();
            Direction d = n->getDirectionTo(parent);
            if (d != Direction::NONE) {
                path.push_front(d);
            }
            n = parent;
        }
    }

    /*
    Free allocated resources.
    */
    void freeResources() {
        for (const auto &n : alloc) {
            delete n;
        }
        alloc.clear();
        openList.clear();
        closeList.clear();
    }
};

TASTYLIB_NS_END

#endif
