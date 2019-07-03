#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
import MySQLdb
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionOnline
from comm import LogSet
from logbase import common
from generating_log import system_log
from htmlencode import checkaccount

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
from logbase import common
from logbase import defines
from logbase import task_client
from htmlencode import parse_sess
work_order_z = Blueprint('work_order_z',__name__)

ERRNUM_MODULE_work_order_z = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

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

@work_order_z.route('/add_workorder',methods=['GET', 'POST'])
def add_workorder():
	se= request.form.get('a0')
	us = request.form.get('a1')
	now = request.form.get('z1')
	edit = request.form.get('z2')
	type = request.form.get('z3')
	keyword = request.form.get('z4')
	manage_filter_flag = request.form.get('z5')
	selectid = request.form.get('z6')
	if keyword == None:
		keyword = "[]"
	if selectid == None:
		selectid = "[]"
		
	if(str(manage_filter_flag).isdigit() == False):
		return '',403
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
	
	if edit !="None":
		if(str(edit).isdigit() == False):
			return '',403	
		
	t = "add_workorder.html"
	if edit != "None":
		return render_template(t,edit=edit,now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag,selectid=selectid,se=se,us=us);
	else:
		return render_template(t,edit='"None"',now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag,selectid=selectid,se=se,us=us);		
		
@work_order_z.route('/get_hostdirectory_zw',methods=['GET','POST'])
def get_hostdirectory_zw():
	debug('get_hostdirectory_zw')
	session = request.form.get('a0')
	id = request.form.get('z1')
	wid = request.form.get('z2')
	find_doing=request.form.get('z3')
	#debug('find_doing:%s'%str(find_doing))	
	client_ip = request.remote_addr
	debug('usercode')
	(error,usercode,mac) = SessionCheck(session,client_ip);
	debug(usercode)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	error_1= SessionOnline(session)
	if id == "":
		id = 0
	if str(find_doing)=='true':
		debug("str(find_doing)=='true'")
		sql="select public.\"PGetHostDirectory\"(E'%s',%d,4,%d,null,null,%s);" %(MySQLdb.escape_string(usercode).decode("utf-8"),int(id),int(wid),str(find_doing))
		#sql="select public.\"PGetHostDirectory\"('%s',%d,4,%d,null,null);" %(usercode,int(id),int(wid))
	else:
		sql="select public.\"PGetHostDirectory\"(E'%s',%d,4,%d,null,null);" %(MySQLdb.escape_string(usercode).decode("utf-8"),int(id),int(wid))
		#sql="select public.\"PGetHostDirectory\"('%s',%d,4,%d,null,null,%s);" %(usercode,int(id),int(wid),str(find_doing))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			debug('------')
			debug((sql))
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_userdirectory_zw',methods=['GET','POST'])
def get_userdirectory_zw():
	session = request.form.get('a0')
	ugid = request.form.get('z1')
	uid = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if ugid == "-1":
		ugid = "0"
	elif not ugid.isdigit():
		return '',403
	if uid == "-1":
		uid = "null"
	elif not uid.isdigit():
		return '',403
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetUserDirectory\"(E'%s',%s,5,%s,null,null);" %(MySQLdb.escape_string(usercode).decode("utf-8"),ugid,uid))
			curs.execute("select public.\"PGetUserDirectory\"(E'%s',%s,5,%s,null,null);" %(MySQLdb.escape_string(usercode).decode("utf-8"),ugid,uid))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)


