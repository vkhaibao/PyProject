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
import datetime
import shutil

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import defines
from logbase import task_client
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
system_update = Blueprint('system_update',__name__)
from generating_log import system_log

UPLOAD_FOLDER = '/usr/storage/.system/update'


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
	
@system_update.route('/system_update_show',methods=['GET', 'POST'])
def system_update_show():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data="KERNEL is X64KERNEL_VERSION_MAJOR is 6 KERNEL_VERSION_MINOR is 18FLASH_DISK is hdaIS_SLV is 0"
	system_type = common.get_server_cluster_type();
	return render_template('system_update.html',data=data,system_type=system_type)
	
#系统升级信息回显 ok3-8
@system_update.route('/get_sysupdate',methods=['GET', 'POST'])
def get_sysupdate():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('se')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	oper = "系统升级"
	
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	version = ""	
	if os.path.exists(UPLOAD_FOLDER):

		list_file = os.listdir(UPLOAD_FOLDER)
		file_arr = []		
		if list_file:
			for file in list_file:
				if os.path.isdir(UPLOAD_FOLDER + "/" + file) and len(file)>8:
					if file[0:3] == "bh-" :
						file_arr.append(file)
			if file_arr :
				filedate = file_arr[0][-10:]
				
				if len(file_arr) > 1:
					t1 = os.path.getmtime(UPLOAD_FOLDER +'/' + file_arr[0])
					for files in file_arr:
						t2 = os.path.getmtime(UPLOAD_FOLDER +'/' + files)
						if t2>=t1:
							version = files
							t1 = t2
				else:
					version = file_arr[0]
		
		sql = "select server_id,ip from server_global;"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		rows = curs.fetchall()
		
		node_id_all = ""
		if rows == 0:
			curs.close()
			conn.close()
			return "{\"Result\":true,\"info\":\"\",\"file\":\"%s\"}" %(version)
		else:
			for row in rows:
				node_id = str(row[0])
				node_ip = row[1]
				node_id_all = node_id_all + node_id + " ( " + node_ip + " ) " + ","
			if node_id_all :
				node_id_all = node_id_all[:-1]
		
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":\"%s\",\"file\":\"%s\"}" %(node_id_all,version)
	else:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: 路径不存在(%d)\"}" %(sys._getframe().f_lineno)
