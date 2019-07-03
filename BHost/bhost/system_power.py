#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import time
import json
import MySQLdb
import urllib
import htmlencode
import cgi
import redis

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
import base64
from logbase import common
from logbase import defines
from logbase import task_client
from generating_log import system_log
from flask import request,Blueprint,render_template,send_from_directory # 

import xml.etree.ElementTree as ET

system_power = Blueprint('system_power',__name__)
ERRNUM_MODULE_system_power = 100000
reload(sys)
sys.setdefaultencoding('utf-8')
def debug(c):
	return 0
	path = "/var/tmp/debugyt.txt"
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
	
###系统重启
@system_power.route("/system_reboot", methods=['GET', 'POST'])
def system_reboot():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	t = 'system_reboot.html'
	system_type = common.get_server_cluster_type();
	return render_template(t,se=session,us=userCode,system_type=system_type)

###系统重启
@system_power.route("/system_shutdown", methods=['GET', 'POST'])
def system_shutdown():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	t = 'system_shutdown.html'
		   
	system_type = common.get_server_cluster_type();
	return render_template(t,se=session,us=userCode,system_type=system_type)

	
#获取当前所有的服务器
@system_power.route("/get_cluster", methods=['GET', 'POST'])
def get_cluster():
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
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	sql = "select server_id,ip from  server_global order by server_id;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	result_str = ""
	for result in results:
		server_id = result[0]
		ip = result[1].encode('utf-8')
		result_str += "{\"server_id\":%d,\"ip\":\"%s\"},"%(server_id,ip)
	result_str = result_str[:-1]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (result_str)

#重启
@system_power.route("/reboot", methods=['GET', 'POST'])
def reboot():	
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
	oper = request.form.get('o1')	
	server_id_str = request.form.get('a1')
	all_flag = request.form.get('f1')
	
	if all_flag < 0:
		all_flag = 0
	else:
		all_flag = int(all_flag)
	sreboot = request.form.get('z1')	
	if sreboot < 0:
		sreboot = 0
	else:
		sreboot = int(sreboot)	
		
	if server_id_str == "" or server_id_str <0:
		server_id_str = ""
	#server_id_list = server_id_str.split(',')
	
	###清除 key超过一天的
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, defines.REDIS_MQ_DB);
	keys = r.keys()
	for c in keys:
		if c.find(":reboot")>=0:
			t = int(c.split(':')[0])/1000 # 秒级
			ct = time.time();
			if ct - t > 60 * 60 * 24: ##超过 一天的 清除掉
				r.delete(c)

	
	task_content = '[global]\nclass = taskpower\ntype = reboot\nserver_id_str=%s\nall_flag=%d\nsreboot=%d\nsession=%s\nflag=0' %(server_id_str,all_flag,sreboot,session)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		if not system_log(userCode,oper,"系统异常: %s(%d)"%(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno),'系统管理>系统重启'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
			
	if not system_log(userCode,oper,"成功",'系统管理>系统重启'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return "{\"Result\":true,\"info\":\"\"}"
		

#重启程序
@system_power.route("/reboot_pid", methods=['GET', 'POST'])
def reboot_pid():	
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
	oper = request.form.get('o1')	
	server_id_str = request.form.get('a1')
	if server_id_str == "" or server_id_str <0:
		server_id_str = ""
	#server_id_list = server_id_str.split(',')
		
	task_content = '[global]\nclass = taskpower\ntype = reboot_pid\nserver_id_str=%s\n' %(server_id_str)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		if not system_log(userCode,oper,"系统异常: %s(%d)"%(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno),'系统管理>系统重启程序'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
			
	if not system_log(userCode,oper,"成功",'系统管理>系统重启程序'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return "{\"Result\":true,\"info\":\"\"}"
		
#关闭
@system_power.route("/shutdown", methods=['GET', 'POST'])
def shutdown():	
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
	oper = request.form.get('o1')	
	server_id_str = request.form.get('a1')
	all_flag = request.form.get('f1')
	if all_flag < 0:
		all_flag = 0
	else:
		all_flag = int(all_flag)
	sreboot = request.form.get('z1')	
	if sreboot < 0:
		sreboot = 0
	else:
		sreboot = int(sreboot)	
	if server_id_str == "" or server_id_str <0:
		server_id_str = ""
	#server_id_list = server_id_str.split(',')
	
	###清除 key超过一天的
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, defines.REDIS_MQ_DB);
	keys = r.keys()
	for c in keys:
		if c.find(":halt")>=0:
			t = int(c.split(':')[0])/1000 # 秒级
			ct = time.time();
			if ct - t > 60 * 60 * 24: ##超过 一天的 清除掉
				r.delete(c)
	
	task_content = '[global]\nclass = taskpower\ntype = shutdown\nserver_id_str=%s\n\nall_flag=%d\nsession=%s\nsreboot=%d\nflag=0' %(server_id_str,all_flag,session,sreboot)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		if not system_log(userCode,oper,"系统异常: %s(%d)"%(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno),'系统管理>系统关闭'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
	if not system_log(userCode,oper,"成功",'系统管理>系统关闭'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return "{\"Result\":true,\"info\":\"\"}"		
	
#是否重启成功
@system_power.route("/if_reboot_succ", methods=['GET', 'POST'])
def if_reboot_succ():	
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
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	crm = r.get(session+":reboot")		
	return "{\"Result\":true,\"info\":\"%s\"}" %(str(crm))
	
#是否关闭成功
@system_power.route("/if_halt_succ", methods=['GET', 'POST'])
def if_halt_succ():	
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
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	crm = r.get(session+":halt")	
	return "{\"Result\":true,\"info\":\"%s\"}" %(str(crm))