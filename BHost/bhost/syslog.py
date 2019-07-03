#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import MySQLdb
import json
import time
import datetime
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionCheck
import htmlencode
from index import PGetPermissions
from generating_log import system_log
from flask import Blueprint,request,render_template #
from htmlencode import parse_sess,check_role
 
syslog = Blueprint('syslog',__name__)
ERRNUM_MODULE = 2000

reload(sys)
sys.setdefaultencoding('utf-8')

#ErrorEncode 
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
		fp.write('\n')
		fp.close()

@syslog.route('/manage_syslog',methods=['GET', 'POST'])
def manage_syslog():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	selectid = request.form.get('z3')
	if keyword == None:
		keyword = "[]"
	if selectid == None:
		selectid = "[]"
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
			
	_power=PGetPermissions(us)
	_power_json = json.loads(str(_power));
	_power_mode = 2;
	for one in _power_json:
		if one['SystemMenuId'] == 6:
			_power_mode = one['Mode']
	return render_template('manage_syslog.html',keyword=keyword,now=now,selectid=selectid,error_msg=error_msg,_power_mode=_power_mode);

@syslog.route('/create_syslog',methods=['GET', 'POST'])
def create_syslog():
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
	
		
	t = "create_syslog.html"
	if edit != "None":
		try:
			edit_json = json.loads(edit);
			edit_id = edit_json['data'][0]['SyslogConfigId'];		
			if str(edit_id).isdigit() == False:
				return '',403 
		except:
			return '',403 
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				curs.execute("select public.\"PGetSyslogConfig\"(%d,%d,%d);" % (edit_id,10,0))
				edit = curs.fetchall()[0][0].encode('utf-8')
				
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
				
		
	
		return render_template(t,edit=edit,now=now,keyword=keyword,selectid=selectid)
	else:
		return render_template(t,edit='"None"',now=now,keyword=keyword,flag="None",selectid=selectid)


##设备类型列表、过滤、分页
@syslog.route('/get_syslog_list',methods=['GET', 'POST'])
def get_syslog_list():
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
			curs.execute("select public.\"PGetSyslogConfig\"(null,%d,%d);" % (number,row))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###删除
