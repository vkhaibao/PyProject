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
import htmlencode
from index import PGetPermissions
from generating_log import system_log
from flask import Blueprint,request,render_template # 
smsm = Blueprint('smsm',__name__)
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
		
@smsm.route('/manage_smsm',methods=['GET', 'POST'])
def manage_smsm():
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
	_power=PGetPermissions(us)
	_power_json = json.loads(str(_power));
	_power_mode = 2;
	for one in _power_json:
		if one['SystemMenuId'] == 6:
			_power_mode = one['Mode']
	
	return render_template('manage_smsm.html',keyword=keyword,now=now,selectid=selectid,error_msg=error_msg,_power_mode=_power_mode);

@smsm.route('/create_smsm',methods=['GET', 'POST'])
def create_smsm():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	edit = request.form.get('z3')
	selectid = request.form.get('z4')
	if selectid == None:
		selectid = "[]"
	t = "create_smsm.html"
	if edit != "None":
		return render_template(t,edit=edit,now=now,keyword=keyword,selectid=selectid)
	else:
		return render_template(t,edit='"None"',now=now,keyword=keyword,flag="None",selectid=selectid)


##设备类型列表、过滤、分页
@smsm.route('/get_smsm_list',methods=['GET', 'POST'])
def get_smsm_list():
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
			#debug("select public.\"PGetSmsMConfig\"(null,%d,%d);"%(number,row))
			curs.execute("select public.\"PGetSmsMConfig\"(null,%d,%d);" % (number,row))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###删除
@smsm.route('/smsms_delete',methods=['GET', 'POST'])
def smsms_delete():
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"SmsMConfigName\" from public.\"SmsMConfig\" where \"SmsMConfigId\" in (%s)" % id[1:-1]
				#debug("sql:%s" % sql)
				curs.execute(sql)
				name_str = ""
				for row in curs.fetchall():
					name_str = name_str + row[0].encode('utf-8') + ","
				
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"SmsMConfigName\" from public.\"SmsMConfig\" where \"SmsMConfigId\"=%d" % int(id)
					#debug("sql:%s" % sql)
					curs.execute(sql)
					smsmname = curs.fetchall()[0][0].encode('utf-8')
					
					curs.execute("select public.\"PDeleteSmsMConfig\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除短信猫：%s" % smsmname,"失败："+result['ErrMsg'],"短信猫")
						conn.rollback()
						return result
				if name_str != "":
					system_log(userCode,"删除短信猫：%s" % name_str[:-1],"成功","短信猫")
				return "{\"Result\":true}"
			else:
				sql = "select \"SmsMConfigName\" from public.\"SmsMConfig\" where \"SmsMConfigId\"=%d" % int(id)
				#debug("sql:%s" % sql)
				curs.execute(sql)
				smsmname = curs.fetchall()[0][0].encode('utf-8')
					
				curs.execute("select public.\"PDeleteSmsMConfig\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				re_smsm = json.loads(results)
				if re_smsm['Result']:
					system_log(userCode,"删除短信猫：%s" % smsmname,"成功","短信猫")
				else:
					system_log(userCode,"删除短信猫：%s" % smsmname,"失败："+result['ErrMsg'],"短信猫")
				
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
###保存（之前可以一次性保存多个）现在一次保存一个
@smsm.route('/save_smsm',methods=['GET', 'POST'])
def save_smsm():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	data = json.loads(data)
	#data = MySQLdb.escape_string(data).decode("utf-8")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			for i in data:
				smsm_data = json.loads(i)
				curs.execute("select public.\"PSaveSmsMConfig\"(E'%s');"%(i))
				result = curs.fetchall()[0][0].encode('utf-8')
				results = json.loads(result)
				if results['Result'] == False:
					if smsm_data['SmsMConfigId'] == 0:
						system_log(userCode,"创建短信猫：%s" % smsm_data['SmsMConfigName'],"失败："+result['ErrMsg'],"短信猫")
					else:
						system_log(userCode,"编辑短信猫：%s" % smsm_data['SmsMConfigName'],"失败："+result['ErrMsg'],"短信猫")
					return result
				if smsm_data['SmsMConfigId'] == 0:
					system_log(userCode,"创建短信猫：%s" % smsm_data['SmsMConfigName'],"成功","短信猫")
				else:
					system_log(userCode,"编辑短信猫：%s" % smsm_data['SmsMConfigName'],"成功","短信猫")
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@smsm.route('/select_smsm_all',methods=['GET', 'POST'])
def select_smsm_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z1')
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
				#debug("select public.\"PGetSmsMConfig\"(%d,null,null);"%(int(id)))
				curs.execute("select public.\"PGetSmsMConfig\"(%d,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetSmsMConfig\"(null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@smsm.route('/check_smsmconfig_name',methods=['GET', 'POST'])
def check_smsmconfig_name():
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
			curs.execute("select public.\"PGetSmsMConfigByName\"(E'%s');" % name)
			results = curs.fetchall()[0][0]
			return str(results) 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
@smsm.route('/get_smsm_flag',methods=['GET', 'POST'])
def get_smsm_flag():
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
			sql = "select count(*) from \"SmsMConfig\""
			#debug('sql:%s' % sql)
			curs.execute(sql)
			count_smsm = curs.fetchall()[0][0]
			sql = "select count(*) from \"SmsMConfig\" where \"Flag\" = 2"
			#debug('sql:%s' % sql)
			curs.execute(sql)
			def_smsm = curs.fetchall()[0][0]
			sql = "select count(*) from \"SmsMConfig\" where \"Flag\" = 1"
			#debug('sql:%s' % sql)
			curs.execute(sql)
			spare_smsm = curs.fetchall()[0][0]
			return "{\"Result\":true,\"count_smsm\":%s,\"def_smsm\":%s,\"spare_smsm\":%s}" % (count_smsm,def_smsm,spare_smsm)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
