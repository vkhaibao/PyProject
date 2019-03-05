# coding=utf8
from greenlet import greenlet
import time
import os


def test1():
    while True:
        print("%s" % os.getpid())
        print("%s" % os.getppid())
        print("---A--")
        gr2.switch()
        time.sleep(0.5)


def test2():
    while True:
        print("%s" % os.getpid())
        print("%s" % os.getppid())
        print("---B--")
        gr1.switch()
        time.sleep(0.5)


gr1 = greenlet(test1)
gr2 = greenlet(test2)


# 切换到gr1中运行
gr1.switch()
