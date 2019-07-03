#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
macset_add = Blueprint('macset_add',__name__)

ERRNUM_MODULE_cmdset = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@macset_add.route('/get_macset_list',methods=['GET', 'POST'])
def get_macset_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	page = request.form.get('z5')
	ipage = request.form.get('z6')
	name = request.form.get('z7')
	keyword = request.form.get('z8')
	debug(keyword)
	debug("uuuuuiiii")
	keyword = keyword.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("|","\\\\|").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
	debug("tttttyyy")
	debug(keyword)
	page = int(page)
	ipage = int(ipage)
	if page < 0:
		page = 0
	if ipage < 0:
		ipage = 0
	row = page*(ipage-1)
	if keyword == "":
		type = 0
	else:
		type = 1
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == 0) or (name == '0'):
				debug("qwerqwe")
				curs.execute("select public.\"PGetMACSet\"(null,null,null,null,%d,%d);"%(page,row))
			else:
				if name == '1':
					curs.execute("select public.\"PGetMACSet\"(null,E'%s',null,null,%d,%d);"%(keyword,page,row))
			conn.commit()
			results = curs.fetchall()[0][0].encode('utf-8')
			debug("444")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))

@macset_add.route('/save_macset', methods=['GET','POST'])
def save_macset():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	name = request.form.get('d1')
	description = request.form.get('d2')
	mac_str = request.form.get('d3')
	type = request.form.get('d4')
	id = request.form.get('d5')
	description = description.replace('\\','\\\\\\\\').replace("'","''").replace('"','\\\\"')
	debug(mac_str)
	debug(type)
	debug(name)	
	mac_result = mac_str.split(';')
	debug("111")
	data = "E'{\"MACSetId\":\""+id+"\",\"Name\":\""+name+"\",\"Description\":\""+description+"\",\"Set\":["
	debug("222")
	debug(data)
	k = 1
	for i in mac_result:
		data = data +"{"+"\"MACSetMemberId\":0"+",\"Order\":\""+str(k)+"\",\"MACAddress\":\""+i+"\"},"
		k = k + 1
	data = data[:-1]
	data = data+"]}'"
	debug(data)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			debug("aaaa")
			curs = conn.cursor()
			debug("bbbbb")
			curs.execute("select public.\"PSaveMACSet\"(%s,0,null);"%(data))
			debug("cccc")
			results = curs.fetchall()[0][0].encode('utf-8')
			debug("ddddd")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))

@macset_add.route('/select_macset_all', methods=['GET','POST'])
def select_macset_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z11')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor();
			if id == "-1":
				curs.execute("select public.\"PGetMACSet\"(null,null,null,null,null,null);")
			else:	
				curs.execute("select public.\"PGetMACSet\"(%d,null,null,null,null,null);"%(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))

@macset_add.route('/delete_macset', methods=['GET','POST'])				
def delete_macset():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('z9')
	id = request.form.get('z10')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug(type)
			if (type == '1'):
				debug("kaishi")
				id_array = id[1:-1].split(',')
				debug("id_arrry")
				for id in id_array:
					debug(id)
					curs.execute("select public.\"PDeleteMACSet\"(%d,0,null);"%(int(id)))
					debug("jiehsu")
					conn.commit()
			else:
				curs.execute("select public.\"PDeleteMACSet\"(%d,0,null);"%(int(id)))
		return "{\"Result\":true}"	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))
