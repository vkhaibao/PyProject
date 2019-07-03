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
from htmlencode import parse_sess
from htmlencode import check_role
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
module_app_set = Blueprint('module_app_set',__name__)

ERRNUM_MODULE_module_app_set = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

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

def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			debug(str(sql))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
	
@module_app_set.route('/module_app_set_show',methods=['GET', 'POST'])
def module_app_set_show():			
	reload(sys)
	sys.setdefaultencoding('utf-8')
	return render_template('module_app_set.html')

@module_app_set.route('/module_app_set_list',methods=['GET', 'POST'])
def module_app_set_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetApplicationConfig\"(null,null)")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@module_app_set.route('/Save_ApplicationConfig',methods=['GET', 'POST'])
def Save_ApplicationConfig():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	data = request.form.get('z1')
	flag = request.form.get('z2')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	module_data = json.loads(data)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetApplicationConfig\"(null,null)")
			results = curs.fetchall()[0][0].encode('utf-8')
			old_module = json.loads(results)
			
			curs.execute("select public.\"PSaveApplicationConfig\"(E'%s')" % (data))
			results = curs.fetchall()[0][0].encode('utf-8')
			re_module = json.loads(results)
			
			mode_dict = {"2":"认证","1":"直连"}
			service_dict = {"True":"开启服务","False":"关闭服务"}
			serport_dict = {"True":"开启端口访问","False":"关闭端口访问"}
			i = 0
			show_msg_list = []
			while (i < len(old_module['data'])):
				show_msg_detail_list = []
				if str(old_module['data'][i]['Mode']) != str(module_data[i]['Mode']):
					show_msg_detail_list.append(mode_dict[str(module_data[i]['Mode'])])
				
				if old_module['data'][i]['Enabled'] != module_data[i]['Enabled']:
					show_msg_detail_list.append(service_dict[str(module_data[i]['Enabled'])])
					
				if old_module['data'][i]['EnableServicePort'] != module_data[i]['EnableServicePort']:
					show_msg_detail_list.append(serport_dict[str(module_data[i]['EnableServicePort'])]) 
				
				if str(old_module['data'][i]['ServicePort']) != str(module_data[i]['ServicePort']):
					show_msg_detail_list.append(str(module_data[i]['ServicePort']))
				
				if len(show_msg_detail_list) > 0:
					show_msg = old_module['data'][i]['ApplicationName'] + '：' + '、'.join(show_msg_detail_list)
					show_msg_list.append(show_msg)
				i = i + 1

			if len(show_msg_list) > 0:
				show_msg = '，'.join(show_msg_list)
				if re_module['Result']:
					system_log(userCode,show_msg,"成功","模块设置")
				else:
					system_log(userCode,show_msg,"失败："+re_module['ErrMsg'],"模块设置")
			'''
			if flag == '1':
				sql = 'update public."GlobalStrategy" set "IsTunnel" = false'
				curs.execute(sql)
				conn.commit()
			'''
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

"""
@module_app_set.route('/module_app_set_show',methods=['GET', 'POST'])
def module_app_set_show():
        reload(sys)
        sys.setdefaultencoding('utf-8')
        try:
                with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
                        curs = conn.cursor()
                        debug("1233")
                        debug("select public.\"PGetApplicationConfig\"(null,null)")
                        curs.execute("select public.\"PGetApplicationConfig\"(null,null)")
                        debug("1233")
                        data = curs.fetchall()[0][0].encode('utf-8')
                        data = json.loads(data)
                        data = data['data']
                        data = json.dumps(data)
        except pyodbc.Error,e:
                return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_module_app_set + 3, ErrorEncode(e.args[1]))
        debug(data)
        return render_template('module_app_set.html',data=data)
"""
