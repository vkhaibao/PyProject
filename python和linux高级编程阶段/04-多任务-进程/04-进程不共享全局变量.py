# -*- coding:utf-8 -*-
from multiprocessing import Process
import os
import time

nums = [11, 22]

def work1():
    """子进程要执行的代码"""
    print("in process1 pid=%d ,nums=%s" % (os.getpid(), nums))
    for i in range(3):
        nums.append(i)
        time.sleep(1)
        print("in process1 pid=%d ,nums=%s" % (os.getpid(), nums))
        print(id(nums))

def work2():
    """子进程要执行的代码"""
    print("in process2 pid=%d ,nums=%s" % (os.getpid(), nums))
    print(id(nums))

if __name__ == '__main__':
    p2 = Process(target=work2)
    p2.start()
    time.sleep(2)
    p1 = Process(target=work1)
    p1.start()
