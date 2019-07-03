#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
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
from htmlencode import parse_sess
from htmlencode import check_role
from logbase import common
from index import PGetPermissions
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
protocol_lxz = Blueprint('protocol_app',__name__)

ERRNUM_MODULE_protocol_app = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

def debug(c):
	return 0
	path = "/var/tmp/debuglxz.txt"
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
			sql="select public.\"PGetPermissions\"('%s');" %(MySQLdb.escape_string(us))
			debug(str(sql))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
'''

#协议主页	
@protocol_lxz.route('/protocol_app_show',methods=['GET', 'POST'])
def protocol_app_show():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se=request.form.get('a0')
	ipage=request.form.get('a1')
	keyword=request.form.get('a2')
	selid=request.form.get('a3')
	sear=request.form.get('a4')
	
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
	
	if keyword==None:
		keyword="[]"
	if sear==None:
		sear="[]"
	if selid==None:
		selid="[]"
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	if	selid.find(']') < 0:
		return '',403
	select_tmp = selid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 	
	select_tmp = sear[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 			
	if ipage and  (str(ipage).isdigit() == False):
		return '',403
	
	
	
	_power = PGetPermissions(usercode)
	_power = str(_power)
	_power_json = json.loads(_power)
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])

	return render_template('protocol_lxz.html',ipage=ipage,keyword=keyword,selid=selid,sear=sear,manage_power_id=manage_power_id)

#向数据库请求模板数据
@protocol_lxz.route('/get_agreement_list',methods=['GET','POST'])
def get_agreement_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	page=request.form.get('data1')
	nowpage=request.form.get('data2')
	keyword=request.form.get('data3')
	session = request.form.get('a0')
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
	elif dsc!='false' and dsc!='true':
		return '',403
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if page<0:
		page=0
	elif page!='null' and not page.isdigit():
		return '',403
	if nowpage<0:
		nowpage=0
	if nowpage!="null":
		luo=int(page)*(int(nowpage)-1)
	else:
		luo="null"
	keyword=json.loads(keyword)
	if str(keyword)!="[None]":
		keyword1=""
		keyword2=""
		keyword3=""
		keyword4=""
		if len(keyword)!=0:
			for i in keyword:
				word_arry=i.split('-',2)
				if word_arry[0]=="名称":
					keyword1=keyword1+MySQLdb.escape_string(word_arry[1])+'\n'
				if word_arry[0]=="端口":
					keyword2=keyword2+MySQLdb.escape_string(word_arry[1])+'\n'
				if word_arry[0]=="描述":
					keyword3=keyword3+MySQLdb.escape_string(word_arry[1])+'\n'
				if word_arry[0] == "所有":
					keyword4=keyword4+MySQLdb.escape_string(word_arry[1])+'\n'
			if keyword1 !="":
				keyword1 = keyword1[:-1]
				keyword1 = MySQLdb.escape_string(keyword1)
			if keyword2 !="":
				keyword2 = keyword2[:-1]
				keyword2 = MySQLdb.escape_string(keyword2)
			if keyword3 !="":
				keyword3 = keyword3[:-1]
				keyword3 = MySQLdb.escape_string(keyword3)
			if keyword4 !="":
				keyword4 = keyword4[:-1]
				keyword4 = MySQLdb.escape_string(keyword4)
			keyword1=keyword1.replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			keyword2=keyword2.replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			keyword3=keyword3.replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			keyword4=keyword4.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
	else:
		keyword1=""
		keyword2=""
		keyword3=""
		keyword4=""
	if keyword4 == "":
		searchstring = 'null'
	else:
		searchstring = "E'{\"searchstring\":\"%s\"}'" % keyword4
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs=conn.cursor()
			sql="select public.\"PGetAccessProtocol\"(null,E\'%s\',E\'%s\',E\'%s\',%s,%s,%s,%s);"%(keyword1,keyword2,keyword3,str(page),str(luo),searchstring,dsc)
			curs.execute(sql)
			result=curs.fetchall()[0][0].encode('utf-8')
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#进入创建网页   
@protocol_lxz.route('/create_agreement',methods=['GET','POST'])
def create_agreement():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	type=request.form.get('t1')
	ipage=request.form.get('x1')
	protocolid=request.form.get('x2')
	keyword=request.form.get('x3')
	selid=request.form.get('x4')
	sear=request.form.get('x5')
	
	if keyword==None:
		keyword="[]"
	if sear==None:
		sear="[]"
	if selid==None:
		selid="[]"
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	if	selid.find(']') < 0:
		return '',403
	select_tmp = selid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 	
	select_tmp = sear[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 			
	if ipage and  (str(ipage).isdigit() == False):
		return '',403
	
	if type and  (str(type).isdigit() == False):
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

	return render_template('create_protocol.html',tasktape=type,ipage=ipage,protocolid=protocolid,keyword=keyword,selid=selid,sear=sear,manage_power_id=manage_power_id)

#创建新的协议
@protocol_lxz.route('/set_protocol',methods=['GET','POST'])
def set_protocol():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data=request.form.get('x1')
	session = request.form.get('a0')
	module_type = request.form.get('a10')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if module_type == "" or module_type == None:
		title = "运维管理>协议"
		module_name = "协议"
	else:
		title = module_type
		module_name = title.split(">")[1]
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(userCode,'访问授权,工单授权,管理授权,主机管理,密码修改') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs=conn.cursor()
			data = json.loads(data)
			pro_name = ""
			return_id_arr=[]
			for i in data:
				pro_json = json.loads(i)
				if pro_json['ProtocolId'] != 0:
					edit_flag = 1#编辑
				else:
					edit_flag = 0
				pro_name = pro_name + pro_json['ProtocolName'] + ','
				i_v = MySQLdb.escape_string(i).decode("utf-8")
				sql="select public.\"PSaveAccessProtocol\"(E\'%s\');"%(i_v)
				debug(sql)
				curs.execute(sql)
				result=curs.fetchall()[0][0].encode('utf-8')
				ret = json.loads(result)
				if ret['Result'] == False:
					if edit_flag == 0:
						system_log(userCode,"创建协议：%s" % pro_json['ProtocolName'],"失败："+ret['ErrMsg'],title)
					else:
						system_log(userCode,"编辑协议：%s" % pro_json['ProtocolName'],"失败："+ret['ErrMsg'],title)
					conn.rollback();
					return result
				else:
					return_id_arr.append(ret['ProtocolId'])
					if len(data) == 1:
						return result
			if edit_flag == 0:
				system_log(userCode,"创建协议：%s" % pro_name[:-1],"成功",title)
			else:
				system_log(userCode,"编辑协议：%s" % pro_name[:-1],"成功",title)
			return '{"Result":true,"id_arr":%s}'%(json.dumps(return_id_arr))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#删除协议
@protocol_lxz.route('/new_delete_protocol',methods=['GET','POST'])
def new_delete_protocol():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	ty=request.form.get('b1')
	protocolid=request.form.get('b2')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(userCode,'访问授权,工单授权,管理授权,主机管理,密码修改') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)			
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs=conn.cursor()
			if(ty=='0'):
				sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\" in (%s)" % protocolid[1:-1]
				debug("sql:%s" % sql)
				curs.execute(sql)
				pro_str = ""
				for row in curs.fetchall():
					pro_str = pro_str + row[0].encode('utf-8') + ","
				
				debug("pro_str:%s" % pro_str)
				
				id_array=protocolid[1:-1].split(',')
				for protocolid in id_array:
					debug("start")
					sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\"=%d" % int(protocolid)
					debug("sql:%s" % sql)
					curs.execute(sql)
					pro_name = curs.fetchall()[0][0].encode('utf-8')
					
					sql="select public.\"PDeleteAccessProtocol\"(%d);"%(int(protocolid))
					curs.execute(sql)
					result=curs.fetchall()[0][0].encode('utf-8')
					results=json.loads(result)
					
					if results['Result']==False:
						system_log(userCode,"删除协议：%s" % pro_name,"失败："+result['ErrMsg'],"运维管理>协议")
						conn.rollback()
						return result
				debug("12313131313123")
				if pro_str != "":
					system_log(userCode,"删除协议：%s" % pro_str[:-1],"成功","运维管理>协议")
				return "{\"Result\":true}"
			else:
				sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\"=%d" % int(protocolid)
				curs.execute(sql)
				pro_name = curs.fetchall()[0][0].encode('utf-8')
				
				sql="select public.\"PDeleteAccessProtocol\"(%d);"%(int(protocolid))
				curs.execute(sql)
				result=curs.fetchall()[0][0].encode('utf-8')
				
				re_p = json.loads(result)
				if re_p['Result']:
					system_log(userCode,"删除协议：%s" % pro_name,"成功","运维管理>协议")
				else:
					system_log(userCode,"删除协议：%s" % pro_name,"失败："+re_p['ErrMsg'],"运维管理>协议")
				return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)    

#查询单个协议
@protocol_lxz.route('/select_protocol',methods=['GET','POST'])
def select_protocol():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	protocolid=request.form.get('x1')
	protocolid=int(protocolid)
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs=conn.cursor()
			if protocolid==0:
				sql="select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
			else:
				sql="select public.\"PGetAccessProtocol\"(%d,null,null,null,null,null);"%(int(protocolid))
			curs.execute(sql)
			result=curs.fetchall()[0][0].encode('utf-8')
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
@protocol_lxz.route('/select_name',methods=['GET','POST'])
def select_name():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	name=request.form.get('x1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs=conn.cursor()
			sql="select public.\"PGetAccessProtocolByName\"(E\'%s\');"%(name)
			curs.execute(sql)
			result=curs.fetchall()[0][0]
			return str(result)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
