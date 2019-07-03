#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import stat
import re
import thread
import socket
import pyodbc
import MySQLdb
import json
import time
import binascii
import ConfigParser
import random
import smtplib
import signal
from urllib import unquote
from comm import SessionCheck,LogSet,SessionLogin,StrSqlConn,StrMD5
from logbase import common,task_client,defines
from ctypes import *
from struct import pack
from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader 

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from ftplib import FTP
from generating_log import system_log
from comm_function import encrypt_pwd_make_file,decrypt_pwd,e_transmit,f_transmit

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
pwd_export_py = Blueprint('pwd_export_py',__name__)

SIZE_PAGE = 20
EXPORT_PWD='/usr/storage/.system/passwd/expt_%s.%s.pwd'
oper=''
oper_fail=''
mesg=''
module=''
user=''
se=''

def debug(c):
	return 0
	path = "/var/tmp/debug_ccp_pwd_export_list.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
def debuglen(c):
	path = "/var/tmp/debug_ccp_pwd_export_list_len.txt"
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

#获取用户邮箱s
def get_user_email(system_user):
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select a.\"Email\" FROM public.\"User\" a WHERE a.\"UserCode\"='%s';"%(system_user)
			curs.execute(sql)
			email = curs.fetchall()[0][0]
			return (0,email)
	except pyodbc.Error,e:
		return (-1,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno))
#拼接写入内容
def splice_content(json_data):
	json_data= json.loads(json_data)
	str_write=''
	num_i=0
	global oper
	global oper_fail
	global module
	# try:
	oper_success_value=''
	for i in json_data["data"]:
		num_j=0
		debug(str(i))
		if module=='密码导出':
			oper_success_value+=(i["HostName"]+'、')
		for j in i["AccountPassword"]:
			Status=''
			if j.has_key("Status")==True:
				Status=j["Status"]
			if 1==j["PasswordType"]:
				if j["Password"]==None:
					j["Password"]='*'
				elif j["Password"]=='':
					j["Password"]='-'
				else:
					(error,j["Password"])=decrypt_pwd(j["Password"])#获取变量的值
					if error!=0:
						return (error,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno))
			if j.has_key("OldPasswordType")==True:
				if 1==j["OldPasswordType"]:
					if j["OldPassword"]==None:
						j["OldPassword"]='*'
					elif j["OldPassword"]=='':
						j["OldPassword"]='-'
					else:
						(error,j["OldPassword"])=decrypt_pwd(j["OldPassword"])#获取变量的值
						if error!=0:
							return (error,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno))
			if module!='密码导出':
				oper_success_value+=(i['HostName']+'-'+j['AccountName']+'、')
			str_write_item='%s(%s)\t%s(%s)\t%s\t%s\t-\n'%(i["HostName"],i["HostIP"],(j.has_key("AccountType")==False) and j["AccountName"] or ((1==j["AccountType"]) and j["AccountName"] or '-'),j["ProtocolName"],(1==j["PasswordType"] and (((Status!='（登录失败）' and Status!='（改密失败）' and Status!='（确认失败）' and Status!='（域账号已改密）')and j["Password"] or '-')+Status) or ('-'+Status)),(j.has_key("OldPasswordType")==False and '-' or(1==j["OldPasswordType"] and j["OldPassword"] or '-')))
			debug(str_write_item)
			str_write+=str_write_item
	oper_success_value=oper_success_value[:-1]
	if module=='密码导出':
		oper=oper_fail+'（主机：'+oper_success_value+'）'
	else:
		oper=oper_fail+'（账号：'+oper_success_value+'）'
	# except Exception,e:
		# debug(str(e))
	return (0,str_write)

#生成密码文件
def export_pwd_function(json_data,system_user):
	global user
	global oper
	global oper_fail
	global module
	(error,str_write)=splice_content(json_data)
	debug('--------')
	if error!=0:
		return (error,str_write)
	path=EXPORT_PWD%(system_user,se)
	(error,return_value)=encrypt_pwd_make_file(system_user,str_write,path,module)
	if error==0:
		return (0,path)
	else :
		if error==-2:
			if not system_log(user,oper_fail,'文件加密失败','密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return (error,"{\"Result\":false,\"ErrMsg\":\"%s\"}"%(return_value))
		else:
			return (error,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno))
#获取全局设置
def get_hostpwdstrate(system_user):
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetHostPwdStrategy\"('%s');"%(system_user)
			curs.execute(sql)
			hostpwd = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		return (-1,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno))
	return (0,hostpwd)

#获取邮件设置
def get_get_smtp_data():
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetSmtpConfig\"(null,2,0);"
			curs.execute(sql)
			smtp_data = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		return (-1,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno))
	return (0,smtp_data)
