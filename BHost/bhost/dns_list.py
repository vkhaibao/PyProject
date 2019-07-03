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
from logbase import task_client
from logbase import defines
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
dns_list = Blueprint('dns_list',__name__)
module = "系统管理>网络设置"
SIZE_PAGE = 20
def debug(c):
	return 0
	path = "/var/tmp/debugyt.txt"
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
	
	
#跳转至dns页面
@dns_list.route('/dns_show',methods=['GET','POST'])
def dns_show():
	session=request.form.get('se')
	if session<0:
		session=""
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	error_msg ='';
	
	if error < 0:
		error_msg =  "系统繁忙(%d)" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			error_msg =  "非法访问(%d)" %(sys._getframe().f_lineno)
		else:
			error_msg =  "系统超时(%d)" %(sys._getframe().f_lineno)
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetDNSConfig\"();"
			debug(sql)
			curs.execute(sql)
			data = curs.fetchall()[0][0]
			if data :
				DNSIP = json.loads(data)['DNSIP'];
				DNSConfigId = json.loads(data)['DNSConfigId'];
			else:
				DNSIP='';
				DNSConfigId =0;
			
			#{"DNSConfigId": 1,"DNSIP": "192.168.0.0,192.168.0.1"} 
				
	except pyodbc.Error,e:
		error_msg = ErrorEncode(e.args[1])
		
	return render_template('dns_list.html',se=session,error_msg=error_msg,DNSIP=DNSIP,DNSConfigId=DNSConfigId)
	
#跳转至dns页面
@dns_list.route('/save_dns',methods=['GET','POST'])
def save_dns():	
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	'''
	{
        "DNSConfigId": 1,
        "DNSIP": ""
	}
	'''
	if check_role(userCode,"系统管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	DNSConfigId = request.form.get('c1')
	DNSIP = request.form.get('i1')
	oper = request.form.get('o1')
	
	if DNSIP < 0:
		DNSIP = '';
	if DNSConfigId < 0 or DNSConfigId == "":
		DNSConfigId = '0';
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PSaveDNSConfig\"('{\"DNSConfigId\":%s,\"DNSIP\":\"%s\"}');" %(DNSConfigId,DNSIP)
			debug(sql)
			curs.execute(sql)
			data = curs.fetchall()[0][0]
			
			if json.loads(data)['Result'] == False:
				msg = json.loads(data)['ErrMsg']
				if not system_log(userCode,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return data
			conn.commit();
			#{"DNSConfigId": 1,"DNSIP": "192.168.0.0,192.168.0.1"} 
			###下发任务
			task_content = '[global]\nclass = taskglobal\ntype = dns_set\ndns_ip=%s'%(DNSIP);
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				msg = "系统异常: %s(%d)"%(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
			
			if not system_log(userCode,oper,"成功",module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return data;
	except pyodbc.Error,e:
		error_msg = ErrorEncode(e.args[1])
		return "{\"Result\":false,\"info\":\"系统异常：%s(%d)\"}" %(error_msg,sys._getframe().f_lineno)
		
	
	
	
	