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
from logbase import defines
from logbase import task_client
from generating_log import system_log
from htmlencode import checkaccount
from htmlencode import check_role
from htmlencode import parse_sess,checkhostaccount,checkaccount

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
access_auth_z = Blueprint('access_auth_z',__name__)

ERRNUM_MODULE_access_auth_z = 1000

reload(sys)
sys.setdefaultencoding('utf-8')

global t
t = 0

def cmp(src_data,dst_data):
	global t
	if isinstance(src_data, dict):
		"""若为dict格式"""
		for key in dst_data:
			if key == "DeleteAuthObject" or key == "AuthObject":
				continue
			if key not in src_data:
				t += 1 
				#print("src不存在这个key")
		for key in src_data:
			if key in dst_data:
				thiskey = key
				"""递归"""
				cmp(src_data[key], dst_data[key])
			else:
				dic[key] = ["dst不存在这个key"]
	elif isinstance(src_data, list):
		"""若为list格式"""
		if len(src_data) != len(dst_data):
			t += 1 
			#print("list len: '{}' != '{}'".format(len(src_data), len(dst_data)))
		for src_list, dst_list in zip(sorted(src_data), sorted(dst_data)):
			"""递归"""
			cmp(src_list, dst_list)
	else:
		if str(src_data) != str(dst_data):
			t += 1 
			#print(src_data)

def debug(c):
	return 0
	path = "/var/tmp/debugzdp123.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@access_auth_z.route('/get_hostdirectory_z',methods=['GET','POST'])
def get_hostdirectory_z():
	session = request.form.get('a0')
	hid = request.form.get('z1')
	aid = request.form.get('z2')
	find_doing = request.form.get('z3')
	loginusercode = request.form.get('z4')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if aid == "":
		aid = '-1'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if aid != '-1':
				if str(find_doing) == 'true':
					#debug("select public.\"PGetHostDirectory\"('%s',%d,3,%d,null,null,%s);" %(usercode,int(hid),int(aid),str(find_doing)))
					curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,3,%d,null,null,%s);" %(loginusercode,int(hid),int(aid),str(find_doing)))
				else:
					#debug("select public.\"PGetHostDirectory\"('%s',%d,3,%d,null,null);" %(usercode,int(hid),int(aid)))
					curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,3,%d,null,null);" %(loginusercode,int(hid),int(aid)))
			else:
				#debug("select public.\"PGetHostDirectory\"('%s',%d,3,null,null,null);" %(usercode,int(hid)))
				curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,3,null,null,null);" %(loginusercode,int(hid)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_userdirectory_z',methods=['GET','POST'])
def get_userdirectory_z():
	session = request.form.get('a0')
	ugid = request.form.get('z1')
	uid = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if ugid == "-1":
		ugid = "0"
	if uid == "-1":
		uid = "null"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetUserDirectory\"('%s',%s,4,%s,null,null);" %(usercode,ugid,uid))
			curs.execute("select public.\"PGetUserDirectory\"(E'%s',%s,4,%s,null,null);" %(usercode,ugid,uid))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))


@access_auth_z.route('/get_AccessStrategy',methods=['GET','POST'])
def get_AccessStrategy():
	session = request.form.get('a0')
	id = request.form.get('z1')
	name = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if name != '':
				if checkhostaccount(name) == False:
					return '',403
				curs.execute("select public.\"PGetAccessStrategy\"(null,E'%s',null,1,null,null);" %(name))
			else:				
				if id == '-1':
					curs.execute("select public.\"PGetAccessStrategy\"(null,null,null,1,null,null);")
				else:
					if(str(id).isdigit() == False):
						return '',403
					curs.execute("select public.\"PGetAccessStrategy\"(%d,null,null,1,null,null);"%(int(id)))	
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_ServerScope',methods=['GET','POST'])
def get_ServerScope():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetServerScope\"(null,null,true,null,null,E'%s',null);" % usercode)
			#debug("select public.\"PGetServerScope\"(null,null,true,null,null,'%s');" % usercode)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_AccountProtocolForAuth',methods=['GET','POST'])
