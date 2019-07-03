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
from htmlencode import parse_sess
from htmlencode import check_role

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
ip_list = Blueprint('ip_list',__name__)

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
# def sendlog(oper,desc,cname):
	# client_ip = request.remote_addr    #获取客户端IP
	# happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	# sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	# LogSet(None, sqlconf, 6)
	
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
#1创建 2编辑 3列表
@ip_list.route('/ipset_handle',methods=['GET','POST'])
def ipset_handle():
	tasktype = request.form.get("tasktype")
	ipsetId = request.form.get("ipsetId")
	paging = request.form.get("paging")
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or tasktype == "2":
		t = "ip_add.html"
	if tasktype == "3":
		t = "ip_list.html"
		ipsetId="0"
	return render_template(t,tasktype=tasktype,ipsetId=ipsetId,paging=paging)
#跳转至IP集合
@ip_list.route('/ip_show',methods=['GET','POST'])
def ip_show():
	sess=request.form.get('se')
	if sess<0:
		sess=""
	return render_template('ip_list.html',se=sess,paging="1")
#显示 or 分页 or 搜索
@ip_list.route('/get_ipset_list',methods=['GET', 'POST'])
def get_ipset_list():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 10000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('se')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	noset = request.form.get('a5')
	ipsetId = request.form.get('a1')
	search_typeall = request.form.get('a2')
	Name="";
	Description="";
	if search_typeall<0:
		search_typeall=""
	if noset<0 or noset=="":
		noset="false"
	if ipsetId<0 or ipsetId=="0" or ipsetId=="":
		ipsetId="null"
	if sess < 0:
		sess = ""
	
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+11,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+12,ErrorEncode(e.args[1]))
	# PGetIPSet(ipsetid,noset,limitrow,offsetrow)
	# {"totalrow":2,"data":[
    # {
        # "IPSetId": 1,    
        # "Name": "IP策略1",
        # "Description": null,    
        # "Set": [
            # {
                # "IPSetMemberId": 1,
                # "Order": 1,
                # "StartIP": "192.168.0.1", 
                # "EndIP": "192.168.0.100"                               
            # },
            # {
                # "IPSetMemberId": 3,
                # "Order": 2,
                # "StartIP": "192.168.0.150",  
                # "EndIP": "192.168.0.160"                              
            # }
        # ]
    # },
    # {
        # "IPSetId": 2,    
        # "Name": "IP策略2",
        # "Description": null,    
        # "Set": [
            # {
                # "IPSetMemberId": 2,
                # "Order": 1,
                # "StartIP": "192.168.0.80", 
                # "EndIP": "192.168.0.200"                              
            # }
        # ]
    # }
	# ]}
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Description":
			Description=Description+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	if Description=="":
		Description="null"
	else:
		Description="E'%s'"%(Description[:-1])
	Name=Name.replace("\\\\","\\\\\\\\");
	Name=Name.replace(".","\\\\.");
	Name=Name.replace("?","\\\\?");
	Name=Name.replace("+","\\\\+");
	Name=Name.replace("(","\\\\(");
	Name=Name.replace("*","\\\\*");
	Name=Name.replace("[","\\\\[");
	Description=Description.replace("\\\\","\\\\\\\\");
	Description=Description.replace(".","\\\\.");
	Description=Description.replace("?","\\\\?");
	Description=Description.replace("+","\\\\+");
	Description=Description.replace("(","\\\\(");
	Description=Description.replace("*","\\\\*");
	Description=Description.replace("[","\\\\[");
	if paging!="null":
		paging=(paging-1)*num;
	sql="select public.\"PGetIPSet\"(%s,%s,%s,%s,%s,%s);"%(ipsetId,Name,Description,noset,num,paging)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"查询异常(%d):%s\"}" %(ERRNUM_MODULE+13,ErrorEncode(e.args[1]))
	results = curs.fetchall()[0][0]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" % results
#创建 or 编辑
@ip_list.route('/add_ipset',methods=['GET', 'POST'])
def add_ipset():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('se')
	ipset = request.form.get('a1')
	ipset=str(ipset)
	fid = request.form.get('a3')
	iptype = request.form.get('a2')
	if session < 0:
		session = ""
	if iptype < 0 or iptype=="":
		iptype = "0"
	if fid < 0 or fid=="":
		fid = "null"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+11,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+12,ErrorEncode(e.args[1]))
	# PSaveIPSet(jsondata)
	# return
	# {
        # "IPSetId": 0,    --新增IP区间，IPSetId和IPSetMemberId为0 
        # "Name": "IP策略1",
        # "Description": null,    
        # "Set": [
            # {
                # "IPSetMemberId": 0,
                # "Order": 1,
                # "StartIP": "192.168.0.1", 
                # "EndIP": "192.168.0.100"                               
            # },
            # {
                # "IPSetMemberId": 0,
                # "Order": 2,
                # "StartIP": "192.168.0.150",  
                # "EndIP": "192.168.0.160"                              
            # }
        # ]
	# }
	sql="select public.\"PSaveIPSet\"(E'%s',%s,%s);" %(MySQLdb.escape_string(ipset).decode("utf-8"),iptype,fid)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"添加异常(%d):%s\"}" %(ERRNUM_MODULE+79,ErrorEncode(e.args[1]))
	result = curs.fetchall()[0][0]
	conn.commit()
	curs.close()
	conn.close()
	return result  
#删除认证方式
@ip_list.route('/del_ipset',methods=['GET', 'POST'])
def del_ipset():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	iptype = request.form.get('a2')
	fid = request.form.get('a3')
	session = request.form.get('se')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	if fid < 0 or fid=="":
		fid = "null"
	if iptype < 0 or iptype=="":
		iptype = "0"
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
	# PDeleteIPSet(ipsetid,iptype,fid)
	# return
	# {"Result":false,"ErrMsg":"传入参数不正确"}或
	# {"Result":true,"RowCount":1}
		sql = "select public.\"PDeleteIPSet\"(%d,%s,%s);" % (id,iptype,fid)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"删除异常(%d):%s\"}" %(ERRNUM_MODULE+79,ErrorEncode(e.args[1]))
		result = curs.fetchall()[0][0]
		if "false" in result:
			curs.close()
			conn.close()
			return result
	conn.commit()
	curs.close()
	conn.close()
	return result  