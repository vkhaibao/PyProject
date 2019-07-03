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
from comm import SessionLogin
from comm import SessionCheck
sys.path.append('/flash/system/bin')
from bhcomm import StrClas
from generating_log import system_log
#函数是EncodeStr DecodeStr
from comm import EncodeStr
from comm import DecodeStr
from logbase import defines
from logbase import task_client
from logbase import common
from htmlencode import checkhostaccount
from htmlencode import checkaccount

import base64

from flask import request,Blueprint,render_template,send_from_directory # 

import xml.etree.ElementTree as ET
from htmlencode import parse_sess,check_role
search = Blueprint('search',__name__)
ERRNUM_MODULE_search = 10000
reload(sys)
sys.setdefaultencoding('utf-8')
module ='数据检索'
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
###所有协议

def proto_all():
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
	#debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')
	
	curs.close()
	conn.close()
	return result

###检索页面 父框架
@search.route("/search_frame", methods=['GET', 'POST'])
def search_frame():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	taskid = request.args.get('t1')
	if taskid <0:
		taskid = 0
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	return render_template('search_frame.html',se=session,us=userCode,taskid=taskid)
###检索页面
@search.route("/search_index", methods=['GET', 'POST'])
def search_index():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	taskid = request.args.get('t1')
	if taskid <0:
		taskid = 0
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
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ERRNUM_MODULE_host + 3, ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ERRNUM_MODULE_host + 4, ErrorEncode(e.args[1]))
		
	sql = "select public.\"PGetLogFieldConfig\"(1);";
	#debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	#debug(str(results));
	service_1 = ""
	results_json = json.loads(results)
	for result in results_json:
		service_1 = service_1 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
	service_1 = service_1[:-1]
	
	sql = "select public.\"PGetLogFieldConfig\"(2);";
	#debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	service_2 = ""
	results_json = json.loads(results)
	for result in results_json:
		service_2 = service_2 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
	service_2 = service_2[:-1]
	
	sql = "select public.\"PGetLogFieldConfig\"(3);";
	#debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	service_3 = ""
	results_json = json.loads(results)
	for result in results_json:
		service_3 = service_3 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
	service_3 = service_3[:-1]
	
	
	curs.close()
	conn.close()
	
	
	return render_template('search.html',se=session,us=userCode,taskid=taskid,service_1=service_1,service_2=service_2,service_3=service_3)
###检索页面
@search.route("/_search_index", methods=['GET', 'POST'])
def _search_index():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	taskid = request.args.get('t1')
	tasktype = request.form.get('tasktype')
	flag_from_index = request.form.get('i1')
	if taskid <0:
		taskid = 0
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	t = 'search.html'
	if flag_from_index <0:
		flag_from_index = ''
	if tasktype == '0':
		t = 'search_index.html'
		   
	return render_template(t,se=session,us=userCode,taskid=taskid,flag_from_index=flag_from_index)	

@search.route("/_search_index1", methods=['GET', 'POST'])
def _search_index1():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	taskid = request.args.get('t1')
	tasktype = request.args.get('tasktype')
	flag_from_index = request.args.get('i1')
	if taskid <0:
		taskid = 0
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	t = 'search.html'
	if flag_from_index <0:
		flag_from_index = ''
	if tasktype == '0':
		t = 'search_index.html'

	return render_template(t,se=session,us=userCode,taskid=taskid,flag_from_index=flag_from_index)

##检索结果
@search.route("/search_result", methods=['GET', 'POST'])
def search_result():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	taskid = request.args.get('t1')
	btn_status = request.args.get('t2')
	from_flag = request.args.get('f1')
	
	tasktype = request.args.get('t3')
	name = request.args.get('t4')
	task_page = request.args.get('tp1') ##历史任务的页码
	current_page = request.args.get('p1') ###当前页
	if tasktype < 0:
		tasktype = ""
	if name < 0:
		name = ""
	if task_page <0:
		task_page = 1
	else:
		task_page = int(task_page)
		
	if current_page <0:
		current_page = 1
	else:
		current_page = int(current_page)
	
	if btn_status < 0:
		btn_status = ""
	if taskid <0 or taskid =='None':
		taskid = 0
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if btn_status != '' and str(btn_status).isdigit() == False:
		return '',403 
		
	if from_flag and checkhostaccount(from_flag) == False:
		return '',403 
	
	if taskid and str(taskid).isdigit() == False:
		return '',403 
		
	if tasktype:
		if str(tasktype).isdigit() == False:
			return '',403
	if name != '' and checkhostaccount(name) == False:
		return '',403 
		
	if task_page:
		if str(task_page).isdigit() == False:
			return '',403		
	if current_page:
		if str(current_page).isdigit() == False:
			return '',403
			
	if from_flag == 'monitor':

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
			sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (userCode);
			#debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0]
		if (results & 1)>0:
			t = "monitorWhite.html"
		else:
			t = "monitor.html"
		
		_power=PGetPermissions(userCode)
		_power=str(_power)
		_power_json = json.loads(_power);
		monitor_flag1 = 0
		monitor_flag2 = 0
		for one in _power_json:
	 		if one['SubMenuId'] == 1:#数据监控
	 			if one['Mode'] == 2:#管理
	   				monitor_flag1 = 2
	                        else:
	 				monitor_flag1 = 1
	  		elif one['SubMenuId'] == 7:#系统监控
		                if one['Mode'] == 2:#管理
		                         monitor_flag2 = 2
		                else:
		                         monitor_flag2 = 1
		return render_template(t,us=userCode,se=session,a4=btn_status,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2)
	elif from_flag == 'data_dis_info':
		_power=PGetPermissions(userCode)
		_power=str(_power)
		_power_json = json.loads(_power);
		monitor_flag1 = 0
		monitor_flag2 = 0
		for one in _power_json:
	 		if one['SubMenuId'] == 1:#数据监控
	 			if one['Mode'] == 2:#管理
	   				monitor_flag1 = 2
	                        else:
	 				monitor_flag1 = 1
	  		elif one['SubMenuId'] == 7:#系统监控
		                if one['Mode'] == 2:#管理
		                         monitor_flag2 = 2
		                else:
		                         monitor_flag2 = 1
		return render_template('data_distribution_info.html',us=userCode,se=session,tasktype=tasktype,a1=name,a4=btn_status,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2)
	else:
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ERRNUM_MODULE_host + 3, ErrorEncode(e.args[1]))
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ERRNUM_MODULE_host + 4, ErrorEncode(e.args[1]))
			
		sql = "select public.\"PGetLogFieldConfig\"(1);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		#debug(str(results));
		service_1 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_1 = service_1 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_1 = service_1[:-1]
		
		sql = "select public.\"PGetLogFieldConfig\"(2);";
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_2 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_2 = service_2 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_2 = service_2[:-1]
		
		sql = "select public.\"PGetLogFieldConfig\"(3);";
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_3 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_3 = service_3 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_3 = service_3[:-1]
		
		curs.close()
		conn.close()
		return render_template('search_result.html',se=session,us=userCode,taskid=taskid,from_flag=from_flag,task_page=task_page,current_page=current_page,service_1=service_1,service_2=service_2,service_3=service_3)
