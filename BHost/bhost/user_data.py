#!/usr/bin/env python
# encoding: utf-8
from __future__ import division
import os
import sys
import cgi
import cgitb
import re
import pyodbc
import MySQLdb
import json
import time
import htmlencode
from generating_log import system_log
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionCheckLocal
from comm import LogSet
from logbase import common
from logbase import task_client
from comm_function import get_user_perm_value
from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader 
from comm import CertGet
from comm import UsrSize
from comm import SysSize
from htmlencode import checkaccount
from comm import *
import redis
from logbase import defines;
from logbase import paths;

sys.path.append('/flash/system/bin')
from bhcomm import StrClas
import base64
import xml.etree.ElementTree as ET
import datetime
import ssl
import uuid
import httplib, urllib,urllib2
import hashlib
from ctypes import *
from comm import BlockProxy
from htmlencode import check_role
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
user_data = Blueprint('user_data',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000
def debug(c):
		return 0
		path = "/var/tmp/debugrxl.txt"
		fp = open(path,"a+")
		if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
def debug1(c):
		return 0
		path = "/var/tmp/debug111.txt"
		fp = open(path,"a+")
		if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
# def sendlog(oper,desc,cname):
	# client_ip = request.remote_addr    #获取客户端IP
	# happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	# sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	# LogSet(None, sqlconf, 6)
	
#HTMLEncode 
def HTMLEncode(str1):
	newStr = "";
	if str1 == "":
		return "";
	newStr = str1.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;
	
#ErrorEncode 
def ErrorEncode(str1):
	newStr = "";
	if str1 == "":
		return "";
	newStr = str1.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	


def readMemInfo():
	res = {'total':0, 'free':0, 'buffers':0, 'cached':0}
	f = open('/proc/meminfo')
	lines = f.readlines()
	f.close()
	i = 0
	for line in lines:
		if i == 4:
			break;
		line = line.lstrip()
		memItem = line.lower().split()
		if memItem[0] == 'memtotal:':
			res['total'] = long(memItem[1])
			i = i +1
		elif memItem[0] == 'memfree:':
			res['free'] = long(memItem[1])
			i = i +1
		elif memItem[0] == 'buffers:':
			res['buffers'] = long(memItem[1])
			i = i +1
		elif memItem[0] == 'cached:':
			res['cached'] = long(memItem[1])
			i = i +1
	return res

def GetNowTime():
	return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))

####格式检查
#账号
def checkaccount(account):
	p = re.compile(u'^[\w\.\-]+$')
	if p.match(account):
		return True
	else:
		return False

def checkip(ip):
	p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
	if p.match(ip):
		return True
	else:
		return False

def checkpro(pro):
	p = re.compile(u'^[\w\.\-\u4e00-\u9fa5]+$')
	if p.match(pro):
		return True
	else:
		return False

@user_data.route('/monitor_route',methods=['GET', 'POST'])
def monitor_route():
	tasktype = request.form.get("tasktype")
	us = request.form.get("se")
	us = filter(str.isdigit, str(us))
	name = request.form.get("a1")
	_type = request.form.get("a2")
	normal = request.form.get("a3")
	btn_status = request.form.get("a4")
	condition = request.form.get("a5")
	t_tasktype = request.form.get("a6")
	now_page = request.form.get("a7")
	more_condition = request.form.get("a8")
	
	hash  = request.form.get('ha');
	
	if hash < 0 or hash =='':
		pass
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();
			

	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(us,client_ip)
	_power=PGetPermissions(system_user)
	_power=str(_power)
	_power_json = json.loads(_power);
	monitor_flag1 = 0
	monitor_flag2 = 0
	for one in _power_json:
		if one['SubMenuId'] == 1:#数据监控
			if one['Mode'] == 2:#管理
				monitor_flag1 = 2
			else:
				monitor_flag1 = 1
		elif one['SubMenuId'] == 7:#系统监控
			if one['Mode'] == 2:#管理
				monitor_flag2 = 2
			else:
				monitor_flag2 = 1
	if t_tasktype < 0:
		t_tasktype = ""
	if name < 0 or name == None:
		name = ""
	if normal < 0:
		normal = ""
	if btn_status < 0:
		btn_status = ""
	if condition < 0:
		condition = "0"
	if now_page < 0:
		now_page = ""
	if more_condition < 0:
		more_condition = "no_con"
	session = us
	if tasktype < 0 or tasktype == None:
		tasktype = "1"

	##XSS Defence
	if str(_type).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"a2格式错误\"}"
	if str(normal).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"a3格式错误\"}"
	if str(btn_status).isdigit() == True or btn_status == "":
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"a4格式错误\"}"
	if condition == "":
		pass
	else:
		if checkaccount(condition) == False and checkip(condition) == False and checkpro(condition) == False:
			return "{\"result\":false,\"ErrMsg\":\"a5格式错误\"}"
		else:
			pass
	if str(t_tasktype).isdigit() == True or t_tasktype == "":
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"a6格式错误\"}"

	if tasktype == "1":
		t = "monitor.html"
	if tasktype == "1_1":
		t = "monitorWhite.html"
	if tasktype == "2":
		t = "data_distribution_info.html"
	if tasktype == "3":
		t = "data_distribution_info.html"
	if tasktype == "4":
		t = "data_distribution_info.html"
	if tasktype == "5":
		t = "data_distribution_info.html"
	if tasktype == "6":
		t = "more_ses_info.html"
	if tasktype == "7":
		t = "ses_detail.html"
	if tasktype == "8":
		t = "data_distribution_info.html"
	myCookie = request.cookies #获取所有cookie
	hash = '';
	if myCookie.has_key('bhost'):
		hash = StrMD5(myCookie['bhost']);
		
	if(tasktype == "6"):
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
		sql = "select public.\"PGetLogFieldConfig\"(1);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_1 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_1 = service_1 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_1 = service_1[:-1]
		
		sql = "select public.\"PGetLogFieldConfig\"(2);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_2 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_2 = service_2 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_2 = service_2[:-1]
		curs.close()
		conn.close()
		return render_template(t,tasktype = tasktype,us = system_user,se = session,a1 = name,a2 = _type,a3 = normal,a4 = btn_status,a5 = condition,a6 = t_tasktype,a7 = now_page,a8 = more_condition,service_1=service_1,service_2=service_2,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2,hash=hash)
	else:
			
		return render_template(t,tasktype = tasktype,us = system_user,se = session,a1 = name,a2 = _type,a3 = normal,a4 = btn_status,a5 = condition,a6 = t_tasktype,a7 = now_page,a8 = more_condition,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2,hash=hash)

@user_data.route('/get_crt',methods=['GET','POST'])
def get_crt():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
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
	#r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=3);
	#serial = r.hget('0','oldestsn')
	server_id=common.get_server_id();
	try:
		crt_t = CertGet(int(server_id))
	except Exception,e:
		crt_t=None
	serial=crt_t[-1].replace('\n','').replace('\r','')
	if crt_t[0] == None:
		crt_list = "{\"productor_name\":\"\",\"client_name\":\"\",\"devid_name\":\"\",\"dev_name\":\"\",\"start\":\"\",\"end\":\"\",\"istest\":0,\"count\":0,\"serial\":\"%s\"}" %((serial))
		return "{\"Result\":true,\"info\":{\"data\":[%s]}}" % crt_list
	productor_name = crt_t[0].decode("utf-8");
	client_name = crt_t[1].decode("utf-8");
	devid_name = crt_t[2].decode("utf-8");
	dev_name = crt_t[3].decode("utf-8");
	start =time.strftime("%Y-%m-%d", time.localtime(crt_t[4]))
	end =time.strftime("%Y-%m-%d", time.localtime(crt_t[5]))
	istest = crt_t[6]
	count = crt_t[7]
	'''
	if(not crt_t[8]):
		serial = ""
	else:
		serial = crt_t[8]
		if(None == serial):	
			serial = ""
	'''
	crt_list = "{\"productor_name\":\"%s\",\"client_name\":\"%s\",\"devid_name\":\"%s\",\"dev_name\":\"%s\",\"start\":\"%s\",\"end\":\"%s\",\"istest\":%d,\"count\":%d,\"serial\":\"%s\"}"%(productor_name,client_name,devid_name,dev_name,start,end,istest,count,(serial))
	return "{\"Result\":true,\"info\":{\"data\":[%s]}}" % crt_list

#获取操作数据分布数据
@user_data.route('/get_ops_data_distribution',methods=['GET','POST'])
def get_ops_data_distribution():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type = request.form.get('a1') #  1: hour    2: day
	refresh = request.form.get("a2")
	normal = request.form.get("a3") # 1: normal  2: alert
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	elif condition_server!='0':
		condition_server_arr=condition_server.split('.')
		if len(condition_server_arr)!=4:
			return '',403
		for a in condition_server_arr:
			if not a.isdigit():
				return '',403
	if condition_user < 0 or condition_user=='0':
		condition_user = "0"
	elif condition_user!="" and not checkaccount(condition_user):
		return '',403
	if condition_protocol < 0:
		condition_protocol = "0"
	elif not condition_protocol.isdigit():
		return '',403
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
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
		try:
			time.strptime(time1, "%Y-%m-%d %H")
		except:
			return '',403
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	if type == '1':
		if refresh == "1":
			sql = "select set_realtime('ops_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if normal == "1":
			if condition_time != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE hour='%s' GROUP BY hour ORDER BY hour ASC;" %(time1)
			elif condition_server != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE ip in (E'%s') GROUP BY hour ORDER BY hour ASC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE usr in (E'%s') GROUP BY hour ORDER BY hour ASC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE clas in (%s) GROUP BY hour ORDER BY hour ASC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday GROUP BY hour ORDER BY hour ASC;"
		elif normal == '2':	
			if condition_time != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE(flag!=0 and hour='%s') GROUP BY hour ORDER BY hour ASC;" %(time1)
			elif condition_server != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY hour ORDER BY hour ASC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY hour ORDER BY hour ASC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY hour ORDER BY hour ASC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT hour, sum(count) FROM ops_all_curday WHERE flag!=0 GROUP BY hour ORDER BY hour ASC;"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		data_total = []
		for result in results:
			str_ip = result[0].split('-')
			del str_ip[0]
			ip = '-'.join(str_ip)
			count = result[1]
			data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
			data_total.append(data)
		data_str = ",".join(data_total)
		curs.close()
		conn.close()
		return "{\"Result\":true,\"Type\":%s,\"info\":[%s]}"% (type,data_str)
	elif type == '2':
		if refresh == "1":
			sql = "select set_realtime('ops_time_14days', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if normal == '1':
			sql="SELECT day,sum(count) FROM public.ops_time_14days GROUP BY day ORDER BY day DESC;"
		if normal == '2':
			sql="SELECT day,sum(count) FROM public.ops_time_14days WHERE flag!=0 GROUP BY day ORDER BY day DESC;"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		data_total = []
		for result in results:
			str_ip = result[0].split('-')
			del str_ip[0]
			ip = '-'.join(str_ip)
			count = result[1]
			data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
			data_total.append(data)
		# 获取当天
		now_date = time.strftime("%x",time.localtime())
		date = now_date.split('/')[1]		#当前的日期
		d_month = now_date.split('/')
		del d_month[2]
		date_month = '-'.join(d_month)		#当前的月-天
		if refresh == "1":
			sql = "select set_realtime('ops_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if normal == "1":
			sql="SELECT hour, sum(count) FROM ops_all_curday GROUP BY hour ORDER BY hour ASC;"
		elif normal == '2':				
			sql="SELECT hour, sum(count) FROM ops_all_curday WHERE flag!=0 GROUP BY hour ORDER BY hour ASC;"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		count = 0
		for result in results:
			result_date = result[0].split(' ')[0].split('-')[2]
			if result_date == date:
				count += result[1]
		ip = date_month
		data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
		data_total.append(data)

		data_str = ",".join(data_total)
		curs.close()
		conn.close()
		return "{\"Result\":true,\"Type\":%s,\"info\":[%s]}"% (type,data_str)
	curs.close()
	conn.close()

