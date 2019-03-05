# -*- coding:utf-8 -*-
from multiprocessing import Process
import time
import os


def run_proc01():
    """子进程要执行的代码"""
    while True:
        print("----2----")
        print('子进程运行中，pid=%d...' % os.getpid())
        time.sleep(1)


def run_proc02():
    """子进程要执行的代码"""
    while True:
        print("----3----")
        print('子进程运行中，pid=%d...' % os.getpid())
        time.sleep(1)


if __name__ == '__main__':
    p01 = Process(target=run_proc01)
    p02 = Process(target=run_proc02)
    p01.start()
    p02.start()
    while True:
        print('父进程pid: %d' % os.getpid())
        print("----1----")
        time.sleep(1)