##主机组页面
@search.route("/search_hostgroup", methods=['GET', 'POST'])
def search_hostgroup():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	path=request.args.get('p1')
	if path < 0 :
		path = '0'
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	return render_template('search_hostgroup.html',se=session,path =path)

##开始检索，创建任务
@search.route("/search_action", methods=['GET', 'POST'])
def search_action():
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
	taskid = request.form.get('s1')
	json_condition = request.form.get('s2')
	tasktype = request.form.get('s3') ### 0->检索 1->保存模板
	md5_str = request.form.get('m1')
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(json_condition);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	if taskid <0 or taskid =="":
		taskid = 0
	else:
		taskid = int(taskid)
		
	if tasktype <0 or tasktype =="":
		tasktype = 0
	else:
		tasktype = int(tasktype)
		
	if json_condition <0 or json_condition =="":
		json_condition = []
	
	oper = request.form.get('s8') ###堡垒管理   ###	if not system_log(user,oper,msg,module):
												#		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	if oper < 0:
		oper = '';
	
	###解析 json格式
	'''
	var json_condition ={
		"type":SYSTEM, //NORMAL SESSION  SYSTEM
		"data":[
			{
				"operate":"xtime_00",
				"translate:"编号",
				"condition":[
					{
						"action":"between",
						"value":"2017-10-9 00:00:00;2017-10-9 23:59:59"
					}
				]
				
			}
		]
	}
	'''
	try:
		
		##解析条件结束
		if tasktype == 0:
			if_disable = request.form.get('s9');
			json_condition = json.loads(json_condition)
			type = json_condition['type']
			datas = json_condition['data']
			hostgrp = []
			### 编写 
			#debug(str(datas))
			condition = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<Search>\n\t<KeyLogType>%s</KeyLogType>\n\t<KeyRule>\n" %(type)
			tmpstr = ""
			for data in datas:
				operate = data['operate']
				conditions =  data['condition']
				tmpstr = tmpstr + "\t\t<KeyCondition field=\"%s\" index=\"%s\">\n" %(operate.split('_')[0],operate.split('_')[1])
				for cond in conditions:
					if(operate.find('xtime') >=0 and (not operate == 'xtime_00') and (not operate == 'xtime_03' )): ##除去 编号 和标识
						##转化 时间戳
						if(cond['value'].find(';')>=0):
							value = str(int(time.mktime(time.strptime(cond['value'].split(';')[0], '%Y-%m-%d %H:%M:%S')))) + ";" + str(int(time.mktime(time.strptime(cond['value'].split(';')[1], '%Y-%m-%d %H:%M:%S'))))
						else:
							value = str(int(time.mktime(time.strptime(cond['value'], '%Y-%m-%d %H:%M:%S'))))
					elif operate =='int64_15':
						value = int('0x'+str(cond['value']),16);
					else:
						value = cond['value']
					if(cond['action'] == 'group'):
						hostgrp.append(value)
						
					not_flag ='' 
					if cond['action'].find('not') >=0:
						cond['action'] = cond['action'].replace('not ','')
						not_flag = 'not="y"'
					
					#tmpstr = tmpstr + "\t\t\t<value %s action=\"%s\">%s</value>\n" %(not_flag,cond['action'],cgi.escape(value).replace('\'',"&apos;").replace('"',"&quot;"))
					tmpstr = tmpstr + "\t\t\t<value %s action=\"%s\">%s</value>\n" %(not_flag,cond['action'],value)
					
				tmpstr = tmpstr + "\t\t</KeyCondition>\n"
			
			
			condition = condition + tmpstr +"\t</KeyRule>\n" 
			
			try:
				conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
			except pyodbc.Error,e:
				msg ='系统异常: %s(%d)' %(ERRNUM_MODULE_host + 3, ErrorEncode(e.args[1]))
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ERRNUM_MODULE_host + 3, ErrorEncode(e.args[1]))
			try:
				curs = conn.cursor()
			except pyodbc.Error,e:
				conn.close()
				msg ='系统异常: %s(%d)' %(ERRNUM_MODULE_host + 4, ErrorEncode(e.args[1]))
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ERRNUM_MODULE_host + 4, ErrorEncode(e.args[1]))
			condition_sql = '\t<KeyLogType>%s</KeyLogType>\n\t<KeyRule>\n'+ tmpstr+'\t</KeyRule>\n'
			sql = "select public.\"PGetDataRetrievalTaskByCond\"('%s',E'%s');" %(userCode,MySQLdb.escape_string(condition.replace('%','\\%')).decode('utf-8'))
			#debug("sss")
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg ='系统异常: %s(%d)' %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			results = curs.fetchall()[0][0]
			if results == None:
				pass
			else:
				results = json.loads(results)
				#debug(str(results))
				if results[0]['TaskId'] == 0:
					pass
				else:
					curs.close()
					conn.close()
					msg ='成功'
					if not system_log(userCode,oper,msg,module+">条件检索"):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":true,\"jump\":true,\"TaskId\":%d,\"Status\":%d,\"CancelStatus\":%d}"% (results[0]['TaskId'],results[0]['Status'],results[0]['CancelStatus'])
			
			#debug("123")
			###获取当前 类型的所有字段 PGetLogFieldConfig		
			if(type == 'NORMAL'):
				sql = "select public.\"PGetLogFieldConfig\"(1);";
			elif(type == 'SESSION'):
				sql = "select public.\"PGetLogFieldConfig\"(2);";
			elif(type == 'SYSTEM'):
				sql = "select public.\"PGetLogFieldConfig\"(3);";
			else:
				sql = "select public.\"PGetLogFieldConfig\"(1);"; ###暂定1
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
			results = curs.fetchall()[0][0]
			if results:
				results =  results.encode('utf-8')
			else:
				results=[]
			Column_list = json.loads(results)
			tmpstr ="\t<Column>\n"
			for column in Column_list:
				tmpstr = tmpstr +"\t\t<value name=\"%s\">%s</value>\n" %(column['Content'],column['Translation'])
			tmpstr = tmpstr + "\t</Column>\n"
			condition = condition + tmpstr 
			##获取字段结束
			
			###获取所有 协议
			results = proto_all()
			tmpstr = "\t<Proto>\n"
			proto_list = json.loads(results)['data']
			if proto_list == None:
				proto_list = []
			for proto in proto_list:
				tmpstr =  tmpstr + "\t\t<value name=\"%s\">%d</value>\n" %(proto['ProtocolName'],proto['ProtocolId'])
			tmpstr =  tmpstr + "\t</Proto>\n"
			condition = condition + tmpstr
			##获取协议结束
			
			tmpstr = "\t<Perm>\n"
			if(type != 'SYSTEM'):
				###获取当前用户的服务器管理权限 所有主机  PGetManagedScope
				sql = "select public.\"PGetManagedScope\"('%s');" %(userCode)
				try:
					curs.execute(sql)
				except pyodbc.Error,e:
					curs.close()
					conn.close()
					msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					if not system_log(userCode,oper,msg,module+">条件检索"):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				results = curs.fetchall()
				#debug(sql)
				
					
				if not len(results) == 0:
					#results = results.encode('utf-8')
					manageScope_list = json.loads(results[0][0].encode('utf-8'))
					MHostList = manageScope_list['MHostList']
					MIPList = manageScope_list['MIPList']
					if MHostList == None:
						MHostList = []
					if MIPList == None:
						MIPList = []	
					for MHost in MHostList:
						tmpstr =  tmpstr + "\t\t<value>%s</value>\n" %(MHost['HostIP'])
					for MIP in MIPList:
						tmpstr =  tmpstr + "\t\t<value>%s;%s</value>\n" %(MIP['StartIP'],MIP['EndIP'])
			
						
			tmpstr =  tmpstr + "\t</Perm>\n"
			condition = condition + tmpstr
			##获取管理权限结束
			
			###获取 当前主机组下的所有主机
			tmpstr = ""

			for group in hostgrp:
				tmpstr = tmpstr +  "\t\t<KeyGroup name=\"%s\">\n" % (group)
				sql = "select public.\"PGetHostList\"(%s);" %(group)
				#debug(sql)
				curs.execute(sql)
				results = curs.fetchall()
				if results[0][0] == None:
					tmpstr = tmpstr + "\t\t</KeyGroup>\n"
					continue
				else:					
					results = results[0][0].encode('utf-8')
				results = json.loads(results)
				for host in results:
					tmpstr = tmpstr + '\t\t\t<value>%s</value>\n' %(host['HostIP'])
				tmpstr = tmpstr + "\t\t</KeyGroup>\n"
				
			tmpstr = "\t<Group>\n"+tmpstr +"\t</Group>\n" 
			condition = condition + tmpstr
			##获取主机组结束
			
			##获取主机名和IP
			'''
			[
				{
					"HostIP": "192.168.7.1",
					"HostId": 30,
					"HostName": "ddd"
				}
			]
			
			tmpstr = ""
			sql = "select public.\"PGetHost\"(null,true,'%s');" %(userCode)
			#debug(sql)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
			results = curs.fetchall()
			if results[0][0] !=None:
				results = results[0][0].encode('utf-8')
			else:
				results = '[]'
			results = json.loads(results);
			for host in results:
				tmpstr = tmpstr + '\t\t<value name=\"%s\">%s</value>\n' %(host['HostName'],host['HostIP'])
				
			tmpstr = "\t<Host>\n"+tmpstr +"\t</Host>\n"
			condition = condition + tmpstr
			'''
			##获取主机结束
			###三权分立 if_disable 1-2-1
			perm_list = if_disable.split('-');
			tmpstr = "";
			# 三权分立 8->主机操作(操作、会话) 9->运维管理(堡垒管理-运维部分) 11->堡垒管理(堡垒管理-非运维用户部分)
			if type == 'SYSTEM':
				if (perm_list[1] == '2' and perm_list[2] == '2'):
					pass;
				else:			
					if perm_list[1] == '2':
						clas = 'N';
					else:
						clas = 'Y';
					##获取用户名
					#if clas =='Y':
					#sql = 'select public."PGetRole"(null,null,FALSE,null,null,null,\'{"submenuname":"运维管理"}\',\'{}\');';
					sql = 'select public."PGetRole"(null,null,FALSE,null,null,null,\'{"submenuname":"堡垒管理"}\',\'{}\');';
					#else:
					#	sql = 'select public."PGetRole"(null,null,FALSE,null,null,null,\'{"submenuname":"堡垒管理"}\',\'{}\');';
					try:
						curs.execute(sql.decode('utf-8'))
						debug(sql)
					except pyodbc.Error,e:
						curs.close()
						conn.close()
						msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
						if not system_log(userCode,oper,msg,module+">条件检索"):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					results = curs.fetchall()[0][0]
					debug(str(results))
					results_json = json.loads(results);
					json_data = results_json['data'];
					for da in json_data:
						RoleId = da['RoleId']
						sql = 'select  public."User"."UserCode" from public."User"  where  public."User"."UserId" IN(select public."UserRole"."UserId" from public."UserRole" where public."UserRole"."RoleId"=%d) ;' %(RoleId)
						try:
							curs.execute(sql)
						except pyodbc.Error,e:
							curs.close()
							conn.close()
							msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
							if not system_log(userCode,oper,msg,module+">条件检索"):
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
						results_tmp = curs.fetchall()
						for utmp in results_tmp:
							tmpstr = tmpstr + '\t\t<value name=\"%s\">%s</value>\n' %(utmp[0].encode('utf-8'),clas);
						tmpstr = tmpstr + '\t\t<value name=\"\">%s</value>\n' %(clas);	
				tmpstr = "\t<Account>\n"+tmpstr +"\t</Account>\n"
			condition = condition + tmpstr
			condition = condition + "</Search>\n"
			
			
			#插入数据
			sql = "select public.\"PSaveDataRetrievalTask\"(%d,E'%s',E'%s',E'{%s}');" %(0,userCode,MySQLdb.escape_string(condition).decode('utf-8'),(',').join(hostgrp))
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			results = curs.fetchall()
			#debug(str(results))
			if results:
				results = results[0][0].encode('utf-8')
			conn.commit()
			curs.close()
			conn.close()
			msg ='成功'
			if not system_log(userCode,oper,msg,module+">条件检索"):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"			
			return results
		elif tasktype == 1:		
			try:
				conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
			except pyodbc.Error,e:
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ERRNUM_MODULE_host + 3, ErrorEncode(e.args[1]))
			try:
				curs = conn.cursor()
			except pyodbc.Error,e:
				conn.close()
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ERRNUM_MODULE_host + 4, ErrorEncode(e.args[1]))
			template_name = request.form.get('s4')
			
			##判断是否存在相同的名称 
			sql = "select \"Id\" from public.\"DataRetrievalTemplate\" where \"Name\" =E'%s' and \"UserCode\" ='%s'; " %(template_name,userCode)
			#debug(sql)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}"% ( sys._getframe().f_lineno)
			results = curs.fetchall()
			if results:
				id = results[0][0]
			else:
				id = 0
				
			tmpstr = '{"Id": %d,"Name": "%s","UserId": null,"UserCode": "%s","Condition": "%s"}' %(id,template_name,userCode,base64.b64encode(json_condition))
			sql ="select public.\"PSaveDataRetrievalTemplate\"(E'%s');"%(MySQLdb.escape_string(tmpstr).decode('utf-8'))
			#debug(sql)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module+">条件检索"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			results = curs.fetchall()[0][0].encode('utf-8')
			conn.commit()
			curs.close()
			conn.close()
			result_json = json.loads(results);
			if(result_json['Result'] == True):
				msg ='成功'
			else:
				msg = result_json['ErrMsg']
			if not system_log(userCode,oper,msg,module+">条件检索"):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"			
			return results
		
	except:
		msg ='系统异常: %s(%d)'% (ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
		if not system_log(userCode,oper,msg,module+">条件检索"):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"info\":\"系统异常: (%d)\"}" %(sys._getframe().f_lineno)
	###编写xml格式
	'''
	<?xml version="1.0" encoding="UTF-8"?>
	<Search>
		<KeyLogType>NORMAL</KeyLogType>
		<KeyRule>
			<KeyCondition field="xtime" index="01">
				<value action="between">1507564801;1507649039</value>
			</KeyCondition>
		</KeyRule>
		<Column>
			<value name="xtime_00">编号</value>
			<value name="xtime_01">入库时间</value>
			<value name="xtime_02">发生时间</value>
			<value name="xtime_03">会话标识</value>
			<value name="xtime_04">起始时间</value>
			<value name="int08_00">属性</value>
		</Column>
		<Perm>
		</Perm>
	</Search>
	'''
	###回显 模板的条件
@search.route("/search_show_condition", methods=['GET', 'POST'])
def search_show_condition():
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
	template_id = request.form.get('t1')
	if template_id == '0':
		return "[]"
	if template_id == '-1':
		template_id =  "null"
	elif not template_id.isdigit():
		return '',403
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select public.\"PGetDataRetrievalTemplate\"(%s,'%s')" %(template_id,userCode);
	#debug(sql);
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	if results[0][0] == None:
		results = "[]"
	else:
		results = results[0][0].encode('utf-8')
		results = json.loads(results)
		###debug(str(results))
		for result in results:
			###debug(base64.b64decode(result['Condition']))
			result['Condition'] = base64.b64decode(result['Condition']).encode('utf-8')
		#debug(str(results))
		results = json.dumps(results)
	curs.close()
	conn.close()	
	return results

def parse_condition(taskid,userCode):
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		sql = 'select public."PGetDataRetrievalTask"(%d,\'%s\',1,0);' %(taskid,userCode)
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#debug('1')
		results = curs.fetchall()[0][0].encode('utf-8')
		#debug('2')
		cond = json.loads(results)['data'][0]['Condition']
		
		#debug('3')
		try:
			root = ET.fromstring(cond);
			if len(cond) < 2:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: 条件格式不正确(%d)\"}"% (sys._getframe().f_lineno)
		except:
			return "{\"Result\":true,\"info\":\"\"}"
		#debug('4')
		nodestr = ""
		for node in root[1]:
			field = node.get('field')
			index = node.get('index')
			temstr = ""
			for snode in node:
				action = snode.get('action');
				n = snode.get('not');
				value = snode.text;
				if n == 'y':
					action = 'not ' + action
					
				if field == 'xtime':
					if index == "00" or index == "03": ##编号和标识 不需要转时间						
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,value)
					else: ##time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(qtime[-1][0]))
						if action == "between":##区间
							start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value.split(';')[0])));
							end = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value.split(';')[1])));
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,start +';' + end)
						else:
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value))))
				elif field == 'ip':
					if action == 'group':
						###组存在的路径 和组名					
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,value)
					else:
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,value)				
				else:
					if root[0].text == 'SYSTEM':
						if field =='int08' or index =='12':
							if StrClas(field,index,(value),1,1) =='':
								tmp_str = '无'
							else:
								tmp_str = StrClas(field,index,(value),1,1)
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,tmp_str)
						elif field =='int32' and index == "01" : ###日志类型
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,(value))	
								
						else:
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,StrClas(field,index,(value).replace('"','\\"').replace('\\','\\\\'),1,1))
					else:
						if field =='int32' and index == "01" : ###日志类型
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,(value))
						elif field =='int64' and index == "15" : ###
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,StrClas(field,index,int(value),0,1))
						else:
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,StrClas(field,index,(value).replace('"','\\"').replace('\\','\\\\'),0,1))		
					#temstr = temstr + '{"action":"%s","value":"%s"},' %(action,cgi.escape(value).replace('\'',"&apos;").replace('"',"&quot;").replace('\\','\\\\'))	
			temstr = temstr[:-1]			
			nodestr = nodestr + '{"operate":"%s","condition":[%s]},' %(field + "_" + index,temstr)
		nodestr = nodestr[:-1]
		condition_json = '{\"taskid\":%d,"type":"%s","data":[%s]}' %(taskid,root[0].text,nodestr)
		condition_json = "{\"Result\":true,\"info\":%s}" %(condition_json)
		curs.close()
		conn.close()
		return condition_json
	except:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
