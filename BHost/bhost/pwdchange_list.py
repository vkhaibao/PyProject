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
from comm_function import get_user_perm_value

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
pwdchange_list = Blueprint('pwdchange_list',__name__)

SIZE_PAGE = 20
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
#1创建 2编辑 3列表
@pwdchange_list.route('/pwdchange_handle',methods=['GET','POST'])
def pwdchange_handle():
	tasktype = request.form.get("tasktype")
	conn_d = request.form.get("a")
	page = request.form.get("c")
	search_typeall = request.form.get("d")
	e = request.form.get("e")
	us = request.form.get("us")
	se = request.form.get("se")
	debug(tasktype)
	if us<0:
		us=''
	if se<0:
		se=''
	if tasktype < 0:
		tasktype = "1"
	if conn_d<0 or conn_d == None:
		conn_d="0"
	if page<0 or page == None:
		page="1"
	if search_typeall<0 or search_typeall == None:
		search_typeall=""
	if e<0 or e==None:
		e=':'
	if tasktype == "3":
		conn_d='0'
		t = "pwdchange_list.html"
	else:
		t="pwdchange_add.html"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_1=1
	perm_client=0
	perm_client=0
	perm_host=1
	for i in perm_json:
		if i['SubMenuId']==14 and i['SystemMenuId']==3 and perm_host<i['Mode']:
			perm_host=i['Mode']
		elif i['SubMenuId']==13 and i['SystemMenuId']==3 and perm_client<i['Mode']:
			perm_client=i['Mode']
		elif i['SubMenuId']==21 and i['SystemMenuId']==4:
			perm=i['Mode']
			# if i['Mode']>perm_server:
			# 	perm_server=i['Mode']
			# if i['Mode']>perm_pwd_mod:
			# 	perm_pwd_mod=i['Mode']
		elif i['SubMenuId']==24 and i['SystemMenuId']==6 and perm_1<i['Mode']:
			perm_1=i['Mode']
		# elif i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm_server:
		# 	perm_server=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3 and i['Mode']>perm_client:
			perm_client=i['Mode']
		# 	perm_server=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3 and i['Mode']>perm_client:
			perm_client=i['Mode']
		# 	perm_server=i['Mode']
		elif  i['SubMenuId']==18 and i['SystemMenuId']==3 and i['Mode']>perm_client:
			perm_client=i['Mode']
		# 	perm_server=i['Mode']
		# elif  i['SubMenuId']==21 and i['SystemMenuId']==4:
		# 	if i['Mode']>perm_server:
		# 		perm_server=i['Mode']
		# 	if i['Mode']>perm_pwd_mod:
		# 		perm_pwd_mod=i['Mode']
		if perm_1==2 and perm==2 and perm_client==2 and perm_host==2:
			break
	perm_server=perm
	perm_pwd_mod=perm
	return render_template(t,tasktype=tasktype,a=conn_d,perm_host=perm_host,perm_client=perm_client,c=page,d=search_typeall,se=se,us=us,e=e,perm=perm,perm_pwd_mod=perm_pwd_mod,perm_1=perm_1,perm_server=perm_server)
