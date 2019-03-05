# 2.1 列表常用操作
name_list = ["zhangsan", "lisi", "wangwu", "lisi"]
print(len(name_list))
print(name_list.count("lisi"))
for name in name_list:
    if name == 'lisi':
        print(name)
        print(name_list.index(name))
print("end")
print(name_list[3])

import keyword
print(keyword.kwlist)
# print(len(keyword.kwlist))

# 2.2 元组常用操作

# - 在 ipython3 中定义一个 元组，例如：info = ()
# - 输入 info. 按下 TAB 键，ipython 会提示 元组 能够使用的函数如下：
info = ("sunhaibao", 19)
print("%s 的年龄是 %d" % info)

# 字典基本操作
xiaoming = {"name": "小明",
            "age": 18,
            "gender": True,
            "height": 1.75}
for k in xiaoming:
    print("%s: %s" % (k, xiaoming[k]))
