#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
import pyodbc
import pyodbc
import ConfigParser
import MySQLdb
import json
import time

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import task_client
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from logbase import defines
from ctypes import *
from urllib import unquote
from generating_log import system_log
from comm_function import get_user_perm_value
from htmlencode import parse_sess,check_role
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
hostpwdstrategy_change = Blueprint('hostpwdstrategy_change',__name__)

SIZE_PAGE = 20
def debug(c):
	return 0
    	path = "/var/tmp/debug_hostpwd.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
# def sendlog(oper,desc,cname):
	# client_ip = request.remote_addr    #获取客户端IP
	# happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	# sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	# LogSet(None, sqlconf, 6)
	
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
#跳转至密码策略
@hostpwdstrategy_change.route('/hostpwdstrategy_show',methods=['GET','POST'])
def hostpwdstrategy_show():
	sess=request.form.get('se')
	us=request.form.get('us')
	if sess<0:
		sess=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==31 and i['SystemMenuId']==4:
			perm=i['Mode']
			break
	return render_template('hostpwdstrategy_change.html',se=sess,a=0,us=us,perm=perm)

#get_global_IfPwdApprove
@hostpwdstrategy_change.route('/get_global_IfPwdApprove',methods=['GET','POST'])
def get_global_IfPwdApprove():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetHostPwdStrategy(usercode)
			sql = "SELECT row_to_json(r)::jsonb FROM(\n\
			SELECT gs.\"PwdApproveNum\",gs.\"PwdFileApproveNum\"\n\
			FROM \"GlobalStrategy\" gs) as r\n"
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#add_global_IfPwdApprove
@hostpwdstrategy_change.route('/add_global_IfPwdApprove',methods=['GET','POST'])
def add_global_IfPwdApprove():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	IfPwdApprove=request.form.get('a1')
	IfPwdFileApprove=request.form.get('a2')
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
	
	if check_role(system_user,'31') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if IfPwdApprove.isdigit() and IfPwdFileApprove.isdigit():
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	
	#UPDATE "GlobalStrategy" SET "IfPwdApprove"=false
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetHostPwdStrategy(usercode)
			sql = "UPDATE \"GlobalStrategy\" SET \"PwdApproveNum\"=%s,\"PwdFileApproveNum\"=%s;"%(IfPwdApprove,IfPwdFileApprove)
			curs.execute(sql)
			if IfPwdApprove!='0':
				oper_IfPwdApprove='改密审批：启用，审批人数：%s'%(IfPwdApprove)
			else:
				oper_IfPwdApprove='改密审批：停用'
			if IfPwdFileApprove!='0':
				oper_IfPwdFileApprove='下载审批：启用，审批人数：%s'%(IfPwdFileApprove)
			else:
				oper_IfPwdFileApprove='下载审批：停用'
			oper='编辑改密全局策略（%s，%s）'%(oper_IfPwdApprove,oper_IfPwdFileApprove)
			if not system_log(system_user,oper,'成功','密码管理>全局策略'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			conn.commit()
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#获取
@hostpwdstrategy_change.route('/get_hostpwdstrategy',methods=['GET','POST'])
def get_hostpwdstrategy():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetHostPwdStrategy(usercode)
			sql = "select public.\"PGetHostPwdStrategy\"(E'%s');"%(system_user)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results==None:
				results='null'
			else:
				results = json.loads(results)
				if results['Password']!='' and results['Password']!=None:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					ret = lib.decrypt_pwd(results['Password'],pwd_rc4);#执行函数
					results['Password'] = pwd_rc4.value #获取变量的值
				results = json.dumps(results)
				results = str(results)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
@hostpwdstrategy_change.route('/add_hostpwdstrategy',methods=['GET','POST'])
def add_hostpwdstrategy():
	debug('---------add_hostpwdstrategy--------')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	hostpwd = request.form.get('a1')
	type_name=request.form.get('a2')
	md5_str=request.form.get('m1')
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
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(hostpwd);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	hostpwd = json.loads(hostpwd)
	if type_name<0 or type_name==None or type_name=='1':
		oper_fail='编辑密码策略'
	else:
		oper_fail='编辑发送策略'

	debug('3')
	hostpwd['UserCode']=system_user
	if(hostpwd['Password'] != "" and hostpwd['Password']!=None):
		if os.path.exists('/usr/lib64/logproxy.so') == False:
				return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(hostpwd['Password'],pwd_rc4);#执行函数
		hostpwd['Password'] = pwd_rc4.value #获取变量的值
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveHostPwdStrategy(jsondata)
			# {"Result":true,"RowCount":1}
			sql="select public.\"PSaveHostPwdStrategy\"(E'%s')" %(MySQLdb.escape_string(str(json.dumps(hostpwd))).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if 'false' in result:
				if not system_log(system_user,oper_fail,'用户账号不存在','密码管理>改密设定'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			conn.commit()
			if type_name<0 or type_name==None or type_name=='1':
				if hostpwd['IfPwdComplex']:
					IfPwdComplex_str='密码复杂度要求：启用，小写字母：%s，大写字母：%s，数字：%s，特殊字符：%s'%(hostpwd['PwdIncLowerAphaCount'],hostpwd['PwdIncUpperAphaCount'],hostpwd['PwdIncNumberCount'],hostpwd['PwdIncSpecialCharCount'])
				else:
					IfPwdComplex_str='密码复杂度要求：停用'
				debug('3-1')
				if hostpwd['IfPwdUnRepeat']:
					IfPwdUnRepeat_str='密码安全策略：启用，单字符使用最大次数：%s，不出现在旧密码中的字符最小数：%s'%(hostpwd['CharRepeatCount'],hostpwd['UnRepeatCharCount'])
				else:
					IfPwdUnRepeat_str='密码安全策略：停用'
				debug('3-2')
				if hostpwd['PwdApproveNum']>0:
					PwdApproveNum=[]
					for i in hostpwd['PwdApproveUserSet']:
						PwdApproveNum.append(i['UserCode'])
					IfPwdApprove_str='改密审批：启用，审批管理员：%s'%('，'.join(PwdApproveNum))
				else:
					IfPwdApprove_str='改密审批：停用'
				if hostpwd['PwdFileApproveNum']>0:
					PwdFileApproveNum=[]
					for i in hostpwd['PwdFileApproveUserSet']:
						PwdFileApproveNum.append(i['UserCode'])
					IfPwdFileApprove_str='下载审批：启用，审批管理员：%s'%('，'.join(PwdFileApproveNum))
				else:
					IfPwdFileApprove_str='下载审批：停用'
				debug('3-3')
				oper=oper_fail+'（密码最小长度：%s，%s，%s，%s,%s）'%(hostpwd['PwdMinLen'],IfPwdComplex_str,IfPwdUnRepeat_str,IfPwdApprove_str,IfPwdFileApprove_str)
				debug('3-4')
			else:
				sql_r="select public.\"PGetHostPwdStrategy\"(E'%s');"%(system_user)
				debug(sql_r)
				curs.execute(sql_r)
				result_r = curs.fetchall()[0][0]
				result_r_json=json.loads(result_r)
				debug(result_r)
				if result_r_json['SendMethod']==1:
					if result_r_json['MasterSmtpConfig']==None:
						result_r_json['MasterSmtpConfig']={}
						result_r_json['MasterSmtpConfig']['SmtpConfigName']='全局指定'
					elif result_r_json['MasterSmtpConfig']['SmtpConfigName']=='':
						result_r_json['MasterSmtpConfig']['SmtpConfigName']='全局指定'
					if result_r_json['StandBySmtpConfig']==None:
						result_r_json['StandBySmtpConfig']={}
						result_r_json['StandBySmtpConfig']['SmtpConfigName']='全局指定'
					elif result_r_json['StandBySmtpConfig']['SmtpConfigName']=='':
						result_r_json['StandBySmtpConfig']['SmtpConfigName']='全局指定'
					ReceiverSet_str=''
					debug('1')
					if result_r_json['ReceiverSet']!=None:
						ReceiverSet_str='，接收者：'
						for i in result_r_json['ReceiverSet']:
							ReceiverSet_str=ReceiverSet_str+'%s、'%(i['Name'])
						ReceiverSet_str=ReceiverSet_str[:-1]
					debug('1-2')
					oper=oper_fail+'（'+'发送方式：邮件，默认：%s，备用：%s%s）'%(result_r_json['MasterSmtpConfig']['SmtpConfigName'],result_r_json['StandBySmtpConfig']['SmtpConfigName'],ReceiverSet_str)
				else:
					if result_r_json['MasterFTPServer']==None:
						result_r_json['MasterFTPServer']={}
						result_r_json['MasterFTPServer']['FTPServerName']='全局指定'
					elif result_r_json['MasterFTPServer']['FTPServerName']=='':
						result_r_json['MasterFTPServer']['FTPServerName']='全局指定'
					if result_r_json['StandByFTPServer']==None:
						result_r_json['StandByFTPServer']={}
						result_r_json['StandByFTPServer']['FTPServerName']='全局指定'
					elif result_r_json['StandByFTPServer']['FTPServerName']=='':
						result_r_json['StandByFTPServer']['FTPServerName']='全局指定'
					ReceiverSet_str=''
					debug('1')
					if result_r_json['ReceiverSet']!=None:
						ReceiverSet_str='，接收者：'
						for i in result_r_json['ReceiverSet']:
							ReceiverSet_str=ReceiverSet_str+'%s、'%(i['Name'])
						ReceiverSet_str=ReceiverSet_str[:-1]
					debug('1-2')
					debug('2')
					oper=oper_fail+'（'+'发送方式：邮件，默认：%s，备用：%s%s）'%(result_r_json['MasterFTPServer']['FTPServerName'],result_r_json['StandByFTPServer']['FTPServerName'],ReceiverSet_str)
			debug('1-3')
			if not system_log(system_user,oper,'成功','密码管理>改密设定'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result  
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

	
