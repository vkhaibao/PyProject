# coding=utf8
import re
"""
匹配多个字符
匹配多个字符的相关格式
    字符	功能
    *	匹配前一个字符出现0次或者无限次，即可有可无
    +	匹配前一个字符出现1次或者无限次，即至少有1次
    ?	匹配前一个字符出现1次或者0次，即要么有1次，要么没有
    {m}	匹配前一个字符出现m次
    {m,n}	匹配前一个字符出现从m到n次
"""
# 示例1：*
# 需求：匹配出，一个字符串第一个字母为大小字符，后面都是小写字母并且这些小写字母可有可无
ret = re.match("[A-Z][a-z]*", "A")
print(ret.group())
ret = re.match("[A-Z][a-z]*\s*[a-z]*", "Hello python")
print(ret.group())
ret = re.match("[A-Z][a-z]*\s*[a-z]*", "Hello pythoN")
print(ret.group())

# 示例2：+
# 需求：匹配出，变量名是否有效
names = ["name1", "_name", "2_name", "__name__"]
for name in names:
    ret = re.match("[a-zA-Z_]+[\w]", name)
    if ret:
        print("变量名 %s 符合要求" % ret.group())
    else:
        print("变量名 %s 非法" % name)

# 示例3：?
# 需求：匹配出，0到99之间的数字
ret = re.match("[0-9]?[0-9]", "99")
print(ret.group())

ret = re.match("[1-9]?\d", "33")
print(ret.group())

ret = re.match("[1-9]?\d", "09")  # 这个结果并不是想要的，利用$才能解决
print(ret.group())

# 示例4：{m}
# 需求：匹配出，8到20位的密码，可以是大小写英文字母、数字、下划线

ret = re.match("[a-zA-Z0-9_]{8,20}", "klasdlf123")
print(ret.group())

# 题目1：匹配出163的邮箱地址，且@符号之前有4到20位，例如hello@163.com
mail_l = ["sunhaibao@163.com", "280764069@qq.com", "sunhaibao@163.com123"]
for mail in mail_l:
    #ret =re.match("[a-zA-Z0-9]{4,20}@163.com", mail)
    ret =re.match("[\w]{4,20}@163\.com", mail)  # 同作用
    if ret:
        print("是163的邮箱，邮箱地址为：%s  %s " % (mail, ret.group()))
    else:
        print("非163邮箱地址，邮箱地址为：%s " % mail)
