#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
import shutil
import MySQLdb
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from generating_log import system_log
from jinja2 import Environment,FileSystemLoader
import csv
import re
import codecs
import htmlencode
from ctypes import *
import urllib
from logbase import defines
from logbase import task_client
from urllib import unquote
from htmlencode import parse_sess
from index import PGetPermissions
from htmlencode import check_role
from werkzeug.utils import secure_filename
from comm_function import PGetSecurityPasswd
from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
manage_workorder = Blueprint('manage_workorder',__name__)
UPLOAD_FOLDER='/usr/storage/.system/upload'
ERRNUM_MODULE_manage_workorder = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

def debug(c):
	return 0
	path = "/var/tmp/debugzdp_workorder.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
	
'''
def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
'''
	
@manage_workorder.route('/show_manage_workorder',methods=['GET', 'POST'])
def show_manage_workorder():
	se = request.form.get('a0')
	now = request.form.get('z1')
	type = request.form.get('z3')
	keyword = request.form.get('z4')
	manage_filter_flag = request.form.get('z5')
	selectid = request.form.get('z6')
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if keyword == None:
		keyword = "[]"
	if selectid == None:
		selectid = "[]"
	
	if manage_filter_flag == None or manage_filter_flag=='':
		manage_filter_flag = 0
		
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
	
	_power=PGetPermissions(usercode)
	_power=str(_power)
	_power_json = json.loads(_power)
	auth_flag1 = 0
	auth_flag2 = 0
	auth_flag3 = 0
	auth_flag4 = 0
	for one in _power_json:
		if one['SubMenuId'] == 15:#访问授权
			if one['Mode'] == 2:#管理
				auth_flag1 = 1
			else:
				auth_flag1 = 2				
		elif one['SubMenuId'] == 16:#工单授权
			if one['Mode'] == 2:#管理
				auth_flag2 = 1
			else:
				auth_flag2 = 2	
		elif one['SubMenuId'] == 17:#指令授权
			if one['Mode'] == 2:#管理
				auth_flag3 = 1
			else:
				auth_flag3 = 2	
		elif one['SubMenuId'] == 18:#管理授权
			if one['Mode'] == 2:#管理
				auth_flag4 = 1
			else:
				auth_flag4 = 2	
	return render_template("manage_workorder.html",now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag,selectid=selectid,auth_flag1=auth_flag1,auth_flag2=auth_flag2,auth_flag3=auth_flag3,auth_flag4=auth_flag4)

