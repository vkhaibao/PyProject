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
from index import PGetPermissions

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
cmdset = Blueprint('cmdset',__name__)

ERRNUM_MODULE_cmdset = 1000

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
'''
def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
'''
	
@cmdset.route('/cmdset_list',methods=['GET', 'POST'])
def cmdset_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	page = request.form.get('z1')
	ipage = request.form.get('z2')
	keyword = request.form.get('z3')
	filter_flag = request.form.get('z4')
	selectid = request.form.get('z5')
	
	
	
	if se == "" or se == None:
		se = request.args.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if keyword == None:
		keyword = "[]"
	if filter_flag == None:
		filter_flag = 0
	if selectid == None:
		selectid = "[]"
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403		
	if page and str(page).isdigit() == False:
		return '',403
	if ipage and str(ipage).isdigit() == False:
		return '',403
	if filter_flag and str(filter_flag).isdigit() == False:
		return '',403		
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 			
	
	_power = PGetPermissions(usercode)
	_power = str(_power)
	_power_json = json.loads(_power)
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	
	return render_template('cmdset_list1.html',page=page,ipage=ipage,keyword=keyword,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id)
	
@cmdset.route('/create_cmdset',methods=['GET', 'POST'])
def create_cmdset():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	id = request.form.get('z1')
	type = request.form.get('tasktype')
	page = request.form.get('z2')
	ipage = request.form.get('z3')
	keyword = request.form.get('z4')
	filter_flag = request.form.get('z5')
	selectid = request.form.get('z6')
	
	if keyword == None:
		keyword = "[]"
	if filter_flag == None:
		filter_flag = 0
	if selectid == None:
		selectid = "[]"
		
	if type and str(type).isdigit() == False:
		return '',403	
	if id and str(id).isdigit() == False:
		return '',403
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403		
	if page and str(page).isdigit() == False:
		return '',403
	if ipage and str(ipage).isdigit() == False:
		return '',403
	if filter_flag and str(filter_flag).isdigit() == False:
		return '',403		
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
	
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	_power = PGetPermissions(usercode)
	_power = str(_power)
	_power_json = json.loads(_power)
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	
	return render_template('create1_cmdset.html',tasktype=type,cmdsetid=id,page=page,ipage=ipage,keyword=keyword,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id)
"""
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor();
			if (type == '1'):
				curs.execute("select public.\"PGetCmdSet\"(%d,null,null,1,0);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				results = json.loads(results)
				#CmdSetName = results["data"][0]["Name"]
				#Description = results["data"][0]["Description"]
				Content = results["data"][0]["Content"]
				Content = base64.decodestring(Content)
				Content= Content.replace('\n',',')
				return render_template('create1_cmdset.html',Content=Content,tasktype=type,cmdsetid=id)
			else:
				return render_template('create1_cmdset.html',tasktype=type,cmdsetid=id)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))
"""
