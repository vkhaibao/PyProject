# coding=utf8
from multiprocessing import Process
import os
from time import sleep


def run_proc(name, *args, **kwargs):
    """子进程要执行的代码"""
    while True:
        print('子进程运行中name=%s，pid=%d...' % (name, os.getpid()))  # os.getpid获取当前进程的进程号
        print(kwargs)
        sleep(0.2)
        print('子进程将要结束...')


if __name__ == "__main__":
    print('父进程pid: %d' % os.getpid())  # os.getpid获取当前进程的进程号
    p = Process(target=run_proc, args=('test', 18), kwargs={"m": 20})
    p.start()
    sleep(1)  # 1秒中之后，立即结束子进程