###回显 任务过来的 条件
@search.route("/search_task_condition", methods=['GET', 'POST'])
def search_task_condition():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	taskid = request.form.get('t1')
	if taskid< 0 or taskid == "" or taskid == '0':
		return "{\"Result\":true,\"info\":[]}" 
	else:
		taskid = int(taskid);
	condition_json= parse_condition(taskid,userCode);
	
	#debug('5')
	return 	condition_json

def parse_condition_historytask(Condition):
	try:
		cond = Condition
		try:
			root = ET.fromstring(cond);
			if len(cond) < 2:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: 条件格式不正确(%d)\"}"% (sys._getframe().f_lineno)
		except:
			return "{\"Result\":true,\"info\":\"\"}"
		nodestr = ""
		for node in root[1]:
			field = node.get('field')
			index = node.get('index')
			temstr = ""
			for snode in node:
				action = snode.get('action');
				n = snode.get('not');
				value = snode.text;
				if n == 'y':
					action = 'not ' + action
					
				if field == 'xtime':
					if index == "00" or index == "03": ##编号和标识 不需要转时间						
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,value)
					else: ##time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(qtime[-1][0]))
						if action == "between":##区间
							start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value.split(';')[0])));
							end = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value.split(';')[1])));
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,start +';' + end)
						else:
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value))))
				elif field == 'ip':
					if action == 'group':
						###组存在的路径 和组名					
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,value)
					else:
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,value)				
				else:
					if(root[0].text == 'SYSTEM'):
						temstr = temstr + '{"action":"%s","value":"%s"},' %(action,StrClas(field,index,value.replace('"','\\"').replace('\\','\\\\'),1,1))
					else:
						if field =='int32' and index == "01" : ###日志类型
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,(value))
						else:
							temstr = temstr + '{"action":"%s","value":"%s"},' %(action,StrClas(field,index,(value).replace('"','\\"').replace('\\','\\\\'),0,1))		
					#temstr = temstr + '{"action":"%s","value":"%s"},' %(action,cgi.escape(value).replace('\'',"&apos;").replace('"',"&quot;").replace('\\','\\\\'))	
			temstr = temstr[:-1]			
			nodestr = nodestr + '{"operate":"%s","condition":[%s]},' %(field + "_" + index,temstr)
		nodestr = nodestr[:-1]
		condition_json = '{"type":"%s","data":[%s]}' %(root[0].text,nodestr)
		condition_json = "{\"Result\":true,\"info\":%s}" %(condition_json)
		return condition_json
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
	
