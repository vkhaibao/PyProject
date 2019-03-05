# coding=utf8
import re
"""
匹配开头结尾
    字符	功能
        ^	匹配字符串开头
        $	匹配字符串结尾
"""
# 示例1：$
email_list = ["xiaoWang@163.com", "xiaoWang@163.comheihei", ".com.xiaowang@qq.com123"]

for email in email_list:
    ret = re.match("[\w]{4,20}@163\.com$", email)
    if ret:
        print("%s 是符合规定的邮件地址,匹配后的结果是:%s" % (email, ret.group()))
    else:
        print("%s 不符合要求" % email)