# coding=utf8
from time import ctime, sleep
"""
装饰器
    装饰器是程序开发中经常会用到的一个功能，用好了装饰器，开发效率如虎添翼，所以这也是Python面试中必问的问题，
    但对于好多初次接触这个知识的人来讲，这个功能有点绕，自学时直接绕过去了，然后面试问到了就挂了，
    因为装饰器是程序开发的基础知识，这个都不会，别跟人家说你会Python, 看了下面的文章，保证你学会装饰器。
"""
# 1、先明白这段代码
#### 第一波 ####
def foo():
    print('foo')

print(foo)
foo  # 表示是函数
foo()  # 表示执行foo函数

#### 第二波 ####
def foo():
    print('foo')

foo = lambda x: x + 1

print(foo(10))  # 执行lambda表达式，而不再是原来的foo函数，因为foo这个名字被重新指向了另外一个匿名函数

"""
 函数名仅仅是个变量，只不过指向了定义的函数而已，所以才能通过 函数名()调用，如果 函数名=xxx被修改了，
 那么当在执行 函数名()时，调用的就不知之前的那个函数了
"""

"""
写代码要遵循开放封闭原则，虽然在这个原则是用的面向对象开发，但是也适用于函数式编程，
简单来说，它规定已经实现的功能代码不允许被修改，但可以被扩展，
即：
封闭：已实现的功能代码块
开放：对扩展开发
"""

print("*" * 50)
def w1(func):
    def inner():
        print("验证1")
        print("验证2")
        print("验证3")
        func()

    return inner

@w1
def f1():
    print('f1')


f1()
"""
python解释器就会从上到下解释代码，步骤如下：

   1、 def w1(func): ==>将w1函数加载到内存
   2、 @w1
没错， 从表面上看解释器仅仅会解释这两句代码，因为函数在 没有被调用之前其内部代码不会被执行。

从表面上看解释器着实会执行这两句，但是 @w1 这一句代码里却有大文章， @函数名 是python的一种语法。
"""
"""
上例@w1内部会执行一下操作：
    执行w1函数 
        并将 @w1 下面的函数作为w1函数的参数，即：@w1 等价于 w1(f1) 所以，内部就会去执行：
        def inner(): 
            #验证 1
            #验证 2
            #验证 3
            f1()    # func是参数，此时 func 等于 f1 
        return inner # 返回的 inner，inner代表的是函数，非执行函数 ,其实就是将原来的 f1 函数塞进另外一个函数中
    w1的返回值
        将执行完的w1函数返回值 赋值 给@w1下面的函数的函数名f1 即将w1的返回值再重新赋值给 f1，即：
        新f1 = def inner(): 
            #验证 1
            #验证 2
            #验证 3
            原来f1()
        return inner
"""


# 3. 再议装饰器

# 定义函数：完成包裹数据

def makeBold(fn):
    def wrapped():
        return "<b>" + fn() + "</b>"
    return wrapped
# 定义函数：完成包裹数据

def makeItalic(fn):
    def wrapped():
        return "<i>" + fn() + "</i>"
    return wrapped

@makeBold
def test1():
    return "hello world-1"

@makeItalic
def test2():
    return "hello world-2"

@makeBold
@makeItalic
def test3():
    return "hello world-3"

print(test3())

"""
4. 装饰器(decorator)功能
    引入日志
    函数执行时间统计
    执行函数前预备处理
    执行函数后清理功能
    权限校验等场景
    缓存
"""
print("===========例1:无参数的函数============")
# 5. 装饰器示例

def timefun(func):
    def wrapped_func():
        print("%s called at %s" % (func.__name__, ctime()))
        func()
    return wrapped_func

@timefun
def foo():
    print("I am foo")

foo()
sleep(2)
foo()


"""
上面代码理解 装饰器执行行为 可理解成
    foo = timefun(foo)
    # foo先作为参数赋值给func后,foo接收指向timefun返回的wrapped_func
    foo()
    # 调用foo(),即等价调用wrapped_func()
    # 内部函数wrapped_func被引用，所以外部函数的func变量(自由变量)并没有释放
    # func里保存的是原foo函数对象
"""

print("===========例2:被装饰的函数有参数============")


def timefun(func):
    def wrapped_func(a, b):
        print("%s called at %s" % (func.__name__, ctime()))
        print(a, b)
        func(a, b)
    return wrapped_func

@timefun
def foo(a, b):
    print(a+b)


foo(3, 5)
sleep(2)
foo(2, 4)

print("=========例3:被装饰的函数有不定长参数===========")
def timefun(func):
    def wrapped_func(*args, **kwargs):
        print("%s called at %s"%(func.__name__, ctime()))
        func(*args, **kwargs)
    return wrapped_func

@timefun
def foo(a, b, c):
    print(a+b+c)

foo(3,5,7)
sleep(2)
foo(2,4,9)

print("==========例4:装饰器中的return==========")
def timefun(func):
    def wrapped_func():
        print("%s called at %s" % (func.__name__, ctime()))
        func()
    return wrapped_func

@timefun
def foo():
    print("I am foo")

@timefun
def getInfo():
    return '----hahah---'

foo()
sleep(2)
print("---------------")
foo()
print("---------------")
print(getInfo())

# 总结：
# 一般情况下为了让装饰器更通用，可以有return


print("====例5:装饰器带参数,在原有装饰器的基础上，设置外部变量====")

def timefun_arg(pre="hello"):
    def timefun(func):
        def wrapped_func():
            print("%s called at %s %s" % (func.__name__, ctime(), pre))
            return func()
        return wrapped_func
    return timefun

# 下面的装饰过程
# 1. 调用timefun_arg("itcast")
# 2. 将步骤1得到的返回值，即time_fun返回， 然后time_fun(foo)
# 3. 将time_fun(foo)的结果返回，即wrapped_func
# 4. 让foo = wrapped_fun，即foo现在指向wrapped_func
@timefun_arg("itcast")
def foo():
    print("I am foo")

@timefun_arg("python")
def too():
    print("I am too")

foo()
sleep(2)
foo()

too()
sleep(2)
too()
# 可以理解为 foo()==timefun_arg("itcast")(foo)()

"""
例6：类装饰器（扩展，非重点）
    装饰器函数其实是这样一个接口约束，它必须接受一个callable对象作为参数，然后返回一个callable对象。
    在Python中一般callable对象都是函数，但也有例外。只要某个对象重写了 __call__() 方法，那么这个对象就是callable的。
"""

class Test():
    def __call__(self):
        print('call me!')


t = Test()
t()  # call me