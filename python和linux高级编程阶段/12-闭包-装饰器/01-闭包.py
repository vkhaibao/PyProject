# coding=utf8
# 1. 函数引用
def test1():
    print("--- in test1 func----")

# 调用函数
test1()

# 引用函数
ret = test1

print(id(ret))
print(id(test1))

#通过引用调用函数
ret()

# 2. 什么是闭包 在函数内部再定义一个函数，并且这个函数用到了外边函数的变量，那么将这个函数以及用到的一些变量称之为闭包
# 定义一个函数
def test(number):

    # 在函数内部再定义一个函数，并且这个函数用到了外边函数的变量，那么将这个函数以及用到的一些变量称之为闭包
    def test_in(number_in):
        print("in test_in 函数, number_in is %d" % number_in)
        return number+number_in

    # 其实这里返回的就是闭包的结果
    return test_in

# 给test函数赋值，这个20就是给参数number
ret = test(20)

# 注意这里的100其实给参数number_in
print(ret(100))

# 注意这里的200其实给参数number_in

print(ret(200))

# 3. 看一个闭包的实际例子：
def line_conf(a, b):
    def line(x):
        return a*x+b
    return line


# 先引用line_conf函数 本质：是返回一函数体内的一个新的函数对象，然后调用新的函数
line1 = line_conf(1, 1)
line2 = line_conf(4, 5)
line3 = line_conf(2, 4)
#
print(line1(5))
print(line2(5))
print(line3(8))
print("*" * 50)

# 4. 修改外部函数中的变量
def counter(start=0):
    def incr():
        nonlocal start
        start += 1
        return start
    return incr


c1 = counter(5)
print(c1)
print(c1())
print(c1())