#获取会话数据分布数据
@user_data.route('/get_ses_data_distribution',methods=['GET','POST'])
def get_ses_data_distribution():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type = request.form.get('a1') #  1: hour    2: day
	refresh = request.form.get('a2')
	normal = request.form.get("a3") #  1: normal  2: alert
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	if condition_user < 0:
		condition_user = "0"
	if condition_protocol < 0:
		condition_protocol = "0"
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	if type == "1":
		if refresh == "1":
			sql = "select set_realtime('ses_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
		if normal == "1":
			if condition_time != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE hour=E'%s' GROUP BY hour ORDER BY hour ASC;" %(time1)
			elif condition_server != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE ip in (E'%s') GROUP BY hour ORDER BY hour ASC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE usr in (E'%s') GROUP BY hour ORDER BY hour ASC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE clas in (%s) GROUP BY hour ORDER BY hour ASC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday GROUP BY hour ORDER BY hour ASC;"
		elif normal == '2':
			if condition_time != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY hour ORDER BY hour ASC;" %(time1)
			elif condition_server != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY hour ORDER BY hour ASC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY hour ORDER BY hour ASC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY hour ORDER BY hour ASC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT hour, sum(count) FROM ses_all_curday WHERE flag!=0 GROUP BY hour ORDER BY hour ASC;"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		data_total = []
		for result in results:
			str_ip = result[0].split('-')
			del str_ip[0]
			ip = '-'.join(str_ip)
			count = result[1]
			data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
			data_total.append(data)
		data_str = ",".join(data_total)
		curs.close()
		conn.close()
		return "{\"Result\":true,\"Type\":%s,\"info\":[%s]}"% (type,data_str)
	elif type == "2":
		if refresh == "1":
			sql = "select set_realtime('ses_time_14days', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if normal == '1':
			sql="SELECT day,sum(count) FROM public.ses_time_14days GROUP BY day ORDER BY day DESC;"
		if normal == '2':
			sql="SELECT day,sum(count) FROM public.ses_time_14days WHERE flag!=0 GROUP BY day ORDER BY day DESC;"		
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		data_total = []
		for result in results:
			str_ip = result[0].split('-')
			del str_ip[0]
			ip = '-'.join(str_ip)
			count = result[1]
			data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
			data_total.append(data)
		# 获取当天
		now_date = time.strftime("%x",time.localtime())
		date = now_date.split('/')[1]		#当前的日期
		d_month = now_date.split('/')
		del d_month[2]
		date_month = '-'.join(d_month)		#当前的月-天
		if refresh == "1":
			sql = "select set_realtime('ses_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if normal == "1":
			sql="SELECT hour, sum(count) FROM ses_all_curday GROUP BY hour ORDER BY hour ASC;"
		elif normal == '2':				
			sql="SELECT hour, sum(count) FROM ses_all_curday WHERE flag!=0 GROUP BY hour ORDER BY hour ASC;"		
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()
		count = 0
		for result in results:
			result_date = result[0].split(' ')[0].split('-')[2]
			if result_date == date:
				count += result[1]
		ip = date_month
		data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
		data_total.append(data)

		data_str = ",".join(data_total)
		curs.close()
		conn.close()
		return "{\"Result\":true,\"Type\":%s,\"info\":[%s]}"% (type,data_str)
	curs.close()
	conn.close()

#获取会话服务器数据
@user_data.route('/get_ses_service_data',methods=['GET','POST'])
def get_ses_service_data():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')
	normal = request.form.get('a2')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	limitrow = request.form.get('n1')
	if limitrow < 0:
		limitrow = "10"
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	if condition_user < 0:
		condition_user = "0"
	if condition_protocol < 0:
		condition_protocol = "0"
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == "1":
		sql = "select set_realtime('ses_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if normal == '1':
		if condition_time != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE hour=E'%s' GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(time1,limitrow)
		elif condition_server != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE ip in (E'%s') GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_server,limitrow)
		elif condition_user != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE usr in (E'%s') GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_user,limitrow)
		elif condition_protocol != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE clas in (%s) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_protocol,limitrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(limitrow)
	elif normal == '2':
		if condition_time != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(time1,limitrow)
		elif condition_server != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_server,limitrow)
		elif condition_user != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_user,limitrow)
		elif condition_protocol != '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_protocol,limitrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT ip, sum(count) FROM ses_all_curday WHERE flag!=0 GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(limitrow)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	total = 0
	for result in results:
		total += int(result[1])
	for result in results:
		ip = result[0]
		count = result[1]
		percent = '%.4f' %(int(result[1])/total)
		data = "{\"name\":\"%s\",\"value\":\"%s\",\"percent\":\"%s\"}" %(ip,count,percent)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取操作服务器数据
@user_data.route('/get_ops_service_data',methods=['GET','POST'])
def get_ops_service_data():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get("a1")
	normal = request.form.get('a2')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	limitrow = request.form.get('n1')
	if limitrow < 0:
		limitrow = "10"
	elif not limitrow.isdigit():
		return '',403
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	elif condition_server!='0':
		condition_server_arr=condition_server.split('.')
		if len(condition_server_arr)!=4:
			return '',403
		else:
			for a in condition_server_arr:
				if not a.isdigit():
					return '',403
	if condition_user < 0:
		condition_user = "0"
	elif condition_user!='0' and not checkaccount(condition_user):
		return '',403
	if condition_protocol < 0 or condition_protocol=='0':
		condition_protocol = "0"
	elif not condition_protocol.isdigit():
		return '',403
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
		try:
			time.strptime(time1, "%Y-%m-%d %H")
		except:
			return '',403
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == "1":
		sql = "select set_realtime('ops_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if normal == '1':
		if condition_time != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE hour=E'%s' GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(time1,limitrow)
		elif condition_server != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE ip in (E'%s') GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_server,limitrow)
		elif condition_user != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE usr in (E'%s') GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_user,limitrow)
		elif condition_protocol != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE clas in (%s) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_protocol,limitrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(limitrow)
	elif normal == '2':
		if condition_time != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(time1,limitrow)
		elif condition_server != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_server,limitrow)
		elif condition_user != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_user,limitrow)
		elif condition_protocol != '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(condition_protocol,limitrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT ip, sum(count) FROM ops_all_curday WHERE flag!=0 GROUP BY ip ORDER BY sum DESC LIMIT %s;" %(limitrow)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	total = 0
	for result in results:
		total += int(result[1])
	for result in results:
		ip = result[0]
		count = result[1]
		percent = '%.4f' %(int(result[1])/total)
		data = "{\"name\":\"%s\",\"value\":\"%s\",\"percent\":\"%s\"}" %(ip,count,percent)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取操作用户数据
@user_data.route('/get_ops_user_data',methods=['GET','POST'])
def get_ops_user_data():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get("a1")
	normal = request.form.get('a2')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	elif condition_server!='0':
		condition_server_arr=condition_server.split('.')
		if len(condition_server_arr)!=4:
			return '',403
		else:
			for a in condition_server_arr:
				if not a.isdigit():
					return '',403
	if condition_user < 0:
		condition_user = "0"
	elif condition_user!='0' and not checkaccount(condition_user):
		return '',403
	if condition_protocol < 0:
		condition_protocol = "0"
	elif not condition_protocol.isdigit():
		return '',403
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
		try:
			time.strptime(time1, "%Y-%m-%d %H")
		except:
			return '',403
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == "1":
		sql = "select set_realtime('ops_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	if normal == '1':
		if condition_time != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE hour=E'%s' GROUP BY usr ORDER BY sum DESC;" %(time1)
		elif condition_server != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE ip in (E'%s') GROUP BY usr ORDER BY sum DESC;" %(condition_server)
		elif condition_user != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE usr in (E'%s') GROUP BY usr ORDER BY sum DESC;" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE clas in (%s) GROUP BY usr ORDER BY sum DESC;" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday GROUP BY usr ORDER BY sum DESC;"
	if normal == '2':
		if condition_time != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY usr ORDER BY sum DESC;" %(time1)
		elif condition_server != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY usr ORDER BY sum DESC;" %(condition_server)
		elif condition_user != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY usr ORDER BY sum DESC;" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY usr ORDER BY sum DESC;" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT usr, sum(count) FROM ops_all_curday WHERE flag!=0 GROUP BY usr ORDER BY sum DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		ip = result[0]
		count = result[1]
		data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取会话用户数据
@user_data.route('/get_ses_user_data',methods=['GET','POST'])
def get_ses_user_data():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')
	normal = request.form.get('a2')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	if condition_user < 0:
		condition_user = "0"
	if condition_protocol < 0:
		condition_protocol = "0"
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == "1":
		sql = "select set_realtime('ses_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if normal == '1':
		if condition_time != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE hour=E'%s' GROUP BY usr ORDER BY sum DESC;" %(time1)
		elif condition_server != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE ip in (E'%s') GROUP BY usr ORDER BY sum DESC;" %(condition_server)
		elif condition_user != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE  usr in (E'%s') GROUP BY usr ORDER BY sum DESC;" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE  clas in (%s) GROUP BY usr ORDER BY sum DESC;" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday GROUP BY usr ORDER BY sum DESC;"	
	if normal == '2':
		if condition_time != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY usr ORDER BY sum DESC;" %(time1)
		elif condition_server != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY usr ORDER BY sum DESC;" %(condition_server)
		elif condition_user != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY usr ORDER BY sum DESC;" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY usr ORDER BY sum DESC;" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT usr, sum(count) FROM ses_all_curday WHERE flag!=0 GROUP BY usr ORDER BY sum DESC;"		
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		ip = result[0]
		count = result[1]
		data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取协议数据
