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
access_set = Blueprint('access_set',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
        path = "/var/tmp/debugrxl.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	LogSet(None, sqlconf, 6)
	
#HTMLEncode 
def HTMLEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	
#创建 编辑 列表
@access_set.route('/timeset_list',methods=['GET','POST'])
def timeset_list():
	debug("timeset_list");
	tasktype = request.form.get("tasktype")
	debug(str(tasktype));
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1":
		t = "timeset_list.html"
	if tasktype=="3":
		t = "timeset_add.html"
	debug("end");
	return render_template(t,tasktype=tasktype)
#显示 or 分页 or 搜索
@access_set.route('/xx1',methods=['GET', 'POST'])
def xx1():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 10000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('se')
	num = request.form.get('num')
	paging = request.form.get('paging')
	search_typeall = request.form.get('search_typeall')
	id = request.form.get('DomainId')
	DomainName = ""
	ServerIP = ""
	if id<0:
		id=""
	if id!="":
		DomainId=int(id)
	else:
		DomainId=0
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	paging=int(paging)
	if paging <0:
		paging = 1
	num=int(num)
	if num <0:
		num = 5
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+11,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+12,ErrorEncode(e.args[1]))
	# PGetDomain(domainid,domainname,serverip,limitrow,offsetrow)
	# {"totalrow":1,"data":[
    # {
        # "DomainId": 1,
        # "DomainName": "主机域1",
        # "ServerIP": "192.168.0.1;192.168.0.55"        
    # }
	# ]}
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split(',')
	for search in typeall:
		search_s = search.split('-')
		if search_s[0]=="DomainName":
			DomainName=DomainName+search_s[1]+"\\n"
		elif search_s[0]=="ServerIP":
			ServerIP=ServerIP+search_s[1]+"\\n"
	sql=""
	if DomainId==0:
		sql = sql+"select public.\"PGetDomain\"(null,"
	else:
		sql = sql+"select public.\"PGetDomain\"(%d," % DomainId
	if DomainName=="":
		sql = sql+"null,"
	else:
		sql = sql+"'%s'," % DomainName[:-2]
	if ServerIP=="":
		sql = sql+"null,"
	else:
		sql = sql+"'%s'," % ServerIP[:-2]
	sql = sql+"%d,%d);" % (num,(paging-1)*num)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"连接参数查询异常(%d):%s\"}" %(ERRNUM_MODULE+13,ErrorEncode(e.args[1]))
	results = curs.fetchall()[0][0]
	if not results:
		return "{\"Result\":true,\"info\":{\"totalrow\":0,\"data\":[]}}" 
	else:
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":%s}" % results
#删除连接参数
@access_set.route('/xx2',methods=['GET', 'POST'])
def xx2():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('delect_str')
	session = request.form.get('se')
	ids = id_str.split(',')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+77,ErrorEncode(e.args[1]))
		
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+78,ErrorEncode(e.args[1]))
	for id in ids:
		id=int(id)
	# PDeleteDomain(domainid)
	# return
	# {"Result":false,"ErrMsg":"传入参数不正确"}或
	# {"Result":true,"RowCount":1}
		sql = "select public.\"PDeleteDomain\"(%d);" % (id)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"连接参数查询异常(%d):%s\"}" %(ERRNUM_MODULE+79,ErrorEncode(e.args[1]))
		result = curs.fetchall()[0][0]
		if "false" in result:
			curs.close()
			conn.close()
			return result
	conn.commit()
	curs.close()
	conn.close()
	return result  
