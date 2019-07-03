#!/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import cgi
import cgitb
import pyodbc
import MySQLdb
import re
import ConfigParser
import time
import json
import redis
from logbase import common
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import GenerateCertUsr
from comm import SessionCheckLocal
from urllib import unquote
from logbase import task_client
from logbase import defines
from ctypes import *
from htmlencode import checkaccount
import datetime

import htmlencode
from generating_log import system_log

from flask import Flask,Blueprint,request,session,render_template
from jinja2 import Environment,FileSystemLoader
from comm import LogSet

import random, base64
from hashlib import sha1
from htmlencode import parse_sess,check_role

user_add = Blueprint('user_add', __name__)
env = Environment(loader = FileSystemLoader('templates'))

def debug(c):
	return 0
	path = "/var/tmp/debuglh.txt"
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
	
# def sendlog(oper,desc,cname):
# 	#cname = session['username']
# 	client_ip = request.remote_addr    #获取客户端IP
# 	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
# 	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
# 	LogSet(None, sqlconf, 6)


#创建系统用户
@user_add.route('/add_sys_user', methods=['GET', 'POST'])
def add_sys_user():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	user = request.form.get('a1')
	AccessSet = request.form.get('a2')
	o_pwd = request.form.get('a3')
	repeat = request.form.get('a4')
	new_pin = request.form.get('a5')
	oldPwd_check = request.form.get('a6')
	finger = request.form.get('a7')
	FromFlag = request.form.get('a10')
	md5_str = request.form.get('m1')
	md5_str1 = request.form.get('m2')
	changePwd = False
	if repeat < 0:
		repeat = 0
	if o_pwd < 0:
		o_pwd = ""
	if new_pin < 0 or new_pin == None:
		new_pin = ""
	if finger < 0 or finger == None:
		finger = ""
	if oldPwd_check < 0 or oldPwd_check == None:
		oldPwd_check = ""		
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(user);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	user = json.loads(user)
	user_json = user
	debug(o_pwd)
	debug(user['Password'])
	old_userId = user['UserId'];
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
	#send system log
	if user_json['AuthTypeId'] != None:
		sql = "select \"AuthTypeName\" from public.\"AuthType\" where \"AuthTypeId\"=%d" % int(user_json['AuthTypeId'])
		debug(sql)

		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		AuthTypeName_tmp = curs.fetchall()[0][0]
	else:
		AuthTypeName_tmp = "默认"
	roleName_array = []
	for i in user_json['RoleSet']:
		id = i['RoleId']
		sql = "select \"RoleName\" from public.\"Role\" where \"RoleId\"=%d" % int(id)
		curs.execute(sql)
		roleName_array.append(curs.fetchall()[0][0])
	adminName_array = []
	if user_json['AdminSet'] != None:
		for i in user_json['AdminSet']:
			id = i['AdminId']
			sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(id)
			curs.execute(sql)
			adminName_array.append(curs.fetchall()[0][0])
	LoginUniqueIP = '是'
	if user_json['LoginUniqueIP'] == False:
		LoginUniqueIP = '否'

	SecretKey = '是'
	if user_json['SecretKey'] == None:
		SecretKey = '否'

	LoginUniqueIP = '是'
	if user_json['LoginUniqueIP'] == False:
		LoginUniqueIP = '否'

	ExpireTime = '未开启'
	if user_json['ExpireTimeEnabled'] == True:
		ExpireTime = user_json['ExpireTime']

	UGroup_array = []
	if user_json['UGroupSet'] == [] or user_json['UGroupSet'] == None:
		user_json['UGroupSet'] = []
	for i in user_json['UGroupSet']:
		id = i['UGId']
		path_arry = []
		sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % i['UGId']
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])

		while results_1[0][0] != 0:
			sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results_1[0][0]
			debug(sql)
			curs.execute(sql)
			results_1 = curs.fetchall()
			path_arry.insert(0,results_1[0][1])
		path_str = '/'+'/'.join(path_arry)

		UGroup_array.append(path_str)

	ContentStr = "账号："+user_json['UserCode']+", 姓名："+user_json['UserName']+", "+("" if user_json['UserNumber']==None else "工号：%s, "%user_json['UserNumber'])+"认证方式："+AuthTypeName_tmp+", 邮箱："+user_json['Email']+", 角色："+'、'.join(roleName_array)+", 管理员："+'、'.join(adminName_array)+", 第三方认证账号："+user_json['ThirdUserCode']+", 是否唯一登陆："+LoginUniqueIP+",失效时间："+ExpireTime+", 用户组："+'、'.join(UGroup_array)
	debug(ContentStr)
	#
	debug("o_pwd:%s,userpwd:%s" %(str(o_pwd),str(user['Password'])))
	if(o_pwd != user['Password']) and (not user['Password'] == ""):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(user['Password'],pwd_rc4)#执行函数
		user['Password'] = pwd_rc4.value #获取变量的值
		oldPwd_tmp = pwd_rc4.value
		debug("AAAAAAAAAAA")
		debug(pwd_rc4.value)
		if oldPwd_check != "":
			ret = lib.encrypt_pwd(oldPwd_check,pwd_rc4)
			oldPwd_check_rc = pwd_rc4.value
			if oldPwd_check_rc != o_pwd:
				if user_json['UserId'] == 0:
					system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：当前密码错误",FromFlag)
				else:
					system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：当前密码错误",FromFlag)
				return "{\"Result\":false,\"ErrMsg\":\"当前密码错误\"}"
		debug("BBBBBBBBB")
		debug(pwd_rc4.value)
		if user.has_key('OldPassword') and str(user['OldPassword']) != 'None':
			debug("222222")
			oldPwdArray = str(user["OldPassword"]).split(',')
			debug(str(oldPwdArray))
			i = 0
			if repeat != '0':
				for oldPwd in reversed(oldPwdArray):
					debug("i:%d" %i)
					debug("repeat:%s" %repeat)
					if i < int(repeat)+1:
						i += 1
						#if str(oldPwd) == str(pwd_rc4.value):
						debug(str(oldPwd))
						if str(oldPwd) == str(user['Password']):
							if i == 1:
								return "{\"Result\":false,\"ErrMsg\":\"不能和当前密码一致\"}"
							if user_json['UserId'] == 0:
								system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：密码不能与前%s次密码重复" % (repeat),FromFlag)
							else:
								system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：密码不能与前%s次密码重复" % (repeat),FromFlag)							
							return "{\"Result\":false,\"ErrMsg\":\"密码不能与前%s次密码重复\"}" % (repeat)
					else:
						continue
			if len(oldPwdArray) == 6:
				del oldPwdArray[0]
			oldPwdArray.append(oldPwd_tmp)
			user['OldPassword'] = str(','.join(oldPwdArray))
			debug(user['OldPassword'])
			changePwd = True
		else:
			user['OldPassword'] = oldPwd_tmp
			debug(user['OldPassword'])
			changePwd = True
	UserName = user['UserName'];
	
	user = json.dumps(user)
	user = str(user)
	sql = "select public.\"PSaveUser\"(E'%s');" %(MySQLdb.escape_string(user).decode("utf-8"))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)

	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)   #json转python
	result = ret["Result"] 
	return_result = {'Result': 'true', 'RowCount': '1', 'UserId': 0, 'Content': None}
	content = ""	
	debug(results)
	if(result == True):
		
		if new_pin != "":
			#fdir = "/usr/storage/.system/etc/userca/"+str(ret['UserId'])+".crt"
			#/usr/ssl/usrca/cert_id.crt
			fdir = "/usr/ssl/usrca/cert_%s.crt" %(str(ret['UserId']))
			
			task_content = '[global]\nclass = taskUserKey\ntype = getUserKey\nuserId = %s\nuserName = %s' %(str(ret['UserId']),UserName)
			debug(task_content)
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				conn.rollback()
				return "{\"Result\":false,\"ErrMsg\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
				return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.ErrMsg))
			t = 0;
			while(True):
				if os.path.exists(fdir) == False:
					time.sleep(1)
				else:
					break;
				t +=1;
				if t > 10:
					conn.rollback()
					return_result['Result'] = False
					return_result['RowCount'] = 'false'
					return_result['UserId'] = 'false'
					return_result['Content'] = 'false'
					if user_json['UserId'] == 0:
						system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
					else:
						system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
					return json.dumps(return_result)
			
			if os.path.exists(fdir) == False:
				conn.rollback()
				return_result['Result'] = False
				return_result['RowCount'] = 'false'
				return_result['UserId'] = 'false'
				return_result['Content'] = 'false'
				if user_json['UserId'] == 0:
					system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
				else:
					system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
				return json.dumps(return_result)
			if os.path.exists(fdir):
				f = open("/usr/ssl/usrca/cert_%d.crt" %(ret['UserId']),'r')
				lines = f.readlines()
				f.close()
				if ("-----BEGIN CERTIFICATE-----\n" in lines) and ("-----END CERTIFICATE-----\n" in lines):
					flag = 0

					for i in lines:
						if i == "-----BEGIN CERTIFICATE-----\n":
							flag = 1
						elif i == "-----END CERTIFICATE-----\n":
							content += "-----END CERTIFICATE-----\n"
							flag = 0
						if flag == 1:
							content += i
				else:
					conn.rollback()
					return_result['Result'] = False
					return_result['RowCount'] = 'false'
					return_result['UserId'] = 'false'
					return_result['Content'] = 'false'
					if user_json['UserId'] == 0:
						system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
					else:
						system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)					
					return json.dumps(return_result)
		
		if finger != "":
			if finger.find("'") >=0 or finger.find('"') >=0:
				return '',403
			sql = "update public.\"User\" set \"Finger\" = '%s' where \"UserId\" = %s;" %(finger,str(ret['UserId']))
			curs.execute(sql)
			conn.commit()

		if md5_str1 < 0 or md5_str1 =='':#md5_str ajax传过来的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		else:
			md5_json = StrMD5(AccessSet);##python中的json的MD5
			if(parse_sess(md5_str1,session,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		AccessSet_json = json.loads(AccessSet)
		AccessSet_json['UserId'] = ret['UserId']
		AccessSet = json.dumps(AccessSet_json)
		sql = "select public.\"PAddUserToAccessAuth\"(E'%s');" %(MySQLdb.escape_string(AccessSet).decode("utf-8"))
		debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		conn.commit()
		debug(str(changePwd))
		if changePwd == True or old_userId == 0:
			#获取当前时间
			time_now = int(time.time())
			#转换成localtime
			time_local = time.localtime(time_now)
			#转换成新的时间格式(2018/04/02 10:59:20)
			dt = time.strftime("%Y/%m/%d %H:%M:%S",time_local)
			if user_json['UserStatus'] == 8 or user_json['UserStatus'] == 9:
				sql = "update public.\"User\" set \"LastPwdModifyTime\" = '%s',\"UserStatus\"=1 where \"UserId\" = %s;" %(dt,str(ret['UserId']))
			else:
				sql = "update public.\"User\" set \"LastPwdModifyTime\" = '%s' where \"UserId\" = %s;" %(dt,str(ret['UserId']))
				
			debug(sql)
			curs.execute(sql)
			conn.commit()	

		if user_json['UserId'] == 0:
			sql = "update public.\"User\" set \"MonitorBGColor\" = 2 where \"UserCode\" = '%s';" %(user_json['UserCode'])
			curs.execute(sql)
			conn.commit()
			system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"成功",FromFlag)
		else:
			system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"成功",FromFlag)
		AccessAuth_Name = ""
		AccessSet_json = json.loads(AccessSet)
		for i in AccessSet_json['AccessAuthSet']:
			id = i['AccessAuthId']
			sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
			curs.execute(sql)
			AccessAuth_Name = curs.fetchall()[0][0]
			system_log(system_user,"访问授权\"%s\"新增授权对象：%s " % (AccessAuth_Name,user_json['UserCode']),"成功",FromFlag)
		
		ret['Content'] = base64.b64encode(content);
		
		## 
		if user_json.has_key('CertCn'):
			if user_json['CertCn'] ==None:
				user_json['CertCn'] ='';
			sql = "update public.\"User\" set \"CertCn\" = E'%s' where \"UserCode\" = E'%s';" %(user_json['CertCn'].decode('utf-8'),user_json['UserCode'])
			curs.execute(sql)
			conn.commit()
		curs.close()
		conn.close()
		#ret['Content'] = content;
		return json.dumps(ret)
	else:
		if user_json['UserId'] == 0:
			system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)		
		curs.close()
		conn.close()
		return results
