# -*- coding: utf-8 -*-
import urllib
from bs4 import BeautifulSoup
from http import cookiejar
import http
import json
import wmi
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
c = wmi.WMI()
# 获取主板序列号
sn = c.Win32_BaseBoard()[0].SerialNumber.strip()
beg = sn.find('/')
sn = sn[beg+1:]
end = sn.find('/')
sn = sn[:end]
# 通过handler来构建opener
cookie = http.cookiejar.CookieJar()
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)
loginurl = "https://sso.kedacom.com:8443/CasServer/login"

# 登陆前准备：获取 lt 和 "exection"
response = opener.open(loginurl)
soup = BeautifulSoup(response.read(), "lxml")
for input in  soup.form.find_all("input"):
    if input.get("name") == "lt":
        lt = input.get("value")
    if input.get("name") == "execution":
        execution = input.get("value")
    if input.get("name") == "vcode":
        vcode = input.get("value")
    if input.get("name") == "rememberMetest":
        rememberMetest = input.get("value")
    if input.get("name") == "_eventId":
        _eventId = input.get("value")
# post信息
values = {
        "username":
            "sunhaibao@kedacom.com",
        "password":
            "shbmyy0615..",
        "vcode":
            vcode,
        'rememberMetest':
            rememberMetest,
        'lt':
            lt,
        'execution':
            execution,
        '_eventId':
             _eventId,
        'submit':
            ''    }
postdata = urllib.parse.urlencode(values).encode('utf-8')
opener.addheaders = [("Content-Type", "application/x-www-form-urlencoded")]
result = opener.open(loginurl, postdata)
url = "https://oa.kedacom.com/assets-webapp/assets/manage/getAssetsList.do?code="+sn
result = opener.open(url)
hjson = json.loads(result.read())
for k in hjson['rows'][0]:
    if hjson['rows'][0][k] is not None:
        print("%s = %s " % (k, hjson['rows'][0][k]), end="\n")
