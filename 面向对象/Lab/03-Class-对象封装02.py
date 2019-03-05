"""
目标
士兵突击案例
身份运算符
封装

封装 是面向对象编程的一大特点
面向对象编程的 第一步 —— 将 属性 和 方法 封装 到一个抽象的 类 中
外界 使用 类 创建 对象，然后 让对象调用方法
对象方法的细节 都被 封装 在 类的内部
一个对象的 属性 可以是 另外一个类创建的对象

01. 士兵突击
需求

士兵 许三多 有一把 AK47
士兵 可以 开火
枪 能够 发射 子弹
枪 装填 装填子弹 —— 增加子弹数量
"""


class Gun:
    def __init__(self, model):
        self.model = model
        self.bullet_count = 0

    def add_bullet(self, count):
        self.bullet_count += count

    def shoot(self):
        # 判断是否还有子弹
        if self.bullet_count <= 0:
            print("没有子弹了...")

            return

        # 发射一颗子弹
        self.bullet_count -= 1

        print("%s 发射子弹[%d]..." % (self.model, self.bullet_count))


class Soldier:
    def __init__(self, name):
        self.name = name
        self.gun = None

    def fire(self):
        # 1. 判断士兵是否有枪
        if self.gun is None:
            print("[%s] 还没有抢" % self.name)
            return
        print("%s有 %s" % (self.name, self.gun.model))
        # 2. 高喊口号
        print("冲啊...[%s]" % self.name)

        # 3. 让枪装填子弹
        if self.gun.bullet_count <= 0:
            self.gun.add_bullet(50)
        # 4. 让枪发射子弹
        self.gun.shoot()

    # 创建枪对象


ak47 = Gun("UZI")

xusanduo = Soldier("许三多")
xusanduo.gun = ak47
xusanduo.fire()
xusanduo.fire()
xusanduo.fire()
xusanduo.fire()
xusanduo.fire()
xusanduo.fire()
xusanduo.fire()
xusanduo.fire()

"""
02. 身份运算符
身份运算符用于 比较 两个对象的 内存地址 是否一致 —— 是否是对同一个对象的引用

在 Python 中针对 None 比较时，建议使用 is 判断
运算符	描述	实例
is	is 是判断两个标识符是不是引用同一个对象	x is y，类似 id(x) == id(y)
is not	is not 是判断两个标识符是不是引用不同对象	x is not y，类似 id(a) != id(b)
is 与 == 区别：
is 用于判断 两个变量 引用对象是否为同一个 
== 用于判断 引用变量的值 是否相等
"""
b = 1
a = 1

print(id(a))
print(id(b))

a = [1, 2, 3]
b = [1, 2, 3]

print(id(a))
print(id(b))