@manage_workorder.route('/get_workorder_z',methods=['GET', 'POST'])
def get_workorder_z():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	number = request.form.get('z1')
	curpage = request.form.get('z2')
	keyword = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if number < 0:
		number = 0
	if curpage < 0:
		curpage = 0
	if number != "null":
		row = int(number)*(int(curpage)-1)
	else:
		row = "null"
	filter_cond_arry = []
	i = 0
	while i < 14:
		filter_cond_arry.append([])
		i += 1
	#所有、名称、运维用户、用户组、工单策略、管理员、主机组、主机名、主机服务、账号、服务器范围、授权动作、状态、工单状态
	keyword = json.loads(keyword);
	if len(keyword) != 0:
		for i in keyword:
			filter_arry = i.split('-',1)
			filter_cond_arry[int(filter_arry[0])].append(MySQLdb.escape_string(filter_arry[1]).decode("utf-8"))
	i = 0
	while i < 14:
		filter_cond_arry[i] = '\n'.join(filter_cond_arry[i])
		filter_cond_arry[i] = MySQLdb.escape_string(filter_cond_arry[i]).decode("utf-8")
		if i == 0:
			filter_cond_arry[i] = filter_cond_arry[i].replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		else:
			filter_cond_arry[i] = filter_cond_arry[i].replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		
		if filter_cond_arry[i] == "":
			filter_cond_arry[i] = 'null'
		else:
			if i == 11 or i == 12 or i == 13:
				if filter_cond_arry[i] == '0':
					filter_cond_arry[i] = 'null'
				else:
					filter_cond_arry[i] = '%s' % filter_cond_arry[i]
			else:
				filter_cond_arry[i] = '"%s"' % filter_cond_arry[i]
		i += 1
	
	usercode = '"%s"' % usercode
	data = '{"loginusercode":%s,"workordername":%s,"accessstrategyname":%s,"adminusercode":%s,"ugname":%s,"usercode":%s,"hgname":%s,"hostname":%s,"serverscopename":%s,"hostservicename":%s,"accountname":%s,"searchstring":%s,"limitrow":%s,"offsetrow":%s,"Action":%s,"Enabled":%s,"Status":%s}' % (usercode,filter_cond_arry[1],filter_cond_arry[4],filter_cond_arry[5],filter_cond_arry[3],filter_cond_arry[2],filter_cond_arry[6],filter_cond_arry[7],filter_cond_arry[10],filter_cond_arry[8],filter_cond_arry[9],filter_cond_arry[0],str(number),str(row),filter_cond_arry[11],filter_cond_arry[12],filter_cond_arry[13])
	data = "E'%s'" % MySQLdb.escape_string(data).decode("utf-8")
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetWorkOrder\"(%s);" % data)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_workorder.route('/get_workordertask_data',methods=['GET', 'POST'])
def get_workordertask_data():
	se = request.form.get('a0')
	cur = request.form.get('a1')
	page_total = request.form.get('a2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if page_total == 'null':
		offsetrow = 'null'
	else:
		offsetrow = str((int(cur)-1)*(int(page_total)))
	data = '{"UserImportTaskId":null,"Type":2,"limitrow":'+page_total+',"offsetrow":'+offsetrow+',"UserCode": "'+userCode+'"}'

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_workorder.route('/import_data_workorder',methods=['GET', 'POST'])
def import_data_workorder():
	global UPLOAD_FOLDER
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	cover = request.form.get('a1')
	use_BH = request.form.get('a99')
	if use_BH=='0':
		f = request.files['file_change1']
		file_v = f.filename
	else:
		file_v = request.form.get('file_v')
		file_change = request.form.get('file_change')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(system_user,'工单授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	fname = file_v
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
	file_pwd = os.path.join(UPLOAD_FOLDER,'workorder.%s'%fname)
	if use_BH=='0':
		f.save(file_pwd)
	else:
		shutil.move(file_change,file_pwd)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:#新建任务
			curs = conn.cursor()
			data_json = '{"AuthImportTaskId":0,"AuthImportTaskName":"%s","Type":2,"UserCode": "%s"}' % (MySQLdb.escape_string(taskname).decode("utf-8"),system_user)
			sql = 'select public."PSaveAuthImportTask"(E\'%s\')' % (MySQLdb.escape_string(data_json).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0].encode('utf-8')
			result_json = json.loads(result)
			if result_json['Result']:
				taskId = result_json['Id']
			else:
				return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	task_content = '[global]\nclass = taskimport_user\ntype = execute_cmd_workorder\nfile_pwd=\"%s\"\ncover=\"%s\"\ntaskid=\"%s\"\nuserid=\"%s\"\nclient_ip=\"%s\"\n' % (file_pwd,cover,str(taskId),system_user,client_ip)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		curs.close()
		conn.close()
		system_log(system_user,"创建工单导入任务：%s" % fname[:-4],"失败：任务下发异常","运维管理>授权管理")
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
	system_log(system_user,"创建工单导入任务：%s" % fname[:-4],"成功","运维管理>授权管理")
	return "{\"Result\":true}"

@manage_workorder.route('/del_work_task',methods=['GET', 'POST'])
def del_work_task():
	se = request.form.get('a0')
	del_id = request.form.get('a1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(userCode,'工单授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			id_array = str(del_id).split(',')
			Name_arry = []
			for id_v in id_array:
				curs.execute("select \"AuthImportTaskName\" from private.\"AuthImportTask\" where \"AuthImportTaskId\" = %d;" % int(id_v))
				result_1 = curs.fetchall()[0][0].encode('utf-8')
				Name_arry.append(result_1)
				sql ="delete from private.\"AuthImportTask\" where  \"AuthImportTaskId\" = %d;" % int(id_v)
				#debug(sql)
				curs.execute(sql)
			system_log(userCode,"删除工单授权导入任务：%s" % ('、'.join(Name_arry)),"成功","运维管理>授权管理")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_workorder.route('/isexist_import_workorder',methods=['GET', 'POST'])
def isexist_import_workorder():
	se = request.form.get('a0')
	#name = request.form.get('z1')
	fname = request.form.get('file_v')
	# file_change = request.form.get('file_change')
	f_name = fname[:-4]
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
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
			sql = "select * from private.\"AuthImportTask\" where \"AuthImportTaskName\" = E\'%s\' and \"Type\"=2 and \"Status\"=0;" % MySQLdb.escape_string(taskname).decode("utf-8")
			#debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				return "{\"Result\":true}"
			else:
				system_log(userCode,"创建工单导入任务：%s" % fname,"失败：该任务已存在","运维管理>授权管理")
				return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@manage_workorder.route('/export_data_workorder',methods=['GET', 'POST'])
def export_data_workorder():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('a1')
	session = request.form.get('a0')
	Type=request.form.get('z2')
	format=request.form.get('z3')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	time_value=int(time.time()*1000)
	if type == '1':
		return 'true'
	else:
		task_content = '[global]\nclass = taskdown_user\ntype = execute_down_workorder\nusercode=\"%s\"\nsession="%s"\ntype_value=%s\nformat_value=%s\ntime_value=%s\n' % (userCode,session,Type,format,time_value)
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
	return "true:workorder.%s.%s.%s"%(userCode,session,time_value)

@manage_workorder.route('/download_file_workorder',methods=['GET', 'POST'])
def download_file_workorder():
	se = request.form.get('a0')
	file_name = request.form.get('a2')
	Type=request.form.get('z1')
	use_BH=request.form.get('a99')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	system_log(userCode,"导出工单","成功","运维管理>授权管理")	
	file_name_arr=file_name.split('.')
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	if use_BH=='0':
		return send_from_directory('/usr/storage/.system/dwload',file_name,as_attachment=True,attachment_filename=('.'.join(file_name_arr)))
	else:
		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"%s","filenewname":"%s"}'% (file_name,('.'.join(file_name_arr)))

@manage_workorder.route('/get_down_ok_workorder',methods=['GET', 'POST'])
def get_down_ok_workorder():
	se = request.form.get('a0')
	Type=request.form.get('a1')
	file_name=request.form.get('a2')
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
			sql = "select * from private.\"AuthExportInfo\" where \"FileName\" like E'%"+file_name+"%';"
			#debug(str(sql))
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				sql = "delete from private.\"AuthExportInfo\" where \"FileName\" like E'%"+file_name+"%';"
				curs.execute(sql)
				conn.commit()
			else:
				return "{\"Result\":false,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
			return "{\"Result\":true,\"ErrMsg\":\""+str(results[0][2])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"file_name\":\""+str(results[0][1])+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_workorder.route('/del_workorder_file',methods=['GET', 'POST'])
def del_workorder_file():
        se = request.form.get('a0')
        type = request.form.get('z1')
        client_ip = request.remote_addr
        (error,userCode,mac) = SessionCheck(se,client_ip);
        if error < 0:
                return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        elif error > 0:
                if error == 2:
                        return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
                else:
                        return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        passwd=PGetSecurityPasswd(userCode,1)
        if passwd==0:
                return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
        if passwd!='':
                filename='workorder.%s.%s.zip' % (userCode,se)
        else:
			if type == '1':
					filename='workorder.%s.%s.xls' % (userCode,se)
			elif type == '2':
					filename='workorder.%s.%s.xlsx' % (userCode,se)
			else:
					filename='workorder.%s.%s.csv' % (userCode,se)
		# filename='workorder.%s.%s.csv' % (userCode,se)
        task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(filename))
        if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return 'true'

@manage_workorder.route('/check_editwork',methods=['GET', 'POST'])
def check_editwork():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
	if id == '-1':
		id = 'null'
	usercode = '"%s"' % usercode
	data = '{"loginusercode":'+usercode+',"workorderid":'+id+',"limitrow":null,"offsetrow":null}'
	data = "E'%s'" % data
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetWorkOrder\"(%s);"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
		
@manage_workorder.route('/delete_work',methods=['GET', 'POST'])
def delete_work():
	session = request.form.get('a0')
	type = request.form.get('z1')
	id = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,'工单授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	work_title = "运维管理>工单授权"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"WorkOrderName\" from public.\"WorkOrder\" where \"WorkOrderId\" in (%s)" % id[1:-1]
				#debug("sql:%s" % sql)
				curs.execute(sql)
				auth_str = ""
				for row in curs.fetchall():
					auth_str = auth_str + row[0].encode('utf-8') + ","
					
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"WorkOrderName\" from public.\"WorkOrder\" where \"WorkOrderId\"=%d" % int(id)
					#debug("sql:%s" % sql)
					curs.execute(sql)
					auth_name = curs.fetchall()[0][0].encode('utf-8')
				
					curs.execute("select public.\"PDeleteWorkOrder\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(usercode,"删除工单授权：%s" % auth_name,"失败："+results['ErrMsg'],work_title)
						conn.rollback();
						return result
				if auth_str != "":
					system_log(usercode,"删除工单授权：%s" % auth_str[:-1],"成功",work_title)
				return "{\"Result\":true}"
			else:
				sql = "select \"WorkOrderName\" from public.\"WorkOrder\" where \"WorkOrderId\"=%d" % int(id)
				#debug("sql:%s" % sql)
				curs.execute(sql)
				auth_name = curs.fetchall()[0][0].encode('utf-8')
			
				curs.execute("select public.\"PDeleteWorkOrder\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				result = json.loads(results)
				if result['Result']:
					system_log(usercode,"删除工单授权：%s" % auth_name,"成功",work_title)
				else:
					system_log(usercode,"删除工单授权：%s" % auth_name,"失败："+result['ErrMsg'],work_title)
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_workorder.route('/modify_priority',methods=['GET', 'POST'])
def modify_priority():
	session = request.form.get('a0')
	modifyid = request.form.get('z1')
	referid = request.form.get('z2')
	position = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,'工单授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PModifyWorkOrderPriority\"(%d,%d,%d);"%(int(modifyid),int(referid),int(position)))
			results = curs.fetchall()[0][0].encode('utf-8')
			
			sql = "select \"WorkOrderName\" from public.\"WorkOrder\" where \"WorkOrderId\" in (%s,%s)" %(modifyid,referid)
			curs.execute(sql)
			name_re = curs.fetchall()
			
			if results == "1":
				if position == '1':
					system_log(usercode,"工单授权（%s）的优先级改为在工单授权（%s）之前" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"成功","工单授权")
				else:
					system_log(usercode,"工单授权（%s）的优先级改为在工单授权（%s）之后" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"成功","工单授权")
			else:
				if position == '1':
					system_log(usercode,"工单授权（%s）的优先级改为在工单授权（%s）之前" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"失败","工单授权")
				else:
					system_log(usercode,"工单授权（%s）的优先级改为在工单授权（%s）之后" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"失败","工单授权")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
@manage_workorder.route('/enable_workorder',methods=['GET', 'POST'])
def enable_workorder():
	session = request.form.get('a0')
	workid = request.form.get('z1')
	e_type = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,'工单授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"WorkOrderName\" from \"WorkOrder\" where \"WorkOrderId\"=%s" % workid
			curs.execute(sql)
			workname = curs.fetchall()[0][0].encode('utf-8')
			if e_type == '1':
				curs.execute("update \"WorkOrder\" set \"Enabled\"= true,\"InvalidLog\"=null where \"WorkOrderId\"= %s" % workid)
				system_log(usercode,"启用工单授权：%s" % workname,"成功","工单授权")
			else:
				curs.execute("update \"WorkOrder\" set \"Enabled\"= false,\"InvalidLog\"=null where \"WorkOrderId\"= %s" % workid)
				system_log(usercode,"停用工单授权：%s" % workname,"成功","工单授权")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@manage_workorder.route('/change_time',methods=['GET', 'POST'])
def change_time():
	session = request.form.get('a0')
	accstrid = request.form.get('z1')
	start_date = request.form.get('z2')
	start_time = request.form.get('z3')
	end_date = request.form.get('z4')
	end_time = request.form.get('z5')
	workid = request.form.get('z6')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
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
		md5_json = StrMD5(start_date);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(usercode,'工单授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetAccessStrategy\"(%d,null,null,2,null,null);" %(int(accstrid)))
			#debug("select public.\"PGetAccessStrategy\"(%d,null,null,2,null,null);" %(int(accstrid)))
			result = curs.fetchall()[0][0].encode('utf-8')
			work_data = json.loads(result)
			#debug("%s" % work_data)
			if len(work_data['data']) == 0:
				system_log(usercode,"修改工单授权：%s的策略生效时间" % workname,"失败：策略不存在","工单授权")
				return "{\"Result\":false,\"ErrMsg\":\"策略不存在(%d)\"}" % (sys._getframe().f_lineno)
			else:
				if len(work_data['data'][0]['TimeConfig']) != 0:
					sql = 'UPDATE "TimeSetMember" SET "StartDate" = E\'%s\', "EndDate" = E\'%s\', "StartTime" = E\'%s\', "EndTime" = E\'%s\' WHERE "TimeSetId" = %d' % (start_date,end_date,start_time,end_time,work_data['data'][0]['TimeConfig'][0]['TimeSetId'])
					#debug("sql:%s" % sql)
					curs.execute(sql)
					sql = "select \"WorkOrderName\" from \"WorkOrder\" where \"WorkOrderId\"=%d" % int(workid)
					curs.execute(sql)
					workname = curs.fetchall()[0][0]
					if work_data['data'][0]['AccessStrategyName'].find('#') == 0:
						system_log(usercode,"修改工单授权（%s）的策略生效时间" % workname,"成功","工单授权")
					else:
						system_log(usercode,"修改工单授权（%s）的策略（%s）生效时间" % (workname,work_data['data'][0]['AccessStrategyName']),"成功","工单授权")
					return "{\"Result\":true}" 
				else:
					return "{\"Result\":false,\"ErrMsg\":\"策略错误(%d)\"}" % (sys._getframe().f_lineno)
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_workorder.route('/update_enable',methods=['GET', 'POST'])
def update_enable():
	session = request.form.get('a0')
	id_str	= request.form.get('z1')
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
			sql = "update public.\"WorkOrder\" set \"Enabled\"=false where \"WorkOrderId\" in (%s)" % id_str[1:-1]
			curs.execute(sql)
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