def get_AccountProtocolForAuth():
	session = request.form.get('a0')
	data = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	data=json.loads(data)
	data['LoginUserCode']=usercode
	data=json.dumps(data)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetAccountProtocolForAuth\"(\'%s\');"%(data))
			curs.execute("select public.\"PGetAccountProtocolForAuth\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_ConnParam',methods=['GET','POST'])
def get_ConnParam():
	session = request.form.get('a0')
	pid = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetConnParam\"(%d,null,null,null,null,null,null);"%(int(pid)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_manager_z',methods=['GET','POST'])
def get_manager_z():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	user_value=request.form.get('a1')
	type_value=request.form.get('a2')
	if type_value<0:
		type_value=1
	if not checkaccount(user_value):
		return '',403
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        try:
                with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
                        curs.execute("select public.\"PGetUser\"(null,%s);"%type_value)
                        results = curs.fetchall()[0][0].encode('utf-8')
                        result_json = json.loads(results)
                        #debug("select a.\"UserId\" from public.\"User\" a where a.\"UserCode\"='%s';" %usercode)
                        curs.execute("select a.\"UserId\" from public.\"User\" a where a.\"UserCode\"=E'%s';" %user_value)
                        loginuserid=curs.fetchall()[0][0]
                        debug(str(result_json))
                        for index,i in enumerate(result_json):
                                debug("select public.\"IsAllowToManageAuth\"(%s, %s);" %(str(i['UserId']), str(loginuserid)))
                                curs.execute("select public.\"IsAllowToManageAuth\"(%s, %s);" %(str(i['UserId']), str(loginuserid)))
                                result_flag = curs.fetchall()[0][0]
                                debug(str(result_flag))
                                if str(result_flag) == '0':
                                        #del result_json[index]
                                        i['del'] = "true"
                                else:
                                        i['del'] = "false"
                        def fun1(s):
                                return s['del'] if s['del'] != "true" else None
                        result_json1 = filter(fun1, result_json)
                        results = json.dumps(result_json1)
                        return results

	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_timeset_z',methods=['GET','POST'])
def get_timeset_z():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetTimeSet\"(null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_clientset_z',methods=['GET','POST'])
def get_clientset_z():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetClientScope\"(null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_macset_z',methods=['GET','POST'])
def get_macset_z():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetMACSet\"(null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_approval_z',methods=['GET','POST'])
def get_approval_z():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetApproveStrategy\"(null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_eventalarm_z',methods=['GET','POST'])
def get_eventalarm_z():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetEventAlarmInfo\"(null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/save_AccessStrategy',methods=['GET','POST'])
def save_AccessStrategy():
	session = request.form.get('a0')
	data = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PSaveAccessStrategy\"('%s',0,0);"%(data))
			curs.execute("select public.\"PSaveAccessStrategy\"(E'%s',0,0);"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@access_auth_z.route('/save_AccessAuth',methods=['GET','POST'])
def save_AccessAuth():
	debug('save_AccessAuth')
	session = request.form.get('a0')
	data = request.form.get('z1')
	#prv_data = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			debug('1')
			curs.execute("select public.\"PSaveAccessAuth\"(E\'%s\');"%(MySQLdb.escape_string(data).decode("utf-8")))
			results = curs.fetchall()[0][0].encode('utf-8')
			results_json=json.loads(results)
			if results_json["Result"] == False:
				data0 = json.loads(data)
				if data0['AccessAuthId'] == 0:
					system_log(usercode,"创建访问授权：%s" % data0['AccessAuthName'],"失败","运维管理>访问授权")
				else:
					#data1 = json.loads(prv_data)
					#cmp(data0,data1)
					#if t != 0:
					system_log(usercode,"编辑访问授权：%s" % data0['AccessAuthName'],"失败","运维管理>访问授权")
				return results
			task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=3\nid=%s\n' % (results_json["AccessAuthId"])
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				data0 = json.loads(data)
				if data0['AccessAuthId'] == 0:
					system_log(usercode,"创建访问授权：%s" % data0['AccessAuthName'],"任务下发失败","运维管理>访问授权")
				else:
					#data1 = json.loads(prv_data)
					#cmp(data0,data1)
					#if t != 0:
					system_log(usercode,"编辑访问授权：%s" % data0['AccessAuthName'],"任务下发失败","运维管理>访问授权")
				return "{\"Result\":false,\"ErrMsg\":\"扫描任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
			debug('2')
			get_data = '{"loginusercode":"'+usercode+'","accessauthid":'+str(results_json["AccessAuthId"])+',"limitrow":null,"offsetrow":null}'
			get_data = "E'%s'" % MySQLdb.escape_string(get_data).decode("utf-8")
			curs.execute("select public.\"PGetAccessAuth\"(%s);"%(get_data))
			debug('3')
			re_data = curs.fetchall()[0][0].encode('utf-8')
			debug(str(re_data))
			re_data = json.loads(re_data)
			if len(re_data['data']) == 0:
				data0 = json.loads(data)
				sql = "select \"UserCode\" from public.\"User\" where \"UserId\"=%d" % data0['AdminSet'][0]['AdminId']
				curs.execute(sql)
				UserCode = curs.fetchall()[0][0].encode('utf-8')
				get_data = '{"loginusercode":"'+UserCode+'","accessauthid":'+str(results_json["AccessAuthId"])+',"limitrow":null,"offsetrow":null}'
				get_data = "'%s'" % get_data
				debug('4')
				curs.execute("select public.\"PGetAccessAuth\"(%s);"%(get_data))
				debug('5')
				re_data = curs.fetchall()[0][0].encode('utf-8')
				re_data = json.loads(re_data)
			_obj = ""
			if re_data['data'][0]["AuthMode"] == 1:
				_obj = "方式：对象指定"
			elif re_data['data'][0]["AuthMode"] == 2:
				_obj = "方式：范围指定（共有）"
			elif re_data['data'][0]["AuthMode"] == 3:
				_obj = "方式：范围指定（所有）"
			else:
				_obj = "方式：范围指定（自定义）"
			
			scopename = ""
			if re_data['data'][0]['AuthScope'] != None and len(re_data['data'][0]['AuthScope']) != 0:
				flag_u = 0
				for scope in re_data['data'][0]['AuthScope']:
					if flag_u >= 1000:
						break
					scopename = scopename + scope['ServerScopeName'] + ','
					flag_u += 1
				scopename = scopename[:-1]
			
			auth_obj = []
			if re_data['data'][0]['AuthObject'] != None and len(re_data['data'][0]['AuthObject']) != 0:
				auth_hg = ""
				auth_host = ""
				auth_account = ""
				flag_h = 0
				for authobj in re_data['data'][0]['AuthObject']:
					if flag_h >= 1000:
						break
					if authobj['AccountName'] != None:
						auth_account = auth_account + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + '-' + authobj['AccountName'] + ','
					elif authobj['HostName'] != None:
						auth_host = auth_host + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + ','
					else:
						auth_hg = auth_hg + '[' + authobj['HGName'] + '],'
					flag_h += 1
				
				
				if auth_hg != "":
					auth_hg = "指定主机组：" + auth_hg[:-1]
					auth_obj.append(auth_hg)
				if auth_host != "":
					auth_host = "指定主机：" + auth_host[:-1]
					auth_obj.append(auth_host)
				if auth_account != "":
					auth_account = "指定账号：" + auth_account[:-1]
					auth_obj.append(auth_account)
			auth_obj_str = ','.join(auth_obj)
			if scopename != "":
				_obj = _obj + ',' + "服务器范围：" + scopename
				
			if auth_obj_str != "":
				_obj = _obj + ',' + auth_obj_str
				
			if re_data['data'][0]['Enabled'] == True:
				_obj = _obj + ',' + "启用"
			else:
				_obj = _obj + ',' + "停用"
			
			if re_data['data'][0]['AdminSet'] != None and len(re_data['data'][0]['AdminSet']) != 0:
				admin_str = ""
				for admin in re_data['data'][0]['AdminSet']:
					admin_str = admin_str + admin['UserCode'] + ','
				if admin_str != "":
					admin_str = "管理者：" + admin_str[:-1]

				_obj = _obj + ',' + admin_str
			
			if re_data['data'][0]['AuthUserSet'] != None and len(re_data['data'][0]['AuthUserSet']) != 0:
				user_str = ""
				userhg_str = ""
				for user in re_data['data'][0]['AuthUserSet']:
					if user['Type'] == 1:
						user_str = user_str + user['Name'] + ','
					else:
						userhg_str = userhg_str + user['Name'] + ','
				if user_str != "":
					user_str = "授权用户：" + user_str[:-1]
					_obj = _obj + ',' + user_str
				if userhg_str != "":
					userhg_str = "授权用户组：" + userhg_str[:-1]
					_obj = _obj + ',' + userhg_str
			
			if re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName'].find('#') != -1:
				_obj = _obj + ",权限配置：#私有"
				strategyname = "#私有"
			else:
				_obj = _obj + ",权限配置：" + re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName']
				strategyname = re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName']
		
			#权限配置日志
			sql = "select public.\"PGetAccessStrategy\"(%d,null,null,1,null,null)" % re_data['data'][0]['AccessStrategyInfo']['AccessStrategyId']
			curs.execute(sql)
			strategy = curs.fetchall()[0][0].encode('utf-8')
			strategy = json.loads(strategy)
			
			log_array = [];
			if strategy['data'][0]['EnableApprove']:
				log_array.append("登录审批："+strategy['data'][0]['ApproveStrategyName'])
			if strategy['data'][0]['EnableDoubleCollaboration']:
				log_array.append("协同登录")
			if strategy['data'][0]['EnableAccessInfo']:
				log_array.append("访问备注")
			if strategy['data'][0]['EnableWorkOrderApprove']:
				log_array.append("工单审批："+strategy['data'][0]['WorkOrderApproveStrategyName'])
			if strategy['data'][0]['EnableAlarm']:
				log_array.append("登录告警："+strategy['data'][0]['EventAlarmInfoName'])
			
			RDP_flag = 0
			if strategy['data'][0]['EnableRDPClipboard'] == 1:
				log_array.append("RDP传输控制：剪贴板上传")
			elif strategy['data'][0]['EnableRDPClipboard'] == 2:
				log_array.append("RDP传输控制：剪贴板下载")
			elif strategy['data'][0]['EnableRDPClipboard'] == 3:
				log_array.append("RDP传输控制：剪贴板上传?*下载")
			else:
				RDP_flag = 1
			if strategy['data'][0]['EnableRDPFileRecord']:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：文件记录")
				else:
					log_array.append("文件记录")
			'''
			if strategy['data'][0]['EnableRDPDiskMap']:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：磁盘映射")
				else:
					log_array.append("磁盘映射")
			'''	
			
			if strategy['data'][0]['EnableRDPDiskMap'] == 1:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：磁盘上行")
				else:
					log_array.append("磁盘上行")
			elif strategy['data'][0]['EnableRDPDiskMap'] == 2:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：磁盘下行")
				else:
					log_array.append("磁盘下行")
			elif strategy['data'][0]['EnableRDPDiskMap'] == 3:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：磁盘上行?*下行")
				else:
					log_array.append("磁盘上行?*下行")
			else:
				pass
					
			if strategy['data'][0]['EnableRDPKeyRecord']:
				if RDP_flag == 1:
					log_array.append("RDP传输控制：键盘记录")
				else:
					log_array.append("键盘记录")
			
			SSH_flag = 0
			if strategy['data'][0]['EnableSSHFileTrans'] == 1:
				log_array.append("SSH传输控制：文件上传")
			elif strategy['data'][0]['EnableSSHFileTrans'] == 2:
				log_array.append("SSH传输控制：文件下载")
			elif strategy['data'][0]['EnableSSHFileTrans'] == 3:
				log_array.append("SSH传输控制：文件上传?*下载")
			else:
				SSH_flag = 1

			if strategy['data'][0]['EnableSSHFileRecord']:
				if SSH_flag == 1:
					log_array.append("SSH传输控制：文件记录")
				else:
					log_array.append("文件记录")
			FTP_flag = 0
			if strategy['data'][0]['EnableFTPFileTrans'] == 1:
				log_array.append("FTP传输控制：文件上传")
			elif strategy['data'][0]['EnableFTPFileTrans'] == 2:
				log_array.append("FTP传输控制：文件下载")
			elif strategy['data'][0]['EnableFTPFileTrans'] == 3:
				log_array.append("FTP传输控制：文件上传?*下载")
			else:
				FTP_flag = 1
			if strategy['data'][0]['EnableFTPFileRecord']:
				if FTP_flag == 1:
					log_array.append("FTP传输控制：文件记录")
				else:
					log_array.append("文件记录")
			#
			if strategy['data'][0]['TimeAction'] == 1:
				TimeAction = "允许"
			elif strategy['data'][0]['TimeAction'] == 2:
				TimeAction = "例外"
			else:
				TimeAction = "不限制"
			
			if strategy['data'][0]['ClientScopeAction'] == 1:
				ClientScopeAction = "允许"
			elif strategy['data'][0]['ClientScopeAction'] == 2:
				ClientScopeAction = "例外"
			else:
				ClientScopeAction = "不限制"
			timerange = ""
			
			if strategy['data'][0]['TimeConfig'] != None and len(strategy['data'][0]['TimeConfig']) != 0:
				if strategy['data'][0]['TimeConfig'][0]['Set'] != None and len(strategy['data'][0]['TimeConfig'][0]['Set']) != 0:#自定义
					taskday_time = ""
					taskparent_time = ""
					Section_time = ""
					everyday = ""
					everyweek = ""
					everymonth = ""
					for timeset in strategy['data'][0]['TimeConfig'][0]['Set']:
						if timeset['TimeSetType'] == 32:#任务当天
							if timeset['StartDate'].find('T') != -1:
								StartDate = timeset['StartDate'].split('T')[0]
							if timeset['EndDate'].find('T') != -1:
								EndDate = timeset['EndDate'].split('T')[0]
							taskday_time = taskday_time + StartDate + ' ' + timeset['StartTime'] + '-'+EndDate + ' ' + timeset['EndTime'] + '?*'
						elif timeset['TimeSetType'] == 31:#任务当前
							if timeset['StartDate'].find('T') != -1:
								StartDate = timeset['StartDate'].split('T')[0]
							if timeset['EndDate'].find('T') != -1:
								EndDate = timeset['EndDate'].split('T')[0]
							taskparent_time = taskparent_time + StartDate + ' ' + timeset['StartTime'] + '-' + EndDate + ' ' + timeset['EndTime'] + '?*'
						elif timeset['TimeSetType'] == 20:#区间
							if timeset['StartDate'].find('T') != -1:
								StartDate = timeset['StartDate'].split('T')[0]
							if timeset['EndDate'].find('T') != -1:
								EndDate = timeset['EndDate'].split('T')[0]
							Section_time = Section_time + StartDate + ' ' + timeset['StartTime'] + '-' + EndDate + ' ' + timeset['EndTime'] + '?*'
						elif timeset['TimeSetType'] == 13:#周期每月
							everymonth = everymonth + str(timeset['StartPeriod']) + '日-' + timeset['StartTime'] + '至' + str(timeset['EndPeriod']) + '日-' + timeset['EndTime'] + '?*'
						elif timeset['TimeSetType'] == 12:#周期每周
							everyweek = everyweek + '周' + str(timeset['StartPeriod']) + ' ' + timeset['StartTime'] + '至周' + str(timeset['EndPeriod']) + ' ' + timeset['EndTime'] + '?*'
						elif timeset['TimeSetType'] == 11:#周期每天
							everyday = everyday + timeset['StartTime'] + '-' + timeset['EndTime'] + '?*'
					if taskday_time != "":
						taskday_time = "任务当天：" + taskday_time[:-2]
						timerange = timerange + taskday_time + '?;'
					if taskparent_time != "":
						taskparent_time = "任务当前：" + taskparent_time[:-2]
						timerange = timerange + taskparent_time + '?;'
					if Section_time != "":
						Section_time = "区间：" + Section_time[:-2]
						timerange = timerange + Section_time + '?;'
					if everyday != "":
						everyday = "周期每天：" + everyday[:-2]
						timerange = timerange + everyday + '?;'
					if everyweek != "":
						everyweek = "周期每周：" + everyweek[:-2]
						timerange = timerange + everyweek + '?;'
					if everymonth != "":
						everymonth = "周期每月：" + everymonth[:-2]
						timerange = timerange + everymonth + '?;'
				else:
					time_str = ""
					for timegather in strategy['data'][0]['TimeConfig']:
						time_str = time_str + timegather['TimeSetName'] + '?*'
					if time_str != "":
						timerange = timerange + "时间集合：" + time_str[:-2]
			clientrange = ""
			if strategy['data'][0]['ClientScopeConfig'] != None and len(strategy['data'][0]['ClientScopeConfig']) != 0:
				if strategy['data'][0]['ClientScopeConfig'][0]['IPList'] != None and strategy['data'][0]['ClientScopeConfig'][0]['IPList']['Set'] != None and len(strategy['data'][0]['ClientScopeConfig'][0]['IPList']['Set']) != 0:#自定义
					IPaddress = ""
					IPinterval = ""
					for client in strategy['data'][0]['ClientScopeConfig'][0]['IPList']['Set']:
						if client['StartIP'] == client['EndIP']:
							IPaddress = IPaddress + client['StartIP'] + '?*'
						else:
							IPinterval = IPinterval + client['StartIP'] + '-' + client['EndIP'] + '?*'
					if IPaddress != "":
						clientrange = clientrange + 'IP地址：' + IPaddress[:-2] + '?*'
					if IPinterval != "":
						clientrange = clientrange + 'IP区间：' + IPinterval[:-2] + '?*'
				if strategy['data'][0]['ClientScopeConfig'][0]['MACList'] != None and strategy['data'][0]['ClientScopeConfig'][0]['MACList']['Set'] != None and len(strategy['data'][0]['ClientScopeConfig'][0]['MACList']['Set']) != 0:#自定义
					MACaddress = ""
					MACinterval = ""
					for client in strategy['data'][0]['ClientScopeConfig'][0]['MACList']['Set']:
						if client['StartMACAddress'] == client['EndMACAddress']:
							MACaddress = MACaddress + client['StartMACAddress'] + '?*'
						else:
							MACinterval = MACinterval + client['StartMACAddress'] + '-' + client['EndMACAddress'] + '?*'
					if MACaddress != "":
						clientrange = clientrange + 'MAC地址：' + MACaddress[:-2] + '?*'
					if MACinterval != "":
						clientrange = clientrange + 'MAC区间：' + MACinterval[:-2] + '?*'
				if strategy['data'][0]['ClientScopeConfig'][0]['ClientScopeName']!= None:
					client_str = ""
					for clientset in strategy['data'][0]['ClientScopeConfig']:
						client_str = client_str + clientset['ClientScopeName'] + '?*'
					if client_str != "":
						clientrange = clientrange + "客户端集合：" + client_str[:-2]
			
			strategy_str = ""
			
			strategy_str = strategy_str + "时间生效范围：" + TimeAction
			if timerange != "":
				#timerange = timerange[:-1]
				strategy_str = strategy_str + '（'+ timerange + '）,'
			else:
				strategy_str = strategy_str + ','
			strategy_str = strategy_str + "客户端地址限制：" + ClientScopeAction
			if clientrange != "":
				#clientrange = clientrange[:-1]
				strategy_str = strategy_str + '（' + clientrange + '）,'
			else:
				strategy_str = strategy_str + ','
			strategy_str = strategy_str[:-1]
			#debug("strategy_str:%s" % strategy_str)
			log_array.append(strategy_str)
			strategy_str = ','.join(log_array)
			strategy_str = strategy_str.replace("?*","、").replace("?;","；").replace(",","，")
			data0 = json.loads(data)
			
			if data0['AccessStrategyInfo']['AccessStrategyId'] == 0:
				system_log(usercode,"创建权限配置：%s（%s）" % (strategyname,strategy_str),"成功","运维管理>访问授权")
			else:
				system_log(usercode,"编辑权限配置：%s（%s）" % (strategyname,strategy_str),"成功","运维管理>访问授权")
			if data0['AccessAuthId'] == 0:
				system_log(usercode,"创建访问授权：%s（%s）" % (data0['AccessAuthName'],_obj),"成功","运维管理>访问授权")
			else:
				#data1 = json.loads(prv_data)
				#cmp(data0,data1)
				#if t != 0:
				system_log(usercode,"编辑访问授权：%s（%s）" % (data0['AccessAuthName'],_obj),"成功","运维管理>访问授权")
					
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/delete_AccessStrategy',methods=['GET','POST'])
def delete_AccessStrategy():
	session = request.form.get('a0')
	id = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"AccessStrategyName\" from public.\"AccessStrategy\" where \"AccessStrategyId\"=%d" % int(id)
			curs.execute(sql)
			strategyname = curs.fetchall()[0][0].encode('utf-8')
			
			#debug("select public.\"PDeleteAccessStrategy\"(%d);"%(int(id)))
			curs.execute("select public.\"PDeleteAccessStrategy\"(%d);"%(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			re_del = json.loads(results)
			if re_del['Result']:
				system_log(usercode,"删除权限配置：%s" % strategyname,"成功","运维管理>权限配置")
			else:
				system_log(usercode,"删除权限配置：%s" % strategyname,"失败","运维管理>权限配置")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_authname',methods=['GET','POST'])
def get_authname():
	session = request.form.get('a0')
	name = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetAccessAuthByName\"('%s');"%(name))
			if checkaccount(name) == False:
				return '',403
			curs.execute("select public.\"PGetAccessAuthByName\"(E'%s');"%(name))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/get_AccessAuth_all',methods=['GET', 'POST'])
def get_AccessAuth_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetAccessAuth\"(E'%s',null,null,null,null,null);"%(usercode))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/check_ServerScopeName',methods=['GET', 'POST'])
def check_ServerScopeName():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	name = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetServerScopeByName\"(E'%s');"%(name))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@access_auth_z.route('/Pind_UserDirectory',methods=['GET', 'POST'])
def Pind_UserDirectory():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	filter = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	filter = json.loads(filter)
	
	filter_name = ""
	filter_code = ""
	filter_all = ""
	if len(filter) != 0:
		for i in filter:
			filter_arry = i.split('-')
			if filter_arry[0] == "组名":
				filter_name = filter_name + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "账号":
				filter_code = filter_code + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "所有":
				filter_all = filter_all + MySQLdb.escape_string(filter_arry[1]) + '\n'
	if filter_name == "":
		filter_name = 'null'
	else:
		filter_name = filter_name[:-1]
		filter_name = MySQLdb.escape_string(filter_name).decode('utf-8')
		#debug("filter_name1:%s" % filter_name)
		filter_name=filter_name.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_name = '"%s"' % filter_name
	if filter_code == "":
		filter_code = 'null'
	else:
		filter_code = filter_code[:-1]
		filter_code = MySQLdb.escape_string(filter_code).decode('utf-8')
		filter_code = filter_code.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_code = '"%s"' % filter_code
	if filter_all == "":
		filter_all = 'null'
	else:
		filter_all = filter_all[:-1]
		filter_all = MySQLdb.escape_string(filter_all).decode('utf-8')
		filter_all = filter_all.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_all = '"%s"' % filter_all
	data='{"ugid":0,"istree":true,"ugname":'+filter_name+',"usercode":'+filter_code+',"userstatus":null, "mobilephone":null,"department":null,"description":null,"rolename":null, "adminusercode":null,"searchstring":'+filter_all+',"limitrow":null,"offsetrow":null}'
	data = "E'%s'" % data
	#debug("data:%s" % data)
	'''
	filter_v = ""
	if len(filter) != 0:
		for i in filter:
			i=i.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
			filter_v = filter_v + i + '\\n'
	if filter_v == "":
		filter_v = 'null'
	else:
		filter_v = filter_v[:-2]
		filter_v = MySQLdb.escape_string(filter_v).decode('utf-8')
		#filter_v=filter_v.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
		filter_v = '"%s"' % filter_v
	data='{"ugid":0,"istree":true,"ugname":null,"usercode":null,"userstatus":null, "mobilephone":null,"department":null,"description":null,"rolename":null, "adminusercode":null,"searchstring":'+filter_v+',"limitrow":null,"offsetrow":null}'
	data = "'%s'" % data
	'''
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			#curs = conn.cursor()
			#debug("select public.\"PFindUserDirectory\"(%s);"%(data))
			curs.execute("select public.\"PFindUserDirectory\"(%s);"%(data))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/PFindHostDirectory_z',methods=['GET', 'POST'])
def PFindHostDirectory_z():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	filter = request.form.get('z1')
	##++
	_type=request.form.get('z2')
	_id=request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	filter = json.loads(filter)
	filter_hgname = ""
	filter_hname = ""
	filter_ip = ""
	filter_ser = ""
	filter_account = ""
	filter_all = ""
	if len(filter) != 0:
		for i in filter:
			filter_arry = i.split('-')
			if filter_arry[0] == "所有":
				filter_all = filter_all + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "组名":
				filter_hgname = filter_hgname + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "主机名":
				filter_hname = filter_hname + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "IP":
				filter_ip = filter_ip + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "服务":
				filter_ser = filter_ser + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "账号":
				filter_account = filter_account + MySQLdb.escape_string(filter_arry[1]) + '\n'
	if filter_all == "":
		filter_all = 'null'
	else:
		filter_all = filter_all[:-1]
		filter_all = MySQLdb.escape_string(filter_all).decode('utf-8')
		filter_all=filter_all.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_all = '"%s"' % filter_all

	if filter_hgname == "":
		filter_hgname = 'null'
	else:
		filter_hgname = filter_hgname[:-1]
		filter_hgname = MySQLdb.escape_string(filter_hgname).decode('utf-8')
		filter_hgname = filter_hgname.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_hgname = '"%s"' % filter_hgname

	if filter_hname == "":
		filter_hname = 'null'
	else:
		filter_hname = filter_hname[:-1]
		filter_hname = MySQLdb.escape_string(filter_hname).decode('utf-8')
		filter_hname = filter_hname.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_hname = '"%s"' % filter_hname		
	
	if filter_ip == "":
		filter_ip = 'null'
	else:
		filter_ip = filter_ip[:-1]
		filter_ip = MySQLdb.escape_string(filter_ip).decode('utf-8')
		filter_ip = filter_ip.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_ip = '"%s"' % filter_ip	
	
	if filter_ser == "":
		filter_ser = 'null'
	else:
		filter_ser = filter_ser[:-1]
		filter_ser = MySQLdb.escape_string(filter_ser).decode('utf-8')
		filter_ser = filter_ser.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_ser = '"%s"' % filter_ser	
	
	if filter_account == "":
		filter_account = 'null'
	else:
		filter_account = filter_account[:-1]
		filter_account = MySQLdb.escape_string(filter_account).decode('utf-8')
		filter_account = filter_account.replace("\\","\\\\").replace(".","\\\\\\\\.").replace("?","\\\\\\\\?").replace("+","\\\\\\\\+").replace("(","\\\\\\\\(").replace(")","\\\\\\\\)").replace("*","\\\\\\\\*").replace("[","\\\\\\\\[").replace("]","\\\\\\\\]")
		filter_account = '"%s"' % filter_account
	'''
	filter_v = ""
	if len(filter) != 0:
		for i in filter:
			i=i.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
			filter_v = filter_v + i + '\\n'
	usercode = '"%s"' % usercode
	if filter_v == "":
		filter_v = 'null'
	else:
		filter_v = filter_v[:-2]
		filter_v = MySQLdb.escape_string(filter_v).decode('utf-8')
		filter_v = '"%s"' % filter_v
	'''
	data = '{"type":'+_type+',"id":'+_id+',"loginusercode":"'+usercode+'","hgid":0,"istree":true,"hgname":'+filter_hgname+',"hostname":'+filter_hname+', "hostip":'+filter_ip+',"devicetypename":null,"accountname":'+filter_account+',"hostservicename":'+filter_ser+',"protocolname":null,"searchstring":'+filter_all+',"limitrow":null,"offsetrow":null}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PFindHostDirectory\"('%s');"%(MySQLdb.escape_string(data).decode('utf-8')))
			curs.execute("select public.\"PFindHostDirectory\"(E'%s');"%(data))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/IsSScopeDisplay',methods=['GET', 'POST'])
def IsSScopeDisplay():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	s_id = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"IsSScopeDisplay\"('%s',%s);"%(usercode,s_id))
			curs.execute("select public.\"IsSScopeDisplay\"(E'%s',%s);"%(usercode,s_id))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
