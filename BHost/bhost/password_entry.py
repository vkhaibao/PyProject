#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionOnline
from comm import LogSet
from htmlencode import parse_sess
from htmlencode import check_role,checkarr_1
from logbase import common
from ctypes import *
import MySQLdb
from generating_log import system_log


from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
password_entry = Blueprint('password_entry',__name__)

ERRNUM_MODULE_password_entry = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@password_entry.route('/password_entry_show',methods=['GET','POST'])
def password_entry_show():
	return render_template('password_entry.html')

@password_entry.route('/manage_pwd',methods=['GET','POST'])
def manage_pwd():
	return render_template('manage_password.html')
	
@password_entry.route('/get_hostdirectory_pwd',methods=['GET','POST'])
def get_hostdirectory_pwd():
	session = request.form.get('a0')
	id = request.form.get('z1')
	find_doing = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	error_1= SessionOnline(session)
	if id == "-1":
		id = 0
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if str(find_doing)=='true':
				curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,0,0,null,null,%s);" %(MySQLdb.escape_string(usercode).decode("utf-8"),int(id),str(find_doing)))
			else:
				debug("select public.\"PGetHostDirectory\"('%s',%d,0,0,null,null);" %(MySQLdb.escape_string(usercode).decode("utf-8"),int(id)))
				curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,0,0,null,null);" %(MySQLdb.escape_string(usercode).decode("utf-8"),int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@password_entry.route('/get_host_pwd',methods=['GET','POST'])
def get_host_pwd():
	session = request.form.get('a0')
	id = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	#error_1=SessionOnline(session)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetHost\"(%d,false,'%s');" %(int(id),usercode))
			if client_ip == '192.168.0.103':
				debug("id=%d---time=%s" %(int(id),str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))))
			curs.execute("select public.\"PGetHost\"(%d,false,E'%s');" %(int(id),usercode))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@password_entry.route('/get_hgroup_pwd',methods=['GET','POST'])
def get_hgroup_pwd():
	session = request.form.get('a0')
	id = request.form.get('z1')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetHGroup\"(%d);" %(int(id)))
			curs.execute("select public.\"PGetHGroup\"(%d);" %(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@password_entry.route('/modify_pwd',methods=['GET','POST'])
def modify_pwd():
	session = request.form.get('a0')
	data = request.form.get('z1')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)：%d\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno)

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(usercode,'密码录入') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	pwd_json =  json.loads(data);
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	if pwd_json['Password'] != None:
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd(pwd_json['Password'],pwd_rc4);#执行函数
		pwd_json['Password'] = pwd_rc4.value #获取变量的值
       	pwd_data = json.dumps(pwd_json)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PBatchModifyPwd\"(E'%s');" %(MySQLdb.escape_string(pwd_data).decode('utf-8')))
			curs.execute("select public.\"PBatchModifyPwd\"(E'%s');" %(MySQLdb.escape_string(pwd_data).decode('utf-8')))
			results = curs.fetchall()[0][0]
			hgoper=''
			hostoper=''
			accoper=''
			for i in pwd_json['HostSet']:
				if i['HostId']==None:
					hgoper=hgoper+'['+i['Name']+']'+'、'
				else:
					hostoper=hostoper+i['Name'].split('-')[0]+'、'
			for i in pwd_json['PasswordAuthSet']:
				accoper=accoper+i['Name']+'、'
			oper='录入密码（'
			if hgoper!='':
				hgoper=hgoper[:-1]
				oper=oper+'主机组：'+hgoper+'，'
			if hostoper!='':
				hostoper=hostoper[:-1]
				oper=oper+'主机：'+hostoper+'，'
			if accoper!='':
				accoper=accoper[:-1]
				oper=oper+'账号：'+accoper+'，'
			oper=oper[:-1]
			oper=oper+'）'
			if not system_log(usercode,oper,'成功','密码管理>密码录入'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@password_entry.route('/PGet_AccountNum',methods=['GET','POST'])
def PGet_AccountNum():
	session = request.form.get('a0')
	json_data = request.form.get('z1')
	try:
		json_data_t=json.loads(json_data)
		if 'hgidset' in json_data_t and not checkarr_1(json_data_t['hgidset']):
			return '',403
		if 'hostidset' in json_data_t and not checkarr_1(json_data_t['hostidset']):
			return '',403
	except ValueError:
		return '',403
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetAccountNum\"(E\'%s\');" % (json_data))
			curs.execute("select public.\"PGetAccountNum\"(E\'%s\');" % (json_data))
			results = curs.fetchall()[0][0]
			debug("11111")
			debug(str(results))
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)