#获取FTP设置
def get_get_ftp_data():
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetFTPServer\"(null,null,2,0);"
			curs.execute(sql)
			ftp_data = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		return (-1,"{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno))
	return (0,ftp_data)
#发送函数
def send_function(path,system_user):
	global user
	global oper
	global oper_fail
	global module
	# debug('send_function')
	(error,result)=get_hostpwdstrate(system_user)
	if error!=0:
		return result
	elif result==None:
		if not system_log(user,oper_fail,'未设置发送方式','密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"请设置发送方式\",\"info\":-1}"
	json_data=json.loads(result)
	debug(str(json_data))
	debug('--1--')
	debug(str(json_data['SendMethod']))
	if 1==json_data['SendMethod']:
		(error,_to)=get_user_email(system_user)
		if error!=0:
			return _to
		elif _to==None:
			if not system_log(user,oper_fail,'未设置账号邮箱','密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"请设置账号邮箱\"}"
		(error,smtp_all_data)=get_get_smtp_data()
		debug('smtp_all_data')
		debug(str(smtp_all_data))
		if error!=0:
			return smtp_all_data
		elif smtp_all_data==None:
			if not system_log(user,oper_fail,'未设置邮件服务器','密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"请设置邮件服务器\",\"info\":-1}"
		smtp_all_data=json.loads(smtp_all_data)
		debug('--2--')
		debug(str(json_data['MasterSmtpConfig']))
		if json_data['MasterSmtpConfig']['SmtpConfigId']==0:
			debug('--3--')
			json_data['MasterSmtpConfig']=None
			for i in smtp_all_data['data']:
				debug(str(i))
				if i['Flag']==2:
					json_data['MasterSmtpConfig']=i
					debug(str(i))
					break
		if json_data['StandBySmtpConfig']['SmtpConfigId']==0:
			json_data['StandBySmtpConfig']=None
			for i in smtp_all_data['data']:
				if i['Flag']==1:
					json_data['StandBySmtpConfig']=i
					break
		result="{\"Result\":false,\"ErrMsg\":\"请设置邮件服务器\"}"
		debug('MasterSmtpConfig')
		if json_data['MasterSmtpConfig']!=None:
			_server=json_data['MasterSmtpConfig']['SmtpServer']
			_user=json_data['MasterSmtpConfig']['SenderEmail']
			debug('_pwd')
			if json_data['MasterSmtpConfig']['SenderEmailPass']!='' and json_data['MasterSmtpConfig']['SenderEmailPass']!=None:
				(error,_pwd)=decrypt_pwd(json_data['MasterSmtpConfig']['SenderEmailPass'])
				if error!=0:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno)
			else:
				_pwd=''
			debug(str(json_data['MasterSmtpConfig']))
			debug(path)
			(error,result)=e_transmit(_server,_user,_pwd,_to,path)
		debug('StandBySmtpConfig')
		debug(str(result))
		if error!=0:
			if not system_log(user,oper_fail,'默认%s'%result,'密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			if json_data['StandBySmtpConfig']==None:
				if not system_log(user,oper_fail,'未设置备用邮件服务器','密码管理>%s'%module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"请设置邮件服务器\"}"
			else:
				_server=json_data['StandBySmtpConfig']['SmtpServer']
				_user=json_data['StandBySmtpConfig']['SenderEmail']
				if json_data['StandBySmtpConfig']['SenderEmailPass']!='' and json_data['StandBySmtpConfig']['SenderEmailPass']!=None:
					(error,_pwd)=decrypt_pwd(json_data['StandBySmtpConfig']['SenderEmailPass'])
					if error!=0:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno)
				else:
					_pwd=''
				(error,result)=e_transmit(_server,_user,_pwd,_to,path)
				debug(str(result))
				if error!=0:
					if not system_log(user,oper_fail,'备用%s'%result,'密码管理>%s'%module):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"%s\"}"%result
				if not system_log(user,oper,'成功','密码管理>%s'%module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":true,\"info\":\"密码文件发送成功（备用邮件配置）\"}"
		if not system_log(user,oper,'成功','密码管理>%s'%module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":true,\"info\":\"密码文件发送成功（默认邮件配置）\"}"
	elif 2==json_data['SendMethod']:
		(error,ftp_all_data)=get_get_ftp_data()
		if error!=0:
			return ftp_all_data
		elif ftp_all_data==None:
			if not system_log(user,oper_fail,'未设置FTP服务器','密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"请设置FTP服务器\",\"info\":-1}"
		ftp_all_data=json.loads(ftp_all_data)
		if json_data['MasterFTPServer']['FTPServerId']==0:
			json_data['MasterFTPServer']=None
			for i in ftp_all_data['data']:
				if i['Flag']==2:
					json_data['MasterFTPServer']=i
					break
		if json_data['StandByFTPServer']['FTPServerId']==0:
			json_data['StandByFTPServer']=None
			for i in ftp_all_data['data']:
				if i['Flag']==1:
					json_data['StandByFTPServer']=i
					break
		host=json_data['MasterFTPServer']['ServerIP']
		username=json_data['MasterFTPServer']['ServerUser']
		(error,password)=decrypt_pwd(json_data['MasterFTPServer']['ServerPasswd'])
		if error!=0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno)
		localpath=path
		remotepath=json_data['MasterFTPServer']['ServerPath']
		(error,result)=f_transmit(host, username, password, localpath, remotepath)
		if error!=0:
			if not system_log(user,oper_fail,"默认%s"%result,'密码管理>%s'%module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			if json_data['StandByFTPServer']==None:
				return "{\"Result\":false,\"ErrMsg\":\"默认%s\"}"%result
			else:
				host=json_data['StandByFTPServer']['ServerIP']
				username=json_data['StandByFTPServer']['ServerUser']
				(error,password)=decrypt_pwd(json_data['StandByFTPServer']['ServerPasswd'])
				if error!=0:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno)
				localpath=path
				remotepath=json_data['StandByFTPServer']['ServerPath']
				(error,result)=f_transmit(host, username, password, localpath, remotepath)
				if error!=0:
					if not system_log(user,oper_fail,"备用%s"%result,'密码管理>%s'%module):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"备用%s\"}"%result
				if not system_log(user,oper,'成功','密码管理>%s'%module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":true,\"info\":\"密码文件发送成功（备用FTP配置）\"}"
		if not system_log(user,oper,'成功','密码管理>%s'%module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":true,\"info\":\"密码文件发送成功（默认FTP配置）\"}"
#def f_transmit(host, username, password, localpath, remotepath = "/"):

@pwd_export_py.route('/user_value',methods=['GET','POST'])
def user_value():
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	if sess<0 or sess==None:
		sess=''
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	user=system_user
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
			sql="select u.\"UserId\",u.\"PwdFileApprove\" from public.\"User\" u where u.\"UserCode\"='%s';"%(system_user)
			curs.execute(sql)
			results = curs.fetchall()
			if len(results)==0:
				return "{\"Result\":false,\"ErrMsg\":'登录账号不存在'}"
			new_time=time.time()
			if results[0][1]==None or results[0][1]=='':
				user_appr=[]
			else:
				user_appr=results[0][1].split('\n')
			ip_str=[]
			ip_new_str=[]
			appr=0
			while ('' in user_appr):
				user_appr.remove('')
			for i in range(len(user_appr)):
				item_appr=user_appr[i].split(':')
				if len(item_appr[0])==6:
					ip_new_str.append(user_appr[i])
				elif (new_time-int(item_appr[0]))>(60*60*2):
					pass
				else:
					ip_str.append(item_appr[1])
					ip_new_str.append(user_appr[i])
			sql="select u.\"UserId\",u.\"PwdFileApprove\" from  where u.\"UserCode\"='%s';"%(system_user)
			sql='UPDATE public.\"User\" SET \"PwdFileApprove\" = \'%s\' WHERE \"UserCode\"=\'%s\';'%('\n'.join(ip_new_str),system_user)
			curs.execute(sql)
			conn.commit()
			return "{\"Result\":true,\"info\":%s,\"appr\":%s,\"ip_str\":\"%s\"}" % (results[0][0],appr,','.join(ip_str))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)	
#下载 #发送
@pwd_export_py.route('/export_pwd',methods=['GET','POST'])
def export_pwd():
	global oper
	global oper_fail
	global module
	global user
	global se
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	if sess<0 or sess==None:
		sess=''
	se=sess
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	user=system_user
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	json_data=request.form.get('a1')
	debug(str(json_data))
	if json_data<0 or json_data==None:
		json_data=''
	_type=request.form.get('a2')
	if _type<0 or _type==None:
		_type='1'
	type_name=request.form.get('a3')
	if type_name<0 or type_name==None or type_name=='1':
		module='自动改密'
		oper_fail='下载改密结果'
	elif type_name=='2':
		module='手动改密'
		oper_fail='下载改密结果'
	elif type_name=='3':
		module='历史清单'
		oper_fail='下载历史清单'
	elif type_name=='4':
		module='密码导出'
		if _type=='1':
			oper_fail='下载密码文件'
		else:
			oper_fail='发送密码文件'
	json_data=str(json_data).decode('utf-8')
	task_content = '[global]\nclass = taskpwd_export\ntype = export_pwd_function\njson_data=%s\nsystem_user=%s\nclient_ip=%s\nsess=%s\nmodule=%s\noper_fail=%s\n_type=%s\n' % (str(json_data),system_user,client_ip,sess,module,oper_fail,_type)
	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":true}" 
	# (error,results)=export_pwd_function(json_data,system_user)
	# if error!=0:
	# 	return results
	# if _type=='1':
	# 	results_array=results.split('/')
	# 	file_name=results_array.pop(len(results_array)-1)
	# 	path='/'.join(results_array)
	# 	if not system_log(user,oper,'成功','密码管理>%s'%module):
	# 		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	# 	return send_from_directory(path,file_name,as_attachment=True)
	# elif _type=='2':
	# 	results=send_function(results,system_user)
	# 	return results
	

#下载文件
@pwd_export_py.route('/download_expt',methods=['GET','POST'])
def download_expt():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	if sess<0 or sess==None:
		sess=request.args.get('a0')
		if sess<0 or sess==None:
			sess=''
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)%s\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	return send_from_directory('/usr/storage/.system/passwd','expt_%s.%s.pwd' % (system_user,sess),as_attachment=True,attachment_filename='expt_%s.pwd'%system_user)
	
#页面跳转函数
@pwd_export_py.route('/pwd_export',methods=['GET','POST'])
def pwd_export():
	tasktype = request.form.get("tasktype")
	page = request.form.get("c")
	search = request.form.get("d")
	search2 = request.form.get("e")
	# se=request.form.get('se')
	if page < 0 or page == None:
		page = "1"
	if search < 0 or search == None:
		search = ""
	if search2 < 0 or search2 == None:
		search2 = ""
	id = 0
	if tasktype < 0 or tasktype == None:
		tasktype = "1"
	if tasktype == "1":
		t = "pwd_export_list.html"
	elif tasktype=="3":
		t = "pwd_export_add.html"
	elif tasktype=="2":
		id = request.form.get("a")
		if id < 0 or id == None:
			id = "0"
		t = "pwd_export_add.html"
	return render_template(t,tasktype=tasktype,a=id,c=page,d=search,e=search2)

#get_down_ok_pwd
@pwd_export_py.route('/get_down_ok_pwd',methods=['GET','POST'])
def get_down_ok_pwd():
	se = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			file_name='expt_%s.%s.pwd'% (userCode,se)
			sql = "select * from private.\"AuthExportInfo\" where \"FileName\"=E'%s'"%(file_name)
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				sql = "delete from private.\"AuthExportInfo\" where \"FileName\"=E'%s'"%(file_name)
				curs.execute(sql)
				conn.commit()
			else:
				return "{\"Result\":false,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
			return "{\"Result\":true,\"ErrMsg\":\""+str(results[0][2])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#列表
@pwd_export_py.route('/get_pwd_export_list',methods=['GET','POST'])
def get_pwd_export_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	if sess<0 or sess==None:
		sess=''
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
	id=request.form.get('a1')
	if id<0 or id==None:
		id='null'
	elif id!='null':
		id="'%s'"%id
	search_typeall=request.form.get('a2')
	if search_typeall<0 or search_typeall==None:
		search_typeall=''
	paging=request.form.get('a3')
	if paging<0 or paging==None:
		paging='null'
	else:
		paging=int(paging)
	num=request.form.get('a4')
	if num<0 or num==None:
		num='null'
	else:
		num=int(num)
	nodetails=request.form.get('a5')
	if nodetails<0 or nodetails==None:
		nodetails='true'
	hostip=''
	hostname=''
	searchstring=''
	typeall = search_typeall.split('\t')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="hostip":
			hostip=hostip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=='hostname':
			hostname=hostname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if hostip=="":
		hostip="null"
	else:
		hostip="'%s'"%(hostip[:-1])
	if hostname=="":
		hostname="null"
	else:
		hostname="E'%s'"%(hostname[:-1])
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	searchconn['searchstring']=searchstring
	searchconn['LoginUserCode']=system_user
	searchconn=json.dumps(searchconn)
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	hostip=hostip.replace("\\\\","\\\\\\\\")
	hostip=hostip.replace(".","\\\\.")
	hostip=hostip.replace("?","\\\\?")
	hostip=hostip.replace("+","\\\\+")
	hostip=hostip.replace("(","\\\\(")
	hostip=hostip.replace("*","\\\\*")
	hostip=hostip.replace("[","\\\\[")
	hostname=hostname.replace("\\\\","\\\\\\\\")
	hostname=hostname.replace(".","\\\\.")
	hostname=hostname.replace("?","\\\\?")
	hostname=hostname.replace("+","\\\\+")
	hostname=hostname.replace("(","\\\\(")
	hostname=hostname.replace("*","\\\\*")
	hostname=hostname.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetHostAccountPwd\"(%s,%s,%s,%s,%s,%s,E'%s');"%(id,hostip,hostname,nodetails,num,paging,searchconn)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#SaveAuthMessage
@pwd_export_py.route('/save_authmessage',methods=['GET','POST'])
def save_authmessage():
	debug('save_authmessage')
	se=request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
			if error == 2:
					return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
					return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	UserId_str=request.form.get('a1')
	ApproveStrategyId=request.form.get('a2')
	PwdFileApproveType=request.form.get('a3')
	content=request.form.get('a4')
	MessageId_arr=request.form.get('a5')
	ip_arr=request.form.get('a6')
	ip_len=request.form.get('a7')
	if PwdFileApproveType<0 or PwdFileApproveType==None:
		PwdFileApproveType=1;
	PwdFileApproveType=int(PwdFileApproveType)
	if PwdFileApproveType<=1:
		return '{"Result":true}'
	code=random.randint(100000,999999)
	code_arr=[]
	for i in range(int(ip_len)):
		code_arr.append(str(code))
	MessageId_arr=MessageId_arr.split(',');
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			for i in MessageId_arr:
				sql='update private."Message" set "VerificationCode"=\'%s\' where "MessageId"=%s;'%(code,i)
				curs.execute(sql)
				conn.commit()
			sql='select u."UserName",u."Email",u."MobilePhone" from public."User" u where u."UserCode"=\'%s\';'%userCode
			curs.execute(sql)
			User_g = curs.fetchall()[0]
			contest_p_m='';
			if User_g[2]=='' or User_g[2]==None:
				if User_g[1]=='' or User_g[1]==None:
					contest_p_m='联系方式：'
			else:
				if User_g[1]=='' or User_g[1]==None:
					contest_p_m='联系方式：%s'%(User_g[2])
				else:
					contest_p_m='联系方式：%s，%s'%(User_g[2],User_g[1])
			ApproveStrategyId=ApproveStrategyId.split(',')
			if (PwdFileApproveType&4)>0:
				contest_p_m='详情请见消息中心';				
				ms_content='%s(%s)发起下载申请\r\n%s'%(userCode,User_g[0],contest_p_m)
				sql="select public.\"SaveAuthMessage\"(E'%s','{%s}',3,%s,'{%s}');"%(MySQLdb.escape_string(ms_content).decode("utf-8"),UserId_str,ApproveStrategyId[0],','.join(code_arr))
				debug(sql)
				curs.execute(sql)
				conn.commit()
				ApproveStrategyId.pop(0)
			if (PwdFileApproveType&8)>0:
				smtp_content='%s(%s)发起下载申请\r\n%s\r\n%s'%(userCode,User_g[0],content,contest_p_m)
				sql="select public.\"SaveAuthMessage\"(E'%s','{%s}',1,%s,'{%s}');"%(MySQLdb.escape_string(smtp_content).decode("utf-8"),UserId_str,ApproveStrategyId[0],','.join(code_arr))
				debug(sql)
				curs.execute(sql)
				conn.commit()
			curs.execute('select u."PwdFileApprove" from public."User" u where u."UserCode"=\'%s\';'%userCode)
			user_app=curs.fetchall()[0][0]
			PwdFileApprove_str=''
			if user_app==None or user_app=='':
				pass
			else:
				PwdFileApprove_str=user_app.encode('utf-8')+'\n'
			PwdFileApprove_str=PwdFileApprove_str+('%s:%s'%(code,ip_arr))
			curs.execute('UPDATE public."User" SET "PwdFileApprove"=\'%s\' WHERE "UserCode"=\'%s\';'%(PwdFileApprove_str,userCode))
			conn.commit()
			return "{\"Result\":true,\"code\":\""+str(code)+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)%s\"}" %(sys._getframe().f_lineno,str(e))		

#删除下载文件
@pwd_export_py.route('/del_pwd_file',methods=['GET','POST'])
def del_pwd_file():
        se = request.form.get('a0')
        client_ip = request.remote_addr
        (error,userCode,mac) = SessionCheck(se,client_ip);
        if error < 0:
                return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        elif error > 0:
                if error == 2:
                        return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
                else:
                        return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        path=EXPORT_PWD%(userCode,se)
        task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=%s\n' % (str(path))
        if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        return 'true'
	
