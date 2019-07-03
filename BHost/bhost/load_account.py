#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
import pyodbc
import MySQLdb
import json
import time
import base64
import csv
import math

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from ctypes import *
from logbase import common
from logbase import defines
from logbase import task_client
from urllib import unquote

from htmlencode import parse_sess
from htmlencode import check_role

from generating_log import system_log
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
from jinja2 import Environment,FileSystemLoader 
from comm_function import PGetSecurityPasswd
load_account = Blueprint('load_account',__name__)

ERRNUM_MODULE_load_account = 1000
reload(sys)
sys.setdefaultencoding('utf-8')

def debug(c):
	return 0
	# path = "/var/tmp/debugzdpg_test.txt"
	path = "/var/tmp/debughrj_load.txt"
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

@load_account.route('/PGetHostList_m',methods=['GET', 'POST'])
def PGetHostList_m():
	session = request.form.get('a0')
	hgid = request.form.get('a1')
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
			sql = "select public.\"PGetHostList_m\"(%s,E'%s')" % (hgid,userCode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results==None:
				results='[]'
			else:
				results=results.encode('utf-8')
			return "{\"Result\":true,\"info\":%s}"%results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/load_account_z',methods=['GET', 'POST'])
def load_account_z():
	session = request.form.get('a0')
	data = request.form.get('a1')
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

	if check_role(userCode,'主机管理') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" %(sys._getframe().f_lineno)

	json_data = json.loads(data)
	for acc_i in json_data['AccountSet']:
		if acc_i['Password'] != None:
			lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
			pwd_rc4 = c_char_p()# 定义一个指针
			lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
			lib.encrypt_pwd.restype = None #定义函数返回值
			pwd_rc4.value = "0"*512 # 初始化 指针
			lib.encrypt_pwd((acc_i['Password']),pwd_rc4);#执行函数
			acc_i['Password'] = pwd_rc4.value #获取变量的值
	data = json.dumps(json_data)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PBatchSaveHostAccount\"(E'%s')" % MySQLdb.escape_string(data).decode('utf-8')
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			re_save = json.loads(results)
			data_json = json.loads(data)
			'''
			host_str = ""
			hg_str = ""
			detail_str = ""
			if len(data_json['HostSet']) != 0:
				for hostset in data_json['HostSet']:
					host_str = host_str + hostset['HostName'] + '，'
				if host_str != "":
					host_str = host_str[:-2]
					detail_str = "主机：" + host_str + '，'

			if len(data_json['HGroupSet']) != 0:
				for hgname in data_json['HGroupSet']:
					hg_str = hg_str + hgname['HGName'] + ','
				if hg_str != "":
					hg_str = hg_str[:-1]
					detail_str = "主机组：" + hg_str + ','
			if detail_str != "":
				detail_str = detail_str[:-1]
			'''
			show_msg_list = []
			if re_save['SuccLog'] != "":
				show_msg = "成功（%s）" % re_save['SuccLog']
				show_msg_list.append(show_msg)
			if re_save['FailLog'] != "":
				show_msg = "失败（%s）" % re_save['FailLog']
				show_msg_list.append(show_msg)
			if re_save['Result']:
				if len(show_msg_list) > 0:
					system_log(userCode,"批量保存账号：%s" % ('，'.join(show_msg_list)),"成功","运维管理>主机管理")
				#system_log(userCode,"批量保存账号：%s（%s）" % (data_json['AccountSet'][0]['HostAccount']['AccountName'],detail_str),"成功：%s，失败：%s" % (re_save['SuccCount'],re_save['FailCount']),"主机管理>批量账号")
			else:
				if len(show_msg_list) > 0:
					system_log(userCode,"批量保存账号：%s" % ('，'.join(show_msg_list)),"失败","运维管理>主机管理")
				#system_log(userCode,"批量保存账号：%s（%s）" % (data_json['AccountSet'][0]['HostAccount']['AccountName'],detail_str),"失败","主机管理>批量账号")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/delete_account_z',methods=['GET', 'POST'])
def delete_account_z():
	session = request.form.get('a0')
	data = request.form.get('a1')
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

	if check_role(userCode,'主机管理') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PBatchDeleteHostAccount\"(E'%s')" % MySQLdb.escape_string(data).decode('utf-8')
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			re_save = json.loads(results)
			data_json = json.loads(data)
			host_str = ""
			hg_str = ""
			detail_str = ""
			if len(data_json['HostSet']) != 0:
				for hostset in data_json['HostSet']:
					host_str = host_str + hostset['HostName'] + ','
				if host_str != "":
					host_str = host_str[:-1]
					detail_str = "主机：" + host_str + ','

			if len(data_json['HGroupSet']) != 0:
				for hgname in data_json['HGroupSet']:
					hg_str = hg_str + hgname['HGName'] + ','
				if hg_str != "":
					hg_str = hg_str[:-1]
					detail_str = detail_str + "主机组：" + hg_str + ','
			
			ServiceName_str = ""
			for sername in data_json['AccountSet'][0]['HostServiceSet']:
				ServiceName_str = ServiceName_str + sername['ServiceName'] + ','
			if ServiceName_str != "":
				ServiceName_str = ServiceName_str[:-1]
				detail_str = detail_str + "服务：" + ServiceName_str + ','
			if detail_str != "":
				detail_str = detail_str[:-1]
			if re_save['Result']:
				system_log(userCode,"批量删除账号：%s（%s）" % (data_json['AccountSet'][0]['AccountName'],detail_str),"成功：%s，失败：%s" % (re_save['SuccCount'],re_save['FailCount']),"运维管理>主机管理")
			else:
				system_log(userCode,"批量删除账号：%s（%s）" % (data_json['AccountSet'][0]['AccountName'],detail_str),"失败","运维管理>主机管理")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@load_account.route('/PFindHostDirectory_account',methods=['GET', 'POST'])
def PFindHostDirectory_account():
	session = request.form.get('a0')
	filter_value = request.form.get('a1')
	data_arry = json.loads(filter_value)
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	filter_hgname= ""
	filter_hname = ""
	filter_ip = ""
	filter_all = ""
	if len(data_arry) != 0:
		for i in data_arry:
			filter_arry = i.split('-',1)
			if filter_arry[0] == "所有":
				filter_all = filter_all + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_arry[0] == "组名":
				filter_hgname = filter_hgname + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_arry[0] == "主机名":
				filter_hname = filter_hname + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
			if filter_arry[0] == "IP":
				filter_ip = filter_ip + MySQLdb.escape_string(filter_arry[1]).decode("utf-8") + '\n'
		if filter_hgname != "":
			filter_hgname = filter_hgname[:-1]
			filter_hgname = MySQLdb.escape_string(filter_hgname).decode("utf-8")
			filter_hgname = '"%s"' % filter_hgname
		else:
			filter_hgname = "null"
		if filter_hname != "":
			filter_hname = filter_hname[:-1]
			filter_hname = MySQLdb.escape_string(filter_hname).decode("utf-8")
			filter_hname = '"%s"' % filter_hname
		else:
			filter_hname = "null"		
		if filter_ip != "":
			filter_ip = filter_ip[:-1]
			filter_ip = MySQLdb.escape_string(filter_ip).decode("utf-8")
			filter_ip = '"%s"' % filter_ip
		else:
			filter_ip = "null"
		if filter_all != "":
			filter_all = filter_all[:-1]
			filter_all = MySQLdb.escape_string(filter_all).decode("utf-8")
			filter_all = '"%s"' % filter_all
		else:
			filter_all = "null"	
		
		#filter_hgname = filter_hgname.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		#filter_hname = filter_hname.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		#filter_ip = filter_ip.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
	data = '{"type":0,"id":0,"loginusercode":"'+str(userCode)+'","istree":true,"hgid":0,"hgname":'+filter_hgname+',"hostname":'+filter_hname+',"hostip":'+filter_ip+',"searchstring":'+filter_all+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PFindHostDirectory\"(E'%s')" % (MySQLdb.escape_string(data).decode("utf-8"))
			curs.execute(sql)
			results = curs.fetchall()[0][0]#.encode('utf-8')
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/get_hosttask_data',methods=['GET', 'POST'])
def get_hosttask_data():
	se = request.form.get('a0')
	cur = request.form.get('z1')
	page_total = request.form.get('z2')
	keyword = request.form.get('z3')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	debug("enter get_hosttask_data")
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	#data = '{"hostleadintaskid":null,"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": null,"offsetrow": null}'
	debug("next")
	if page_total == 'null':
		offsetrow = 'null'
	else:
		offsetrow = str((int(cur)-1)*(int(page_total)))
	data = '{"hostleadintaskid":null,"limitrow":'+page_total+',"offsetrow":'+offsetrow+',"UserCode": "'+userCode+'"}'
	#data = '{"hostleadintaskid":null,"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": '+page_total+',"offsetrow": '+offsetrow+'}'
	debug("data::"+str(data));
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			# select public."PGetHostLeadInTask"('{"hostleadintaskid":null,"limitrow":5,"offsetrow":0}')
			sql = "select public.\"PGetHostLeadInTask\"(E'%s')" % data
			#sql = "select public.\"PGetHostLeadInTaskDetail\"('%s')" % data
			debug("get_hosttask_data:::"+sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		debug("error_hrj")
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/get_hostexport_data',methods=['GET', 'POST'])
def get_hostexport_data():
	se = request.form.get('a0')
	cur = request.form.get('z1')
	page_total = request.form.get('z2')
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
	data = '{"HostExportTaskId":null,"limitrow":'+page_total+',"offsetrow":'+offsetrow+'}'
	debug("data::"+str(data));
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetHostExportTask\"(E'%s')" % data
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/del_hostexport',methods=['GET', 'POST'])		
def del_hostexport():
	se = request.form.get('a0')
	del_type = request.form.get('z1')
	del_id = request.form.get('z2')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
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
		md5_json = StrMD5(del_type);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(userCode,'主机管理') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			if del_type == '1':
				id_array = del_id[1:-1].split(',')
				sql = "select \"HostExportTaskName\" from private.\"HostExportTask\" where \"HostExportTaskId\" in (%s)" % del_id[1:-1]
				curs.execute(sql)
				taskname_str = ""
				for taskname in curs.fetchall():
					taskname_arr=taskname[0].split('.')
					taskname_arr.pop(-2)
					taskname_arr.pop(-2)
					taskname_arr.pop(-2)
					taskname_str = taskname_str + '.'.join(taskname_arr) + ','
				if taskname_str != "":
					taskname_str = taskname_str[:-1]
				
				for id_v in id_array:
					curs.execute("select \"HostExportTaskName\" from private.\"HostExportTask\" where \"HostExportTaskId\" = %s" % id_v)
					sel_re = curs.fetchall()[0][0]
					sel_re_arr=sel_re.split('.')
					sel_re_arr.pop(-2)
					sel_re_arr.pop(-2)
					sel_re_arr.pop(-2)
					curs.execute("select public.\"PDeleteHostExportTask\"(%d);"%(int(id_v)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除导出任务：%s" % '.'.join(sel_re_arr), "失败", "运维管理>主机管理")
						conn.rollback()
						return result
					else:
						task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(sel_re))
						if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
								return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				system_log(userCode,"删除导出任务：%s" % taskname_str, "成功", "运维管理>主机管理")
				return "{\"Result\":true}"
			else:
				curs.execute("select \"HostExportTaskName\" from private.\"HostExportTask\" where \"HostExportTaskId\" = %s" % del_id)
				sel_re = curs.fetchall()[0][0]
				sel_re_arr=sel_re.split('.')
				sel_re_arr.pop(-2)
				sel_re_arr.pop(-2)
				sel_re_arr.pop(-2)
				# curs.execute("delete from private.\"HostImportTask\" where \"HostImportTaskId\" = %s" % del_id)
				curs.execute("select public.\"PDeleteHostExportTask\"(%d);"%(int(del_id)))
				result = curs.fetchall()[0][0].encode('utf-8')
				re_del = json.loads(result)
				if re_del['Result']:
					task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(sel_re))
					if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
							return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					system_log(userCode,"删除导出任务：%s" % '.'.join(sel_re_arr), "成功", "运维管理>主机管理")
				else:
					system_log(userCode,"删除导出任务：%s" % '.'.join(sel_re_arr), "失败", "运维管理>主机管理")
				return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#exist_download_host
@load_account.route('/exist_download_host',methods=['GET', 'POST'])		
def exist_download_host():
	se = request.form.get("a0")
	file_name = request.form.get("a1")
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			sys.exit()
	elif error > 0:
			if error == 2:
					return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
			else:
					return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
			sys.exit()
	if os.path.exists('/usr/storage/.system/dwload/'+file_name):
			return '{\"Result\":true}'
	else:
			return '{\"Result\":false,"ErrMsg":"文件不存在"}'

@load_account.route('/del_hosttask',methods=['GET', 'POST'])		
def del_hosttask():
	se = request.form.get('a0')
	del_type = request.form.get('z1')
	del_id = request.form.get('z2')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
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
		md5_json = StrMD5(del_type);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(userCode,'主机管理') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if del_type == '1':
				id_array = del_id[1:-1].split(',')
				sql = "select \"HostLeadInTaskName\" from private.\"HostLeadInTask\" where \"HostLeadInTaskId\" in (%s)" % del_id[1:-1]
				curs.execute(sql)
				taskname_str = ""
				for taskname in curs.fetchall():
					taskname_str = taskname_str + taskname[0] + ','
				if taskname_str != "":
					taskname_str = taskname_str[:-1]
				
				for id_v in id_array:
					curs.execute("select \"HostLeadInTaskName\" from private.\"HostLeadInTask\" where \"HostLeadInTaskId\" = %s" % id_v)
					sel_re = curs.fetchall()[0][0]
					curs.execute("delete from private.\"HostImportTask\" where \"HostImportTaskId\" = %s" % id_v)
					curs.execute("select public.\"PDeleteHostLeadInTask\"(%d);"%(int(id_v)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除任务：%s" % sel_re, "失败", "运维管理>主机管理")
						conn.rollback()
						return result
				system_log(userCode,"删除任务：%s" % taskname_str, "成功", "运维管理>主机管理")
				return "{\"Result\":true}"
			else:
				curs.execute("select \"HostLeadInTaskName\" from private.\"HostLeadInTask\" where \"HostLeadInTaskId\" = %s" % del_id)
				sel_re = curs.fetchall()[0][0]
				curs.execute("delete from private.\"HostImportTask\" where \"HostImportTaskId\" = %s" % del_id)
				curs.execute("select public.\"PDeleteHostLeadInTask\"(%d);"%(int(del_id)))
				result = curs.fetchall()[0][0].encode('utf-8')
				re_del = json.loads(result)
				if re_del['Result']:
					system_log(userCode,"删除任务：%s" % sel_re, "成功", "运维管理>主机管理")
				else:
					system_log(userCode,"删除任务：%s" % sel_re, "失败", "运维管理>主机管理")
				return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/get_hosttask_detail',methods=['GET', 'POST'])
def get_hosttask_detail():
	se = request.form.get('a0')
	cur = request.form.get('z1')
	page_total = request.form.get('z2')
	keyword = request.form.get('z3')
	taskid = request.form.get('z4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	#data = '{"hostleadintaskid":null,"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": null,"offsetrow": null}'
	if page_total == 'null':
		offsetrow = 'null'
	else:
		offsetrow = str((int(cur)-1)*(int(page_total)))
	keyword = json.loads(keyword)
	status_v = 0
	if len(keyword) == 0:
		status = "null"
	else:
		for key_v in keyword:
			key_arry = key_v.split('-',1)
			if key_arry[0] == "status":
				status_v = status_v + int(key_arry[1])
		#2 7 5
		if status_v == 14:#所有连接成功+登录失败+连接失败+不支持连接测试
			status = "11"
		elif status_v == 12:#登陆失败+连接失败+不支持连接测试
			status = "9"
		elif status_v == 7 and len(keyword) > 1:#不支持连接测试+成功
			status = "8"
		elif status_v == 9:#成功+登陆失败+连接失败
			status = "7"
		elif status_v == 7 and len(keyword) == 1:#登陆失败+连接失败
			status = "10"
		elif status_v == 2:#成功
			status = "2"
		elif status_v == 5:#不支持连接测试
			status = "5"
	data = '{"hostleadintaskid":'+taskid+',"status":'+status+',"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": '+page_total+',"offsetrow": '+offsetrow+'}'
	#data = '{"hostleadintaskid":'+taskid+',"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": '+page_total+',"offsetrow": '+offsetrow+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetHostLeadInTaskDetail\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@load_account.route('/get_import_deatil',methods=['GET', 'POST'])
def get_import_deatil():
	se = request.form.get('a0')
	t_id = request.form.get('z1')
	keyword = request.form.get('z2')
	limitrow = request.form.get('z3')
	offsetrow = request.form.get('z4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	keyword = json.loads(keyword)
	debug("398  ::"+str(keyword))
	if len(keyword) == 0:
		status = "null"
	else:
		for key_v in keyword:
			key_arry = key_v.split('-',1)
			if key_arry[0] == "status":
				status = key_arry[1]
	if limitrow == "null":
		offsetrow = "null"
	data = '{"hostimporttaskid":'+t_id+',"status":'+status+',"limitrow": '+limitrow+',"offsetrow": '+offsetrow+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetHostImportTask\"(E'%s')" % data
			debug("get_import_deatil  sql::"+sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/isexist_data',methods=['GET', 'POST'])
def isexist_data():
	se = request.form.get('a0')
	file_v = request.form.get('file_v')
	# file_change = request.form.get('file_change')
	# #name = request.form.get('z1')
	# f = request.files['file_change']
	fname = file_v
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
			sql = "select \"Status\",\"HostLeadInTaskName\" from private.\"HostLeadInTask\" where \"HostLeadInTaskName\" = E\'%s\'" % MySQLdb.escape_string(f_name).decode("utf-8")
			debug("isexist_data:"+sql);
			curs.execute(sql)
			debug("441")
			results = curs.fetchall()
			debug("443")
			debug("results::"+str(len(results)))
			for i in range(len(results)):
				debug("446")
				a = results[i]
				debug("448")
				#debug("results[i]::"+results[i])
				debug("450")
				debug("451:::"+str(a[0]))
				debug("452")
				if a[0] == 4:
					debug("454")
					return "{\"Result\":false}"
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
@load_account.route('/get_detail_count',methods=['GET', 'POST'])
def get_detail_count():	
	se = request.form.get('a0')
	taskid = request.form.get('z1')
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
			#失败
			sql = "select count(*) from private.\"HostLeadInTaskDetail\" where \"Status\" in(3,4,5) and \"HostLeadInTaskId\"= %s" % taskid
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				fail_count = 0
			else:
				fail_count = results[0][0]
			#不支持连接测试
			sql = "select count(*) from private.\"HostLeadInTaskDetail\" where \"Status\"=5 and \"HostLeadInTaskId\"= %s" % taskid
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				support_count = 0
			else:
				support_count = results[0][0]
			#成功
			sql = "select count(*) from private.\"HostLeadInTaskDetail\" where \"Status\"=2 and \"HostLeadInTaskId\"= %s" % taskid
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				succ_count = 0
			else:
				succ_count = results[0][0]
			#账号个数
			sql = "select count(*) from private.\"HostLeadInTaskDetail\" where \"HostLeadInTaskId\"= %s" % taskid
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				account_count = 0
			else:
				account_count = results[0][0]
			return "{\"Result\":true,\"succ_count\":"+str(succ_count)+",\"fail_count\":"+str(fail_count)+",\"account_count\":"+str(account_count)+",\"support_count\":"+str(support_count)+"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@load_account.route('/get_down_ok',methods=['GET', 'POST'])
def get_down_ok():
	se = request.form.get('a0')
	type = request.form.get('a1')
	time1 = request.form.get('a2')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			file_name='host.%s.%s.%s'%(userCode,se,time1)
			progress_file_name='host.%s.%s.%s.num'% (userCode,se,time1)
			path = "/usr/storage/.system/dwload/host.%s.%s.%s.num"%(userCode,se,time1)
			if os.path.exists(path):
				fp = open(path,"r")
				if fp :
					line=fp.read().split(':')	
					if line[0]=='0':
						progress=0
					else:
						progress=math.ceil((int(line[0])-1)/int(line[1]))
					fp.close()
			else:
				progress=0
			sql = "select * from private.\"HostExportTask\" where \"HostExportTaskName\" like E'%"+file_name+"%' and \"Status\"<>0;"
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				if results[0][2]==1:
					return "{\"Result\":true,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"progress\":\"100\",\"file_name\":\""+str(results[0][1])+"\"}"
				else:
					return "{\"Result\":false,\"ErrMsg\":\""+str(results[0][3])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"progress\":\"\",\"file_name\":\""+str(results[0][1])+"\"}"
			else:
				return "{\"Result\":true,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"progress\":\""+str(progress)+"\",\"file_name\":\"\"}"
				#return "{\"Result\":true,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"progress\":\""+str(progress)+"\",\"file_name\":\""+str(results[0][1])+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@load_account.route('/download_file',methods=['GET', 'POST'])
def download_file():
	se = request.form.get('a0')
	if se<0:
		se = request.args.get('a0')
	file_name = request.form.get('a1')
	if file_name<0:
		file_name = request.args.get('a1')
	file_name_arr=file_name.split('.')
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	return send_from_directory('/usr/storage/.system/dwload',file_name,as_attachment=True,attachment_filename=('.'.join(file_name_arr)))
	

@load_account.route('/del_host_file',methods=['GET', 'POST'])
def del_host_file():
	se = request.form.get('a0')
        time1 = request.form.get('z1')
        client_ip = request.remote_addr
        (error,userCode,mac) = SessionCheck(se,client_ip);
        if error < 0:
                return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        elif error > 0:
                if error == 2:
                        return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
                else:
                        return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/host.%s.%s.%s.num\n'%(userCode,se,time1)
   	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
      		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return 'true'
