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

import htmlencode
from generating_log import system_log
from logbase import common
from comm import CertGet
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionCheckLocal
from comm import LogSet
from logbase import common
from index import PGetPermissions

from flask import Flask,Blueprint,request,session,render_template 
from jinja2 import Environment,FileSystemLoader

from logbase import common
from logbase import defines
from logbase import task_client
from htmlencode import parse_sess,check_role
find_host = Blueprint('find_host',__name__)
env = Environment(loader = FileSystemLoader('templates'))

def debug(c):
	return 0
        path = "/var/tmp/debuglh.txt"
        fp = open(path,"a+")
        if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
#HTMLEncode 
def HTMLEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr
	
#error encode
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"',"'").replace('\n',"\\n")
	return newStr

@find_host.route('/f_host_show',methods=['GET', 'POST'])
def f_host_show():
		tasktype = request.form.get("tasktype")
		session = request.form.get('a0')
		if session < 0 or session == '':
			session = request.form.get('se')
			if session < 0:
				session = ""
		client_ip = request.remote_addr
		(error,system_user,mac) = SessionCheck(session,client_ip)
		if error < 0:
			return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+806,error)
			sys.exit()
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+807,error)
			else:
				return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+808,error)
				
		if tasktype < 0 or tasktype == None:
			tasktype = "1"
		if tasktype == "1":
			t = "find_host.html"
		_power=PGetPermissions(system_user)
		_power_json = json.loads(str(_power));
		_power_mode = 1;
		for one in _power_json:
			if one['SubMenuId'] == 14:
				_power_mode = one['Mode']	
			
		return render_template(t,tasktype = tasktype,se = session,_power_mode=_power_mode)

#取保存扫描任务
@find_host.route('/get_hostscan_task', methods=['GET', 'POST'])
def get_hostscan_task():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheckLocal(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PGetHostScanTask\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results	

#保存扫描任务
@find_host.route('/save_hostscan_task', methods=['GET', 'POST'])
def save_hostscan_task():
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	jsondata = request.form.get('a1')
	jsondata_tmp = json.loads(jsondata)
	networkSeg = request.form.get('a2')
	port = request.form.get('a3')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	data = str(jsondata)
	sql = "select public.\"PSaveHostScanTask\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	debug(sql)

	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	debug(results)
	result = ret["Result"]

	Server_arry = []
	if jsondata_tmp['DeviceServiceId'] == "":
			Server_arry = ['所有服务']
	else:
		DeviceServiceId_arry = str(jsondata_tmp['DeviceServiceId']).split(',')
		for i in DeviceServiceId_arry:
			sql = 'select "DeviceService"."DeviceServiceName","DeviceService"."Port" from "DeviceService" where "DeviceService"."DeviceServiceId" = %d;' % int(i)
			curs.execute(sql)
			results_1 = curs.fetchall()
			Name_str = str(results_1[0][0])+'('+str(results_1[0][1])+')'
			Server_arry.append(Name_str)

	NetWorkSeg_arry = str(jsondata_tmp['NetWorkSeg']).split(',')

	ContentStr = "任务名称："+jsondata_tmp['TaskName']+"，检测网段："+'、'.join(NetWorkSeg_arry)+"，检测服务："+'、'.join(Server_arry)

	if(result == True):
		hst_id = ret["HostScanTaskId"]
		networkSeg = "%s" %(networkSeg)
		port = "%s" %(port)
		#debug(hst_id)
		##[global]
		#class=taskhostscan
		#type=hostscan_run
		#HostScanTaskId=hst_id
		#ipstr=networkSeg
		#port=port
		task_content = '[global]\nclass = taskhostscan\ntype = hostscan_run\nHostScanTaskId=%s\nipstr=%s\nports=%s\n' % (hst_id,networkSeg,port)
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
		debug(task_content)	
		conn.commit()
		if jsondata_tmp['HostScanTaskId'] == 0:
			system_log(system_user,"创建发现主机任务：%s (%s)" % (jsondata_tmp['TaskName'],ContentStr),"成功","运维管理>发现主机")
		else:
			system_log(system_user,"编辑发现主机任务：%s (%s)" % (jsondata_tmp['TaskName'],ContentStr),"成功","运维管理>发现主机")
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":%d}" %hst_id
	else:
		if jsondata_tmp['HostScanTaskId'] == 0:
			system_log(system_user,"创建发现主机任务：%s (%s)" % (jsondata_tmp['TaskName'],ContentStr),"失败："+ret['ErrMsg'],"运维管理>发现主机")
		else:
			system_log(system_user,"编辑发现主机任务：%s (%s)" % (jsondata_tmp['TaskName'],ContentStr),"失败："+ret['ErrMsg'],"运维管理>发现主机")	
		curs.close()
		conn.close()
		return results

#删除任务
@find_host.route('/del_hostscan_task', methods=['GET', 'POST'])
def del_hostscan_task():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(system_user,'主机管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	TaskName = []
	for id in ids:
		id = int(id)
		get_data = '{"hostscantaskid":'+str(id)+',"taskname":null,"networkseg":null,"starttime":null,"endtime":null,"limitrow":1,"offsetrow":0}'
		get_data = "E'%s'" % get_data
		curs.execute("select public.\"PGetHostScanTask\"(%s);" %(get_data))
		result_1 = curs.fetchall()[0][0]
		result_1 = json.loads(result_1)
		TaskName.append(str(result_1['data'][0]['TaskName']))

		sql = "select public.\"PDeleteHostScanTask\"(%d);" %(id)
		# debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		result = curs.fetchall()[0][0].encode('utf-8')
		ret = json.loads(result)
		if "false" in result:
			system_log(system_user,"删除发现主机任务：%s" % str(result_1['data'][0]['TaskName']),"失败："+ret['ErrMsg'],"运维管理>发现主机")
			curs.close()
			conn.close()
			return result
	conn.commit()
	system_log(system_user,"删除发现主机任务：%s" % ('、'.join(TaskName)),"成功","运维管理>发现主机")
	curs.close()
	conn.close()
	return result

#停止任务
@find_host.route('/stop_hostscan_task', methods=['GET', 'POST'])
def stop_hostscan_task():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	if session < 0:
		session = "" 
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	for id in ids:
		#debug(hst_id)
		##[global]
		#class=taskhostscan
		#type=hostscan_del
		#HostScanTaskId=id
		task_content = '[global]\nclass = taskhostscan\ntype = hostscan_del\nHostScanTaskId=%s\n' % (id)
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
		debug(task_content)
	return "{\"Result\":true}"

#改变扫描任务状态
@find_host.route('/save_hostscan_task_s', methods=['GET','POST'])
def save_hostscan_task_s():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	md5_str = request.form.get('m1')
	jsondata_tmp = json.loads(jsondata)
	data = str(jsondata)
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PSaveHostScanTask\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno) 
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]
	if(result == True):
		conn.commit()
		system_log(system_user,"停止发现主机任务：%s" % (jsondata_tmp['TaskName']),"成功","运维管理>发现主机")
		curs.close()
		conn.close()
		return results
	else:
		system_log(system_user,"停止发现主机任务：%s" % (jsondata_tmp['TaskName']),"失败："+ret['ErrMsg'],"运维管理>发现主机")
		curs.close()
		conn.close()
		return results

