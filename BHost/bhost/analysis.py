#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import time
import json
import MySQLdb
import urllib
import htmlencode
import cgi

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionCheck
from htmlencode import checkproto
from htmlencode import checkaccount
from htmlencode import checkhostaccount


sys.path.append('/flash/system/bin')
from bhcomm import StrClas

import base64

from flask import request,Blueprint,render_template,send_from_directory # 

import xml.etree.ElementTree as ET

analysis = Blueprint('analysis',__name__)
ERRNUM_MODULE_search = 10000
maxpage = 100;
reload(sys)
sys.setdefaultencoding('utf-8')
def debug(c):
	return 0
	path = "/var/tmp/debugyt.txt"
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
	
###检索页面 父框架
@analysis.route("/analysis_index", methods=['GET', 'POST'])
def analysis_index():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	'''
	tp1 = request.args.get('tp1')
	p1 = request.args.get('p1')
	i1 = request.args.get('i1')
	taskid = request.args.get('a1')
	logtype = request.args.get('a2')
	t1 = request.args.get('t1')
	f1 = request.args.get('f1')
	btn_status = request.args.get('a4')
	tasktype= request.args.get('tasktype')
	name = request.args.get('a5')
	'''	
	sessid = request.args.get('s1')#
	stime = request.args.get('st')#
	etime = request.args.get('et')
	statue = request.args.get('stat');
	type =request.args.get('tp');#
	server_user = request.args.get('su');#
	y_user = request.args.get('yu');#
	server_ip = request.args.get('si');#
	logtype = request.args.get('lo');
	other = request.args.get('ot');#
	error_msg = "";
	analysis_id = 0;
	hash  = request.args.get('ha');
	
	if hash < 0 or hash =='':
		pass
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();
			
	
	if logtype <0 or logtype == "":
		logtype == '1'
		
	if logtype == '1':
		ana_str = '关联分析'
	else:
		ana_str = '指令查看'
		
	if sessid:
		if( str(sessid) !='' and str(sessid).isdigit() == False):
			return '',403 
			
	if type:	
		if checkproto(type) == False:
			return '',403 
		
	if other:
		other_tmp = other.split('@');
		if other_tmp[1] != "true" and other_tmp[1] !="false":
			return '',403 
			
	if server_ip:
		server_ip_tmp = server_ip.split('.');
		for n in server_ip_tmp:
			if n.isdigit() == False:
				return '',403 
	if stime:
		try:
			time.mktime(time.strptime(stime,'%Y-%m-%d %H:%M:%S'))
		except:
			return '',403 	
	if server_user:
		if checkhostaccount(server_user)== False:
			return '',403
			
	if y_user:
		if checkaccount(y_user)== False:
			return '',403	
		
	if etime < 0 or etime =="" or etime==' ':
		try:
			with pyodbc.connect(StrSqlConn('BH_DATA')) as conn:
				curs = conn.cursor()
				sql = "select \"xtime_05\" from public.\"ses_table\"  where \"xtime_03\" =%s " %(sessid)
				debug(sql)
				curs.execute(sql)
				data = curs.fetchall()
				if data :
					etime =  data[0];
					if etime == None:
						etime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
					else:
						etime =  data[0][0];
						if etime == None:
							etime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
				else:
					etime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
					
		except pyodbc.Error,e:
			error_msg = ErrorEncode(e.args[1])
	else:
		if statue == '0':
			etime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
			
		else:
			timeArray = time.strptime(etime, "%Y-%m-%d %H:%M:%S");
			timestamp = time.mktime(timeArray);
			#timestamp += 60 * 5;
			time_local = time.localtime(timestamp)
			etime = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
		
	### 创建任务
	'''
	{"SubmitUserCode":"", "SessionId":"", "SessionStatus":"","StartTime":"","EndTime":""}
	'''
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PSaveAssociationAnalysis\"(E'{\"SubmitUserCode\":\"%s\", \"SessionId\":\"%s\", \"SessionStatus\":%s,\"StartTime\":\"%s\",\"EndTime\":\"%s\"}');" %(userCode,sessid,statue,stime,etime)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			debug(str(results))
			results = json.loads(results)
			if(results['Result'] == True):
				analysis_id = results['Id']
			else:
				error_msg = results['ErrMsg']
	except pyodbc.Error,e:
		error_msg = ErrorEncode(e.args[1])
	debug(error_msg)
	return render_template('analysis.html',se=session,us=userCode,sessid=sessid,stime=stime,etime=etime,error_msg = error_msg,analysis_id=analysis_id,type=type,server_user=server_user.replace('\\','\\\\'),y_user=y_user,server_ip=server_ip,logtype=logtype,ana_str=ana_str,other=other)
#获取当前的 数量 和状态 
@analysis.route("/get_stat_row", methods=['GET', 'POST'])
def get_stat_row():
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
	analysis_id = request.form.get('a1')
	sessid = request.form.get('a2');
	
	if analysis_id != '' and str(analysis_id).isdigit() == False:
		return '',403 
	if sessid != '' and str(sessid).isdigit() == False:
		return '',403 	
		
	##状态
	status = 0;
	total_row = 0;
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"Status\" from private.\"AssociationAnalysis\" where \"Id\"=%s;" %(analysis_id)
			debug(sql)
			curs.execute(sql)
			status = curs.fetchall()[0][0]	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetChatCount\"(%s);" %(sessid)
			debug(sql)
			curs.execute(sql)
			total_row = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	return "{\"Result\":true,\"total_row\":%Ld,\"status\":%d,\"info\":\"\"}" %(total_row,status)
	
#获取当前的 数据
@analysis.route("/get_analysis_data", methods=['GET', 'POST'])
def get_analysis_data():	
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
	sessid = request.form.get('a1')
	curpage = request.form.get('p1')
	if curpage <0 or curpage == "":
		curpage = 1
	else:
		curpage = int(curpage)
		
	offset = maxpage*(curpage-1)
	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetChatData\"(%s,'xtime_01,str32_01,xtime_02,str32_02,str32_28,ip_02,xtime_04,str32_22,str32_23,int64_13',%d,%d)" %(sessid,maxpage,offset)
			debug(sql)
			curs.execute(sql)
			data = curs.fetchall()
			if data :
				result = data[0][0]
			else:
				result = "[]"
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
