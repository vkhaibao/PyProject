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
import base64
from bhcomm import StrClas
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import defines
from logbase import task_client
from bhcomm import StrClas
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
connect_session = Blueprint('connect_session',__name__)

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
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

def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)

def proto_all():
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
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
	
@connect_session.route('/session_html_show',methods=['GET', 'POST'])
def session_html_show():
	se = request.args.get('a0')
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	return render_template('connect_session.html')
	
@connect_session.route('/session_list',methods=['GET', 'POST'])
def session_list():			
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	mpage = request.form.get('z1')
	cpage = request.form.get('z2')
	
	offsetrow = (int(cpage)-1)*int(mpage)
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn,conn.cursor() as curs,pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn1,conn1.cursor() as curs1:
			sql = "SELECT count(*) FROM public.ses_table WHERE str32_22='%s' AND int08_03=0" % usercode
			curs.execute(sql)
			countall = curs.fetchall()[0][0]
			
			sql = "SELECT xtime_04,xtime_05,int32_01,int08_03,str32_22,str32_23,ip_01,str32_25,str32_00,xtime_03,int32_14,str32_26,int08_14,str32_28 FROM public.ses_table WHERE str32_22='%s' AND int08_03=0 ORDER BY xtime_04 DESC LIMIT %s OFFSET %s;" %(usercode,mpage, offsetrow)
			curs.execute(sql)
			results = curs.fetchall()
			rowcount = int(curs.rowcount)
			if results == None:
				#return "{\"Result\":true,\"data\":[],\"totalrow\":%d}" % countall
				return "{\"Result\":true,\"data\":[],\"totalrow\":0}"
			else:
				count = 0
				data_str = ""
				proto_list = proto_all()
				proto_list = json.loads(proto_list)['data']
				
				while count < rowcount:
					starttime = results[count][0]
					endtime = results[count][1]
					log_type = results[count][2]
					for proto in proto_list:
						if log_type == proto['ProtocolId']:
							log_type = proto['ProtocolName']
							break
					'''
					if log_type != "SSH" and log_type != "TELNET" and log_type != "RLOGIN" and log_type != "RDP":
						count = count + 1
						countall = countall - 1
						continue
					'''
					if endtime != None:
						#最后更新时间超过300秒显示为断开
						systemTime1 = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
						timeArray = time.strptime(systemTime1, "%Y-%m-%d %H:%M:%S")
						timeArray1 = time.strptime(str(endtime), "%Y-%m-%d %H:%M:%S")
						timestamp = time.mktime(timeArray)
						timestamp1 = time.mktime(timeArray1)
						Seconds = timestamp - timestamp1
						if Seconds > 300:
							count = count + 1
							countall = countall - 1
							continue

					status = results[count][3]
					'''
					if(results[count][12] > 0): ##未启用告警
						clas = 1
					else:
						clas = 0
					status = StrClas('int08','03',status,clas)
					'''
					operationaluser = results[count][4].encode('utf-8').replace('\\',"\\\\")
					operationalusername = results[count][5].encode('utf-8').replace('\\',"\\\\")
					serverip = results[count][6]
					approvalusername = results[count][7].encode('utf-8').replace('\\',"\\\\")
					serverusername = results[count][8].encode('utf-8').replace('\\',"\\\\")
					number = results[count][9]
					pid = results[count][10]
					BlockingUsers = results[count][11].encode('utf-8').replace('\\',"\\\\")
					Playback_file = results[count][13]
					if approvalusername == '':
						approvalusername == None
						
					sql = "select public.\"PGetMessage\"(E'%s',null,null,null,null,null,3,E'%s')" % (usercode,number)
					curs1.execute(sql)
					message = curs1.fetchall()[0][0].encode('utf-8')
					data = "{\"Number\":\"%s\",\"StartTime\":\"%s\",\"EndTime\":\"%s\",\"Type\":\"%s\",\"Status\":\"%s\",\"OperationalUser\":\"%s\",\"OperationalUserName\":\"%s\",\"ServerIP\":\"%s\",\"ApprovalUserName\":\"%s\",\"ServerUserName\":\"%s\",\"PId\":%d,\"BlockingUsers\":\"%s\",\"MessAge\":%s,\"Playback_file\":\"%s\"}" %(number,starttime,endtime,log_type,status,operationaluser,operationalusername,serverip,approvalusername,serverusername,pid,BlockingUsers,message,Playback_file)
					
					data_str = data_str + data + ','
					count = count + 1
				return "{\"Result\":true,\"data\":[%s],\"totalrow\":%d}" % (data_str[:-1],countall)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@connect_session.route('/PSave_Message',methods=['GET', 'POST'])
def PSave_Message():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	data = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
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
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			data = json.loads(data)
			Title_arr=data['Title'].split(':')
			if len(Title_arr)==2:
				Title_arr[1]=str(client_ip)+'->'+Title_arr[1]
			data['Title']=':'.join(Title_arr)
			sql = "select \"UserId\" from public.\"User\" where \"UserCode\"='%s'" % usercode
			curs.execute(sql)
			data['SenderId'] = curs.fetchall()[0][0]
			data['Sender'] = usercode
			sql = "select public.\"PSaveMessage\"(E'%s')" % MySQLdb.escape_string(json.dumps(data)).decode('utf-8')
			curs.execute(sql)
			result = curs.fetchall()[0][0].encode('utf-8')
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@connect_session.route('/cancel_mess',methods=['GET', 'POST'])
def cancel_mess():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	messid = request.form.get('z1')
	pid = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "update private.\"Message\" set \"ProcessStatus\"=3 where \"MessageId\"=%s" % messid
			curs.execute(sql)
			task_content = '[global]\nclass = kill_connect\ntype = execute_cmd\npid=%s\nsignal=%d\n' % (pid,41)
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
			conn.commit()
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@connect_session.route('/get_request_user_list',methods=['GET', 'POST'])
def get_request_user_list():			
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetUser\"(null,5,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
