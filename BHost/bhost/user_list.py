#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import cgi
import cgitb
import pyodbc
import redis
import MySQLdb
import re
import pyodbc
import ConfigParser
import time
import json
from logbase import common
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from htmlencode import checkaccount
from comm import StrMD5
from urllib import unquote
from logbase import task_client
from logbase import defines
from index import PGetPermissions

import htmlencode
from generating_log import system_log

from comm_function import del_file_while_user_del
from flask import Flask,Blueprint,request,session,render_template
from jinja2 import Environment,FileSystemLoader
from comm import LogSet
from htmlencode import parse_sess,check_role
import random
import string
user_list = Blueprint('user_list', __name__)
env = Environment(loader = FileSystemLoader('templates'))

def debug(c):
	return 0
	path = "/var/tmp/debuglh11.txt"
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
	
#error encode
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"',"'").replace('\n',"\\n")
	return newStr


#用户、角色管理跳转
@user_list.route('/user_p', methods=['GET','POST'])
def user_manage():
	tasktype = request.form.get("tasktype")
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1":
		t = "user_manage.html"
	if tasktype == "2":
		t = "role_manage.html"
	sess = request.form.get('a0')
	if sess <0 or sess == '':
		sess = request.args.get('a0')
	if sess <0 or sess =='':
		sess ='';
	client_ip = request.remote_addr
	(error,us,mac) = SessionCheck(sess,client_ip)
	error_msg=''
	if error < 0:
		error_msg = "系统繁忙(%d)" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			error_msg = "非法访问"
		else:
			error_msg = "系统超时" 
	_power=PGetPermissions(us)
	_power_json = json.loads(str(_power));
	_power_mode = 2;
	_power_sonid = [];
	_power_mode_id = [];
	for one in _power_json:
		_power_sonid.append(one['SubMenuId']);
		if one['Mode'] == 2:
			_power_mode_id.append(one['SubMenuId'])
		if one['SubMenuId'] == 2:
			_power_mode = one['Mode']
	return render_template(t, tasktype= tasktype,error_msg=error_msg,_power_mode=_power_mode,_power_sonid=_power_sonid,_power_mode_id=_power_mode_id,us=us)

#取某个用户组下所有用户和用户组信息
@user_list.route('/get_ugroup_list', methods=['GET','POST'])
def get_ugroup_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	loginusercode = request.form.get('a1')
	ugid = request.form.get('a2')
	loginuserid = request.form.get('a3')
	if not loginuserid.isdigit():
		return '',403
	if not checkaccount(loginusercode):
		return '',403
	loginusercode = "'%s'" %loginusercode
	limitrow = "null"
	offsetrow = "null"
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	if ugid != "null":
		if not ugid.isdigit():
			return '',403
		ugid = "%s" %(ugid)
	sql = "select public.\"PGetUserDirectory\"(E%s,%s,8,%s,%s,%s);" %(loginusercode,ugid,loginuserid,limitrow,offsetrow)
	# debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

#获取用户组的信息
@user_list.route('/get_ugroup', methods=['GET','POST'])
def get_ugroup():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	UGId = request.form.get('a1')
	
	if UGId and str(UGId).isdigit() == False:
		return '',403
	
	if UGId < 0 or UGId =="":
		UGId = "null"
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	if UGId != "null":
		UGId = "'%s'" %(UGId)
	sql = "select public.\"PGetUGroup\"(%s);" %(UGId)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