###任务列表
@search.route("/get_search_task_list", methods=['GET', 'POST'])
def get_search_task_list():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		maxpage = int(request.form.get('t1'))
		curpage = int(request.form.get('t2'))
		select_all = int(request.form.get('t3'))
		offset = maxpage*(curpage-1)
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if select_all == 1:
			sql = "select public.\"PGetDataRetrievalTask\"(null,'%s',null,null);" %(userCode)
			#debug(sql);
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			#results = curs.fetchall()[0][0].encode('utf-8').replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;");
			results = curs.fetchall()[0][0].encode('utf-8')
			curs.close()
			conn.close()
			return results
		else:
			sql = "select public.\"PGetDataRetrievalTask\"(null,'%s',%d,%s);" %(userCode,maxpage,offset);
			#debug(sql);
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			#results = curs.fetchall()[0][0].encode('utf-8').replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;");
			results = curs.fetchall()[0][0].encode('utf-8')
			'''
			results_json = json.loads(results)
			for c_json in results_json['data']:
				taskid = int(c_json['TaskId']);
				##解析条件
				condition_json= parse_condition_historytask(c_json['Condition']);
				#debug(str(condition_json))
				condition_json = json.loads(condition_json)
				if condition_json['Result'] == True:
					c_json['c_json'] =condition_json['info']
				else:
					c_json['c_json'] ={"type":"未知类型","data":[]}
			results = json.dumps(results_json)
			'''
			curs.close()
			conn.close()
			return results
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)

		
@search.route("/history_condition", methods=['GET', 'POST'])
def history_condition():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		task_str = request.form.get('t1');
		
		task_list = task_str.split(',')
		result_json = {
			"Result":True,
			"info":[]
		}
		for taskid in task_list:
			if taskid != '' and str(taskid).isdigit() == False:
				return '',403 
				
			condition= parse_condition(int(taskid),userCode);
			#debug(str(condition))
			condition_json= json.loads(condition)
			
			if condition_json['Result'] == True:
				result_json['info'].append(condition_json['info'])
			else:
				result_json['info'].append({"taskid":taskid,"type":"未知类型","data":[]})
					
		#debug(str(result_json))
		return json.dumps(result_json)
	except:
		#debug(ErrorEncode(str(sys.exc_info()[0]),str(sys.exc_info()[1])))
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
		
