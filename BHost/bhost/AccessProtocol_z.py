#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
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

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
AccessProtocol_z = Blueprint('AccessProtocol_z',__name__)

ERRNUM_MODULE_AccessProtocol_z = 1000

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

@AccessProtocol_z.route('/AccessProtocol_list',methods=['GET', 'POST'])
def AccessProtocol_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	ipage = request.form.get('z2')	
	keyword = request.form.get('z3')
	if keyword == None:
		keyword = "[]"
	return render_template('AccessProtocol_list.html',ipage=ipage,keyword=keyword)
	
@AccessProtocol_z.route('/create_AccessProtocol_z',methods=['GET', 'POST'])
def create_AccessProtocol_z():
	now = request.form.get('z1')
	edit = request.form.get('z2')
	type = request.form.get('z3')
	keyword = request.form.get('z4')
	t = "add_AccessProtocol_z.html"
	return render_template(t,edit=edit,now=now,tasktype=type,keyword=keyword)
	
@AccessProtocol_z.route("/save_AccessProtocol", methods=['GET', 'POST'])
def save_AccessProtocol():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	protocol = request.form.get('a1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_AccessProtocol_z+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_AccessProtocol_z+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_AccessProtocol_z+2,error)
	protocol = json.loads(protocol)			
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			for i in protocol:	
				i = i.replace("\t",'\\"')
				dec="select public.\"PSaveAccessProtocol\"(E'%s')" % (MySQLdb.escape_string(i).decode('utf-8'))
				curs.execute(dec)
				results = curs.fetchall()[0][0].encode('utf-8')
				ret = json.loads(results)         #json转python对象
				result = ret["Result"]
				if(result == False):
					return results
			return "{\"Result\":true}"
	except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"插入协议失败(%d): %s\"}"% (ERRNUM_MODULE_AccessProtocol_z + 1, ErrorEncode(e.args[1]))

@AccessProtocol_z.route("/get_AccessProtocol_all_z", methods=['GET', 'POST'])
def get_AccessProtocol_all_z():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_AccessProtocol_z+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_AccessProtocol_z+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_AccessProtocol_z+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()	
			curs.execute("select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"插入协议失败(%d): %s\"}"% (ERRNUM_MODULE_AccessProtocol_z + 1, ErrorEncode(e.args[1]))
