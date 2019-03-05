import keyword
print(keyword.kwlist)
# 1. 定义年龄变量
age = int(input("age:"))

# 2. 判断是否满 18 岁
# if 语句以及缩进部分的代码是一个完整的代码块
if age >= 18:
    print("可以进网吧嗨皮……")
else:
    print("NO")
# 3. 思考！- 无论条件是否满足都会执行
print("这句代码什么时候执行?")