###删除任务
@search.route("/delete_task", methods=['GET', 'POST'])
def delete_task():	
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(userCode, "主机操作") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	#删除检索任务：2018-03-07 14:47:59
	oper ='删除检索任务：'
	try:
		type = request.form.get('t1')
		id = request.form.get('t2')
		#debug(str(id))
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if (type == '1'):
			id_array = id[1:-1].split(',')
			SubmitTime = '';
			for id in id_array:
				###获取当前任务的状态 状态(0-队列中，1-执行中，2-检索成功，3-检索失败，4-导出队列中，5-导出执行中，6-导出成功，7-导出失败)
				###取消状态（0-正常状态，1-取消状态）  
				### 0 1  4  5 这几个状态删除是 只是取消 把 取消状态置为取消即可
				### 2 3 6 7 可以直接删除 
				sql = "select \"Status\",\"SubmitTime\" from private.\"DataRetrievalTask\" where \"TaskId\" = %d;" %(int(id))
				#debug(sql)
				curs.execute(sql)
				results = curs.fetchall()
				result = results[0][0]
				SubmitTime = results[0][1]
				oper += '检索时间(%s),' %(str(SubmitTime))
				if result in [0,1,4,5]:
					sql = "select public.\"PChangeDataRetrievalTaskStatus\"(%d,null,1);" %(int(id))
					#debug(sql)
					curs.execute(sql)
					id_array.remove(id)
				else:					
					curs.execute("select public.\"PDeleteDataRetrievalTask\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						conn.rollback();
						curs.close()
						conn.close()
						msg =results['ErrMsg']
						if not system_log(userCode,oper,msg,module+">历史任务"):
							return "{\"Result\":false,\"info\":\"生成日志失败\"}"
						return result
				
					
			###删除表
			try:
				conn1 = pyodbc.connect(StrSqlConn('BH_DATA'))
			except pyodbc.Error,e:
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			try:
				curs1 = conn1.cursor()
			except pyodbc.Error,e:
				conn1.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			for id in id_array:
				
				curs1.execute("select public.\"PDropQryTbl\"(%d);"%(int(id)))
				result = curs1.fetchall()[0][0]
				#debug(str(result))
				if str(result) == 'False':
					conn.rollback();
					curs.close()
					conn.close()
					
					conn1.rollback();
					curs1.close()
					conn1.close()
					msg = result['ErrMsg']
					if not system_log(userCode,oper,msg,module+">历史任务"):
						return "{\"Result\":false,\"info\":\"生成日志失败\"}"
					return result
					
			conn.commit()
			curs.close()
			conn.close()
			
			conn1.commit()
			curs1.close()
			conn1.close()
			msg = '成功'
			oper = oper[:-1]
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "{\"Result\":true}"
			
		else:
			sql = "select \"Status\",\"SubmitTime\" from private.\"DataRetrievalTask\" where \"TaskId\" = %d;" %(int(id))
			curs.execute(sql)
			results = curs.fetchall()
			result = results[0][0]
			SubmitTime = results[0][1]
			oper += '检索时间(%s)' %(str(SubmitTime))
			if result in [0,1,4,5]:
				sql = "select public.\"PChangeDataRetrievalTaskStatus\"(%d,null,1);" %(int(id))
				#debug(sql)
				curs.execute(sql)
				conn.commit()
				curs.close()
				conn.close()
			else:			
				curs.execute("select public.\"PDeleteDataRetrievalTask\"(%d);"%(int(id)))
				result = curs.fetchall()[0][0].encode('utf-8')
				conn.commit()
				curs.close()
				conn.close()
				###删除 表
				try:
					conn = pyodbc.connect(StrSqlConn('BH_DATA'))
				except pyodbc.Error,e:
					msg = '系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					if not system_log(userCode,oper,msg,module+">历史任务"):
						return "{\"Result\":false,\"info\":\"生成日志失败\"}"
					return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				try:
					curs = conn.cursor()
				except pyodbc.Error,e:
					conn.close()
					msg = '系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					if not system_log(userCode,oper,msg,module):
						return "{\"Result\":false,\"info\":\"生成日志失败\"}"
					return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				curs.execute("select public.\"PDropQryTbl\"(%d);"%(int(id)))
				result = curs.fetchall()[0][0].encode('utf-8')
				conn.commit()
				curs.close()
				conn.close()
				name = 'query_'+ str(id) + '.zip'
				path = '/usr/storage/.system/export/' +name ;
				content = "[global]\nclass = taskglobal\ntype = delfile\npath=%s\n" %(path)
				ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
				if ss == False:
					return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
				
			msg = '成功'
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return 'true'
	except:
		msg = '系统异常: %s(%d)'% (ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
		if not system_log(userCode,oper,msg,module+">历史任务"):
			return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)

###删除模板
@search.route("/delete_template", methods=['GET', 'POST'])
def delete_template():	
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if check_role(userCode, "主机操作") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	oper = request.form.get('o1')	
	if oper < 0:
		oper = '';
	try:
		id = request.form.get('t1')
		#debug(str(id))
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			if not system_log(userCode,oper,msg,module+">条件检索"):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			if not system_log(userCode,oper,msg,module+">条件检索"):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
				
		curs.execute("select public.\"PDeleteDataRetrievalTemplate\"(%d);"%(int(id)))
		result = curs.fetchall()[0][0].encode('utf-8')
		conn.commit()
		curs.close()
		conn.close()
		result_json = json.loads(result);
		if(result_json['Result'] == True):
			msg ='成功'
		else:
			msg = result_json['ErrMsg']
		if not system_log(userCode,oper,msg,module+">条件检索"):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
		return result
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)	

