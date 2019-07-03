#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
import pyodbc
import pyodbc
import MySQLdb
import json
import time

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
pwdauth_list = Blueprint('pwdauth_list',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 1000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
        path = "/var/tmp/debugrx_ccp.txt"
        fp = open(path,"a+")
        if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
# def sendlog(oper,desc,cname):
	# client_ip = request.remote_addr    #获取客户端IP
	# happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	# sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	# LogSet(None, sqlconf, 6)
	
#HTMLEncode 
def HTMLEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr
#打开管理权限创建页面
@pwdauth_list.route('/pwdauth_handle',methods=['GET','POST'])
def pwdauth_handle():
	tasktype = request.form.get("tasktype")
	pwdauthId = request.form.get("pwdauthId")
	paging = request.form.get("paging")
	if tasktype < 0:
		tasktype = "1"
	if pwdauthId < 0:
		pwdauthId = "0"
	if paging < 0:
		paging = "1"
	if tasktype == "3":
		t = "pwdauth_list.html"
	else:
		t = "pwdauth_add.html"
	return render_template(t,paging=paging,pwdauthId=pwdauthId,tasktype=tasktype)