# coding=utf-8
from threading import Thread
from time import sleep, ctime
g_num = 100


def work1():
    global g_num
    for i in range(10):
        g_num += 1

    print("----in work1, g_num is %d---" % g_num)


def work2():
    global g_num
    print("----in work2, g_num is %d---" % g_num)


print("---线程创建之前g_num is %d---" % g_num)


t1 = Thread(target=work1)
t2 = Thread(target=work2)

t1.start()
t2.start()


# 列表当做实参传递到线程中
print("*" * 50)
print("列表当做实参传递到线程中")


def work3(nums):
    nums.append(44)
    print("----in work1---", nums)


def work4(nums):
    print("----in work2---", nums)


gl_num01 = [1, 2, 3]

t3 = Thread(target=work3, args=(gl_num01,))
t4 = Thread(target=work4, args=(gl_num01,))

t3.start()
t4.start()