###获取日志字段
@search.route("/get_logfield", methods=['GET', 'POST'])
def get_logfield():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		logtype = request.form.get('o1')
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if(logtype == 'NORMAL'):
			sql = "select public.\"PGetLogFieldConfig\"(1);";
		elif(logtype == 'SESSION'):
			sql = "select public.\"PGetLogFieldConfig\"(2);";
		elif(logtype == 'SYSTEM'):
			sql = "select public.\"PGetLogFieldConfig\"(3);";
		else:
			sql = "select public.\"PGetLogFieldConfig\"(null);"; ###暂定1
		
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		curs.close()
		conn.close()
		return results
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
	

###日志列表
@search.route("/get_log_list", methods=['GET', 'POST'])
def get_log_list():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		maxpage = int(request.form.get('t1'))
		curpage = request.form.get('t2')
		taskid = int(request.form.get('t3'))
		logtype = request.form.get('t4')
		fieldsname = request.form.get('t5')
		
		if curpage <0 or curpage == "":
			curpage = 1
		else:
			curpage = int(curpage)
		
		offset = maxpage*(curpage-1)
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_DATA'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
		if(logtype == 'NORMAL'):
			type = 1;
		elif(logtype == 'SESSION'):
			type = 2;
		elif(logtype == 'SYSTEM'):
			type = 3;
		else:
			type = 1;

		sql = "select public.\"PGetLogData\"(%d,%d,'%s',%d,%d);" %(taskid,type,fieldsname,maxpage,offset);
		
		#debug(sql);
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#results = curs.fetchall()[0][0].encode('utf-8').replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;");
		results = curs.fetchall()
		if results:
			if results[0][0] ==None:
				results ='[]'
			else:
				results = results[0][0].encode('utf-8')
		else:
			results ='[]'
		
		curs.close()
		conn.close()
		###debug(str(results))
		return results
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)	

###获取列表显示的日志字段
@search.route("/get_displaylogfield", methods=['GET', 'POST'])
def get_displaylogfield():	
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		logtype = request.form.get('o1')
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if(logtype == 'NORMAL'):
			sql = "select public.\"PGetUserLogFieldConfig\"('%s',1);" %(userCode)
		elif(logtype == 'SESSION'):
			sql = "select public.\"PGetUserLogFieldConfig\"('%s',2);" %(userCode)
		elif(logtype == 'SYSTEM'):
			sql = "select public.\"PGetUserLogFieldConfig\"('%s',3);" %(userCode)
		else:
			sql = "select public.\"PGetUserLogFieldConfig\"('%s',1);" %(userCode)
		
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		curs.close()
		conn.close()
		return results
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
	
###获取日志 数量
@search.route("/get_totalrow", methods=['GET', 'POST'])
def get_totalrow():	
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		taskid = request.form.get('t1')
		if taskid != '' and str(taskid).isdigit() == False:
			return '',403 
			
		taskid = int(request.form.get('t1'))	
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "select \"Status\" from private.\"DataRetrievalTask\" where \"TaskId\" = %d;" %(taskid)
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		result = curs.fetchall()
		Status = result[0][0]
		curs.close()
		conn.close()
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_DATA'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "select public.\"PGetLogCount\"(%d);" %(taskid)
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		result = curs.fetchall()
		Count = result[0][0]
		curs.close()
		conn.close()
		
		return "{\"Result\":true,\"Count\":%d,\"Status\":%d}" % (Count,Status)
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
	
###导出
@search.route("/export_result", methods=['GET', 'POST'])
def export_result():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if check_role(userCode, "主机操作") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	oper ='导出检索结果'
	try:
		taskid = request.form.get('t1')
		if taskid != '' and str(taskid).isdigit() == False:
			return '',403 
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			msg = '系统异常: %s(%d)' % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			msg = '系统异常: %s(%d)' % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		###导出 	
		sql = "select public.\"PChangeDataRetrievalTaskStatus\"(%d,4,null);" %(int(taskid))
		curs.execute(sql)
		result = curs.fetchall()[0][0].encode('utf-8')
		conn.commit()
		curs.close()
		conn.close()
		msg = '成功' 
		if not system_log(userCode,oper,msg,module+">历史任务"):
			return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return result
	except:
		msg = '系统异常: %s(%d)' %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
		if not system_log(userCode,oper,msg,module+">历史任务"):
			return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
'''
	<script src="/manage/js/jquery.min.js"></script><script src="/manage/js/jquery.easing.js"></script><script src="/manage/js/layer.js"></script><link rel="stylesheet" href="/manage/css/style.css"><script src="/manage/js/common.js"></script><script src="/manage/js/common_e.js"></script>
layer.open({
			type:1,
			title:title,
			content:'<div class="layer-alert"><i class="'+class_name+'"></i>'+result+'</div>',
			btn:['确&nbsp;&nbsp;定'],
			btnAlign:'c',
			closeBtn: false,
			skin:'layer-custom',
			area:['380px','310px'],
			move: false,
			resize: false,
			btn1:function(i){
				layer.close(i);
				obj.focus();
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
			        }

			}
		});
'''	
##下载
@search.route("/download_result", methods=['GET', 'POST'])
def download_result():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if check_role(userCode, "主机操作") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if error < 0:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script src=\"/manage/js/jquery.min.js\"></script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'下载数据','系统繁忙(%d)')</script></html>" % (sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script src=\"/manage/js/jquery.min.js\"></script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'下载数据','非法访问(%d)')</script></html>" % (sys._getframe().f_lineno)
		else:
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script src=\"/manage/js/jquery.min.js\"></script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'下载数据','系统超时(%d:%d)')</script></html>" % (sys._getframe().f_lineno)
	
	try:
		oper ='下载检索结果'
		taskid = request.form.get('t1')
		name = 'query_'+ taskid + '.zip'
		down_dir = '/usr/storage/.system/export/' ;
		if not os.path.exists(down_dir + name ):
			msg = '文件不存在' 
			if not system_log(userCode,oper,msg,module+">历史任务"):
				return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><link rel=\"stylesheet\" href=\"/manage/css/style.css\" type=\"text/css\" /><link rel=\"stylesheet\" href=\"/manage/css/passport.css\" type=\"text/css\" /><script type=\"text/javascript\" src=\"/manage/js/jquery.min.js\"></script><script type=\"text/javascript\" src=\"/manage/js/dialog-plus.js\"></script><body><div class=\"dialog-cont\" id= \"DAlert\"><div class=\"fwarn\"><i></i><div id=\"aler_text\" align=\"center\">文件不存在(%d)</div><a class=\"btn\" herf=\"javascript:;\">确定</a></div></div></body><style>.ui-dialog-header button.ui-dialog-close{display:none!important};a{text-decoration:blink;}a:hover{text-decoration:blink;}</style><script>var $Alert  = $(\"#DAlert\").show();var d = dialog({title:\"警告\",content:$Alert,id:\"Alert\"});d.showModal();$(\"a.btn\",$Alert).unbind().bind(\"click\",function(){d.close().remove();top.location.href='/';;});</script></html>" % (sys._getframe().f_lineno)
		msg = '成功' 
		if not system_log(userCode,oper,msg,module+">历史任务"):
			return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return send_from_directory(down_dir,name,as_attachment=True)
	except:
		msg = '系统异常：' %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno,)
		if not system_log(userCode,oper,msg,module+">历史任务"):
			return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常：%s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
	
