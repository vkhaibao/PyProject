# coding=utf8
from multiprocessing import Queue
from multiprocessing import Process
import os, time, random


def p_in(q):

    for value in range(10):
        print('Put %s to queue...' % value)
        q.put(value)
        time.sleep(random.random())


def p_out(q):
    while True:
        if not q.empty():
            value = q.get()
            print("取出队列值为%s" % value)
            time.sleep(random.random())
        else:
            break


if __name__ == "__main__":
    q = Queue()
    p_putin = Process(target=p_in, args=(q,))
    p_getout = Process(target=p_out, args=(q,))
    p_putin.start()
    p_putin.join()
    p_getout.start()
    p_getout.join()
    # pr进程里是死循环，无法等待其结束，只能强行终止:
    print('')
    print('所有数据都写入并且读完')