#取扫描任务结果
@find_host.route('/get_hostscan_result', methods=['GET', 'POST'])
def get_hostscan_result():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PGetHostScanResult\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno) 
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results	

#保存结果
@find_host.route('/add_host', methods=['GET', 'POST'])
def add_host():
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	jsondata = request.form.get('a1')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	host_json = json.loads(jsondata)
	sql = "select public.\"PSaveHost\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	debug(sql)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	#判断 是否 超过 托管上限
	server_id=common.get_server_id();
	try:
		crt_t = CertGet(int(server_id))
	except Exception,e:
		crt_t = None

	max_count = 0
	if crt_t != None:
		max_count = crt_t[7]
	else:
		max_count = 0

	sql1 = "select count(*) from public.\"Host\";"

	curs.execute(sql1)
	OperationalHosts = int(curs.fetchall()[0][0])

	if int(max_count) <= OperationalHosts:
		results = '{"Result":false,"ErrMsg":"主机数量已达到托管上限"}'
		ret = json.loads(results)
		result = ret["Result"]		
	else:
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		ret = json.loads(results)
		result = ret["Result"]

	#send system log
	sql = "select \"DeviceTypeName\" from public.\"DeviceType\" where \"DeviceTypeId\"=%d" % int(host_json['DeviceTypeId'])
	debug(sql)
	curs.execute(sql)
	DeviceTypeName_tmp = curs.fetchall()[0][0]

	if host_json['ServiceSet'] == []:
		Service_str = "无"
	else:
		HostService_array = []
		for i in host_json['ServiceSet']:
			host_array_tmp = {"HostServiceName":"SSH1","Protocol":"SSH","Port":"21","Account":[]}
			host_array_tmp['HostServiceName'] = i['HostServiceName']
			host_array_tmp['Protocol'] = i['HostServiceName']
			host_array_tmp['Port'] = i['Port']
			AccountName_array = []
			AccountName_array.append("*")
			host_array_tmp['Account'] = AccountName_array
			HostService_array.append(host_array_tmp)
		debug(str(HostService_array))
		Service_str = "服务："
		for i in HostService_array:
			if Service_str == "服务：":
				Service_str += str(i['HostServiceName'])+"(协议："+str(i['Protocol'])+"，端口："+str(i['Port'])+"，账号["+'、'.join(i['Account'])+"])"
			else:
				Service_str += "、"+str(i['HostServiceName'])+"(协议："+str(i['Protocol'])+"，端口："+str(i['Port'])+"，账号["+'、'.join(i['Account'])+"])"
	debug(Service_str)
	AccessRate = ''
	if int(host_json['AccessRate']) == 1:
		AccessRate = '正常'
	elif int(host_json['AccessRate']) == 2:
		AccessRate = '较慢'
	elif int(host_json['AccessRate']) == 3:
		AccessRate = '很慢'

	# Status = '启用'
	# if int(host_json['Status']) == 2:
	# 	Status = '停用'

	EnableLoginLimit = '是'
	if host_json['EnableLoginLimit'] == False:
		EnableLoginLimit = '否'

	HGroup_array = []
	if host_json['HGroupSet'] == []:
		host_json['HGroupSet'] = [{"HGId":1}]
	for i in host_json['HGroupSet']:
		id = i['HGId']
		path_arry = []
		sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % i['HGId']
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])

		while results_1[0][0] != 0:
			sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results_1[0][0]
			debug(sql)
			curs.execute(sql)
			results_1 = curs.fetchall()
			path_arry.insert(0,results_1[0][1])
		path_str = '/'+'/'.join(path_arry)

		HGroup_array.append(path_str)

	ContentStr = "主机IP："+host_json['HostIP']+", 设备类型："+DeviceTypeName_tmp+", 访问速度："+AccessRate+", 是否唯一登陆："+EnableLoginLimit+", "+Service_str+", 主机组："+'、'.join(HGroup_array)

	if(result == True):
		conn.commit()
		system_log(system_user,"创建主机：%s (%s)" % (host_json['HostName'],ContentStr),"成功","运维管理>发现主机")
		curs.close()
		conn.close()
		return results
	else:
		system_log(system_user,"创建主机：%s (%s)" % (host_json['HostName'],ContentStr),"失败："+ret['ErrMsg'],"运维管理>发现主机")
		curs.close()
		conn.close()
		return results

