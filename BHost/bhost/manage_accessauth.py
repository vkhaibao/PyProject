#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
import MySQLdb
import shutil
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
from index import PGetPermissions
from generating_log import system_log
from comm_function import PGetSecurityPasswd
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
from jinja2 import Environment,FileSystemLoader
manage_accessauth = Blueprint('manage_accessauth',__name__)

ERRNUM_MODULE_manage_accessauth = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

UPLOAD_FOLDER = "/usr/storage/.system/upload"
def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
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
			#debug(str(sql))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
'''
		
@manage_accessauth.route('/show_manage_accessauth',methods=['GET', 'POST'])
def show_manage_accessauth():
	se = request.form.get('a0')
	now = request.form.get('z1')
	type = request.form.get('z3')
	keyword = request.form.get('z4')
	manage_filter_flag =  request.form.get('z5')
	selectid =  request.form.get('z6')
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
	
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

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
	return render_template("manage_accessauth.html",now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag,selectid=selectid,auth_flag1=auth_flag1,auth_flag2=auth_flag2,auth_flag3=auth_flag3,auth_flag4=auth_flag4)

@manage_accessauth.route('/add_access_auth',methods=['GET', 'POST'])
def add_access_auth():
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
		
	t = "add_access_auth.html"
	if edit != "None":
		return render_template(t,edit=edit,now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag,selectid=selectid)
	else:
		return render_template(t,edit='"None"',now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag,selectid=selectid)	

	
@manage_accessauth.route('/get_AccessAuth_z',methods=['GET', 'POST'])
def get_AccessAuth_z():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	number = request.form.get('z1')
	curpage = request.form.get('z2')
	keyword = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
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
	while i < 13:
		filter_cond_arry.append([])
		i += 1
	#所有、名称、运维用户、用户组、访问策略、管理员、主机组、主机名、主机服务、账号、服务器范围、授权动作、状态
	keyword = json.loads(keyword);
	if len(keyword) != 0:
		for i in keyword:
			filter_arry = i.split('-',1)
			filter_cond_arry[int(filter_arry[0])].append(MySQLdb.escape_string(filter_arry[1]).decode("utf-8"))
	i = 0
	while i < 13:
		filter_cond_arry[i] = '\n'.join(filter_cond_arry[i])
		filter_cond_arry[i] = MySQLdb.escape_string(filter_cond_arry[i]).decode("utf-8")
		if i == 0:
			filter_cond_arry[i] = filter_cond_arry[i].replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		else:
			filter_cond_arry[i] = filter_cond_arry[i].replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		
		if filter_cond_arry[i] == "":
			filter_cond_arry[i] = 'null'
		else:
			if i == 11 or i == 12:
				if filter_cond_arry[i] == '0':
					filter_cond_arry[i] = 'null'
				else:
					filter_cond_arry[i] = '%s' % filter_cond_arry[i]
			else:
				filter_cond_arry[i] = '"%s"' % filter_cond_arry[i]
		i += 1
	#debug("filter_cond_arry:%s" % str(filter_cond_arry))
	usercode = '"%s"' % usercode
	data = '{"loginusercode":%s,"accessauthname":%s,"accessstrategyname":%s,"adminusercode":%s,"ugname":%s,"usercode":%s,"hgname":%s,"hostname":%s,"serverscopename":%s,"hostservicename":%s,"accountname":%s,"searchstring":%s,"limitrow":%s,"offsetrow":%s,"Action":%s,"Enabled":%s}' % (usercode,filter_cond_arry[1],filter_cond_arry[4],filter_cond_arry[5],filter_cond_arry[3],filter_cond_arry[2],filter_cond_arry[6],filter_cond_arry[7],filter_cond_arry[10],filter_cond_arry[8],filter_cond_arry[9],filter_cond_arry[0],str(number),str(row),filter_cond_arry[11],filter_cond_arry[12])
	data = "E'%s'" % MySQLdb.escape_string(data).decode("utf-8")

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetAccessAuth\"(%s);" % data)
			curs.execute("select public.\"PGetAccessAuth\"(%s);" % data)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
		
@manage_accessauth.route('/check_edit',methods=['GET', 'POST'])
def check_edit():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if id == '-1':
		id = 'null'
	usercode = '"%s"' % usercode
	data = '{"loginusercode":'+usercode+',"accessauthid":'+id+',"limitrow":null,"offsetrow":null}'
	data = "E'%s'" % data
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetAccessAuth\"(%s);"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@manage_accessauth.route('/delete_auth',methods=['GET', 'POST'])
def delete_auth():
	session = request.form.get('a0')
	type = request.form.get('z1')
	id = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,'访问授权') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\" in (%s)" % id[1:-1]
				#debug("sql:%s" % sql)
				curs.execute(sql)
				auth_str = ""
				for row in curs.fetchall():
					auth_str = auth_str + row[0].encode('utf-8') + ","
					
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
					#debug("sql:%s" % sql)
					curs.execute(sql)
					auth_name = curs.fetchall()[0][0].encode('utf-8')
				
					curs.execute("select public.\"PDeleteAccessAuth\"(%d);"%(int(id)))
					results = curs.fetchall()[0][0].encode('utf-8')
					result = json.loads(results)
					if result['Result'] == False:
						system_log(usercode,"删除访问授权：%s" % auth_name,"失败："+result['ErrMsg'],"运维管理>访问授权")
						conn.rollback();
						return results
				if auth_str != "":
					system_log(usercode,"删除访问授权：%s" % auth_str[:-1],"成功","运维管理>访问授权")
				return "{\"Result\":true}"
			else:
				sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
				#debug("sql:%s" % sql)
				curs.execute(sql)
				auth_name = curs.fetchall()[0][0].encode('utf-8')
				
				curs.execute("select public.\"PDeleteAccessAuth\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				result = json.loads(results)
				if result['Result']:
					system_log(usercode,"删除访问授权：%s" % auth_name,"成功","运维管理>访问授权")
				else:
					system_log(usercode,"删除访问授权：%s" % auth_name,"失败："+result['ErrMsg'],"运维管理>访问授权")
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_accessauth.route('/modify_priority_z',methods=['GET', 'POST'])
def modify_priority_z():
	session = request.form.get('a0')
	modifyid = request.form.get('z1')
	referid = request.form.get('z2')
	position = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,'访问授权') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PModifyAccessAuthPriority\"(%d,%d,%d);"%(int(modifyid),int(referid),int(position)))
			#debug("select public.\"PModifyAccessAuthPriority\"(%d,%d,%d);"%(int(modifyid),int(referid),int(position)))
			results = curs.fetchall()[0][0].encode('utf-8')
			
			sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\" in (%s,%s)" %(modifyid,referid)
			curs.execute(sql)
			name_re = curs.fetchall()
			if results == "true":
				if position == '1':
					system_log(usercode,"访问授权（%s）的优先级改为在访问授权（%s）之前" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"成功","运维管理>访问授权")
				else:
					system_log(usercode,"访问授权（%s）的优先级改为在访问授权（%s）之后" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"成功","运维管理>访问授权")
			else:
				if position == '1':
					system_log(usercode,"访问授权（%s）的优先级改为在访问授权（%s）之前" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"失败","运维管理>访问授权")
				else:
					system_log(usercode,"访问授权（%s）的优先级改为在访问授权（%s）之后" % (name_re[0][0].encode('utf-8'),name_re[1][0].encode('utf-8')),"失败","运维管理>访问授权")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_accessauth.route('/enable_work',methods=['GET', 'POST'])
def enable_work():
	session = request.form.get('a0')
	authid = request.form.get('z1')
	e_type = request.form.get('z2')
	moudule = request.form.get('a10')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(usercode,"访问授权") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"AccessAuthName\" from \"AccessAuth\" where \"AccessAuthId\"=%s" % authid
			curs.execute(sql)
			authname = curs.fetchall()[0][0].encode('utf-8')
			if e_type == '1':
				curs.execute("update \"AccessAuth\" set \"Enabled\"= true,\"InvalidLog\"=null where \"AccessAuthId\"= %s" % authid)
				#debug("update \"AccessAuth\" set \"Enabled\"= true where \"AccessAuthId\"= %s" % authid)
				system_log(usercode,"启用访问授权：%s" % authname,"成功","运维管理>访问授权")
			else:
				curs.execute("update \"AccessAuth\" set \"Enabled\"= false,\"InvalidLog\"=null where \"AccessAuthId\"= %s" % authid)
				#debug("update \"AccessAuth\" set \"Enabled\"= false where \"AccessAuthId\"= %s" % authid)
				system_log(usercode,"停用访问授权：%s" % authname,"成功","运维管理>访问授权")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_accessauth.route('/import_access',methods=['GET', 'POST'])
def import_access():
	debug('import_access')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	debug(se)
	cover = request.form.get('a1')
	use_BH = request.form.get('a99')
	if use_BH=='0':
		f = request.files['file_change1']
		file_v = secure_filename(f.filename)
	else:
		file_v = request.form.get('file_v')
		file_change = request.form.get('file_change')
	fname = file_v
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if check_role(system_user,'访问授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	fname = file_v
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	debug(file_pwd)
	debug(fname)
	debug('-------------------')
	if use_BH=='0':
		f.save(os.path.join(UPLOAD_FOLDER, fname))
	else:
		shutil.move(file_change,file_pwd) 
	debug(str(sys._getframe().f_lineno))
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
	debug(str(sys._getframe().f_lineno))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:#新建任务
			curs = conn.cursor()
			sql = "SELECT nextval('private.\"AuthImportTask_AuthImportTaskId_seq\"'::regclass);"
			#debug(sql)
			curs.execute(sql)
			taskid = curs.fetchall()[0][0]
			sql = "SELECT \"UserId\" from public.\"User\" where \"UserCode\"='%s';"%(MySQLdb.escape_string(system_user).decode("utf-8"))
			curs.execute(sql)
			userid=curs.fetchall()[0][0]
			sql = "insert into private.\"AuthImportTask\"(\"AuthImportTaskId\",\"AuthImportTaskName\",\"Type\",\"UserId\") values(%d,E'%s',1,%s);" %(taskid,MySQLdb.escape_string(taskname).decode("utf-8"),userid)
			#debug(sql)
			curs.execute(sql)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	task_content = '[global]\nclass = taskdown_access\ntype = execute_import_cmd\nfile_pwd=\"%s\"\ncover=\"%s\"\ntaskid=\"%s\"\nusercode=\"%s\"\nclientip=\"%s\"\n' % (file_pwd,cover,str(taskid),system_user,client_ip)
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
	debug(task_content)
	return "{\"Result\":true}"

@manage_accessauth.route('/down_access',methods=['GET', 'POST'])
def down_access():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	choose = request.form.get('z2')
	format = request.form.get('z3')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
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
			sql = "delete from private.\"AuthExportInfo\" where \"FileName\"=E'access.%s.%s.csv'" % (system_user,se)
			curs.execute(sql)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
	time_value=int(time.time()*1000)
	task_content = '[global]\nclass = taskdown_access\ntype = execute_down_cmd\nusercode=\"%s\"\nclientip=\"%s\"\nse=\"%s\"\nchoose=%s\nformat=%s\ntime_value=%s\n' % (system_user,client_ip,se,choose,format,time_value)
	#debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		system_log(system_user,"创建授权导出任务","失败：任务下发异常","运维管理>访问授权")
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)

	system_log(system_user,"创建授权导出任务","成功","运维管理>访问授权")
	return "{\"Result\":true,\"file_name\":\"access.%s.%s.%s\"}"%(system_user,se,time_value)
	
@manage_accessauth.route('/download_file_access',methods=['GET', 'POST'])
def download_file_access():
	se = request.form.get('a0')	
	format = request.form.get('a1')
	filename = request.form.get('a2')
	use_BH = request.form.get('a99')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	filename_arr=filename.split('.')
	filename_arr.pop(-2)
	filename_arr.pop(-2)
	filename_arr.pop(-2)
	if use_BH=='0':
		return send_from_directory('/usr/storage/.system/dwload',filename,as_attachment=True,attachment_filename=('.'.join(filename_arr)))
	else:
		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"'+filename+'","filenewname":"'+('.'.join(filename_arr))+'"}'
	# passwd=PGetSecurityPasswd(userCode,1)
	# if passwd==0:
	# 		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	# if passwd!='':
	# 	if use_BH=='0':
	# 		return send_from_directory('/usr/storage/.system/dwload','access.%s.%s.zip' % (userCode,se),as_attachment=True,attachment_filename='access.zip')
	# 	else:
	# 		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"access.%s.%s.zip","filenewname":"access.zip"}'%(userCode,se)
	# if format=='0':
	# 	if use_BH=='0':
	# 		return send_from_directory('/usr/storage/.system/dwload','access.%s.%s.csv' % (userCode,se),as_attachment=True,attachment_filename='access.csv')
	# 	else:
	# 		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"access.%s.%s.csv","filenewname":"access.csv"}'%(userCode,se)
	# elif format=='1':
	# 	if use_BH=='0':
	# 		return send_from_directory('/usr/storage/.system/dwload','access.%s.%s.xls' % (userCode,se),as_attachment=True,attachment_filename='access.xls')
	# 	else:
	# 		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"access.%s.%s.xls","filenewname":"access.xls"}'%(userCode,se)
	# elif format=='2':
	# 	if use_BH=='0':
	# 		return send_from_directory('/usr/storage/.system/dwload','access.%s.%s.xlsx' % (userCode,se),as_attachment=True,attachment_filename='access.xlsx')
	# 	else:
	# 		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"access.%s.%s.xlsx","filenewname":"access.xlsx"}'%(userCode,se)
	
@manage_accessauth.route('/get_down_ok_access',methods=['GET', 'POST'])
def get_down_ok_access():
	se = request.form.get('a0')
	format=request.form.get('a1')
	filename=request.form.get('a2')
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
			# file_name='access.%s.%s.csv'%(userCode,se)
			# if format=='1':
			# 	file_name='access.%s.%s.xls'%(userCode,se)
			# elif format=='2':
			# 	file_name='access.%s.%s.xlsx'%(userCode,se)
			# passwd=PGetSecurityPasswd(userCode,1)
			# if passwd==0:
			# 	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
			# if passwd!='':
			# 	file_name='access.%s.%s.zip'% (userCode,se)	
			sql = "select * from private.\"AuthExportInfo\" where \"FileName\" like E'%"+filename+"%';"
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				sql = "delete from private.\"AuthExportInfo\" where \"FileName\" like E'%"+filename+"%';"
				curs.execute(sql)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
			return "{\"Result\":true,\"ErrMsg\":\""+str(results[0][2])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"filename\":\""+str(results[0][1])+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)

@manage_accessauth.route('/del_access_file',methods=['GET', 'POST'])
def del_host_file():
        se = request.form.get('a0')
        type = request.form.get('a1')
        client_ip = request.remote_addr
        (error,userCode,mac) = SessionCheck(se,client_ip);
        if error < 0:
                return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        elif error > 0:
                if error == 2:
                        return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
                else:
                        return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        if check_role(userCode,'访问授权') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
        passwd=PGetSecurityPasswd(userCode,1)
        if passwd==0:
                return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
        if passwd!='':
                filename='access.%s.%s.zip' % (userCode,se)
        else:
			filename='access.%s.%s.csv' % (userCode,se)
			if type == '1':
					filename='access.%s.%s.xls' % (userCode,se)
			elif type == '2':
					filename='access.%s.%s.xlsx' % (userCode,se)
			else:
					filename='access.%s.%s.csv' % (userCode,se)
        task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(filename))
        if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return 'true'
	
@manage_accessauth.route('/PGet_AuthImportTask',methods=['GET', 'POST'])
def PGet_AuthImportTask():
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
	data = '{"AuthImportTaskId":null,"Type":1,"limitrow":'+page_total+',"offsetrow":'+offsetrow+',"UserCode": "'+userCode+'"}'

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			#debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		
@manage_accessauth.route('/isexist_auth_import',methods=['GET', 'POST'])
def isexist_auth_import():
	se = request.form.get('a0')
	#name = request.form.get('z1')
	fname = request.form.get('file_v')
	file_change = request.form.get('file_change')
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
			sql = "select * from private.\"AuthImportTask\" where \"AuthImportTaskName\" = E\'%s\' and \"Type\"=1 and \"Status\"=0;" % MySQLdb.escape_string(taskname).decode("utf-8")
			#debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				system_log(userCode,"创建访问授权导入任务：%s" % fname,"成功","运维管理>访问授权")
				return "{\"Result\":true}"
			else:
				system_log(userCode,"创建访问授权导入任务：%s" % fname,"失败：该任务已存在","运维管理>访问授权")
				return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manage_accessauth.route('/del_auth_task',methods=['GET', 'POST'])
def del_auth_task():
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
	if check_role(userCode,'访问授权') == False:
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
			system_log(userCode,"删除访问授权导入任务：%s" % ('、'.join(Name_arry)),"成功","运维管理>访问授权")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
