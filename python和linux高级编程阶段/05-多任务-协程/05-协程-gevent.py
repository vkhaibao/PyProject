# coding=utf8
from gevent import monkey
import gevent
import random
import time

# 1. gevent的使用


def f01(n):
    for i in range(n):
        print(gevent.getcurrent(), i)


g1 = gevent.spawn(f01, 5)
g2 = gevent.spawn(f01, 5)
g3 = gevent.spawn(f01, 5)
g1.join()
g2.join()
g3.join()


# 2. gevent切换执行


def f02(n):
    for i in range(n):
        print(gevent.getcurrent(), i)
        #用来模拟一个耗时操作，注意不是time模块中的sleep
        gevent.sleep(2)


g01 = gevent.spawn(f02, 5)
g02 = gevent.spawn(f02, 5)
g03 = gevent.spawn(f02, 5)
g01.join()
g02.join()
g03.join()

# 3. 给程序打补丁
def coroutine_work(coroutine_name):
    for i in range(10):
        print(coroutine_name, i)
        time.sleep(random.random())

gevent.joinall([
    gevent.spawn(coroutine_work, "worker01"),
    gevent.spawn(coroutine_work, "worker02")
])

# 耗时操作

# 有耗时操作时需要
monkey.patch_all()  # 将程序中用到的耗时操作的代码，换为gevent中自己实现的模块

def coroutine_work01(coroutine_name):
    for i in range(10):
        print(coroutine_name, i)
        time.sleep(random.random())

gevent.joinall([
        gevent.spawn(coroutine_work01, "work1"),
        gevent.spawn(coroutine_work01, "work2")
])