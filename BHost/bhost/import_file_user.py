#!usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import sys
import os
import base64
import csv
import pyodbc
import re
import codecs
import shutil
import MySQLdb
import htmlencode
from generating_log import system_log
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from htmlencode import parse_sess
from htmlencode import check_role
from logbase import common
from logbase import defines
from logbase import task_client
from urllib import unquote
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
import_file_user = Blueprint('import_file_user',__name__)

UPLOAD_FOLDER = '/usr/storage/.system/upload'
#HTMLEncode 
def HTMLEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

def debug(c):
	return 0
	path = "/var/tmp/debuglhimport.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

###############用户

#导入
@import_file_user.route('/import_data_user',methods=['GET', 'POST'])
def import_data_user():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	cover = request.form.get('a1')
	use_BH = request.form.get('a99')
	file_v = request.form.get('file_v')
	if use_BH=='0':
		f = request.files['file_change1']
		file_v = secure_filename(f.filename)
	else:
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
	if check_role(system_user,'用户管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	fname = file_v
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	debug(file_pwd)
	if use_BH=='0':
		f.save(os.path.join(UPLOAD_FOLDER, fname))
	else:
		shutil.move(file_change,file_pwd) 
	debug("12313")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:#新建任务
			curs = conn.cursor()
			data_json = '{"UserImportTaskId":0,"UserImportTaskName":"%s","UserCode": "%s"}' % (MySQLdb.escape_string(fname[:-4]).decode("utf-8"),system_user)
			sql = 'select public."PSaveUserImportTask"(E\'%s\')' % (MySQLdb.escape_string(data_json).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0].encode('utf-8')
			result_json = json.loads(result)
			debug(str(result_json))
			taskId = result_json['Id']
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	task_content = '[global]\nclass = taskimport_user\ntype = execute_cmd\nfile_pwd=\"%s\"\ncover=\"%s\"\ntaskid=\"%s\"\nusercode=\"%s\"\nclientip=\"%s\"\n' % (file_pwd,cover,str(taskId),system_user,client_ip)
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		debug("hhhhhhh")
		curs.close()
		conn.close()
		system_log(system_user,"创建用户导入任务：%s" % fname,"失败：任务下发异常","运维管理>用户管理")
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)

	system_log(system_user,"创建用户导入任务：%s" % fname,"成功","运维管理>用户管理")
	return "{\"Result\":true}"
