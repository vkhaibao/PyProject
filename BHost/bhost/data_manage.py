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
import shutil

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from index import PGetPermissions

from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader
from werkzeug.utils import secure_filename
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

data_manage = Blueprint('data_manage',__name__)
env = Environment(loader = FileSystemLoader('templates'))

def debug(c):
	return 0
        path = "/var/tmp/debugdata_manage.txt"
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
	
#error encode
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"',"'").replace('\n',"\\n")
	return newStr

@data_manage.route('/data_show',methods=['GET', 'POST'])
def data_show():
		tasktype = request.form.get("tasktype")
		sess =request.form.get('se')
		if sess<0 or sess==None:
			sess=request.args.get('se')
		if tasktype < 0 or tasktype == None:
			tasktype = "1"
		if tasktype == "1":
			t = "archiving_strategy.html"
		elif tasktype == "2":
			t = "manual_backup.html"
		elif tasktype == "3":
			t = "data_recovery.html"
		elif tasktype == "4":
			t = "auto_archiving.html"
		elif tasktype == "5":
			t = "data_2recovery.html"
		
		client_ip = request.remote_addr
		(error,us,mac) = SessionCheck(sess,client_ip)
		error_msg=''
		if error < 0:
			error_msg = "系统繁忙(%d)" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				error_msg = "非法访问"
			else:
				error_msg = "系统超时" 
		_power=PGetPermissions(us)
		_power_json = json.loads(str(_power));
		_power_mode = 2;
		for one in _power_json:
			if one['SystemMenuId'] == 6:
				_power_mode = one['Mode']
		
		return render_template(t,tasktype = tasktype,se=sess,_power_mode=_power_mode)

#取配置归档策略
@data_manage.route('/get_archive_strategy', methods=['GET', 'POST'])
def get_archive_strategy():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 50000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PGetLogArchiveStrategy\"();"
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results==None:
				results='null'
			return "{\"Result\":true,\"info\":%s}" %results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#保存数据归档策略