#系统升详细信息回显 ok9-10
@system_update.route('/getsys_info',methods=['GET', 'POST'])
def getsys_info():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('se')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		
	node_id = request.form.get('node_id')
	node_id_str = node_id.split('(')
	node_id_s = node_id_str[0].strip()
	version = ''
	last_time =""
	idstr = ""
	#debug(node_id_s)
	##获取版本
	if os.path.exists(UPLOAD_FOLDER):
		list_file = os.listdir(UPLOAD_FOLDER)
		file_arr = []
		if not list_file:
			version = ""
		else:
			for file in list_file:
				if os.path.isdir(UPLOAD_FOLDER + "/" + file) and len(file)>8:
					if file[0:3] == "bh-" :
						file_arr.append(file)
			debug(str(file_arr))
			if not file_arr :
				version = ""
			else :
				filedate = file_arr[0][-10:]
				
				if len(file_arr) > 1:
					t1 = os.path.getmtime(UPLOAD_FOLDER +'/' + file_arr[0])
					for files in file_arr:
						t2 = os.path.getmtime(UPLOAD_FOLDER +'/' + files)
						if t2>=t1:
							version = files
							t1 = t2
				else:
					version = file_arr[0]
	debug(str(version))				
	update_type = request.form.get('update_type')
	node_str = request.form.get('node_str')
	#debug(node_str)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常 :%s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#debug(sql)
	if node_id_s =="":
		return "{\"Result\":true,\"info\":\"\",\"version\":\"%s\",\"last_time\":\"\",\"id\":\"\"}" %(version)
	sql = "select cont,happen,id from  logs_update  where server_id=%s order by happen desc limit 2;" %(node_id_s)
	#debug(sql)	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#debug("1")
	results = curs.fetchall()
	sys_info = ''
	
	if results :
		id = results[0][2]
		#debug(results[0][0])
		if update_type == "new":
			sys_info = results[0][0]
			#result = results[0][0].encode('utf-8').split('	')
			
			#debug(str(result))
			#sys_info = base64.b64decode(result[0]) +  base64.b64decode(result[1]) + base64.b64decode(result[2])
			#debug(str(sys_info))
		else:
			if len(results) > 1:
				sys_info = results[1][0].encode('utf-8')
				#result = results[1][0].encode('utf-8').split('	')
				#sys_info = base64.b64decode(result[0]) +  base64.b64decode(result[1]) + base64.b64decode(result[2])	
		if len(results) > 1:
			#debug(str(results[1][1]))
			happen = results[1][1];
			#debug(str(happen))
			last_time = datetime.datetime.strftime(happen, '%Y-%m-%d %H:%M:%S')
	#debug("2")		
	##获取 升级之前的最大的日志 id
	count_str = '';
	if not node_str =="":
		node_list = node_str.split(',')
		#debug(str(node_list))
		for node_s in node_list:
			node_id_str = node_s.split('(')
			node_id_s = node_id_str[0].strip()
			sql = "select id from  logs_update  where server_id=%s order by happen desc limit 1;" %(node_id_s)
			#debug(sql)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
			#debug(sql)
			results = curs.fetchall()
			if results:
				idstr = idstr + str(results[0][0]) +','
				
			sql = "select count(*) from  logs_update  where server_id=%s;" %(node_id_s)
			#debug(sql)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)			
			results = curs.fetchall()
			count_str = count_str +str(results[0][0]) +','
			
			
		idstr = idstr[:-1]
		count_str = count_str[:-1];
	curs.close()
	conn.close()
	#sys_info = sys_info.decode('gbk')
	#sys_info = sys_info.encode('utf-8')
	
	return "{\"Result\":true,\"info\":\"%s\",\"version\":\"%s\",\"last_time\":\"%s\",\"id\":\"%s\",\"count_str\":\"%s\"}" %(sys_info,version,last_time,idstr,count_str)

#查找文件
@system_update.route('/find_item_sql',methods=['GET','POST'])
def find_item_sql():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	sesstimet = request.form.get('a1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip);
	oper = "系统升级"
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:#新建任务
			sql = "select \"CertInfo\" from private.\"USBKeyResult\" where \"Status\"=3 and \"SessTime\"='%s';" %(sesstimet)
			curs.execute(sql)
			list_arr = curs.fetchall()
			if len(list_arr)==1:
				#sql = "update private.\"USBKeyResult\" set \"Status\"=1 where \"SessTime\"='%s';" %(sesstimet)
				#curs.execute(sql)
				return '{"Result":true,"info":"%s"}'%(list_arr[0][0])
			else:
				return '{"Result":true,"info":null}'
	except Exception,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)%s\"}" %(sys._getframe().f_lineno,str(e))

