#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import MySQLdb
import json
import time

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionCheck
from ctypes import *
import base64
from logbase import db
from logbase import defines
from logbase import common
from logbase import task_client
import htmlencode
import redis
from index import PGetPermissions
from generating_log import system_log

from flask import Blueprint,request,render_template # 
from htmlencode import parse_sess,check_role
smssvr = Blueprint('smssvr',__name__)
ERRNUM_MODULE = 2000
reload(sys)
sys.setdefaultencoding('utf-8')

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;
		
@smssvr.route('/manage_smssvr',methods=['GET', 'POST'])
def smssvr_manage():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	selectid = request.form.get('z3')
	if keyword == None:
		keyword = "[]"
	if selectid == None:
		selectid = "[]"
	
	if now and  str(now).isdigit() == False:
		return '',403
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
		
		
	sess = request.form.get('a0')
	if sess <0 or sess == '':
		sess = request.args.get('a0')
	if sess <0 or sess =='':
		sess ='';
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
	return render_template('manage_smssvr.html',keyword=keyword,now=now,selectid=selectid,error_msg=error_msg,_power_mode=_power_mode);

@smssvr.route('/create_smssvr',methods=['GET', 'POST'])
def create_smssvr():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	edit = request.form.get('z3')
	selectid = request.form.get('z4')
	if selectid == None:
		selectid = "[]"
	if keyword == None:
		keyword = "[]"
	
	if now and  str(now).isdigit() == False:
		return '',403
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
		
		
	t = "create_smssvr.html"	
	if edit != "None":
		try:
			edit_json = json.loads(edit);
			edit_id = edit_json['data'][0]['SmsSvrConfigId'];		
			if str(edit_id).isdigit() == False:
				return '',403 
		except:
			return '',403 
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				#debug("select public.\"PGetSmsSvrConfig\"(null,%d,%d);"%(number,row))
				curs.execute("select public.\"PGetSmsSvrConfig\"(%d,%d,%d);" % (edit_id,10,0))
				results = curs.fetchall()[0][0].encode('utf-8')
				data_json = json.loads(results)
				for data in data_json['data']:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
					pwd_rc4 = c_char_p()# 定义一个指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd(str(data['SmsSvrDBPassword']),pwd_rc4);
					#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
					data['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
					data['SmsSvrDBInsertTemp'] = base64.b64decode(data['SmsSvrDBInsertTemp']).encode('utf-8')
				edit = json.dumps(data_json, encoding='utf-8')
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
	
		return render_template(t,edit=edit,now=now,keyword=keyword,selectid=selectid)
	else:
		return render_template(t,edit='"None"',now=now,keyword=keyword,selectid=selectid)


##设备类型列表、过滤、分页
@smssvr.route('/get_smssvr_list',methods=['GET', 'POST'])
def get_smssvr_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	number = request.form.get('z1')
	curpage = request.form.get('z2')
	keyword = request.form.get('z3')
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
	
	if keyword == None:
		keyword = "[]"
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
		
	if number and str(number).isdigit()	== False:
		return '',403
	if curpage and str(curpage).isdigit()	== False:
		return '',403
			
	number = int(number)
	curpage = int(curpage)
	if number < 0:
		number = 0
	if curpage < 0:
		curpage = 0
	row = number*(curpage-1)
	"""
	if keyword != "":
		keyword = json.loads(keyword);
		filter_name = ""
		filter_des = ""
		if len(keyword) != 0:
			for i in keyword:
				filter_arry = i.split('-',1)
				if filter_arry[0] == "名称":
					filter_name = filter_name + filter_arry[1] + '\n'
				if filter_arry[0] == "描述":
					filter_des = filter_des + filter_arry[1] + '\n'
			if filter_name != "":
				filter_name = filter_name[:-1]
			if filter_des != "":
				filter_des = filter_des[:-1]
			filter_name = filter_name.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			filter_des = filter_des.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		else:
			filter_name = ""
			filter_des = ""
	if filter_name != "":
		filter_name = "'%s'" % filter_name
	else:
		filter_name = "null"
	if filter_des != "":
		filter_des = "'%s'" % filter_des
	else:
		filter_des = "null"
		"""
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetSmsSvrConfig\"(null,%d,%d);"%(number,row))
			curs.execute("select public.\"PGetSmsSvrConfig\"(null,%d,%d);" % (number,row))
			results = curs.fetchall()[0][0].encode('utf-8')
			data_json = json.loads(results)
			for data in data_json['data']:
				if os.path.exists('/usr/lib64/logproxy.so') == False:
					return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
				lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
				pwd_rc4 = c_char_p()# 定义一个指针
				lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
				lib.decrypt_pwd.restype = None #定义函数返回值
				pwd_rc4.value = "0"*512 # 初始化 指针
				lib.decrypt_pwd(str(data['SmsSvrDBPassword']),pwd_rc4);
				#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
				data['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
				data['SmsSvrDBInsertTemp'] = base64.b64decode(data['SmsSvrDBInsertTemp']).encode('utf-8')
			results = json.dumps(data_json, encoding='utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###删除
@smssvr.route('/smssvr_delete',methods=['GET', 'POST'])
def smssvr_delete():
	type = request.form.get('z1')
	id = request.form.get('z2')
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
	
	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	smssvr_title = "系统管理>输出设置>短信网关"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"SmsSvrConfigName\" from public.\"SmsSvrConfig\" where \"SmsSvrConfigId\" in (%s)" % id[1:-1]
				#debug("sql:%s" % sql)
				curs.execute(sql)
				name_str = ""
				for row in curs.fetchall():
					name_str = name_str + row[0].encode('utf-8') + ","
				
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"SmsSvrConfigName\" from public.\"SmsSvrConfig\" where \"SmsSvrConfigId\"=%d" % int(id)
					#debug("sql:%s" % sql)
					curs.execute(sql)
					smssvrname = curs.fetchall()[0][0].encode('utf-8')
					
					curs.execute("select public.\"PDeleteSmsSvrConfig\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除短信网关：%s" % smssvrname,"失败："+results['ErrMsg'],smssvr_title)
						conn.rollback()
						return result
				if name_str != "":
					system_log(userCode,"删除短信网关：%s" % name_str[:-1],"成功",smssvr_title)
				return "{\"Result\":true}"
			else:
				sql = "select \"SmsSvrConfigName\" from public.\"SmsSvrConfig\" where \"SmsSvrConfigId\"=%d" % int(id)
				#debug("sql:%s" % sql)
				curs.execute(sql)
				smssvrname = curs.fetchall()[0][0].encode('utf-8')

				curs.execute("select public.\"PDeleteSmsSvrConfig\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				
				re_smsm = json.loads(results)
				if re_smsm['Result']:
					system_log(userCode,"删除短信网关：%s" % smssvrname,"成功",smssvr_title)
				else:
					system_log(userCode,"删除短信网关：%s" % smssvrname,"失败："+re_smsm['ErrMsg'],smssvr_title)

				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
###保存
@smssvr.route('/save_smssvr',methods=['GET', 'POST'])
def save_smssvr():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data = request.form.get('z1')
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
			
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	data = json.loads(data)
	
	if data['SmsSvrDBType'] == 1:
		SmsSvrDBType = "数据库类型：ORACLE，"
	elif data['SmsSvrDBType'] == 2:
		SmsSvrDBType = "数据库类型：MSSQL，"
	elif data['SmsSvrDBType'] == 3:
		SmsSvrDBType = "数据库类型：MYSQL，"
	elif data['SmsSvrDBType'] == 4:
		SmsSvrDBType = "数据库类型：SYBASE，"
	else:
		SmsSvrDBType = ""
		
	if data['SmsSvrDBServerIP'] != "" and data['SmsSvrDBServerIP'] != None:
		SmsSvrDBServerIP = "服务器地址：" + data['SmsSvrDBServerIP'] + '，'
	else:
		SmsSvrDBServerIP = ""
		
	if data['SmsSvrDBPort'] != "" and data['SmsSvrDBPort'] != None:
		SmsSvrDBPort = "端口：" + str(data['SmsSvrDBPort']) + '，'
	else:
		SmsSvrDBPort = ""
		
	if data['SmsSvrDBUserName'] != "" and data['SmsSvrDBUserName'] != None:
		SmsSvrDBUserName = "账号：" + data['SmsSvrDBUserName'] + '，'
	else:
		SmsSvrDBUserName = ""
		
	if data['SmsSvrDBDatabase'] != "" and data['SmsSvrDBDatabase'] != None:
		SmsSvrDBDatabase = "数据库：" + data['SmsSvrDBDatabase'] + '，'
	else:
		SmsSvrDBDatabase = ""
		
	if data['SmsSvrDBInsertTemp'] != "" and data['SmsSvrDBInsertTemp'] != None:
		SmsSvrDBInsertTemp = "短信sql语句模版：" + data['SmsSvrDBInsertTemp'] + '，'
	else:
		SmsSvrDBInsertTemp = ""
		
	if data['EnCode'] == 0:
		EnCode = "编码方式：UTF-8，"
	elif data['EnCode'] == 1:
		EnCode = "编码方式：GBK，"
	else:
		EnCode = ""
		
	if data['Flag'] == 2:
		Flag = "方式：默认"
	elif data['Flag'] == 1:
		Flag = "方式：备用"
	else:
		Flag = "方式：其他"
		
	show_msg = SmsSvrDBType + SmsSvrDBServerIP + SmsSvrDBPort + SmsSvrDBUserName + SmsSvrDBDatabase + SmsSvrDBInsertTemp + EnCode + Flag
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd(data['SmsSvrDBPassword'],pwd_rc4);#执行函数
	data['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
	data['SmsSvrDBInsertTemp'] = base64.b64encode(data['SmsSvrDBInsertTemp'])
	save_data = json.dumps(data)
	save_data = MySQLdb.escape_string(save_data).decode("utf-8")
	if module_type == None or module_type == "":
		title = "系统管理>输出设置>短信网关"
	else:
		title = module_type
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PSaveSmsSvrConfig\"('%s');"%(data))
			curs.execute("select public.\"PSaveSmsSvrConfig\"(E'%s');"%(save_data))
			results = curs.fetchall()[0][0].encode('utf-8')
			
			re_smssvr = json.loads(results)

			if re_smssvr['Result'] == False:
				if data['SmsSvrConfigId'] == 0:
					system_log(userCode,"创建短信网关：%s" % data['SmsSvrConfigName'],"失败："+re_smssvr['ErrMsg'],title)
				else:
					system_log(userCode,"编辑短信网关：%s" % data['SmsSvrConfigName'],"失败："+re_smssvr['ErrMsg'],title)
				return results
			if data['SmsSvrConfigId'] == 0:
				show_msg = "创建短信网关：%s（%s）" % (data['SmsSvrConfigName'], show_msg)
				system_log(userCode,show_msg,"成功",title)
			else:
				show_msg = "编辑短信网关：%s（%s）" % (data['SmsSvrConfigName'], show_msg)
				system_log(userCode,show_msg,"成功",title)
			
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)

@smssvr.route('/select_smssvr_all',methods=['GET', 'POST'])
def select_smssvr_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z1')
	if id and id!='-1' and str(id).isdigit()	== False:
		return '',403
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
			curs = conn.cursor()
			if id != '-1':
				#debug("select public.\"PGetSmsSvrConfig\"(%d,null,null);"%(int(id)))
				curs.execute("select public.\"PGetSmsSvrConfig\"(%d,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetSmsSvrConfig\"(null,null,null);")	
			results = curs.fetchall()[0][0].encode('utf-8')
			if id != '-1':
				data = json.loads(results)
				if os.path.exists('/usr/lib64/logproxy.so') == False:
					return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
				lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
				pwd_rc4 = c_char_p()# 定义一个指针
				lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
				lib.decrypt_pwd.restype = None #定义函数返回值
				pwd_rc4.value = "0"*512 # 初始化 指针
				lib.decrypt_pwd(str(data['data'][0]['SmsSvrDBPassword']),pwd_rc4);
				#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
				data['data'][0]['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
				data['data'][0]['SmsSvrDBInsertTemp'] = base64.b64decode(data['data'][0]['SmsSvrDBInsertTemp']).encode('utf-8')
				results = json.dumps(data, encoding='utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		
@smssvr.route('/get_smssvr_flag',methods=['GET', 'POST'])
def get_smssvr_flag():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
			curs = conn.cursor()
			sql = "select count(*) from \"SmsSvrConfig\""
			#debug('sql:%s' % sql)
			curs.execute(sql)
			count_smssvr = curs.fetchall()[0][0]
			sql = "select count(*) from \"SmsSvrConfig\" where \"Flag\" = 2"
			#debug('sql:%s' % sql)
			curs.execute(sql)
			def_smssvr = curs.fetchall()[0][0]
			sql = "select count(*) from \"SmsSvrConfig\" where \"Flag\" = 1"
			#debug('sql:%s' % sql)
			curs.execute(sql)
			spare_smssvr = curs.fetchall()[0][0]
			return "{\"Result\":true,\"count_smssvr\":%s,\"def_smssvr\":%s,\"spare_smssvr\":%s}" % (count_smssvr,def_smssvr,spare_smssvr)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
@smssvr.route('/test_smssvr',methods=['GET', 'POST'])
def test_smssvr():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	json_data = request.form.get('z1')
	type = request.form.get('z2')
	phone = request.form.get('z3')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if type == '3':
		data = json.loads(json_data)
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
		pwd_rc4 = c_char_p()# 定义一个指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd(data['MasterConfig']['SmsSvrDBPassword'],pwd_rc4);#执行函数
		data['MasterConfig']['SmsSvrDBPassword'] = pwd_rc4.value #获取变量的值
		data['MasterConfig']['SmsSvrDBInsertTemp'] = base64.b64encode(data['MasterConfig']['SmsSvrDBInsertTemp'])
		json_data = json.dumps(data)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'insert into private."OutputConfigTest"("OutputConfigTestStr") values (E\'%s\')RETURNING "OutputConfigTestId";' % (MySQLdb.escape_string(json_data).decode('utf-8'))
			#debug("sql:%s" % sql)
			curs.execute(sql)
			testid = curs.fetchall()[0][0]
			conn.commit()
			task_content = '[global]\nclass = tasktest_output\ntype = execute_cmd\noutput_type=%s\ntestid=%s\nphone=\"%s\"\nse=%s\n' % (type,testid,str(phone),session)
			#debug(task_content)
			
			r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=10);
			if type == '2':#短信猫
				r.hset("SMSM",session,"-1")
			elif type == '3':#短信网关
				r.hset("SMSSVR",session,"-1")
			else:#SYSLOG
				r.hset("SYSLOG",session,"-1")
			
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				if type == '2':#短信猫
					r.hdel("SMSM",session)
				elif type == '3':#短信网关
					r.hdel("SMSSVR",session)
				else:#SYSLOG
					r.hdel("SYSLOG",session)				
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":true}"
			'''
			if phone != None:
				cmd_str = '/flash/system/appr/send_warn "test" %s %d %s' % (type,testid,phone)
			else:
				cmd_str = '/flash/system/appr/send_warn "test" %s %d' % (type,testid)
			debug("cmd_str:%s" % cmd_str)
			fp = os.popen(cmd_str)
			lines = fp.readlines()
			fp.close()
			debug("lines:%s" % lines)
			sql = 'delete from private."OutputConfigTest" where "OutputConfigTestId" = %d' % testid
			curs.execute(sql)
			conn.commit()
			debug('%s' % lines[-1].strip())
			if lines[-1].strip() == '0':
				return "true"
			else:
				return "false"
			'''
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@smssvr.route('/get_test_flag',methods=['GET', 'POST'])
def get_test_flag():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type = request.form.get('z1')
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
			curs = conn.cursor()
			r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=10);
			if type == '2':#短信猫
				test_re = r.hget("SMSM",session)
				r.hdel("SMSM",session)
			elif type == '3':#短信网关
				test_re = r.hget("SMSSVR",session)
				r.hdel("SMSSVR",session)
			else:#SYSLOG
				test_re = r.hget("SYSLOG",session)
				r.hdel("SYSLOG",session)
			if test_re == "0":
				return "{\"Result\":true}"
			else:
				return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