#删除导入文件
@import_file_user.route('/del_usertask',methods=['GET', 'POST'])		
def del_usertask():
	se = request.form.get('a0')
	del_id = request.form.get('a1')
	debug(str(del_id))
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(userCode,'用户管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			id_array = str(del_id).split(',')
			debug(str(id_array))
			Name_arry = []
			for id_v in id_array:
				debug(str(id_v))
				curs.execute("select \"UserImportTaskName\" from private.\"UserImportTask\" where \"UserImportTaskId\" = %d;" % int(id_v))
				result_1 = curs.fetchall()[0][0].encode('utf-8')
				Name_arry.append(result_1)

				curs.execute("select public.\"PDeleteUserImportTask\"(%d);" %(int(id_v)))
				result = curs.fetchall()[0][0].encode('utf-8')
				debug("result")
				debug(str(result))
				results = json.loads(result)
				if results['Result'] == False:
					system_log(userCode,"删除用户导入任务：%s" % result_1,"失败："+results['ErrMsg'],"运维管理>用户管理")
					conn.rollback()
					return result
			system_log(userCode,"删除用户导入任务：%s" % ('、'.join(Name_arry)),"成功","运维管理>用户管理")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
#结果
@import_file_user.route('/get_usertask_detail',methods=['GET', 'POST'])
def get_usertask_detail():
	se = request.form.get('a0')
	cur = request.form.get('a1')
	page_total = request.form.get('a2')

	taskid = request.form.get('a4')
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


	data = '{"UserImportTaskId":'+taskid+',"Status":'+status+',"limitrow": '+page_total+',"offsetrow": '+offsetrow+'}'
	#data = '{"hostleadintaskid":'+taskid+',"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": '+page_total+',"offsetrow": '+offsetrow+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetUserImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
#列表
@import_file_user.route('/get_usertask_data',methods=['GET', 'POST'])
def get_usertask_data():
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
	data = '{"UserImportTaskId":null,"limitrow":'+page_total+',"offsetrow":'+offsetrow+',"UserCode": "'+userCode+'"}'

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetUserImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
#导入前检查
@import_file_user.route('/isexist_import',methods=['GET', 'POST'])
def isexist_import():
	se = request.form.get('a0')
	#name = request.form.get('z1')
	file_v = request.form.get('file_v')
	debug("1231313")
	fname = file_v
	debug('fname:%s' % fname);
	f_name = fname[:-4]
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
			sql = "select us.\"Status\",us.\"UserImportTaskName\" from private.\"UserImportTask\" as us where \"UserImportTaskName\" = E\'%s\'" % MySQLdb.escape_string(f_name).decode("utf-8")
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			#results = curs.fetchone()
			debug("________aaa_______"+str(len(results)))
			for i in range(len(results)):
				a=results[i];
				b=a[0];
				if b==0:
					system_log(userCode, "创建用户导入任务：%s" % fname, "失败：该任务已存在", "运维管理>用户管理")
					return "{\"Result\":false}"
			debug("eee")
			return "{\"Result\":true}"
			# if len(results) == 0:
			# 	return "{\"Result\":true}"
			# else:
			# 	system_log(userCode,"创建用户导入任务：%s" % fname,"失败：该任务已存在","运维管理>用户管理")
			# 	return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
#详情
@import_file_user.route('/get_import_detail_user',methods=['GET', 'POST'])
def get_import_detail_user():
	se = request.form.get('a0')
	t_id = request.form.get('a1')
	keyword = request.form.get('a2')
	limitrow = request.form.get('a3')
	offsetrow = request.form.get('a4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if keyword < 0 or keyword == "":
		keyword = 0
	if keyword == 0:
		status = "null"
	else:
		status = str(keyword)
	if limitrow == "null":
		offsetrow = "null"
	data = '{"UserImportTaskId":'+t_id+',"Status":'+status+',"limitrow": '+limitrow+',"offsetrow": '+offsetrow+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetUserImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###############指令授权

#导入
@import_file_user.route('/import_data_cmd',methods=['GET', 'POST'])
def import_data_cmd():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	cover = request.form.get('a1')
	use_BH = request.form.get('a99')
	if use_BH=='0':
		f = request.files['file_change1']
		file_v = secure_filename(f.filename)
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
	if check_role(system_user,'指令授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	fname = file_v
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	debug(file_pwd)
	if use_BH=='0':
		f.save(os.path.join(UPLOAD_FOLDER, fname))
	else:
		shutil.move(file_change,file_pwd)
	debug("12313")
	taskid = 0
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:#新建任务
			curs = conn.cursor()
			sql = "SELECT nextval('private.\"AuthImportTask_AuthImportTaskId_seq\"'::regclass);"
			debug(sql)
			curs.execute(sql)
			taskid = curs.fetchall()[0][0]
			sql = "SELECT \"UserId\" from public.\"User\" where \"UserCode\"='%s';"%(MySQLdb.escape_string(system_user).decode("utf-8"))
                        curs.execute(sql)
                        userid=curs.fetchall()[0][0]	
			sql = "insert into private.\"AuthImportTask\"(\"AuthImportTaskId\",\"AuthImportTaskName\",\"Type\",\"UserId\") values(%d,E'%s',3,%s);" %(taskid,MySQLdb.escape_string(taskname).decode("utf-8"),userid)
			debug(sql)
			curs.execute(sql)
			conn.commit()
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	task_content = '[global]\nclass = taskimport_user\ntype = execute_cmdlist\nfile_pwd=\"%s\"\ncover=\"%s\"\ntaskid=\"%s\"\nusercode=\"%s\"\nclientip=\"%s\"\n' % (file_pwd,cover,str(taskid),system_user,client_ip)
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		debug("hhhhhhh")
		curs.close()
		conn.close()
		system_log(system_user,"创建指令授权导入任务：%s" % fname,"失败：任务下发异常","运维管理>指令授权")
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)

	system_log(system_user,"创建指令授权导入任务：%s" % fname,"成功","运维管理>指令授权")
	return "{\"Result\":true}"

#删除导入文件
@import_file_user.route('/del_cmdtask',methods=['GET', 'POST'])		
def del_cmdtask():
	se = request.form.get('a0')
	del_id = request.form.get('a1')
	debug(str(del_id))
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(userCode,'指令授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			id_array = str(del_id).split(',')
			debug(str(id_array))
			Name_arry = []
			for id_v in id_array:
				debug(str(id_v))
				curs.execute("select \"AuthImportTaskName\" from private.\"AuthImportTask\" where \"AuthImportTaskId\" = %d;" % int(id_v))
				result_1 = curs.fetchall()[0][0].encode('utf-8')
				Name_arry.append(result_1)

				curs.execute("delete from private.\"AuthImportTask\" where  \"AuthImportTaskId\" = %d;" % int(id_v))

			system_log(userCode,"删除指令授权导入任务：%s" % ('、'.join(Name_arry)),"成功","运维管理>指令授权")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#明细
@import_file_user.route('/get_cmdtask_detail',methods=['GET', 'POST'])
def get_cmdtask_detail():
	se = request.form.get('a0')
	cur = request.form.get('a1')
	page_total = request.form.get('a2')

	taskid = request.form.get('a4')
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


	data = '{"AuthImportTaskId":'+taskid+',"Status":'+status+',"limitrow": '+page_total+',"offsetrow": '+offsetrow+',"UserCode": "'+userCode+'"}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#列表
@import_file_user.route('/get_cmdtask_data',methods=['GET', 'POST'])
def get_cmdtask_data():
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
	data = '{"AuthImportTaskId":null,"Type":3,"limitrow":'+page_total+',"offsetrow":'+offsetrow+',"UserCode": "'+userCode+'"}'

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#导入前检查
@import_file_user.route('/isexist_import_cmd',methods=['GET', 'POST'])
def isexist_import_cmd():
	se = request.form.get('a0')
	#name = request.form.get('z1')
	file_v = request.form.get('file_v')
	debug("1231313")
	fname = file_v
	debug('fname:%s' % fname);
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select * from private.\"AuthImportTask\" where \"AuthImportTaskName\" = E\'%s\' and \"Type\" = E\'%s\' and \"Status\"=0;" % (MySQLdb.escape_string(taskname).decode("utf-8"),'3')
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				return "{\"Result\":true}"
			else:
				system_log(userCode,"创建指令授权导入任务：%s" % fname,"失败：该任务已存在","运维管理>指令授权")
				return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#详情
@import_file_user.route('/get_import_detail_cmd',methods=['GET', 'POST'])
def get_import_detail_cmd():
	se = request.form.get('a0')
	t_id = request.form.get('a1')
	keyword = request.form.get('a2')
	limitrow = request.form.get('a3')
	offsetrow = request.form.get('a4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if keyword < 0 or keyword == "":
		keyword = 0
	if keyword == 0:
		status = "null"
	else:
		status = str(keyword)
	if limitrow == "null":
		offsetrow = "null"
	data = '{"AuthImportTaskId":'+t_id+',"Status":'+status+',"limitrow": '+limitrow+',"offsetrow": '+offsetrow+',"UserCode": "'+userCode+'"}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