#主机PING测试
@find_host.route('/ping_test', methods=['GET', 'POST'])
def ping_test():
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	ip = request.form.get('a1')
	f = os.popen("ping -c 4 "+ip)
	result = f.read()
	return "{\"ip\":\"%s\",\"result\":\"%s\"}" %(ip,result)

#保存前置机IP
@find_host.route('/save_acc_ip', methods=['GET','POST'])
def save_acc_ip():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	FromFlag = request.form.get('a10')
	md5_str = request.form.get('m1')
	jsondata_tmp = json.loads(jsondata)
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select public.\"PSaveAccIP\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]
	if(result == True):
		conn.commit()
		system_log(system_user,"创建前置机IP：%s" % (str(jsondata_tmp['AccIP'])),"成功",FromFlag)
		curs.close()
		conn.close()
		return results
	else:
		system_log(system_user,"创建前置机IP：%s" % (str(jsondata_tmp['AccIP'])),"失败："+ret['ErrMsg'],FromFlag)
		curs.close()
		conn.close()
		return results

#删除前置机IP
@find_host.route('/del_acc_ip', methods=['GET','POST'])
def del_acc_ip():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 60000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ip_id = request.form.get('a1')
	FromFlag = request.form.get('a10')
	ip_id = int(ip_id)
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if FromFlag.find('主机') >= 0:
		module_role = "主机管理"
	else:
		module_role = "32"
	if check_role(system_user, module_role) == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	

	debug('select "AccIP" from "AccIP" where "AccIPId" = %d;' % ip_id)
	curs.execute('select "AccIP" from "AccIP" where "AccIPId" = %d;' % ip_id)
	debug("ssssssssssssss")
	result_1 = curs.fetchall()[0][0]
	debug(str(result_1))

	sql = "select public.\"PDeleteAccIP\"(%d);" %(ip_id)
	# debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')
	if "false" in result:
		ret = json.loads(result)
		system_log(system_user,"删除前置机IP：%s" % (str(result_1)),"失败："+ret['ErrMsg'],FromFlag)
		curs.close()
		conn.close()
		return result
	conn.commit()
	system_log(system_user,"删除前置机IP：%s" % (str(result_1)),"成功",FromFlag)
	curs.close()
	conn.close()
	return result

