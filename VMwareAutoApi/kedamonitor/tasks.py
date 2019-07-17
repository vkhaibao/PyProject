from __future__ import absolute_import, unicode_literals
from VMwareAutoApi.celery import app
from .kedaopmanage.kedaopm import *

@app.task
def getinfo():
    url = "http://10.2.2.33:8086/fault/AlarmView.do?viewId=ActiveAlarms"
    username = "admin"
    password = "admin"
    resultinfo = getalertinfo(url, username, password)
    return resultinfo