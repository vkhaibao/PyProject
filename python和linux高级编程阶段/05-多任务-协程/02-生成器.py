# coding=utf8
"""
1. 生成器
利用迭代器，我们可以在每次迭代获取数据（通过next()方法）时按照特定的规律进行生成。但是我们在实现一个迭代器时，
关于当前迭代到的状态需要我们自己记录，进而才能根据当前状态生成下一个数据。
为了达到记录当前状态，并配合next()函数进行迭代使用，我们可以采用更简便的语法，即生成器(generator)。生成器是一类特殊的迭代器。
"""

# 2. 创建生成器方法1
#    要创建一个生成器，有很多种方法。第一种方法很简单，只要把一个列表生成式的 [ ] 改成 ( )

L = [x for x in range(5)]

print(L)

G = (x for x in range(5))

print(next(G))
print(next(G))
print(next(G))
print(next(G))
print(next(G))

# 用函数写生成器


def fib(n):
    current = 0
    num1 = 0
    num2 = 1
    while current < n:
        num = num1
        num1, num2 = num2, num1 + num2
        current += 1
        yield num
    return 'done'

F = fib(10)
print(next(F))
print(next(F))
print(next(F))
print(next(F))

"""
使用了yield关键字的函数不再是函数，而是生成器。（使用了yield的函数就是生成器）
yield关键字有两点作用：
保存当前运行状态（断点），然后暂停执行，即将生成器（函数）挂起
将yield关键字后面表达式的值作为返回值返回，此时可以理解为起到了return的作用
可以使用next()函数让生成器从断点处继续执行，即唤醒生成器（函数）
Python3中的生成器可以使用return返回最终运行的返回值，而Python2中的生成器不允许使用
return返回一个返回值（即可以使用return从生成器中退出，但return后不能有任何表达式）。
"""

# 4. 使用send唤醒
"""
我们除了可以使用next()函数来唤醒生成器继续执行外，还可以使用send()函数来唤醒执行。
使用send()函数的一个好处是可以在唤醒的同时向断点处传入一个附加数据。

例子：执行到yield时，gen函数作用暂时保存，返回i的值; temp接收下次c.send("python")，
send发送过来的值，c.next()等价c.send(None)
"""


print("*" * 70)


def gen():
    i = 0
    while i < 5:
        temp = yield i
        print(temp)
        i += 1


f = gen()

print(next(f))
f.send('haha')
print(next(f))
f.send('haha')
print(next(f))
f.send('haha')
print(next(f))
f.send('haha')
print(next(f))
f.send('haha')