#系统升级
@system_update.route('/sys_updata',methods=['GET', 'POST'])
def sys_updata():
	try:
		reload(sys)
		sys.setdefaultencoding('utf-8')
		session = request.form.get('se')
		use_BH = request.form.get('a99')
		server_id = request.form.get('s1')
		if server_id and server_id !='-1':
			node_id_str = server_id.split('(')
			server_id = node_id_str[0].strip()
			if str(server_id).isdigit() == False:
				return '',403
			
		client_ip = request.remote_addr
		(error,system_user,mac) = SessionCheck(session,client_ip);
		oper = "系统升级"
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			sys.exit()
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
		sys_ok = 1  #判断是否升级正常完成
		is_dir_in = 0  #判断解压后的文件夹是否存在
		is_sh_in = 0  #判断脚本文件PNUpdate.sh是否存在
		if use_BH=='1':
			file_change = request.form.get('file_change')
			file_v = request.form.get('file_v')
			fname=file_v
		else:
			f = request.files['file_change1']
			fname = secure_filename(f.filename) #获取一个安全的文件名，且仅支持ascii字符；
		if not os.path.exists(UPLOAD_FOLDER): 
			sys_ok = 2
			return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
		else:
			if use_BH=='1':
				os.rename(file_change,UPLOAD_FOLDER+'/'+fname)
			else:	
				f.save(os.path.join(UPLOAD_FOLDER, fname))	
			first_name = fname[:-4]
			# return 0;
			####解密pkt文件成tgz 然后到任务中解压tgz，最后删除pkt文件	
			command = "sinit " + UPLOAD_FOLDER + "/" + fname +" "+ UPLOAD_FOLDER + "/" + first_name +".tgz" + " 87653667"
			f = os.popen(command)
			#contc = f.read()
			f.close()
			i = 0
			while(1):
				if i > 5:
					sys_ok = 2
					if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
					return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
					
				if os.path.exists(UPLOAD_FOLDER + "/" + first_name +".tgz"):
					break
				else:
					time.sleep(0.5)
				i = i + 1 
				
			
			command = "tar -zxvf " + UPLOAD_FOLDER + "/" + first_name +".tgz -C " + UPLOAD_FOLDER
			f = os.popen(command)
			contc = f.read()
			debug(contc)
			f.close()
			
			i = 0
			while(1):	
				if i > 10:
					sys_ok = 2
					if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
					return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
				if os.path.exists(UPLOAD_FOLDER + "/" + first_name):
					break
				else:
					time.sleep(0.5)
				i = i + 1
			
			list_file = os.listdir(UPLOAD_FOLDER + "/" + first_name)  #获取目录下的文件列表
			if not list_file:
				sys_ok = 2
				if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
				return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
			else:
				file_x86 = False
				file_arm = True
				for file in list_file:
					if file == "x86.tgz":
						file_x86 = True
						
				if 	file_x86 == True and file_arm == True:
					pass
				else:
					sys_ok = 2
					if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
					return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)

			
			content = "[global]\nclass = taskglobal\ntype = system_update\nfname=%s\n" %(first_name)
			try:
				if server_id == '-1':
					
					ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
				else:
					ss = task_client.task_send(server_id, content)
			except:
				sys_ok = 2
				if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
				return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
			if ss == False:
				sys_ok = 2
				if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
				return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
	except:
		if not system_log(system_user,oper,"升级失败(%d)" %(sys._getframe().f_lineno),'系统管理>系统升级'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
		debug(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])))
		return "{\"Result\":false,\"info\":\"升级失败(%d)\"}" %(sys._getframe().f_lineno)
	if not system_log(system_user,oper,"成功",'系统管理>系统升级'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
	
	return "{\"Result\":true,\"info\":\"升级成功\"}" 

#系统升详细信息回显 ok11-18 
@system_update.route('/if_sys_succ',methods=['GET', 'POST'])
def if_sys_succ():
	session = request.form.get('se')
	curr_server_id =  request.form.get('s1')
	if curr_server_id < 0 or curr_server_id =='':
		curr_server_id = -1
	else:
		node_id_str = curr_server_id.split('(')
		curr_server_id = int(node_id_str[0].strip())
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip);
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
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	if curr_server_id == -1:
		sql = "select server_id from server_global order by server_id;"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常(%d):%s\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		if not results:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		curs.close()
		conn.close()
	else:
		results =[]
		results.append(curr_server_id)

	error_index = 0
	idstr = request.form.get('id');
	if idstr < 0:
		idstr=""
	count_str = request.form.get('count_str');
	if count_str <0 :
		count_str = '';
	
	
	i = 0
	idstr="";	
	try:
		conn1 = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	try:
		curs1 = conn1.cursor()
	except pyodbc.Error,e:
		conn1.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	for result in results:
		if curr_server_id == -1:		
			server_id = result[0]
		else:
			server_id = result
			
		if idstr == "":
			sql = "select count(*) from logs_update where server_id=%d;" %(server_id)
			curs1.execute(sql)
			results_tmp = curs1.fetchall()
			debug(sql)
			debug(str(results_tmp))
			if results_tmp[0][0] == 0 or count_str =='':
				error_index = len(results)
			else:
				if int(count_str.split(',')[i]) == results_tmp[0][0] :
					error_index = error_index + 1
						
		else:
			try:
				id = idstr.split(',')[i]
				sql = "select cont from logs_update where id in ( select id from logs_update where server_id=%d order by happen desc limit 1) and id !=%s;" %(server_id,id)
				curs1.execute(sql)
				results_tmp = curs1.fetchall()
				#debug(sql)
				if len(results_tmp) == 0:
					error_index = len(results)
				else:
					for result_tmp in results_tmp:
						result = result_tmp[0].encode('utf-8')
						if result.find("升级完成") <0:
							error_index = error_index + 1	
			except:
				error_index = error_index + 1				
			
		i = i+ 1
		
	curs1.close()
	conn1.close()
	#debug(str(results))		
	if error_index == 0:
		return "{\"Result\":true,\"info\":\"升级成功\"}" 
	elif len(results) == error_index:
		return "{\"Result\":true,\"info\":\"全部服务器升级失败(%d)\"}" %(sys._getframe().f_lineno)
	elif len(results) > error_index:
		return "{\"Result\":true,\"info\":\"部分服务器升级失败(%d)\"}" %(sys._getframe().f_lineno)
	else:
		return "{\"Result\":true,\"info\":\"服务器升级未知错误(%d)\"}" %(sys._getframe().f_lineno)	
		
