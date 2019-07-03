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
pwdresult_list = Blueprint('pwdresult_list',__name__)

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
	return newStr;	
#1创建 2编辑 3列表
@pwdresult_list.route('/pwdresult_handle',methods=['GET','POST'])
def pwdresult_handle():
	tasktype = request.form.get("tasktype")
	conn_d = request.form.get("a")
	pwdauth_page = request.form.get("c")
	pwdauth_search_typeall = request.form.get("d")
	se = request.form.get("se")
	us = request.form.get("us")
	if tasktype < 0:
		tasktype = "1"
	if conn_d<0 or conn_d == None:
		conn_d="0"
	if pwdauth_page<0 or pwdauth_page == None:
		pwdauth_page="1"
	if pwdauth_search_typeall<0 or pwdauth_search_typeall == None:
		pwdauth_search_typeall=""
	if tasktype == "3":
		t = "pwdauth_list.html"
	else:
		t = "pwdresult_list.html"
	return render_template(t,tasktype=tasktype,a=conn_d,c=pwdauth_page,d=pwdauth_search_typeall,us=us,se=se)
#显示连接参数 or 分页 or 搜索
@pwdresult_list.route('/get_pwdresult_list',methods=['GET', 'POST'])
def get_pwdresult_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	id = request.form.get('a1')
	
	if id<0 or id=="" or id=="0":
		id="null"
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	searchstring=''
	hostip=''
	hostname=''
	protocolname=''
	accountname=''
	starttime=''
	endtime=''
	username=''
	ExecuteUserName=''
	Status=''
	PwdModType=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="hostip":
			hostip=hostip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="hostname":
			hostname=hostname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="protocolname":
			protocolname=protocolname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="accountname":
			accountname=accountname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="starttime":
			starttime=starttime+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="endtime":
			endtime=endtime+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="username":
			username=username+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ExecuteUserName":
			ExecuteUserName=ExecuteUserName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Status":
			Status=Status+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="PwdModType":
			PwdModType=PwdModType+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"

	if hostip=="":
		hostip="null"
	else:
		hostip="'%s'"%hostip[:-1]
	if username=="":
		username="null"
	else:
		username="'%s'"%username[:-1]
	if hostname=="":
		hostname="null"
	else:
		hostname="E'%s'"%hostname[:-1]
	if protocolname=="":
		protocolname="null"
	else:
		protocolname="E'%s'"%protocolname[:-1]
	if accountname=="":
		accountname="null"
	else:
		accountname="E'%s'"%accountname[:-1]
	if starttime=="":
		starttime="null"
	else:
		starttime="E'%s'"%starttime[:-1]
	if endtime=="":
		endtime="null"
	else:
		endtime="E'%s'"%endtime[:-1]
	if searchstring!="":
		searchstring=searchstring[:-1]
	if ExecuteUserName!="":
		ExecuteUserName=ExecuteUserName[:-1]
	else:
		ExecuteUserName=None
	if Status!="":
		Status=Status[:-1]
		if Status=='准备':
			Status=0
		elif Status=='生成预备密码完成':
			Status=1
		elif Status=='可以执行改密':
			Status=2
		elif Status=='正在执行改密':
			Status=3
		elif Status=='成功':
			Status=4
		elif Status=='登录失败':
			Status=5
		elif Status=='改密失败':
			Status=6
		elif Status=='确认失败':
			Status=7
		elif Status=='域账号已改密':
			Status=8
		elif Status=='取消改密':
			Status=9
		elif Status=='所有':
			Status=None
	else:
		Status=None
	if PwdModType!="":
		PwdModType=PwdModType[:-1]
		if PwdModType=="自动改密":
			PwdModType=1
		elif PwdModType=="手工改密":
			PwdModType=2
	else:
		PwdModType=None
	searchconn={}
	searchconn['searchstring']=searchstring
	searchconn['ExecuteUserName']=ExecuteUserName
	searchconn['Status']=Status
	searchconn['PwdModType']=PwdModType
	searchconn=json.dumps(searchconn)
	hostip=hostip.replace("\\\\","\\\\\\\\")
	hostip=hostip.replace(".","\\\\.")
	hostip=hostip.replace("?","\\\\?")
	hostip=hostip.replace("+","\\\\+")
	hostip=hostip.replace("(","\\\\(")
	hostip=hostip.replace("*","\\\\*")
	hostip=hostip.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	username=username.replace("\\\\","\\\\\\\\")
	username=username.replace(".","\\\\.")
	username=username.replace("?","\\\\?")
	username=username.replace("+","\\\\+")
	username=username.replace("(","\\\\(")
	username=username.replace("*","\\\\*")
	username=username.replace("[","\\\\[")
	hostname=hostname.replace("\\\\","\\\\\\\\")
	hostname=hostname.replace(".","\\\\.")
	hostname=hostname.replace("?","\\\\?")
	hostname=hostname.replace("+","\\\\+")
	hostname=hostname.replace("(","\\\\(")
	hostname=hostname.replace("*","\\\\*")
	hostname=hostname.replace("[","\\\\[")
	protocolname=protocolname.replace("\\\\","\\\\\\\\")
	protocolname=protocolname.replace(".","\\\\.")
	protocolname=protocolname.replace("?","\\\\?")
	protocolname=protocolname.replace("+","\\\\+")
	protocolname=protocolname.replace("(","\\\\(")
	protocolname=protocolname.replace("*","\\\\*")
	protocolname=protocolname.replace("[","\\\\[")
	accountname=accountname.replace("\\\\","\\\\\\\\")
	accountname=accountname.replace(".","\\\\.")
	accountname=accountname.replace("?","\\\\?")
	accountname=accountname.replace("+","\\\\+")
	accountname=accountname.replace("(","\\\\(")
	accountname=accountname.replace("*","\\\\*")
	accountname=accountname.replace("[","\\\\[")
	starttime=starttime.replace("\\\\","\\\\\\\\")
	starttime=starttime.replace(".","\\\\.")
	starttime=starttime.replace("?","\\\\?")
	starttime=starttime.replace("+","\\\\+")
	starttime=starttime.replace("(","\\\\(")
	starttime=starttime.replace("*","\\\\*")
	starttime=starttime.replace("[","\\\\[")
	endtime=endtime.replace("\\\\","\\\\\\\\")
	endtime=endtime.replace(".","\\\\.")
	endtime=endtime.replace("?","\\\\?")
	endtime=endtime.replace("+","\\\\+")
	endtime=endtime.replace("(","\\\\(")
	endtime=endtime.replace("*","\\\\*")
	endtime=endtime.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			#PGetPwdModTaskDetails(pwdmodtaskid,hostip,hostname,protocolname,accountname,starttime,endtime,limitrow,offsetrow)
			sql="select public.\"PGetPwdModTaskDetails\"(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,E'%s');"% (id,hostip,hostname,protocolname,accountname,starttime,endtime,username,num,paging,searchconn)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
