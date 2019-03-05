#coding=utf-8
# 1. re模块的使用过程
# 导入re模块
import re

# 使用match方法进行匹配操作
#result = re.match(正则表达式,要匹配的字符串)

# 如果上一步匹配到数据的话，可以使用group方法来提取数据
#result.group()

# 2. re模块示例(匹配以itcast开头的语句)
result = re.match("itcast", "itcast.cn")

print(result.group())
"""
3. 说明
re.match() 能够匹配出以xxx开头的字符串
"""