@syslog.route('/syslogs_delete',methods=['GET', 'POST'])
def syslogs_delete():
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
	syslog_title = "系统管理>输出设置>SYSLOG"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"SyslogConfigName\" from public.\"SyslogConfig\" where \"SyslogConfigId\" in (%s)" % id[1:-1]
				curs.execute(sql)
				name_str = ""
				for row in curs.fetchall():
					name_str = name_str + row[0].encode('utf-8') + ","
					
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"SyslogConfigName\",\"Flag\" from public.\"SyslogConfig\" where \"SyslogConfigId\"=%d" % int(id)
					curs.execute(sql)
					syslog_data = curs.fetchall()
					syslogname = syslog_data[0][0].encode('utf-8')
					syslogflag = syslog_data[0][1]
					if syslogflag == 2:
						nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						sql = "update public.\"GlobalStrategy\" set \"LastModifyTime\"='%s'" % nowtime
						curs.execute(sql)
						
					curs.execute("select public.\"PDeleteSyslogConfig\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除SYSLOG：%s" % syslogname,"失败："+results['ErrMsg'],syslog_title)
						conn.rollback()
						return result
				if name_str != "":
					system_log(userCode,"删除SYSLOG：%s" % name_str[:-1],"成功",syslog_title)
				return "{\"Result\":true}"
			else:
				sql = "select \"SyslogConfigName\",\"Flag\" from public.\"SyslogConfig\" where \"SyslogConfigId\"=%d" % int(id)
				curs.execute(sql)
				syslog_data = curs.fetchall()
				syslogname = syslog_data[0][0].encode('utf-8')
				syslogflag = syslog_data[0][1]
				if syslogflag == 2:
					nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					sql = "update public.\"GlobalStrategy\" set \"LastModifyTime\"='%s'" % nowtime
					curs.execute(sql)
						
				curs.execute("select public.\"PDeleteSyslogConfig\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				
				re_syslog = json.loads(results)
				if re_syslog['Result']:
					system_log(userCode,"删除SYSLOG：%s" % syslogname,"成功",syslog_title)
				else:
					system_log(userCode,"删除SYSLOG：%s" % syslogname,"失败："+re_syslog['ErrMsg'],syslog_title)
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
###保存
@syslog.route('/save_syslog',methods=['GET', 'POST'])
def save_syslog():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data = request.form.get('z1')
	session = request.form.get('a0')
	modify_flag = request.form.get('z2')
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
	#data = MySQLdb.escape_string(data).decode("utf-8")
	if module_type == None or module_type == "":
		title = "系统管理>输出设置>SYSLOG"
	else:
		title = module_type
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			for i in data:
				syslog_json = json.loads(i)
				curs.execute("select public.\"PSaveSyslogConfig\"(E'%s');"%(MySQLdb.escape_string(i).decode('utf-8')))
				result = curs.fetchall()[0][0].encode('utf-8')
				results = json.loads(result)
				
				if syslog_json['SyslogServerIP'] != "" and syslog_json['SyslogServerIP'] != None:
					SyslogServerIP = "服务器地址：" + syslog_json['SyslogServerIP'] + '，'
				else:
					SyslogServerIP = ""
					
				if syslog_json['SyslogPort'] != "" and syslog_json['SyslogPort'] != None:
					SyslogPort = "端口：" + str(syslog_json['SyslogPort']) + '，'
				else:
					SyslogPort = ""
				
				if syslog_json['EnCode'] == "" or syslog_json['EnCode'] == None:
					EnCode = ""
				elif int(syslog_json['EnCode']) == 0:
					EnCode = "编码方式：UTF-8，"
				elif int(syslog_json['EnCode']) == 1:
					EnCode = "编码方式：GBK，"
				else:
					EnCode = ""
					
				if syslog_json['Flag'] == "" or syslog_json['Flag'] == None:
					Flag = "方式：其他"
				elif int(syslog_json['Flag']) == 2:
					Flag = "方式：默认"
				elif int(syslog_json['Flag']) == 1:
					Flag = "方式：备用"
				else:
					Flag = "方式：其他"
					
				show_msg = SyslogServerIP + SyslogPort + EnCode + Flag
				
				if results['Result'] == False:
					if syslog_json['SyslogConfigId'] == 0:
						system_log(userCode,"创建SYSLOG：%s" % syslog_json['SyslogConfigName'],"失败："+results['ErrMsg'],title)
					else:
						system_log(userCode,"编辑SYSLOG：%s" % syslog_json['SyslogConfigName'],"失败："+results['ErrMsg'],title)
					return result
				if syslog_json['Flag'] == '2':
					nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					if syslog_json['SyslogConfigId'] == 0 or modify_flag == '1':
						sql = "update public.\"GlobalStrategy\" set \"LastModifyTime\"='%s'" % nowtime
						curs.execute(sql)
				if syslog_json['SyslogConfigId'] == 0:
					show_msg = "创建SYSLOG：%s（%s）" % (syslog_json['SyslogConfigName'],show_msg)
					system_log(userCode,show_msg,"成功",title)
				else:
					show_msg = "编辑SYSLOG：%s（%s）" % (syslog_json['SyslogConfigName'],show_msg)
					system_log(userCode,show_msg,"成功",title)
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@syslog.route('/select_syslog_all',methods=['GET', 'POST'])
def select_syslog_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z1')
	if id and id !='-1' and str(id).isdigit()	== False:
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
				curs.execute("select public.\"PGetSyslogConfig\"(%d,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetSyslogConfig\"(null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@syslog.route('/check_syslogconfig_name',methods=['GET', 'POST'])
def check_syslogconfig_name():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	name = request.form.get('z1')
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
			curs.execute("select public.\"PGetSyslogConfigByName\"(E'%s');" % name)
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
@syslog.route('/get_syslog_flag',methods=['GET', 'POST'])
def get_syslog_flag():
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
			sql = "select count(*) from \"SyslogConfig\""
			curs.execute(sql)
			count_syslog = curs.fetchall()[0][0]
			sql = "select count(*) from \"SyslogConfig\" where \"Flag\" = 2"
			curs.execute(sql)
			def_syslog = curs.fetchall()[0][0]
			sql = "select count(*) from \"SyslogConfig\" where \"Flag\" = 1"
			curs.execute(sql)
			spare_syslog = curs.fetchall()[0][0]
			return "{\"Result\":true,\"count_syslog\":%s,\"def_syslog\":%s,\"spare_syslog\":%s}" % (count_syslog,def_syslog,spare_syslog)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
