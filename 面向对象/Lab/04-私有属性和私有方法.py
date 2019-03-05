"""
01. 应用场景及定义方式
应用场景

在实际开发中，对象 的 某些属性或方法 可能只希望 在对象的内部被使用，而 不希望在外部被访问到
私有属性 就是 对象 不希望公开的 属性
私有方法 就是 对象 不希望公开的 方法
定义方式

在 定义属性或方法时，在 属性名或者方法名前 增加 两个下划线，定义的就是 私有 属性或方法
"""


class Women:
    def __init__(self, name):
        self.name = name
        self.__age = 18

    def __secret(self):
        print("我的年龄是 %d" % self.__age)
        pass
    pass


xiaofang = Women("xiaofang")
#print(xiaofang.name)

# 私有属性，外部不能直接访问


# 私有方法，外部不能直接调用
#print(xiaofang.__secret())
# 私有属性，外部不能直接访问到
"""
02. 伪私有属性和私有方法（科普）
提示：在日常开发中，不要使用这种方式，访问对象的 私有属性 或 私有方法

Python 中，并没有 真正意义 的 私有

在给 属性、方法 命名时，实际是对 名称 做了一些特殊处理，使得外界无法访问到
处理方式：在 名称 前面加上 _类名 => _类名__名称
"""
print(xiaofang._Women__age)

# 私有方法，外部不能直接调用
xiaofang._Women__secret()
