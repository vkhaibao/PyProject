# coding=utf8
"""
1、系统调用t1，然后获取到g_num的值为0，此时上一把锁，即不允许其他线程操作g_num
2、t1对g_num的值进行+1
3、t1解锁，此时g_num的值为1，其他的线程就可以使用g_num了，而且是g_num的值不是0而是1
4、同理其他线程在对g_num进行修改时，都要先上锁，处理完后再解锁，在上锁的整个过程中不允许其他线程访问，就保证了数据的正确性
"""
"""
互斥锁
    多个线程几乎同时修改某一个共享数据的时候，需要进行同步控制

    线程同步能够保证多个线程安全访问竞争资源，最简单的同步机制是引入互斥锁。

    互斥锁为资源引入一个状态：锁定/非锁定

    某个线程要更改共享数据时，先将其锁定，此时资源的状态为“锁定”，其他线程不能更改；直到该线程释放资源，将资源的状态变成“非锁定”，
    其他的线程才能再次锁定该资源。互斥锁保证了每次只有一个线程进行写入操作，从而保证了多线程情况下数据的正确性。
"""
"""
threading模块中定义了Lock类，可以方便的处理锁定：
    # 创建锁
    mutex = threading.Lock()
    # 锁定
    mutex.acquire()
    # 释放
    mutex.release()
    
如果这个锁之前是没有上锁的，那么acquire不会堵塞
如果在调用acquire对这个锁上锁之前 它已经被 其他线程上了锁，那么此时acquire会堵塞，直到这个锁被解锁为止    
"""
import threading
import time
# 用互斥锁完成2个线程对同一个全局变量各加100万次的操作
gl_num = 0


def test1(num):
    global gl_num
    for i in range(num):
        mutex.acquire()
        gl_num += 1
        mutex.release()
    print("---test1---g_num=%d" % gl_num)


def test2(num):
    global gl_num
    for i in range(num):
        mutex.acquire()
        gl_num += 1
        mutex.release()
    print("---test2---g_num=%d" % gl_num)


mutex = threading.RLock()

# 创建2个线程，让他们各自对g_num加1000000次
p1 = threading.Thread(target=test1, args=(1000000,))
p1.start()

p2 = threading.Thread(target=test2, args=(1000000,))
p2.start()

# 等待计算完成
print(threading.enumerate())
while len(threading.enumerate()) != 1:
    time.sleep(1)

print("2个线程对同一个全局变量操作之后的最终结果是:%s" % gl_num)