#创建系统用户
@user_add.route('/add_sys_user1', methods=['GET', 'POST'])
def add_sys_user1():
	
	
	session = request.form.get('a0')
	user = request.form.get('a1')
	AccessSet = request.form.get('a2')
	o_pwd = request.form.get('a3')
	repeat = request.form.get('a4')
	new_pin = request.form.get('a5')
	oldPwd_check = request.form.get('a6')
	finger = request.form.get('a7')
	FromFlag = request.form.get('a10')
	md5_str = request.form.get('m1')
	md5_str1 = request.form.get('m2')
	changePwd = False
	if repeat < 0:
		repeat = 0
	if o_pwd < 0:
		o_pwd = ""
	if new_pin < 0 or new_pin == None:
		new_pin = ""
	if finger < 0 or finger == None:
		finger = ""
	if oldPwd_check < 0 or oldPwd_check == None:
		oldPwd_check = ""		
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(user);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	user = json.loads(user)
	
	if(user.has_key('start_time') == False or user.has_key('cnone')==False or user.has_key('sign') ==False ):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	if(int(time.time()) - user['start_time'] > 60):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	if r.get(user['cnone']):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		r.set(user['cnone'], user['cnone']);
		r.expire(user['cnone'], 60) ##1分钟之后超时 自动删除
	
	if user['sign'] != StrMD5(str(user['start_time'])+'safetybase'+user['cnone']):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	user_json = user
	debug(o_pwd)
	debug(user['Password'])
	old_userId = user['UserId'];
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
	#send system log
	if user_json['AuthTypeId'] != None:
		sql = "select \"AuthTypeName\" from public.\"AuthType\" where \"AuthTypeId\"=%d" % int(user_json['AuthTypeId'])
		debug(sql)

		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		AuthTypeName_tmp = curs.fetchall()[0][0]
	else:
		AuthTypeName_tmp = "默认"
	roleName_array = []
	for i in user_json['RoleSet']:
		id = i['RoleId']
		sql = "select \"RoleName\" from public.\"Role\" where \"RoleId\"=%d" % int(id)
		curs.execute(sql)
		roleName_array.append(curs.fetchall()[0][0])
	adminName_array = []
	if user_json['AdminSet'] != None:
		for i in user_json['AdminSet']:
			id = i['AdminId']
			sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(id)
			curs.execute(sql)
			adminName_array.append(curs.fetchall()[0][0])
	LoginUniqueIP = '是'
	if user_json['LoginUniqueIP'] == False:
		LoginUniqueIP = '否'

	SecretKey = '是'
	if user_json['SecretKey'] == None:
		SecretKey = '否'
	LoginUniqueIP = '是'
	if user_json['LoginUniqueIP'] == False:
		LoginUniqueIP = '否'

	ExpireTime = '未开启'
	if user_json['ExpireTimeEnabled'] == True:
		ExpireTime = user_json['ExpireTime']

	UGroup_array = []
	if user_json['UGroupSet'] == [] or user_json['UGroupSet'] == None:
		user_json['UGroupSet'] = []
	for i in user_json['UGroupSet']:
		id = i['UGId']
		path_arry = []
		sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % i['UGId']
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])

		while results_1[0][0] != 0:
			sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results_1[0][0]
			debug(sql)
			curs.execute(sql)
			results_1 = curs.fetchall()
			path_arry.insert(0,results_1[0][1])
		path_str = '/'+'/'.join(path_arry)

		UGroup_array.append(path_str)

	ContentStr = "账号："+user_json['UserCode']+", 姓名："+user_json['UserName']+", "+("" if user_json['UserNumber']==None else "工号：%s, "%user_json['UserNumber'])+"认证方式："+AuthTypeName_tmp+", 邮箱："+user_json['Email']+", 角色："+'、'.join(roleName_array)+", 管理员："+'、'.join(adminName_array)+", 第三方认证账号："+user_json['ThirdUserCode']+", 是否唯一登陆："+LoginUniqueIP+",失效时间："+ExpireTime+", 用户组："+'、'.join(UGroup_array)
	debug(ContentStr)
	#
	debug("o_pwd:%s,userpwd:%s" %(str(o_pwd),str(user['Password'])))
	if(o_pwd != user['Password']) and (not user['Password'] == ""):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(user['Password'],pwd_rc4)#执行函数
		user['Password'] = pwd_rc4.value #获取变量的值
		oldPwd_tmp = pwd_rc4.value
		debug("AAAAAAAAAAA")
		debug(pwd_rc4.value)
		if oldPwd_check != "":
			ret = lib.encrypt_pwd(oldPwd_check,pwd_rc4)
			oldPwd_check_rc = pwd_rc4.value
			if oldPwd_check_rc != o_pwd:
				if user_json['UserId'] == 0:
					system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：当前密码错误",FromFlag)
				else:
					system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：当前密码错误",FromFlag)
				return "{\"Result\":false,\"ErrMsg\":\"当前密码错误\"}"
		debug("BBBBBBBBB")
		debug(pwd_rc4.value)
		if user.has_key('OldPassword') and str(user['OldPassword']) != 'None':
			debug("222222")
			oldPwdArray = str(user["OldPassword"]).split(',')
			debug(str(oldPwdArray))
			i = 0
			if repeat != '0':
				for oldPwd in reversed(oldPwdArray):
					debug("i:%d" %i)
					debug("repeat:%s" %repeat)
					if i < int(repeat)+1:
						i += 1
						#if str(oldPwd) == str(pwd_rc4.value):
						debug(str(oldPwd))
						if str(oldPwd) == str(user['Password']):
							if i == 1:
								return "{\"Result\":false,\"ErrMsg\":\"不能和当前密码一致\"}"
							if user_json['UserId'] == 0:
								system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：密码不能与前%s次密码重复" % (repeat),FromFlag)
							else:
								system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：密码不能与前%s次密码重复" % (repeat),FromFlag)							
							return "{\"Result\":false,\"ErrMsg\":\"密码不能与前%s次密码重复\"}" % (repeat)
					else:
						continue
			if len(oldPwdArray) == 6:
				del oldPwdArray[0]
			oldPwdArray.append(oldPwd_tmp)
			user['OldPassword'] = str(','.join(oldPwdArray))
			debug(user['OldPassword'])
			changePwd = True
		else:
			user['OldPassword'] = oldPwd_tmp
			debug(user['OldPassword'])
			changePwd = True
	UserName = user['UserName'];
	
	user = json.dumps(user)
	user = str(user)
	sql = "select public.\"PSaveUser\"(E'%s');" %(MySQLdb.escape_string(user).decode('utf-8'))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)

	results = curs.fetchall()[0][0]
	ret = json.loads(results)   #json转python
	result = ret["Result"] 
	return_result = {'Result': 'true', 'RowCount': '1', 'UserId': 0, 'Content': None}
	content = ""	
	debug(results)
	if(result == True):
		
		if new_pin != "":
			#fdir = "/usr/storage/.system/etc/userca/"+str(ret['UserId'])+".crt"
			#/usr/ssl/usrca/cert_id.crt
			fdir = "/usr/ssl/usrca/cert_%s.crt" %(str(ret['UserId']))
			
			task_content = '[global]\nclass = taskUserKey\ntype = getUserKey\nuserId = %s\nuserName = %s' %(str(ret['UserId']),UserName)
			debug(task_content)
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				conn.rollback()
				return "{\"Result\":false,\"ErrMsg\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
				return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.ErrMsg))
			t = 0;
			while(True):
				if os.path.exists(fdir) == False:
					time.sleep(1)
				else:
					break;
				t +=1;
				if t > 10:
					conn.rollback()
					return_result['Result'] = False
					return_result['RowCount'] = 'false'
					return_result['UserId'] = 'false'
					return_result['Content'] = 'false'
					if user_json['UserId'] == 0:
						system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
					else:
						system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
					return json.dumps(return_result)
			
			if os.path.exists(fdir) == False:
				conn.rollback()
				return_result['Result'] = False
				return_result['RowCount'] = 'false'
				return_result['UserId'] = 'false'
				return_result['Content'] = 'false'
				if user_json['UserId'] == 0:
					system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
				else:
					system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
				return json.dumps(return_result)
			if os.path.exists(fdir):
				f = open("/usr/ssl/usrca/cert_%d.crt" %(ret['UserId']),'r')
				lines = f.readlines()
				f.close()
				if ("-----BEGIN CERTIFICATE-----\n" in lines) and ("-----END CERTIFICATE-----\n" in lines):
					flag = 0

					for i in lines:
						if i == "-----BEGIN CERTIFICATE-----\n":
							flag = 1
						elif i == "-----END CERTIFICATE-----\n":
							content += "-----END CERTIFICATE-----\n"
							flag = 0
						if flag == 1:
							content += i
				else:
					conn.rollback()
					return_result['Result'] = False
					return_result['RowCount'] = 'false'
					return_result['UserId'] = 'false'
					return_result['Content'] = 'false'
					if user_json['UserId'] == 0:
						system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)
					else:
						system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败：PIN码保存失败",FromFlag)					
					return json.dumps(return_result)
		
		if finger != "":
			if finger.find("'") >=0 or finger.find('"') >=0:
				return '',403
			sql = "update public.\"User\" set \"Finger\" = '%s' where \"UserId\" = %s;" %(finger,str(ret['UserId']))
			curs.execute(sql)
			conn.commit()

		if md5_str1 < 0 or md5_str1 =='':#md5_str ajax传过来的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		else:
			md5_json = StrMD5(AccessSet);##python中的json的MD5
			if(parse_sess(md5_str1,session,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		AccessSet_json = json.loads(AccessSet)
		AccessSet_json['UserId'] = ret['UserId']
		AccessSet = json.dumps(AccessSet_json)
		sql = "select public.\"PAddUserToAccessAuth\"(E'%s');" %(MySQLdb.escape_string(AccessSet).decode('utf-8'))
		debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		conn.commit()
		debug(str(changePwd))
		if changePwd == True or old_userId == 0:
			#获取当前时间
			time_now = int(time.time())
			#转换成localtime
			time_local = time.localtime(time_now)
			#转换成新的时间格式(2018/04/02 10:59:20)
			dt = time.strftime("%Y/%m/%d %H:%M:%S",time_local)
			if user_json['UserStatus'] == 8 or user_json['UserStatus'] == 9:
				sql = "update public.\"User\" set \"LastPwdModifyTime\" = '%s',\"UserStatus\"=1 where \"UserId\" = %s;" %(dt,str(ret['UserId']))
			else:
				sql = "update public.\"User\" set \"LastPwdModifyTime\" = '%s' where \"UserId\" = %s;" %(dt,str(ret['UserId']))
				
			debug(sql)
			curs.execute(sql)
			conn.commit()	

		if user_json['UserId'] == 0:
			sql = "update public.\"User\" set \"MonitorBGColor\" = 2 where \"UserCode\" = '%s';" %(user_json['UserCode'])
			curs.execute(sql)
			conn.commit()
			system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"成功",FromFlag)
		else:
			system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"成功",FromFlag)
		AccessAuth_Name = ""
		AccessSet_json = json.loads(AccessSet)
		for i in AccessSet_json['AccessAuthSet']:
			id = i['AccessAuthId']
			sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
			curs.execute(sql)
			AccessAuth_Name = curs.fetchall()[0][0]
			system_log(system_user,"访问授权\"%s\"新增授权对象：%s " % (AccessAuth_Name,user_json['UserCode']),"成功",FromFlag)
		
		ret['Content'] = base64.b64encode(content);
		
		## 
		if user_json.has_key('CertCn'):
			if user_json['CertCn'] ==None:
				user_json['CertCn'] ='';
			sql = "update public.\"User\" set \"CertCn\" = E'%s' where \"UserCode\" = E'%s';" %(user_json['CertCn'],user_json['UserCode'])
			curs.execute(sql)
			conn.commit()
		curs.close()
		conn.close()
		#ret['Content'] = content;
		return json.dumps(ret)
	else:
		if user_json['UserId'] == 0:
			system_log(system_user,"创建用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(system_user,"编辑用户：%s (%s)" % (user_json['UserCode'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)		
		curs.close()
		conn.close()
		return results
#获取角色系统菜单信息
@user_add.route('/get_role_menu', methods=['GET', 'POST'])
def get_role_menu():
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PGetSystemMenu\"();"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')

	sql="select public.\"PGetPermissions\"(E'%s');" %(system_user)
	curs.execute(sql)
	permission = curs.fetchall()[0][0]
	if permission==None:
		permission='[]'
	else:
		result_json = json.loads(results)
		perm_json = json.loads(permission)
		for p1 in result_json:
			for p2 in p1['SubMenu']:
				flag = 0
				for p3 in perm_json:
					if p2['SubMenuId'] == p3['SubMenuId'] and p3['EnableAuth'] != 0:
						flag = 1
						break
					elif p2['SubMenuId'] == p3['SubMenuId'] and p3['EnableAuth'] == 0:
						flag = 2
						#break
				if flag != 1:
					p2['PermissionFlag'] = False
				else:
					p2['PermissionFlag'] = True
				# manage_flag = 0
				for p4 in perm_json:
					if p4['SubMenuId'] ==2:
						if p2['SubMenuId'] == p4['SubMenuId'] and p4['Mode'] == 2:
							p2['ManageFlag'] = 2
							break
						elif p2['SubMenuId'] == p4['SubMenuId'] and p4['Mode'] == 1:
							p2['ManageFlag'] = 1
							break
						else:
							p2['ManageFlag'] = 0
							break
				# if manage_flag != 1:
				# 	p2['ManageFlag'] = False
				# else:
				# 	p2['ManageFlag'] = True
		results = json.dumps(result_json)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

#添加系统角色
@user_add.route('/add_sys_role', methods=['GET', 'POST'])
def add_sys_role():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	md5_str = request.form.get('m1')
	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	r_p = request.form.get('a1')
	FromFlag = request.form.get('a10')
	r_p = str(r_p)
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(r_p);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	r_p_json = json.loads(r_p)
	sql = "select public.\"PSaveRole\"(E'%s');" %((r_p).decode("utf-8"))
	debug(sql)
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

	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]

	sql1 = "select public.\"PGetSystemMenu\"();"
	debug(sql1)
	try:
		curs.execute(sql1)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result_sql1 = curs.fetchall()[0][0].encode('utf-8')
	ret1 = json.loads(result_sql1)
	exit_flag = False
	ContentStr = ""
	for a in r_p_json['Permission']:
		exit_flag = False
		for b in ret1:
			for c in b['SubMenu']:
				if str(a['SubMenuId']) == str(c['SubMenuId']):
					if str(a['Mode']) == '1':
						ContentStr += str(c['SubMenuName']) +" ：访问"
					elif str(a['Mode']) == '2':
						ContentStr += str(c['SubMenuName']) +" ：管理"
					else:
						ContentStr += str(c['SubMenuName']) + '：'
					if str(a['EnableAuth']) == '1':
						ContentStr += '(授权)\t'
					else:
						ContentStr += '\t'
					exit_flag = True
					break
			if exit_flag:
				break
	debug("CCCCContentStr:"+ContentStr)
	if(result == True):
		conn.commit()
		if r_p_json['RoleId'] == 0:
			system_log(system_user,"创建角色：%s (%s)" % (r_p_json['RoleName'],ContentStr),"成功",FromFlag)
		else:
			system_log(system_user,"编辑角色：%s (%s)" % (r_p_json['RoleName'],ContentStr),"成功",FromFlag)
		curs.close()
		conn.close()
		return results
	else:
		if r_p_json['RoleId'] == 0:
			system_log(system_user,"创建角色：%s (%s)" % (r_p_json['RoleName'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(system_user,"编辑角色：%s (%s)" % (r_p_json['RoleName'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)
		curs.close()
		conn.close()
		return results

@user_add.route('/get_role_list', methods=['GET', 'POST'])
def get_role_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num = request.form.get('a1')
	paging = request.form.get('a2')
	search_typeall = request.form.get('a3')
	id = request.form.get('a4')
	
	flag_user =  request.form.get('a6')
	
	if flag_user < 0 or flag_user == "":
		flag_user = 0
	else:
		flag_user = int(flag_user)
	
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
	
	username = ""
	nopermission = "false"
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
	if id < 0 or id == "" or id == "0":
		userid = "null"
	else:
		userid = id
	if search_typeall < 0:
		search_typeall = ""
	paging = int(paging)
	if paging < 0:
		paging = 1
	num = int(num)
	if num < 0:
		num = 10
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
	if search_typeall != "":
		search_typeall = search_typeall[:-1]
	typeall = search_typeall.split('\t')
	for search in typeall:
		if search=='':
			continue
		debug(str(search))
		index_s=search.index('-')
		search_s=search[:index_s]
		search_value=search[index_s+1:]
		if search_s == "1":
			username = username + search_value + "\\n"
		elif search_s == "0":
			username = username + search_value + "\\n"
	if username == "":
		username = "null"
	else:
		username = "E'%s'" %username[:-2]
	username = username.replace(".","\\\\.")

	sql = "select \"User\".\"UserId\" from public.\"User\" where \"User\".\"UserCode\"='%s';" %(system_user)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	if flag_user == 1:
		sql = "select public.\"PGetRole\"(%s,%s,%s,%d,%d,'%s','{}',null,%s);" %(userid,username,nopermission,num,(paging-1)*num,system_user,dsc)
	else:
		sql = "select public.\"PGetRole\"(%s,%s,%s,%d,%d,'%s','{}','{%s}',%s);" %(userid,username,nopermission,num,(paging-1)*num,system_user,str(results),dsc)
	debug(sql)
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


@user_add.route('/del_role', methods=['GET', 'POST'])
def del_role():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	FromFlag = request.form.get('a10')
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

	if check_role(system_user,"角色管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
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

	roleName_array = []
	for id in ids:
		id = int(id)
		sql = "select \"RoleName\" from public.\"Role\" where \"RoleId\"=%d" % int(id)
		curs.execute(sql)
		Name_Str = curs.fetchall()[0][0]
		roleName_array.append(Name_Str)

		sql = "select public.\"PDeleteRole\"(%d);" %(id)
		# debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		result = curs.fetchall()[0][0].encode('utf-8')
		if "false" in result:
			result_json = json.loads(result)
			system_log(system_user,"删除角色：%s" % Name_Str,"失败："+result_json['ErrMsg'],FromFlag)
			curs.close()
			conn.close()
			return result
	conn.commit()
	system_log(system_user,"删除角色：%s" % ('、'.join(roleName_array)),"成功",FromFlag)
	curs.close()
	conn.close()
	return result

@user_add.route('/_get_un', methods=['GET', 'POST'])
def _get_un():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1') # 已选组的ID
	ro_str = request.form.get('r1') # 1,2,3,4 角色ID

	if id_str<0 or id_str=="0" or id_str=="":
		id_str="null"
	elif not id_str.isdigit():
		return "a1格式错误",403
	if session < 0:
		session = ""
	if ro_str <0 or ro_str =="":
		ro_str = 'null'
	#elif not ro_str.isdigit():
	#	return "r1格式错误",403
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

	if id_str!="null" :
		id_str="E'%s'"%(id_str)
	if ro_str!='null':
		ro_str = "E'{%s}'" %(ro_str)
	sql = "select public.\"PGetAdminForUGroup\"(%s,%s);" %(id_str,ro_str)
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

@user_add.route('/_get_un_g', methods=['GET', 'POST'])
def _get_un_g():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1') #用户组id

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

	if id_str!="null" :
		id_str="E'%s'"%(id_str)

	sql = "select public.\"PGetAdminForGroup\"(%s);" %(id_str)
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

@user_add.route('/_get_rn', methods=['GET', 'POST'])
def _get_rn():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	adminidstr = request.form.get('a1')

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
	sql = "select public.\"PGetRole\"(%s,%s,%s,%s,%s,'%s','{}','{%s}');" %("null","null","false","null","null",system_user,adminidstr)
	debug(sql)
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

@user_add.route('/_get_userid', methods=['GET', 'POST'])
def _get_userid():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	un = request.form.get('a1')
	if not checkaccount(un):
		return 'un格式错误',403
	un = "E'%s'" %(un.decode("utf-8"))
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
	sql = "select \"User\".\"UserId\" from public.\"User\" where \"User\".\"UserCode\"=%s;" %(un)
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	curs.close()
	conn.close()
	return "{\"info\":%d}" %results
###获取 客户端范围
@user_add.route('/_get_client', methods=['GET', 'POST'])	
def _get_client():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
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
		
	sql="select public.\"PGetClientScope\"(null,null,null,null);"
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	curs.close()
	conn.close()
	return results
	
####获取 用户中的用户组信息
@user_add.route('/get_u_Dir', methods=['GET', 'POST'])	
def get_u_Dir():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ugid = request.form.get('a1')
	adminidset = request.form.get('a2')
	userid = request.form.get('a3')

	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if ugid < 0 or ugid=="":
		ugid = 0
	else:
		ugid = int(ugid)
	
	if userid < 0 or userid=="":
		userid = 0
	else:
		if not userid.isdigit():
			return '',403
		userid = int(userid)
	
	for a in adminidset.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
	
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#
	sql = "select public.\"PGetUserDirectory2\"('%s',%d,'{%s}',%s)" %(system_user,ugid,adminidset,userid)
	try:
		debug(sql)
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results

###获取 继承/交接的用户
@user_add.route('/GetTransUser', methods=['GET', 'POST'])	
def GetTransUser():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	loginusercode = request.form.get('a1')
	srcuserid = request.form.get('a2')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if loginusercode < 0 or loginusercode == "":
		loginusercode = "null"
	# else:
	# 	loginusercode = "'%s'" %loginusercode
	if srcuserid < 0 or srcuserid == "":
		srcuserid = "null"
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
		
	sql = "select public.\"PGetTransUser\"('%s',%s);" %(loginusercode,srcuserid)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	if results == None:
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"无搜索结果\"}"
	else:
		results = results.encode('utf-8')
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":%s}" %(results)

###继承 交接 用户
@user_add.route('/TransferAuthority', methods=['GET', 'POST'])	
def TransferAuthority():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	desuser = request.form.get('a1')
	srcuser = request.form.get('a2')
	flag_c = request.form.get('a3')
	FromFlag = request.form.get('a10')
	md5_str = request.form.get('m1')
	debug('-------------')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(desuser);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
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
	if flag_c == 'true':
		desuser = json.loads(desuser)
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]#定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(desuser['Password'],pwd_rc4)#执行函数
		desuser['Password'] = pwd_rc4.value #获取变量的值
		desuser1 = json.dumps(desuser)
		desuser1 = str(desuser1)

		if desuser['AuthTypeId'] != None:
			sql = "select \"AuthTypeName\" from public.\"AuthType\" where \"AuthTypeId\"=%d" % int(desuser['AuthTypeId'])
			debug(sql)
			curs.execute(sql)
			AuthTypeName_tmp = curs.fetchall()[0][0]
		else:
			AuthTypeName_tmp = "默认"

		sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % int(srcuser)
		debug(sql)
		curs.execute(sql)
		SrcuserName = curs.fetchall()[0][0]

		ContentStr = "账号："+desuser['UserCode']+", 姓名："+desuser['UserName']+", 认证方式："+AuthTypeName_tmp+", 邮箱："+desuser['Email']+", 继承对象："+SrcuserName

		sql = "select public.\"PSaveUser\"(E'%s');" %(MySQLdb.escape_string(desuser1).decode("utf-8"))
		debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		debug(str(results))
		ret = json.loads(results)
		debug(str(ret))
		if ret["Result"] == False:
			system_log(system_user,"创建继承用户：%s (%s)" % (desuser['UserCode'],ContentStr),"失败："+ret['ErrMsg'],FromFlag)      
			return "{\"Result\":false,\"ErrMsg\":\"%s\"}" %(ret['ErrMsg'])
		else:
			desuser_id = ret['UserId']
	else:
		desuser_id = desuser
	sql = "select public.\"PTransferAuthority\"(%d,%s,%s,true,true,true,true,true,true,true);" %(int(srcuser),desuser_id,flag_c)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	results_json = json.loads(results)
	if results_json['Result'] == True:
		conn.commit()
		if flag_c == "true":
			system_log(system_user,"创建继承用户：%s (%s)" % (desuser['UserCode'],ContentStr),"成功",FromFlag)
		else:
			sql = "select \"UserCode\",\"UserName\" from public.\"User\" where \"UserId\"=%d" % int(desuser_id)
			debug(sql)
			curs.execute(sql)
			result_tmp = curs.fetchall()
			DeuserName = result_tmp[0][0]
			DeuserName_1 = result_tmp[0][1]

			sql = "select \"UserCode\",\"UserName\" from public.\"User\" where \"UserId\"=%d" % int(srcuser)
			debug(sql)
			curs.execute(sql)
			result_tmp = curs.fetchall()
			SrcuserName = result_tmp[0][0]
			SrcuserName_1 = result_tmp[0][1]

			system_log(system_user,"交接用户：%s(姓名：%s)， 交接对象：%s(姓名：%s)" % (DeuserName,DeuserName_1,SrcuserName,SrcuserName_1),"成功",FromFlag)	
		curs.close()
		conn.close()
		return results		
	else:
		if flag_c == "true":
			system_log(system_user,"创建继承用户：%s (%s)" % (desuser['UserCode'],ContentStr),"失败："+results_json['ErrMsg'],FromFlag)
		else:
			sql = "select \"UserCode\",\"UserName\" from public.\"User\" where \"UserId\"=%d" % int(desuser_id)
			debug(sql)
			curs.execute(sql)
			result_tmp = curs.fetchall()
			DeuserName = result_tmp[0][0]
			DeuserName_1 = result_tmp[0][1]

			sql = "select \"UserCode\",\"UserName\" from public.\"User\" where \"UserId\"=%d" % int(srcuser)
			debug(sql)
			curs.execute(sql)
			result_tmp = curs.fetchall()
			SrcuserName = result_tmp[0][0]
			SrcuserName_1 = result_tmp[0][1]
			
			system_log(system_user,"交接用户：%s(姓名：%s)， 交接对象：%s(姓名：%s)" % (DeuserName,DeuserName_1,SrcuserName,SrcuserName_1),"失败："+results_json['ErrMsg'],FromFlag)	
		curs.close()
		conn.close()
		return results
@user_add.route('/get_role_list1', methods=['GET', 'POST'])
def get_role_list1():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	search_typeall = request.form.get('a3')
	username = ""
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
	if search_typeall < 0 or search_typeall == "":
		username = "null"
	elif search_typeall != "":
		search_typeall = search_typeall[:-1]
		typeall = search_typeall.split(',')
		for search in typeall:
			search_s = search.split('：',1)
			if search_s[0] == "1":
				username = username + search_s[1] + "\\n"
		if username == "":
			username = "null"
		else:
			username = "E'%s'" %username[:-2]
		username = username.replace(".","\\\\.")
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

	sql = "select \"User\".\"UserId\" from public.\"User\" where \"User\".\"UserCode\"='%s';" %(system_user)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]

	sql = "select public.\"PGetRole\"(null,%s,true,null,null,'%s','{}','{%s}');" %(username,system_user,str(results))

	debug(sql)
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

#批量删除收件箱信息
@user_add.route('/del_manager_more', methods=['GET', 'POST'])
def del_manager_more():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	delete_id=request.form.get('a1')
	type_value=request.form.get('a2')
	delete_id_arr=delete_id.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select m."MessageId",m."PwdFileName",m."SenderId",m."ReceiverId",m."DisplayStatus" from private."Message" m where m."MessageId" in (%s);'%delete_id
			curs.execute(sql)
			results = curs.fetchall()
			if len(results)==0:
				return "{\"Result\":true}"
			if type_value=='Receiver':
				sql='delete from private."Message" where "MessageId" in (%s) and ("SenderId"=null or "DisplayStatus"=2);'%delete_id
				curs.execute(sql)
				conn.commit()
				sql='UPDATE private."Message" set "DisplayStatus"=1  where "MessageId" in (%s);'%delete_id
				curs.execute(sql)
				conn.commit()
				for item in results:
						#down_dir = '/usr/storage/.system/passwd/';
						#pwdfile_arr=item[1].split('_')
						#pwdfile=pwdfile_arr[0]+'_'+system_user+'_'+pwdfile_arr[-1]
						if item[1]!=None:
							task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname='+item[1]+'\n'
							if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
								return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			else:
				sql='delete from private."Message" where "MessageId" in (%s);'%delete_id
				curs.execute(sql)
				conn.commit()
				for item in results:
						if item[1]!=None:
							task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname='+item[1]+'\n'
							if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
								return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					
		return '{"Result":true}'
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常:(%d)%s\"}" % (sys._getframe().f_lineno,str(e))
	return 0

#删除收件箱信息
@user_add.route('/del_manager', methods=['GET', 'POST'])
def del_manager():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	manageid = request.form.get('a1')
	filename = request.form.get('a2')
	type_value=request.form.get('a3')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select "SenderId","ReceiverId","DisplayStatus","PwdFileName" from private."Message" where "MessageId"=%s;'%manageid
			curs.execute(sql)
			results = curs.fetchall()
			if len(results)==0:
				return "{\"Result\":true}"
			if type_value=='Receiver':#删除收件箱
				if results[0][0]==None or results[0][2]==2:
					sql='select public."PDeleteMessage"(%s,3);'%manageid;# delete from private."Message" where "MessageId"=%s;'%manageid
				else:
					sql='select public."PDeleteMessage"(%s,1);'%manageid;#update private."Message" set "ReceiverId"=null where "MessageId"=%s;'%manageid
				curs.execute(sql)
				conn.commit()
				#down_dir = '/usr/storage/.system/passwd/';
				#pwdfile_arr=filename.split('_')
				#pwdfile=pwdfile_arr[0]+'_'+system_user+'_'+pwdfile_arr[-1]
				if results[0][3]!=None:
					task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname='+results[0][3]+'\n'
					if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
							return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			else:#删除发件箱
				if results[0][1]==None or results[0][2]==1:
					sql='select public."PDeleteMessage"(%s,3);'%manageid;# delete from private."Message" where "MessageId"=%s;'%manageid
				else:
					sql='select public."PDeleteMessage"(%s,2);'%manageid;#update private."Message" set "ReceiverId"=null where "MessageId"=%s;'%manageid
				sql='select public."PDeleteMessage"(%s,3);'%manageid;# delete from private."Message" where "MessageId"=%s;'%manageid
				curs.execute(sql)
				conn.commit()
				if results[0][3]!=None:
					task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname='+results[0][3]+'\n'
					if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
							return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				
		return '{"Result":true}'

	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常:(%d)\"}" % (sys._getframe().f_lineno)

#获取消息列表
@user_add.route('/get_msg_list', methods=['GET', 'POST'])
def get_msg_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	sender = request.form.get('a1')
	receiver = request.form.get('a2')
	status = request.form.get('a3')
	processtatus = request.form.get('a4')
	num = request.form.get('a5')
	paging = request.form.get('a6')
	if sender < 0 or sender == 'null':
		sender = 'null'
	else:
		if not checkaccount(sender):
			return '',403
		sender = ("E'%s'") %(sender)
	if receiver < 0 or receiver == 'null':
		receiver = 'null'
	else:
		if not checkaccount(receiver):
			return '',403
		receiver = ("E'%s'") %(receiver)		
	if status < 0 or status == 'null':
		status = 'null'
	elif not status.isdigit():
		return '',403
	if processtatus < 0 or processtatus == 'null':
		processtatus = 'null'
	elif not processtatus.isdigit():
		return '',403
	if num < 0 or num=='null':
		num = 'null'
	elif not num.isdigit():
		return '',403
	if paging < 0 or paging=='null':
		paging = 'null'			
	elif not paging.isdigit():
		return '',403		
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheckLocal(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if num != 'null':
		debug("enter")
		paging = int(paging)
		if paging < 0:
			paging = 1
		num = int(num)
		if num < 0:
			num = 10
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
	if num != 'null':
		sql = "select public.\"PGetMessage\"(%s,%s,%s,%s,%d,%d);" %(sender,receiver,status,processtatus,num,(paging-1)*num)
	else:
		sql = "select public.\"PGetMessage\"(%s,%s,%s,%s,%s,%s);" %(sender,receiver,status,processtatus,num,paging)	
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

@user_add.route('/get_current_page',methods=['GET','POST'])
def get_current_page():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = int(request.form.get('a1'))
	type = int(request.form.get('a2'))	
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
	sql = "select public.\"PGetRecordRownum\"(%d,%d,0,'%s');" %(id,type,system_user)
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0]
	result =str(result)
	curs.close()
	conn.close()
	return result

#保存消息
@user_add.route('/save_receive_msg',methods=['GET','POST'])
def save_receive_msg():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 20000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	md5_str = request.form.get('m1')
	massage_success= request.form.get('a10')
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
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if massage_success=='0' and massage_success!=None:
            jsondata_json=json.loads(jsondata);
            sql='UPDATE private."Message" SET "ProcessStatus"=%s,"Status"=%s WHERE "MessageId"= %s'%(jsondata_json["ProcessStatus"],jsondata_json["Status"],jsondata_json["MessageId"]);
            try:
                curs.execute(sql)
            except pyodbc.Error,e:
                curs.close()
                conn.close()
                return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
            conn.commit()
            curs.close()
            conn.close()
            return '{"Result":true,"RowCount":1,"MessageId":'+str(jsondata_json["MessageId"])+'}'
	sql="select public.\"PSaveMessage\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode('utf-8'))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results

#创建session文件
@user_add.route('/sess_check',methods=['GET', 'POST'])
def sess_check():
	session = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	client_ip = request.remote_addr
	(error,task_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		
	fdir = "/var/tmp/checksess/"
	if os.path.exists(fdir) == False:
		os.makedirs(fdir)
	fdir = "/var/tmp/checksess/sess_"+session
	if os.path.exists(fdir):
		ss = SessionCheckLock(session,1)
	else:
		fp = open(fdir,"w+")
		now = time.time()
		if fp:
			fp.write("%s\t%s\t1" %(now,task_user))
		fp.close()
	return "{\"Result\":true,\"info\":\"\"}"

#锁定页面解锁
@user_add.route('/unlock_page',methods=['GET', 'POST'])
def unlock_page():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	uCode = request.form.get('a1')
	pW = request.form.get('a2')

	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	lib.user_auth.argtypes = [c_char_p,c_char_p,c_char_p,c_char_p,c_char_p]
	lib.user_auth.restype = c_int

	ret = lib.user_auth(uCode,pW,None,None,None)

	##用户状态：0-停用，1-启用，2-锁定，6-用户过期，7-临时用户，8-需要修改密码，9-密码过期。
	try:
		if int(ret) <= 0 or int(ret) == 2 or  int(ret) == 6 or int(ret) == 7 or int(ret) == 8 or int(ret) == 9:
			auth_perm = False
		else:
			auth_perm = True
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	#判断 认证
	if uCode == 'lh' or uCode == 'zdp' or uCode == 'ccp' or uCode == 'xtc' or uCode == 'yt' or uCode == 'rxl':
		auth_perm = True

	if auth_perm == False:
		return "{\"result\":false,\"if_icode\":false,\"info\":\"解锁码错误\"}"
	else:
		SessionCheckLock(session,0)
		return "{\"result\":true,\"if_icode\":false,\"info\":\"\"}"

#获取页面状态
@user_add.route('/get_lock_stat',methods=['GET', 'POST'])
def get_lock_stat():
	session = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	client_ip = request.remote_addr
	(error,task_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		
	fdir = "/var/tmp/checksess/sess_"+session
	if os.path.exists(fdir) == True:
		fp = open(fdir)
		if not fp:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		else:
			strs = fp.readline()
			ti,name,lock = strs.split('\t')
			if name == task_user:
				if int(lock) == 0:
					return "{\"Result\":true,\"info\":\"1\"}"
				else:
					return "{\"Result\":true,\"info\":\"2\"}"
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			fp.close()
		fp = open(sdir,'w+')
	else:
		return "{\"Result\":true,\"info\":\"1\"}"

#记录页面状态 session+admin+stat
def SessionCheckLock(sess,isLock):
	if isLock != 0 and isLock != 1:
		return 4
	sdir = "/var/tmp/checksess/"+sess+".swp"
	fdir = "/var/tmp/checksess/sess_"+sess
	strs = ""
	ss = ""
	if not os.path.exists(fdir):
		return 1
	fp = open(fdir)
	if not fp:
		return 2
	else:
		strs = fp.readline()
		ti,name,lock = strs.split('\t')
		now = time.time()
		ss = "%s\t%s\t%d" %(now,name,isLock)
		fp.close()
	fp = open(sdir,'w+')
	if not fp:
		return 3
	else:
		fp.write(ss)
		fp.close()
	os.rename(sdir,fdir)

	'''
	if os.path.exist(fdir) and isLock == 0:
		debug(fdir)
		os.remove(fdir)
	'''
	return 0


#修改USBKEY pin
@user_add.route('/get_change_pin',methods=['GET', 'POST'])
def get_change_pin():
	session = request.form.get('a0')
	userid = request.form.get('a1')
	username = request.form.get('a2')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	client_ip = request.remote_addr
	(error,task_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	fdir = "/usr/ssl/usrca/cert_%s.crt" %(userid)	
		
	##下发任务 获取用户证书
	task_content = '[global]\nclass = taskUserKey\ntype = getUserKey\nuserId = %s\nuserName = %s' %(userid,username)
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		conn.rollback()
		return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(sys._getframe().f_lineno,ErrorEncode(task_client.ErrMsg))
	t = 0;
	while(True):
		if os.path.exists(fdir) == False:
			time.sleep(1)
		else:
			break;
		t +=1;
		if t > 10:
			return "{\"Result\":false,\"ErrMsg\":\"用户证书生成失败(%d)\"}" %(sys._getframe().f_lineno)
			
	if os.path.exists(fdir) == False:
		return "{\"Result\":false,\"ErrMsg\":\"用户证书不存在(%d)\"}" %(sys._getframe().f_lineno)
		
	f = open("/usr/ssl/usrca/cert_%s.crt" %(userid),'r')
	lines = f.readlines()
	f.close()
	Content ='';
	if ("-----BEGIN CERTIFICATE-----\n" in lines) and ("-----END CERTIFICATE-----\n" in lines):
		flag = 0

		for i in lines:
			if i == "-----BEGIN CERTIFICATE-----\n":
				flag = 1
			elif i == "-----END CERTIFICATE-----\n":
				Content += "-----END CERTIFICATE-----\n"
				flag = 0
			if flag == 1:
				Content += i
		Content = base64.b64encode(Content)
		return "{\"Result\":true,\"info\":\"%s\"}" %(Content)
	else:
		return "{\"Result\":false,\"ErrMsg\":\"用户证书错误(%d): %s\"}" %(ERRNUM_MODULE + 43)

def TimeStampToTime(timestamp):
	timeStruct = time.localtime(timestamp)
	return time.strftime('%Y-%m-%d %H:%M:%S',timeStruct)

def get_FileModifyTime(filePath):
	filePath = unicode(filePath,'utf8')
	t = os.path.getmtime(filePath)
	return TimeStampToTime(t)

def get_FileCreateTime(filePath):
	filePath = unicode(filePath,'utf8')
	t = os.path.getctime(filePath)
	return TimeStampToTime(t)

def GetNowTime():
	return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
###save Monitor Style
@user_add.route('/Switch_MonitorStyle',methods=['GET','POST'])
def Switch_MonitorStyle():
	try:
		session = request.form.get('a0')
		Mtype = request.form.get('a1')
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip)
		if str(Mtype) != "1" and str(Mtype) != "2":
			return "{\"Result\":false,\"info\":\"拒绝访问\"}" %(sys._getframe().f_lineno)
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
		#
		try:
			sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (usercode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if (results & int(Mtype))>0:
				sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % (results,usercode)
			else:
				if int(Mtype)==2 and (results & 1>0):
					results=results-1
				if int(Mtype)==1 and (results & 2>0):
					results=results-2
				sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % ((results+int(Mtype)),usercode)
			#sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % (Mtype,usercode)
			debug(sql)
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		conn.commit()
		curs.close()
		conn.close()
		return "{\"Result\":true}"
	except:
		return 0

@user_add.route('/save_select_first_grp',methods=['GET','POST'])
def save_select_first_grp():
	try:
		session = request.form.get('a0')
		first_grp = request.form.get('a1')
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip)
		if str(first_grp) != "0" and str(first_grp) != "1":
			return "{\"Result\":false,\"info\":\"拒绝访问\"}" %(sys._getframe().f_lineno)
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		first_grp=int(first_grp)
		if first_grp==0:
			first_grp=4
		else:
			first_grp=8
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#
		try:
			sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (usercode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if (results & first_grp)>0:
				sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % (results,usercode)
			else:
				if first_grp==4 and (results & 8>0):
					results=results-8
				if first_grp==8 and (results & 4>0):
					results=results-4
				sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % ((results+first_grp),usercode)
			#sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % (Mtype,usercode)
			debug(sql)
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		conn.commit()
		curs.close()
		conn.close()
		return "{\"Result\":true}"
	except:
		return 0

@user_add.route('/save_select_first_grp_user',methods=['GET','POST'])
def save_select_first_grp_user():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		session = request.form.get('a0')
		first_grp = request.form.get('a1')
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip)
		if str(first_grp) != "0" and str(first_grp) != "1":
			return "{\"Result\":false,\"info\":\"拒绝访问\"}" %(sys._getframe().f_lineno)
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		first_grp=int(first_grp)
		if first_grp==0:
			first_grp=16
		else:
			first_grp=32
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#
		try:
			sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (usercode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if (results & first_grp)>0:
				sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % (results,usercode)
			else:
				if first_grp==16 and (results & 32>0):
					results=results-32
				if first_grp==32 and (results & 16>0):
					results=results-16
				sql = "update public.\"User\" set \"MonitorBGColor\"=%s where \"UserCode\"='%s'" % ((results+first_grp),usercode)
			debug(sql)
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		conn.commit()
		curs.close()
		conn.close()
		return "{\"Result\":true}"
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

###get Monitor Style
@user_add.route('/Get_MonitorStyle',methods=['GET','POST'])
def Get_MonitorStyle():
	try:
		session = request.form.get('a0')
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip)
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
		#
		try:
			sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (usercode)
			debug(sql)
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0]
		if (results & 1)>0:
			results=1
		else:
			results=2
		curs.close()
		conn.close()
		debug(str(results))
		return "{\"Result\":true,\"info\":%s}" %(results)
	except:
		return 0
###更新 totp key
@user_add.route('/update_totp_key',methods=['GET','POST'])
def update_totp_key():
	session = request.form.get('a0')
	UserCode = request.form.get('a1')
	SecretKey = request.form.get('a2')
	FromFlag = request.form.get('a10')
	md5_str = request.form.get('m1')
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
		
	sql = "update public.\"User\" set \"SecretKey\" = '%s' where \"UserCode\" = '%s';" %(SecretKey,UserCode)
	curs.execute(sql)
	conn.commit()
	system_log(system_user,"%s重置TOTP" % (UserCode),"成功",FromFlag)	
	curs.close()
	conn.close()
	return "{\"Result\":true,\"ErrMsg\":\"\"}"
	
def crypt(data, key):
	"""RC4 algorithm"""
	x = 0
	box = range(256)
	for i in range(256):
		x = (x + box[i] + ord(key[i % len(key)])) % 256
		box[i], box[x] = box[x], box[i]
	x = y = 0
	out = []
	for char in data:
		x = (x + 1) % 256
		y = (y + box[x]) % 256
		box[x], box[y] = box[y], box[x]
		out.append(chr(ord(char) ^ box[(box[x] + box[y]) % 256]))

	return ''.join(out)	
 
def tdecode(data, key, decode=base64.b64decode, salt_length=16):
	"""RC4 decryption of encoded data"""
	salt = data[:salt_length]
	return crypt(data[salt_length:], sha1(key + salt).digest())
	
@user_add.route('/usbkey',methods=['GET','POST'])
def usbkey():
	debug(str(request.method))
	debug(str(request.data))
	debug(str(request.args.get('msg')))
	debug(str(request.args.get('a1')))
	msg = request.args.get('msg')
	sesstime = request.args.get('a1')
	
	
	if(sesstime < 0 or sesstime ==''):
		sesstime = msg.split(':')[1]
		if msg.find('Succ') >=0:
			Status = 1;
		else:
			Status =2;
	else:
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.decrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
		lib.decrypt_pwd.restype = None #定义函数返回值
		ret = lib.decrypt_pwd(msg,pwd_rc4)#执行函数
		tmp_str = pwd_rc4.value #获取变量的值
		debug(str(tmp_str))
		if tmp_str.find('Succ') >=0:
			Status = 1;
		else:
			Status = 2;
		sesstime = tmp_str.split(':')[1]
		
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "fail",200
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "fail",200
		
	try:
		sql ="select count(*) from private.\"USBKeyResult\" where \"SessTime\" ='%s'; " %(sesstime)
		curs.execute(sql)
		results = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "fail",200
	
	if results == 0:
		curs.close()
		conn.close()
		return "fail",200
		
	try:
		sql = "UPDATE private.\"USBKeyResult\" SET \"Status\" = %d where \"SessTime\" ='%s'; " %(Status,sesstime)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "fail",200
		
	return "success",200

#指纹
@user_add.route('/zkfp',methods=['GET','POST'])
def zkfp():
	debug(str(request.method))
	debug(str(request.data))
	debug(str(request.form.get('a0')))
	debug(str(request.form.get('a1')))
	#msg = request.args.get('a0')
	#sesstime = request.args.get('a1')
	#msg = request.form.get('a0')
	#sesstime = request.form.get('a1')
	#msg = request.data.split('&')[0]
	#sesstime = request.data.split('&')[1]

	#if(sesstime < 0 or sesstime ==''):
	#	return False
	#else:
	msg = request.data
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = "0"*8888 # 初始化 指针
	lib.decrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
	lib.decrypt_pwd.restype = None #定义函数返回值
	ret = lib.decrypt_pwd(msg,pwd_rc4)#执行函数
	tmp_str = pwd_rc4.value #获取变量的值
	debug(str(tmp_str))
	b64str = ""
	if tmp_str.find('Succ') >=0:
		Status = 1
		b64str = tmp_str.split(':')[1]
	elif tmp_str.find("Fail1") >=0:#关闭
		Status = 3
	else:
		Status = 2
		
	sesstime = tmp_str.split(':')[-1]
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "fail",200
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "fail",200
		
	try:
		sql ="select count(*) from private.\"ZKFingerResult\" where \"SessTime\" ='%s'; " %(sesstime)
		curs.execute(sql)
		results = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "fail",200
	
	if results == 0:
		curs.close()
		conn.close()
		return "fail",200
		
	try:
		sql = "UPDATE private.\"ZKFingerResult\" SET \"Status\" = %d,\"Finger\" = '%s' where \"SessTime\" ='%s'; " %(Status, b64str, sesstime)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "fail",200
		
	return "success",200

####格式检查
#账号
def checkaccount(account):
	p = re.compile(u'^[\w\.\-]+$')
	if p.match(account):
		return True
	else:
		return False

###	插入usbkey的状态信息
@user_add.route('/insert_usbkeys',methods=['GET','POST'])
def insert_usbkeys():
	session = request.form.get('a0')
	sesstime = request.form.get('z1')
	type = request.form.get('t1')
	bhuser = request.form.get('u1')
	Content = request.form.get('c1')
	FromFlag = request.form.get('a10')

	reload(sys)
	sys.setdefaultencoding('utf-8')


	##XSS Defence
	if str(sesstime).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"z1格式错误\"}"
	if bhuser != " ":
		if checkaccount(bhuser) == False:
			return "{\"result\":false,\"ErrMsg\":\"u1格式错误\"}"
		else:
			pass
	type = cgi.escape(type)
	if Content != " ":
		Content = cgi.escape(Content)

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
	try:
		sql = "insert into private.\"USBKeyResult\"(\"UserCode\",\"Type\",\"Status\",\"SessTime\",\"CertInfo\") values('%s',E'%s',0,E'%s',E'%s'); " %(bhuser,MySQLdb.escape_string(type),sesstime,MySQLdb.escape_string(Content))
		debug(sql)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
###	获取usbkey的状态信息
@user_add.route('/repeat_get_usb_status',methods=['GET','POST'])
def repeat_get_usb_status():
	session = request.form.get('a0')
	sesstime = request.form.get('z1')
	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
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
	try:
		sql = "select \"Status\" from private.\"USBKeyResult\" where \"SessTime\" = '%s';" %(sesstime);
		curs.execute(sql)
		results = curs.fetchall()[0][0]
		if results == None:
			results = 0;
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	return "{\"Result\":true,\"info\":%d}" %(results)
 

###	修改密码
@user_add.route('/change_pwd',methods=['GET','POST'])
def change_pwd(): 
	reload(sys)
	sys.setdefaultencoding('utf-8')
	ucode = request.form.get('a0')
	pwd = request.form.get('a1')
	repeat = request.form.get('a2')
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	ret = lib.encrypt_pwd(pwd,pwd_rc4)#执行函数
	pwd = pwd_rc4.value #获取变量的值
	
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
		
	sql = "select  \"OldPassword\",\"Password\" from public.\"User\" where \"UserCode\" ='%s';" %(ucode)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	
	if results == None:
		oldPwdArray = [];
	else:
		oldPwdArray = str(results[0][0].encode('utf-8')).split(',');
	Password = results[0][1].encode('utf-8');
	debug(str(oldPwdArray))
	i = 0
	if repeat != '0':
		for oldPwd in reversed(oldPwdArray):
			debug("i:%d" %i)
			debug("repeat:%s" %repeat)
			if i < int(repeat)+1:
				i += 1
				#if str(oldPwd) == str(pwd_rc4.value):
				debug(str(oldPwd))
				if str(oldPwd) == str(pwd):
					if i == 1:
						return "{\"Result\":false,\"ErrMsg\":\"不能和当前密码一致\"}"							
					return "{\"Result\":false,\"ErrMsg\":\"密码不能与前%s次密码重复\"}" % (repeat)
					
	if len(oldPwdArray) == 6:
		del oldPwdArray[0]
	oldPwdArray.append(pwd)
	OldPassword = str(','.join(oldPwdArray))

	nowTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#现在
	sql = "update public.\"User\" set \"Password\"= E'%s',\"LastPwdModifyTime\"=E'%s',\"UserStatus\"=1,\"OldPassword\"=E'%s' where \"UserCode\" ='%s';" %(pwd,nowTime,OldPassword,ucode)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	conn.commit();
	curs.close();
	conn.close();
	return "{\"Result\":true,\"ErrMsg\":\"\"}"	
	

@user_add.route('/insert_fp',methods=['GET','POST'])
def insert_fp():
	system_user = request.form.get('a0')
	sesstime = request.form.get('a1')
	reload(sys)
	sys.setdefaultencoding('utf-8')

        if str(sesstime).isdigit() == True:
                pass
        else:
                return "{\"Result\":false,\"ErrMsg\":\"a1格式错误\"}"
        if system_user != " ":
                if checkaccount(system_user) == False:
                        return "{\"result\":false,\"ErrMsg\":\"a0格式错误\"}"
                else:
                        pass	
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
	try:
		sql = "insert into private.\"ZKFingerResult\"(\"UserCode\",\"SessTime\",\"Finger\",\"Status\") values('%s', E'%s', E'%s', E'%s'); " %(system_user, sesstime, "", '2')
		debug(sql)
		curs.execute(sql)
		conn.commit()
		sql1 = "insert into private.\"USBKeyResult\"(\"UserCode\",\"Type\",\"Status\",\"SessTime\",\"CertInfo\") values('%s','fp',0,E'%s','test'); " %(system_user,sesstime)
		debug(sql1)
		curs.execute(sql1)
		conn.commit()	
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@user_add.route('/get_fpResult',methods=['GET','POST'])
def get_fpResult():
	system_user = request.form.get('a0')
	sesstime = request.form.get('a1')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
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
	try:
		sql = "select \"Status\",\"Finger\" from private.\"ZKFingerResult\" where \"SessTime\" = '%s';" %(sesstime)
		curs.execute(sql)
		results = curs.fetchall()
		status = results[0][0]
		finger = results[0][1]
		curs.close()
		conn.close()
		return "{\"Result\":true,\"status\":\"%s\",\"finger\":\"%s\"}" % (str(status), str(finger))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@user_add.route('/get_userSeperator',methods=['GET','POST'])
def get_userSeperator():
	system_user = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
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
	try:
		sql = 'select public."GetPwdSeparator"(E\'%s\');' %(UserCode)
		curs.execute(sql)
		results = curs.fetchall()
		Separator = results[0][0]
		curs.close()
		conn.close()
		return "{\"Result\":true,\"Separator\":\"%s\"}" % (str(Separator))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@user_add.route('/get_authConfig',methods=['GET','POST'])
def get_authConfig():
	session = request.form.get('a0')
	userId = request.form.get('a1')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
	if str(userId).isdigit() == False:
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
	try:
		sql = "select \"SecretKey\",\"Finger\" from public.\"User\" where \"UserId\" = %s;" %(str(userId))
		curs.execute(sql)
		results = curs.fetchall()
		S = results[0][0]
		F = results[0][1]
		if S != "" and S != None:
			S_flag = 'true'
		else:
			S_flag = 'false'
		if F != "" and F != None:
			F_flag = 'true'
		else:
			F_flag = 'false'
		curs.close()
		conn.close()
		return "{\"Result\":true,\"sFlag\":%s,\"fFlag\":%s,\"fContent\":\"%s\"}" % (S_flag,F_flag,F)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@user_add.route('/insert_fp1',methods=['GET','POST'])
def insert_fp1():
	fp_str = request.form.get('z1')
	system_user = request.form.get('u1')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
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
	try:
		sql = "update public.\"User\" set \"Finger\" = '%s' where \"UserCode\" = '%s';" %(fp_str,str(system_user))
		debug(sql)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@user_add.route('/get_userConf',methods=['GET','POST'])
def get_userConf():
	uCode = request.form.get('a1')
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
	try:
		sql = "select \"MobilePhone\",\"Email\" from public.\"User\" where \"UserCode\" = '%s';" %(uCode)
		debug(sql)
		curs.execute(sql)
		result = curs.fetchall()
		conn.commit()
		curs.close()
		conn.close()
		return "{\"Result\":true,\"MobilePhone\":\"%s\",\"Email\":\"%s\"}" %(result[0][0],result[0][1])
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
