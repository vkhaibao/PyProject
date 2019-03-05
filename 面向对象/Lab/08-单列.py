"""
目标
单例设计模式(单实例)
__new__ 方法
Python 中的单例

01. 单例设计模式
    设计模式
        设计模式 是 前人工作的总结和提炼，通常，被人们广泛流传的设计模式都是针对 某一特定问题 的成熟的解决方案
        使用 设计模式 是为了可重用代码、让代码更容易被他人理解、保证代码可靠性
    单例设计模式
        目的 —— 让类创建的对象，在系统中只有唯一的一个实例
        每一次执行 类名() 返回的对象，内存地址是相同的
单例设计模式的应用场景
音乐播放 对象
回收站 对象
打印机 对象

02. __new__ 方法
    使用 类名() 创建对象时，Python 的解释器 首先 会 调用 __new__ 方法为对象 分配空间
    __new__ 是一个 由 object 基类提供的 内置的静态方法，主要作用有两个：
        1) 在内存中为对象 分配空间
        2) 返回 对象的引用
    Python 的解释器获得对象的 引用 后，将引用作为 第一个参数，传递给 __init__ 方法
        重写 __new__ 方法 的代码非常固定！
    重写 __new__ 方法 一定要 return super().__new__(cls)
    否则 Python 的解释器 得不到 分配了空间的 对象引用，就不会调用对象的初始化方法
    注意：__new__ 是一个静态方法，在调用时需要 主动传递 cls 参数
"""


class MusicPlayer01(object):

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        print("初始化音乐播放对象")


player01 = MusicPlayer01()
player02 = MusicPlayer01()
print(id(player01))
print(id(player02))
print("=" * 50)
"""
03. Python 中的单例
    单例 —— 让 类 创建的对象，在系统中 只有 唯一的一个实例
        定义一个 类属性，初始值是 None，用于记录 单例对象的引用
        重写 __new__ 方法
        如果 类属性 is None，调用父类方法分配空间，并在类属性中记录结果
        返回 类属性 中记录的 对象引用
        
    只执行一次初始化工作
    在每次使用 类名() 创建对象时，Python 的解释器都会自动调用两个方法：
        __new__ 分配空间
        __init__ 对象初始化
    在上一小节对 __new__ 方法改造之后，每次都会得到 第一次被创建对象的引用
    但是：初始化方法还会被再次调用
    
需求

    让 初始化动作 只被 执行一次
    解决办法
    定义一个类属性 init_flag 标记是否 执行过初始化动作，初始值为 False
    在 __init__ 方法中，判断 init_flag，如果为 False 就执行初始化动作
    然后将 init_flag 设置为 True
    这样，再次 自动 调用 __init__ 方法时，初始化动作就不会被再次执行 了  
"""


class MusicPlayer02(object):

    instance = None
    init_flag = False

    def __new__(cls, *args, **kwargs):

        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, name):
        if not MusicPlayer02.init_flag:
            self.name = name
            print("%s" % self.name)
            MusicPlayer02.init_flag = True
        else:
            print("%s" % self.name)


player03 = MusicPlayer02("Test")
print(id(player03))
player04 = MusicPlayer02("Sun")
print(id(player04))
player05 = MusicPlayer02("Son")
print(id(player05))