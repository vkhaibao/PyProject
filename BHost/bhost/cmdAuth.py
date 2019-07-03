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
from logbase import defines
from logbase import task_client
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from htmlencode import check_role
from htmlencode import parse_sess

cmdAuth = Blueprint('cmdAuth',__name__)

ERRNUM_MODULE_cmd = 5000

def debug(c):
	return 0
	path = "/var/tmp/debugxtc.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

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
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
		
@cmdAuth.route('/cmdAuth_show',methods=['GET', 'POST'])
def cmdAuth_show():	
	tasktype = request.form.get('tasktype')  
	if tasktype < 0:
		tasktype = "0"
	if tasktype == '0':
		t = "access_control.html"
		return render_template(t,tasktype=tasktype)
	elif tasktype == '1':
		t = "cmdAuth_user.html"
		return render_template(t,tasktype=tasktype,manage_filter_flag=0,selectid="[]")
	elif tasktype == '2':
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		if selectid == None:
			selectid = "[]"
			
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
		#page =1;
		t = "cmdAuth_user.html"
		return render_template(t,tasktype=tasktype,page=page,name=name,type=type,manage_filter_flag=manage_filter_flag,selectid=selectid)
	elif tasktype == '3':#编辑
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		id = request.form.get('id')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		if selectid == None:
			selectid = "[]"
		if(str(id).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
		t = "cmdAuth_user.html"
		return render_template(t,tasktype=tasktype,name=name,type=type,page=page,id=id,manage_filter_flag=manage_filter_flag,selectid=selectid)
	elif tasktype == '4':
		se = request.form.get('a0')
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(se,client_ip);
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		
		if selectid == None:
			selectid = "[]"
		
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');	
		
			
		t = "auth_manage_xtc.html"
		
		_power=PGetPermissions(usercode)
		_power=str(_power)
		_power_json = json.loads(_power)
		auth_flag1 = 0
		auth_flag2 = 0
		auth_flag3 = 0
		auth_flag4 = 0
		for one in _power_json:
			if one['SubMenuId'] == 15:#访问授权
				if one['Mode'] == 2:#管理
					auth_flag1 = 1
				else:
					auth_flag1 = 2				
			elif one['SubMenuId'] == 16:#工单授权
				if one['Mode'] == 2:#管理
					auth_flag2 = 1
				else:
					auth_flag2 = 2	
			elif one['SubMenuId'] == 17:#指令授权
				if one['Mode'] == 2:#管理
					auth_flag3 = 1
				else:
					auth_flag3 = 2	
			elif one['SubMenuId'] == 18:#管理授权
				if one['Mode'] == 2:#管理
					auth_flag4 = 1
				else:
					auth_flag4 = 2
		
		return render_template(t,tasktype=tasktype,name=name,type=type,page=page,manage_filter_flag=manage_filter_flag,selectid=selectid,auth_flag1=auth_flag1,auth_flag2=auth_flag2,auth_flag3=auth_flag3,auth_flag4=auth_flag4)
@cmdAuth.route('/cmdAuth_show_a',methods=['GET', 'POST'])
def cmdAuth_show_a():
	tasktype = request.form.get('tasktype')  
	if tasktype < 0:
		tasktype = "0"
	if tasktype == '0':
		t = "access_control.html"
		return render_template(t,tasktype=tasktype)
	elif tasktype == '1':#外面创建
		t = "cmdAuth_access.html"
		return render_template(t,tasktype=tasktype,selectid="[]")
	elif tasktype == '2':#列表创建
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		if selectid == None:
			selectid = "[]"
			
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
		#page =1;
		t = "cmdAuth_access.html"
		return render_template(t,tasktype=tasktype,page=page,name=name,type=type,manage_filter_flag=manage_filter_flag,selectid=selectid)
	elif tasktype == '3':#编辑
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		id = request.form.get('id')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		
		if selectid == None:
			selectid = "[]"
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
			
		t = "cmdAuth_access.html"
		return render_template(t,tasktype=tasktype,name=name,type=type,page=page,id=id,manage_filter_flag=manage_filter_flag,selectid=selectid)
	elif tasktype == '4':
		se = request.form.get('a0')
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		if selectid == None:
			selectid = "[]"
		
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
			
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(se,client_ip);
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

		t = "auth_manage_xtc.html"#继续
		
		_power=PGetPermissions(usercode)
		_power=str(_power)
		_power_json = json.loads(_power)
		auth_flag1 = 0
		auth_flag2 = 0
		auth_flag3 = 0
		auth_flag4 = 0
		for one in _power_json:
			if one['SubMenuId'] == 15:#访问授权
				if one['Mode'] == 2:#管理
					auth_flag1 = 1
				else:
					auth_flag1 = 2				
			elif one['SubMenuId'] == 16:#工单授权
				if one['Mode'] == 2:#管理
					auth_flag2 = 1
				else:
					auth_flag2 = 2	
			elif one['SubMenuId'] == 17:#指令授权
				if one['Mode'] == 2:#管理
					auth_flag3 = 1
				else:
					auth_flag3 = 2	
			elif one['SubMenuId'] == 18:#管理授权
				if one['Mode'] == 2:#管理
					auth_flag4 = 1
				else:
					auth_flag4 = 2
		return render_template(t,tasktype=tasktype,name=name,type=type,page=page,manage_filter_flag=manage_filter_flag,selectid=selectid,auth_flag1=auth_flag1,auth_flag2=auth_flag2,auth_flag3=auth_flag3,auth_flag4=auth_flag4)
		
@cmdAuth.route('/cmdAuth_show_w',methods=['GET', 'POST'])
def cmdAuth_show_w():
	tasktype = request.form.get('tasktype')  
	if tasktype < 0:
		tasktype = "0"
	if tasktype == '0':
		t = "access_control.html"
		return render_template(t,tasktype=tasktype)
	elif tasktype == '1':
		t = "cmdAuth_work.html"
		return render_template(t,tasktype=tasktype,selectid="[]")
	elif tasktype == '2':
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		if selectid == None:
			selectid = "[]"
		
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
		
		#page =1;
		t = "cmdAuth_work.html"
		return render_template(t,tasktype=tasktype,page=page,name=name,type=type,manage_filter_flag=manage_filter_flag,selectid=selectid)
	elif tasktype == '3':#编辑
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		id = request.form.get('id')
		selectid = request.form.get('z2')
		if selectid == None:
			selectid = "[]"
		
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
		
		t = "cmdAuth_work.html"
		return render_template(t,tasktype=tasktype,name=name,type=type,page=page,id=id,manage_filter_flag=manage_filter_flag,selectid=selectid)
	elif tasktype == '4':
		se = request.form.get('a0')
		page = request.form.get('page')
		name = request.form.get('name')
		type = request.form.get('type')
		manage_filter_flag = request.form.get('z1')
		selectid = request.form.get('z2')
		
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(se,client_ip);
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
		if selectid == None:
			selectid = "[]"
		
		if(str(page).isdigit() == False):
			return '',403
		if(str(manage_filter_flag).isdigit() == False):
			return '',403
		if	selectid.find(']') < 0:
			return '',403
			
		select_tmp = selectid[1:-1]
		for a in select_tmp.split(','):
			if( str(a) !='' and str(a).isdigit() == False):
				return '',403 	
		if name:
			name_tmp = name[1:-1]		
			if(len(name_tmp) > 0 and name_tmp.find('-') < 0):
				return '',403
			name = name.replace('(','').replace(')','');
			
		t = "auth_manage_xtc.html"
		
		_power=PGetPermissions(usercode)
		_power=str(_power)
		_power_json = json.loads(_power)
		auth_flag1 = 0
		auth_flag2 = 0
		auth_flag3 = 0
		auth_flag4 = 0
		for one in _power_json:
			if one['SubMenuId'] == 15:#访问授权
				if one['Mode'] == 2:#管理
					auth_flag1 = 1
				else:
					auth_flag1 = 2				
			elif one['SubMenuId'] == 16:#工单授权
				if one['Mode'] == 2:#管理
					auth_flag2 = 1
				else:
					auth_flag2 = 2	
			elif one['SubMenuId'] == 17:#指令授权
				if one['Mode'] == 2:#管理
					auth_flag3 = 1
				else:
					auth_flag3 = 2	
			elif one['SubMenuId'] == 18:#管理授权
				if one['Mode'] == 2:#管理
					auth_flag4 = 1
				else:
					auth_flag4 = 2
		
		return render_template(t,tasktype=tasktype,name=name,type=type,page=page,manage_filter_flag=manage_filter_flag,selectid=selectid,auth_flag1=auth_flag1,auth_flag2=auth_flag2,auth_flag3=auth_flag3,auth_flag4=auth_flag4)

@cmdAuth.route('/auth_manage_xtc',methods=['GET', 'POST'])
def auth_manage_xtc():
	se = request.form.get('a0')
	tasktype = request.form.get('tasktype')
	manage_filter_flag = request.form.get('z1')
	
	if manage_filter_flag == None or manage_filter_flag=='':
		manage_filter_flag = 0
		
	if(str(manage_filter_flag).isdigit() == False):
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
			
	t = "auth_manage_xtc.html"
	_power=PGetPermissions(usercode)
	_power=str(_power)
	_power_json = json.loads(_power)
	auth_flag1 = 0
	auth_flag2 = 0
	auth_flag3 = 0
	auth_flag4 = 0
	for one in _power_json:
		if one['SubMenuId'] == 15:#访问授权
			if one['Mode'] == 2:#管理
				auth_flag1 = 1
			else:
				auth_flag1 = 2				
		elif one['SubMenuId'] == 16:#工单授权
			if one['Mode'] == 2:#管理
				auth_flag2 = 1
			else:
				auth_flag2 = 2	
		elif one['SubMenuId'] == 17:#指令授权
			if one['Mode'] == 2:#管理
				auth_flag3 = 1
			else:
				auth_flag3 = 2	
		elif one['SubMenuId'] == 18:#管理授权
			if one['Mode'] == 2:#管理
				auth_flag4 = 1
			else:
				auth_flag4 = 2	
	return render_template(t,tasktype=tasktype,manage_filter_flag=manage_filter_flag,selectid="[]",auth_flag1=auth_flag1,auth_flag2=auth_flag2,auth_flag3=auth_flag3,auth_flag4=auth_flag4)

@cmdAuth.route('/get_account_list_xtc',methods=['GET', 'POST'])#获取账号
def get_account_list_xtc():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetAccount\"(null,null,null,null);"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results

@cmdAuth.route('/get_ucont_list',methods=['GET', 'POST'])#获取管理员
def get_ucont_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetUser\"(null,3);"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
@cmdAuth.route('/get_service_range_x',methods=['GET', 'POST'])#获取服务器范围
def get_service_range_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetServerScope\"(null,null,true,null,null,null,null);"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
@cmdAuth.route('/get_all_message',methods=['GET', 'POST'])
def get_all_message():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	rangeid = request.form.get('a1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetAccountProtocolForAuth\"(E'%s')" % (MySQLdb.escape_string(rangeid))
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
@cmdAuth.route('/get_access_x',methods=['GET', 'POST'])
def get_access_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetAccessStrategy\"(null,null,null,null,null);"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results	
@cmdAuth.route('/get_cmd_all_x',methods=['GET', 'POST'])#获取指令集合
def get_cmd_all_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetCmdSet\"(null,null,null,null,null);"
	#debug(dec)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results

@cmdAuth.route('/get_warning_all_x',methods=['GET', 'POST'])#获取告警信息
def get_warning_all_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetEventAlarmInfo\"(null,null,null,null,null);"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
	
@cmdAuth.route('/get_ApproveStrategy_all_x',methods=['GET', 'POST'])#获取审批策略
def get_ApproveStrategy_all_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetApproveStrategy\"(null,null,null,null);"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
	
@cmdAuth.route('/get_groupdirectory_x',methods=['GET', 'POST'])
def get_groupdirectory_x():#获取主机主机组树
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	id = request.form.get('a1')
	if int(id) == 0:
		dec="select public.\"PGetUserDirectory\"(E'%s',0,6,0,null,null);" % (usercode)
	else:
		dec="select public.\"PGetUserDirectory\"(E'%s',%d,6,0,null,null);" % (usercode,int(id))
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results

@cmdAuth.route('/save_cmdauth_all_x',methods=['GET', 'POST'])
def save_cmdauth_all_x():#保存指令授权
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	cmdauthdata = request.form.get('a1')
	content = request.form.get('a2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(cmdauthdata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	json_cmd = json.loads(cmdauthdata)
	#content_array = content[2:-2].split(',')
	if content != "":
		#content = '\r\n'.join(content_array)
		content = content.replace('\n','\r\n')
		content = base64.encodestring(content)
		content = content.replace("\n",'')
		for v in json_cmd['AuthCmdSet']:
			if v['Type'] == 2:
				v['Content'] = content
	task_flag = 0
	if str(json_cmd['CmdAuthType']) == '1':
		if len(json_cmd['AuthObjectSet']['AuthObject']) != 0:
			task_flag = 1
		
	cmdauthdata = json.dumps(json_cmd)
	dec="select public.\"PSaveCmdAuth\"(E'%s')" % (MySQLdb.escape_string(cmdauthdata).decode('utf-8'))
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	results_json=json.loads(results)
	if task_flag == 1:
		if results_json["Result"] == False:
			if json_cmd['CmdAuthId'] == 0:
				if str(json_cmd['CmdAuthType']) == '1':
					system_log(usercode,"创建指令授权->按对象授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '2':
					system_log(usercode,"创建指令授权->按访问授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '3':
					system_log(usercode,"创建指令授权->按工单授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
			else:
				if str(json_cmd['CmdAuthType']) == '1':
					system_log(usercode,"编辑指令授权->按对象授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '2':
					system_log(usercode,"编辑指令授权->按访问授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '3':
					system_log(usercode,"编辑指令授权->按工单授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
			return results
		task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=5\nid=%s\n' % (results_json["CmdAuthId"])
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			if json_cmd['CmdAuthId'] == 0:
				if str(json_cmd['CmdAuthType']) == '1':
					system_log(usercode,"创建指令授权->按对象授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '2':
					system_log(usercode,"创建指令授权->按访问授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '3':
					system_log(usercode,"创建指令授权->按工单授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
			else:
				if str(json_cmd['CmdAuthType']) == '1':
					system_log(usercode,"编辑指令授权->按对象授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '2':
					system_log(usercode,"编辑指令授权->按访问授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
				elif str(json_cmd['CmdAuthType']) == '3':
					system_log(usercode,"编辑指令授权->按工单授权：%s" % json_cmd['CmdAuthName'],"失败","运维管理>指令授权")
			return "{\"Result\":false,\"info\":\"扫描任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
	t = int(time.time())
	try:
		cmd = "echo {} > /var/tmp/refresh_access".format(t)
		p = os.system(cmd)
	# 调用系统命令失败
	except OSError:
		exit(0)
	
	
	sql = "select public.\"PGetCmdAuth\"(E'%s',%d,null,null,null,null,null);" % (usercode,results_json['CmdAuthId'])
	curs.execute(sql)
	re_data = curs.fetchall()[0][0].encode('utf-8')
	re_data = json.loads(re_data)
	if len(re_data['data']) == 0:
		data0 = json.loads(cmdauthdata)
		sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % data0['AdminSet'][0]['AdminId']
		curs.execute(sql)
		UserCode = curs.fetchall()[0][0].encode('utf-8')
		curs.execute("select public.\"PGetCmdAuth\"(E'%s',%d,null,null,null,null,null);" % (UserCode,results_json['CmdAuthId']))
		re_data = curs.fetchall()[0][0].encode('utf-8')
		re_data = json.loads(re_data)
	_obj = ""
	if str(re_data['data'][0]["CmdAuthType"]) == '1':
		if re_data['data'][0]["AuthMode"] == 1:
			_obj = "方式：对象指定"
		elif re_data['data'][0]["AuthMode"] == 2:
			_obj = "方式：范围指定（共有）"
		elif re_data['data'][0]["AuthMode"] == 3:
			_obj = "方式：范围指定（所有）"
		else:
			_obj = "方式：范围指定（自定义）"
	
		scopename = ""
		if re_data['data'][0]['AuthObjectSet']['AuthScope'] != None and len(re_data['data'][0]['AuthObjectSet']['AuthScope']) != 0:
			for scope in re_data['data'][0]['AuthObjectSet']['AuthScope']:
				scopename = scopename + scope['ServerScopeName'] + ','
			scopename = scopename[:-1]
	
		auth_obj = []
		if re_data['data'][0]['AuthObjectSet']['AuthObject'] != None and len(re_data['data'][0]['AuthObjectSet']['AuthObject']) != 0:
			auth_hg = ""
			auth_host = ""
			auth_account = ""
			ii = 0;
			for authobj in re_data['data'][0]['AuthObjectSet']['AuthObject']:
				ii += 1;
				if ii > 1000:
					break;
				if authobj['AccountName'] != None:
					auth_account = auth_account + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + '-' + authobj['AccountName'] + ','
				elif authobj['HostName'] != None:
					auth_host = auth_host + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + ','
				else:
					auth_hg = auth_hg + '[' + authobj['HGName'] + '],'
			
			
			if auth_hg != "":
				auth_hg = "指定主机组：" + auth_hg[:-1]
				auth_obj.append(auth_hg)
			if auth_host != "":
				auth_host = "指定主机：" + auth_host[:-1]
				auth_obj.append(auth_host)
			if auth_account != "":
				auth_account = "指定账号：" + auth_account[:-1]
				auth_obj.append(auth_account)
		auth_obj_str = '，'.join(auth_obj)
		
		if scopename != "":
			_obj = _obj + '，' + "服务器范围：" + scopename
			
		if auth_obj_str != "":
			_obj = _obj + '，' + auth_obj_str
		
		if re_data['data'][0]['AuthObjectSet']['AuthUserSet'] != None and len(re_data['data'][0]['AuthObjectSet']['AuthUserSet']) != 0:
			user_str = ""
			userhg_str = ""
			ii = 0;
			for user in re_data['data'][0]['AuthObjectSet']['AuthUserSet']:
				ii += 1;
				if ii > 1000:
					break
				if user['Type'] == 1:
					user_str = user_str + user['Name'] + ','
				else:
					userhg_str = userhg_str + user['Name'] + ','
			if user_str != "":
				user_str = "授权用户：" + user_str[:-1]
				_obj = _obj + '，' + user_str
			if userhg_str != "":
				userhg_str = "授权用户组：" + userhg_str[:-1]
				_obj = _obj + '，' + userhg_str
	elif str(re_data['data'][0]["CmdAuthType"]) == '2':
		access_str = ""
		if re_data['data'][0]["AuthObjectSet"] != None and len(re_data['data'][0]["AuthObjectSet"]) != 0:
			for access in re_data['data'][0]["AuthObjectSet"]:
				access_str = access_str + access['AccessAuthName'] + ','
			if access_str != "":
				access_str = access_str[:-1]
				_obj  = _obj + "访问授权：" + access_str
	else:
		if re_data['data'][0]["AuthObjectSet"] != None and len(re_data['data'][0]["AuthObjectSet"]) != 0:
			work_str = ""
			for work in re_data['data'][0]["AuthObjectSet"]:
				work_str = work_str + work['WorkOrderName'] + ','
			if work_str != "":
				work_str = work_str[:-1]
				_obj = _obj + "工单授权：" + work_str

	if re_data['data'][0]['Enabled'] == True:
		_obj = _obj + '，' + "启用"
	else:
		_obj = _obj + '，' + "停用"
	
	if re_data['data'][0]['AdminSet'] != None and len(re_data['data'][0]['AdminSet']) != 0:
		admin_str = ""
		for admin in re_data['data'][0]['AdminSet']:
			admin_str = admin_str + admin['UserCode'] + ','
		if admin_str != "":
			admin_str = "管理者：" + admin_str[:-1]

		_obj = _obj + '，' + admin_str
	
	if re_data['data'][0]['AuthCmdSet'] != None and len(re_data['data'][0]['AuthCmdSet']) != 0:
		cmdset_str = ""
		cmdcont_str = ""
		for cmdset in re_data['data'][0]['AuthCmdSet']:
			if cmdset['Type'] == 1:
				cmdset_str = cmdset_str + cmdset['Name'] + ','
			else:
				cmdcont_str = cmdcont_str + base64.b64decode(cmdset['Content']) + ','
		if cmdset_str != "":
			cmdset_str = "指令集合：" + cmdset_str[:-1]
			_obj = _obj + '，' + cmdset_str
		
		if cmdcont_str != "":
			cmdcont_str = "指令：" + cmdcont_str[:-1]
			_obj = _obj + '，' + cmdcont_str
	
	ResponseMode_name = "";
	if re_data['data'][0]['ResponseMode'] == 1:
		ResponseMode_name = "产生告警"
	elif re_data['data'][0]['ResponseMode'] == 2:
		ResponseMode_name = "阻断会话";
	elif re_data['data'][0]['ResponseMode'] == 3:
		ResponseMode_name = "阻断会话，产生告警"
	elif re_data['data'][0]['ResponseMode'] == 4:
		ResponseMode_name = "忽略指令"
	elif re_data['data'][0]['ResponseMode'] == 5:
		ResponseMode_name = "忽略指令，产生告警"
	elif re_data['data'][0]['ResponseMode'] == 8:
		ResponseMode_name = "指令审批"
	elif re_data['data'][0]['ResponseMode'] == 9:
		ResponseMode_name = "指令审批，产生告警"
	else:
		ResponseMode_name = ""
	_obj = _obj + '，响应方式：' + ResponseMode_name
	
	if json_cmd['CmdAuthId'] == 0:
		if str(json_cmd['CmdAuthType']) == '1':
			system_log(usercode,"创建指令授权->按对象授权：%s（%s）" % (json_cmd['CmdAuthName'],_obj),"成功","运维管理>指令授权")
		elif str(json_cmd['CmdAuthType']) == '2':
			system_log(usercode,"创建指令授权->按访问授权：%s（%s）" % (json_cmd['CmdAuthName'],_obj),"成功","运维管理>指令授权")
		elif str(json_cmd['CmdAuthType']) == '3':
			system_log(usercode,"创建指令授权->按工单授权：%s（%s）" % (json_cmd['CmdAuthName'],_obj),"成功","运维管理>指令授权")
	else:
		if str(json_cmd['CmdAuthType']) == '1':
			system_log(usercode,"编辑指令授权->按对象授权：%s（%s）" % (json_cmd['CmdAuthName'],_obj),"成功","运维管理>指令授权")
		elif str(json_cmd['CmdAuthType']) == '2':
			system_log(usercode,"编辑指令授权->按访问授权：%s（%s）" % (json_cmd['CmdAuthName'],_obj),"成功","运维管理>指令授权")
		elif str(json_cmd['CmdAuthType']) == '3':
			system_log(usercode,"编辑指令授权->按工单授权：%s（%s）" % (json_cmd['CmdAuthName'],_obj),"成功","运维管理>指令授权")
	conn.commit()
	curs.close()
	conn.close()
	return results

	
@cmdAuth.route('/check_name',methods=['GET', 'POST'])#判断授权名称是否已经存在
def check_name():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	name = request.form.get('a1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetCmdAuthByName\"(E'%s');" %(name)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	curs.close()
	conn.close()
	return str(results)


@cmdAuth.route('/get_cmdauth_list_x',methods=['GET', 'POST'])#获取指令授权列表
def get_cmdauth_list_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	page = request.form.get('a3')
	ts = request.form.get('a4')
	#way = request.form.get('a2')
	name_s = request.form.get('a1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if page != "null":
		row = (int(page)-1)*(int(ts))
	else:
		row = "null"
	
	filter_cond_arry = []
	i = 0
	while i < 15:
		filter_cond_arry.append([])
		i += 1
	#所有、名称、管理员、授权方式、授权动作、状态、响应方式、用户组、运维用户、主机组、主机名、服务器范围、主机服务、账号、指令
	name_s = json.loads(name_s)
	if len(name_s) != 0:
		for i in name_s:
			filter_arry = i.split('-',1)
			filter_cond_arry[int(filter_arry[0])].append(MySQLdb.escape_string(filter_arry[1]).decode("utf-8"))
	i = 0
	while i < 15:
		if i == 6:
			filter_cond_arry[i] = str(sum(int(each_v) for each_v in filter_cond_arry[i]))
		else:
			filter_cond_arry[i] = '\n'.join(filter_cond_arry[i])
			filter_cond_arry[i] = MySQLdb.escape_string(filter_cond_arry[i]).decode("utf-8")
		if i == 0:
			filter_cond_arry[i] = filter_cond_arry[i].replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		else:
			filter_cond_arry[i] = filter_cond_arry[i].replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		
		if filter_cond_arry[i] == "":
			filter_cond_arry[i] = 'null'
		else:
			if i == 3 or i == 4 or i == 5 or i == 6:
				if filter_cond_arry[i] == '0':
					filter_cond_arry[i] = 'null'
				else:
					if i == 3:
						filter_cond_arry[i] = "'%s'" % filter_cond_arry[i]
						#filter_cond_arry[i] = "%s" % filter_cond_arry[i]
					else:
						filter_cond_arry[i] = '%s' % filter_cond_arry[i]
			else:
				if i == 1:
					filter_cond_arry[i] = "'%s'" % filter_cond_arry[i]
				else:
					filter_cond_arry[i] = '"%s"' % filter_cond_arry[i]
		i += 1
	usercode = "E'%s'" % usercode
	data = '{"adminusercode":%s,"ugname":%s,"usercode":%s,"hgname":%s,"hostname":%s,"serverscopename":%s,"hostservicename":%s,"accountname":%s,"searchstring":%s,"Action":%s,"Enabled":%s,"Content":%s,"ResponseMode":%s}' % (filter_cond_arry[2],filter_cond_arry[7],filter_cond_arry[8],filter_cond_arry[9],filter_cond_arry[10],filter_cond_arry[11],filter_cond_arry[12],filter_cond_arry[13],filter_cond_arry[0],filter_cond_arry[4],filter_cond_arry[5],filter_cond_arry[14],filter_cond_arry[6])
	data = "E'%s'" % MySQLdb.escape_string(data).decode("utf-8")
	dec="select public.\"PGetCmdAuth\"(%s,null,%s,%s,null,%s,%s,%s)" % (usercode,filter_cond_arry[1],filter_cond_arry[3],ts,row,data)
	#dec="select public.\"PGetCmdAuth\"(%s,null,%s,%s,null,%s,%s)" % (usercode,filter_cond_arry[1],filter_cond_arry[3],ts,row)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results

@cmdAuth.route('/del_cmdauth_x',methods=['GET', 'POST'])#删除指令授权
def del_cmdauth_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	cmdid = request.form.get('a1')
	del_type = request.form.get('a2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:	
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#插入数据	
	try:
		if del_type == '1':
			cmd_array = json.loads(cmdid)
			sql = "select \"CmdAuthName\" from public.\"CmdAuth\" where \"CmdAuthId\" in (%s)" % cmdid[1:-1]
			curs.execute(sql)
			auth_str = ""
			for row in curs.fetchall():
				auth_str = auth_str + row[0].encode('utf-8') + ","
			for cmd_one in cmd_array:
				sql = "select \"CmdAuthName\" from public.\"CmdAuth\" where \"CmdAuthId\"=%d" % int(cmd_one)
				curs.execute(sql)
				auth_name = curs.fetchall()[0][0].encode('utf-8')
				
				dec="select public.\"PDeleteCmdAuth\"(%d)" %(int(cmd_one))
				curs.execute(dec)
				results = curs.fetchall()[0][0].encode('utf-8')
				re_del = json.loads(results)
				if re_del['Result'] == False:
					system_log(usercode,"删除指令授权：%s" % auth_name,"失败："+result['ErrMsg'],"运维管理>指令授权")
					conn.rollback()
					return results
			conn.commit()
			curs.close()
			conn.close()
			t = int(time.time())
                        try:
                                cmd = "echo {} > /var/tmp/refresh_access".format(t)
                                p = os.system(cmd)
                        # 调用系统命令失败
                        except OSError:
                                exit(0)
			if auth_str != "":
				system_log(usercode,"删除指令授权：%s" % auth_str[:-1],"成功","运维管理>指令授权")
			return "{\"Result\":true}"
		else:
			sql = "select \"CmdAuthName\" from public.\"CmdAuth\" where \"CmdAuthId\"=%d" % int(cmdid)
			curs.execute(sql)
			auth_name = curs.fetchall()[0][0].encode('utf-8')
			
			dec="select public.\"PDeleteCmdAuth\"(%d)" %(int(cmdid))
			curs.execute(dec)
			results = curs.fetchall()[0][0].encode('utf-8')
			conn.commit()
			curs.close()
			conn.close()
			t = int(time.time())
                        try:
                                cmd = "echo {} > /var/tmp/refresh_access".format(t)
                                p = os.system(cmd)
                        # 调用系统命令失败
                        except OSError:
                                exit(0)
			re_del = json.loads(results)
			if re_del['Result']:
				system_log(usercode,"删除指令授权：%s" % auth_name,"成功","运维管理>指令授权")
			else:
				system_log(usercode,"删除指令授权：%s" % auth_name,"失败","运维管理>指令授权")
			return results
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	
@cmdAuth.route('/get_groupdirectory_idx',methods=['GET', 'POST'])
def get_groupdirectory_idx():#编辑回显用户用户组树
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('a1')
	ugid = request.form.get('a2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetUserDirectory\"(E'%s',%d,6,%d,null,null);" % (usercode,int(ugid),int(id))
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
	
@cmdAuth.route('/PGetCmdAuth_x',methods=['GET', 'POST'])
def PGetCmdAuth_x():#获取编辑信息
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('a1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	dec="select public.\"PGetCmdAuth\"(E'%s',%d,null,null,null,null,null);" % (usercode,int(id))
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	results_json = json.loads(results)
	for i in results_json['data'][0]['AuthCmdSet']:
		if i['Content'] != None:
			i['Content'] = base64.b64decode(results_json['data'][0]['AuthCmdSet'][0]['Content'])
	results = json.dumps(results_json)
	conn.commit()
	curs.close()
	conn.close()
	return results

@cmdAuth.route('/get_access_way_x',methods=['GET', 'POST'])#获取授权方式
def get_access_way_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	#Id = request.form.get('a0')
	#(error,system_user,mac) = SessionCheck(session
	usercode = '"%s"' % usercode
	data = '{"loginusercode":'+usercode+',"limitrow":null,"offsetrow":null}'
	data = "E'%s'" % data
	dec="select public.\"PGetAccessAuth\"(%s);" %(data)
	#debug(dec)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
	
	
@cmdAuth.route('/get_work_way_x',methods=['GET', 'POST'])#获取工单授权方式
def get_work_way_x():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	usercode = '"%s"' % usercode
	data = '{"loginusercode":'+usercode+',"limitrow":null,"offsetrow":null}'
	dec="select public.\"PGetWorkOrder\"(E'%s');" %(data)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#插入数据	
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results

@cmdAuth.route('/get_all_cmd_z',methods=['GET', 'POST'])#获取工单授权方式
def get_all_cmd_z():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			dec="SELECT \"CmdAuthId\" FROM \"CmdAuth\";"
			curs.execute(dec)
			results = curs.fetchall()
			a=[]
			for i in results:
				a.append(i[0])
			return str(a)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@cmdAuth.route('/get_hostdirectory_zc',methods=['GET','POST'])
def get_hostdirectory_zc():
	session = request.form.get('a0')
	hid = request.form.get('z1')
	aid = request.form.get('z2')
	find_doing = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if aid == "":
		aid = '-1'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if aid != '-1':
				if str(find_doing) == 'true':
					curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,5,%d,null,null,%s);" %(usercode,int(hid),int(aid),str(find_doing)))
				else:
					curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,5,%d,null,null);" %(usercode,int(hid),int(aid)))
			else:
				curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,5,null,null,null);" %(usercode,int(hid)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
@cmdAuth.route('/enable_cmdauth',methods=['GET', 'POST'])
def enable_cmdauth():
	session = request.form.get('a0')
	cmdid = request.form.get('z1')
	e_type = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"CmdAuthName\" from \"CmdAuth\" where \"CmdAuthId\"=%s" % cmdid
			curs.execute(sql)
			authname = curs.fetchall()[0][0].encode('utf-8')
			
			if e_type == '1':
				curs.execute("update \"CmdAuth\" set \"Enabled\"= true,\"InvalidLog\"=null where \"CmdAuthId\"= %s" % cmdid)
				system_log(usercode,"启用指令授权：%s" % authname,"成功","运维管理>指令授权")
			else:
				curs.execute("update \"CmdAuth\" set \"Enabled\"= false,\"InvalidLog\"=null where \"CmdAuthId\"= %s" % cmdid)
				system_log(usercode,"停用指令授权：%s" % authname,"成功","运维管理>指令授权")
			return 	"{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@cmdAuth.route('/check_edit_cmdAuth',methods=['GET', 'POST'])
def check_edit_cmdAuth():
	session = request.form.get('a0')
	cmdid = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute('select public."PGetCmdAuth"(E\'%s\',null,null,null,null,null,null)' % (usercode))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@cmdAuth.route('/modify_priority_cmd',methods=['GET','POST'])
def modify_priority_cmd():
	session = request.form.get('a0')
	modifyid = request.form.get('z1')
	referid = request.form.get('z2')
	position = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,'指令授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			curs.execute("select public.\"PModifyCmdAuthPriority\"(%d,%d,%d);"%(int(modifyid),int(referid),int(position)))
			results = curs.fetchall()[0][0].encode('utf-8')
			sql = "select \"CmdAuthName\" from public.\"CmdAuth\" where \"CmdAuthId\" = %s;" %(modifyid)
			curs.execute(sql)
			name_re1 = curs.fetchall()
			sql = "select \"CmdAuthName\" from public.\"CmdAuth\" where \"CmdAuthId\" = %s;" %(referid)
			curs.execute(sql)
			name_re2 = curs.fetchall()
			if results == "true":
				if position == '1':
					system_log(usercode,"指令授权（%s）的优先级改为在指令授权（%s）之前" % (name_re1[0][0].encode('utf-8'),name_re2[0][0].encode('utf-8')),"成功","运维管理>指令授权")
				else:
					system_log(usercode,"指令授权（%s）的优先级改为在指令授权（%s）之后" % (name_re1[0][0].encode('utf-8'),name_re2[0][0].encode('utf-8')),"成功","运维管理>指令授权")
			else:
				if position == '1':
					system_log(usercode,"指令授权（%s）的优先级改为在指令授权（%s）之前" % (name_re1[0][0].encode('utf-8'),name_re2[0][0].encode('utf-8')),"失败","运维管理>指令授权")
				else:
					system_log(usercode,"指令授权（%s）的优先级改为在指令授权（%s）之后" % (name_re1[0][0].encode('utf-8'),name_re2[0][0].encode('utf-8')),"失败","运维管理>指令授权")
			return results
        except pyodbc.Error,e:
                return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
