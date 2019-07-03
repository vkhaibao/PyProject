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
import base64

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
from htmlencode import parse_sess 
syswarn = Blueprint('syswarn',__name__)

ERRNUM_MODULE_syswarn = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

@syswarn.route('/syswarn_show',methods=['GET', 'POST'])
def syswarn_show():			
	return render_template('syswarn.html')

@syswarn.route('/get_syswarn_config',methods=['GET','POST'])
def get_syswarn_config():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetSystemAlarmConfig\"();")
			result = curs.fetchall()[0][0].encode('utf-8')
			return result
	except:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_syswarn + 3, ErrorEncode(e.args[1]))

@syswarn.route('/save_syswarn_config',methods=['GET','POST'])
def save_syswarn_config():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data = request.form.get('z1')
	session = request.form.get('a0')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PSaveSystemAlarmConfig\"(%s);"%(data))
			curs.execute("select public.\"PSaveSystemAlarmConfig\"(E\'%s\');"%(data))
			result = curs.fetchall()[0][0].encode('utf-8')
			sys_re = json.loads(result)
			if sys_re['Result']:
				system_log(userCode,"保存系统告警","成功","系统告警")
			else:
				system_log(userCode,"保存系统告警","失败："+sys_re['ErrMsg'],"系统告警")
			return result
	except:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_syswarn + 3, ErrorEncode(e.args[1]))