@user_data.route('/get_protocol_data',methods=['GET','POST'])
def get_protocol_data():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')
	_type = request.form.get('a2')
	normal = request.form.get('a3')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7')
	if condition_time < 0:
		condition_time = "0"
	if condition_server < 0:
		condition_server = "0"
	if condition_user < 0:
		condition_user = "0"
	if condition_protocol < 0:
		condition_protocol = "0"
	if condition_time != "0":
		time1 = condition_time.split('**')[0]
		time1 = time1.split(':')[0]
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if _type == '1':
		if refresh == '1':
			sql = "select set_realtime('ses_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
		if normal == '1':
			if condition_time != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE hour=E'%s' GROUP BY clas ORDER BY sum DESC;" %(time1)
			elif condition_server != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE ip in (E'%s') GROUP BY clas ORDER BY sum DESC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE usr in (E'%s') GROUP BY clas ORDER BY sum DESC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE clas in (%s) GROUP BY clas ORDER BY sum DESC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday GROUP BY clas ORDER BY sum DESC;"
		elif normal == '2':
			if condition_time != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY clas ORDER BY sum DESC;" %(time1)
			elif condition_server != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY clas ORDER BY sum DESC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY clas ORDER BY sum DESC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY clas ORDER BY sum DESC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT clas, sum(count) FROM ses_all_curday WHERE flag!=0 GROUP BY clas ORDER BY sum DESC;"					
	elif _type == '2':
		if refresh == '1':
			sql = "select set_realtime('ops_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
		if normal == '1':
			if condition_time != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(flag=0 and hour=E'%s') GROUP BY clas ORDER BY sum DESC;" %(time1)
			elif condition_server != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(ip in (E'%s') and flag=0) GROUP BY clas ORDER BY sum DESC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(flag=0 and usr in (E'%s')) GROUP BY clas ORDER BY sum DESC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(flag=0 and clas in (%s)) GROUP BY clas ORDER BY sum DESC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE flag=0 GROUP BY clas ORDER BY sum DESC;"
		elif normal == '2':
			if condition_time != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(flag!=0 and hour=E'%s') GROUP BY clas ORDER BY sum DESC;" %(time1)
			elif condition_server != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(ip in (E'%s') and flag!=0) GROUP BY clas ORDER BY sum DESC;" %(condition_server)
			elif condition_user != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(flag!=0 and usr in (E'%s')) GROUP BY clas ORDER BY sum DESC;" %(condition_user)
			elif condition_protocol != '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE(flag!=0 and clas in (%s)) GROUP BY clas ORDER BY sum DESC;" %(condition_protocol)
			elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
				sql="SELECT clas, sum(count) FROM ops_all_curday WHERE flag!=0 GROUP BY clas ORDER BY sum DESC;"
	elif _type == '3':
		if refresh == '1':
			sql = "select set_realtime('ses_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "SELECT clas, flag, count FROM public.ses_all_curday;"
	elif _type == '4':
		if refresh == '1':
			sql = "select set_realtime('ops_all_curday', '5 seconds');"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "SELECT clas, flag, count FROM public.ops_all_curday;"		
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	if _type == '3' or _type == '4':
		for result in results:
			ip = result[0]
			normal = result[1]
			count = result[2]
			data = "{\"name\":\"%s\",\"Type\":\"%s\",\"value\":\"%s\"}" %(ip,normal,count)
			data_total.append(data)
		data_str = ",".join(data_total)
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":[%s]}"% (data_str)	
	else:
		for result in results:
			ip = result[0]
			count = result[1]
			data = "{\"name\":\"%s\",\"value\":\"%s\"}" %(ip,count)
			data_total.append(data)
		data_str = ",".join(data_total)
		curs.close()
		conn.close()
		return "{\"Result\":true,\"info\":[%s]}"% (data_str)
	curs.close()
	conn.close()

#获取最新会话数据
@user_data.route('/get_new_session',methods=['GET','POST'])
def get_new_session():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	limitrow =  request.form.get('a1')
	offsetrow = request.form.get('a2')
	ses_type = request.form.get('a3')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7') 
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
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if condition_time != '0':
		time1 = condition_time.split('**')[0]
		time2 = condition_time.split('**')[1]
	#0:all 1:normal 2:alert
	if ses_type == "0":
		if condition_time != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE xtime_04 between E'%s' and E'%s' ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow, offsetrow)
		elif condition_server != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE ip_01 in (E'%s') ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_server,limitrow, offsetrow)		
		elif condition_user != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE str32_22 in (E'%s') ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_user,limitrow, offsetrow)		
		elif condition_protocol != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE int32_01 in (%s) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_protocol,limitrow, offsetrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
	if ses_type == "1":
		if condition_time != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12=0 and xtime_04 between E'%s' and E'%s') ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow, offsetrow)
		elif condition_server != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12=0 and  ip_01 in (E'%s')) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_server,limitrow, offsetrow)		
		elif condition_user != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12=0 and  str32_22 in (E'%s')) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_user,limitrow, offsetrow)		
		elif condition_protocol != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12=0 and  int32_01 in (%s)) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_protocol,limitrow, offsetrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE int08_12=0 ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
		#sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE int08_12=0 ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
	elif ses_type == "2":
		if condition_time != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12!=0 and xtime_04 between E'%s' and E'%s' ) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow, offsetrow)
		elif condition_server != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12!=0 and  ip_01 in (E'%s')) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_server,limitrow, offsetrow)		
		elif condition_user != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12!=0 and  str32_22 in (E'%s')) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_user,limitrow, offsetrow)		
		elif condition_protocol != '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE(int08_12!=0 and  int32_01 in (%s)) ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(condition_protocol,limitrow, offsetrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE int08_12!=0 ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
		#sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE int08_12!=0 ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	number = int(curs.rowcount)
	if results == []:
		data_total = ""
	else:
		data_total = ""
		limitrow = int(limitrow)
		if limitrow>number:
			limitrow=number
		count = 0
		while count<limitrow:
			_id = results[count][9]
			starttime = results[count][0]
			endtime = results[count][1]
			_type = results[count][2]
			status = results[count][3]
			operationaluser = results[count][4]
			operationalusername = results[count][5]
			serverip = results[count][6]
			approvalusername = results[count][7]
			serverusername = results[count][8]
			if approvalusername == '':
				approvalusername == None
			data = "{\"Id\":\"%s\",\"StartTime\":\"%s\",\"EndTime\":\"%s\",\"Type\":\"%s\",\"Status\":\"%s\",\"OperationalUser\":\"%s\",\"OperationalUserName\":\"%s\",\"ServerIP\":\"%s\",\"ApprovalUserName\":\"%s\",\"ServerUserName\":\"%s\"}" %(_id,starttime,endtime,_type,status,operationaluser,operationalusername,serverip,approvalusername,serverusername)
			data_total = data_total + str(data) + ','
			count = count + 1
		if(limitrow>0):
			data_total = data_total[:-1]
	#获取会话数量
	#0:all 1:normal 2:alert
	if ses_type == '0':
		if condition_time != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE xtime_04 between E'%s' and E'%s' ;" %(time1,time2)
		elif condition_server != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE ip_01 in (E'%s');" %(condition_server)
		elif condition_user != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE str32_22 in (E'%s');" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE int32_01 in (%s);" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT count(*) FROM public.ses_table;"
	if ses_type == '1':
		if condition_time != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12=0 and xtime_04 between E'%s' and E'%s' );" %(time1,time2)
		elif condition_server != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12=0 and ip_01 in (E'%s'));" %(condition_server)
		elif condition_user != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12=0 and str32_22 in (E'%s'));" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12=0 and int32_01 in (%s));" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT count(*) FROM public.ses_table WHERE int08_12=0;"		
	elif ses_type == '2':
		if condition_time != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12!=0 and xtime_04 between E'%s' and E'%s');" %(time1,time2)
		elif condition_server != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12!=0 and ip_01 in (E'%s'));" %(condition_server)
		elif condition_user != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12!=0 and str32_22 in (E'%s'));" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT count(*) FROM public.ses_table WHERE(int08_12!=0 and int32_01 in (%s));" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT count(*) FROM public.ses_table WHERE int08_12!=0;"		
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	totalrow = results[0][0]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"totalrow\":%s,\"info\":[%s]}"% (totalrow,data_total)	