###所有主机
@search.route("/get_search_host", methods=['GET', 'POST'])
def get_search_host():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "select public.\"PGetHostList\"(0);"
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		result = curs.fetchall()[0][0].encode('utf-8')
		
		curs.close()
		conn.close()
		return result
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)	

@search.route("/get_search_proto", methods=['GET', 'POST'])
def get_search_proto():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		result = proto_all()
		return result
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
		
###获取 主机组名
@search.route("/get_host_name", methods=['GET', 'POST'])
def get_host_name():
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	id = request.form.get('g1')
	type = request.form.get('t1')
	if type <0 or type =="":
		type = 0;
	else:
		type = int(type)
		
	if type == 0:
		sql = "select \"HGName\" from public.\"HGroup\" where \"HGId\" = %s;" %(id)
	elif type == 1:
		sql = "select \"HostName\" from public.\"Host\" where \"HostIP\" = '%s';" %(id)
	else:
		sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\" = %s;" %(id)
	curs.execute(sql)
	results = curs.fetchall()
	if results:
		name = results[0][0].encode('utf-8')
	else:
		name = ""
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":\"%s\"}"% (name)	
def get_name(type,id): # 0->主机组  1->主机 （ip->name） 2->协议
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return -1
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return -1
		
	if type == 0:
		sql = "select \"HGName\" from public.\"HGroup\" where \"HGId\" = %d;" %(int(id))
	elif type == 1:
		sql = "select \"HostName\" from public.\"Host\" where \"HostIP\" = '%s';" %(str(id))
	else:
		sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\" = %d;" %(int(id))
		
	curs.execute(sql)
	results = curs.fetchall()
	if results:
		name = results[0][0].encode('utf-8')
		if(type == 1):
			name = name +"("+str(id)+")"
	else:
		name = str(id);
		
	curs.close()
	conn.close()
	return name
		
### 获取列表结果 控件版本
@search.route("/get_log_list_mm", methods=['GET', 'POST'])
def get_log_list_mm():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		maxpage = int(request.args.get('limit'))
		#curpage = request.args.get('t2')
		taskid = int(request.args.get('t3'))
		logtype = request.args.get('t4')
		fieldsname = request.args.get('t5')
		curpage = request.args.get('page')
		
		if curpage <0 or curpage == "":
			curpage = 1
		else:
			curpage = int(curpage)
		
		if fieldsname:
			fieldsname_tmp = fieldsname.split(',');
			for n in fieldsname_tmp:
				if checkaccount(n) == False:
					return '',403 
		
		offset = maxpage*(curpage-1)
		
		proto_list = proto_all();
		proto_list = json.loads(proto_list)['data']
		if proto_list == None:
			proto_list = []
		pro_l = []
		for proto in proto_list:
			pro_l.append([])
			pro_l[-1].append(proto['ProtocolId']);
			pro_l[-1].append(proto['ProtocolName']);
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_DATA'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
		if(logtype == 'NORMAL'):
			type = 1;
		elif(logtype == 'SESSION'):
			type = 2;
		elif(logtype == 'SYSTEM'):
			type = 3;
		else:
			type = 1;

		sql = "select public.\"PGetLogData\"(%d,%d,E'%s',%d,%d);" %(taskid,type,fieldsname,maxpage,offset);
		
		#debug(sql);
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#results = curs.fetchall()[0][0].encode('utf-8').replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;");
		results = curs.fetchall()
		if results:
			if results[0][0] ==None:
				results ='[]'
			else:
				results = results[0][0].encode('utf-8')
				
				results_json = json.loads(results)
				for one in results_json:
					if(logtype == 'SYSTEM'):
						one['int32_01'] = StrClas('int32','01',int(one['int32_01']),1,1)
						if(one['int08_12'] > 0 ): ##未启用告警
							clas = 1
						else:
							clas = 0
						one['int08_12'] = StrClas('int08','12',int(one['int08_12']),1,1)
						for o in one:
							if o == 'int08_11':
								if clas == 1:
									if one[o] == 1:
										one[o] = '已处理'
									elif one[o] == 0:
										one[o] = '未处理'
								else:
									one[o] = '';

					else:
						one['xtime_03'] = '%d' %(one['xtime_03'])
						if(one['int08_12'] > 0 ): ##未启用告警
							clas = 1
						else:
							clas = 0
						
						for pro in pro_l:
							if pro[0] == one['int32_01']:
								one['int32_01'] = pro[1];
						for o in one:
							field = o.split('_')[0];
							index = o.split('_')[1];
							#debug(field)
							#debug(index)
							if o.find('int08') >=0 and (index == '11' or index == '14' or index == '03' or index == '15'):
								one[o] = StrClas(field,index,str(one[o]),0,clas)
							if o == 'int64_15':
								#tmp = StrClas(fieldset[i][0],fieldset[i][1],int('0x'+str(value), 16),0,1);
								one[o] = StrClas(field,index,int(one[o]),0,1)
						if int(one['int16_00']) == 0:
							one['int16_00'] ='';			
						if int(one['int16_01']) == 0:
							one['int16_01'] ='';			
								
						one['DownloadEnable'] = False
						one['DeleteEnable'] = False
						one['IfReplay'] = False ##是否使用控件回放
						one['IfReplayDrawing'] = False ##回放  字符回放（ssh等） 图形回放（RDP等）
						#检查是否有回放文件
						if one['str32_28'] != "":
							one['DownloadEnable'] = True
							one['DeleteEnable'] = False
							##
							one['IfReplay'] = True;							
							pro = one['str32_28'].split('/')[-2].upper()
							if pro =="RDP" or pro =="ACC" or pro =="VNC" or pro =="X11":
								one['IfReplayDrawing'] = True	
						else:
							#检查日志类型字段是否是 FTP 或者 SFTP
							if one['int32_01'] == 'FTP' or one['int32_01'] == 'SFTP':
								#检查操作字段是否有 "Save" 字符串
								if one['str32_01'].find("Save") != -1:
									#debug(str(one))
									#检查传输文件是否存在
									#filename = one['str32_01'].split(" ")[1]
									filename = one['str32_01'].replace('Save ','',1)
									filepath = '/usr/storage/.system/transf/ftp/'
									fdir = filepath + filename
									#debug(fdir)
									if os.path.exists(fdir):
										one['DownloadEnable'] = True
										one['DeleteEnable'] = True
										#debug(str(one))

					one['search'] = True		
				#debug(str(results_json))			
				results = json.dumps(results_json)
				
		else:
			results ='[]'
		###获取当前数据总数
		curs.close()
		conn.close()
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_DATA'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "select public.\"PGetLogCount\"(%d);" %(taskid)
		#debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		result = curs.fetchall()
		Count = result[0][0]
		
		curs.close()
		conn.close()
		
		###拼接 json格式
		results_list = json.loads(results)
		result_json ={
			"page":curpage,
			"totalCount":Count,
			"items":[]
		}
		for one in results_list:
			if 'int64_14' in one.keys():
				one['int64_14']='%sB'%one['int64_14']
			result_json['items'].append(one)
		
		#debug(str(result_json))
		return json.dumps(result_json)
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d:%s)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)