@work_order_z.route('/get_AccessStrategy_w',methods=['GET','POST'])
def get_AccessStrategy_w():
	session = request.form.get('a0')
	id = request.form.get('z1')
	name = request.form.get('z2')
	if name!='' and not checkaccount(name):
		return 'z2格式错误',403
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	#debug(id)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if name != '':
				curs.execute("select public.\"PGetAccessStrategy\"(null,E'%s',null,2,null,null);" %(name))
			else:
				if id == '-1':
					curs.execute("select public.\"PGetAccessStrategy\"(null,null,null,2,null,null);")
				else:
					curs.execute("select public.\"PGetAccessStrategy\"(%d,null,null,2,null,null);"%(int(id)))	
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_ServerScope_w',methods=['GET','POST'])
def get_ServerScope_w():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetServerScope\"(null,null,true,null,null,'%s',null);" % MySQLdb.escape_string(usercode).decode("utf-8"))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_AccountProtocolForAuth_w',methods=['GET','POST'])
def get_AccountProtocolForAuth_w():
	data = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetAccountProtocolForAuth\"(E\'%s\');"%(data))
			curs.execute("select public.\"PGetAccountProtocolForAuth\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_ConnParam_w',methods=['GET','POST'])
def get_ConnParam_w():
	pid = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetConnParam\"(%d,null,null,null,null,null,null);"%(int(pid)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_manager_zw',methods=['GET','POST'])
def get_manager_zw():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetUser\"(null,2);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_timeset_zw',methods=['GET','POST'])
def get_timeset_zw():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetTimeSet\"(null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_clientset_zw',methods=['GET','POST'])
def get_clientset_zw():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetClientScope\"(null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_macset_zw',methods=['GET','POST'])
def get_macset_zw():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetMACSet\"(null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_approval_zw',methods=['GET','POST'])
def get_approval_zw():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetApproveStrategy\"(null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_eventalarm_zw',methods=['GET','POST'])
def get_eventalarm_zw():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetEventAlarmInfo\"(null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/save_AccessStrategy_w',methods=['GET','POST'])
def save_AccessStrategy_w():
	data = request.form.get('z1')
	session = request.form.get('a0')
	md5_str = request.form.get('m1')
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PSaveAccessStrategy\"('%s',0,0);"%(data))
			curs.execute("select public.\"PSaveAccessStrategy\"(E'%s',0,0);"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/save_WorkOrder',methods=['GET','POST'])
def save_WorkOrder():
	data = request.form.get('z1')
	session = request.form.get('a0')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			#curs = conn.cursor()
			debug("select public.\"PSaveWorkOrder\"(E\'%s\');"%(data))
			curs.execute("select public.\"PSaveWorkOrder\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			results_json=json.loads(results)
			if results_json["Result"] == False:
				data0 = json.loads(data)
				if data0['WorkOrderId'] == 0:
					system_log(usercode,"创建工单授权：%s" % data0['WorkOrderName'],"失败","运维管理>工单授权")
				else:
					#data1 = json.loads(prv_data)
					#cmp(data0,data1)
					#if t != 0:
					system_log(usercode,"编辑工单授权：%s" % data0['WorkOrderName'],"失败","运维管理>工单授权")
				return results
			debug("1111111111111111")
			debug(str(results_json))
			#conn.commit()
			debug("select public.\"PSaveWorkOrderMessage\"(%s,true,'%s');"%(results_json["WorkOrderId"],MySQLdb.escape_string(usercode).decode("utf-8")))
			#curs.execute("select public.\"PSaveWorkOrderMessage\"(%s,true,'%s');"%(results_json["WorkOrderId"],usercode))
			debug("22222222222222222")
			##[global]
			#class=taskupdatehnodeselected
			#type=update_run
			#id_type=id_type
			#id=id
			task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=4\nid=%s\n' % (results_json["WorkOrderId"])
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				data0 = json.loads(data)
				if data0['WorkOrderId'] == 0:
					system_log(usercode,"创建工单授权:%s" % data0['WorkOrderName'],"失败","运维管理>工单授权")
				else:
					#data1 = json.loads(prv_data)
					#cmp(data0,data1)
					#if t != 0:
					system_log(usercode,"编辑工单授权:%s" % data0['WorkOrderName'],"失败","运维管理>工单授权")
				return "{\"Result\":false,\"ErrMsg\":\"扫描任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
			
			get_data = '{"loginusercode":"'+MySQLdb.escape_string(usercode).decode("utf-8")+'","workorderid":'+str(results_json['WorkOrderId'])+',"limitrow":null,"offsetrow":null}'
			get_data = "'%s'" % get_data
			curs.execute("select public.\"PGetWorkOrder\"(E%s);"%(get_data))
			re_data = curs.fetchall()[0][0].encode('utf-8')
			debug("re_data:%s" % re_data)
			re_data = json.loads(re_data)
			data0 = json.loads(data)
			if len(re_data['data']) == 0:
				
				sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % data0['AdminSet'][0]['AdminId']
				curs.execute(sql)
				UserCode = curs.fetchall()[0][0].encode('utf-8')
				get_data = '{"loginusercode":"'+UserCode+'","workorderid":'+str(results_json["WorkOrderId"])+',"limitrow":null,"offsetrow":null}'
				get_data = "'%s'" % get_data
				curs.execute("select public.\"PGetWorkOrder\"(E%s);"%(get_data))
				re_data = curs.fetchall()[0][0].encode('utf-8')
				re_data = json.loads(re_data)
			
			
			_obj = ""
			if re_data['data'][0]["AuthMode"] == 1:
				_obj = "方式：对象指定"
			elif re_data['data'][0]["AuthMode"] == 2:
				_obj = "方式：范围指定（共有）"
			elif re_data['data'][0]["AuthMode"] == 3:
				_obj = "方式：范围指定（所有）"
			else:
				_obj = "方式：范围指定（自定义）"
			
			scopename = ""
			if re_data['data'][0]['AuthScope'] != None and len(re_data['data'][0]['AuthScope']) != 0:
				for scope in re_data['data'][0]['AuthScope']:
					scopename = scopename + scope['ServerScopeName'] + ','
				scopename = scopename[:-1]
			
			auth_obj = []
			if re_data['data'][0]['AuthObject'] != None and len(re_data['data'][0]['AuthObject']) != 0:
				auth_hg = ""
				auth_host = ""
				auth_account = ""
				flag_h = 0
				for authobj in re_data['data'][0]['AuthObject']:
					if flag_h >= 1000:
						break
					if authobj['AccountName'] != None:
						auth_account = auth_account + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + '-' + authobj['AccountName'] + ','
					elif authobj['HostName'] != None:
						auth_host = auth_host + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + ','
					else:
						auth_hg = auth_hg + '[' + authobj['HGName'] + '],'
					flag_h += 1
				
				if auth_hg != "":
					auth_hg = "指定主机组：" + auth_hg[:-1]
					auth_obj.append(auth_hg)
				if auth_host != "":
					auth_host = "指定主机：" + auth_host[:-1]
					auth_obj.append(auth_host)
				if auth_account != "":
					auth_account = "指定账号：" + auth_account[:-1]
					auth_obj.append(auth_account)
			auth_obj_str = '，'.join(auth_obj)
			if scopename != "":
				_obj = _obj + '，' + "服务器范围：" + scopename
				
			if auth_obj_str != "":
				_obj = _obj + '，' + auth_obj_str
				
			if re_data['data'][0]['Enabled'] == True:
				_obj = _obj + '，' + "启用"
			else:
				_obj = _obj + '，' + "停用"
			
			if re_data['data'][0]['AdminSet'] != None and len(re_data['data'][0]['AdminSet']) != 0:
				admin_str = ""
				for admin in re_data['data'][0]['AdminSet']:
					admin_str = admin_str + admin['UserCode'] + ','
				if admin_str != "":
					admin_str = "管理者：" + admin_str[:-1]

				_obj = _obj + '，' + admin_str
			
			if re_data['data'][0]['AuthUserSet'] != None and len(re_data['data'][0]['AuthUserSet']) != 0:
				user_str = ""
				userhg_str = ""
				flag_h = 0			
				for user in re_data['data'][0]['AuthUserSet']:
					if flag_h >= 1000:
						break
					if user['Type'] == 1:
						user_str = user_str + user['Name'] + ','
					else:
						userhg_str = userhg_str + user['Name'] + ','
					flag_h += 1
				debug("user_str:%s" % user_str)
				debug("userhg_str:%s" % userhg_str)
				if user_str != "":
					user_str = "授权用户：" + user_str[:-1]
					_obj = _obj + '，' + user_str
				if userhg_str != "":
					userhg_str = "授权用户组：" + userhg_str[:-1]
					_obj = _obj + '，' + userhg_str
			
			if re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName'].find('#') != -1:
				_obj = _obj + "，权限配置：#私有"
				strategyname = "#私有"
			else:
				_obj = _obj + "，权限配置：" + re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName']
				strategyname = re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName']
			
			#权限配置日志
			sql = "select public.\"PGetAccessStrategy\"(%d,null,null,2,null,null)" % re_data['data'][0]['AccessStrategyInfo']['AccessStrategyId']
			debug("sql:%s" % sql)
			curs.execute(sql)
			strategy = curs.fetchall()[0][0].encode('utf-8')
			debug("strategy:%s" % str(strategy))
			strategy = json.loads(strategy)
			
			log_array = [];
			if strategy['data'][0]['EnableApprove']:
				log_array.append("登录审批："+strategy['data'][0]['ApproveStrategyName'])
			if strategy['data'][0]['EnableDoubleCollaboration']:
				log_array.append("协同登录")
			if strategy['data'][0]['EnableAccessInfo']:
				log_array.append("访问备注")
			if strategy['data'][0]['EnableAlarm']:
				log_array.append("登录告警："+strategy['data'][0]['EventAlarmInfoName'])
			
			RDP_flag = 0
			if strategy['data'][0]['EnableRDPClipboard'] == 1:
				log_array.append("RDP传输控制：剪贴板上传")
			elif strategy['data'][0]['EnableRDPClipboard'] == 2:
				log_array.append("RDP传输控制：剪贴板下载")
			elif strategy['data'][0]['EnableRDPClipboard'] == 3:
				log_array.append("RDP传输控制：剪贴板上传、下载")
			else:
				RDP_flag = 1
			if strategy['data'][0]['EnableRDPFileRecord']:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：文件记录")
				else:
					log_array.append("文件记录")
				RDP_flag = 0
			if strategy['data'][0]['EnableRDPDiskMap']==1:
                		if RDP_flag == 1:
                    			log_array.append("RDP传输控制：磁盘上行")
                		else:
                    			log_array.append("磁盘上行")
				RDP_flag = 0
            		elif strategy['data'][0]['EnableRDPDiskMap']==2:
                		if RDP_flag == 1:
                    			log_array.append("RDP传输控制：磁盘下行")
                		else:
                    			log_array.append("磁盘下行")
				RDP_flag = 0
            		elif strategy['data'][0]['EnableRDPDiskMap']==3:
                		if RDP_flag == 1:
                    			log_array.append("RDP传输控制：磁盘上行、下行")
                		else:
                    			log_array.append("磁盘上行、下行")
				RDP_flag = 0
            		else:
                		RDP_flag=1
			'''
			if strategy['data'][0]['EnableRDPDiskMap']:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：磁盘映射")
				else:
					log_array.append("磁盘映射")
			'''
			if strategy['data'][0]['EnableRDPKeyRecord']:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：键盘记录")
				else:
					log_array.append("键盘记录")
			
			SSH_flag = 0
			if strategy['data'][0]['EnableSSHFileTrans'] == 1:
				log_array.append("SSH传输控制：文件上传")
			elif strategy['data'][0]['EnableSSHFileTrans'] == 2:
				log_array.append("SSH传输控制：文件下载")
			elif strategy['data'][0]['EnableSSHFileTrans'] == 3:
				log_array.append("SSH传输控制：文件上传、下载")
			else:
				SSH_flag = 1

			if strategy['data'][0]['EnableSSHFileRecord']:
				if SSH_flag == 1:
					log_array.append("SSH传输控制：文件记录")
				else:
					log_array.append("文件记录")
			FTP_flag = 0
			if strategy['data'][0]['EnableFTPFileTrans'] == 1:
				log_array.append("FTP传输控制：文件上传")
			elif strategy['data'][0]['EnableFTPFileTrans'] == 2:
				log_array.append("FTP传输控制：文件下载")
			elif strategy['data'][0]['EnableFTPFileTrans'] == 3:
				log_array.append("FTP传输控制：文件上传、下载")
			else:
				FTP_flag = 1
			if strategy['data'][0]['EnableFTPFileRecord']:
				if FTP_flag == 1:
					log_array.append("FTP传输控制：文件记录")
				else:
					log_array.append("文件记录")
			
			
			if strategy['data'][0]['ClientScopeAction'] == 1:
				ClientScopeAction = "允许"
			elif strategy['data'][0]['ClientScopeAction'] == 2:
				ClientScopeAction = "例外"
			else:
				ClientScopeAction = "不限制"

			clientrange = ""
			if strategy['data'][0]['ClientScopeConfig'] != None and len(strategy['data'][0]['ClientScopeConfig']) != 0:
				if strategy['data'][0]['ClientScopeConfig'][0]['IPList'] != None and strategy['data'][0]['ClientScopeConfig'][0]['IPList']['Set'] != None and len(strategy['data'][0]['ClientScopeConfig'][0]['IPList']['Set']) != 0:#自定义
					IPaddress = ""
					IPinterval = ""
					for client in strategy['data'][0]['ClientScopeConfig'][0]['IPList']['Set']:
						if client['StartIP'] == client['EndIP']:
							IPaddress = IPaddress + client['StartIP'] + '?*'
						else:
							IPinterval = IPinterval + client['StartIP'] + '-' + client['EndIP'] + '?*'
					if IPaddress != "":
						clientrange = clientrange + 'IP地址：' + IPaddress[:-2] + '?*'
					if IPinterval != "":
						clientrange = clientrange + 'IP区间：' + IPinterval[:-2] + '?*'
				if strategy['data'][0]['ClientScopeConfig'][0]['MACList'] != None and strategy['data'][0]['ClientScopeConfig'][0]['MACList']['Set'] != None and len(strategy['data'][0]['ClientScopeConfig'][0]['MACList']['Set']) != 0:#自定义
					MACaddress = ""
					MACinterval = ""
					for client in strategy['data'][0]['ClientScopeConfig'][0]['MACList']['Set']:
						if client['StartMACAddress'] == client['EndMACAddress']:
							MACaddress = MACaddress + client['StartMACAddress'] + '?*'
						else:
							MACinterval = MACinterval + client['StartMACAddress'] + '-' + client['EndMACAddress'] + '?*'
					if MACaddress != "":
						clientrange = clientrange + 'MAC地址：' + MACaddress[:-2] + '?*'
					if MACinterval != "":
						clientrange = clientrange + 'MAC区间：' + MACinterval[:-2] + '?*'
				if strategy['data'][0]['ClientScopeConfig'][0]['ClientScopeName']!= None:
					client_str = ""
					for clientset in strategy['data'][0]['ClientScopeConfig']:
						client_str = client_str + clientset['ClientScopeName'] + '?*'
					if client_str != "":
						clientrange = clientrange + "客户端集合：" + client_str[:-2]
		
			strategy_str = "客户端地址限制：" + ClientScopeAction
			if clientrange != "":
				#clientrange = clientrange[:-1]
				strategy_str = strategy_str + '（' + clientrange + '）,'
			else:
				strategy_str = strategy_str + ','
			
			strategy_str = strategy_str[:-1]
			log_array.append(strategy_str)
			strategy_str = ','.join(log_array)
			strategy_str = strategy_str.replace("?*","、").replace(",","，")
			'''
			if len(log_array) != 0:
				log_str = '，'.join(log_array)
				strategy_str = log_str + ',' + strategy_str
			'''
			data0 = json.loads(data)
			if data0['AccessStrategyInfo']['AccessStrategyId'] == 0:
				system_log(usercode,"创建权限配置：%s（%s）" % (strategyname,strategy_str),"成功","运维管理>工单授权")
			else:
				debug("99999999999999999999")
				system_log(usercode,"编辑权限配置：%s（%s）" % (str(strategyname),str(strategy_str)),"成功","运维管理>工单授权")
				debug("99999999999999999999zzzzzzzzzzzzz")
			
			if data0['WorkOrderId'] == 0:
				system_log(usercode,"创建工单授权:%s（%s）" % (data0['WorkOrderName'],_obj),"成功","运维管理>工单授权")
			else:
				#data1 = json.loads(prv_data)
				#cmp(data0,data1)
				#if t != 0:
				system_log(usercode,"编辑工单授权:%s（%s）" % (data0['WorkOrderName'],_obj),"成功","运维管理>工单授权")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/delete_AccessStrategy_w',methods=['GET','POST'])
def delete_AccessStrategy_w():
	id = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PDeleteAccessStrategy\"(%d);"%(int(id)))
			curs.execute("select public.\"PDeleteAccessStrategy\"(%d);"%(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_workname',methods=['GET','POST'])
def get_workname():
	name = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetWorkOrderByName\"(E'%s');"%(name))
			curs.execute("select public.\"PGetWorkOrderByName\"(E'%s');"%(name))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@work_order_z.route('/Get_SameAccountProtocolForAuth',methods=['GET','POST'])
def Get_SameAccountProtocolForAuth():
	data = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetSameAccountProtocolForAuth\"(E\'%s\');"%(data))
			curs.execute("select public.\"PGetSameAccountProtocolForAuth\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0]
			if(not results):
				return "None"
			else:
				results = results.encode('utf-8')
				return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@work_order_z.route('/get_server',methods=['GET','POST'])
def get_server():

	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)：%d\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetDeviceType\"(null,null,null,null,null,null,null);")
			curs.execute("select public.\"PGetDeviceType\"(null,null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
###获取 主机组 用户组 的选中状态
@work_order_z.route('/PGetHNodeSelected',methods=['GET','POST'])
def PGetHNodeSelected():
	try:
		debug('PGetHNodeSelected')
		session = request.form.get('a0')
		json = request.form.get('z1')
		client_ip = request.remote_addr
		json=str(json)
		(error,usercode,mac) = SessionCheck(session,client_ip);
		if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
						
		'''
		SELECT public."PGetHNodeSelected"(json) 
		'''
		
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
			sql = "SELECT public.\"PGetHNodeSelected\"(E'%s') " %(json)
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			debug('error')
			debug(sql);
			debug('---')
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0]
		curs.close()
		conn.close()
		debug(str(results))
		return "{\"Result\":true,\"info\":%s}" % (results)
	except:
		debug(str(sys.exc_info()[0]) +str(sys.exc_info()[1]))
		return 0
		
###获取 用户组 的选中状态
@work_order_z.route('/PGetUNodeSelected',methods=['GET','POST'])
def PGetUNodeSelected():
	try:
		debug('PGetUNodeSelected')
		session = request.form.get('a0')
		jsondata = request.form.get('z1')
		client_ip = request.remote_addr
		jsondata=str(jsondata)
		try:
			json.loads(jsondata)
		except ValueError:
			return "z1格式错误",403
		(error,usercode,mac) = SessionCheck(session,client_ip);
		if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
						
		'''
		SELECT public."PGetUNodeSelected"(jsondata) 
		'''
		
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
			sql = "SELECT public.\"PGetUNodeSelected\"(E'%s') " %(jsondata)
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			debug('error')
			debug(sql);
			debug('---')
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		results = curs.fetchall()[0][0]
		conn.commit()
		curs.close()
		conn.close()
		debug(str(results))
		return "{\"Result\":true,\"info\":%s}" % (results)
	except:
		debug(str(sys.exc_info()[0]) +str(sys.exc_info()[1]))
		return 0
###获取 主机组 用户组 的选中状态		
@work_order_z.route('/IsHNodeSelected',methods=['GET','POST'])
def IsHNodeSelected():
	try:
		session = request.form.get('a0')
		typ = request.form.get('z1')
		editid = request.form.get('z2')
		selectid = request.form.get('z3')
		flag_host = request.form.get('z4')
		p_hgid = request.form.get('z5')
		pid = request.form.get('z6')
		
		if typ and str(typ).isdigit() == False:
			return '',403
		if editid and str(editid).isdigit() == False:
			return '',403
		if selectid and str(selectid).isdigit() == False:
			return '',403
		if p_hgid and p_hgid !='null' and str(p_hgid).isdigit() == False:
			return '',403
		if pid and str(pid).isdigit() == False:
			return '',403
		if flag_host !='false' and flag_host!='true':
			return '',403
			
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip);
		if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
				
		'''
		SELECT public."IsHNodeSelected"(type, id, NULL, hg."HGId", FALSE) 
		'''
		
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
			sql = "SELECT public.\"IsHNodeSelected\"(%s, %s, %s,%s, %s) " %(typ,editid,p_hgid,selectid,flag_host)
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0]
		curs.close()
		conn.close()
		debug(str(results))
		return "{\"Result\":true,\"info\":{\"current_id\":%s,\"status\":%s,\"pid\":%s}}" % (selectid,results,pid)
		
	except:
		debug(str(sys.exc_info()[0]) +str(sys.exc_info()[1]))
		return 0
			
###获取多个主机信息
@work_order_z.route('/get_hosts',methods=['GET','POST'])
def get_hosts():
	try:
		session = request.form.get('a0')
		hosts = request.form.get('z1')
		if hosts <0:
			hosts = ''
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip);
		if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
				
		'''
		SELECT public."PGetHostForTest"('{2,3,4,5,6}') 
		'''
		
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
		hostlist = hosts.split(',');
		hostl = []
		for host in hostlist:
			hostl.append(int(host.split(':')[1]));
		hostl.sort()	
		try:
			sql = "SELECT public.\"PGetHostForTest\"(E'{%s}') " %(str(hostl)[1:][:-1])
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":%s,\"grp\":\"%s\"}" % (results,str(hostl)[1:][:-1])
		
	except:
		debug(str(sys.exc_info()[0]) +str(sys.exc_info()[1]))
		return 0
			
@work_order_z.route('/check_strategy',methods=['GET','POST'])
def check_strategy():
	session = request.form.get('a0')
	startegyname = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAccessStrategyByName\"(E'%s')" % startegyname
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"data\":%d}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	

		
