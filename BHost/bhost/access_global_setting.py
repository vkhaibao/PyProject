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
import httplib, urllib,urllib2

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import task_client
from logbase import defines
from ctypes import *
from urllib import unquote
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
access_global_setting = Blueprint('access_global_setting',__name__)

SIZE_PAGE = 20
ErrorNum = 10000
def debug(c):
	return 0
	path = "/var/tmp/debugaccess_global_setting.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
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

#页面跳转函数
@access_global_setting.route('/access_global_setting_show',methods=['GET','POST'])
def pwd_trust():
		#页面跳转函数
		#参数 tasktype = 添加-1
		#a=id
		#session = request.form.get("se")
		se=request.form.get("a0")
		if se ==None or se<0:
				se=request.args.get("a0")
		if se<0:
				se=''
		t = "access_global_setting.html"
		return render_template(t,se=se)

@access_global_setting.route('/PGet_LocalClient',methods=['GET','POST'])
def PGet_LocalClient():
		###session 检查
		reload(sys)
		sys.setdefaultencoding('utf-8')
		sess = request.form.get('a0')
		json_str=request.form.get('a1')
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
				sql="select public.\"PGetLocalClient\"(E'%s');"%(system_user)
				debug(str(sql))
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				if results==None:
					results='null'
				else:
					results=json.loads(str(results))
					for i in  results['data']:
						i['ClientProgram']=base64.b64decode(i['ClientProgram'])
					results=str(json.dumps(results))
				return "{\"Result\":true,\"info\":%s,\"client_ip_global\":\"%s\"}" % (results,client_ip)
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@access_global_setting.route('/PGet_UserGlobalConfig',methods=['GET','POST'])
def PGet_UserGlobalConfig():
		###session 检查
		reload(sys)
		sys.setdefaultencoding('utf-8')
		sess = request.form.get('a0')
		json_str=request.form.get('a1')
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
				sql="select public.\"PGetUserGlobalConfig\"(E'%s');"%(system_user)
				debug(str(sql))
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				if results==None:
					results='null'
				return "{\"Result\":true,\"info\":%s}" % (results)
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@access_global_setting.route('/PSave_UserGlobalConfig',methods=['GET','POST'])
def PSave_UserGlobalConfig():
		###session 检查
		reload(sys)
		sys.setdefaultencoding('utf-8')
		sess = request.form.get('a0')
		json_str=request.form.get('a1')
		md5_str = request.form.get('m1')
		
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
			md5_json = StrMD5(json_str);##python中的json的MD5
			if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
				
		json_str=json.loads(str(json_str))
		json_str['UserCode']=system_user
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql="select public.\"PSaveUserGlobalConfig\"(E'%s');"%(str(json.dumps(json_str)))
				debug(str(sql))
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				results_json=json.loads(results)
				if json_str['EnableRemoteApp']:
					oper='全局设定：启用remoteapp(前置机)'
				else:
					oper='全局设定：停用remoteapp(前置机)'
				if not results_json['Result']:
					if not system_log(system_user,oper,results_json['ErrMsg'],'访问工具>全局设定'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					conn.commit()
					if not system_log(system_user,oper,'成功','访问工具>全局设定'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return results 
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@access_global_setting.route('/PSave_LocalClient',methods=['GET','POST'])
def PSave_LocalClient():
		###session 检查
		reload(sys)
		sys.setdefaultencoding('utf-8')
		sess = request.form.get('a0')
		json_str=request.form.get('a1')
		md5_str = request.form.get('m1')
		
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
			md5_json = StrMD5(json_str);##python中的json的MD5
			if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
		json_str=json.loads(str(json_str))
		json_str['UserCode']=system_user
		ClientProgram_value=json_str['ClientProgram']
		json_str['ClientProgram']=base64.b64encode(json_str['ClientProgram'])
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql="select public.\"PSaveLocalClient\"(E'%s');"%(str(json.dumps(json_str)))
				debug(str(sql))
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				results_json=json.loads(results)
				if json_str['ClientName']=='Putty':
					json_str['ProtocolName']='SSHCONSOLE'
				elif json_str['ClientName']=='SecureCRT':
					json_str['ProtocolName']='SSHCONSOLE'
				elif json_str['ClientName']=='XShell':
					json_str['ProtocolName']='SSHCONSOLE'
				elif json_str['ClientName']=='FlashfXP':
					json_str['ProtocolName']='FTP/SFTP'
				elif json_str['ClientName']=='SecureCRT':
					json_str['ProtocolName']='SSHCONSOLE'
				if json_str['LocalClientId']==0:
					oper='创建%s(%s)：%s'%(json_str['ClientName'],json_str['ProtocolName'],ClientProgram_value)
				else:
					oper='编辑%s(%s)：%s'%(json_str['ClientName'],json_str['ProtocolName'],ClientProgram_value)
				if not results_json['Result']:
					if not system_log(system_user,oper,results_json['ErrMsg'],'访问工具>全局设定'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					if not system_log(system_user,oper,'成功','访问工具>全局设定'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"    
				conn.commit()
				return results 
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@access_global_setting.route('/get_8080_token',methods=['GET','POST'])
def get_8080_token():
	try:
		url = 'http://192.168.0.157:8080/bhremote/api/tokens'
		post_data = "username=admin:11223344556677889900@192.168.0.30:rdp&password=11223344556677889900"
		req = urllib2.urlopen(url, post_data)
		content = req.read()
		return content
	except Error,e:
		debug(str(e))

#删除
@access_global_setting.route('/PDelete_LocalClient',methods=['GET', 'POST'])
def PDelete_LocalClient():
		reload(sys)
		sys.setdefaultencoding('utf-8')
		id_str = request.form.get('a1')
		session = request.form.get('a0')
		id_name = request.form.get('a2')
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
				# PDeleteConnParam(id)
				sql = "select public.\"PDeleteLocalClient\"(%s);" % (id_str)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				debug(str(id_name))
				id_name_arr=id_name.split('_')
				if id_name_arr[0]=='Putty':
					id_name_arr[1]='SSHCONSOLE'
				elif id_name_arr[0]=='SecureCRT':
					id_name_arr[1]='SSHCONSOLE'
				elif id_name[0]=='XShell':
					id_name_arr[1]='SSHCONSOLE'
				elif id_name_arr[0]=='FlashfXP':
					id_name_arr[1]='FTP/SFTP'
				elif id_name_arr[0]=='SecureCRT':
					id_name_arr[1]='SSHCONSOLE'
				debug(str(id_name_arr))
				id_name_arr[0]=id_name_arr[0].replace('-','.')
				oper='删除%s(%s)'%(id_name_arr[0],id_name_arr[1])
				debug(str(oper))
				if not result_json['Result']:
					if not system_log(system_user,oper,result_json['ErrMsg'],'访问工具>全局设定'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					if not system_log(system_user,oper,'成功','访问工具>全局设定'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
				return result 
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
###获取 浏览全路径
@access_global_setting.route('/SaveClientPath',methods=['GET', 'POST'])
def SaveClientPath():
	headers  = str(request.headers);
	if headers.find("a0") < 0 and headers.find('a1') < 0:
		try:
			Session = request.args.get('a0');
			Path = request.args.get('a1');
		except:
			return "{\"Result\":false,\"ErrMsg\":\"参数错误(%d)\"}" %(sys._getframe().f_lineno),200
	else:
		try:
			Session = headers.split('a0',0)[1].split()[1]
			Path = headers.split('a1',0)[1].split()[1]
		except:
			return "{\"Result\":false,\"ErrMsg\":\"参数错误(%d)\"}" %(sys._getframe().f_lineno),200
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200
		
	try:
		sql ="select count(*) from private.\"USBKeyResult\" where \"SessTime\" ='%s'; " %(Session)
		debug(sql)
		curs.execute(sql)
		results = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"\"}",200
		#return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200
	
	if results == 0:
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"\"}",200
		#return "{\"Result\":false,\"ErrMsg\":\"Session 不存在(%d)\"}" %(sys._getframe().f_lineno),200

	try:
		sql = "UPDATE private.\"USBKeyResult\" SET \"Status\" = 1,\"CertInfo\"='%s' where \"SessTime\" ='%s'; " %(base64.b64decode(Path).decode("utf-8"),Session)
		debug(sql)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":true,\"ErrMsg\":\"\"}",200
		#return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200
		
	return "{\"Result\":true,\"ErrMsg\":\"\"}",200
		
@access_global_setting.route('/UpdateMac',methods=['GET', 'POST'])
def UpdateMac():
	headers  = str(request.headers);
	if headers.find("a1") < 0 and headers.find('a2') < 0:
		try:
			ip = request.args.get('a1');
			mac = request.args.get('a2');
		except:
			return "{\"Result\":false,\"ErrMsg\":\"参数错误(%d)\"}" %(sys._getframe().f_lineno),200
	else:
		try:
			ip = headers.split('a1',0)[1].split()[1]
			mac = headers.split('a2',0)[1].split()[1]
		except:
			return "{\"Result\":false,\"ErrMsg\":\"参数错误(%d)\"}" %(sys._getframe().f_lineno),200
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200
		
	try:
		sql = "select * from private.\"IPMACMap\" where \"ClientIP\" = '%s';" % ip
		debug(sql)
		curs.execute(sql)
		results = curs.fetchall()
		modiftime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		if len(results) != 0:
			sql ="update private.\"IPMACMap\" set \"ClientMAC\" = \'%s\', \"LastModifyTime\" = \'%s\' where \"ClientIP\" ='%s';" % (mac, modiftime, ip)
		else:
			sql ="insert into private.\"IPMACMap\"(\"ClientMAC\", \"ClientIP\", \"LastModifyTime\")values('%s', '%s', '%s');" % (mac, ip, modiftime)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"更新失败(%d)\"}" %(sys._getframe().f_lineno),200
		#return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno),200	
	return "{\"Result\":true,\"ErrMsg\":\"\"}",200
###	获取path的状态信息
@access_global_setting.route('/repeat_get_path',methods=['GET','POST'])
def repeat_get_path():
	session = request.form.get('a0')
	sesstime = request.form.get('z1')

	##XSS Defence
	if str(sesstime).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session time格式错误\"}"
		
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
	path = '';
	try:
		sql = "select \"Status\",\"CertInfo\",\"Type\" from private.\"USBKeyResult\" where \"SessTime\" = '%s';" %(sesstime);
		curs.execute(sql)
		res_tmp = curs.fetchall()
		if not res_tmp:
			return "{\"Result\":true,\"info\":0,\"path\":\" \"}"
		results = res_tmp[0][0]
		Type =res_tmp[0][2]
		#if Type == 'IfUpdate':
		#	return "{\"Result\":true,\"info\":1,\"path\":\"True\"}"

		if results == None:
			results = 0;
		else:
			path = res_tmp[0][1]
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		return "{\"Result\":true,\"info\":1,\"path\":\"True\"}"
	return "{\"Result\":true,\"info\":%d,\"path\":\"%s\"}" %(results,path)		
	
###########################偏好设定函数
#页面跳转函数
@access_global_setting.route('/styleConfig_show',methods=['GET','POST'])
def styleConfig_show():
	se=request.form.get("a0")
	if se ==None or se<0:
			se=request.args.get("a0")
	if se<0:
			se=''
	t = "style_config.html"
	return render_template(t,se=se)

@access_global_setting.route('/PSave_UserStyleConfig',methods=['GET','POST'])
def PSave_UserStyleConfig():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	session = request.form.get('a0')
	value = request.form.get('a1')
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
	if value != '0' and value != '1' and value != '2':
		return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
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
		sql = "update public.\"User\" set \"ColorScheme\" = %s where \"UserCode\" = '%s';" %(value,system_user)
		debug(sql)
		curs.execute(sql)
		conn.commit()
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false}"
	return "{\"Result\":true}"

@access_global_setting.route('/PGet_UserStyleConfig',methods=['GET','POST'])
def PGet_UserStyleConfig():
	reload(sys)
	sys.setdefaultencoding('utf-8')

	session = request.form.get('a0')
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
		sql = "select \"ColorScheme\" from public.\"User\" where \"UserCode\" = '%s';" %(system_user)
		debug(sql)
		curs.execute(sql)
		results = curs.fetchall()[0][0]
		curs.close()
		conn.close()
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false}"
	return "{\"Result\":true,\"Value\":%d}" %(results)


