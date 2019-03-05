# coding=utf8
from gevent import monkey
import gevent
import urllib.request
# 有耗时操作时需要

monkey.patch_all()
def download(url):
    print("GET : %s" % url)
    resp = urllib.request.urlopen(url)
    data =resp.read()
    print('%d bytes received from %s.' % (len(data), url))


gevent.joinall([
    gevent.spawn(download, "https://www.baidu.com/"),
    gevent.spawn(download, "http://www.kedacom.com/"),
    gevent.spawn(download, "http://www.itheima.com/")
])


monkey.patch_all()

def download_v(filename, url):
    print('GET: %s' % url)
    resp = urllib.request.urlopen(url)
    data = resp.read()

    with open(filename, "wb") as f:
        f.write(data)

    print('%d bytes received from %s.' % (len(data), url))
gevent.joinall([
        gevent.spawn(download_v, "bg.jpg", 'https://sso.kedacom.com:8443/CasServer/themes/20181114/images/bg.jpg'),
        gevent.spawn(download_v, "submit.png", 'https://sso.kedacom.com:8443/CasServer/themes/20181114/images/submit.png'),
])