#获取服务器ip  getdomain
@find_host.route('/getdomain', methods=['GET', 'POST'])
def getdomain():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	seserid = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	server_id=common.get_server_id()
	if int(server_id)==int(seserid):
		return "{\"Result\":true,\"ip\":\"\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select public."PGetServerIPV4"(null,null,null,null,null,%s,null,null,true);'%(server_id)
			curs.execute(sql)
			result1 = curs.fetchall()[0][0]
			result1=json.loads(result1);
			if len(result1['data'])==0:
				return "{\"Result\":false,\"ErrMsg\":\"请先设置服务器%s的物理地址\"}"%(server_id)
			sql='select public."PGetServerIPV4"(null,null,null,null,null,%s,null,null,true);'%(seserid)
			curs.execute(sql)
			result2 = curs.fetchall()[0][0]
			result2=json.loads(result2);
			if len(result2['data'])==0:
				return "{\"Result\":false,\"ErrMsg\":\"请先设置服务器%s的物理地址\"}"%(seserid)
			for i in result2['data']:
				for j in result1['data']:
					if ipInSubnet('%s/%s'%(i['ip_addr'],i['mask_addr']),'%s/%s'%(j['ip_addr'],j['mask_addr'])):
						return "{\"Result\":true,\"ip\":\"%s\"}"%(i['ip_addr'])
		return "{\"Result\":false,\"ErrMsg\":\"非同网段，连接失败\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

##将IP地址转为二进制
def ipToBinary(ip):
	ip_num = ip.split('.')
	x = 0
	
	##IP地址是点分十进制，例如：192.168.1.33，共32bit
	##第1节（192）向前移24位，第2节（168）向前移16位
	##第3节（1）向迁移8位，第4节（33）不动
	##然后进行或运算，得出数据
	for i in range(len(ip_num)):
		num = int(ip_num[i]) << (24 - i*8)
		x = x | num

	brnary = str(bin(x).replace('0b',''))
	return brnary
	
##将子网掩码转为二进制
def maskToBinary(mask):
	mask_list = str(mask).split('.')
	binary = ipToBinary(mask)
	return binary

##判断IP地址是否属于这个网段 1.1.1.0/255.255.255.0
def ipInSubnet(subnet1,subnet2):
	subnet_list = subnet1.split('/')
	networt_add1 = subnet_list[0]
	network_mask1 = subnet_list[1]
	subnet_list = subnet2.split('/')
	networt_add2 = subnet_list[0]
	network_mask2 = subnet_list[1]
	##原来的得出的二进制数据类型是str，转换数据类型
	ip_num1 = int(ipToBinary(networt_add1),2)
	mask_bin1 = int(maskToBinary(network_mask1),2)
	ip_num2 = int(ipToBinary(networt_add2),2)
	mask_bin2 = int(maskToBinary(network_mask2),2)
	##IP和掩码与运算后比较
	if (ip_num1 & mask_bin1) == (ip_num2 & mask_bin2):
		return True
	else:
		return False

#取消息详情 for Msg cowork
@find_host.route('/getSesMsg', methods=['GET', 'POST'])
def getSesMsg():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select int32_01,int32_14,str32_22,ip_01,int16_01,int16_02,str32_00,str32_28,xtime_03,int32_15 from ses_table where xtime_03 = %s;" %(str(id_str))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno) 
	results = curs.fetchall()
	proto_list = proto_all();
	proto_list = json.loads(proto_list)['data']
	if proto_list == None:
		proto_list = []
	pro_l = []
	for proto in proto_list:
		pro_l.append([])
		pro_l[-1].append(proto['ProtocolId'])
		pro_l[-1].append(proto['ProtocolName'])
	for pro in pro_l:
		if pro[0] == results[0][0]:
			results[0][0] = pro[1];
	result_json = '{"int32_01":"'+str(results[0][0])+'","int32_14":"'+str(results[0][1])+'","str32_22":"'+str(results[0][2])+'","ip_01":"'+str(results[0][3])+'","int16_01":"'+str(results[0][4])+'","int16_02":"'+str(results[0][5])+'","str32_00":"'+str(results[0][6])+'","str32_28":"'+str(results[0][7])+'","xtime_03":"'+str(results[0][8])+'","int32_15":"'+str(results[0][9])+'"}'
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %result_json

def proto_all():
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
	#debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')
	
	curs.close()
	conn.close()
	return result