@data_manage.route('/save_archive_strategy', methods=['GET', 'POST'])
def save_archive_strategy():
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
	jsondata = request.form.get('a1')
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	data = str(jsondata)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PSaveLogArchiveStrategy\"(E'%s');" %(MySQLdb.escape_string(data).decode("utf-8"))
			curs.execute(sql)
			debug(sql)
			results = curs.fetchall()[0][0]
			if 'false' in results:
				if not system_log(system_user,'编辑归档策略','参数错误','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				conn.commit()
				data=json.loads(data)
				oper='编辑归档策略（'
				if data['ArchiveStyle']==1:
					oper=oper+'归档类型：配额归档，磁盘配额：%s%%，'%(data['DiskLimit'])
				else:
					oper=oper+'归档类型：配额归档，存储周期：%s，'%(data['StoragePeriod'])
				if data['ArchiveType']==0:
					oper=oper+'归档方式：本地保存'
				elif  data['ArchiveType']==1:
					oper=oper+'归档方式：自动丢弃'
				else:
					oper=oper+'归档方式：FTP上传，'
					if data['FTPServerId']==0:
						oper=oper+'FTP配置：默认'
					else:
						sql_ftp = "select ftp.\"FTPServerName\" from  public.\"FTPServer\" ftp where ftp.\"FTPServerId\"=%s;" %(data['FTPServerId'])
						curs.execute(sql_ftp)
						results_ftp = curs.fetchall()[0][0]
						oper=oper+'FTP配置：%s'%(results_ftp)
				oper=oper+'）'
				if not system_log(system_user,oper,'成功','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#获取数据恢复任务列表
@data_manage.route('/get_lrecovery_task', methods=['GET', 'POST'])
def get_lrecovery_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num = request.form.get('a1')
	paging = request.form.get('a2')
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
	if paging < 0:
		paging = 'null'
	else:
		paging = int(paging)
	if num < 0:
		num = 'null'
	else:
		num = int(num)
	if paging!='null':
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PGetLogRecoveryTask\"(E'%s',%s,%s);" %(system_user,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" %results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#上传文件
@data_manage.route('/import_recovery_data',methods=['GET','POST'])
def import_recovery_data():
	debug('import_recovery_data')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num=request.form.get('a1')
	debug(str(num))
	num=int(num)
	type_name=request.form.get('a2')
	file_save=request.form.get('a3')
	recover=request.form.get('a10')
	use_BH=request.form.get('a99')
	if use_BH=='1':
		filename=request.form.get('filename')
		fname=request.form.get('fname')
	else:
		f = request.files['filename1']
		fname = secure_filename(f.filename) #获取一个安全的文件名，且仅支持ascii字符；
	if session < 0:
		session = ""
	if recover<0:
		recover='upload'
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
	if type_name<0 or type_name==None:
			fname = fname.decode('utf-8')
			debug(str(fname))
			if os.path.exists('/usr/storage/.system/'+recover+'/%s_%s'%(system_user,fname)):
				return '{\"Result\":false,\"ErrMsg\":\"存在同名的文件\"}'
			type_name='1'
	debug('type_name:%s'%(str(type_name)))
	if	type_name=='1':
			if not fname:
				if not system_log(system_user,'上传文件','上传失败','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return '{\"Result\":false,\"ErrMsg\":\"上传失败\"}'
			fname = fname.decode('utf-8')
			fpath_all='/usr/storage/.system/'+recover+'/%s_%s'%(system_user,fname)
			if use_BH=='1':
				shutil.move(filename,fpath_all)
			else:
				f.save(fpath_all)
			if not system_log(system_user,'上传文件：%s'%(fname),'成功','系统管理>数据管理'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			if file_save==None or file_save<0:
				json_task={
					"LoginUserCode":system_user,
					"LogRecoveryTaskId": 0,    
					"FileName": fpath_all,
					"Status": 0,
					"CancelStatus":0,
					"Memo":None
				}
				debug(str(json_task))
				try:
					with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
						debug('-2-2-2-')
						sql = "select public.\"PSaveLogRecoveryTask\"(E'%s');" %(MySQLdb.escape_string(str(json.dumps(json_task))).decode("utf-8"))
						debug(str(sql))
						curs.execute(sql)
						results = curs.fetchall()[0][0]
						conn.commit()
						debug(str(results))
						results_all=json.loads(results)
						debug(str(results_all))
						if not results_all['Result']:
							if not system_log(system_user,'创建数据恢复任务（恢复文件：%s）'%(fname),results_all['ErrMsg'],'系统管理>数据管理'):
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return results
						sql_item = "select log.\"SubmitTime\" from private.\"LogRecoveryTask\" log where log.\"TaskId\"=%s;" %(results_all['LogRecoveryTaskId'])
						curs.execute(sql_item)
						results_item=curs.fetchall()[0][0]
						debug(str(results_item))
						if not system_log(system_user,'创建数据恢复任务（任务提交时间：%s，恢复文件：%s）'%(results_item,fname),'成功','系统管理>数据管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				except pyodbc.Error,e:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif type_name=='2':
			if not fname:
				if not system_log(system_user,'上传文件','上传失败','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return '{\"Result\":false,\"ErrMsg\":\"上传失败\"}'
			fname = fname.decode('utf-8')
			fpath_all='/usr/storage/.system/'+recover+'/%s_%s'%(system_user,fname)
			if not os.path.exists(fpath_all):
				if use_BH=='1':
					shutil.move(filename,fpath_all)
				else:
					f.save(fpath_all)
				if not system_log(system_user,'上传文件：%s'%(fname),'成功','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			if file_save==None or file_save<0:
				json_task={
					"LoginUserCode":system_user,
					"LogRecoveryTaskId": 0,    
					"FileName": fpath_all,
					"Status": 0,
					"CancelStatus":0,
					"Memo":None
				}
				debug(str(json_task))
				try:
					with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
						sql = "select public.\"PSaveLogRecoveryTask\"(E'%s');" %(MySQLdb.escape_string(str(json.dumps(json_task))).decode("utf-8"))
						debug(str(sql))
						curs.execute(sql)
						results = curs.fetchall()[0][0]
						conn.commit()
						debug(str(results))
						results_all=json.loads(results)
						debug(str(results_all))
						if not results_all['Result']:
							if not system_log(system_user,'创建数据恢复任务（恢复文件：%s）'%(fname),results_all['ErrMsg'],'系统管理>数据管理'):
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return results
						sql_item = "select log.\"SubmitTime\" from private.\"LogRecoveryTask\" log where log.\"TaskId\"=%s;" %(results_all['LogRecoveryTaskId'])
						curs.execute(sql_item)
						results_item=curs.fetchall()[0][0]
						debug(str(results_item))
						if not system_log(system_user,'创建数据恢复任务（任务提交时间：%s，恢复文件：%s）'%(results_item,fname),'成功','系统管理>数据管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				except pyodbc.Error,e:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return '{\"Result\":true,\"info\":\"上传成功\"}'

#停用恢复任务
@data_manage.route('/stop_recovery_task',methods=['GET','POST'])
def stop_recovery_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	task_id=request.form.get('a1')
	task_name=request.form.get('a2')
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
			sql = "UPDATE private.\"LogRecoveryTask\" log SET \"CancelStatus\"=1 WHERE  log.\"TaskId\"=%s;"%(task_id)
			curs.execute(sql)
			debug(sql)
			conn.commit()
			if not system_log(system_user,'取消数据恢复任务（恢复文件：%s）'%(task_name),'成功','系统管理>数据管理'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#取消数据备份任务
@data_manage.route('/stop_backup_task',methods=['GET','POST'])
def stop_backup_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	task_id=request.form.get('a1')
	task_name=request.form.get('a2')
	task_time=request.form.get('a3')
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
			sql = "select log.\"Status\",log.\"CancelStatus\" from private.\"LogBackupTask\" log WHERE  log.\"TaskId\"=%s;"%(task_id)
			curs.execute(sql)
			results = curs.fetchall()
			if (results[0][0]==2 or results[0][0]==3):
				return "{\"Result\":false,\"ErrMsg\":\"该日志无法取消\"}"
			if  results[0][1]==1:
				return "{\"Result\":false,\"ErrMsg\":\"该日志已被取消\"}"
			sql = "UPDATE private.\"LogBackupTask\" log SET \"CancelStatus\"=1 WHERE  log.\"TaskId\"=%s;"%(task_id)
			curs.execute(sql)
			debug(sql)
			conn.commit()
			if not system_log(system_user,'取消数据备份任务（备份时间范围：%s，任务提交时间：%s）'%(task_name,task_time),'成功','系统管理>数据管理'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#start_recovery_task启用数据恢复任务
@data_manage.route('/start_recovery_task',methods=['GET','POST'])
def start_recovery_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	task_id=request.form.get('a1')
	task_name=request.form.get('a2')
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
			sql = "UPDATE private.\"LogRecoveryTask\" log SET \"Memo\"=null,\"CancelStatus\"=0,\"Status\"=0 WHERE  log.\"TaskId\"=%s;"%(task_id)
			curs.execute(sql)
			debug(sql)
			conn.commit()
			if not system_log(system_user,'启用数据恢复任务（恢复文件：%s）'%(task_name),'成功','系统管理>数据管理'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#删除数据恢复任务列表
@data_manage.route('/del_lrecovery_task', methods=['GET', 'POST'])
def del_lrecovery_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)x\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
		
	if check_role(system_user,"系统管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			for id in ids:
				id = int(id)
				sql_item = "select log.\"SubmitTime\",log.\"FileName\" from private.\"LogRecoveryTask\" log where log.\"TaskId\"=%s;" %(id)
				debug(sql_item)
				curs.execute(sql_item)
				result_item = curs.fetchall()
				debug(str(result_item))
				debug(str(result_item[0][0]))
				debug(str(result_item[0][1]))
				result_item[0][1]=result_item[0][1].split('\/')[-1]
				result_item[0][1]=result_item[0][1][result_item[0][1].find('_')+1:]
				sql = "select public.\"PDeleteLogRecoveryTask\"(%d);" %(id)
				debug(sql)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				if "false" in result:
					if not system_log(system_user,'删除数据恢复任务（恢复文件：%s）'%(result_item[0][1]),'参数错误','系统管理>数据管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					fail_num+=1
				else:
					conn.commit()
					if not system_log(system_user,'删除数据恢复任务（恢复文件：%s）'%(result_item[0][1]),'成功','系统管理>数据管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					success_num+=1
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s}" %(success_num,fail_num)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#获取数据恢复文件列表
@data_manage.route('/get_lrecovery_file', methods=['GET', 'POST'])
def get_lrecovery_file():
	debug('get_lrecovery_file')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num = request.form.get('a1')
	paging = request.form.get('a2')
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
	if check_role(system_user,"系统管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	if paging < 0:
		paging = 'null'
	else:
		paging = int(paging)
	if num < 0:
		num = 'null'
	else:
		num = int(num)
	if paging!='null':
		paging=(paging-1)*num
	info_json={}
	path='/usr/storage/.system/upload'
	file_name_arr=os.listdir(path)
	debug(str(file_name_arr))
	file_name_arr=filter(lambda x:x[-5:] =='.slzs',file_name_arr)
	debug(str(file_name_arr))
	for num,i in enumerate(file_name_arr):
		file_name_arr[num]={
			"FileName":path+'/'+i,
			"ImportTime":os.path.getmtime(path+'/'+i)
		}
		debug(str(i))
	debug(str(file_name_arr))
	file_name_arr.sort(key=lambda file_name_arr_ind:file_name_arr_ind["ImportTime"],reverse=True)
	debug(str(file_name_arr))
	info_json["totalrow"]=len(file_name_arr)
	data_arr=[]
	for file_name_index,file_name_value in enumerate(file_name_arr):
		if (paging!='null' and (file_name_index>=paging and file_name_index<paging+10)) or paging=='null':
			json_index={}
			json_index["FileName"]=file_name_value['FileName']
			json_index["ImportTime"]=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(file_name_value['ImportTime']))
			fsize=os.path.getsize(json_index["FileName"])
			fsize_type=' B'
			if fsize>1024:
				fsize=fsize/float(1024)
				fsize_type=' K'
				if fsize>1024:
					fsize=fsize/float(1024)
					fsize_type=' M'
					if fsize>1024:
						fsize=fsize/float(1024)
						fsize_type=' G'
						if fsize>1024:
							fsize=fsize/float(1024)
							fsize_type=' T'
			json_index["FileSize"]='%s%s'%(str(float(int(fsize*100))/100),fsize_type)
			data_arr.append(json_index)
	info_json["data"]=data_arr
	return "{\"Result\":true,\"info\":%s}" %(json.dumps(info_json).decode('utf-8'))	

#删除数据恢复文件
@data_manage.route('/del_lrecovery_file', methods=['GET', 'POST'])
def del_lrecovery_file():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
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
	if check_role(system_user,"系统管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	if id_str < 0:
		id_str = ""
	ids = id_str.split('\t')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			for id in ids:
				# id = int(id)
				# sql_item = "select log.\"ImportTime\",log.\"FileName\" from private.\"LogRecoveryFile\" log where log.\"LogRecoveryFileId\"=%s;" %(id)
				# debug(sql_item)
				# curs.execute(sql_item)
				# result_item = curs.fetchall()
				# debug(str(result_item))
				# debug(str(result_item[0][0]))
				# debug(str(result_item[0][1]))
				file_name=id.split('\/')[-1]
				file_name=file_name[file_name.find('_')+1:]
				# sql = "select public.\"PDeleteLogRecoveryFile\"(%d);" %(id)
				# debug(sql)
				# curs.execute(sql)
				# result = curs.fetchall()[0][0]
				# if "false" in result:
				# 	if not system_log(system_user,'删除数据恢复文件：%s'%(file_name),'参数错误','系统管理>数据管理'):
				# 		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				# 	fail_num+=1
				# else:
				# 	conn.commit()
				if os.path.exists(id):
					os.remove(id)
				if not system_log(system_user,'删除数据恢复文件：%s'%(file_name),'成功','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				# success_num+=1
			return "{\"Result\":true}"
			# return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s}" %(success_num,fail_num)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#下载数据恢复文件
@data_manage.route('/download_recover_file',methods=['GET','POST'])
def download_recover_file():
	debug('download_recover_file')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	down_path=request.form.get('a1')
	debug(str(down_path))
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
	debug(str(system_user))
	path_array=down_path.split('/')
	debug(str(path_array))
	down_file=path_array.pop(len(path_array)-1)
	debug(str(down_file))
	path='/'.join(path_array)
	debug(str(path))
	filename=down_file[down_file.find('_')+1:]
	debug(str(filename))
	if not system_log(system_user,'下载数据恢复文件：%s'%(filename),'成功','系统管理>数据管理'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return send_from_directory(path,down_file,as_attachment=True,attachment_filename=filename)

#判断文件是否存在
@data_manage.route('/file_exit',methods=['GET','POST'])
def file_exit():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	down_path=request.form.get('a1')
	type_name=request.form.get('a2')
	debug(str(down_path))
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
	if not os.path.exists(down_path):
		path_array=down_path.split('/')
		debug(str(path_array))
		down_file=path_array.pop(len(path_array)-1)
		if not system_log(system_user,'下载%s文件：%s'%(type_name,down_file),'文件不存在','系统管理>数据管理'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":'文件不存在'}"
	return "{\"Result\":true,\"info\":true}"

#下载数据备份文件
@data_manage.route('/download_backup_file',methods=['GET','POST'])
def download_backup_file():
	debug('download_backup_file')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	down_path=request.form.get('a1')
	type_=request.form.get('a2')
	type_name=request.form.get('a3')
	debug(str(down_path))
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
	debug(str(system_user))
	path_array=down_path.split('/')
	debug(str(path_array))
	down_file=path_array.pop(len(path_array)-1)
	debug(str(down_file))
	path='/'.join(path_array)
	debug(str(path))
	if type_=='2':
		filename=down_file
	else:
		filename=down_file[down_file.find('_')+1:]
		debug(str(filename))
	if not system_log(system_user,'下载%s文件：%s'%(type_name,filename),'成功','系统管理>数据管理'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return send_from_directory(path,down_file,as_attachment=True,attachment_filename=filename)

#创建恢复任务
@data_manage.route('/make_recovery_task',methods=['GET','POST'])
def make_recovery_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	recovery_id_str=request.form.get('a1')
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
	recovery_id_arr=recovery_id_str.split('\t')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			for _id in recovery_id_arr:
				# sql_file_item = "select log.\"FileName\" from private.\"LogRecoveryFile\" log where log.\"LogRecoveryFileId\"=%s;" %(_id)
				# curs.execute(sql_file_item)
				# recovery_path=curs.fetchall()[0][0]
				debug(str(_id))
				path_array=_id.split('/')
				down_file=path_array.pop(len(path_array)-1)
				recovery_name=down_file[down_file.find('_')+1:]
				json_task={
					"LoginUserCode":system_user,
					"LogRecoveryTaskId": 0,    
					"FileName": '/usr/storage/.system/recover/'+down_file,
					"Status": 0,
					"CancelStatus":0,
					"Memo":None
				}
				if not os.path.exists(_id):
					fail_num+=1
					continue
				else:
					shutil.move(_id,'/usr/storage/.system/recover/'+down_file)
				debug(str(json_task))
				sql = "select public.\"PSaveLogRecoveryTask\"(E'%s');" %(MySQLdb.escape_string(str(json.dumps(json_task))).decode("utf-8"))
				debug(str(sql))
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				debug(str(results))
				results_all=json.loads(results)
				debug(str(results_all))
				if not results_all['Result']:
					if not system_log(system_user,'创建数据恢复任务（恢复文件：%s）'%(recovery_name),results_all['ErrMsg'],'系统管理>数据管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					fail_num+=1
					# return results
				else:
					conn.commit()
					sql_item = "select log.\"SubmitTime\" from private.\"LogRecoveryTask\" log where log.\"TaskId\"=%s;" %(results_all['LogRecoveryTaskId'])
					curs.execute(sql_item)
					results_item=curs.fetchall()[0][0]
					debug(str(results_item))
					if not system_log(system_user,'创建数据恢复任务（任务提交时间：%s，恢复文件：%s）'%(results_item,recovery_name),'成功','系统管理>数据管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					success_num+=1
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s}"%(success_num,fail_num)
				# return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#获取数据备份任务列表
@data_manage.route('/get_lbackup_task', methods=['GET', 'POST'])
def get_lbackup_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num = request.form.get('a1')
	paging = request.form.get('a2')
	tasktype = request.form.get('a3')
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
	if tasktype < 0 or tasktype == "":
		tasktype = "null"
	if paging < 0:
		paging = 'null'
	else:
		paging = int(paging)
	if num < 0:
		num = 'null'
	else:
		num = int(num)
	if paging!='null':
		paging=(paging-1)*num
	if tasktype=='0':
		system_user='null'
	else:
		system_user="E'%s'"%system_user
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PGetLogBackupTask\"(%s,%s,%s,%s);" %(tasktype,system_user,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return "{\"Result\":true,\"info\":%s}" %results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#创建数据备份任务
@data_manage.route('/save_lbackup',methods=['GET','POST'])
def save_lbackup():
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
	jsondata = request.form.get('a1')
	data = str(jsondata)
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	data=json.loads(data)
	data['LoginUserCode']=system_user
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# sql_ftp='select log."FTPServerId",log."ArchiveType" FROM public."LogArchiveStrategy" log'
			# curs.execute(sql_ftp)
			# results_all=curs.fetchall()
			# results_ftp =results_all[0][0]
			# results_type=results_all[0][1]
			# if results_type==2 and (results_ftp==None or results_ftp==0):
			# 	sql_flag_2='select ftp."FTPServerId" FROM public."FTPServer" ftp WHERE ftp."Flag"=2'
			# 	curs.execute(sql_flag_2)
			# 	results_ftp_flag_2= curs.fetchall()[0][0]
			# 	if results_ftp_flag_2==None or results_ftp_flag_2==0:
			# 		if not system_log(system_user,'创建数据备份任务','FTP服务器未配置','系统管理>数据管理'):
			# 			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			# 		return "{\"Result\":false,\"ErrMsg\":\"FTP服务器未配置\"}"
			# 	else:
			# 		data['FTPServerId']=results_ftp_flag_2
			# elif results_type==2:
			# 	data['FTPServerId']=results_ftp
			jsondata=json.dumps(data)
			sql = "select public.\"PSaveLogBackupTask\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results_json=json.loads(results)
			if not results_json['Result']:
				if not system_log(system_user,'创建数据备份任务',results_json['ErrMsg'],'系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				results_all=json.loads(results)
				conn.commit()
				sql_item = "select log.\"SubmitTime\" from private.\"LogBackupTask\" log where log.\"TaskId\"=%s;" %(results_all['LogBackupTaskId'])
				curs.execute(sql_item)
				results_item=curs.fetchall()[0][0]
				debug(str(results_item))
				if data['FTPServerId']==None:
					oper_ftp='方式：本地保存'
				else:
					oper_ftp='方式：FTP上传'
				if not system_log(system_user,'创建数据备份任务（任务提交时间：%s，备份时间范围：%s 至 %s，%s）'%(results_item,data['StartTime'],data['EndTime'],oper_ftp),'成功','系统管理>数据管理'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)


#删除数据备份任务
@data_manage.route('/del_lbackup', methods=['GET', 'POST'])
def del_lbackup():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	type_name=request.form.get('a2')
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
	if check_role(system_user,"系统管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			for id in ids:
				id = int(id)
				sql_item = "select log.\"StartTime\",log.\"EndTime\",log.\"FileName\",log.\"SubmitTime\" from private.\"LogBackupTask\" log where log.\"TaskId\"=%s;" %(id)
				debug(sql_item)
				curs.execute(sql_item)
				result_item = curs.fetchall()
				debug(str(result_item))
				debug(str(result_item[0][0]))
				debug(str(result_item[0][1]))
				debug(str(result_item[0][2]))
				sql = "select public.\"PDeleteLogBackupTask\"(%d);" %(id)
				debug(sql)
				curs.execute(sql)
				result = curs.fetchall()[0][0].encode('utf-8')
				debug(str(result))
				result_json=json.loads(result)
				if not result_json['Result']:
					if not system_log(system_user,'删除%s任务（备份时间范围：%s 至 %s，任务提交时间：%s）'%(type_name,str(result_item[0][0]).split(' ')[0],str(result_item[0][1]).split(' ')[0],result_item[0][3]),result_json['ErrMsg'],'系统管理>数据管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					fail_num+=1
				else:
					conn.commit()
					if not system_log(system_user,'删除%s任务（备份时间范围：%s 至 %s，任务提交时间：%s）'%(type_name,str(result_item[0][0]).split(' ')[0],str(result_item[0][1]).split(' ')[0],result_item[0][3]),'成功','系统管理>数据管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					debug(str(result_item[0][2]))
					sql_count="select count(*) from private.\"LogBackupTask\" log where log.\"FileName\"='%s';"%result_item[0][2]
					curs.execute(sql_count)
					result_sql_count = curs.fetchall()[0][0]
					if result_sql_count==0 and result_item[0][2]!='' and result_item[0][2]!=None and os.path.exists(result_item[0][2]):
						os.remove(result_item[0][2])
					debug(str(success_num))
					success_num+=1
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s}" %(success_num,fail_num)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#----------------------------------------------------------------------------------------------------


