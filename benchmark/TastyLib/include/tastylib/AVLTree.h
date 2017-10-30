#ifndef TASTYLIB_AVLTREE_H_
#define TASTYLIB_AVLTREE_H_

#include "tastylib/internal/base.h"
#include <functional>
#include <string>
#include <sstream>

TASTYLIB_NS_BEGIN

/*
A self-balancing binary search tree.

@param Value   The type of the values stored in the tree nodes
@param PredCmp A binary predicate to arrange the tree nodes.
               The tree ensures that for each node N,
               PredCmp(N.leftchild.value, N.value) == true AND
               PredCmp(N.value, N.rightchild.value) == true.
@param PredEq  A binary predicate that checks if two values are equal.
               If PredEq(a, b) == true, then value 'a' and value 'b' are
               considered equal.
*/
template<typename Value,
         typename PredCmp = std::less<Value>,
         typename PredEq = std::equal_to<Value>>
class AVLTree {
public:
    typedef std::size_t SizeType;

    struct Node {
        Value val;
        Node* left;
        Node* right;
        int height;

        Node(const Value &v, Node *const l = nullptr, Node *const r = nullptr)
            : val(v), left(l), right(r), height(0) {}
    };

    /*
    Destructor.
    */
    ~AVLTree() {
        clear();
    }

    /*
    Initialize the tree.
    */
    AVLTree() : root(nullptr), size(0) {}

    /*
    Return true if there are no elements in the tree.
    */
    bool isEmpty() const {
        return size == 0;
    }

    /*
    Return the amount of elements in the tree.
    */
    SizeType getSize() const {
        return size;
    }

    /*
    Remove all nodes and free the resources.
    */
    void clear() {
        release(root);
        size = 0;
        root = nullptr;
    }

    /*
    Return true if a value exists in the tree.

    @param val The value to be found
    */
    bool has(const Value &val) const {
        return !!find(val, root);
    }

    /*
    Insert a value into the tree.

    @param val The value to be inserted
    */
    void insert(const Value &val) {
        root = insertBalance(val, root);
        ++size;
    }

    /*
    Remove all nodes that has a given value in the tree.

    @param val The given value
    */
    void remove(const Value &val) {
        while (has(val)) {
            root = removeBalance(val, root);
            --size;
        }
    }

    /*
    Return a string representation of the tree node values traversed
    in postorder. The value type must overload operator '<<'.
    */
    std::string postorder() const {
        bool first = true;
        std::ostringstream oss;
        oss << "{";
        traversePostorder(root, [&](const Value &val) {
            if (!first) {
                oss << ", ";
            }
            first = false;
            oss << val;
        });
        oss << "}";
        return oss.str();
    }

    /*
    Return a string representation of the tree node values traversed
    in inorder. The value type must overload operator '<<'.
    */
    std::string inorder() const {
        bool first = true;
        std::ostringstream oss;
        oss << "{";
        traverseInorder(root, [&](const Value &val) {
            if (!first) {
                oss << ", ";
            }
            first = false;
            oss << val;
        });
        oss << "}";
        return oss.str();
    }

    /*
    Return a string representation of the tree node values traversed
    in preorder. The value type must overload operator '<<'.
    */
    std::string preorder() const {
        bool first = true;
        std::ostringstream oss;
        oss << "{";
        traversePreorder(root, [&](const Value &val) {
            if (!first) {
                oss << ", ";
            }
            first = false;
            oss << val;
        });
        oss << "}";
        return oss.str();
    }

private:
    Node *root;
    SizeType size;

    PredEq predEq;
    PredCmp predCmp;

    /*
    Remove all nodes of a tree and free the resources.

    @param r The root of the tree
    */
    void release(Node *const r) {
        if (r) {
            release(r->left);
            release(r->right);
            delete r;
        }
    }

    /*
    Find a node that has a given value in a tree.

    @param val The given value
    @param r   The root of the tree
    @return    The pointer of the node that has the given value.
               Return nullptr if the node does not exist.
    */
    Node* find(const Value &val, Node *const r) const {
        if (!r || predEq(val, r->val)) {
            return r;
        } else if (predCmp(val, r->val)) {
            return find(val, r->left);
        } else {
            return find(val, r->right);
        }
    }

    /*
    Traverse a tree in postorder.

    @param r The root of the tree.
    @param f The function to manipulate each node value.
    */
    void traversePostorder(const Node *const r,
                           const std::function<void(const Value&)> &f) const {
        if (r) {
            traversePostorder(r->left, f);
            traversePostorder(r->right, f);
            f(r->val);
        }
    }

    /*
    Traverse a tree in inorder.

    @param r The root of the tree.
    @param f The function to manipulate each node value.
    */
    void traverseInorder(const Node *const r,
                         const std::function<void(const Value&)> &f) const {
        if (r) {
            traverseInorder(r->left, f);
            f(r->val);
            traverseInorder(r->right, f);
        }
    }