#系统升级 切换时间 详细信息回显 ok11-18 
@system_update.route('/change_update',methods=['GET', 'POST'])
def change_update():
	session = request.form.get('se')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)：%d\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno)
		sys.exit()
	node_id = request.form.get('node_id')
	node_id_str = node_id.split('(')
	node_id_s = node_id_str[0].strip()
	
	version = ''
	##获取版本
	if os.path.exists(UPLOAD_FOLDER):
		list_file = os.listdir(UPLOAD_FOLDER)
		file_arr = []
		if not list_file:
			version = ""
		else:
			for file in list_file:
				if os.path.isdir(UPLOAD_FOLDER + "/" + file) and len(file)>8:
					if file[0:3] == "bh-" :
						file_arr.append(file)
			if not file_arr :
				version = ""
			else :
				filedate = file_arr[0][-10:]
				
				if len(file_arr) > 1:
					t1 = os.path.getmtime(UPLOAD_FOLDER +'/' + file_arr[0])
					for files in file_arr:
						t2 = os.path.getmtime(UPLOAD_FOLDER +'/' + files)
						if t2>=t1:
							version = files
							t1 = t2
				else:
					version = file_arr[0]
	
	update_type = request.form.get('update_type')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#debug(sql)
	sql = "select cont from  logs_update  where server_id=%s order by happen desc limit 2;" %(node_id_s)
		
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	results = curs.fetchall()
	sys_info = ''
	if results :
		if update_type == "new":
			sys_info = results[0][0].encode('utf-8')
			#result = results[0][0].encode('utf-8').split('	')
			#sys_info = base64.b64decode(result[0]) +  base64.b64decode(result[1]) + base64.b64decode(result[2])
		else:
			if len(results) > 1:
				sys_info = results[1][0].encode('utf-8')
				#result = results[1][0].encode('utf-8').split('	')
				#sys_info = base64.b64decode(result[0]) +  base64.b64decode(result[1]) + base64.b64decode(result[2])	
	
	return "{\"Result\":true,\"info\":\"%s\",\"version\":\"%s\"}" %(sys_info,version)		