#获取最新操作数据
@user_data.route('/get_new_option',methods=['GET','POST'])
def get_new_option():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	limitrow =  request.form.get('a1')
	offsetrow = request.form.get('a2')
	ops_type = request.form.get('a3')
	condition_time = request.form.get('a4') 
	condition_server = request.form.get('a5') 
	condition_user = request.form.get('a6') 
	condition_protocol = request.form.get('a7') 	
	session = request.form.get('a0')
	if limitrow == "":
		limitrow = "null"
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
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if condition_time != '0':
		##
		time1 = condition_time.split('**')[0]
		time2 = condition_time.split('**')[1]
		##
	if ops_type == "0":
		if condition_time != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE xtime_02 between E'%s' and E'%s' ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow, offsetrow)
		elif condition_server != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE ip_01 in (E'%s') ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_server,limitrow, offsetrow)		
		elif condition_user != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE str32_22 in (E'%s') ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_user,limitrow, offsetrow)		
		elif condition_protocol != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE int32_01 in (%s) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_protocol,limitrow, offsetrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
		#sql="SELECT xtime_02,int32_01,str32_00,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)		
	if ops_type == "1":
		if condition_time != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12=0 and xtime_04 between E'%s' and E'%s') ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow, offsetrow)
		elif condition_server != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12=0 and  ip_01 in (E'%s')) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_server,limitrow, offsetrow)		
		elif condition_user != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12=0 and  str32_22 in (E'%s')) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_user,limitrow, offsetrow)		
		elif condition_protocol != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12=0 and  int32_01 in (%s)) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_protocol,limitrow, offsetrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE int08_12=0 ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)		
		#sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE int08_12=0 ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)
	elif ops_type == "2":
		if condition_time != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12!=0 and xtime_04  between E'%s' and E'%s') ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow, offsetrow)
		elif condition_server != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12!=0 and  ip_01 in (E'%s')) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_server,limitrow, offsetrow)		
		elif condition_user != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12!=0 and  str32_22 in (E'%s')) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_user,limitrow, offsetrow)		
		elif condition_protocol != '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE(int08_12!=0 and  int32_01 in (%s)) ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(condition_protocol,limitrow, offsetrow)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT xtime_02,int32_01,str32_22,str32_23,ip_01,str32_25,str32_00,str32_01,xtime_00 FROM public.ops_table WHERE int08_12!=0 ORDER BY xtime_02 DESC LIMIT %s OFFSET %s;" %(limitrow, offsetrow)	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	number = int(curs.rowcount)
	data_total = ""
	if results == []:
		data_total = ""
	else:
		limitrow = int(limitrow)
		if limitrow>number:
			limitrow=number
		count = 0
		while count<limitrow:
			_id = results[count][8]
			starttime = results[count][0]
			_type = results[count][1]
			bhuser = results[count][2]
			bhusername = results[count][3]
			serverip = results[count][4]
			approvalusername = results[count][5]
			serverusername = results[count][6]
			option = results[count][7]
			if approvalusername == '':
				approvalusername == None
			data = "{\"Id\":\"%s\",\"StartTime\":\"%s\",\"Type\":\"%s\",\"Bhuser\":\"%s\",\"Bhusername\":\"%s\",\"ServerIP\":\"%s\",\"ApprovalUserName\":\"%s\",\"ServerUserName\":\"%s\",\"Option\":\"%s\"}" %(_id,starttime,_type,bhuser,bhusername,serverip,approvalusername,serverusername,option)
			data_total = data_total + str(data) + ','
			count = count + 1
		if(limitrow>0):
			data_total = data_total[:-1]
	#获取操作数量
	if ops_type == '0':
		if condition_time != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE xtime_04 between E'%s' and E'%s';" %(time1,time2)
		elif condition_server != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE ip_01 in (E'%s');" %(condition_server)
		elif condition_user != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE str32_22 in (E'%s');" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE int32_01 in (%s);" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT count(*) FROM public.ops_table;"		
	if ops_type == '1':
		if condition_time != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12=0 and xtime_04 between E'%s' and E'%s');" %(time1,time2)
		elif condition_server != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12=0 and ip_01 in (E'%s'));" %(condition_server)
		elif condition_user != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12=0 and str32_22 in (E'%s'));" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12=0 and int32_01 in (%s));" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT count(*) FROM public.ops_table WHERE int08_12=0;"	
	elif ops_type == '2':
		if condition_time != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12!=0 and xtime_04 between E'%s' and E'%s');" %(time1,time2)
		elif condition_server != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12!=0 and ip_01 in (E'%s'));" %(condition_server)
		elif condition_user != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12!=0 and str32_22 in (E'%s'));" %(condition_user)
		elif condition_protocol != '0':
			sql="SELECT count(*) FROM public.ops_table WHERE(int08_12!=0 and int32_01 in (%s));" %(condition_protocol)
		elif condition_time == '0' and condition_server == '0' and condition_user == '0' and condition_protocol == '0':
			sql="SELECT count(*) FROM public.ops_table WHERE int08_12!=0;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	totalrow = results[0][0]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"totalrow\":%s,\"info\":[%s]}"% (totalrow,data_total)	

#获取当天会话数量
@user_data.route('/get_ses_amount_d',methods=['GET','POST'])
def get_ses_amount_d():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ses_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT clas,sum(count) FROM public.ses_all_curday WHERE flag = 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] == 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)	

#获取当月会话数量
@user_data.route('/get_ses_amount_m',methods=['GET','POST'])
def get_ses_amount_m():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ses_clas_curmon', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT clas,sum(count) FROM public.ses_clas_curmon WHERE flag = 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] == 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取当天异常会话数量
@user_data.route('/get_ases_amount_d',methods=['GET','POST'])
def get_ases_amount_d():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ses_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT clas,sum(count) FROM public.ses_all_curday WHERE flag != 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] > 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)	

#获取当月异常会话数量
@user_data.route('/get_ases_amount_m',methods=['GET','POST'])
def get_ases_amount_m():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ses_clas_curmon', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT clas,sum(count) FROM public.ses_clas_curmon WHERE flag != 0 GROUP BY clas ORDER BY sum(count) DESC"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] > 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取当天操作数量
@user_data.route('/get_ops_amount_d',methods=['GET','POST'])
def get_ops_amount_d():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ops_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT clas,sum(count) FROM public.ops_all_curday WHERE flag = 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)	

#获取当月操作数量
@user_data.route('/get_ops_amount_m',methods=['GET','POST'])
def get_ops_amount_m():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ops_clas_curmon', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT clas,sum(count) FROM public.ops_clas_curmon WHERE flag = 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] == 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)

#获取当天异常操作数量
@user_data.route('/get_aops_amount_d',methods=['GET','POST'])
def get_aops_amount_d():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ops_all_curday', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	sql="SELECT clas,sum(count) FROM public.ops_all_curday WHERE flag != 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] > 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)	

#获取当月异常操作数量
@user_data.route('/get_aops_amount_m',methods=['GET','POST'])
def get_aops_amount_m():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	refresh = request.form.get('a1')	
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
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if refresh == '1':
		sql="select set_realtime('ops_clas_curmon', '5 seconds');"
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	sql="SELECT clas,sum(count) FROM public.ops_clas_curmon WHERE flag != 0 GROUP BY clas ORDER BY sum(count) DESC;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] > 0:
		_type = result[0]
		count = result[1]
		data = "{\"Type\":\"%s\",\"Count\":\"%s\"}" %(_type,count)
		data_total.append(data)
	data_str = ",".join(data_total)
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s]}"% (data_str)


#获取用户空间容量
@user_data.route('/getUSize',methods=['GET','POST'])
def getUSize():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
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
	r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=2)
	results = UsrSize(r)
	result = results[1]
	result = result.replace("[","").replace("]","")
	result_array = result.split(', ')

	_time_local=time.time()
	
	total = float(result_array[1].replace("L",""))
	used = float(result_array[0].replace("L",""))
	percentage = (round(used*100/total,2))
	percentage = float(percentage)
	total = int(result_array[1].replace("L","")) / 1024 / 1024 / 1024
	used = int(result_array[0].replace("L","")) / 1024 / 1024 / 1024

	info = []
	info_tmp = {"total":"","used":"","percentage":""}
	info_tmp['total'] = round(total,0)
	info_tmp['used'] = round(used,0)
	info_tmp['percentage'] = percentage	
	info.append(info_tmp)
	result = {"Result":"true","info":[],"status":"true"}

	if (_time_local-int(result_array[2].replace("L",""))) <= 3000:
		result['info'] = info
		return json.dumps(result)
	else:
		result['info'] = info
		result['status'] = "false"
		return json.dumps(result)


#获取系统空间容量
@user_data.route('/getSSize',methods=['GET','POST'])
def getSSize():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	sid_str = request.form.get('a1')
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
	r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=2)
	info = []
	sid_array = sid_str.split(',')
	for sid in sid_array:
		results = SysSize(r,sid)
		if results[1] == None:
			debug(str(sid))
			info_tmp = {"total":"0","used":"0","percentage":"0","server_id":""}
			info_tmp['server_id'] = sid
			info.append(info_tmp)
		elif results and len(results) > 1:
			result = results[1]
			result = result.replace("[","").replace("]","")
			result_array = result.split(', ')
			_time_local=time.time()
		
			total = float(result_array[1].replace("L",""))
			used = float(result_array[0].replace("L",""))
			percentage = (round(used*100/total,2))
			percentage = float(percentage)
			total = int(result_array[1].replace("L","")) / 1024 / 1024 / 1024
			used = int(result_array[0].replace("L","")) / 1024 / 1024 / 1024
				
			info_tmp = {"total":"","used":"","percentage":"","server_id":"","status":""}
			info_tmp['total'] = round(total,0)
			info_tmp['used'] = round(used,0)
			info_tmp['percentage'] = percentage
			info_tmp['server_id'] = sid
			if (int(_time_local)-int(result_array[2].replace("L",""))) <= 3000:	
				info_tmp['status'] = "true"
			else:
				info_tmp['status'] = "false"
			info.append(info_tmp)
		else:
			total = 0;
			used = 0;
			percentage = 0;
	result = {"Result":"true","info":[]}
	result['info'] = info

	return json.dumps(result)

#获取系统时间
@user_data.route('/get_systemTime',methods=['GET','POST'])
def get_systemTime():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
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
	systemTime = GetNowTime();
	return "{\"Result\":true,\"info\":[{\"time\":\"%s\"}]}"% (systemTime)

#获取当天最新会话数据(一层监控页面)
@user_data.route('/get_new_session_monitor1',methods=['GET','POST'])
def get_new_session_monitor1():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	condition1 = request.form.get('a1')
	condition2 = request.form.get('a2')
	limitrow = request.form.get('a3')
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
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE xtime_04 between E'%s' and E'%s' ORDER BY xtime_04 DESC LIMIT %s;" %(condition1, condition2,limitrow)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	number = int(curs.rowcount)
	if results == []:
		data_total = ""
	else:
		data_total = ""
		count = 0
		while count < number:
			_id = results[count][9]
			starttime = results[count][0]
			endtime = results[count][1]
			_type = results[count][2]
			status = results[count][3]
			operationaluser = results[count][4]
			operationalusername = results[count][5]
			serverip = results[count][6]
			approvalusername = results[count][7]
			serverusername = results[count][8]
			if approvalusername == '':
				approvalusername == None
			data = "{\"Id\":\"%s\",\"StartTime\":\"%s\",\"EndTime\":\"%s\",\"Type\":\"%s\",\"Status\":\"%s\",\"OperationalUser\":\"%s\",\"OperationalUserName\":\"%s\",\"ServerIP\":\"%s\",\"ApprovalUserName\":\"%s\",\"ServerUserName\":\"%s\"}" %(_id,starttime,endtime,_type,status,operationaluser,operationalusername,serverip,approvalusername,serverusername)
			data_total = data_total + str(data) + ','
			count = count + 1
		if(number > 0):
			data_total = data_total[:-1]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"totalrow\":%s,\"info\":[%s]}"% (number,data_total)	

