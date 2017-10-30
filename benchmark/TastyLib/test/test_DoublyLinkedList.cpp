#include "gtest/gtest.h"
#include "tastylib/util/convert.h"
#include "tastylib/DoublyLinkedList.h"
#include <string>

using tastylib::DoublyLinkedList;
using tastylib::toString;
using std::string;

typedef DoublyLinkedList<int>::SizeType SizeType;

template<typename T>
string getListContent(const DoublyLinkedList<T> &list) {
    string str;
    list.traverse([&](const SizeType pos, const T &val) {
        UNUSED(pos);
        str += toString(val);
    });
    return str;
}

TEST(DoublyLinkedList, Basic) {
    DoublyLinkedList<int> list;
    EXPECT_TRUE(list.isEmpty());
    list.insertBack(1);
    EXPECT_STREQ(getListContent(list).c_str(), "1");
    list.insertFront(2);
    EXPECT_STREQ(getListContent(list).c_str(), "21");
    list.insert(1, 3);
    EXPECT_STREQ(getListContent(list).c_str(), "231");
    list.insert(3, 4);
    EXPECT_STREQ(getListContent(list).c_str(), "2314");
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "1234");
    int p1 = list.find(3);
    EXPECT_EQ(p1, 2);
    list.remove(p1);
    EXPECT_STREQ(getListContent(list).c_str(), "124");
    list.removeFront();
    EXPECT_STREQ(getListContent(list).c_str(), "24");
    list.removeBack();
    EXPECT_STREQ(getListContent(list).c_str(), "2");
    int p2 = list.find(3);
    EXPECT_EQ(p2, -1);
    EXPECT_EQ(list.getSize(), (SizeType)1);
    list.clear();
    EXPECT_TRUE(list.isEmpty());
    EXPECT_EQ(list.getSize(), (SizeType)0);
}

TEST(DoublyLinkedList, Insert) {
    DoublyLinkedList<int> list;

    // Test insertFront()
    for (int i = 1; i < 10; ++i) {
        list.insertFront(i);
    }
    EXPECT_STREQ(getListContent(list).c_str(), "987654321");

    // Test insertBack()
    list.clear();
    for (int i = 1; i < 10; ++i) {
        list.insertBack(i);
    }
    EXPECT_STREQ(getListContent(list).c_str(), "123456789");

    // Test insert()
    for (int i = 0; i < 8; ++i) {
        list.insert(2 * i + 1, 0);
    }
    EXPECT_STREQ(getListContent(list).c_str(), "10203040506070809");
    list.insert(0, 1);
    list.insert(100, 9);
    EXPECT_STREQ(getListContent(list).c_str(), "1102030405060708099");
}

TEST(DoublyLinkedList, Remove) {
    DoublyLinkedList<int> list;

    // Test removeFront()
    for (int i = 1; i < 6; ++i) {
        list.insertBack(i);
    }
    for (int i = 0; i < 3; ++i) {
        list.removeFront();
    }
    EXPECT_STREQ(getListContent(list).c_str(), "45");
    for (int i = 0; i < 2; ++i) {
        list.removeFront();
    }
    EXPECT_STREQ(getListContent(list).c_str(), "");

    // Test removeBack()
    for (int i = 1; i < 6; ++i) {
        list.insertBack(i);
    }
    for (int i = 0; i < 3; ++i) {
        list.removeBack();
    }
    EXPECT_STREQ(getListContent(list).c_str(), "12");
    for (int i = 0; i < 2; ++i) {
        list.removeBack();
    }
    EXPECT_STREQ(getListContent(list).c_str(), "");

    // Test remove()
    for (int i = 1; i < 6; ++i) {
        list.insertBack(i);
    }
    list.remove(0);
    list.remove(3);
    list.remove(100);
    EXPECT_STREQ(getListContent(list).c_str(), "234");
    list.remove(1);
    list.remove(1);
    EXPECT_STREQ(getListContent(list).c_str(), "2");
    list.remove(1);
    list.remove(0);
    EXPECT_STREQ(getListContent(list).c_str(), "");
}

TEST(DoublyLinkedList, Find) {
    DoublyLinkedList<int> list;
    for (int i = 0; i < 3; ++i) {
        list.insertBack(i);
    }
    int p = list.find(0);
    EXPECT_EQ(p, 0);
    p = list.find(1);
    EXPECT_EQ(p, 1);
    p = list.find(2);
    EXPECT_EQ(p, 2);
    p = list.find(3);
    EXPECT_EQ(p, -1);
}

TEST(DoublyLinkedList, Sort) {
    DoublyLinkedList<int> list;
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "");
    list.insertBack(0);
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "0");
    list.removeFront();
    list.insertFront(1);
    list.insertFront(2);
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "12");
    list.removeBack();
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "1");
    for (int i = 0; i < 5; ++i) {
        list.insertFront(i);
    }
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "011234");
    list.insertBack(2);
    list.sort();
    EXPECT_STREQ(getListContent(list).c_str(), "0112234");
}
