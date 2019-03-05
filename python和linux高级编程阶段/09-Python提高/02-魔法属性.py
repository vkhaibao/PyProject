# coding=utf8
# 1. __doc__
import os
class Foo:
    """描述"""
    def func(self):
        pass

print(Foo.__doc__)

# 2. __module__ 和 __class__
# __module__ 表示当前操作的对象在哪个模块
# __class__ 表示当前操作的对象的类是什么
from time import sleep

print(sleep.__module__)  # 输出 test 即：输出模块
print(sleep.__class__)  # 输出 test.Person 即：输出类

# 5. __call__  对象后面加括号，触发执行。

class Foo:
    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        print('__call__')


obj = Foo()  # 执行 __init__
obj()  # 执行 __call__

# 6. __dict__ 类或对象中的所有属性  类的实例属性属于对象；类中的类属性和方法等属于类，即：
print(Foo.__dict__)

class Province(object):
    country = 'China'

    def __init__(self, name, count):
        self.name = name
        self.count = count

    def func(self, *args, **kwargs):
        print('func')

# 获取类的属性，即：类属性、方法、
print(Province.__dict__)
# 输出：{'__dict__': <attribute '__dict__' of 'Province' objects>, '__module__': '__main__', 'country': 'China', '__doc__': None, '__weakref__': <attribute '__weakref__' of 'Province' objects>, 'func': <function Province.func at 0x101897950>, '__init__': <function Province.__init__ at 0x1018978c8>}

obj1 = Province('山东', 10000)
print(obj1.__dict__)
# 获取 对象obj1 的属性
# 输出：{'count': 10000, 'name': '山东'}

obj2 = Province('山西', 20000)
print(obj2.__dict__)
# 获取 对象obj1 的属性
# 输出：{'count': 20000, 'name': '山西'}