"""
###获取 用户组 用户组 的选中状态
@access_auth_z.route('/PGetUNodeSelected',methods=['GET','POST'])
def PGetUNodeSelected():
	try:
		session = request.form.get('a0')
		json = request.form.get('z1')
		client_ip = request.remote_addr
		json=str(json)
		(error,usercode,mac) = SessionCheck(session,client_ip);
		if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
						
		'''
		SELECT public."PGetUNodeSelected"(json) 
		'''
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()		
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		#       
		try:
			sql = "SELECT public.\"PGetUNodeSelected\"('%s') " %(json)
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0]
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":%s}" % (results)
	except:
		return 0
"""
@access_auth_z.route('/IsAllowToManageAuth',methods=['GET','POST'])
def IsAllowToManageAuth():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	userid = request.form.get('a1')
	loginuserid = request.form.get('a2')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"IsAllowToManageAuth\"(%d,%d);" %(int(userid), int(loginuserid)))
			curs.execute("select public.\"IsAllowToManageAuth\"(%d,%d);" %(int(userid), int(loginuserid)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@access_auth_z.route('/PUpdateHNodeSelectedForQuick',methods=['GET', 'POST'])
def PUpdateHNodeSelectedForQuick():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	s_id = request.form.get('z1')
	s_type = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"IsSScopeDisplay\"('%s',%s);"%(usercode,s_id))
			curs.execute("select public.\"PUpdateHNodeSelectedForQuick\"(%s,%s);"%(s_type,s_id))
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@access_auth_z.route('/PUpdateUNodeSelectedForQuick',methods=['GET', 'POST'])
def PUpdateUNodeSelectedForQuick():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	s_id = request.form.get('z1')
	s_type = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"IsSScopeDisplay\"('%s',%s);"%(usercode,s_id))
			curs.execute("select public.\"PUpdateUNodeSelectedForQuick\"(%s,%s);"%(s_type,s_id))
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))