#获取一周内连接中的会话数据(一层监控页面)
@user_data.route('/get_new_session_monitor2',methods=['GET','POST'])
def get_new_session_monitor2():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	condition1 = request.form.get('a1')
	condition2 = request.form.get('a2')
	limitrow = request.form.get('a3')	
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
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_00 FROM public.ses_table WHERE (xtime_04 between E'%s' and E'%s' and int08_03=0) ORDER BY xtime_04 DESC LIMIT %s;" %(condition1, condition2, limitrow)

	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	number = int(curs.rowcount)
	if results == []:
		data_total = ""
	else:
		data_total = ""
		count = 0
		while count < number:
			_id = results[count][9]
			starttime = results[count][0]
			endtime = results[count][1]
			_type = results[count][2]
			status = results[count][3]
			operationaluser = results[count][4]
			operationalusername = results[count][5]
			serverip = results[count][6]
			approvalusername = results[count][7]
			serverusername = results[count][8]
			if approvalusername == '':
				approvalusername == None
			data = "{\"Id\":\"%s\",\"StartTime\":\"%s\",\"EndTime\":\"%s\",\"Type\":\"%s\",\"Status\":\"%s\",\"OperationalUser\":\"%s\",\"OperationalUserName\":\"%s\",\"ServerIP\":\"%s\",\"ApprovalUserName\":\"%s\",\"ServerUserName\":\"%s\"}" %(_id,starttime,endtime,_type,status,operationaluser,operationalusername,serverip,approvalusername,serverusername)
			data_total = data_total + str(data) + ','
			count = count + 1
		if(number > 0):
			data_total = data_total[:-1]
	curs.close()
	conn.close()
	return "{\"Result\":true,\"totalrow\":%s,\"info\":[%s]}"% (number,data_total)

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

