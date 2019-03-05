def measure():
    """返回当前的温度"""

    print("开始测量...")
    temp = 39
    wetness = 10
    print("测量结束...")

    return (temp, wetness)


# 在 Python 中，可以 将一个元组 使用 赋值语句 同时赋值给 多个变量
# 注意：变量的数量需要和元组中的元素数量保持一致

result = temp, wetness = measure()


# 只要 针对参数 使用 赋值语句，会在 函数内部 修改 局部变量的引用，不会影响到 外部变量的引用


def demo(num, num_list):
    print("函数内部")

    # 赋值语句
    num = 200
    num_list = [1, 2, 3]

    print(num)
    print(num_list)

    print("函数代码完成")


gl_num = 99
gl_list = [4, 5, 6]
demo(gl_num, gl_list)
print(gl_num)
print(gl_list)


# 如果传递的参数是 可变类型，在函数内部，使用 方法 修改了数据的内容，同样会影响到外部的数据


def mutable(num_list):
    # num_list = [1, 2, 3]
    num_list.extend([1, 2, 3])

    print(num_list)


gl_list = [6, 7, 8]
mutable(gl_list)
print(gl_list)


def demo(num, num_list):
    print("函数内部代码")

    # num = num + num
    num += num
    # num_list.extend(num_list) 由于是调用方法，所以不会修改变量的引用
    # 函数执行结束后，外部数据同样会发生变化
    num_list += num_list

    print(num)
    print(num_list)
    print("函数代码完成")


gl_num = 9
gl_list = [1, 2, 3]
demo(gl_num, gl_list)
print(gl_num)
print(gl_list)

gl_num_list = [6, 3, 9]

# 默认就是升序排序，因为这种应用需求更多
gl_num_list.sort()
print(gl_num_list)

# 只有当需要降序排序时，才需要传递 `reverse` 参数
gl_num_list.sort(reverse=True)
print(gl_num_list)


# 定义函数时，可以给 某个参数 指定一个默认值，具有默认值的参数就叫做 缺省参数
# 调用函数时，如果没有传入 缺省参数 的值，则在函数内部使用定义函数时指定的 参数默认值
# 函数的缺省参数，将常见的值设置为参数的缺省值，从而 简化函数的调用

def print_info(name, gender=True):
    gender_text = "男生"
    if not gender:
        gender_text = "女生"

    print("%s 是 %s" % (name, gender_text))


print_info("miaoyuanyuan")
print_info("sunhaibao", gender=False)


# 必须保证 带有默认值的缺省参数 在参数列表末尾
# 所以，以下定义是错误的！
# def print_info(name, gender=True, title):
# 在调用函数时，如果有多个缺省参数，需要指定参数名，这样解释器才能够知道参数的对应关系！
def print_info(name, title="", gender=True):
    """

    :param title: 职位
    :param name: 班上同学的姓名
    :param gender: True 男生 False 女生
    """

    gender_text = "男生"

    if not gender:
        gender_text = "女生"

    print("%s%s 是 %s" % (title, name, gender_text))


# 提示：在指定缺省参数的默认值时，应该使用最常见的值作为默认值！
print_info("小明")
print_info("老王", title="班长")
print_info("小美", gender=False)


# python 中有 两种 多值参数：

# 参数名前增加 一个 * 可以接收 元组
# 参数名前增加 两个 * 可以接收 字典
def demo(num, *args, **kwargs):
    print(num)
    print(args)
    print(kwargs)


demo(1, 2, 3, 4, 5, name="小明", age=18, gender=True)


def sum_numbers(*args):
    num = 0
    # 遍历 args 元组顺序求和
    for n in args:
        num += n

    return num


print(sum_numbers(1, 2, 3))

print("=" * 50)


def demo(*args, **kwargs):
    print(args)
    print(kwargs)


# 需要将一个元组变量/字典变量传递给函数对应的参数
gl_nums = (1, 2, 3)
gl_xiaoming = {"name": "小明", "age": 18}

# 会把 num_tuple 和 xiaoming 作为元组传递个 args
demo(gl_nums, gl_xiaoming)
demo(*gl_nums, **gl_xiaoming)
print("=" * 50)

'''
 函数的递归
 一个函数 内部 调用自己

 函数内部可以调用其他函数，当然在函数内部也可以调用自己

代码特点

1. 函数内部的 代码 是相同的，只是针对 参数 不同，处理的结果不同
2. 当 参数满足一个条件 时，函数不再执行
   - 这个非常重要，通常被称为递归的出口，否则 会出现死循环！
'''


def sum_numbers(num):
    print(num)

    # 递归的出口很重要，否则会出现死循环
    if num == 1:
        return

    sum_numbers(num - 1)


sum_numbers(3)

print("=" * 50)