#新建用户组
@user_list.route('/save_ugroup_list', methods=['GET','POST'])
def save_ugroup_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	FromFlag = request.form.get('a10')
	u_group = request.form.get('a1')
	AccessSet = request.form.get('a2')
	md5_str = request.form.get('m1')
	md5_str1 = request.form.get('m2')
	Ugroup_json = json.loads(u_group)
	
	u_group = str(u_group)
	debug("md5_str %s" % md5_str)
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(u_group);##python中的json的MD5
		debug("md5_json %s" % md5_json)
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	debug("77777777777777777777777777777777777")
	
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PSaveUGroup\"(E'%s');" %(MySQLdb.escape_string(u_group).decode("utf-8"))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]

	adminName_array = []
	for i in Ugroup_json['AdminSet']:
		id = i['AdminId']
		sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(id)
		curs.execute(sql)
		adminName_array.append(curs.fetchall()[0][0])

	ContentStr = "管理员："+'、'.join(adminName_array)
	debug(ContentStr)
	if(result == True):
		if md5_str1 < 0 or md5_str1 =='':#md5_str ajax传过来的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		else:
			md5_json = StrMD5(AccessSet);##python中的json的MD5
			if(parse_sess(md5_str1,session,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		AccessSet_json = json.loads(AccessSet)
		AccessSet_json['UGId'] = ret['UGId']
		AccessSet = json.dumps(AccessSet_json)
		sql = "select public.\"PAddUserToAccessAuth\"(E'%s');" %(MySQLdb.escape_string(AccessSet).decode("utf-8"))
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		conn.commit()
		if int(Ugroup_json['UGId']) == 0:
			system_log(system_user,"创建用户组：%s (%s)" % (Ugroup_json['UGName'],ContentStr),"成功",FromFlag)
		else:
			system_log(system_user,"编辑用户组：%s (%s)" % (Ugroup_json['UGName'],ContentStr),"成功",FromFlag)
		AccessAuth_Name = ""
		AccessSet_json = json.loads(AccessSet)
		for i in AccessSet_json['AccessAuthSet']:
			id = i['AccessAuthId']
			sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
			curs.execute(sql)
			AccessAuth_Name = curs.fetchall()[0][0]
			system_log(system_user,"访问授权\"%s\"新增授权对象：%s " % (AccessAuth_Name,Ugroup_json['UGName']),"成功",FromFlag)
		curs.close()
		conn.close()
		return results
	else:
		if int(Ugroup_json['UGId']) == 0:
			system_log(system_user,"创建用户组：%s (%s)" % (Ugroup_json['UGName'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(system_user,"编辑用户组：%s (%s)" % (Ugroup_json['UGName'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)			
		curs.close()
		conn.close()
		return results

#产生随机数
		
@user_list.route('/make_cache', methods=['GET','POST'])
def make_cache():
	start_time = int(time.time());
	cnone = ''.join(random.sample(string.ascii_letters + string.digits, 8));
	sign = StrMD5(str(start_time)+"safetybase"+cnone);
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);	
	r.set(str(start_time), sign);
	r.expire(str(start_time), 60) ##1分钟之后超时 自动删除
	return "{\"start_time\":%d,\"cnone\":\"%s\",\"sign\":\"%s\"}" %(start_time,cnone,sign)
#获取用户信息
@user_list.route('/get_user_list1', methods=['GET','POST'])
def get_user_list1():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	userid = request.form.get('a1')
	defu = request.form.get('d1')
	if userid and str(userid).isdigit() == False:
		return '',403
	if defu < 0:
		defu = 'false'	
		
	if userid < 0 or userid =="":
		userid = "null"
	if session < 0:
		session = ""
	
	start_time = request.form.get('s1')
	cnone = request.form.get('c1')
	sign = request.form.get('sign')
	
	if(sign < 0 or sign ==''  or cnone < 0 or cnone == ''  or start_time< 0 or start_time==''):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	if(int(time.time()) - int(start_time) > 60):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	if r.get(cnone):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		r.set(cnone, cnone);
		r.expire(cnone, 60) ##1分钟之后超时 自动删除
	
	if sign != StrMD5(str(start_time)+'safetybase'+cnone):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
		
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PGetUser\"(%s,0,'',%s);" %(userid,defu)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	try:
		if userid !='null':
			result_json = json.loads(results)['info'];
			authtype = result_json['AuthTypeId'];
			if authtype ==None:
				sql = "select count(*) from public.\"AuthTypeMember\" where \"AuthTypeId\" in(select \"AuthTypeId\" from public.\"AuthType\" where \"IsDefault\"='t' ) and \"AuthModuleId\"=10;"
				try:
					curs.execute(sql)
				except pyodbc.Error,e:
					curs.close()
					conn.close()
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if curs.fetchall()[0][0] == 0:
					if result_json['SecretKey'] !=None and len(result_json['SecretKey']) > 1:
						result_json['SecretKey'] = ' ';
			else:
				sql = "select count(*) from public.\"AuthTypeMember\" where \"AuthTypeId\"=%d and \"AuthModuleId\"=10;" %(authtype)
				try:
					curs.execute(sql)
				except pyodbc.Error,e:
					curs.close()
					conn.close()
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if curs.fetchall()[0][0] == 0:
					if result_json['SecretKey'] !=None and len(result_json['SecretKey']) > 1:
						result_json['SecretKey'] = ' ';
			results = json.dumps(result_json);		
	except:
		pass
	'''
	### 防止重放
	results_json = json.loads(results);
	start_time = int(time.time());
	cnone = ''.join(random.sample(string.ascii_letters + string.digits, 8));
	sign = StrMD5(results_json['UserCode']+str(start_time)+cnone);
	results_json['start_time'] = start_time;
	results_json['cnone'] = cnone;
	results_json['sign'] = sign;
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	
	r.set(results_json['UserCode']+':'+str(start_time), sign);
	r.expire(results_json['UserCode']+':'+str(start_time), 60) ##1分钟之后超时 自动删除
	
	results = json.dumps(results_json);
	'''
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results
	
#获取用户信息
@user_list.route('/get_user_list', methods=['GET','POST'])
def get_user_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	session = request.form.get('a0')
	userid = request.form.get('a1')
	defu = request.form.get('d1')
	if userid and str(userid).isdigit() == False:
		return '',403
	if defu < 0:
		defu = 'false'	
		
	if userid < 0 or userid =="":
		userid = "null"
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PGetUser\"(%s,0,'',%s);" %(userid,defu)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	try:
		if userid !='null':
			result_json = json.loads(results)['info'];
			authtype = result_json['AuthTypeId'];
			if authtype ==None:
				sql = "select count(*) from public.\"AuthTypeMember\" where \"AuthTypeId\" in(select \"AuthTypeId\" from public.\"AuthType\" where \"IsDefault\"='t' ) and \"AuthModuleId\"=10;"
				try:
					curs.execute(sql)
				except pyodbc.Error,e:
					curs.close()
					conn.close()
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if curs.fetchall()[0][0] == 0:
					if result_json['SecretKey'] !=None and len(result_json['SecretKey']) > 1:
						result_json['SecretKey'] = ' ';
			else:
				sql = "select count(*) from public.\"AuthTypeMember\" where \"AuthTypeId\"=%d and \"AuthModuleId\"=10;" %(authtype)
				try:
					curs.execute(sql)
				except pyodbc.Error,e:
					curs.close()
					conn.close()
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if curs.fetchall()[0][0] == 0:
					if result_json['SecretKey'] !=None and len(result_json['SecretKey']) > 1:
						result_json['SecretKey'] = ' ';
			results = json.dumps(result_json);		
	except:
		pass
	'''
	### 防止重放
	results_json = json.loads(results);
	start_time = int(time.time());
	cnone = ''.join(random.sample(string.ascii_letters + string.digits, 8));
	sign = StrMD5(results_json['UserCode']+str(start_time)+cnone);
	results_json['start_time'] = start_time;
	results_json['cnone'] = cnone;
	results_json['sign'] = sign;
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	
	r.set(results_json['UserCode']+':'+str(start_time), sign);
	r.expire(results_json['UserCode']+':'+str(start_time), 60) ##1分钟之后超时 自动删除
	
	results = json.dumps(results_json);
	'''
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

#删除用户组
@user_list.route('/delete_user_list', methods=['GET','POST'])
def delete_user_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	loginusercode = request.form.get('a1')
	parentid = request.form.get('a2')
	del_ug = request.form.get('a3')
	isuser = request.form.get('a4')
	isdeleteuser = request.form.get('a5')
	FromFlag = request.form.get('a10')
	loginusercode = "'%s'" %loginusercode
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
	
	if check_role(system_user,"用户管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	if int(parentid) == 0:
		P_Name = '/'
	else:
		P_Name = ""
		path_arry = []
		sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % int(parentid)
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])

		while results_1[0][0] != 0:
			sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results_1[0][0]
			debug(sql)
			curs.execute(sql)
			results_1 = curs.fetchall()
			path_arry.insert(0,results_1[0][1])
		P_Name = '/'+'/'.join(path_arry)

	Name = ""
	if isuser == "true":
		sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(del_ug)
	else:
		sql = "select public.\"PGetGroupMember\"(%d,1);" %(int(del_ug))
		debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		mems_result = curs.fetchall()[0][0]
		if mems_result == None:
			mems_result = []
			Members_array = ['无']
		else:
			mems_result = json.loads(mems_result)
			Members_array = []
			for i in mems_result:
				MembersStr = i['UserCode']+'('+i['UserName']+')'
				Members_array.append(MembersStr)

		sql = "select \"UGName\" from public.\"UGroup\" where \"UGId\"=%d" % int(del_ug)
	curs.execute(sql)
	Name = curs.fetchall()[0][0]


	sql = "select public.\"PDeleteUserDirectory\"(%s,%s,%s,%s,%s);" %(loginusercode, parentid, del_ug, isuser, isdeleteuser)
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')


	if isdeleteuser == "true":
		Type_delete_str = "删除组内用户"
	else:
		Type_delete_str = "移除组内用户"
	ret = json.loads(result)
	if "false" in result:
		if isuser == "true":
			system_log(system_user,"移除用户：%s (所属组：%s)" % (Name,P_Name),"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(system_user,"删除用户组：%s (所属组：%s，%s：%s)" % (Name,P_Name,Type_delete_str,'、'.join(Members_array)),"失败："+ret['ErrMsg'],FromFlag)
		curs.close()
		conn.close()
		return result
	conn.commit()
	if isuser == "true":
		system_log(system_user,"移除用户：%s (所属组：%s)" % (Name,P_Name),"成功",FromFlag)
	else:
		system_log(system_user,"删除用户组：%s (所属组：%s，%s：%s)" % (Name,P_Name,Type_delete_str,'、'.join(Members_array)),"成功",FromFlag)
	curs.close()
	conn.close()
	return result

#删除用户
@user_list.route('/delete_user_list_u', methods=['GET','POST'])
def delete_user_list_u():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	loginusercode = request.form.get('a1')
	del_id = request.form.get('a2')
	FromFlag = request.form.get('a10')
	debug("before delete user files")
	del_file_while_user_del(del_id)
	debug("after delete user files")
	if loginusercode < 0:
		loginusercode = 'admin'
	loginusercode = "'%s'" %loginusercode
	if session < 0:
		session = ""
	if FromFlag < 0:  #FromFlag 不传系统日志
		FromFlag = '-1'
	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if FromFlag == '-1':
		pass
	else:
		if check_role(system_user,"用户管理") == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	Name = ""
	sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(del_id)
	curs.execute(sql)
	Name = curs.fetchall()[0][0]

	sql = "select public.\"PDeleteUser\"(%s);" %(del_id)
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')

	task_content = '[global]\nclass = taskdown_user\ntype = D_H5ConfigFiles\nusercode=\"%s\"\nclientip=\"%s\"\nse=\"%s\"\nuserid=\"%s\"\n' % (system_user,client_ip,session,str(del_id))
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		return "{\"Result\":false,\"ErrMsg\":\"任务下发异常\"}"

	if "false" in result:
		curs.close()
		conn.close()
		ret = json.loads(result)
		system_log(system_user,"删除用户：%s" % Name,"失败："+ret['ErrMsg'],FromFlag)
		return result
	conn.commit()

	if FromFlag != '-1':
		system_log(system_user,"删除用户：%s" % Name,"成功",FromFlag)
	curs.close()
	conn.close()
	return result

#过滤查询
@user_list.route('/find_user_list',methods=['GET','POST'])
def find_user_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 21000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	jsondata = str(jsondata)
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	jsondata=jsondata.replace("\\\\","\\\\\\\\")
	jsondata=jsondata.replace(".","\\\\.")
	jsondata=jsondata.replace("?","\\\\?")
	jsondata=jsondata.replace("+","\\\\+")
	jsondata=jsondata.replace("(","\\\\(")
	jsondata=jsondata.replace("*","\\\\*")
	jsondata=jsondata.replace("[","\\\\[")
	sql = "select public.\"PFindUserDirectory\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
	if result[0][0]:
		debug("aaaa")
		results = result[0][0].encode('utf-8')
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":%s}" %results
	else:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":null}"

@user_list.route('/paste_user', methods=['GET','POST'])
def paste_user():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 21000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	loginusercode = request.form.get('a1')
	oldpid = request.form.get('a2')
	newpid = request.form.get('a3')
	copy_id = request.form.get('a4')
	isuser = request.form.get('a5')
	iscut = request.form.get('a6')
	FromFlag = request.form.get('a10')
	loginusercode = "'%s'" %loginusercode
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	if isuser == "true":
		isuser_c = "用户"
	else:
		isuser_c = "用户组"	
	if iscut == "true":
		iscut_c = "剪切"
	else:
		iscut_c = "复制"

	Name = ""
	if isuser == "true":
		sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(copy_id)
	else:
		sql = "select \"UGName\" from public.\"UGroup\" where \"UGId\"=%d" % int(copy_id)
	debug(sql)
	curs.execute(sql)
	Name = curs.fetchall()[0][0]

	OP_Name = ""
	path_arry = []
	sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % int(oldpid)
	curs.execute(sql)
	results_1 = curs.fetchall()
	path_arry.insert(0,results_1[0][1])

	while results_1[0][0] != None:
		sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results_1[0][0]
		debug(sql)
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])
	OP_Name = '/'.join(path_arry)

	NP_Name = ""
	path_arry = []
	sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % int(newpid)
	curs.execute(sql)
	results_1 = curs.fetchall()
	path_arry.insert(0,results_1[0][1])

	while results_1[0][0] != 0:
		sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results_1[0][0]
		debug(sql)
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])
	NP_Name = '/'+'/'.join(path_arry)


	ContentStr = iscut_c+isuser_c+":"+Name+"(原组："+OP_Name[1:]+"\t目标组："+NP_Name+")"
	debug(ContentStr)
	sql = "select public.\"PPasteUserDirectory\"(%s,%s,%s,%s,%s,%s);" %(loginusercode,oldpid,newpid,copy_id,isuser,iscut)
	# debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	conn.commit()
	if ret['Result'] == False:
		system_log(system_user,"%s" % ContentStr,"失败："+ret['ErrMsg'],FromFlag)
	else:
		system_log(system_user,"%s" % ContentStr,"成功",FromFlag)
	curs.close()
	conn.close()
	return results

#获取授权信息
# @user_list.route('/get_access_auth', methods=['GET','POST'])
# def get_access_auth():
# 	global ERRNUM_MODULE
# 	ERRNUM_MODULE = 20000
# 	reload(sys)
# 	sys.setdefaultencoding('utf-8')
# 	session = request.form.get('a0')
# 	userid = request.form.get('a1')
# 	if userid < 0 or userid =="":
# 		userid = "null"
# 	if session < 0:
# 		session = ""
# 	client_ip = request.remote_addr
# 	(error,system_user,mac) = SessionCheck(session,client_ip)
# 	if error < 0:
# 		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+906,error)
# 		sys.exit()
# 	elif error > 0:
# 		if error == 2:
# 			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+907,error)
# 		else:
# 			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+908,error)
# 		sys.exit()
# 	try:
# 		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
# 	except pyodbc.Error,e:
# 		conn.close()
# 		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+903,ErrorEncode(e.args[1]))
# 	try:
# 		curs = conn.cursor()
# 	except pyodbc.Error,e:
# 		conn.close()
# 		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+904,ErrorEncode(e.args[1]))

# 	sql = "select public.\"PGetUser\"(%s,0);" %(userid)
# 	try:
# 		curs.execute(sql)
# 	except pyodbc.Error,e:
# 		curs.close()
# 		conn.close()
# 		return "{\"Result\":false,\"ErrMsg\":\"用户信息获取异常(%d):%s\"}" %(ERRNUM_MODULE+905,ErrorEncode(e.args[1])) 
# 	results = curs.fetchall()[0][0].encode('utf-8')
# 	curs.close()
# 	conn.close()
# 	return "{\"Result\":true,\"info\":%s}" %results
@user_list.route('/get_AuthType_role', methods=['GET','POST'])
def get_AuthType_role():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	_power=PGetPermissions(system_user)
	_power_json = json.loads(str(_power));
	_power_mode = 0;
	for one in _power_json:
		if one['SubMenuId'] == 33:
			_power_mode = one['Mode']
	
	return "{\"Result\":true,\"info\":%d}" %(_power_mode)		
	
@user_list.route('/IsUNodeSelected', methods=['GET','POST'])
def IsUNodeSelected():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)			
			
	ugid = request.form.get('z1');
	pugid = request.form.get('z2');
	loginuserid =  request.form.get('z3');
	tp = request.form.get('z4');
	
	if ugid and str(ugid).isdigit() == False:
		return '',403 	
	if pugid and str(pugid).isdigit() == False:
		return '',403
	if loginuserid and str(loginuserid).isdigit() == False:
		return '',403
	if tp and str(tp).isdigit() == False:
		return '',403
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	sql = "select public.\"IsUNodeSelected\"(%s,%s,%s,false);" %(tp,loginuserid,ugid)
	# debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	results = curs.fetchall()[0][0]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%d,\"ugid\":%s,\"pugid\":%s}" %(results,ugid,pugid)
	
	
