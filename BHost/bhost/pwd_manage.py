#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
import pyodbc
import MySQLdb
import ConfigParser
import json
import time
import base64

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from htmlencode import parse_sess
from htmlencode import check_role
from logbase import common
from logbase import task_client
from logbase import defines
from ctypes import *
from urllib import unquote
from generating_log import system_log
from comm_function import get_user_perm_value

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
pwd_manage = Blueprint('pwd_manage',__name__)

SIZE_PAGE = 20
ErrorNum = 10000
def debug(c):
	return 0
        path = "/var/tmp/debugrx_ccp123.txt"
        fp = open(path,"a+")
        if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values (E'%s',E'%s',E'%s',E'%s',E'%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	LogSet(None, sqlconf, 6)
	
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
#删除del_pwdauth
@pwd_manage.route('/del_pwdauth',methods=['GET', 'POST'])
def del_pwdauth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	type_plan=request.form.get('a2')
	if type_plan<0 or type_plan==None or type_plan==1:
		type_plan='自动改密'
	else:
		type_plan='手动改密'
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			for id in ids:
				id=int(id)
				sql1='select plan."PwdModPlanName" from public."PwdModPlan" plan where plan."PwdModPlanId"=%s;'%(id)
				curs.execute(sql1)
				result1 = curs.fetchall()[0][0]
				# PDeletePwdModPlan(pwdmodplanid)
				sql = "select public.\"PDeletePwdModPlan\"(%d);" % (id)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				if "false" in result:
					if not system_log(system_user,'删除改密计划：%s'%(result1),'参数错误','密码管理>%s'%type_plan):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					#return result
					fail_num+=1
				else:
					conn.commit()
					if not system_log(system_user,'删除改密计划：%s'%(result1),'成功','密码管理>%s'%type_plan):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					success_num+=1
			return "{\"Result\":true,\"success_num\":%d,\"fail_num\":%d}" %(success_num,fail_num)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#停1s
@pwd_manage.route('/sleep_1_s',methods=['GET','POST'])
def  sleep_1_s():
	session = request.form.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	time.sleep(1)
	
#页面跳转函数
@pwd_manage.route('/pwd_trust',methods=['GET','POST'])
def pwd_trust():
	#页面跳转函数
	#参数 tasktype = 添加-1
	#a=id
	#session = request.form.get("se")
	tasktype = request.form.get("tasktype")
	page = request.form.get("c")
	id = request.form.get("a")
	search_typeall=request.form.get("d")
	us=request.form.get("us")
	se=request.form.get("se")
	e=request.form.get("e")
	if e<0:
		e=''
	if se<0:
		se=''
	if us<0:
		us=''
	if id < 0 or id == None:
		id = "0"
	if page < 0 or page == None:
		page = "1"
	if tasktype < 0 or tasktype == None:
		tasktype = "1"
	if search_typeall < 0 or search_typeall == None:
		search_typeall = ""
	if e<0 or e==None:
		e=':'
	if tasktype == "3":
		t = "pwdauth_list.html"
	else:
		t = "pwdauth_add.html"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_1=1
	perm_server=1
	perm_pwd_mod=1
	perm_client=0
	perm_host=1
	for i in perm_json:
		if i['SubMenuId']==20 and i['SystemMenuId']==4:
			if i['Mode']>perm:
				perm=i['Mode']
			#if i['Mode']>perm_server:
			#	perm_server=i['Mode']
			#if i['Mode']>perm_pwd_mod:
			# 	perm_pwd_mod=i['Mode']
		elif i['SubMenuId']==14 and i['SystemMenuId']==3 and perm_host<i['Mode']:
			perm_host=i['Mode']
		elif i['SubMenuId']==13 and i['SystemMenuId']==3 and perm_client<i['Mode']:
			perm_client=i['Mode']
		elif i['SubMenuId']==24 and i['SystemMenuId']==6 and perm_1<i['Mode']:
			perm_1=i['Mode']
		#elif i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm_server:
			#perm_server=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3:
			#if i['Mode']>perm_server:
			#	perm_server=i['Mode']
			if i['Mode']>perm_client:
				perm_client=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3:
			#if i['Mode']>perm_server:
			#	perm_server=i['Mode']
			if i['Mode']>perm_client:
				perm_client=i['Mode']
		elif  i['SubMenuId']==18 and i['SystemMenuId']==3:
			#if i['Mode']>perm_server:
			#	perm_server=i['Mode']
			if i['Mode']>perm_client:
				perm_client=i['Mode']
		#elif  i['SubMenuId']==21 and i['SystemMenuId']==4:
			#if i['Mode']>perm_server:
			#	perm_server=i['Mode']
			#if i['Mode']>perm_pwd_mod:
			#	perm_pwd_mod=i['Mode']
		if perm_1==2 and perm==2 and perm_client==2 and perm_host==2:
			break
	perm_server=perm
	perm_pwd_mod=perm
	return render_template(t,tasktype=tasktype,a=id,c=page,perm_host=perm_host,perm_client=perm_client,d=search_typeall,us=us,se=se,e=e,perm=perm,perm_1=perm_1,perm_server=perm_server,perm_pwd_mod=perm_pwd_mod)
#显示 or 分页 or 搜索改密策略
@pwd_manage.route('/get_pwdmodstrategy',methods=['GET', 'POST'])
def get_pwdmodstrategy():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	loginusercode = request.form.get('a5')
	pwdauthId = request.form.get('a1')
	search_typeall = request.form.get('a2')
	Name=""
	if loginusercode < 0:
		loginusercode = "null"
	else:
		loginusercode="'%s'"% loginusercode
	if search_typeall<0:
		search_typeall=""
	if pwdauthId<0 or pwdauthId=="0" or pwdauthId=="":
		pwdauthId="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split(',')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetPwdModStrategy(loginusercode,pwdmodstrategyid,pwdmodstrategyname,limitrow,offsetrow)
			sql="select public.\"PGetPwdModStrategy\"(%s,%s,%s,%s,%s);"%(loginusercode,pwdauthId,Name,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results = json.loads(results)
			if pwdauthId!='null':
				if results['data'][0]['Password']!='' and results['data'][0]['Password']!=None:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					ret = lib.decrypt_pwd(results['data'][0]['Password'],pwd_rc4);#执行函数
					results['data'][0]['Password'] = pwd_rc4.value #获取变量的值
			results = json.dumps(results)
			results = str(results)	
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	

#显示 or 分页 or 搜索FTP服务器
@pwd_manage.route('/get_ftpserver',methods=['GET', 'POST'])
def get_ftpserver():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	ftpserverid = request.form.get('a1')
	search_typeall = request.form.get('a2')
	Name=""
	if search_typeall<0:
		search_typeall=""
	if ftpserverid<0 or ftpserverid=="0" or ftpserverid=="":
		ftpserverid="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split(',')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetFTPServer(ftpserverid,name,limitrow,offsetrow)
			sql="select public.\"PGetFTPServer\"(%s,%s,%s,%s);"%(ftpserverid,Name,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results = json.loads(results)
			if ftpserverid!='null':
				if results['data'][0]['ServerPasswd']!='' and results['data'][0]['ServerPasswd']!=None:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					ret = lib.decrypt_pwd(results['data'][0]['ServerPasswd'],pwd_rc4);#执行函数
					results['data'][0]['ServerPasswd'] = pwd_rc4.value #获取变量的值
			results = json.dumps(results)
			results = str(results)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除FTP服务器
@pwd_manage.route('/del_ftpserver',methods=['GET', 'POST'])
def del_ftpserver():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	if session <0 :
		sesson=""
	if id_str <0 :
		id_str=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PDeleteFTPServer(id)
			sql = "select public.\"PDeleteFTPServer\"(%s);" % (id_str)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			conn.commit()
			return results  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#创建 or 编辑add_ftpserver
@pwd_manage.route('/add_ftpserver',methods=['GET','POST'])
def add_ftpserver():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	ftpserver_save = request.form.get('a1')
	type_name=request.form.get('a2')
	md5_str=request.form.get('m1')
	if sess<0:
		sess=""
	if type_name<0:
		type_name='系统管理>输出设置'
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(ftpserver_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	ftpserver_save = json.loads(ftpserver_save)
	if(ftpserver_save['ServerPasswd'] != "" and ftpserver_save['ServerPasswd']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
				return "{\"Result\":false,\"info\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(ftpserver_save['ServerPasswd'],pwd_rc4);#执行函数
		ftpserver_save['ServerPasswd'] = pwd_rc4.value #获取变量的值
	ftpserver_save = json.dumps(ftpserver_save)
	ftpserver_save=str(ftpserver_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveFTPServer(ftpserver_save)
			sql="select public.\"PSaveFTPServer\"(E'%s');" %(MySQLdb.escape_string(ftpserver_save).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			ftpserver_save_json=json.loads(ftpserver_save)
			if ftpserver_save_json['FTPServerId']==0:
				_type_name='新建'
			else :
				_type_name='编辑'
			if result_json['Result']:
				conn.commit()
				if ftpserver_save_json['Flag']==0:
					ftpserver_save_json['Flag']='其他'
				elif ftpserver_save_json['Flag']==1:
					ftpserver_save_json['Flag']='备用'
				elif ftpserver_save_json['Flag']==2:
					ftpserver_save_json['Flag']='默认'
				if ftpserver_save_json['IfPasv']:
					ftpserver_save_json['IfPasv']='被动'
				else:
					ftpserver_save_json['IfPasv']='主动'
				if not system_log(system_user,'%sFTP服务器配置：%s（服务器IP：%s，用户名：%s，上传路径：%s，方式：%s，模式：%s）'
				%(_type_name,ftpserver_save_json['FTPServerName'],ftpserver_save_json['ServerIP'],ftpserver_save_json['ServerUser'],ftpserver_save_json['ServerPath'],ftpserver_save_json['Flag'],ftpserver_save_json['IfPasv']),'成功',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				if not system_log(system_user,'%sFTP服务器配置：%s'
				%(_type_name,ftpserver_save_json['FTPServerName']),result_json['ErrMsg'],type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result
			 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索邮件服务器
@pwd_manage.route('/get_smtpconfig',methods=['GET', 'POST'])
def get_smtpconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	smtpconfigid = request.form.get('a1')
	if smtpconfigid<0 or smtpconfigid=="0" or smtpconfigid=="":
		smtpconfigid="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetSmtpConfig(smtpconfigid,limitrow,offsetrow)
			sql="select public.\"PGetSmtpConfig\"(%s,%s,%s);"%(smtpconfigid,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results = json.loads(results)
			if smtpconfigid!='null':
				if results['data'][0]['SenderEmailPass']!='' and results['data'][0]['SenderEmailPass']!=None:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					ret = lib.decrypt_pwd(results['data'][0]['SenderEmailPass'],pwd_rc4);#执行函数
					results['data'][0]['SenderEmailPass'] = pwd_rc4.value #获取变量的值
			results = json.dumps(results)
			results = str(results)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#创建 or 编辑add_smtpconfig
@pwd_manage.route('/add_smtpconfig',methods=['GET','POST'])
def add_smtpconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	smtpconfig_save = request.form.get('a1')
	type_name = request.form.get('a2')
	md5_str=request.form.get('m1')
	if sess<0:
		sess=""
	if type_name<0:
		type_name='系统管理>输出设置'
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(smtpconfig_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	smtpconfig_save = json.loads(smtpconfig_save)
	if(smtpconfig_save['SenderEmailPass'] != "" and smtpconfig_save['SenderEmailPass']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(smtpconfig_save['SenderEmailPass'],pwd_rc4);#执行函数
		smtpconfig_save['SenderEmailPass'] = pwd_rc4.value #获取变量的值
	smtpconfig_save = json.dumps(smtpconfig_save)
	smtpconfig_save = str(smtpconfig_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveSmtpConfig(smtpconfig_save)
			sql="select public.\"PSaveSmtpConfig\"(E'%s');" %(MySQLdb.escape_string(smtpconfig_save).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			smtpconfig_save_json=json.loads(smtpconfig_save)
			if smtpconfig_save_json['SmtpConfigId']==0:
				_type_name='新建'
			else :
				_type_name='编辑'
			if result_json['Result']:
				conn.commit()
				if smtpconfig_save_json['Flag']==0:
					smtpconfig_save_json['Flag']='其他'
				elif smtpconfig_save_json['Flag']==1:
					smtpconfig_save_json['Flag']='备用'
				elif smtpconfig_save_json['Flag']==2:
					smtpconfig_save_json['Flag']='默认'
				if smtpconfig_save_json['EnCode']==0:
					smtpconfig_save_json['EnCode']='UTF-8'
				else:
					smtpconfig_save_json['EnCode']='GBK'
				if smtpconfig_save_json['ServerVerify']:
					smtpconfig_save_json['ServerVerify']='是'
				else:
					smtpconfig_save_json['ServerVerify']='否'
				if smtpconfig_save_json['AttachMaxLimit']==None:
					smtpconfig_save_json['AttachMaxLimit']='0'
				if not system_log(system_user,'%s邮件服务器配置：%s（服务器：%s，账号：%s，地址：%s，附件大小：%sM，服务器验证：%s，编码方式：%s，方式：%s）'
				%(_type_name,smtpconfig_save_json['SmtpConfigName'],smtpconfig_save_json['SmtpServer'],smtpconfig_save_json['Sender'],
				smtpconfig_save_json['SenderEmail'],smtpconfig_save_json['AttachMaxLimit'],smtpconfig_save_json['ServerVerify'],smtpconfig_save_json['EnCode'],smtpconfig_save_json['Flag']),'成功',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				if not system_log(system_user,'%s邮件服务器配置：%s'
				%(_type_name,smtpconfig_save_json['SmtpConfigName']),result_json['ErrMsg'],type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result
			# conn.commit()
			# return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除邮件服务器
@pwd_manage.route('/del_smtpconfig',methods=['GET', 'POST'])
def del_smtpconfig():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	if session <0 :
		sesson=""
	if id_str <0 :
		id_str=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PDeleteSmtpConfig(id)
			sql = "select public.\"PDeleteSmtpConfig\"(%s);" % (id_str)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			conn.commit()
			return results  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#显示 or 分页 or 搜索短信网关
@pwd_manage.route('/get_smssvrconfig',methods=['GET', 'POST'])
def get_smssvrconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	smssvrconfigid = request.form.get('a1')
	if smssvrconfigid<0 or smssvrconfigid=="0" or smssvrconfigid=="":
		smssvrconfigid="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetSmsSvrConfig(smssvrconfigid,limitrow,offsetrow)
			sql="select public.\"PGetSmsSvrConfig\"(%s,%s,%s);"%(smssvrconfigid,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results = json.loads(results)
			if smssvrconfigid!='null':
				if results['data'][0]['SmsSvrDBPassword']!='' and results['data'][0]['SmsSvrDBPassword']!=None:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					ret = lib.decrypt_pwd(results['data'][0]['SmsSvrDBPassword'],pwd_rc4);#执行函数
					results['data'][0]['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
				results['data'][0]['SmsSvrDBInsertTemp'] = base64.b64decode(results['data'][0]['SmsSvrDBInsertTemp']).encode('utf-8')
			results = json.dumps(results)
			results = str(results)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
	
#创建 or 编辑短信网关
@pwd_manage.route('/add_smssvrconfig',methods=['GET','POST'])
def add_smssvrconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	smtpconfig_save = request.form.get('a1')
	module_name=request.form.get('a10')
	md5_str=request.form.get('m1')
	if module_name<0:
		module_name='系统管理>输出设置'
	if sess<0:
		sess=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(smtpconfig_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"		
	smtpconfig_save = json.loads(smtpconfig_save)
	if(smtpconfig_save['SmsSvrDBPassword'] != "" and smtpconfig_save['SmsSvrDBPassword']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(smtpconfig_save['SmsSvrDBPassword'],pwd_rc4);#执行函数
		smtpconfig_save['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
		smtpconfig_save['SmsSvrDBInsertTemp'] =base64.b64encode(smtpconfig_save['SmsSvrDBInsertTemp'])
		
	smtpconfig_save = json.dumps(smtpconfig_save)
	smtpconfig_save = str(smtpconfig_save)
	smtpconfig_save_json=json.loads(smtpconfig_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveSmtpConfig(smtpconfig_save)
			sql="select public.\"PSaveSmsSvrConfig\"(E'%s');" %(MySQLdb.escape_string(smtpconfig_save).decode("utf-8"))
			debug("sql:%s" % sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if smtpconfig_save_json['SmsSvrConfigId']==0:
				oper='创建短信网关配置：%s'%smtpconfig_save_json['SmsSvrConfigName']
			else:
				oper='编辑短信网关配置：%s'%smtpconfig_save_json['SmsSvrConfigName']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				conn.commit()
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#创建 or 编辑短信猫
@pwd_manage.route('/add_smsmconfig',methods=['GET','POST'])
def add_smsmconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	smtpconfig_save = request.form.get('a1')
	module_name=request.form.get('a10')
	md5_str=request.form.get('m1')
	if module_name<0:
		module_name='系统管理>输出设置'
	if sess<0:
		sess=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(smtpconfig_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"				
	smtpconfig_save = str(smtpconfig_save)
	smtpconfig_save_json=json.loads(smtpconfig_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveSmsMConfig(smtpconfig_save)
			sql="select public.\"PSaveSmsMConfig\"(E'%s');" %(MySQLdb.escape_string(smtpconfig_save).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if smtpconfig_save_json['SmsMConfigId']==0:
				oper='创建短信猫配置：%s'%smtpconfig_save_json['SmsMConfigName']
			else:
				oper='编辑短信猫配置：%s'%smtpconfig_save_json['SmsMConfigName']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				conn.commit()
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索短信猫
@pwd_manage.route('/get_smsmconfig',methods=['GET', 'POST'])
def get_smsmconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	smsmconfigid = request.form.get('a1')
	if smsmconfigid<0 or smsmconfigid=="0" or smsmconfigid=="":
		smsmconfigid="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetSmsMConfig(smsmconfigid,limitrow,offsetrow)
			sql="select public.\"PGetSmsMConfig\"(%s,%s,%s);"%(smsmconfigid,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#创建 or 编辑SYSLOG
@pwd_manage.route('/add_syslogconfig',methods=['GET','POST'])
def add_syslogconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	smtpconfig_save = request.form.get('a1')
	module_name = request.form.get('a10')
	md5_str=request.form.get('m1')
	if module_name<0:
		module_name='系统管理>输出设置'
	if sess<0:
		sess=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(smtpconfig_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"			
	smtpconfig_save = str(smtpconfig_save)
	smtpconfig_save_json=json.loads(smtpconfig_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveSyslogConfig(smtpconfig_save)
			sql="select public.\"PSaveSyslogConfig\"(E'%s');" %(MySQLdb.escape_string(smtpconfig_save).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if smtpconfig_save_json['SyslogConfigId']==0:
				oper='创建SYSLOG配置：%s'%smtpconfig_save_json['SyslogConfigName']
			else:
				oper='编辑SYSLOG配置：%s'%smtpconfig_save_json['SyslogConfigName']
			if result_json['Result']:
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			else:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索SYSLOG
@pwd_manage.route('/get_syslogconfig',methods=['GET', 'POST'])
def get_syslogconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	syslogconfigid = request.form.get('a1')
	if syslogconfigid<0 or syslogconfigid=="0" or syslogconfigid=="":
		syslogconfigid="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetSyslogConfig(syslogconfigid,limitrow,offsetrow)
			sql="select public.\"PGetSyslogConfig\"(%s,%s,%s);"%(syslogconfigid,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#创建 or 编辑SNMP
@pwd_manage.route('/add_snmpconfig',methods=['GET','POST'])
def add_snmpconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	smtpconfig_save = request.form.get('a1')
	module_name = request.form.get('a10')
	md5_str=request.form.get('m1')	
	if module_name<0:
		module_name='系统管理>输出设置'
	if sess<0:
		sess=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(smtpconfig_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"				
	smtpconfig_save = str(smtpconfig_save)
	smtpconfig_save_json=json.loads(smtpconfig_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveSnmpConfig(smtpconfig_save)
			sql="select public.\"PSaveSnmpConfig\"(E'%s');" %(MySQLdb.escape_string(smtpconfig_save).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if smtpconfig_save_json['SnmpConfigId']==0:
				oper='创建SNMP配置：%s'%smtpconfig_save_json['SnmpConfigName']
			else:
				oper='编辑SNMP配置：%s'%smtpconfig_save_json['SnmpConfigName']
			if result_json['Result']:
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			else:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索SNMP
@pwd_manage.route('/get_snmpconfig',methods=['GET', 'POST'])
def get_snmpconfig():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	snmpconfigid = request.form.get('a1')
	if snmpconfigid<0 or snmpconfigid=="0" or snmpconfigid=="":
		snmpconfigid="null"
	if sess < 0:
		sess = ""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetSnmpConfig(snmpconfigid,limitrow,offsetrow)
			sql="select public.\"PGetSnmpConfig\"(%s,%s,%s);"%(snmpconfigid,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#创建 or 编辑add_pwdmod
@pwd_manage.route('/add_pwdmod',methods=['GET','POST'])
def add_pwdmod():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	pwdmod = request.form.get('a1')
	md5_str=request.form.get('m1')
	if sess<0:
		sess=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(pwdmod);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"				
	pwdmod = json.loads(pwdmod)
	if(pwdmod['Password'] != "" and pwdmod['Password']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(pwdmod['Password'],pwd_rc4);#执行函数
		pwdmod['Password'] = pwd_rc4.value #获取变量的值
	pwdmod = json.dumps(pwdmod)
	pwdmod=str(pwdmod)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSavePwdModStrategy(pwdmod)
			sql="select public.\"PSavePwdModStrategy\"(E'%s');" %(MySQLdb.escape_string(pwdmod).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			conn.commit()
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#创建 or 编辑 add_pwdauth
@pwd_manage.route('/add_pwdauth',methods=['GET','POST'])
def add_pwdauth():
	debug('========add_pwdauth=======')
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	pwdauth_save = request.form.get('a1')
	md5_str=request.form.get('m1')
	if sess<0:
		sess=""
	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(pwdauth_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"			
	pwdauth_save=str(pwdauth_save)
	pwdauth_save = json.loads(pwdauth_save)
	if pwdauth_save['PwdModPlanId']>0:
		_type_name='编辑'
	else:
		_type_name='创建'
	if pwdauth_save['PwdModType']==1:
		type_plan='自动改密'
	else:
		type_plan='手动改密'
	
	if(pwdauth_save['PwdModStrategyInfo']['Password'] != "" and pwdauth_save['PwdModStrategyInfo']['Password']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(pwdauth_save['PwdModStrategyInfo']['Password'],pwd_rc4);#执行函数
		pwdauth_save['PwdModStrategyInfo']['Password'] = pwd_rc4.value #获取变量的值
	pwdauth_save = json.dumps(pwdauth_save)
	pwdauth_save=str(pwdauth_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSavePwdModPlan(pwdauth_save)
			sql="select public.\"PSavePwdModPlan\"(E'%s');" %(MySQLdb.escape_string(pwdauth_save).decode("utf-8"))
			#return false;
			debug(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			conn.commit()
			results_json=json.loads(result)
			debug(result)
			if not results_json['Result']:
				pwdauth_save = json.loads(pwdauth_save)
				if not system_log(system_user,'%s改密计划：%s'%(_type_name,pwdauth_save['PwdModPlanName']),results_json['ErrMsg'],'密码管理>%s'%type_plan):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				if pwdauth_save['PwdModStrategyInfo']['IsModified']:
					if pwdauth_save['PwdModStrategyInfo']['PwdModStrategyId']==0:
						oper='创建'
					else:
						oper='编辑'
					debug(oper)
					if pwdauth_save['PwdModStrategyInfo']['Type']==1:
						oper=oper+'共有改密策略：'+pwdauth_save['PwdModStrategyInfo']['PwdModStrategyName']
					else:
						oper=oper+'私有改密策略'
					if not system_log(system_user,oper,'保存计划失败','密码管理>%s'%type_plan):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			else:
				pwdauth_save = json.loads(pwdauth_save)
				sql1="select public.\"PGetPwdModPlan\"(%s,null,null,null,null,null);" %(results_json['PwdModPlanId'])
				curs.execute(sql1)
				debug('2')
				results = curs.fetchall()[0][0]
				results_json_1=json.loads(results)
				pwd_get_json=results_json_1['data'][0]
				oper='%s改密计划：%s（'%(_type_name,pwd_get_json['PwdModPlanName'])
				debug('3')
				if not ('#' in pwd_get_json['PwdModStrategyInfo']['PwdModStrategyName']):
					oper=oper+'改密策略：%s，'%(pwd_get_json['PwdModStrategyInfo']['PwdModStrategyName'])
				else:
					oper=oper+'改密策略：#私有，'
				if pwd_get_json['IsSendPrePwdFile']:
					oper=oper+'发送预备改密文件，'
				else:
					oper=oper+'不发送预备改密文件，'
				if pwd_get_json['AuthMode']==1:
					oper=oper+'方式：按目标-指定账号，'
					if pwd_get_json['HostSet']!=None:
						oper=oper+'指定主机/主机组：'
						i_num=0
						for i in pwd_get_json['HostSet']:
							i_num+=1
							if i_num>1000:
								break	
							if i['HostId']==None:
								oper=oper+'[%s]、'%(i['HGName'])
							else:
								oper=oper+'[%s]-%s、'%(i['HGName'],i['HostName'])
						oper=oper[:-1]+'，'
					if pwd_get_json['PasswordAuthSet']!=None:
						oper=oper+'指定账号：'
						i_num=0
						for i in pwd_get_json['PasswordAuthSet']:
							i_num+=1
							if i_num>1000:
								break
							if i['AccountName']!=None:
								oper=oper+'[%s]-%s-%s、'%(i['HGName'],i['HostName'],i['AccountName'])
						oper=oper[:-1]+'，'
				else:
					if pwd_get_json['AuthMode']==2:
						oper=oper+'方式：按范围-共有账号，'
					elif pwd_get_json['AuthMode']==4:
						oper=oper+'方式：按范围-自定义，'
					else:
						oper=oper+'方式：按范围-所有账号，'
					if pwd_get_json['AuthScope']!=None:
						oper=oper+'服务器范围：'
						for i in pwd_get_json['AuthScope']:
							oper=oper+'%s、'%(i['ServerScopeName'])
						oper=oper[:-1]+'，'
					if pwd_get_json['AuthAccountId']!=None:
						if pwd_get_json['AuthAccountId']!='*':
							oper=oper+'账号：'
							AuthAccountId_arr=pwd_get_json['AuthAccountId'].replace(',eck_all_a','').split(',')
							i_num=0
							for i in AuthAccountId_arr:
								i_num+=1
								if i_num>1000:
									break
								sql_acc="select acc.\"Name\" from public.\"Account\" acc where acc.\"AccountId\"=%s" %(i)
								curs.execute(sql_acc)
								results_acc = curs.fetchall()[0][0]
								if results_acc=='*':
									results_acc='任意账号'
								elif results_acc=='-':
									results_acc='空账号'
								oper=oper+'%s、'%(results_acc)
							oper=oper[:-1]+'，'
						else:
							oper=oper+'账号：所有账号，'
					if pwd_get_json['AuthServiceSet']!=None:
						if pwd_get_json['AuthService']!='*':
							oper=oper+'服务：'
							i_num=0
							for i in pwd_get_json['AuthServiceSet']:
								i_num+=1
								if i_num>1000:
									break
								oper=oper+'%s-%s、'%(i['ProtocolName'],i['Port'])
							oper=oper[:-1]+'，'
						else:
							oper=oper+'服务：所有服务，'
					else:
						if pwd_get_json['AuthService']=='*':
							oper=oper+'服务：所有服务，'
				oper=oper[:-1]+'）'
				if not system_log(system_user,oper,'成功','密码管理>%s'%type_plan):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				debug(str(pwdauth_save))
				if pwdauth_save['PwdModStrategyInfo']['IsModified']:
					if pwdauth_save['PwdModStrategyInfo']['PwdModStrategyId']==0:
						oper='创建'
					else:
						oper='编辑'
					debug(oper)
					if pwdauth_save['PwdModStrategyInfo']['Type']==1:
						oper=oper+'共有改密策略：'+pwdauth_save['PwdModStrategyInfo']['PwdModStrategyName']
					else:
						oper=oper+'私有改密策略'
					oper=oper+'（'
					debug(oper)
					if pwdauth_save['PwdModType']==1:
						if pwdauth_save['PwdModStrategyInfo']['PeriodType']==1:
							PeriodType_value='天'
						else:
							PeriodType_value='分钟'
						oper=oper+'开始时间：%s，重复周期：%s%s，'%(pwdauth_save['PwdModStrategyInfo']['StartTime'].replace('T',' '),pwdauth_save['PwdModStrategyInfo']['PeriodValue'],PeriodType_value)
					debug(oper)
					if pwdauth_save['PwdModStrategyInfo']['PasswordType']==1:
						oper=oper+'密码策略：随机生成不同密码，'
					elif pwdauth_save['PwdModStrategyInfo']['PasswordType']==2:
						oper=oper+'密码策略：随机生成相同密码，'
					else:
						oper=oper+'密码策略：人工指定相同密码，'
					debug(oper)
					if pwdauth_save['PwdModStrategyInfo']['ResultSendMethod']==3:
						oper=oper+'发送方式：默认'
					elif pwdauth_save['PwdModStrategyInfo']['ResultSendMethod']==1:
						ReceiverSet_arr=''
						for i in pwdauth_save['PwdModStrategyInfo']['ReceiverSet']:
							ReceiverSet_arr=ReceiverSet_arr+i['Name']+'、'
						ReceiverSet_arr=ReceiverSet_arr[:-1]
						oper=oper+'发送方式：邮件，默认：%s，备用：%s，接受者：%s'%(pwdauth_save['PwdModStrategyInfo']['MasterSmtpConfigName'],pwdauth_save['PwdModStrategyInfo']['StandBySmtpConfigName'],ReceiverSet_arr)
					elif pwdauth_save['PwdModStrategyInfo']['ResultSendMethod']==2:
						oper=oper+'发送方式：FTP，默认：%s，备用：%s'%(pwdauth_save['PwdModStrategyInfo']['MasterFTPServerName'],pwdauth_save['PwdModStrategyInfo']['StandByFTPServerName'])
					else:
						oper=oper+'发送方式：无'
					oper=oper+'）'
					debug(oper)
					if not system_log(system_user,oper,'成功','密码管理>%s'%type_plan):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				debug(oper)
			##[global]
			#class=taskupdatehnodeselected
			#type=update_run
			#id_type=id_type
			#id=id
			task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=6\nid=%s\n' % (results_json["PwdModPlanId"])
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#创建自动改密
@pwd_manage.route('/add_pwdauth_new',methods=['GET','POST'])
def add_pwdauth_new():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	pwdauth_save = request.form.get('a1')
	md5_str=request.form.get('m1')
	if sess<0:
		sess=""
	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问(%d)\"}" %(sys._getframe().f_lineno)
	else:
		md5_json = StrMD5(pwdauth_save);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问(%d)\"}"	%(sys._getframe().f_lineno)		
	pwdauth_save=str(pwdauth_save)
	pwdauth_save = json.loads(pwdauth_save)
	
	if(pwdauth_save['Password'] != "" and pwdauth_save['Password']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(pwdauth_save['Password'],pwd_rc4);#执行函数
		pwdauth_save['Password'] = pwd_rc4.value #获取变量的值
	pwdauth_save = json.dumps(pwdauth_save)
	pwdauth_save=str(pwdauth_save)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PSavePwdModTask\"(E'%s');" %(MySQLdb.escape_string(pwdauth_save).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#取自动改密账号状态
@pwd_manage.route('/get_AccStatus',methods=['GET','POST'])
def get_AccStatus():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	AccountData = request.form.get('a1')
	if sess<0:
		sess=""
	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPwdModTaskDetailSet\"(E'%s');" %(MySQLdb.escape_string(AccountData).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#显示密码托管 or 分页 or 搜索
@pwd_manage.route('/get_pwdauth_list',methods=['GET', 'POST'])
def get_pwdauth_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	passwordauthid = request.form.get('a1')
	loginusercode = request.form.get('a5')
	pwdmodtype=request.form.get('a6')
	if passwordauthid<0 or passwordauthid=="" or passwordauthid=="0":
		passwordauthid="null"
	if pwdmodtype<0:
		pwdmodtype=1
	if sess < 0:
		sess = ""
	
	if search_typeall<0:
		search_typeall=""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if loginusercode < 0 or loginusercode=='':
		loginusercode = "null"
	else:
		loginusercode="'%s'" % system_user
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	pwdmodplanname = ""
	searchstring = ""
	Status = ""
	ReviewStatus = ""
	PwdModStrategyName = ""
	InvalidLog = ""
	Enabled = ""
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="PwdModPlanName":
			pwdmodplanname=pwdmodplanname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			#pwdmodplanname=pwdmodplanname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Status":
			Status=Status+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ReviewStatus":
			ReviewStatus=ReviewStatus+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="PwdModStrategyName":
			PwdModStrategyName=PwdModStrategyName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="InvalidLog":
			InvalidLog=InvalidLog+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Enabled":
			Enabled=Enabled+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if pwdmodplanname=="":
		pwdmodplanname="null"
	else:
		pwdmodplanname="E'%s'"%pwdmodplanname[:-1]
	if searchstring!="":
		searchstring=searchstring[:-1]
	if ReviewStatus!="":
                ReviewStatus=ReviewStatus[:-1]
		if ReviewStatus=='无需审核':
			ReviewStatus=0
		elif ReviewStatus=='需要审核':
			ReviewStatus=1
		elif ReviewStatus=='审核通过':
			ReviewStatus=2
		elif ReviewStatus=='审核不通过':
			ReviewStatus=3
		elif ReviewStatus=='所有':
			ReviewStatus=None
	else:
		ReviewStatus=None
	if Status!="":
		Status=Status[:-1]
		if Status=='准备执行':
			Status=0
		elif Status=='生成预备密码':
			Status=1
		elif Status=='生成密码完成，待发送':
			Status=2
		elif Status=='发送预备密码文件完成，待确认':
			Status=3
		elif Status=='确认预备密码文件':
			Status=4
		elif Status=='执行改密':
			Status=5
		elif Status=='执行完成':
			Status=6
		elif Status=='发送改密文件完成，待确认':
			Status=7
		elif Status=='确认':
			Status=8
		elif Status=='任务失败':
			Status=9
		elif Status=='正在审核':
			Status=1
			ReviewStatus=1
		elif Status=='所有':
			Status=None
	else:
		Status=None
	if PwdModStrategyName!="":
		PwdModStrategyName=PwdModStrategyName[:-1]
	if InvalidLog!="":
		InvalidLog=InvalidLog[:-1]
	if Enabled!="":
		Enabled=Enabled[:-1]
		if Enabled=='启用':
			Enabled=True
		elif Enabled=='停用':
			Enabled=False
		elif Enabled=='所有':
			Enabled=None	
	else:
		Enabled=None
	searchconn={}
	searchconn['searchstring']=searchstring
	searchconn['Status']=Status
	searchconn['ReviewStatus']=ReviewStatus
	searchconn['PwdModStrategyName']=PwdModStrategyName
	searchconn['InvalidLog']=InvalidLog
	searchconn['Enabled']=Enabled
	searchconn['LoginUserCode']=system_user
	searchconn=json.dumps(searchconn)
	pwdmodplanname=pwdmodplanname.replace("\\\\","\\\\\\\\")
	pwdmodplanname=pwdmodplanname.replace(".","\\\\.")
	pwdmodplanname=pwdmodplanname.replace("?","\\\\?")
	pwdmodplanname=pwdmodplanname.replace("+","\\\\+")
	pwdmodplanname=pwdmodplanname.replace("(","\\\\(")
	pwdmodplanname=pwdmodplanname.replace("*","\\\\*")
	pwdmodplanname=pwdmodplanname.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPwdModPlan\"(%s,%s,%s,%s,%s,%s,E'%s');"% (passwordauthid,pwdmodplanname,loginusercode,pwdmodtype,num,paging,searchconn)
			debug("aaa"+sql)
			#sql="select public.\"PGetPwdModPlan\"(%s,%s,%s,%s,%s,%s);"% (passwordauthid,pwdmodplanname,loginusercode,pwdmodtype,num,paging)\
			#debug("bbb"+sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
@pwd_manage.route('/PGetPwdModPlanByName',methods=['GET','POST'])
def PGetPwdModPlanByName():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	name = request.form.get('a1')
	if sess <0:
		sess=""
	if name <0:
		name=""
	else:
		name="E'%s'" % (name)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetPwdModPlanByName(name)
			sql="select public.\"PGetPwdModPlanByName\"(%s);"%(name)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#获得主机信息
@pwd_manage.route('/get_host',methods=['GET', 'POST'])
def get_host():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	nohostservice = request.form.get('a2')
	hostid = request.form.get('a1')
	if hostid<0 or hostid=="0" or hostid=="":
		hostid="null"
	if sess < 0:
		sess = ""
	if nohostservice <0:
		nohostservice = "false"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetHost(hostid,nohostservice)
			sql="select public.\"PGetHost\"(%s,%s,'%s');"%(hostid,nohostservice,system_user)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@pwd_manage.route('/pwd_auth_start_plan',methods=['GET','POST'])
def pwd_auth_start_plan():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	pwdauthid = request.form.get('a1')
	plan_name=request.form.get('a2')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sql='UPDATE "public"."PwdModPlan" SET "Enabled"=TRUE ,"Status"=0,"InvalidLog"=null WHERE "PwdModPlanId"=%s'% pwdauthid
			curs.execute(sql)
			conn.commit()
			if not system_log(system_user,'启用改密计划：%s'%(plan_name),'成功','密码管理>自动改密'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	

@pwd_manage.route('/pwd_auth_stop_plan',methods=['GET','POST'])
def pwd_auth_stop_plan():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	pwdauthid = request.form.get('a1')
	plan_name=request.form.get('a2')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sql='UPDATE "public"."PwdModPlan" SET "Enabled"=FALSE ,"InvalidLog"=null WHERE "PwdModPlanId"=%s'% pwdauthid
			curs.execute(sql)
			conn.commit()
			if not system_log(system_user,'停用改密计划：%s'%(plan_name),'成功','密码管理>自动改密'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@pwd_manage.route('/pwd_auth_cancel_plan',methods=['GET','POST'])
def pwd_auth_cancel_plan():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	pwdauthid = request.form.get('a1')
	plan_name=request.form.get('a2')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sql="select public.\"PCancelPwdModTask\"(%s);"% (pwdauthid)
			curs.execute(sql)
			conn.commit()
			if not system_log(system_user,'取消改密计划：%s'%(plan_name),'成功','密码管理>自动改密'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#显示密码任务 or 分页 or 搜索
@pwd_manage.route('/get_pwdmodtask_list',methods=['GET', 'POST'])
def get_pwdmodtask_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	passwordauthid = request.form.get('a1')
	pwdmodtype=request.form.get('a6')
	if passwordauthid<0 or passwordauthid=="" or passwordauthid=="0":
		passwordauthid="null"
	if pwdmodtype<0:
		pwdmodtype=1
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	searchstring=''
	pwdmodplanname = ""
	starttime=''
	endtime=''
	ReviewStatus=''
	Status=''
	FailMsg=''
	ExecuteUserName=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="pwdmodplanname":
			pwdmodplanname=pwdmodplanname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			#pwdmodplanname=pwdmodplanname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ReviewStatus":
			ReviewStatus=ReviewStatus+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Status":
			Status=Status+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ExecuteUserName":
			ExecuteUserName=ExecuteUserName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="FailMsg":
			FailMsg=FailMsg+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if pwdmodplanname=="":
		pwdmodplanname="null"
	else:
		pwdmodplanname="E'%s'"%pwdmodplanname[:-1]
	if starttime=="":
		starttime="null"
	else:
		starttime="'%s'"%starttime[:-1]
	if endtime=="":
		endtime="null"
	else:
		endtime="E'%s'"%endtime[:-1]
	if searchstring!="":
		searchstring=searchstring[:-1]
	if ReviewStatus!="":
		ReviewStatus=ReviewStatus[:-1]
		if ReviewStatus=='无需审核':
			ReviewStatus=0
		elif ReviewStatus=='需要审核':
			ReviewStatus=1
		elif ReviewStatus=='审核通过':
			ReviewStatus=2
		elif ReviewStatus=='审核不通过':
			ReviewStatus=3
		elif ReviewStatus=='所有':
			ReviewStatus=None
	else:
		ReviewStatus=None
	if Status!="":
		Status=Status[:-1]
		if Status=='准备执行':
			Status=0
		elif Status=='生成预备密码':
			Status=1
		elif Status=='正在审核':
			Status=1
			ReviewStatus=1
		elif Status=='生成密码完成，待发送':
			Status=2
		elif Status=='发送预备密码文件完成，待确认':
			Status=3
		elif Status=='确认预备密码文件':
			Status=4
		elif Status=='执行改密':
			Status=5
		elif Status=='执行完成':
			Status=6
		elif Status=='发送改密文件完成，待确认':
			Status=7
		elif Status=='确认':
			Status=8
		elif Status=='任务失败':
			Status=9
		elif Status=='所有':
			Status=None
	else:
		Status=None
	if ExecuteUserName!="":
		ExecuteUserName=ExecuteUserName[:-1]	
	else:
		ExecuteUserName=None
	if FailMsg!="":
		FailMsg=FailMsg[:-1]
	else:
		FailMsg=None
	searchconn={}
	searchconn['searchstring']=searchstring
	searchconn['ReviewStatus']=ReviewStatus
	searchconn['Status']=Status
	searchconn['ExecuteUserCode']=ExecuteUserName
	searchconn['FailMsg']=FailMsg
	searchconn=json.dumps(searchconn)
	pwdmodplanname=pwdmodplanname.replace("\\\\","\\\\\\\\")
	pwdmodplanname=pwdmodplanname.replace(".","\\\\.")
	pwdmodplanname=pwdmodplanname.replace("?","\\\\?")
	pwdmodplanname=pwdmodplanname.replace("+","\\\\+")
	pwdmodplanname=pwdmodplanname.replace("(","\\\\(")
	pwdmodplanname=pwdmodplanname.replace("*","\\\\*")
	pwdmodplanname=pwdmodplanname.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sql="select public.\"PGetPwdModTask\"(%s,%s,'%s',%s,%s,%s,%s,%s,E'%s');"% (passwordauthid,pwdmodplanname,system_user,pwdmodtype,starttime,endtime,num,paging,searchconn)
			#sql="select public.\"PGetPwdModTask\"(%s,%s,'%s',%s,%s,%s,%s,%s);"% (passwordauthid,pwdmodplanname,system_user,pwdmodtype,starttime,endtime,num,paging)
			debug("select name"+sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#查询策略是否被其他计划使用
@pwd_manage.route('/find_mod_to_other_pwdauth',methods=['GET','POST'])
def find_mod_to_other_pwdauth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_pwdauth = request.form.get('a1')
	id_pwdmod=request.form.get('a2')
	session = request.form.get('a0')
	if session <0 :
		sesson=""
	if id_pwdauth <0 :
		id_pwdauth=""
	if id_pwdmod <0 :
		id_pwdmod=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PDeletePwdModStrategy(id)
			sql = "select count(*) from public.\"PwdModPlan\" where \"PwdModPlanId\"!=%s and \"PwdModStrategyId\"=%s;" % (id_pwdauth,id_pwdmod)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"num\":%s}"%(results)  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除改密策略
@pwd_manage.route('/del_pwdmod',methods=['GET', 'POST'])
def del_pwdmod():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	type_name=request.form.get('a2')
	if session <0 :
		session=""
	if id_str <0 :
		id_str=""
	if type_name<0:
		type_name='密码管理>自动改密'
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql1='select a."PwdModStrategyName" from public."PwdModStrategy" a where a."PwdModStrategyId"=%s;'%(id_str)
			curs.execute(sql1)
			result1 = curs.fetchall()[0][0]
			# PDeletePwdModStrategy(id)
			sql = "select public.\"PDeletePwdModStrategy\"(%s);" % (id_str)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if "false" in results:
				if not system_log(system_user,'删除改密策略：%s'%(result1),'参数错误',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				conn.commit()
				if not system_log(system_user,'删除改密策略：%s'%(result1),'成功',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#删除del_pwdtask
@pwd_manage.route('/del_pwdtask',methods=['GET', 'POST'])
def del_pwdtask():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	type_name=request.form.get('a2')
	if type_name==None or type_name<0 or type_name=='1':
		type_name='自动改密'
	else:
		type_name='手动改密'
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		sys.exit()
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			for id in ids:
				id=int(id)
				sql1='select a."PwdModPlanName" from private."PwdModTask" a where a."PwdModTaskId"=%s;'%(id)
				curs.execute(sql1)
				result1 = curs.fetchall()[0][0]
				# PDeletePwdModTask(pwdmodplanid)
				sql = "select public.\"PDeletePwdModTask\"(%d);" % (id)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				if "false" in result:
					if not system_log(system_user,'删除改密任务：%s'%(result1),'参数错误','密码管理>%s'%type_name):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					fail_num+=1
				else:
					conn.commit()
					if not system_log(system_user,'删除改密任务：%s'%(result1),'成功','密码管理>%s'%type_name):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					success_num+=1
			return "{\"Result\":true,\"success_num\":%d,\"fail_num\":%d}"%(success_num,fail_num)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