def sum_numbers(num):
    """

    :param num:
    :return:
    """
    if num == 1:
        return 1
    sum = sum_numbers(num - 1)
    return num + sum


print(sum_numbers(5))

print("=" * 50)

'''
在 Python 中

- 变量 和 数据 是分开存储的
- 数据 保存在内存中的一个位置
- 变量 中保存着数据在内存中的地址
- 变量 中 记录数据的地址，就叫做 引用
- 使用 id() 函数可以查看变量中保存数据所在的 内存地址

注意：如果变量已经被定义，当给一个变量赋值的时候，本质上是 修改了数据的引用

- 变量 不再 对之前的数据引用
- 变量 改为 对新赋值的数据引用

'''
a = 10
b = a
b = 12
print(id(b))
print(id(a))
'''
1.3 函数的参数和返回值的传递

在 Python 中，函数的 实参/返回值 都是是靠 引用 来传递来的
'''


def test(num):
    print("-" * 50)
    print("%d 在函数内的内存地址是 %x" % (num, id(num)))

    result = 100

    print("返回值 %d 在内存中的地址是 %x" % (result, id(result)))
    print("-" * 50)

    return result


a = 10
print("调用函数前 内存地址是 %x" % id(a))

r = test(a)

print("调用函数后 实参内存地址是 %x" % id(a))
print("调用函数后 返回值内存地址是 %x" % id(r))

print("=" * 50)
a = [1, 2, 3]
print(id(a))
a = [3, 2, 1]
print(id(a))
print("=" * 50)

'''
可变和不可变类型

- 不可变类型，内存中的数据不允许被修改：
  - 数字类型 int, bool, float, complex, long(2.x)
  - 字符串 str
  - 元组 tuple
- 可变类型，内存中的数据可以被修改：
  - 列表 list
  - 字典 dict
  
  注意

1. 可变类型的数据变化，是通过 方法 来实现的
2. 如果给一个可变类型的变量，赋值了一个新的数据，引用会修改
   - 变量 不再 对之前的数据引用
   - 变量 改为 对新赋值的数据引用


'''
demo_list = [1, 2, 4]
print(demo_list)
print("定义列表后的内存地址 %d" % id(demo_list))

demo_list.append(999)
demo_list.pop(0)
demo_list.remove(2)
demo_list[0] = 10
print(demo_list)
print("修改数据后的内存地址 %d" % id(demo_list))

demo_dict = {"name": "小明"}

print("定义字典后的内存地址 %d" % id(demo_dict))

demo_dict["age"] = 18
demo_dict.pop("name")
demo_dict["name"] = "老王"

print("修改数据后的内存地址 %d" % id(demo_dict))
'''
哈希 (hash)

- Python 中内置有一个名字叫做 hash(o) 的函数
  - 接收一个 不可变类型 的数据作为 参数
  - 返回 结果是一个 整数
- 哈希 是一种 算法，其作用就是提取数据的 特征码（指纹）
  - 相同的内容 得到 相同的结果
  - 不同的内容 得到 不同的结果
- 在 Python 中，设置字典的 键值对 时，会首先对 key 进行 hash 已决定如何在内存中保存字典的数据，以方便 后续 对字典的操作：增、删、改、查
  - 键值对的 key 必须是不可变类型数据
  - 键值对的 value 可以是任意类型的数据

'''
print(hash("shbmyy0615"))
print(hash("shbmyy0615.."))
'''
注意：函数执行时，需要处理变量时 会：

1. 首先 查找 函数内部 是否存在 指定名称 的局部变量，如果有，直接使用
2. 如果没有，查找 函数外部 是否存在 指定名称 的全局变量，如果有，直接使用
3. 如果还没有，程序报错！

1) 函数不能直接修改 全局变量的引用

- 全局变量 是在 函数外部定义 的变量（没有定义在某一个函数内），所有函数 内部 都可以使用这个变量

提示：在其他的开发语言中，大多 不推荐使用全局变量 —— 可变范围太大，导致程序不好维护！

- 在函数内部，可以 通过全局变量的引用获取对应的数据
- 但是，不允许直接修改全局变量的引用 —— 使用赋值语句修改全局变量的值

'''
'''
2) 在函数内部修改全局变量的值

- 如果在函数中需要修改全局变量，需要使用 global 进行声明

3) 全局变量定义的位置

- 为了保证所有的函数都能够正确使用到全局变量，应该 将全局变量定义在其他函数的上方


'''
num = 10


def demo1():
    """

    """
    print("demo1" + "-" * 50)

    # global 关键字，告诉 Python 解释器 num 是一个全局变量
    global num
    # 只是定义了一个局部变量，不会修改到全局变量，只是变量名相同而已
    num = 100
    print(num)


def demo2():
    print("demo2" + "-" * 50)
    print(num)


demo1()
demo2()

print("over")
