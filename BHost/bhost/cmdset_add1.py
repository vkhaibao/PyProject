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
cmdset_add1 = Blueprint('cmdset_add1',__name__)
from htmlencode import check_role
from htmlencode import parse_sess,checkhostaccount


ERRNUM_MODULE_cmdset = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@cmdset_add1.route('/get_cmdset_list',methods=['GET', 'POST'])
def get_cmdset_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	page = request.form.get('z4')
	ipage = request.form.get('z5')
	keyword = request.form.get('z6')
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
	keyword = json.loads(keyword)
	if page < 0:
		page = 0
	if ipage < 0:
		ipage = 0
	if page != "null":
		row = int(page)*(int(ipage)-1)
	else:
		row = "null"
	filter_v = ""
	filter_all = ""
	filter_des = ""
	filter_cmd = ""
	if len(keyword) != 0:
		for i in keyword:
			filter_arry = i.split('-',1)
			if filter_arry[0] == "所有":
				filter_all = filter_all + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_arry[0] == "名称":
				filter_v = filter_v + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_arry[0] == "描述":
				filter_des = filter_des + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_arry[0] == "指令":
				#filter_cmd_b64 = base64.b64encode(filter_arry[1])
				filter_cmd = filter_cmd + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
	if filter_v == "":
		filter_v = 'null'
	else:
		filter_v = filter_v[:-1]
		filter_v = MySQLdb.escape_string(filter_v).decode('utf-8')
		filter_v = filter_v.replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
		filter_v = "E'%s'" % filter_v
	
	if filter_des == "":
		filter_des = 'null'
	else:
		filter_des = filter_des[:-1]
		filter_des = MySQLdb.escape_string(filter_des).decode('utf-8')
		filter_des = filter_des.replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
		filter_des = "E'%s'" % filter_des
	
	if filter_cmd == "":
		filter_cmd = 'null'
	else:
		filter_cmd = filter_cmd[:-1]
		filter_cmd = MySQLdb.escape_string(filter_cmd).decode('utf-8')
		filter_cmd = filter_cmd.replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
		filter_cmd = '"%s"' % filter_cmd
	
	if filter_all == "":
		filter_all = 'null'
	else:
		filter_all = filter_all[:-1]
		filter_all = MySQLdb.escape_string(filter_all).decode('utf-8')
		filter_all = filter_all.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
		filter_all = '"%s"' % filter_all

	filter_search = "E'{\"content\":%s,\"searchstring\":%s}'" % (filter_cmd,filter_all)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetCmdSet\"(null,%s,%s,%s,%s,%s,%s);"%(filter_v,filter_des,page,str(row),filter_search,dsc))
			conn.commit()
			results = curs.fetchall()[0][0].encode('utf-8')
			result = json.loads(results)
			data = result['data']
			for i,v in enumerate(data):
				if v['Content'] != None:	
					content = base64.decodestring(v['Content'])
					Content = v['Content'].replace(v['Content'],content)		
					result['data'][i]['Content'] = Content
			results = json.dumps(result)
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))

@cmdset_add1.route('/save_cmdset', methods=['GET','POST'])
def save_cmdset():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	name = request.form.get('z3')
	description = request.form.get('z4')
	content = request.form.get('z5')
	type = request.form.get('z6')
	id = request.form.get('z7')
	module_type = request.form.get('a10')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
			
	if module_type == None:
		title = "运维管理>指令集合"
	else:
		title = module_type
		
	if check_role(userCode,'指令授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (ERRNUM_MODULE_cmdset + 3)
	if not checkhostaccount(name):
		return '',403
		
	rdescription = description.replace('\\','\\\\\\\\').replace("'","''").replace('"','\\\\"')
	bcontent = base64.encodestring(content)
	bcontent = bcontent.replace("\n","") 
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if(type == '0'):
				data = "E'{\"CmdSetId\":0,\"Name\":\""+name+"\",\"Description\":\""+rdescription+"\",\"Content\":\""+bcontent+"\"}'"
				debug(data)
				curs.execute("select public.\"PSaveCmdSet\"(%s,0,null);"%(data))
				results = curs.fetchall()[0][0].encode('utf-8')
				debug(results)
				re_cmd = json.loads(results)
				if re_cmd['Result']:
					show_msg = "创建指令集合：%s（描述：%s，指令：%s）" % (name,description,content)
					system_log(userCode,show_msg,"成功",title)
				else:
					system_log(userCode,"创建指令集合：%s" % name,"失败："+re_cmd['ErrMsg'],title)
				
				return results
			else:	
				data = "E'{\"CmdSetId\":\""+id+"\",\"Name\":\""+name+"\",\"Description\":\""+rdescription+"\",\"Content\":\""+bcontent+"\"}'"
				curs.execute("select public.\"PSaveCmdSet\"(%s,0,null);"%(data))
				results = curs.fetchall()[0][0].encode('utf-8')
				
				re_cmd = json.loads(results)
				if re_cmd['Result']:
					show_msg = "编辑指令集合：%s（描述：%s，指令：%s）" % (name,description,content)
					system_log(userCode,show_msg,"成功",title)
				else:
					system_log(userCode,"编辑指令集合：%s" % name,"失败："+re_cmd['ErrMsg'],title)
				return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d)\"}" % (ERRNUM_MODULE_cmdset + 3)

