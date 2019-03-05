# coding=utf8
from collections import Iterator
from collections import Iterable
class MyList(object):
    def __init__(self):
        self.con = []

    def add(self, item):
        self.con.append(item)

    def __iter__(self):
        pass


mylist = MyList()
mylist.add(1)
mylist.add(2)
mylist.add(3)


# 2. 如何判断一个对象是否可以迭代

print(isinstance(mylist, Iterable))

# 3. 可迭代对象的本质
"""
我们分析对可迭代对象进行迭代使用的过程，发现每迭代一次（即在for...in...中每循环一次）都会返回对象中的下一条数据，
一直向后读取数据直到迭代了所有数据后结束。那么，在这个过程中就应该有一个“人”去记录每次访问到了第几条数据，以便每次
迭代都可以返回下一条数据。我们把这个能帮助我们进行数据迭代的“人”称为迭代器(Iterator)。

可迭代对象的本质就是可以向我们提供一个这样的中间“人”即迭代器帮助我们对其进行迭代遍历使用。

可迭代对象通过__iter__方法向我们提供一个迭代器，我们在迭代一个可迭代对象的时候，实际上就是先获取该对象提供的一个
迭代器，然后通过这个迭代器来依次获取对象中的每一个数据.

那么也就是说，一个具备了__iter__方法的对象，就是一个可迭代对象。
"""

# 4. iter()函数与next()函数
"""
list、tuple等都是可迭代对象，我们可以通过iter()函数获取这些可迭代对象的迭代器。
然后我们可以对获取到的迭代器不断使用next()函数来获取下一条数据。iter()函数实际上就是调用了可迭代对象的__iter__方法。
"""
li = [11, 22, 33, 44, 55]
li_iter = iter(li)
count = len(li)
for i in range(count):
    print(next(li_iter))


# 5. 如何判断一个对象是否是迭代器
#    可以使用 isinstance() 判断一个对象是否是 Iterator 对象：
isinstance([], Iterator)

# 6. 迭代器Iterator
"""
通过上面的分析，我们已经知道，迭代器是用来帮助我们记录每次迭代访问到的位置，当我们对迭代器使用next()函数的时候，
迭代器会向我们返回它所记录位置的下一个位置的数据。实际上，在使用next()函数的时候，调用的就是迭代器对象的__next__方法
（Python3中是对象的__next__方法，Python2中是对象的next()方法）。所以，我们要想构造一个迭代器，就要实现它的__next__方法。
但这还不够，python要求迭代器本身也是可迭代的，所以我们还要为迭代器实现__iter__方法，而__iter__方法要返回一个迭代器，迭代器
自身正是一个迭代器，所以迭代器的__iter__方法返回自身即可。

一个实现了__iter__方法和__next__方法的对象，就是迭代器。
"""
class MyList(object):
    """自定义的一个可迭代对象"""
    def __init__(self):
        self.items = []

    def add(self, val):
        self.items.append(val)

    def __iter__(self):
        myiterator = MyIterator(self)
        return myiterator


class MyIterator(object):
    """自定义的供上面可迭代对象使用的一个迭代器"""
    def __init__(self, mylist):
        self.mylist = mylist
        # current用来记录当前访问到的位置
        self.current = 0

    def __next__(self):
        if self.current < len(self.mylist.items):
            item = self.mylist.items[self.current]
            self.current += 1
            return item
        else:
            raise StopIteration

    def __iter__(self):
        return self


if __name__ == '__main__':
    mylist = MyList()
    mylist.add(1)
    mylist.add(2)
    mylist.add(3)
    mylist.add(4)
    mylist.add(5)
    for num in mylist:
        print(num)