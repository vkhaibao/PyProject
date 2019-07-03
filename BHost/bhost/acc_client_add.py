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
from comm import LogSet
from logbase import common
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
from htmlencode import check_role
from htmlencode import parse_sess
from htmlencode import ErrorEncode

acc_client_add = Blueprint('acc_client_add',__name__)

ERRNUM_MODULE_acc_client = 1000

reload(sys)
sys.setdefaultencoding('utf-8')

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
	
	
@acc_client_add.route('/get_acc_client_list',methods=['GET', 'POST'])
def get_acc_client_list():
	page = request.form.get('z4')
	ipage = request.form.get('z5')
	keyword = request.form.get('z6')
	session = request.form.get('a0')
	desc = request.form.get('z7')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if desc == None or desc == "":
		desc = "false"
	#if (keyword != ""):
	#	keyword = keyword.split('|')
	#keyword = keyword.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
	"""
	if (keyword != "" and keyword.find('|') != -1):
		keyword = keyword.split('|')
	"""
	#page = int(page)
	#ipage = int(ipage)
	if page < 0:
		page = 0
	if ipage < 0:
		ipage = 0
	if page != "null":
		row = int(page)*(int(ipage)-1)
	else:
		row = "null"
	if keyword != "":
		keyword = json.loads(keyword);
		filter_name1 = ""
		filter_name2 = ""
		filter_all = ""
		if len(keyword) != 0:
			for i in keyword:
				filter_arry = i.split('-',1)
				if filter_arry[0] == "所有":
					filter_all = filter_all + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
				elif filter_arry[0] == "协议名称":
					filter_name1 = filter_name1 + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
				else:
					filter_name2 = filter_name2 + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_all != "":
				filter_all = filter_all[:-1]
				filter_all = MySQLdb.escape_string(filter_all).decode("utf-8")
				filter_all = filter_all.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
				filter_all = "E'{\"searchstring\":\"%s\"}'" % filter_all
			else:
				filter_all = 'null'
			if filter_name1 != "":
				filter_name1 = filter_name1[:-1]
				filter_name1 = MySQLdb.escape_string(filter_name1).decode("utf-8")
				filter_name1 = filter_name1.replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
				filter_name1 = "E'%s'" % filter_name1
			else:
				filter_name1 = 'null'
			if filter_name2 != "":
				filter_name2 = filter_name2[:-1]
				filter_name2 = MySQLdb.escape_string(filter_name2).decode("utf-8")
				filter_name2 = filter_name2.replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
				filter_name2 = "'%s'" % filter_name2
			else:
				filter_name2 = 'null'
		else:
			filter_name1 = "null"
			filter_name2 = "null"
			filter_all = "null"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetAccClient\"(null,%s,%s,%s,%s,%s);"%(filter_name1,filter_name2,page,str(row),filter_all))
			curs.execute("select public.\"PGetAccClient\"(null,%s,%s,%s,%s,%s,%s);"%(filter_name1,filter_name2,page,str(row),filter_all, desc))
			conn.commit()
			results = curs.fetchall()[0][0]#.encode('utf-8')
			result = json.loads(results)
			#debug(results)
			data = result['data']
			for i,v in enumerate(data):
				clientprogram = base64.decodestring(v['ClientProgram'][5:])	
				ClientProgram = v['ClientProgram'].replace(v['ClientProgram'],clientprogram)		
				result['data'][i]['ClientProgram'] = ClientProgram	
			result['Result'] = True
			results = json.dumps(result)
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@acc_client_add.route('/save_acc_client', methods=['GET','POST'])
def save_acc_client():
	name = request.form.get('z3')
	clientprogram = request.form.get('z4')
	aid = request.form.get('z5')
	pid = request.form.get('z6')
	session = request.form.get('a0')
	AccUser = request.form.get('z7')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if check_role(userCode,'主机管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	name = name.replace("\\","\\\\\\\\").replace("'","''")
	clientpath = base64.b64encode(clientprogram)
	data = "E'{\"AccClientId\":\""+aid+"\",\"ProtocolId\":\""+pid+"\",\"ClientName\":\""+name+"\",\"ClientProgram\":\"b64>>"+clientpath+"\",\"AccUser\":"+AccUser+"}'"
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\"=%d" % int(pid)
			curs.execute(sql)
			pro_name = curs.fetchall()[0][0]
			
			curs.execute("select public.\"PSaveAccClient\"(%s);"%((data)))
			results = curs.fetchall()[0][0]
			acc_result = json.loads(results)
			if acc_result['Result']:
				if aid == '0':
					system_log(userCode,"创建应用发布（协议类型：%s，客户端名称：%s，路径：%s）" % (pro_name,name,clientprogram),"成功","运维管理>应用发布")
				else:
					system_log(userCode,"编辑应用发布（协议类型：%s，客户端名称：%s，路径：%s）" % (pro_name,name,clientprogram),"成功","运维管理>应用发布")
			else:
				if aid == '0':
					system_log(userCode,"创建应用发布（协议类型：%s，客户端名称：%s，路径：%s）" % (pro_name,name,clientprogram),"失败："+acc_result['ErrMsg'],"运维管理>应用发布")
				else:
					system_log(userCode,"编辑应用发布（协议类型：%s，客户端名称：%s，路径：%s）" % (pro_name,name,clientprogram),"失败："+acc_result['ErrMsg'],"运维管理>应用发布")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@acc_client_add.route('/select_acc_client_all', methods=['GET','POST'])
def select_acc_client_all():
	clientid = request.form.get('z8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if clientid != '-1':
				curs.execute("select public.\"PGetAccClient\"(%d,null,null,null,null);"%(int(clientid)))
			else:
				curs.execute("select public.\"PGetAccClient\"(null,null,null,null,null);")
			results = curs.fetchall()[0][0]
			result = json.loads(results)
			data = result['data'][0]
			clientprogram = base64.decodestring(data['ClientProgram'][5:])	
			ClientProgram = data['ClientProgram'].replace(data['ClientProgram'],clientprogram)
			result['data'][0]['ClientProgram'] = ClientProgram	
			results = json.dumps(result)
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@acc_client_add.route('/delete_acc_client', methods=['GET','POST'])				
def delete_acc_client():
	type = request.form.get('z10')
	id = request.form.get('z9')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("type:%s" % type)
			if (type == '1'):
				sql = "select \"ProtocolId\",\"ClientName\",\"ClientProgram\" from public.\"AccClient\" where \"AccClientId\" in (%s)" % id[1:-1]
				#debug("sql:%s" % sql)
				curs.execute(sql)
				acc_str_all_list = []
				acc_str_all = ""
				pro_client = curs.fetchall()
				for row in pro_client:
					sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\"=%d" % int(row[0])
					curs.execute(sql)
					pro_type = curs.fetchall()[0][0]
					acc_str_all = "协议类型：" + str(pro_type) + "，客户端名称：" + row[1] + "，路径：" + base64.b64decode(row[2][5:])
					acc_str_all_list.append(acc_str_all)
				acc_str_all = "，".join(acc_str_all_list)
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"ProtocolId\",\"ClientName\",\"ClientProgram\" from public.\"AccClient\" where \"AccClientId\"=%d" % int(id)
					#debug("sql:%s" % sql)
					curs.execute(sql)
					sel_result = curs.fetchall()
					sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\"=%d" % sel_result[0][0]
					#debug("sql:%s" % sql)
					curs.execute(sql)
					p_name = curs.fetchall()[0][0]
					acc_str = "协议名称：" + p_name + "，客户端名称："+ sel_result[0][1] + '，路径：' + base64.b64decode(sel_result[0][2][5:])
					curs.execute("select public.\"PDeleteAccClient\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0]
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除应用发布（%s）" % acc_str,"失败："+results['ErrMsg'],"运维管理>应用发布")
						return result
				system_log(userCode,"删除应用发布（%s）" % acc_str_all,"成功","运维管理>应用发布")
				return "{\"Result\":true}"
					#conn.commit()
			else:
				sql = "select \"ProtocolId\",\"ClientName\",\"ClientProgram\" from public.\"AccClient\" where \"AccClientId\"=%d" % int(id)
				#debug("sql:%s" % sql)
				curs.execute(sql)
				sel_result = curs.fetchall()
				#debug("%s" % str(sel_result))
				sql = "select \"ProtocolName\" from public.\"AccessProtocol\" where \"ProtocolId\"=%d" % sel_result[0][0]
				#debug("sql:%s" % sql)
				curs.execute(sql)
				p_name = curs.fetchall()[0][0]
				#debug("p_name:%s" % p_name)
				acc_str = "协议名称：" + p_name + "，客户端名称："+ sel_result[0][1] + '，路径：' + base64.b64decode(sel_result[0][2][5:])
				#debug("select public.\"PDeleteAccClient\"(%d);"%(int(id)))
				curs.execute("select public.\"PDeleteAccClient\"(%d);"%(int(id)))
				result = curs.fetchall()[0][0]
				results = json.loads(result)
				if results['Result']:
					system_log(userCode,"删除应用发布（%s）" % acc_str,"成功","运维管理>应用发布")
				else:
					system_log(userCode,"删除应用发布（%s）" % acc_str,"失败："+results['ErrMsg'],"运维管理>应用发布")
				return result
		#return "{\"Result\":true,\"RowCount\":1}"	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@acc_client_add.route('/get_access_protocol', methods=['GET','POST'])
def get_access_protocol():
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetAccessProtocol\"(null,null,null,null,null,null)")
			results = curs.fetchall()[0][0]
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