    /*
    Traverse a tree in preorder.

    @param r The root of the tree.
    @param f The function to manipulate each node value.
    */
    void traversePreorder(const Node *const r,
                          const std::function<void(const Value&)> &f) const {
        if (r) {
            f(r->val);
            traversePreorder(r->left, f);
            traversePreorder(r->right, f);
        }
    }

    /*
    Insert a value to a tree and maintain the balance.

    @param val The value to be inserted
    @param r   The root of the tree
    @return    The new root of the tree that has been inserted
    */
    Node* insertBalance(const Value &val, Node *r) {
        if (!r) {
            r = new Node(val);
        } else if (predCmp(val, r->val)) {
            r->left = insertBalance(val, r->left);
            if (height(r->left) - height(r->right) == 2) {
                if (predCmp(val, r->left->val)) {
                    r = rotateSingleLeft(r);
                } else {
                    r = rotateDoubleLeft(r);
                }
            }
        } else {
            r->right = insertBalance(val, r->right);
            if (height(r->right) - height(r->left) == 2) {
                if (predCmp(val, r->right->val)) {
                    r = rotateDoubleRight(r);
                } else {
                    r = rotateSingleRight(r);
                }
            }
        }
        updateHeight(r);
        return r;
    }

    /*
    Remove a value from a tree and maintain the balance.
    Precondition: the value must exist in the tree.

    @param val The value to be inserted
    @param r   The root of the tree
    @return    The new root of the tree that has been removed
    */
    Node* removeBalance(const Value &val, Node *r) {
        if (predEq(val, r->val)) {
            if (r->left && r->right) {  // Two child
                Node* node = leftmost(r->right);
                r->val = node->val;
                r->right = removeBalance(node->val, r->right);
            } else {  // One or zero child
                Node* del = r;
                r = !r->left ? r->right : r->left;
                delete del;
            }
        } else if (predCmp(val, r->val)) {
            r->left = removeBalance(val, r->left);
        } else {
            r->right = removeBalance(val, r->right);
        }
        // Maintain balance
        if (r) {
            int d = height(r->left) - height(r->right);
            if (d == 2) {
                if (height(r->left->left) >= height(r->left->right)) {
                    r = rotateSingleLeft(r);
                } else {
                    r = rotateDoubleLeft(r);
                }
            } else if (d == -2) {
                if (height(r->right->right) >= height(r->right->left)) {
                    r = rotateSingleRight(r);
                } else {
                    r = rotateDoubleRight(r);
                }
            }
            updateHeight(r);
        }
        return r;
    }

    /*
    Return the leftmost node in a tree.

    @param r The root of the tree
    */
    Node* leftmost(Node *const r) const {
        if (!r || !r->left) {
            return r;
        } else {
            return leftmost(r->left);
        }
    }

    /*
    Return the height of a tree. The height of the empty tree is -1.

    @param r The root of the tree
    */
    int height(const Node *const r) const {
        return r ? r->height : -1;
    }

    /*
    Update the height of a tree.

    @param r The root of the tree
    */
    void updateHeight(Node *const r) {
        int lh = height(r->left), rh = height(r->right);
        r->height = 1 + (lh > rh ? lh : rh);
    }

    /*
    Single rotation with left when inserting
    into the left subtree of the left child.

    @param r The root of the tree
    @return  The new root of the rotated tree
    */
    Node* rotateSingleLeft(Node *const r) {
        Node* leftChild = r->left;
        r->left = leftChild->right;
        leftChild->right = r;
        updateHeight(r);
        updateHeight(leftChild);
        return leftChild;
    }

    /*
    Single rotation with right when inserting
    into the right subtree of the right child.

    @param r The root of the tree
    @return  The new root of the rotated tree
    */
    Node* rotateSingleRight(Node *const r) {
        Node* rightChild = r->right;
        r->right = rightChild->left;
        rightChild->left = r;
        updateHeight(r);
        updateHeight(rightChild);
        return rightChild;
    }

    /*
    Double rotation with left when inserting
    into the right subtree of the left child.

    @param r The root of the tree
    @return  The new root of the rotated tree
    */
    Node* rotateDoubleLeft(Node *const r) {
        r->left = rotateSingleRight(r->left);
        return rotateSingleLeft(r);
    }

    /*
    Double rotation with right when inserting
    into the left subtree of the right child.

    @param r The root of the tree
    @return  The new root of the rotated tree
    */
    Node* rotateDoubleRight(Node *const r) {
        r->right = rotateSingleLeft(r->right);
        return rotateSingleRight(r);
    }
};

TASTYLIB_NS_END

#endif