### 获取列表结果 (控件版本)-->监控
@user_data.route("/get_log_list_monitor", methods=['GET', 'POST'])
def get_log_list_monitor():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheckLocal(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		maxpage = int(request.args.get('limit'))
		condition = request.args.get('t2')
		logtype = request.args.get('t4')
		fieldsname = request.args.get('t5')
		if fieldsname>0:
			fieldsname_arr=fieldsname.split(',')
			for a in fieldsname_arr:
				if a!='' and checkaccount(a) == False:
					return '',403
		curpage = request.args.get('page')
		if condition == "" or condition < 0:
			condition = 'null'	
		if curpage < 0 or curpage == "":
			curpage = 1
		else:
			curpage = int(curpage)
		
		offset = maxpage*(curpage-1)

		proto_list = proto_all();
		proto_list = json.loads(proto_list)['data']
		if proto_list == None:
			proto_list = []
		pro_l = []
		for proto in proto_list:
			pro_l.append([])
			pro_l[-1].append(proto['ProtocolId'])
			pro_l[-1].append(proto['ProtocolName'])

		try:
			conn = pyodbc.connect(StrSqlConn('BH_DATA'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
		if(logtype == 'NORMAL'):
			type = 1;
		elif(logtype == 'SESSION'):
			type = 2;
		elif(logtype == 'SYSTEM'):
			type = 3;
		else:
			type = 1;
		
		if condition == 'null':
			sql = "select public.\"PGetLogData\"(null,%d,E'%s',%d,%d,null);" %(type,fieldsname,maxpage,offset);
		else:
			condition_json = json.loads(condition);
			if condition_json.has_key('starttime'):
				starttime = condition_json['starttime'];
				if starttime!= None :
					try:
						time.mktime(time.strptime(starttime[:-3],'%Y-%m-%d %H:%M:%S'))
					except:
						return '',403 
			if condition_json.has_key('moretime'):
				moretime = condition_json['moretime'];
				if moretime!= None :
					try:
						time.mktime(time.strptime(moretime[:-3],'%Y-%m-%d %H:%M:%S'))
					except:
						return '',403 
			if condition_json.has_key('endtime'):		
				endtime = condition_json['endtime'];
				if endtime!= None :
					try:
						time.mktime(time.strptime(endtime[:-3],'%Y-%m-%d %H:%M:%S'))
					except:
						return '',403 
			sql = "select public.\"PGetLogData\"(null,%d,E'%s',%d,%d,E'%s');" %(type,fieldsname,maxpage,offset,condition);
		
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		#results = curs.fetchall()[0][0].encode('utf-8').replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;");
		results = curs.fetchall()
		if results:
			if type == 1:
				if results[0][0] == None:
					results ='[]'
				else:
					results = results[0][0].encode('utf-8')
					results_json = json.loads(results)
					for one in results_json:
						if(logtype == 'SYSTEM'):
							one['int32_01'] = StrClas('int32','01',int(one['int32_01']),1,1)
							one['int08_12'] = StrClas('int08','12',int(one['int08_12']),1,1)	
						else:
							one['xtime_03'] = '%d' %(one['xtime_03'])
							if(one['int08_12'] > 0): ##未启用告警
								clas = 1
							else:
								clas = 0
								
							for pro in pro_l:
								if pro[0] == one['int32_01']:
									one['int32_01'] = pro[1];
							for o in one:
								if o == "orderitem":
									continue
								field = o.split('_')[0]
								index = o.split('_')[1]
								if (o.find('int08') >=0 and (index == '11' or index == '14' or index == '03' or index == '15')) or o=='str32_31' or o=='str32_29':
										one[o] = StrClas(field,index,str(one[o]),0,clas)
								if o == 'int64_15':
									num_tmp = hex(int(one[o]))
									one[o] = StrClas(field,index,int(one[o]),clas)
							if int(one['int16_00']) == 0:
								one['int16_00'] ='';			
							if int(one['int16_01']) == 0:
								one['int16_01'] ='';	
							one['DownloadEnable'] = False
							one['DeleteEnable'] = False
							one['IfReplay'] = False ##是否使用控件回放
							one['IfReplayDrawing'] = False ##回放  字符回放（ssh等） 图形回放（RDP等）
							#检查是否有回放文件
							if one['str32_28'] != "":
								one['DownloadEnable'] = True
								one['DeleteEnable'] = False
								##
								one['IfReplay'] = True;							
								pro = one['str32_28'].split('/')[-2].upper()
								if pro =="RDP" or pro =="ACC" or pro =="VNC" or pro =="X11":
									one['IfReplayDrawing'] = True						
								
							else:
								#检查日志类型字段是否是 FTP 或者 SFTP
								if one['int32_01'] == 'FTP' or one['int32_01'] == 'SFTP' or one['int32_01'] == 'SSH':
									#检查操作字段是否有 "Save" 字符串
									if one['str32_01'].find("Save") != -1:
										#检查传输文件是否存在
										filename = one['str32_01'].replace('Save ','',1)
										filepath = '/usr/storage/.system/transf/ftp/'
										fdir = filepath + filename
										if os.path.exists(fdir):
											one['DownloadEnable'] = True
											one['DeleteEnable'] = True
					results = json.dumps(results_json)
			if type == 2:
				if results[0][0] == None:
					results ='[]'
				else:
					results = results[0][0].encode('utf-8')
					results_json = json.loads(results)
					for one in results_json:
						one['xtime_03'] = '%d' %(one['xtime_03'])
						if type == 2 and one['int08_03'] == 0:
							if str(one['xtime_02']) == 'None':
								one['int08_03'] = '1'
							else:
								#最后更新时间超过300秒显示为断开
								systemTime1 = GetNowTime()
								timeArray = time.strptime(systemTime1, "%Y-%m-%d %H:%M:%S")

								systemTime2 = one['xtime_02']
								otime_str1 = systemTime2.split('T')[0]
								otime_str2 = systemTime2.split('T')[1].split('+')[0]
								otime = otime_str1+' '+otime_str2
								timeArray1 = time.strptime(otime, "%Y-%m-%d %H:%M:%S")
								timestamp = time.mktime(timeArray)
								timestamp1 = time.mktime(timeArray1)
								Seconds = timestamp - timestamp1

								if Seconds > 300:
									one['int08_03'] = '2'
								#
						if(one['int08_12'] > 0): ##未启用告警
							clas = 1
						else:
							clas = 0
							
						for pro in pro_l:
							if pro[0] == one['int32_01']:
								one['int32_01'] = pro[1];
						for o in one:
							if o == "orderitem":
								continue
							field = o.split('_')[0];
							index = o.split('_')[1];
							if o.find('int08') >=0 and (index == '11' or index == '14' or index == '03' or index == '15'):
								one[o] = StrClas(field,index,str(one[o]),0,clas)
							if o == 'int64_15':
									num_tmp = hex(int(one[o]))
									one[o] = StrClas(field,index,int(one[o]),clas)
						if int(one['int16_00']) == 0:
							one['int16_00'] ='';			
						if int(one['int16_01']) == 0:
								one['int16_01'] ='';	
						one['DownloadEnable'] = False
						one['DeleteEnable'] = False
						one['IfReplay'] = False ##是否使用控件回放
						one['IfReplayDrawing'] = False ##回放  字符回放（ssh等） 图形回放（RDP等）
						#检查是否有回放文件
						if one['str32_28'] != "":
							one['DownloadEnable'] = True
							one['DeleteEnable'] = False
							##
							one['IfReplay'] = True;							
							pro = one['str32_28'].split('/')[-2].upper()
							if pro =="RDP" or pro =="ACC" or pro =="VNC" or pro =="X11":
								one['IfReplayDrawing'] = True

					results = json.dumps(results_json)
			elif type == 3:
				if results[0][0] == None:
					results ='[]'
				else:
					results = results[0][0].encode('utf-8')
					results_json = json.loads(results)
					for one in results_json:
						if one['int08_12']==None:
							one['int08_12']=0
						if one['int08_12']!=0:
							clas = 1
						else:
							clas = 0
						for o in one:
							if o == "orderitem":
								continue
						
							if o == 'int32_01' or o == 'int08_12':
								field = o.split('_')[0];
								index = o.split('_')[1];
								if one[o] == None:
									one[o] == 0
								one[o] = StrClas(field,index,one[o],1,clas)
							if o == 'int08_11':
								if one['int08_12'] == 1:
									if one[o] == 1:
										one[o] = '已处理'
									elif one[o] == 0:
										one[o] = '未处理'
								else:
									one[o] = ''

						'''
							if o=='int32_01' or o=='int08_12':
								field = o.split('_')[0]
								index = o.split('_')[1]							
								one[o] = StrClas(field,index,int(one[o]),1,1)
						'''
					results = json.dumps(results_json)					
		else:
			results ='[]'
		###获取当前数据总数
		curs.close()
		conn.close()
		
		try:
			conn = pyodbc.connect(StrSqlConn('BH_DATA'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		sql = "select public.\"PGetLogCount\"(null,%d,E'%s');" %(type,condition);
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % ( sys._getframe().f_lineno)
		result = curs.fetchall()
		Count = result[0][0]
		
		curs.close()
		conn.close()
		
		###拼接 json格式
		# if type == 1:
		# 	results = results[0][0].encode('utf-8')
		results_list = json.loads(results)
		result_json ={
			"page":curpage,
			"totalCount":Count,
			"items":[]
		}
		for one in results_list:
			if 'int64_14' in one.keys():
				one['int64_14']='%sB'%one['int64_14']
			result_json['items'].append(one)
		
		return json.dumps(result_json)
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % ( sys._getframe().f_lineno)

@user_data.route('/log_detail_route',methods=['GET', 'POST'])
def log_detail_route():
	a1 = request.args.get("m1")
	a2 = request.args.get("m2")
	a3 = request.args.get("m3")
	a4 = request.args.get("m4")
	a5 = request.args.get("m5")
	a6 = request.args.get("m6")
	xtime_00 = request.args.get("m7")
	index_total = request.args.get("m8")
	page = request.args.get("m9")
	logtype = request.args.get("m10")
	tasktype=request.args.get('tasktype')
	if tasktype < 0:
		tasktype = '1'
	if xtime_00 < 0:
		xtime_00 = ""
	elif xtime_00!='' and not xtime_00.isdigit():
		return '',403
	if index_total < 0:
		index_total = ""
	if page < 0:
		page = ""
	if logtype < 0:
		logtype = ""
	if a1 < 0:
		a1 = "0"
	if a2 < 0:
		a2 = "0"
	if a3 < 0:
		a3 = "0"
	if a4 < 0:
		a4 = "0"
	if a5 < 0:
		a5 = "0"
	if a6 < 0:
		a6 = "0"
											
	session = request.args.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	_power=get_user_perm_value(userCode)
	_power=str(_power)
	_power_json = json.loads(_power);
	monitor_flag1 = 0
	monitor_flag2 = 0
	perm=0
	for one in _power_json:
		if one['SubMenuId'] == 1:#数据监控
			perm=one['Mode']
			if one['Mode'] == 2:#管理
				monitor_flag1 = 2
			else:
				monitor_flag1 = 1
		elif one['SubMenuId'] == 7:#系统监控
			if one['Mode'] == 2:#管理
				monitor_flag2 = 2
			else:
				monitor_flag2 = 1
	if tasktype == '1':
		if logtype < 0:
			logtype = 0
		if logtype=='NORMAL':
			logtype=1
		elif logtype=='SESSION':
			logtype=2
		elif logtype=='SYSTEM':
			logtype=3
		else:
			if str(logtype).isdigit() ==False:
				return '',403
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql="select public.\"PGetLogFieldConfig\"(%s);" %(logtype)
				curs.execute(sql)
				config = curs.fetchall()[0][0]
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		proto_list = proto_all();
		proto_list = json.loads(proto_list)['data']
		if proto_list == None:
			proto_list = []
		pro_l = []
		for proto in proto_list:
			pro_l.append([])
			pro_l[-1].append(proto['ProtocolId'])
			pro_l[-1].append(proto['ProtocolName'])		
		try:
			with pyodbc.connect(StrSqlConn('BH_DATA')) as conn,conn.cursor() as curs:
				sql="select public.\"PGetLogDetail\"(%s,%s);" %(xtime_00,logtype)
				curs.execute(sql)
				detail = curs.fetchall()[0][0]
				detail_json = json.loads(detail)
				detail_json['xtime_03'] = '%d' %(detail_json['xtime_03'])
				if(detail_json['int08_12'] > 0): ##启用告警
					clas = 1
				else:
					clas = 0
				if detail_json['xtime_02']==None:
					detail_json['int08_03']='1'
				else:
					time_now=time.time()
					time_old=time.mktime(time.strptime(detail_json['xtime_02'].split('+')[0].replace('T',' '),'%Y-%m-%d %H:%M:%S'))
					if (time_now-time_old)>300 and str(detail_json['int08_03'])=='0':
						detail_json['int08_03']='2';
				if logtype != 3 and logtype != '3':
					for pro in pro_l:
						if pro[0] == detail_json['int32_01']:
							detail_json['int32_01'] = pro[1]
					for o in detail_json:
						if o == "orderitem":
							continue
						field = o.split('_')[0];
						index = o.split('_')[1];
						if o.find('int08') >=0 and (index == '11' or index == '14' or index == '03' or index == '15'):
							detail_json[o] = StrClas(field,index,str(detail_json[o]),0,clas)
						if o == 'int64_15':
							num_tmp = hex(int(detail_json[o]))
							detail_json[o] = StrClas(field,index,int(detail_json[o]),clas)
						if o == 'int08_11':
							if detail_json['int08_12'] == 1:
								if detail_json[o] == 1:
									detail_json[o] = '已处理'
								elif detail_json[o] == 0:
									detail_json[o] = '未处理'
							else:
								detail_json[o] = ''
				else:
					for o in detail_json:
						if o == 'int32_01' or o=='int08_12':
							field = o.split('_')[0];
							index = o.split('_')[1];
							detail_json[o] = StrClas(field,index,int(detail_json[o]),1,1)
						if o == 'int08_11':
							if detail_json['int08_12'] == 1:
								if detail_json[o] == 1:
									detail_json[o] = '已处理'
								elif detail_json[o] == 0:
									detail_json[o] = '未处理'
							else:
								detail_json[o] = ''
				detail_json["xtime_03"]=str(detail_json["xtime_03"])
				detail_json["xtime_00"]=str(detail_json["xtime_00"])
				detail_json['DownloadEnable']=False
				detail_json['DeleteEnable']=False
				detail_json['IfReplay'] = False ##是否使用控件回放
				detail_json['IfReplayDrawing'] = False ##回放  字符回放（ssh等） 图形回放（RDP等）
				if  detail_json['str32_28']!=None and detail_json['str32_28']!='':
					detail_json['DownloadEnable']=True
					detail_json['IfReplay'] = True
					pro = detail_json['str32_28'].split('/')[-2].upper()
					if pro =="RDP" or pro =="ACC" or pro =="VNC" or pro =="X11":
						detail_json['IfReplayDrawing'] = True
				elif detail_json['str32_28']!=None:
					if detail_json['int32_01']=='FTP' or detail_json['int32_01']=='SSH' or detail_json['int32_01']=='SFTP' or detail_json['int32_01']=='RDP':
						if detail_json['str32_01'].find('Save')!=-1:
							filename=detail_json['str32_01'].replace('Save ','',1)
							filepath='/usr/storage/.system/transf/ftp/'
							# if detail['int32_01']=='FTP':
							# 	filepath='/usr/storage/.system/transf/ftp/'
							# elif detail['int32_01']=='SFTP':
							# 	filepath='/usr/storage/.system/transf/ssh/'
							# else:
							# 	filepath='/usr/storage/.system/transf/rdp/'
							f_all=filepath+filename
							if os.path.exists(f_all):
								detail_json['DownloadEnable']=True
								detail_json['DeleteEnable']=True	
				detail = json.dumps(detail_json)
								
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql="select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
				curs.execute(sql)
				protocol = curs.fetchall()[0][0]
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

		t = "search_log.html"
		if a1=="11":
			return render_template(t,f1="more_ses_info_",se=session,us=userCode,m1=a1,m2=a2,m3=a3,m4=a4,m5=a5,m6=a6,taskid=xtime_00,logtype=logtype,i1=index_total,p1=page,config=config,detail=detail,protocol=protocol,perm=perm)
		elif a1=="10":
			return render_template(t,f1="monitor_",se=session,us=userCode,m1=a1,m2=a2,m3=a3,m4=a4,m5=a5,m6=a6,taskid=xtime_00,logtype=logtype,i1=index_total,p1=page,config=config,detail=detail,protocol=protocol,perm=perm)
	if tasktype == "2":
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
		sql = "select public.\"PGetLogFieldConfig\"(1);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_1 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_1 = service_1 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_1 = service_1[:-1]
		
		sql = "select public.\"PGetLogFieldConfig\"(2);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_2 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_2 = service_2 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_2 = service_2[:-1]
		curs.close()
		conn.close()
		t = "more_ses_info.html"
		_power=PGetPermissions(userCode)
		_power=str(_power)
		_power_json = json.loads(_power);
		monitor_flag1 = 0
		monitor_flag2 = 0
		for one in _power_json:
	 		if one['SubMenuId'] == 1:#数据监控
	 			if one['Mode'] == 2:#管理
	   				monitor_flag1 = 2
	                        else:
	 				monitor_flag1 = 1
	  		elif one['SubMenuId'] == 7:#系统监控
		                if one['Mode'] == 2:#管理
		                         monitor_flag2 = 2
		                else:
		                         monitor_flag2 = 1
		return render_template(t,se=session,us=userCode,a1=a1,a2=a2,a3=a3,a4=a4,a5=a5,a6=a6,p1=page,service_1=service_1,service_2=service_2,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2)
	if tasktype == "3":
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			
		sql = "select public.\"PGetLogFieldConfig\"(1);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_1 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_1 = service_1 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_1 = service_1[:-1]
		
		sql = "select public.\"PGetLogFieldConfig\"(2);";
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		service_2 = ""
		results_json = json.loads(results)
		for result in results_json:
			service_2 = service_2 +result['Content']+','+result['Translation'] +','+str(result['Id']) +';'
		service_2 = service_2[:-1]
		curs.close()
		conn.close()
		t = "more_ses_info.html"
		_power=PGetPermissions(userCode)
		_power=str(_power)
		_power_json = json.loads(_power);
		monitor_flag1 = 0
		monitor_flag2 = 0
		for one in _power_json:
	 		if one['SubMenuId'] == 1:#数据监控
	 			if one['Mode'] == 2:#管理
	   				monitor_flag1 = 2
	                        else:
	 				monitor_flag1 = 1
	  		elif one['SubMenuId'] == 7:#系统监控
		                if one['Mode'] == 2:#管理
		                         monitor_flag2 = 2
		                else:
		                         monitor_flag2 = 1
		return render_template(t,se=session,us=userCode,a1=a1,a2=a2,a3=a3,a4=a4,a5=a5,a6=a6,p1=page,service_1=service_1,service_2=service_2,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2)
	curs.close()
	conn.close()

#协同
@user_data.route('/get_token_remote_Monitor',methods=['GET','POST'])
def get_token_remote_Monitor():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
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

	url_str = request.form.get('a1')
	bhname = request.form.get('a5')
	pid = request.form.get('a3')
	protoname = request.form.get('a4')
	param_str = request.form.get('a7')
	Type = request.form.get('a8')#1 协同 2 监控
	Pro = request.form.get('a9') #1 RDP 0 其他
	json_data = {"username":"","password_hash":"","password_salt":"","connection_name":"","protocol":"","param":[]}
	json_data['username'] =  bhname
	#password_salt
	key = hashlib.sha256(uuid.uuid4().hex).hexdigest().upper();
	#password_hash
	pwd = hashlib.sha256(session + str(key)).hexdigest().upper();
	json_data['password_hash'] = pwd
	json_data['password_salt'] = key
	json_data['connection_name'] = session
	if Pro == '1':
		json_data['protocol'] = 'RDP'
	else:
		json_data['protocol'] = 'TELNET'
	if str(Type) == "1":
		json_data['diskmap'] = False
		json_data['read_only'] = False
	else:
		json_data['diskmap'] = False
		json_data['read_only'] = True
	json_data['not_change_protocol'] = True


	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select \"ColorScheme\" from public.\"User\" where \"UserCode\" = '%s';" %(system_user)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results == 1:
				ColorScheme = {"name":"color-scheme","value":"green-black"}
			elif results == 2:
				ColorScheme = {"name":"color-scheme","value":""}
			elif results == 0:
				ColorScheme = {"name":"color-scheme","value":"white-black"}
			param_str = json.loads(param_str)
			param_str.append(ColorScheme)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

	json_data['param'] = param_str

	try:
		with pyodbc.connect(StrSqlConn('BH_REMOTE')) as conn:
			curs = conn.cursor()
			sql = 'select public."PCreateNewConnection"(E\'%s\')' % (MySQLdb.escape_string(json.dumps(json_data)).decode('utf-8'))
			curs.execute(sql)
			conn.commit()
			try:
				ssl._create_default_https_context = ssl._create_unverified_context
                                if common.get_server_cluster_type() == "gluster" or common.get_server_cluster_type == "double":
                                        url = url_str + '/bhremote/api/tokens'
                                else:
                                        port = url_str.split(':')[-1]
                                        url = 'https://127.0.0.1:'+port+'/bhremote/api/tokens'
				#username = system_user+'@'+bhname+'@'+pid+':'+protoname+'@ad'
				#  bhuser@bhname@pid:proto@ad
				post_data = "username="+bhname+"&password="+session
				req = urllib2.urlopen(url, post_data)
				content = req.read()
				return content
			except Exception,e:
				conn.rollback()
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#取登录用户姓名
@user_data.route('/get_user_name',methods=['GET','POST'])
def get_user_name():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
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
			curs.execute("select \"User\".\"UserName\" from public.\"User\" where \"User\".\"UserCode\"='%s';" %(usercode))
			username = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":\"%s\"}" %(username)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
#取登录用户姓名 和账号
@user_data.route('/get_user_name2',methods=['GET','POST'])
def get_user_name2():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
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
			curs.execute("select \"User\".\"UserName\" from public.\"User\" where \"User\".\"UserCode\"='%s';" %(usercode))
			username = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":\"%s\",\"usercode\":\"%s\"}" %(username,usercode)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
#下载日志文件
@user_data.route('/download_file_log',methods=['GET','POST'])
def download_file_log():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	FromFlag = request.form.get('a10')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(usercode,FromFlag) == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	logid = request.form.get('a1')
	filename = request.form.get('a2')
	downloadType = request.form.get('a3')  #1->replay file 2->ftp transfer file
	try:
		if downloadType == '1':
			TypeStr = "回放文件"
			path_tmp = '/usr/storage/.system/replay/'+filename
			fdir = path_tmp
			path_array = path_tmp.split('/')
			filename = path_array[-1]
			path_array.pop()
			filepath = '/'.join(path_array)
		elif downloadType == '2':
			TypeStr = "FTP传输文件"
			filename = filename
			filepath = '/usr/storage/.system/transf/ftp/'
			fdir = filepath + filename

		#检查目录是否存在
		if not os.path.exists(fdir):
			system_log(usercode,"下载%s：%s" % (TypeStr,filename),"失败：文件不存在",FromFlag)
			return "{\"Result\":false,\"ErrMsg\":\"文件不存在(%d)\"}" %(sys._getframe().f_lineno)

		system_log(usercode,"下载%s：%s" % (TypeStr,filename),"成功",FromFlag)

		return send_from_directory(filepath,filename,as_attachment=True)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#下载前检查日志文件是否存在
@user_data.route('/download_fileCheck',methods=['GET','POST'])
def download_fileCheck():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	FromFlag = request.form.get('a10')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(usercode,"运维概要") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	logid = request.form.get('a1')
	filename = request.form.get('a2')
	downloadType = request.form.get('a3')  #1->replay file 2->ftp transfer file
	try:
		if downloadType == '1':
			TypeStr = "回放文件"
			path_tmp = '/usr/storage/.system/replay/'+filename
			fdir = path_tmp
			path_array = path_tmp.split('/')
			filename = path_array[-1]
			path_array.pop()
			filepath = '/'.join(path_array)
		elif downloadType == '2':
			TypeStr = "FTP传输文件"
			filename = filename
			filepath = '/usr/storage/.system/transf/ftp/'
			fdir = filepath + filename

		#检查目录是否存在
		if not os.path.exists(fdir):
			system_log(usercode,"下载%s：%s" % (TypeStr,filename),"失败：文件不存在",FromFlag)
			return "{\"Result\":false,\"ErrMsg\":\"文件不存在(%d)\"}" %(sys._getframe().f_lineno)
		system_log(usercode,"下载%s：%s" % (TypeStr,filename),"成功",FromFlag)
		return "{\"Result\":true,\"Path\":\"%s\"}" %(filepath)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

# 删除日志传输文件
@user_data.route('/delete_file_log',methods=['GET','POST'])
def delete_file_log():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	FromFlag = request.form.get('a10')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	logid = request.form.get('a1')
	filename = request.form.get('a2')
	
	if check_role(usercode,FromFlag) == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		filename = filename
		fdir = '/usr/storage/.system/transf/ftp/'+filename
		#检查目录是否存在
		if not os.path.exists(fdir):
			system_log(usercode,"删除FTP传输文件：%s" % (filename),"失败：文件不存在",FromFlag)
			return "{\"Result\":false,\"ErrMsg\":\"文件不存在(%d)\"}" %(sys._getframe().f_lineno)

		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

		# lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		# ret = lib.delete_ftp_file(filename)			#执行函数

		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				curs.execute("select \"RecordId\",\"Size\" FROM private.\"FtpRecordFile\" WHERE \"Name\"=E'%s';" %(filename))
				results = curs.fetchall()[0]
				RecordId = results[0]
				Size = results[1]
				curs.execute("DELETE FROM private.\"FtpRecordFile\" WHERE \"RecordId\" = E'%s';" %(RecordId))

				curs.execute("UPDATE private.\"FtpRecordTotalSize\" SET \"TotalSize\" = \"TotalSize\" - %d WHERE \"Id\" = 1;" %(int(Size)))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

		tmp = os.remove(fdir)
		system_log(usercode,"删除FTP传输文件：%s" % (filename),"成功",FromFlag)
		return "{\"Result\":true}"

	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
###yt
# 阻断
@user_data.route('/block_session',methods=['GET','POST'])
def block_session():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	pid = request.form.get('p1')
	serverid = request.form.get('s1')
	sessid = request.form.get('s2')
	username ='';
	## 获取当前 用户 和 姓名
	with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
		curs = conn.cursor()
		curs.execute("select \"User\".\"UserName\" from public.\"User\" where \"User\".\"UserCode\"='%s';" %(usercode))
		username = curs.fetchall()[0][0]	
	###def BlockProxy(serverid, pid, usr, dbcode=5)
	###usr = 会话标识@账号@姓名
	usr = sessid +"@"+usercode+"@"+username
	ret = BlockProxy(serverid,pid,usr)
	if ret !=0:
		return "{\"Result\":false,\"ErrMsg\":\"阻断失败(%d)\"}" %(sys._getframe().f_lineno)
	else:
		content = "[global]\nclass = taskglobal\ntype = send_pid\npid=%s\nnumber=40\n" %(pid)
		ss = task_client.task_send(serverid, content)
		if ss == False:
			return "{\"Result\":false,\"ErrMsg\":\"阻断失败：%s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			
		return "{\"Result\":true,\"ErrMsg\":\"\"}"

#获取数据分布data2
@user_data.route('/get_system_outline_data2',methods=['GET','POST'])
def get_system_outline_data2():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheckLocal(session,client_ip);
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
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select count(*) from public.\"User\";"
	debug(sql)
	curs.execute(sql)
	OperationalUsers = str(curs.fetchall()[0][0])

	sql = "select count(*) from public.\"Host\";"
	debug(sql)
	curs.execute(sql)
	OperationalHosts = str(curs.fetchall()[0][0])

	sql = "select count(*) from public.\"AccessStrategy\";"
	debug(sql)
	curs.execute(sql)
	AccessStrategy = str(curs.fetchall()[0][0])

	sql = "select count(*) from public.\"CmdAuth\";"
	debug(sql)
	curs.execute(sql)
	DirectiveStrategy = str(curs.fetchall()[0][0])

	sql = "select count(*) from public.\"WorkOrder\";"
	debug(sql)
	curs.execute(sql)
	WorkOrderStrategy = str(curs.fetchall()[0][0])

	get_server_global_json = "{\"serverid\":null,\"searchstring\":null,\"ip\":null,\"type\":null,\"cpu\":null,\"limitrow\":null,\"offsetrow\":null}"
	sql='select public."PGetServerGlobal"(E\'%s\');'%(get_server_global_json)
	curs.execute(sql)
	results = curs.fetchall()[0][0]
	'''
	{"totalrow":1,"data":[
	    {
	        "ip": "127.0.0.1",
	        "cpu": "intel",
	        "core": 8,
	        "rack": 0,
	        "type": "master/app/database",
	        "phymem": 6144,
	        "run_app": 1,
	        "run_gtm": 0,
	        "run_mds": 0,
	        "run_mon": 0,
	        "run_coor": 0,
	        "server_id": 1,
	        "max_disk_count": 0,
	        "raid_disk_count": 0
	    }
	]}
	'''
	SeviceStatus = 1 # 1正常
	ServiceNum = 0
	ServiceDetail = []
	g_cluster_type = common.get_server_cluster_type();
	if g_cluster_type=='gluster' or g_cluster_type == 'double':
		if g_cluster_type == 'double':
			GlsterMaster=None
		else:
			(error,GlsterMaster)=GetGlsterMaster(None, common.get_server_id(), server=common.get_inner_master_ip(), listen=6379, dbcode=2)
			if error==0:
				pass
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sql='select client_addr, pg_xlog_location_diff(pg_current_xlog_location(),replay_location) from pg_stat_replication;'
		curs.execute(sql)
		result = curs.fetchall()
		sql='select * from pg_replication_slots;'
		curs.execute(sql)
		node_result = curs.fetchall()
	for i in json.loads(results)['data']:
		ServiceDetail1 = {"ServerIP":"192.168.0.1","ServerID":1,"Status":1} # 1正常
		ServiceNum = ServiceNum + 1
		sid = str(i['server_id'])
		(error,_time)=HstGet(None,sid)
		if error!=0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		if _time==None:
			ServiceDetail1['ServerIP'] = i['ip']
			ServiceDetail1['ServerID'] = i['server_id']
			ServiceDetail1['Status'] = 0
			SeviceStatus = 0
			ServiceDetail.append(ServiceDetail1)
		else:
			_time_local=time.time()
			if (_time_local-int(_time))<=300:
				_time='1'
				if g_cluster_type=='gluster' or g_cluster_type == 'double':
					if sid==GlsterMaster or GlsterMaster==None:
						pass
					else:
						if g_cluster_type == 'double':
							if (len(node_result))<1:
								_time='0'
								SeviceStatus=0
							else:
								node_result_item=node_result[0]
								_time='0'
								if node_result_item[5]!=u'0':#true
									if len(result)<1:
										_time='0'
										SeviceStatus=0
									else:
										result_item=result[0]
										sid_value=int(result_item[1])
										if sid_value<3000000 and sid_value>0:
											_time='1'
										else:
											_time='0'
											SeviceStatus=0
								else:#false
									_time='0'
									SeviceStatus=0
						else:
							_time='0'
							for node_result_item in node_result:
								if sid==node_result_item[0][4:5]:
									if node_result_item[5]!=u'0':#true
										for result_item in result:
											if sid==result_item[0].split('.')[-1]:
												sid_value=int(result_item[1])
												if sid_value<3000000 and sid_value>0:
													_time='1'
												else:
													_time='0'
													SeviceStatus=0
												break
									else:#false
										_time='0'
										SeviceStatus=0
									break
							if _time=='0':
								SeviceStatus=0
			else:
				_time='0'
				SeviceStatus = 0
			ServiceDetail1['ServerIP'] = i['ip']
			ServiceDetail1['ServerID'] = i['server_id']
			ServiceDetail1['Status'] = _time
			ServiceDetail.append(ServiceDetail1)

	data_list = {"OperationalUsers":"123","OperationalHosts":"123","AccessStrategy":"123","DirectiveStrategy":"123","WorkOrderStrategy":"123","SeviceStatus":"123","ServiceNum":"123","ServiceDetail":[]}
	data_list['OperationalUsers'] = OperationalUsers
	data_list['OperationalHosts'] = OperationalHosts
	data_list['AccessStrategy'] = AccessStrategy
	data_list['DirectiveStrategy'] = DirectiveStrategy
	data_list['WorkOrderStrategy'] = WorkOrderStrategy
	data_list['SeviceStatus'] = SeviceStatus
	data_list['ServiceNum'] = ServiceNum
	data_list['ServiceDetail'] = ServiceDetail

	return "{\"Result\":true,\"data\":[%s]}" % json.dumps(data_list)

#获取告警信息
@user_data.route('/get_WarnMsg',methods=['GET','POST'])
def get_WarnMsg():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	limitrow = request.form.get('a1')
	if not limitrow.isdigit():
		return '',403
	offsetrow = request.form.get('a2')
	if not offsetrow.isdigit():
		return '',403
	condition_time = request.form.get('a3')
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

	if condition_time != '0':
		time1 = condition_time.split('**')[0]
		time2 = condition_time.split('**')[1]
		try:
			if ':' in time1:
				time.strptime(time1[:-3], "%Y-%m-%d %H:%M:%S")
			else:
				time.strptime(time1, "%Y-%m-%d")
			if ':' in time2:
				time.strptime(time2[:-3], "%Y-%m-%d %H:%M:%S")
			else:
				time.strptime(time2, "%Y-%m-%d")
		except:
			return '',403
	try:
		conn = pyodbc.connect(StrSqlConn('BH_DATA'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT xtime_02,str32_04,str32_30,int08_11,xtime_00 FROM public.adm_table WHERE (int08_12=1 and xtime_02 between E'%s' and E'%s') ORDER BY int08_11 asc nulls first,xtime_00 DESC LIMIT %s OFFSET %s;" %(time1,time2,limitrow,offsetrow)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	data_total = []
	for result in results:
		# if result[1] > 0:
		timedata = result[0]
		moudule = result[1]
		msg = result[2].replace('\"','\\"')
		re = result[3]
		id = result[4]
		data = "{\"time\":\"%s\",\"moudule\":\"%s\",\"msg\":\"%s\",\"result\":\"%s\",\"id\":\"%s\"}" %(timedata,moudule,msg,re,id)
		data_total.append(data)
	data_str = ",".join(data_total)

	sql="SELECT count(*) FROM public.adm_table WHERE (int08_12=1 and xtime_02 between E'%s' and E'%s');" %(time1,time2)
	curs.execute(sql)
	totalrow = curs.fetchall()[0][0]

	sql="SELECT count(*) FROM public.adm_table WHERE (int08_12=1 and int08_11=1 and xtime_02 between E'%s' and E'%s');" %(time1,time2)
	curs.execute(sql)
	done = curs.fetchall()[0][0]

	pending = int(totalrow) - int(done)

	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":[%s],\"totalrow\":%s,\"solved\":%s,\"pending\":%s}"% (data_str,str(totalrow),str(done),str(pending))

#修改日志状态
@user_data.route('/set_logstat',methods=['GET','POST'])
def set_logstat():
	session = request.form.get('a0')
	type_ = request.form.get('a1')
	logid = request.form.get('a2')
	mark = request.form.get('a3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if str(mark) == 'None':
		mark = ""
	if type_.isdigit():
		type_int = int(type_)
		if type_int in [1,2,3]:
			pass
		else:
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		curs = conn.cursor()
		curs.execute("select \"User\".\"UserName\" from public.\"User\" where \"User\".\"UserCode\"='%s';" %(usercode))
		username = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn:
			curs = conn.cursor()
			curs.execute('select public."PSetWarnFlag"(%d,%d,E\'%s\',E\'%s\',E\'%s\');' %(int(logid),int(type_),usercode,username,mark))
			result = curs.fetchall()[0][0]
			if str(result) == '1':
				conn.commit()
				return "{\"Result\":true,\"UserCode\":\"%s\",\"UserName\":\"%s\"}" %(usercode,username)
			else:
				return "{\"Result\":false}"

	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@user_data.route("/mark_layer", methods=['GET', 'POST'])
def mark_layer():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	s_id=request.args.get('a1')
	type=request.args.get('a2')
	title=request.args.get('a3')
	if s_id < 0 :
		s_id = '0'
	if type < 0 :
		type = '0'
	if title < 0 :
		type = '实时监控'		
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	return render_template('markLayer.html',se=session,s_id = s_id,title = title)
@user_data.route("/pwdChange_time", methods=['GET', 'POST'])
def pwdChange_time():
	session = request.form.get('a0')
	UserId = request.form.get('a1')
	Mid = request.form.get('a2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	#2018/4/28 15:21:40
	NowTime=int(time.time())
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='SELECT u."PwdFileApprove" FROM public."User" u where u."UserId"=%s;'%(UserId)
			curs.execute(sql)
			PwdFileApprove = curs.fetchall()[0][0]
			sql='SELECT m."VerificationCode" FROM private."Message" m where m."MessageId"=%s;'%(Mid)
			curs.execute(sql)
			VerificationCode = curs.fetchall()[0][0]
			new_arr=[]
			if PwdFileApprove!=None or PwdFileApprove!='':
				PwdFileApprove=PwdFileApprove.split('\n')
				for PwdFileApprove_i in PwdFileApprove:
					i_arr=PwdFileApprove_i.split(':')
					if i_arr[0]==VerificationCode:
						new_arr.append('%s:%s'%(NowTime,i_arr[1]))
					else:
						new_arr.append(PwdFileApprove_i)
			curs.execute("update \"User\" set \"PwdFileApprove\" = E'%s' where \"UserId\"=%s;" %('\n'.join(new_arr),UserId))
			curs.commit()
			return 'true'
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	#sess = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	#if sess < 0:
	#        sess = ""
	#client_ip = request.remote_addr
	#(error,us,mac) = SessionCheckLocal(sess,client_ip);
	#(error,us,mac) = SessionCheck(sess,client_ip);
	#if error < 0:
	#        return "{\"Result\":false,\"info\":\"系统异常(%d): %d\"}" %  (ERRNUM_MODULE_top + 1,error)
	#elif error > 0:
	#        if error == 2:
	#                return "{\"Result\":false,\"info\":\"非法访问(%d): %d\"}" % (ERRNUM_MODULE_top + 2,error)
	#        else:
	#                return "{\"Result\":false,\"info\":\"系统超时(%d): %d:%s\"}" % (ERRNUM_MODULE_top + 2,error,str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(MySQLdb.escape_string(us))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if result==None:
				result='[]'
			else:
				result_json = json.loads(result);
				json_list_mode1 = [];
				json_list_mode2 = [];
				json_list_mode = [];
				result = []
				for one in result_json:
					if one['Mode'] == 2:
						json_list_mode2.append(one['SubMenuId'])
					if one['Mode'] == 1:
						json_list_mode1.append(one['SubMenuId'])
				for one in json_list_mode1:
					if one in json_list_mode2:
						json_list_mode.append(one)
				#json_list_mode = json_list_mode + json_list_mode2
				for one in result_json:
					if one['SubMenuId'] in json_list_mode and one['Mode'] == 1:
						one['SubMenuId'] = -1
				result = json.dumps(result_json)
				#result = str(result_json)
	except pyodbc.Error,e:
		return "[]"
	return str(result)

#获取（监控、协同）会话的连接参数
@user_data.route('/get_Param',methods=['GET','POST'])
def get_Param():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	UserCode = request.form.get('a1')
	ServerIP = request.form.get('a2')
	ProtocolName = request.form.get('a3')
	ServerUser = request.form.get('a4')
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

	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql="SELECT a.\"ServiceName\",a.\"ConnMode\",a.\"ConnParam\",a.\"ClientName\" FROM private.\"HostAccessCfg\" a WHERE a.\"UserCode\"=E'%s' AND a.\"ServerIP\"=E'%s' AND a.\"ProtocolName\"=E'%s' AND a.\"ServerUser\"=E'%s';" %(UserCode,ServerIP,ProtocolName,ServerUser.replace('\\', '\\\\'))
	try:
		curs.execute(sql)
		result = curs.fetchall()
		return "{\"Result\":true,\"ServiceName\":\"%s\",\"ConnMode\":\"%s\",\"ConnParam\":\"%s\",\"ClientName\":\"%s\"}"% (str(result[0][0]),str(result[0][1]),str(result[0][2]),str(result[0][3]))
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)




