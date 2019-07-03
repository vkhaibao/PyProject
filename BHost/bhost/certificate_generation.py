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
from logbase import common
from logbase import task_client
from logbase import defines;
from logbase import paths;
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet

from logbase import common
from generating_log import system_log

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
certificate_generation = Blueprint('certificate_generation',__name__)

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

#HTMLEncode 
def HTMLEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	
#跳转至证书生成
@certificate_generation.route('/certificate_generation_show',methods=['GET','POST'])
def certificate_generation_show():
    debug('certificate_generation')
    sess=request.form.get('se')
    if sess<0:
        sess=""
    return render_template('certificate_generation.html',se=sess)
#生成证书
@certificate_generation.route('/add_webcrt',methods=['GET','POST'])
def add_webcrt():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	ip = request.form.get('a1')
	oper = request.form.get('o1')
	is_guide = request.form.get('is')
	
	iplist = request.form.get('a2')
	dnslist = request.form.get('a3')
	
	if iplist < 0:
		iplist = ''
	
	if dnslist < 0:
		dnslist = ''
		
	if is_guide < 0:
		is_guide = ''
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select count(*) from  public.\"WebCertConfig\";";
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	count = curs.fetchall()[0][0]
	if count  == 0:
		sql = "insert into public.\"WebCertConfig\"(\"WebCertConfigId\",\"ServerIP\") values(1,'%s');"%(ip);
	else:	
		sql = "update public.\"WebCertConfig\" set \"ServerIP\" ='%s';"%(ip);
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()
	
	
	content = "[global]\nclass = taskglobal\ntype = webCert\nip=%s\nflag=web\nis_guide=%s\niplist=%s\ndnslist=%s" %(ip,is_guide,iplist,dnslist)
	ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
	if ss == False:
		return "{\"Result\":false,\"ErrMsg\":\"证书生成失败：%s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
	
	if not system_log(system_user,oper,"成功","系统管理>证书生成"):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	
	return "{\"Result\":true,\"ErrMsg\":\"\"}"
@certificate_generation.route('/get_web_cert_config',methods=['GET','POST'])
def get_web_cert_config():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	sql = "select \"ServerIP\"from  public.\"WebCertConfig\";";
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	ServerIP = curs.fetchall()
	if ServerIP:
		ServerIP =ServerIP[0][0].encode('utf-8')	
	else:
		ServerIP = '';
		curs.close()
	conn.close()
	return "{\"Result\":true,\"ErrMsg\":\"\",\"ServerIP\":\"%s\"}" %(ServerIP) 
	