@cmdset_add1.route('/select_cmdset_all', methods=['GET','POST'])
def select_cmdset_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('z8')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if id != "-1":
				curs.execute("select public.\"PGetCmdSet\"(%d,null,null,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetCmdSet\"(null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			result = json.loads(results)
			data = result['data']
			for i,v in enumerate(data):
				if v['Content'] != None:
					content = base64.decodestring(v['Content'])
					Content = v['Content'].replace(v['Content'],content)
					result['data'][i]['Content'] = Content
			results = json.dumps(result)
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))

@cmdset_add1.route('/delete_cmdset', methods=['GET','POST'])				
def delete_cmdset():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type = request.form.get('z10')
	id = request.form.get('z9')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"Name\" from public.\"CmdSet\" where \"CmdSetId\" in (%s)" % id[1:-1]
				debug("sql:%s" % sql)
				curs.execute(sql)
				cmd_str = ""
				for row in curs.fetchall():
					cmd_str = cmd_str + row[0].encode('utf-8') + ","
				
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"Name\" from public.\"CmdSet\" where \"CmdSetId\"=%d" % int(id)
					debug("sql:%s" % sql)
					curs.execute(sql)
					cmd_name = curs.fetchall()[0][0].encode('utf-8')
					
					curs.execute("select public.\"PDeleteCmdSet\"(%d,0,null);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除指令集合：%s" % cmd_name,"失败："+results['ErrMsg'],"运维管理>指令集合")
						conn.rollback();
						return result
				if cmd_str != "":
					system_log(userCode,"删除指令集合：%s" % cmd_str[:-1],"成功","运维管理>指令集合")
				return "{\"Result\":true}"	
			else:
				sql = "select \"Name\" from public.\"CmdSet\" where \"CmdSetId\"=%d" % int(id)
				debug("sql:%s" % sql)
				curs.execute(sql)
				cmd_name = curs.fetchall()[0][0].encode('utf-8')
				
				curs.execute("select public.\"PDeleteCmdSet\"(%d,0,null);"%(int(id)))
				result = curs.fetchall()[0][0].encode('utf-8')
				re_cmd = json.loads(result)
				if re_cmd['Result']:
					system_log(userCode,"删除指令集合：%s" % cmd_name,"成功","运维管理>指令集合")
				else:
					system_log(userCode,"删除指令集合：%s" % cmd_name,"失败："+re_cmd['ErrMsg'],"运维管理>指令集合")
				return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))

@cmdset_add1.route('/get_index', methods=['GET','POST'])				
def get_index():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	rec_id = request.form.get('z1')
	tab_id = request.form.get('z2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_cmdset+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if tab_id == '2' or tab_id == '10' or tab_id == '26':
				debug("select public.\"PGetRecordRownum\"(%d,%d,0,'%s');"%(int(rec_id),int(tab_id),userCode))
				curs.execute("select public.\"PGetRecordRownum\"(%d,%d,0,E'%s');"%(int(rec_id),int(tab_id),userCode))
			else:
				curs.execute("select public.\"PGetRecordRownum\"(%d,%d);"%(int(rec_id),int(tab_id)))
			
			result = curs.fetchall()
			debug("result:%s" % str(result))
			if result[0][0] != None:
				return str(result[0][0])
			else:
				return "1"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_cmdset + 3, ErrorEncode(e.args[1]))
	
