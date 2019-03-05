# -*- coding:utf-8 -*-

# 修改import中的Queue为Manager
from multiprocessing import Manager, Pool
import os,time,random


def writer(q):
    print("writer启动(%s),父进程为(%s)" % (os.getpid(), os.getppid()))
    for i in "sunhaibao":
        print("写入数据 %s" % i)
        q.put(i)


def reader(q):
    print("reader启动(%s),父进程为(%s)" % (os.getpid(), os.getppid()))
    for i in range(q.qsize()):
        print("reader从Queue获取到消息：%s" % q.get(True))


if __name__ == "__main__":
    print("启动主进程 id=%s" % os.getppid())
    q = Manager().Queue()
    # 定义一个进程池，最大为5
    po = Pool(5)
    po.apply_async(writer, (q,))
    # time.sleep(1)  # 先让上面的任务向Queue存入数据，然后再让下面的任务开始从中取数据
    po.apply_async(reader, (q,))
    po.close()
    po.join()
    print("(%s) End" % os.getpid())