### 保存 字段修改信息
@search.route("/ChangeLogFieldStatus", methods=['GET', 'POST'])
def ChangeLogFieldStatus():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		##data:{a0:{{se}},s1:$(this).prop('checked'),d1:_id,l1:logtype},
		field_json = request.form.get('s1')
		md5_str = request.form.get('m1')
		if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		else:
			md5_json = StrMD5(field_json);##python中的json的MD5
			if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		field_json = json.loads(field_json)
		field_json['loginusercode'] = userCode;
		field_str = json.dumps(field_json);
		sql = "select public.\"PChangeLogFieldStatus\"(E'%s');" %(MySQLdb.escape_string(field_str));
		
		#debug(sql);
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#results = curs.fetchall()[0][0].encode('utf-8').replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;");
		results = curs.fetchall()[0][0]
		conn.commit();
		curs.close()
		conn.close()
		return results
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d:%s)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)

##批量获取 任务列表的状态
@search.route("/get_search_status", methods=['GET', 'POST'])
def get_search_status():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:		
		taskstr = request.form.get('t1')
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		taskstatus = []
		for taskid in taskstr.split(','):
			sql = 'select "Status","CancelStatus","Count" from private."DataRetrievalTask" where "TaskId" = %s;' %(taskid)
			curs.execute(sql)
			results = curs.fetchall()
			if results == None or results[0] == None:
				status = 3
				CancelStatus = 0;
				count = 0;
			else:
				status = results[0][0]
				CancelStatus = results[0][1]
				count =results[0][2]
				
			taskstatus.append(str(status)+','+str(CancelStatus)+','+str(count))
		new_dict = dict(zip(taskstr.split(','), taskstatus))
		
		'''
		keys = [1, 2, 3, 4]
		values = [55, 56, 57, 58]	  
		new_dict = dict(zip(keys, values))
		'''
		return str(new_dict).replace('u','').replace('\'','"');
		
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d:%s)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
	
	
	
	
	
	
	
	
	
	
	
##下载证书
@search.route("/download_crt", methods=['GET', 'POST'])
def download_crt():
	try:
		#oper ='下载证书'
		#taskid = request.form.get('t1')
		name = 'ca.crt'
		down_dir = '/usr/ssl/certs/' ;
		if not os.path.exists(down_dir + name ):
		#	msg = '文件不存在' 
		#	if not system_log(userCode,oper,msg,module):
		#		return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><link rel=\"stylesheet\" href=\"/manage/css/style.css\" type=\"text/css\" /><link rel=\"stylesheet\" href=\"/manage/css/passport.css\" type=\"text/css\" /><script type=\"text/javascript\" src=\"/manage/js/jquery.min.js\"></script><script type=\"text/javascript\" src=\"/manage/js/dialog-plus.js\"></script><body><div class=\"dialog-cont\" id= \"DAlert\"><div class=\"fwarn\"><i></i><div id=\"aler_text\" align=\"center\">文件不存在(%d)</div><a class=\"btn\" herf=\"javascript:;\">确定</a></div></div></body><style>.ui-dialog-header button.ui-dialog-close{display:none!important};a{text-decoration:blink;}a:hover{text-decoration:blink;}</style><script>var $Alert  = $(\"#DAlert\").show();var d = dialog({title:\"警告\",content:$Alert,id:\"Alert\"});d.showModal();$(\"a.btn\",$Alert).unbind().bind(\"click\",function(){d.close().remove();top.location.href='/';;});</script></html>" % (sys._getframe().f_lineno)
		#msg = '成功' 
		#if not system_log(userCode,oper,msg,module):
		#	return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return send_from_directory(down_dir,name,as_attachment=True,attachment_filename='webca.crt')
	except:
	#	msg = '系统异常：' %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno,)
	#	if not system_log(userCode,oper,msg,module):
	#		return "{\"Result\":false,\"info\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常：%s(%d)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)	
	


def PGetPermissions(us):
        global ERRNUM_MODULE
        ERRNUM_MODULE = 3000
	#sess = request.form.get('a0')
        reload(sys)
        sys.setdefaultencoding('utf-8')
        #if sess < 0:
        #        sess = ""
        #client_ip = request.remote_addr
        #(error,us,mac) = SessionCheckLocal(sess,client_ip);
        #(error,us,mac) = SessionCheck(sess,client_ip);
        #if error < 0:
        #        return "{\"Result\":false,\"info\":\"系统异常(%d): %d\"}" %  (ERRNUM_MODULE_top + 1,error)
        #elif error > 0:
        #        if error == 2:
        #                return "{\"Result\":false,\"info\":\"非法访问(%d): %d\"}" % (ERRNUM_MODULE_top + 2,error)
        #        else:
        #                return "{\"Result\":false,\"info\":\"系统超时(%d): %d:%s\"}" % (ERRNUM_MODULE_top + 2,error,str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"('%s');" %(MySQLdb.escape_string(us))
			#debug(str(sql))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
			else:
				result_json = json.loads(result);
				json_list_mode1 = [];
				json_list_mode2 = [];
				json_list_mode = [];
				result = []
				for one in result_json:
					if one['Mode'] == 2:
						json_list_mode2.append(one['SubMenuId'])
					if one['Mode'] == 1:
						json_list_mode1.append(one['SubMenuId'])
				for one in json_list_mode1:
					if one in json_list_mode2:
						json_list_mode.append(one)
				#json_list_mode = json_list_mode + json_list_mode2
				#debug(str(json_list_mode))
				for one in result_json:
					if one['SubMenuId'] in json_list_mode and one['Mode'] == 1:
						one['SubMenuId'] = -1
				result = json.dumps(result_json)
				#result = str(result_json)
	except pyodbc.Error,e:
		return "[]"
        return str(result)	
		
@search.route("/encodepwd", methods=['GET', 'POST'])
def encodepwd():		
	session = request.form.get('a0')
	passwd = request.form.get('p1')
	ifopen = request.form.get('i1') #0 ->关闭 1-》开启
	if passwd < 0:
		passwd= '';
	
	_type = request.form.get('t1')
	if _type and str(_type).isdigit() == False:
		return '',403
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if ifopen == '0':
				passwd = 'null';
			else:
				if passwd !='': 
					passwd = "'%s'" %(EncodeStr(passwd))
			if passwd !='':
				sql = "select public.\"PSaveSecurityPasswd\"('%s',%s,%s);" % (usercode,_type,passwd)
				#debug(sql);
				curs.execute(sql)
				results = curs.fetchall()[0][0].encode('utf-8')
				#debug(results);
				if results == '1':
					return "{\"Result\":true,\"ErrMsg\":\"\"}"
				else:
					return "{\"Result\":false,\"ErrMsg\":\"系统异常(%s)\"}" %(str(results))
			else:
				return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@search.route("/get_encodepwd", methods=['GET', 'POST'])
def get_encodepwd():		
	session = request.form.get('a0')
	_type = request.form.get('t1')
	if not _type.isdigit():
		return '',403
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetSecurityPasswd\"('%s',%s);" % (usercode,_type))
			results = curs.fetchall()[0][0]
			if results == None :
				return "{\"Result\":true,\"ifopen\":false,\"info\":\"\"}" 
			else:
				results = results.encode('utf-8')
				return "{\"Result\":true,\"ifopen\":true,\"info\":\"%s\"}" %(str(results))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ifopen\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))		
