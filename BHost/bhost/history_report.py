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
import datetime
import calendar
import base64
import shutil  
import time
import copy
from htmlencode import HtmlEncode
from generating_log import system_log

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from urllib import unquote
from generating_log import system_log
from index import PGetPermissions
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader 
import xml.etree.ElementTree as ET
from logbase import defines
from logbase import task_client
from htmlencode import parse_sess,check_role
history_report = Blueprint('history_report',__name__)

ERRNUM_MODULE_report = 1000
UPLOAD_FOLDER = '/var/www/manage/html/images'

PREFIX_RPT	= "/usr/storage/.system/report/"
PREFIX_RPT_DRES = PREFIX_RPT + "Dynamic/"
PREFIX_RPT_SRES = PREFIX_RPT + "Static/"
reload(sys)
sys.setdefaultencoding('utf-8')

MAX_LINE = 10000;

def debug(c):
	return 0
	path = "/var/tmp/debugyt.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

def debug1(c):
	return 0
	path = "/var/tmp/debugzqy.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

def checkaccount(account):
	p = re.compile(u'^[\w\.\-]+$')
	if p.match(account):
		return True
	else:
		return False
		
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
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
		
def NextExecuteTime(type):
	t = time.localtime(time.time())
	now_time = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00', t),'%Y-%m-%d %H:%M:%S'))
	if type == 1:#Day
		next_time = datetime.date.fromtimestamp(now_time) + datetime.timedelta(days=1)
	elif type == 2:#WEEK
		now_time = datetime.date.fromtimestamp(now_time)
		week_time = now_time.weekday()
		next_time = now_time + datetime.timedelta(7-week_time)
	elif type == 3:#MONTH
		now_time = datetime.date.fromtimestamp(now_time)
		first_day = datetime.date(now_time.year, now_time.month, 1)
		now_days = calendar.monthrange(now_time.year,now_time.month)[1]
		next_time = first_day + datetime.timedelta(days=now_days)
	next_time = "'%s'" % next_time.strftime("%Y-%m-%d 00:00:00")
	return next_time
		
#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

#获取所有协议	
def proto_all():
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"查询日志字段失败(%d)\"}"% (sys._getframe().f_lineno)
			result = curs.fetchall()[0][0].encode('utf-8')
			return result
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
@history_report.route('/report_task',methods=['GET', 'POST'])
def report_task():
	a0=request.form.get('a0')
	module_name=request.form.get('module_name')
	if module_name<0:
		module_name=request.args.get('module_name')
		if module_name<0:		
			if a0<0:
				a0=request.args.get('a0')
				if a0<0:
					a0='运维报表-生成报表'
				else:
					a0='运维报表-历史报表'
			else:
				a0='运维报表-历史报表'
			module_name=a0
	se = request.form.get('se')
	if se < 0 or se == "":
		se = request.args.get('se')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	_power=PGetPermissions(userCode)
	_power_json = json.loads(str(_power));
	_power_mode = 1;
	_power8=1;
	_power9=1;
	_power11=1;
	for one in _power_json:
		if one['SubMenuId'] == 8:
			_power8 = one['Mode']
		if one['SubMenuId'] == 9:
			_power9 = one['Mode']
		if one['SubMenuId'] == 11:
			_power11 = one['Mode']
	if _power8 == 2 or _power9 == 2 or _power11 ==2:
		_power_mode = 2;
	_power_mode = 2;###备注 历史报表不做处理
	
	return render_template('report_task.html',module_name=module_name,se=se,us=userCode,_power_mode=_power_mode)

@history_report.route('/manage_report',methods=['GET', 'POST'])
def manage_report():
	se = request.form.get('se')
	if se < 0 or se == "":
		se = request.args.get('se')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	return render_template('manage_report.html',se=se,us=userCode)

#获取模板详情
@history_report.route('/report_condition',methods=['GET', 'POST'])
def report_condition():
	se = request.args.get('se')
	temp_id = request.args.get('z2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	_power=PGetPermissions(userCode)
	_power_json = json.loads(str(_power));
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	return render_template('report_condition.html',se=se,temp_id=temp_id,us=userCode,manage_power_id=manage_power_id)	

@history_report.route('/modify_template',methods=['GET', 'POST'])
def modify_template():
	se = request.args.get('se')
	temp_id = request.args.get('z2')
	back_type = request.args.get('z1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	_power = PGetPermissions(userCode)
	_power = str(_power)
	_power_json = json.loads(_power)
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	
	return render_template('modify_template.html',se=se,temp_id=temp_id,back_type=back_type,us=userCode,manage_power_id=manage_power_id)	

@history_report.route('/report_details',methods=['GET', 'POST'])
def report_details():
	se = request.args.get('se')
	temp_id = request.args.get('z2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	return render_template('report_details.html',se=se,temp_id=temp_id,us=userCode)	

@history_report.route('/read_report',methods=['GET', 'POST'])
def read_report():
	'''
	z1:1516628148_1516628146
	a0:1516628125301
	d1:0
	fy:HTML/DYNAMIC/-
	'''
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
	
	path = request.args.get('z1')
	eindex = request.args.get('i1')
	ifstatic = request.args.get('is')
	download  = request.args.get('d1')##download
	file_type = request.args.get('fy')##DOC/DYNAMIC/-
	taskid = request.args.get('taskid')##任务id
	fmt = request.args.get('fmt');
	xtime = request.args.get('xt');
	if eindex <0 or eindex == "":
		eindex = 1
	exp = request.args.get('e1')
	if exp <0 or exp == "":
		exp = 0
	if ifstatic <0 or ifstatic == "":
		ifstatic = 0
	if download <0 or download =="":
		download = 0;
	else:
		download = int(download);
	if file_type <0 or file_type == "":
		file_type = ""
		
	if download == 1:
		if ifstatic == 0:
                        path = PREFIX_RPT_DRES +'/'+userCode+'/'+ path
                else:         
                        path = PREFIX_RPT_SRES  +'/'+ path
		if file_type.find('DOC') >=0 or file_type.find('ODT') >=0:
			name = 'doc.tgz';
		if file_type.find('PDF') >=0:
			name = 'pdf.tgz';
		if file_type.find('RTF') >=0:
			name = 'rtf.tgz';
		if file_type.find('XLS') >=0:
			name = 'xls.tgz';
		return send_from_directory(path,name,as_attachment=True)
	else:		
		return render_template('read_report.html',se=session,path=path,eindex=eindex,exp=exp,ifstatic=ifstatic,taskid=taskid,fmt=fmt,xtime=xtime)		

@history_report.route('/scheduled_task_show',methods=['GET', 'POST'])
def scheduled_task_show():
	debug1('scheduled_task_show')
	se = request.args.get('se')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	module_name=request.args.get('module_name')
	if module_name<0:
		module_name=request.form.get('module_name')
	debug1('module_name:'+str(module_name))
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	_power=PGetPermissions(userCode)
	_power_json = json.loads(str(_power));
	_power_mode = 1;
	for one in _power_json:
		if one['SubMenuId'] == 11:
			_power_mode = one['Mode']
	return render_template('scheduled_task.html',module_name=module_name,se=se,us=userCode,_power_mode=_power_mode)

@history_report.route('/report_material_show',methods=['GET', 'POST'])
def report_material_show():
	se = request.form.get('se')
	if se == "" or se < 0:
		se = request.args.get('se')
	back_type = request.form.get("z2")
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	_power=PGetPermissions(userCode)
	_power_json = json.loads(str(_power));
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	return render_template('report_material.html',se=se,us=userCode,back_type=back_type,manage_power_id=manage_power_id)
	
@history_report.route('/report_hostgroup_show',methods=['GET', 'POST'])
def report_hostgroup_show():
	se = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	return render_template('report_hostgroup.html',se=se,us=userCode)
	
@history_report.route('/manage_template',methods=['GET', 'POST'])
def manage_template():
	se = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	return render_template('manage_template.html',se=se,us=userCode)

@history_report.route('/report_list',methods=['GET', 'POST'])
def report_list():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	curpage = request.form.get('z1')
	maxpage = request.form.get('z2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if curpage == "null":
		task_offset = "null"
	else:
		task_offset = (int(curpage)-1)*10
		
	if maxpage and str(maxpage).isdigit() == False:
		return '',403 	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetDataReportTask\"(null,E'%s',0,%s,%s)" % (userCode,maxpage,str(task_offset))
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			result = json.loads(results)
			
			for res in result['data']:
				Condition = res['Condition'];
				ctime = (Condition.split('<RptTime>')[1]).split('</RptTime>')[0]
				#debug(ctime);
				#debug(str(res['SubmitTime']))
				etime = long(time.mktime(time.strptime(res['SubmitTime'], '%Y-%m-%d %H:%M:%S')))
				#debug(str(etime));
				path = str(ctime) +"_" + str(etime);
				res['path'] = path;
			results = json.dumps(result);
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_6 删除任务)
@history_report.route('/report_delete',methods=['GET', 'POST'])
def report_delete():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type = request.form.get('z1')
	id_v = request.form.get('z2')
	type_name=request.form.get('z3')
	module_name=request.form.get('z4')
	if module_name<0:
		module_name='运维报表>生成报表'
	else:
		module_name=module_name.replace('-','>')
	if type_name<0:
		type_name='计划任务'
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(userCode,"报表管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				id_array = id_v[1:-1].split(',')
				succ_num=0
				fail_num=0
				all_arr=[]
				succ_arr=[]
				fail_arr=[]
				for id in id_array:
					sql = 'select "Condition","SubmitTime" from private."DataReportTask" where "TaskId" =%s;' %(id)
					curs.execute(sql);
					result_tmp = curs.fetchall();
					if not result_tmp:
						if not system_log(userCode,'删除%s'%type_name,'任务不存在',module_name):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"info\":\"系统异常: 任务不存在(%d)\"}" %(sys._getframe().f_lineno)
					else:
						Condition =  result_tmp[0][0].encode('utf-8');
						sum = ET.fromstring(Condition)
						name=sum.find('RptName').text
						#name = (Condition.split('<RptName>')[1]).split('</RptName>')[0]
						SubmitTime = result_tmp[0][1];
						all_arr.append(name+'-'+str(SubmitTime))
						ctime = (Condition.split('<RptTime>')[1]).split('</RptTime>')[0]
						etime = long(time.mktime(time.strptime(str(SubmitTime), '%Y-%m-%d %H:%M:%S')))
						path_dir = str(ctime) +"_" + str(etime);
						path = PREFIX_RPT_DRES + userCode +"/" + path_dir +"/";
						content = "[global]\nclass = taskglobal\ntype = deldirs\npath=%s\n" %(path)
						ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
						if ss == False:
							return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
					
					curs.execute("select public.\"PDeleteDataReportTask\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						fail_num+=1
						fail_arr.append(name+'-'+str(SubmitTime))
						conn.rollback();
						if not system_log(userCode,'删除%s：%s' % (type_name,name+'-'+str(SubmitTime)),results['ErrMsg'],module_name):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return result
					else:
						succ_arr.append(name+'-'+str(SubmitTime))
						succ_num+=1
				if not system_log(userCode,'删除%s：%s' % (type_name,'、'.join(all_arr)),'成功',module_name):	
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":true}"
			else:
				sql = 'select "Condition","SubmitTime" from private."DataReportTask" where "TaskId" =%s;' %(id_v)
				curs.execute(sql)
				result_tmp = curs.fetchall()
				if not result_tmp:
					if not system_log(userCode,'删除%s'%type_name,'任务不存在',module_name):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"info\":\"系统异常: 任务不存在(%d)\"}" %(sys._getframe().f_lineno)
				else:
					Condition =  result_tmp[0][0].encode('utf-8');
					#name=sum.find('RptName').text
					sum = ET.fromstring(Condition)
					name=sum.find('RptName').text
					#name = (Condition.split('<RptName>')[1]).split('</RptName>')[0]
					SubmitTime = result_tmp[0][1];
					ctime = (Condition.split('<RptTime>')[1]).split('</RptTime>')[0]
					etime = long(time.mktime(time.strptime(str(SubmitTime), '%Y-%m-%d %H:%M:%S')))
					path_dir = str(ctime) +"_" + str(etime);
					path = PREFIX_RPT_DRES + userCode +"/" + path_dir +"/";
					content = "[global]\nclass = taskglobal\ntype = deldirs\npath=%s\n" %(path)
					ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
					if ss == False:
						if not system_log(userCode,'删除%s：%s' % (type_name,name+'-'+str(SubmitTime)),'系统异常',module_name):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
		
				curs.execute("select public.\"PDeleteDataReportTask\"(%d);"%(int(id_v)))
				results = curs.fetchall()[0][0].encode('utf-8')
				if not system_log(userCode,'删除%s：%s' % (type_name,name+'-'+str(SubmitTime)),'成功',module_name):	
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)

#(zqy_7)		
@history_report.route('/Save_DataReportGlobalCfg',methods=['GET', 'POST'])
def Save_DataReportGlobalCfg():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	# f_id  ID
	f_id = request.form.get('z1')
	# width  宽
	width = request.form.get('z2')
	# height  高
	height = request.form.get('z3')
	# 报表背景图片名称
	report_bg = request.form.get('report_bg')
	# 附件大小，单位M
	jpg_size = request.form.get('jpg_size')
	back_type = request.form.get('z4')
	back_type = str(back_type)
	width = str(width)
	height = str(height)
	jpg_size = str(jpg_size)
	f = request.files['jpg_name']
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(userCode,'报表管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	jpg_size = '0'
	#报表背景图片
	fname = secure_filename(f.filename)
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	data_json = '{"Id":'+f_id+',"ReportBGName": "'+report_bg+'","ReportBGPic": "'+fname+'","AttachMaxLimit": '+jpg_size+',"Width":'+width+',"Height":'+height+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PSaveDataReportGlobalCfg\"(E'%s')" % (data_json)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			save_result = json.loads(results)
			if save_result['Result'] == True:
				if fname != "":
					f.save(os.path.join(UPLOAD_FOLDER, fname))
					task_content = '[global]\nclass = tasksave_jpg\ntype = execute_cmd\nfile_pwd=\"%s\"\n' % (file_pwd)
					if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
						curs.close()
						conn.close()
						if(back_type=="1"):
							if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>报表素材'):                           
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							elif(back_type=="0"):
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>模板管理'):
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							else:
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>生成报表'):         
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
						
					task_content = '[global]\nclass=taskWaterMark\ntype=getWaterMark\nwatername=%s\n' % (report_bg)
					if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
						curs.close()
						conn.close()
						if(back_type=="1"):
							debug1("start")
							if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>报表素材'):
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						elif(back_type=="0"):
							if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>模板管理'):        
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						else:   
							if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>生成报表'):        
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
					
					img_name = request.form.get('z5')
					if img_name <0 or img_name == '':
						pass
					else:
						img_path = "/var/www/manage/html/images/" +img_name
						task_content = '[global]\nclass=taskglobal\ntype=delfile\npath=%s\n' % (img_path)
						if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
							curs.close()
							conn.close()
							if(back_type=="1"):
								debug1("start")
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>报表素材'):
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							elif(back_type=="0"):
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>模板管理'):        
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							else:   
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>生成报表'):        
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
					
					if(back_type=="1"):
						if not system_log(userCode,'编辑报表素材（水印背景：%s ，LOGO图片：%s）' % (report_bg,fname),'成功','运维报表>报表素材'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					elif(back_type=="0"):
						if not system_log(userCode,'编辑报表素材（水印背景：%s ，LOGO图片：%s）' % (report_bg,fname),'成功','运维报表>模板管理'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						if not system_log(userCode,'编辑报表素材（水印背景：%s ，LOGO图片：%s）' % (report_bg,fname),'成功','运维报表>生成报表'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					img_name = request.form.get('z5')
					if img_name <0 or img_name == '':
						pass
					else:
						img_path = "/var/www/manage/html/images/" +img_name
						task_content = '[global]\nclass=taskglobal\ntype=delfile\npath=%s\n' % (img_path)
						if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
							curs.close()
							conn.close()
							if(back_type=="1"):
								debug1("start")
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>报表素材'):
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							elif(back_type=="0"):
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>模板管理'):        
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							else:   
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>生成报表'):        
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
							
						img_path = "/usr/storage/.system/etc/tit.jpg"
						task_content = '[global]\nclass=taskglobal\ntype=delfile\npath=%s\n' % (img_path)
						if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
							curs.close()
							conn.close()
							if(back_type=="1"):
								debug1("start")
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>报表素材'):
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							elif(back_type=="0"):
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>模板管理'):        
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							else:   
								if not system_log(userCode,'编辑报表素材' % (report_bg,fname),'任务下发异常','运维报表>生成报表'):        
									return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)	
						
						
					if(back_type=="1"):
						if not system_log(userCode,'编辑报表素材（水印背景：%s）' % (report_bg),'成功','运维报表>报表素材'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					elif(back_type=="0"):
						if not system_log(userCode,'编辑报表素材（水印背景：%s）' % (report_bg),'成功','运维报表>模板管理'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						if not system_log(userCode,'编辑报表素材（水印背景：%s）' % (report_bg),'成功','运维报表>生成报表'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				'''
				if os.path.exists(UPLOAD_FOLDER):
					shutil.rmtree(UPLOAD_FOLDER)  
					os.mkdir(UPLOAD_FOLDER)
					conn.commit()
					debug1("zqy_7")
					debug1(back_type)
					#oper_arr=[]
					#oper_arr.append('水印背景：%s'%report_bg)
					oper='编辑报表素材（水印背景：%s）' % report_bg
				'''
				if(back_type=="1"):
					if not system_log(userCode,oper,'失败','运维报表>报表素材'):	
						debug1("1")
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				elif(back_type=="0"):
					if not system_log(userCode,oper,'失败','运维报表>模板管理'):	
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					if not system_log(userCode,oper,'失败','运维报表>生成报表'):	
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
		
@history_report.route('/Get_DataReportGlobalCfg',methods=['GET', 'POST'])
def Get_DataReportGlobalCfg():	
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
			sql = "select public.\"PGetDataReportGlobalCfg\"()"
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results == None:
				return "{\"Result\":false}"
			else:
				results = results.encode('utf-8')
				data = json.loads(results)
				if data['ReportBGPic'] != "" and data['ReportBGPic'] != None:
					task_content = '[global]\nclass = tasksave_jpg\ntype = execute_cmd_cp\nbgpic="%s"\n' % data['ReportBGPic']
					if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
						return "{\"Result\":false}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_2 创建分类&编辑分类)
@history_report.route('/Save_DataReportTemplateType',methods=['GET', 'POST'])
def Save_DataReportTemplateType():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type_name = request.form.get('z1')
	type_id = request.form.get('z2')
	back_type = request.form.get('z3')
	usercode_str = request.form.get('z4')
	md5_str = request.form.get('m1')
	back_type = str(back_type)
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(usercode_str);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	#data_json = '{"TemplateTypeId":'+type_id+',"Name":"'+type_name+'","UserCode":"'+userCode+'"}'
	data_json = {"TemplateTypeId":0,"Name":"","UserSet":[]}
	data_json['TemplateTypeId'] = int(type_id)
	data_json['Name'] = type_name
	data_json['UserSet'] = json.loads(usercode_str)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PSaveDataReportTemplateType\"(E'%s')" % json.dumps(data_json)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			results_json=json.loads(results)
			if int(type_id) == 0 :
				if(back_type=="0"):
					if not results_json['Result']:
						if not system_log(userCode,'创建分类：%s' % type_name,results_json['ErrMsg'],'运维报表>模板管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'创建分类：%s' % type_name,'成功','运维报表>模板管理'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					if not results_json['Result']:
						if not system_log(userCode,'创建分类：%s' % type_name,results_json['ErrMsg'],'运维报表>生成报表'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'创建分类：%s' % type_name,'成功','运维报表>生成报表'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else :
				if(back_type=="0"):
					if not results_json['Result']:
						if not system_log(userCode,'编辑分类：%s' % type_name,results_json['ErrMsg'],'运维报表>模板管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'编辑分类：%s' % type_name,'成功','运维报表>模板管理'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					if not results_json['Result']:
						if not system_log(userCode,'编辑分类：%s' % type_name,results_json['ErrMsg'],'运维报表>生成报表'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'编辑分类：%s' % type_name,'成功','运维报表>生成报表'):	
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)

		
@history_report.route('/Get_DataReportTemplateType',methods=['GET', 'POST'])
def Get_DataReportTemplateType():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type_id = request.form.get('z1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if type_id != "null":
		type_id = int(type_id)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetDataReportTemplateType\"(%s,E'%s')" % (type_id,userCode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]#.encode('utf-8')
			if results == None:
				results = "[]"
			else:
				results = results.encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@history_report.route('/Get_DataReportTemplate',methods=['GET', 'POST'])
def Get_DataReportTemplate():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	t_id = request.form.get('z1')
	temp_id = request.form.get('z2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	if t_id and str(t_id).isdigit() == False:
		return '',403 
	if temp_id and str(temp_id).isdigit() == False:
		return '',403 
		
	if t_id == None:
		t_id = "null"
	else:
		temp_id = "null"
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetDataReportTemplate\"(%s,%s)" % (temp_id,t_id)
			curs.execute(sql)
			results = curs.fetchall()[0][0]#.encode('utf-8')
			if results == None:
				return "[]"
			else:
				results = results.encode('utf-8')
				result_temp = json.loads(results)#array
				result_con = json.loads(result_temp[0]['Condition'])
				if result_con['RptMemo'] != "":
					result_con['RptMemo'] = base64.b64decode(result_con['RptMemo'].split(':',1)[1]).encode('utf-8')
				if result_con['RptSugg'] != "":
					result_con['RptSugg'] = base64.b64decode(result_con['RptSugg'].split(':',1)[1]).encode('utf-8')
				result_temp[0]['Condition'] = result_con
				return json.dumps(result_temp,encoding='utf-8')
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_4 创建模板&编辑模板)		
@history_report.route('/Save_DataReportTemplate',methods=['GET', 'POST'])
def Save_DataReportTemplate():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	rpt_json_str = request.form.get('z1')
	back_type = request.form.get('z2')
	md5_str = request.form.get('m1')
	back_type = str(back_type)
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
		md5_json = StrMD5(rpt_json_str);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			rpt_json = json.loads(rpt_json_str)
			rpt_json_c = json.loads(rpt_json['Condition'])
			
			rpt_json_c['RptMemo'] = "B64:" + base64.b64encode(rpt_json_c['RptMemo'])
			rpt_json_c['RptSugg'] = "B64:" + base64.b64encode(rpt_json_c['RptSugg'])
			rpt_json['Condition'] = rpt_json_c
			rpt_json_str = json.dumps(rpt_json)
			sql = "select public.\"PSaveDataReportTemplate\"(E'%s')" % (MySQLdb.escape_string(rpt_json_str).decode('utf-8'))
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			s =json.loads(rpt_json_str)
			t_name = s['Name']
			t_id = str(s['Id'])
			sql1="select plan.\"Condition\" from public.\"DataReportTemplate\" plan where plan.\"Name\"=E'%s';"%(t_name)
			curs.execute(sql1)
			
			result1 = curs.fetchall()[0][0].encode('utf-8')
			condition = json.loads(result1)
			RptName = condition['RptName']
			#描述
			RptMemo = condition['RptMemo']
			if(RptMemo==""):
				RptMemo = "无"
			else:
				RptMemo = str(condition['RptMemo'].split(":",1)[1])
				if RptMemo!='':
					RptMemo = base64.b64decode(RptMemo)
					RptMemo='，描述：'+RptMemo
			#建议
			RptSugg = condition['RptSugg']
			if(RptSugg==""):
				RptSugg = "无"
			else:
				RptSugg = str(condition['RptSugg'].split(":",1)[1])
				if RptSugg!='':
					RptSugg = base64.b64decode(RptSugg)
					RptSugg='，建议：'+RptSugg
			#分类名称
			Rpmember = condition['Rpmember']
			#加载模块
			RptLoad = condition['RptLoad']
			#生成格式
			DataFormat = condition['RptFormat']['DataFormat']
			RptCont = condition['RptCont']
			if(RptCont=="catalog|abstract|chart|layer"):
				RptCont="图形报表：生成，文字报表：生成"
			elif(RptCont == "catalog|abstract|chart|layer-"):
				RptCont="图形报表：生成，文字报表：不生成"
			elif(RptCont == "catalog|abstract|chart-|layer"):
				RptCont="图形报表：不生成，文字报表：生成"
			elif(RptCont == "catalog|abstract|chart-|layer-"):
				RptCont="图形报表：不生成，文字报表：不生成"
			#会话类型（1操作；1,2会话；3系统）
			KeyLogType = str(condition['SearchDef']['KeyLogType']).split(',')
			KeyLogType_arr=[]
			for i in KeyLogType:
				if(i=="1"):
					KeyLogType_arr.append("操作")
				elif(i=="3"):
					KeyLogType_arr.append("系统")
				else:
					KeyLogType_arr.append("会话")
			KeyLogType='、'.join(KeyLogType_arr)
			KeyCondition = condition['SearchDef']['KeyRule']['KeyCondition']
			sum = ""
			for keycondition in KeyCondition :
				#选项
				selectop = str(keycondition['selectop'])
				#操作
				action = str(keycondition['action'])
				#内容
				'''
				value = str(keycondition['value'])
				value = value.replace("'","")
				value = value.replace("[","")
				value = value.replace("]","")
				value = value.replace("u","")
				'''
				value = keycondition['value']
				#名称
				name = keycondition['name']
				#类型
				type = str(keycondition['type'])
				if (type=="select"):
					for i,index in enumerate(value):
						#debug(str(i)+':'+str(index))
						value[i]=index.split(':')[1]
				elif (type=="ip"):
					if action=='ingroup':
						for i,index in enumerate(value):
							value[i]=index.split(':')[1]
					else:
						for i,index in enumerate(value):
							value[i]=index.split('-')[0]
				#value='、'.join(value)
				if(selectop=="1"):
					selectop = "默认"
				elif(selectop=="2"):
					selectop = "可选"	
				if(action=="equal"):
					action="等于"
					'''
					if(type=="select"):
						value = value.split(':')[1]
					elif(type=="ip"):
						value = value.split('-')[0]
					'''
				elif(action=="high"):
					action = ">"
				elif(action=="ehigh"):
					action = ">="	
				elif(action=="low"):
					action = "<"
				elif(action=="elow"):
					action = "<="
				elif(action=="not equal"):
					action = "不等于"
					'''
					if(type=="select"):
						value = value.split(':')[1]
					elif(type=="ip"):
						value = value.split('-')[0]
					'''
				elif(action=="between"):
					action = "区间"
					if(type=="time" or type=="ip"):
						for i,index in enumerate(value):
							value[i]=index.replace(';','-')	
						#a = value.split(';')
						#value = a[0] + "-" + a[1]
					else:
						for i,index in enumerate(value):
							value[i]=index[0]+'-'+index[1]
						#value = value[0] + "-" + value[1]
				
				#elif(action=="span"):
				#	action = "开空间"
				#	if(type=="time" or type=="id"):
				#		a = value.split(';')
				#		value = a[0] + "-" + a[1]
				#	else:
				#		value = value[0] + "-" + value[1]
				#elif(action=="ehspan"):
				#	action = "左开右闭"
				#	if(type=="time" or type=="id"):
				#		a = value.split(';')
				##		value = a[0] + "-" + a[1]
				#	else:
				#		value = value[0] + "-" + value[1]
				#elif(action=="elspan"):
				#	action = "左闭右开"
				#	if(type=="time" or type=="id"):
				#		a = value.split(';')
				#		value = a[0] + "-" + a[1]
				#	else:
				#		value = value[0] + "-" + value[1]
				elif(action=="begin"):
					action = "开始"
				elif(action=="end"):
					action = "结束"
				elif(action=="include"):
					action = "包含"
				elif(action=="not include"):
					action = "不包含"
				elif(action=="regx"):
					action = "正则匹配"
				elif(action=="not regx"):
					action = "正则不匹配"
				elif(action=="ncregx"):
					action = "正则匹配(不敏感)"
				elif(action=="not ncregx"):
					action = "正则不匹配(不敏感)"
				elif(action=="match"):
					action = "通配符"
				elif(action=="ingroup"):
					action = "主机组"
					#value = value.split(':')
					#value = value[1]
				elif(action == ""):
					value = "无"
				value='、'.join(value)
				if(selectop=="可选"):
					sum = sum + "，" + name +"【" + selectop + "】"
				else:
					if(action==""):
						sum = sum + "，" + name +"【" + selectop + "】:"  + value
					else:
						sum = sum + "，" + name +"【" + selectop + "】：" + '【'+action +'】'+ value
			layers = condition['RptBuild']['layer']
			layer_s = ""
			for layer in layers:
				if layer['level']==1:
					layer_s+='，基础报表（'
				elif layer['level']==2:
					layer_s+='，扩展报表（' 
				page = layer['page']
				if page=='':
					page=''	
				else:
					page = "，分页显示："+str(page)+"页"
				template = '加载模块：%s'%str(layer['template'])
				style = str(layer['style'])
				groupstats = layer['groupstat']
				groupstat_s = ""
				if(style=="stat"):
					style="生成类型：统计型"
					for	groupstat in groupstats:
						GroupUnit = str(groupstat['GroupUnit'])
						if(GroupUnit=="day"):
							GroupUnit = "天"
						elif(GroupUnit=="year"):
							GroupUnit = "年"
						elif(GroupUnit=="month"):
							GroupUnit = "月"
						elif(GroupUnit=="hour"):
							GroupUnit = "小时"
						elif(GroupUnit=="minute"):
							GroupUnit = "分钟"
						GroupIndex =str(groupstat['GroupIndex'])
						GroupInnerIndex = "组内位置 - " + str(groupstat['GroupInnerIndex'])
						Grouped = str(groupstat['Grouped'])
						StatMethod = int(groupstat['StatMethod'])
						StatMethod_arr=[]
						if(StatMethod & 1):
							StatMethod_arr.append("最大")
						if(StatMethod & 2):
							StatMethod_arr.append("最小")
						if(StatMethod & 4):
							StatMethod_arr.append("罗列")
						if(StatMethod & 8):
							StatMethod_arr.append("平均")
						if(StatMethod & 16):
							StatMethod_arr.append("累加")
						StatMethod='、'.join(StatMethod_arr)
						if StatMethod!='':
							StatMethod='、'+StatMethod
						Name = groupstat['Name']
						if(Grouped=="true"):
							GroupIndex = "优先级组 - " + GroupIndex
							if(GroupUnit==""):
								groupstat_s = groupstat_s + "，" + Name + "【分组】：" + GroupIndex + "、" + GroupInnerIndex 
							else:
								groupstat_s = groupstat_s + "，" + Name + "【分组】【"+ GroupUnit + "】：" + GroupIndex + "、" + GroupInnerIndex 
						elif(Grouped=="false"):
							GroupIndex = "优先级组 - " + GroupIndex
							groupstat_s = groupstat_s + "，" + Name + "【不分组】：" + GroupIndex + "、" + GroupInnerIndex + StatMethod
				elif(style=="detail"):
					style="生成类型：明细型"
					for	groupstat in groupstats:
						GroupIndex =str(groupstat['GroupIndex'])
						show = str(groupstat['show'])
						Name = groupstat['Name']
						if(show=="true"):
							GroupIndex = "位置 - " + GroupIndex
							groupstat_s = groupstat_s + "，" + Name + "：" + GroupIndex
				config_s = ""
				configs = layer['config']
				if(len(configs)>0):
					for config in configs:
						config_arr=[]
						GroupIndex =str(config['GroupIndex'])
						Sort = str(config['Sort'])
						if(Sort=="32"):
							Sort = "字段排序"
						elif(Sort=="64"):
							Sort = "统计值排序"
						Sorttrue = str(config['Sorttrue'])
						if(Sorttrue=="True"):
							Sorttrue = "升序"
						elif(Sorttrue=="False"):
							Sorttrue = "降序"
						if Sort=='-1':
							config_arr.append('不排序')
						else:
							config_arr.append(Sort+'-'+Sorttrue)
						if(config['StatValueShow']):
							StatValueShow = "显示计数值"
							config_arr.append('显示计数值')
						if(config['Split']):
                                                        config_arr.append('拆分')
						if(config['Lascande']==True):
							config_arr.append('横向扩展')
						top = str(config['ShowFilter']['top'])
						bottom = str(config['ShowFilter']['bottom'])
						opened_1_arr=[]
						if(config['ShowFilter']['opened']==True):
							opened_1 = "显示过滤"
							if(config['ShowFilter']['min']==True):
								opened_1_arr.append('最小值')
							if(config['ShowFilter']['max']==True):
								opened_1_arr.append('最大值')
							if(top!="0"):
								top = "前" + top
								opened_1_arr.append(top)
							if(bottom!="0"):
								bottom = "后" + bottom
								opened_1_arr.append(bottom)
							if len(opened_1_arr)!=0:
								config_arr.append(opened_1+'-'+'、'.join(opened_1_arr))
							else:
								config_arr.append(opened_1)
						opened_2 = str(config['Condition']['opened'])
						if(config['Condition']['opened']==True):
							opened_2 = "统计过滤"
							action = str(config['Condition']['action'])
							if(action=="equal"):
								action="="
							elif(action=="high"):
								action = ">"
							elif(action=="low"):
								action = "<"
							ConditionType = config['Condition']['ConditionType']
							if ConditionType==0:
								ConditionType='计数值'
							elif ConditionType==1:
								ConditionType='最大'
							elif ConditionType==2:
								ConditionType='最小'
							elif ConditionType==8:
								ConditionType='平均'
							elif ConditionType==16:
								ConditionType='累积'
							config_arr.append(opened_2+'-'+ConditionType+action+str(config['Condition']['value'][0]))
						'''
						value = str(config['Condition']['value'])
						value = value.replace("'","")
						value = value.replace("[","")
						value = value.replace("]","")
						'''
						name=""
						for	groupstat in groupstats:
							GroupIndex_1 =str(groupstat['GroupIndex'])
							Name = groupstat['Name']
							if(GroupIndex_1==GroupIndex):
								if(name==""):
									name = Name
								else:
									name = name +"、"+ Name
						config_s+=("，优先级组"+ GroupIndex+ "【" + name  + "】："+'、'.join(config_arr))
						'''	
						if(Sort=="-1"):
							config_s = config_s + "，" +"优先级组"+ GroupIndex+ "：【" + name  + "】" + Sort
						else:
							config_s = config_s + "，" +"优先级组"+ GroupIndex+ "：【" + name  + "】" + Sort + "" + StatValueShow + " " +Lascande + Split
							#config_s = config_s + "，" +"优先级组"+ GroupIndex+ "：【" + name  + "】" + Sort + "【" + Sorttrue + "】" + StatValueShow + " " +Lascande + Split
							if(opened_1!=""):
								if(top!=""):
									opened_1 = opened_1 +top+" "
								if(bottom!=""):
									opened_1 = opened_1+bottom+" " 
								if(max!=""):
									opened_1 = opened_1 +max+" "
								if(min!=""):
									opened_1 = opened_1 +min+" "
								config_s = config_s + "，" +opened_1
							if(opened_2!=""):
								opened_2 = opened_2 + action + value
								config_s = config_s + "，" +opened_2
						'''
				layer_s = layer_s + style + "，" + template + page + groupstat_s + config_s+'）'
				#try:
			open_1 = RptName + "（所属分类：" + Rpmember + "，生成格式：" +DataFormat + "，加载模块：" + RptLoad + "，"+ RptCont + RptMemo + RptSugg + "，日志属性：" + KeyLogType + sum +" "+ layer_s+"）"
				#except Exception,e:
				#	debug1(str(e));
			results_json=json.loads(results)
			if(t_id=="0"):
				
				if(back_type=="0"):
					if not results_json['Result']:
						if not system_log(userCode,'创建模板：%s'%(RptName),results_json['ErrMsg'],'运维报表>模板管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'创建模板：%s'%(open_1),'成功','运维报表>模板管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
				
					if not results_json['Result']:
						if not system_log(userCode,'创建模板：%s'%(RptName),results_json['ErrMsg'],'运维报表>生成报表'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'创建模板：%s'%(open_1),'成功','运维报表>生成报表'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				if(back_type=="0"):
					if not results_json['Result']:
						if not system_log(userCode,'编辑模板：%s'%(RptName),results_json['ErrMsg'],'运维报表>模板管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'编辑模板：%s'%(open_1),'成功','运维报表>模板管理'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
				
					if not results_json['Result']:
						if not system_log(userCode,'编辑模板：%s'%(RptName),results_json['ErrMsg'],'运维报表>生成报表'):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					else:
						conn.commit()
						if not system_log(userCode,'编辑模板：%s'%(open_1),'成功','运维报表>生成报表'):
							debug1("2")
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_3 删除模板)		
@history_report.route('/Delete_DataReportTemplate',methods=['GET', 'POST'])
def Delete_DataReportTemplate():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	t_id = request.form.get('z1')
	back_type = request.form.get('z2')
	back_type = str(back_type)
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(userCode,'报表管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if back_type != '0' and back_type != '1' and back_type != 'None':
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if t_id.isdigit():
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql1='select plan."Name" from public."DataReportTemplate" plan where plan."Id"=%s;'%(t_id)
			curs.execute(sql1)
			result1 = curs.fetchall()[0][0].encode('utf-8')
			
			sql = "select public.\"PDeleteDataReportTemplate\"(%s)" % t_id
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			results_json=json.loads(results)
			if(back_type=="0"):
				if not results_json['Result']:
					if not system_log(userCode,'删除模板：%s'%(result1),results_json['ErrMsg'],'运维报表>模板管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					conn.commit()
					if not system_log(userCode,'删除模板：%s '%(result1),'成功','运维报表>模板管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				if not results_json['Result']:
					if not system_log(userCode,'删除模板：%s'%(result1),results_json['ErrMsg'],'运维报表>生成报表'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					conn.commit()
					if not system_log(userCode,'删除模板：%s '%(result1),'成功','运维报表>生成报表'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_1 删除分类)		
@history_report.route('/Delete_DataReportTemplateType',methods=['GET', 'POST'])
def Delete_DataReportTemplateType():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	t_id = request.form.get('z1')
	back_type = request.form.get('z2')
	back_type = str(back_type)
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(userCode,'报表管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if back_type != '0' and back_type != '1' and back_type != 'None':
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if t_id.isdigit():
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql1 = "select public.\"PGetDataReportTemplateType\"(%s,E'%s')" % (t_id,userCode)
			curs.execute(sql1)
			result1 = curs.fetchall()[0][0].encode('utf-8')
			s = json.loads(result1)
			name = s[0]['Name']
			sql = "select public.\"PDeleteDataReportTemplateType\"(%s)" % t_id
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			results_json=json.loads(results)
			if(back_type=="0"):
				if not results_json['Result']:
					if not system_log(userCode,'删除分类：%s' % name,results_json['ErrMsg'],'运维报表>模板管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					conn.commit()
					if not system_log(userCode,'删除分类：%s' % name,'成功','运维报表>模板管理'):	
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				if not results_json['Result']:
					if not system_log(userCode,'删除分类：%s' % name,results_json['ErrMsg'],'运维报表>生成报表'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					conn.commit()
					if not system_log(userCode,'删除分类：%s' % name,'成功','运维报表>生成报表'):	
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@history_report.route('/get_log_type',methods=['GET', 'POST'])
def get_log_type():	
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
			sql="select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_report + 3, ErrorEncode(e.args[1]))
		
@history_report.route('/get_host_rpt',methods=['GET', 'POST'])
def get_host_rpt():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql="select public.\"PGetHost\"(null,true,E'%s');" % userCode
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_5 执行报表)		
@history_report.route('/execute_rpt',methods=['GET', 'POST'])
def execute_rpt():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	xml_str = request.form.get('z1')
	type = request.form.get('z2')
	hgid_array = request.form.get('z3')
	task_time = request.form.get('z4')
	temp_id = request.form.get('z5')
	if temp_id and str(temp_id).isdigit() == False:
		return '',403 
	
	#back_type = request.form.get('z6')
	#back_type = str(back_type)
	if_disable = request.form.get('z9')
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
		md5_json = StrMD5(xml_str);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			
			sql = "select public.\"PGetDataReportTask\"(null,E'%s',null,null,null)" % (userCode)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			rpt_result = json.loads(results)
			rpt_total = int(rpt_result['totalrow'])
			
			if(type == 'NORMAL'):
				sql = "select public.\"PGetLogFieldConfig\"(1);";
			elif(type == 'SESSION'):
				sql = "select public.\"PGetLogFieldConfig\"(2);";
			elif(type == 'SYSTEM'):
				sql = "select public.\"PGetLogFieldConfig\"(3);";
			else:
				sql = "select public.\"PGetLogFieldConfig\"(1);"; ###暂定1
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"查询日志字段失败(%d)\"}"% (sys._getframe().f_lineno)

			results = curs.fetchall()[0][0].encode('utf-8')
			Column_list = json.loads(results)
			tmpstr ="\t<Column>\n"
			for column in Column_list:
				tmpstr = tmpstr +"\t\t<value name=\"%s\">%s</value>\n" %(column['Content'],column['Translation'])
			tmpstr = tmpstr + "\t</Column>\n"
			xml_str = xml_str + tmpstr
			
			###获取所有 协议
			results = proto_all()
			tmpstr = "\t<Proto>\n"
			proto_list = json.loads(results)['data']
			if proto_list == None:
				proto_list = []
			for proto in proto_list:
				tmpstr =  tmpstr + "\t\t<value name=\"%s\">%d</value>\n" %(proto['ProtocolName'],proto['ProtocolId'])
			tmpstr =  tmpstr + "\t</Proto>\n"
			xml_str = xml_str + tmpstr
			##获取协议结束
			
			sql = "select public.\"PGetManagedScope\"(E'%s');" %(userCode)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"查询日志字段失败(%d)\"}"% (sys._getframe().f_lineno)
			results = curs.fetchall()
			tmpstr = "\t<Perm>\n"
			
			if not len(results) == 0:
				#results = results.encode('utf-8')
				manageScope_list = json.loads(results[0][0].encode('utf-8'))
				MHostList = manageScope_list['MHostList']
				MIPList = manageScope_list['MIPList']
				if MHostList == None:
					MHostList = []
				if MIPList == None:
					MIPList = []	
				for MHost in MHostList:
					tmpstr =  tmpstr + "\t\t<value>%s</value>\n" %(MHost['HostIP'])
				for MIP in MIPList:
					tmpstr =  tmpstr + "\t\t<value>%s;%s</value>\n" %(MIP['StartIP'],MIP['EndIP'])
			
			tmpstr =  tmpstr + "\t</Perm>\n"
			xml_str = xml_str + tmpstr
			##获取管理权限结束
			
			
			###获取 当前主机组下的所有主机
			tmpstr = ""
			hostgrp = json.loads(hgid_array)
			for group in hostgrp:
				tmpstr = tmpstr +  "\t\t<KeyGroup name=\"%s\">\n" % (group)
				sql = "select public.\"PGetHostList\"(%s);" %(group)
				curs.execute(sql)
				results = curs.fetchall()
				if results[0][0] == None:
					tmpstr = tmpstr + "\t\t</KeyGroup>\n"
					continue
				else:					
					results = results[0][0].encode('utf-8')
				results = json.loads(results)
				for host in results:
					tmpstr = tmpstr + '\t\t\t<value>%s</value>\n' %(host['HostIP'])
				tmpstr = tmpstr + "\t\t</KeyGroup>\n"
			tmpstr = "\t<Group>\n"+tmpstr +"\t</Group>\n" 
			
			
			###三权分立 if_disable 8-9-11
			perm_list = if_disable.split('-');
			tmpstr = "";
			# 三权分立 8->运维操作(操作、会话) 9->堡垒操作(堡垒管理-运维部分) 11->堡垒管理(堡垒管理-非运维用户部分)
			if type == 'SYSTEM':
				if ('9' in perm_list ) and ('11' in perm_list ):
					pass;
				else:			
					if ('9' in perm_list ):
						clas = 'N';
					else:
						clas = 'Y';
					##获取用户名
					#if clas =='Y':
					#sql = 'select public."PGetRole"(null,null,FALSE,null,null,null,\'{"submenuname":"堡垒操作"}\',\'{}\');';
					sql = 'select public."PGetRole"(null,null,FALSE,null,null,null,\'{"submenuname":"堡垒管理"}\',\'{}\');';
					#else:
					#	sql = 'select public."PGetRole"(null,null,FALSE,null,null,null,\'{"submenuname":"堡垒管理"}\',\'{}\');';
					try:
						curs.execute(sql.decode('utf-8'))
						debug(sql)
					except pyodbc.Error,e:
						curs.close()
						conn.close()
						msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
						if not system_log(userCode,oper,msg,module+">条件检索"):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					results = curs.fetchall()[0][0]
					debug(str(results))
					results_json = json.loads(results);
					json_data = results_json['data'];
					for da in json_data:
						RoleId = da['RoleId']
						sql = 'select  public."User"."UserCode" from public."User"  where  public."User"."UserId" IN(select public."UserRole"."UserId" from public."UserRole" where public."UserRole"."RoleId"=%d) ;' %(RoleId)
						try:
							curs.execute(sql)
						except pyodbc.Error,e:
							curs.close()
							conn.close()
							msg ='系统异常: %s(%d)'% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
							if not system_log(userCode,oper,msg,module+">条件检索"):
								return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
						results_tmp = curs.fetchall()
						for utmp in results_tmp:
							tmpstr = tmpstr + '\t\t<value name=\"%s\">%s</value>\n' %(utmp[0].encode('utf-8'),clas);
						tmpstr = tmpstr + '\t\t<value name=\"\">%s</value>\n' %(clas);		
				tmpstr = "\t<Account>\n"+tmpstr +"\t</Account>\n"
			xml_str = xml_str + tmpstr
			
			
			
			
			xml_str = xml_str + tmpstr + "</Report>"
			##获取主机组结束
			'''
			##获取主机名和IP
			tmpstr = ""
			sql = "select public.\"PGetHost\"(null,true,E'%s');" %(userCode)
			debug(sql)
			try:
				curs.execute(sql)
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"查询日志字段失败(%d): %s\"}"% (ERRNUM_MODULE_report + 7, ErrorEncode(e.args[1]))
			results = curs.fetchall()[0][0].encode('utf-8')
			results = json.loads(results);
			for host in results:
				tmpstr = tmpstr + '\t\t<value name=\"%s\">%s</value>\n' %(host['HostName'],host['HostIP'])
				
			tmpstr = "\t<Host>\n"+tmpstr +"\t</Host>\n"
			xml_str = xml_str + tmpstr + "</Report>"
			'''
			
			##获取主机结束
			debug1('task_time:'+str(task_time))	
			if task_time == '0' or task_time == '1':
				if task_time == '1':
					root = ET.fromstring(xml_str)
					format = root[6].text.split('/')
					if format[-1] == "DAY":
						type = 1
						next_time = NextExecuteTime(type)
					elif format[-1] == "WEEK":
						type = 2
						next_time =NextExecuteTime(type)
					elif format[-1] == "MONTH":
						type = 3
						next_time = NextExecuteTime(type)
				else:
					next_time = 'null'
					type = 0
				
				if type != 0:
					sql = "select count(*) from private.\"DataReportTask\" where \"TemplateId\"=%s and \"Type\"=%d" % (temp_id,type)
					curs.execute(sql)
					result = curs.fetchall()[0][0]
					if result == 0:
						if rpt_total > 29:
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"超过静态报表数量上限\"}"
				root = ET.fromstring(xml_str)
				'''
				if root[1].text != "" and root[1].text != None:
					memo = "b64:" + base64.b64encode(root[1].text)
					#xml_str = xml_str.replace(root[1].text,memo)
					root[1].text = memo
					xml_str=ET.tostring(root)
				if root[2].text != "" and root[2].text != None:
					sugg = "b64:" + base64.b64encode(root[2].text)
					root[2].text = sugg
					xml_str=ET.tostring(root)
					#xml_str = xml_str.replace(root[2].text,sugg)
				'''
				sql="select public.\"PSaveDataReportTask\"(0,E'%s',E'%s',%d,%s,%s);" % (userCode,MySQLdb.escape_string(xml_str).decode('utf-8'),type,next_time,temp_id)
				curs.execute(sql)
			elif task_time == '2' or task_time == '3':
				root = ET.fromstring(xml_str)
				format = root[6].text.split('/')
				if task_time == '2':
					format_1 = format[:-1]#去掉最后一个
					if format_1[-1] == "DAY":
						type = 1
						next_time = NextExecuteTime(type)
					elif format_1[-1] == "WEEK":
						type = 2
						next_time = NextExecuteTime(type)
					del format[-2]#去掉第一个
				elif task_time == '3':
					format_1 = format[:-2]
					type = 1
					next_time = NextExecuteTime(type)
					del format[-3]#去掉第一个
				format_str = root[6].text
				#root[6].text = '/'.join(format_1)
				#ET.ElementTree(root)
				format1122 = '/'.join(format_1)
				str_1 = xml_str.replace(format_str,format1122)
			
				sql = "select count(*) from private.\"DataReportTask\" where \"TemplateId\"=%s and \"Type\"=%d" % (temp_id,type)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				if result == 0:
					if rpt_total > 29:
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"超过静态报表数量上限\"}"
					else:
						rpt_total = rpt_total + 1
				'''
				if root[1].text != "" and root[1].text != None:
					memo = "b64:" + base64.b64encode(root[1].text)
					str_1 = str_1.replace(root[1].text,memo)
				if root[2].text != "" and root[2].text != None:
					sugg = "b64:" + base64.b64encode(root[2].text)
					str_1 = str_1.replace(root[2].text,sugg)
				'''
				sql="select public.\"PSaveDataReportTask\"(0,E'%s',E'%s',%d,%s,%s);" % (userCode,MySQLdb.escape_string(str_1).decode('utf-8'),type,next_time,temp_id)
				curs.execute(sql)
				
				if task_time == '3':#周时间
					debug1('task_time ==3')
					type = 2
					format_2 = format[:-1]
					next_time = NextExecuteTime(type)
					str_2 = xml_str.replace(format_str,'/'.join(format_2))
					
					sql = "select count(*) from private.\"DataReportTask\" where \"TemplateId\"=%s and \"Type\"=%d" % (temp_id,type)
					curs.execute(sql)
					result = curs.fetchall()[0][0]
					if result == 0:
						if rpt_total > 29:
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"超过静态报表数量上限\"}"
						else:
							rpt_total = rpt_total + 1
					'''
					if root[1].text != "" and root[1].text != None:
						memo = "b64:" + base64.b64encode(root[1].text)
						str_2 = str_2.replace(root[1].text,memo)
					if root[2].text != "" and root[2].text != None:
						sugg = "b64:" + base64.b64encode(root[2].text)
						str_2 = str_2.replace(root[2].text,sugg)
					'''
					sql="select public.\"PSaveDataReportTask\"(0,E'%s',E'%s',%d,%s,%s);" % (userCode,MySQLdb.escape_string(str_2).decode('utf-8'),type,next_time,temp_id)
					curs.execute(sql)
					del format[-2]
				format_3 = format[:]
				if format_3[-1] == "WEEK":
					type = 2
					next_time = NextExecuteTime(type)
				elif format_3[-1] == "MONTH":
					type = 3
					next_time = NextExecuteTime(type)
					
				str_3 = xml_str.replace(format_str,'/'.join(format_3))
				
				sql = "select count(*) from private.\"DataReportTask\" where \"TemplateId\"=%s and \"Type\"=%d" % (temp_id,type)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				if result == 0:
					if rpt_total > 29:
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"超过静态报表数量上限\"}"
				'''
				if root[1].text != "" and root[1].text != None:
					memo = "b64:" + base64.b64encode(root[1].text)
					str_3 = str_3.replace(root[1].text,memo)
				if root[2].text != "" and root[2].text != None:
					sugg = "b64:" + base64.b64encode(root[2].text)
					str_3 = str_3.replace(root[2].text,sugg)
				'''
				sql="select public.\"PSaveDataReportTask\"(0,E'%s',E'%s',%d,%s,%s);" % (userCode,MySQLdb.escape_string(str_3).decode('utf-8'),type,next_time,temp_id)
				curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			sum = ET.fromstring(xml_str)
			RptName = sum.find('RptName').text
			RptSugg = sum.find('RptSugg').text
			oper="执行任务："+ RptName
			oper_arr=[]
			if RptSugg!='' and RptSugg!=None:
				#RptSugg = base64.b64decode(RptSugg.split(':',1)[1])
				oper_arr.append('建议：'+RptSugg)
			#if(RptSugg=="None"):
			#	RptSugg = "无"
			#else:
				#RptSugg = str(sum[2].text.split(":",1)[1])
				#RptSugg = base64.b64decode(RptSugg)
			RptFormat = sum.find('RptFormat').text
			rptformat = RptFormat.split("/")
			filetype=rptformat[0]
			oper_arr.append('文件类型：'+filetype)
			n = len(rptformat)
			plantype_arr=[]
			for i in range(2,n):
				if rptformat[i]=='DAY':
					plantype_arr.append('每天')
				elif rptformat[i]=='WEEK':
					plantype_arr.append('每周')
				elif rptformat[i]=='MONTH':
					plantype_arr.append('每月')
				#elif rptformat[i]=='-':
				#	plantype_arr.append('无')
			if len(plantype_arr)==0:
				plantype='关闭'
			else:
				plantype='、'.join(plantype_arr)
			oper_arr.append('计划任务：'+plantype)
			RptMail = sum.find('RptMail').text
			if(RptMail==None or RptMail==''):
				RptMail="邮件接收：关闭"
			else:
				RptMail="邮件接收：开启 邮箱-"+RptMail
			oper_arr.append(RptMail)
			if sum.find('RptBuild').find('layer').find('expand').text=='true':
				oper_arr.append('二层报表：产生')
			else:
				oper_arr.append('二层报表：不产生')
			KeyLogType = sum.find('SearchDef').find('KeyLogType').text
			if(KeyLogType=="NORMAL"):
				KeyLogType="操作"
			elif(KeyLogType=="SESSION"):
				KeyLogType = "会话"
			else:
				KeyLogType="系统"
			oper_arr.append('日志操作：'+KeyLogType)
			keycondition_all = ""
			value_json={}
			for value_item in sum.find('Column').findall('value'):
				name=value_item.get('name')
				index=value_item.text
				value_json[name]=index
			value_json['xtime_05']='结束时间'
			value_json['int08_03']='会话状态'
			value_json['int32_01']='协议'
			action_name_json={
				"0":"所有",
				"equal":"等于",
				"not equal":"不等于",
				"between":"区间",
				"high":">",
				"ehigh":">=",
				"low":"<",
				"elow":"<=",
				"ingroup":"主机组",
				"include":"包含",
				"not include":"不包含",
				"begin":"开始",
				"end":"结束",
				"regx":"正则匹配",
				"not regx":"正则不匹配",
				"ncregx":"正则匹配（不敏感）",
				"not ncregx":"正则不匹配（不敏感）",
				"match":"通配符",
			}
			eventlv_json={
				'0':'无',
				'1':'高',
				'2':'中',
				'3':'低'
			}
			'''
			debug1("for keycondition in sum.find('SearchSet').find('KeyRule').findall('KeyCondition'):")
			for keycondition in sum.find('SearchSet').find('KeyRule').findall('KeyCondition'):
				name_type = keycondition.attrib
				field = name_type['field']
				index = name_type['index']
				values = ""
				debug1(field+index)
				name=value_json[(field+'_'+index)]
				debug1(name)
				action=keycondition.find('value').get('action')
				not_value=keycondition.find('value').get('not')
				if not_value=='y':
					action='not '+action
				action='【'+action_name_json[action]+'】'
				
				debug1(action)
				value_arr=[]
				for value_item in keycondition.findall('value'):
					value=value_item.text
					if name=='告警等级':
                                                value=eventlv_json[value]
					if action=='【区间】':
						if name=='入库时间' or name=='发生时间' or name=='起始时间' or name=="结束时间":
                                                	xtime_1 = value.split(";")[0]
                                                	xtime_2 = value.split(";")[1]
                                                	timeArray = time.localtime(int(xtime_1))
                                                	xtime_1 = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                                                	timeArray = time.localtime(int(xtime_2))
                                                	xtime_2 = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                                                	value=xtime_1+';'+xtime_2
						xtime_1 = value.split(";")[0]
						xtime_2 = value.split(";")[1]
						value = str(xtime_1)+ "-" +str(xtime_2)
						if name=='入库时间':
							action=''
					else:
						if name=='入库时间' or name=='发生时间' or name=='起始时间' or name=="结束时间":
							timeArray = time.localtime(int(value))
                                                        value = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)	
					value_arr.append(value)
				
				oper_arr.append(name+action+'：'+'、'.join(value_arr))
			'''
			results_json=json.loads(results)
			if not results_json['Result']:
				if not system_log(userCode,oper,results_json['ErrMsg'],'运维报表>生成报表'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				conn.commit()
				if not system_log(userCode,oper+'（'+'，'.join(oper_arr)+'）','成功','运维报表>生成报表'):	
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
			
@history_report.route('/get_scheduled_task',methods=['GET', 'POST'])
def get_scheduled_task():	
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
			sql = "select public.\"PGetDataReportTask\"(null,E'%s',null,null,null)" % (userCode)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			cond = json.loads(results)['data']
			cond_list = [{"d":[],"w":[],"m":[]}]
			for cond_v in cond:
				root = ET.fromstring(cond_v['Condition'])
				if root[6].text.find('DAY') >= 0:
					cond_list[0]['d'].append(cond_v)
				elif root[6].text.find('WEEK') >= 0:
					cond_list[0]['w'].append(cond_v)
				else:
					cond_list[0]['m'].append(cond_v)
				#for node in root[1]:
			return json.dumps(cond_list)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@history_report.route('/test_max',methods=['GET', 'POST'])
def test_max():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	f = request.files['jpg_name']
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	fname = secure_filename(f.filename)
	file_pwd = os.path.join('/flash/system/zdp',fname)
	f.save(file_pwd)
	return "ok"

def sort_field(field):
	#4,服务器端口	4,统计值	2,服务端地址	3,客户端地址	1,用户
	field_list = field.split('\t');
	for i in range(len(field_list)-1):    # 这个循环负责设置冒泡排序进行的次数
		for j in range(len(field_list)-i-1):  # ｊ为列表下标
			if int(field_list[j].split(',')[0]) > int(field_list[j+1].split(',')[0]):
				field_list[j], field_list[j+1] = field_list[j+1], field_list[j]
	field = '\t'.join(field_list);
	return field;
###yt 回显 报表数据
def AnalyseField(line,field, level):
	
	for s in line.split('\t'):
		if s.find(',') <0 :
			sys._getframe().f_lineno;
		level.append(s.split(',')[0]);
		field.append(s.split(',')[1]);
	return 0;
#def GetIndexInfo(char *path, char *name, char *htime, char **abstract, int *stat, int *chart, int *layer, char exp, u_int64 eindex) {
##读取摘要文件
def GetIndexInfo(path, name, htime, abstract, stat, expand ,chart, layer, total,page,field, exp, eindex,level):
	i = 0;
	ret = 0;
	len = 0;

	if (exp):
		file = "%s/rpt.abs.%Ld.exp"%( path, eindex )	
	else:
		file = "%s/rpt.abs"%( path )

	if (os.path.exists(file) == False):
		return sys._getframe().f_lineno,"文件不存在";

	fp = open(file,'r');
	while(True):
		line = fp.readline();
		if line[0] == '{':
			break;
	##		
	line = fp.readline();
	if(line.find('\n')<0):
		return sys._getframe().f_lineno,"文件解析失败";
	name[0] = line[:-1];
	
	line = fp.readline();
	if(line.find('\n')<0):
		return sys._getframe().f_lineno,"文件解析失败";
	htime[0] = line[:-1];
	
	#abstract 描述和条件
	while(True):
		line = fp.readline();
		if line[0] == '}':
			break;
		line = line[:-1]
		abstract.append(line);
	#有效数字
	line = fp.readline();
	abstract.append( line[:-1]);
	
	#建议
	line = fp.readline();
	abstract.append( line[:-1]);
	
	##total
	line = fp.readline();
	total[0] = int(line[6:-1])
	
	##page
	line = fp.readline();
	page[0] = int(line[5:-1])
	
	#stat
	while(True):
		line = fp.readline();
		if not line:
			break;
		if line.find('stat:') >=0:
			break;
	stat[0] =  int(line[5:-1]);
	
	##field
	line = fp.readline();
	line = line[:-1];
	line = sort_field(line);
	
	#def AnalyseField(line, field, level):
	ret = AnalyseField(line,field,level);
	if ret:
		return sys._getframe().f_lineno,"文件解析失败";
	#expand
	while(True):
		line = fp.readline();
		if not line:
			break;
		if line.find('expand:') >=0:
			break;
	expand[0] =  int(line[7:-1]);
	
	#chart
	while(True):
		line = fp.readline();
		if not line:
			break;
		if line.find('chart:') >=0:
			break;
	chart[0] =  int(line[6:-1]);
	#layer
	while(True):
		line = fp.readline();
		if not line:
			break;
		if line.find('layer:') >=0:
			break;
	layer[0] =  int(line[6:-1]);
	fp.close();

	return 0,'';

###读取 图形数据
def read_charts(path):
	result = ""
	#日志时间分布 chart1
	path1 = path +"rpt.chart.1";
	if os.path.exists(path1) == False:
		return '-1';
	i = 0;
	result_tmp = "";
	for line in open(path1,'r'):  
		i += 1;
		if(i <= 3):
			continue;###跳过前3行
		line = line[:-1] #去除\n
		print line
		result_tmp +="{\"data\":\"%s\",\"count\":%s}," %(line.split('	')[0].replace('\\','\\\\').replace('\n',' ').replace('\r',' '),line.split('	')[1])
		
	chart1 = result_tmp[:-1]
	#日志类型分布 chart2
	path2 = path +"rpt.chart.2";
	if os.path.exists(path2) == False:
		return '-1';
	i = 0;
	result_tmp = "";
	for line in open(path2,'r'):  
		i += 1;
		if(i <= 3):
			continue;###跳过前3行
		line = line[:-1] #去除\n
		result_tmp +="{\"name\":\"%s\",\"value\":%s}," %(line.split('	')[0].replace('\\','\\\\').replace('\n',' ').replace('\r',' '),line.split('	')[1].replace('\\','\\\\').replace('\n',' ').replace('\r',' '))

	chart2 = result_tmp[:-1]
	#服务器分布 chart3
	path3 = path +"rpt.chart.3";
	if os.path.exists(path3)== False:
		return '-1';
	i = 0;
	result_tmp = "";
	for line in open(path3,'r'):  
		i += 1;
		if(i <= 3):
			continue;###跳过前3行
		line = line[:-1] #去除\n
		result_tmp +="{\"name\":\"%s\",\"value\":%s}," %(line.split('	')[0].replace('\\','\\\\').replace('\n',' ').replace('\r',' '),line.split('	')[1].replace('\\','\\\\').replace('\n',' ').replace('\r',' '))

	chart3 = result_tmp[:-1]
	
	#用户分布 chart4
	path4 = path +"rpt.chart.4";
	if os.path.exists(path4)== False:
		return '-1';
	i = 0;
	result_tmp = "";
	for line in open(path4,'r'): 
		i += 1;
		if(i <= 3):
			continue;###跳过前3行
		line = line[:-1] #去除\n
		result_tmp +="{\"name\":\"%s\",\"value\":%s}," %(line.split('	')[0].replace('\\','\\\\').replace('\n',' ').replace('\r',' '),line.split('	')[1].replace('\\','\\\\').replace('\n',' ').replace('\r',' '))

	chart4 = result_tmp[:-1]
	
	#top chart5
	path5 = path +"rpt.chart.5";
	if os.path.exists(path5) == False:
		return '-1';
	i = 0;
	result_tmp = "";
	for line in open(path5,'r'):
		i += 1;
		if(i <= 3):
			continue;###跳过前3行
		line = line[:-1] #去除\n
		result_tmp +="{\"data\":\"%s\",\"count\":%s}," %(line.split('	')[0].replace('\\','\\\\').replace('\n',' ').replace('\r',' '),line.split('	')[1].replace('\\','\\\\').replace('\n',' ').replace('\r',' '))
		
	chart5 = result_tmp[:-1]
	
	#top chart6
	path6 = path +"rpt.chart.6";
	if os.path.exists(path6) == False:
		chart6 = "";
	else:
		i = 0;
		result_tmp = "";
		for line in open(path6,'r'):  
			i += 1;
			if(i <= 3):
				continue;###跳过前3行
			line = line[:-1] #去除\n
			result_tmp +="{\"data\":\"%s\",\"count\":%s}," %(line.split('	')[0].replace('\\','\\\\').replace('\n',' ').replace('\r',' '),line.split('	')[1].replace('\\','\\\\').replace('\n',' ').replace('\r',' '))

		chart6 = result_tmp[:-1]
	
	result = "{\"chart1\":[%s],\"chart2\":[%s],\"chart3\":[%s],\"chart4\":[%s],\"chart5\":[%s],\"chart6\":[%s]}" %(chart1,chart2,chart3,chart4,chart5,chart6)
	
	return result
	
###获取 摘要
@history_report.route('/get_abstract',methods=['GET', 'POST'])
def get_abstract():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	path_dir = request.form.get('z1')
	eindex = request.form.get('i1');
	exp = request.form.get('e1');
	ifstatic = request.form.get('is');
	if eindex <0 or eindex == "":
		eindex = 1;
	else:
		eindex = int(eindex)
	if exp <0 or exp == "":
		exp = 0;
	else:
		exp = int(exp)
		
	if ifstatic <0 or ifstatic == "":
		ifstatic = 0;
	else:
		ifstatic = int(ifstatic)
		
	try:
		if ifstatic:
			path = PREFIX_RPT_SRES + userCode +"/" + path_dir +"/";
		else:
			path = PREFIX_RPT_DRES + userCode +"/" + path_dir +"/";
		abstract = [];
		report_name = [];
		report_name.append('');
		htime = [];
		htime.append('');
		
		stat = [];
		stat.append(0);
		expand = [];
		expand.append(0);
		chart = [];
		chart.append(0);
		layer = [];
		layer.append(0);
		total = [];
		total.append(0);
		page = [];
		page.append(200);
		field = [];
		#field.append('');
		level = [];
		#level.append('');
		ret,error_msg= GetIndexInfo(path, report_name, htime, abstract, stat, expand, chart, layer, total , page, field, exp, eindex,level);
		if(ret):
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (error_msg,sys._getframe().f_lineno)
		condition = ""
		i = 1;
		for abs in abstract:
			if(i == (len(abstract)-2)):
				break;
			condition += '{"condtion":\"%s\"},' %(abstract[i].replace('	','\\t'))
			i += 1;
		condition = condition[:-1]
		##报表名称 生成时间 描述 有效数据 建议 条件
		result = "{\"report_name\":\"%s\",\"htime\":\"%s\",\"memo\":\"%s\",\"total_count\":\"%s\",\"sugg\":\"%s\",\"total\":%d,\"cont\":[%s]}" %(report_name[0],(':').join(htime[0].split(':')[1:]),abstract[0],abstract[-2].split(':')[1],abstract[-1].split(':')[1].replace('	','\\t'),total[0],condition)
		
		charts = read_charts(path);
	except :
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: 报表解析失败(%d)\"}" % (ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)
		
	return "{\"Result\":true,\"info\":%s,\"charts\":%s,\"path\":\"%s\",\"stat\":%d,\"expand\":%d,\"chart\":%d,\"lay\":%d,\"page\":%d,\"field\":\"%s\",\"level\":\"%s\"}" %(result,charts,path_dir,stat[0],expand[0],chart[0],layer[0],page[0],';'.join(field),';'.join(level)) 
	

	
def ChangeLine(line, level, field_count):
	#char str[1024], buf[LINE_SIZE];
	#char *p1 = NULL, *ptr1 = line;
	#char *p2 = NULL, *ptr2 = str;
	#int i = 0;

	#memset(buf, 0, LINE_SIZE);
	#memset(str, 0, 1024);
	#strcpy(str, level);
	#level 1,1,2,3
	#line cao	12	0ut	uy	1,2,3,4
	#line_last 1,cao	12,1	0ut,2	uy,3	1,3,4,5
	buf = "";
	line_t = line.split('\t');
	for i in range(0,field_count):
		if line.find('\t') <0:
			return sys._getframe().f_lineno,'';
		buf += level[i] +',' + line_t[i] +'\t';
		
	buf +=line_t[i+1];
	return 0,buf;
	
def parse_line(line,layer,stat,field_count):
	try:
		field = ['' for x in range(0, field_count)];
		row = [0 for x in range(0, field_count)];
		group = [0 for x in range(0, field_count)];
		#char *field[field_count], *ptr = NULL, *ptr1 = NULL, *line = NULL;
		#int row[field_count], group[field_count];
		t = 0;
		n = 0;
		son_num = 0;
		#line_tmp 1,cao	12,1	0ut,2	uy,3	1,3,4,5
		
	
		#field  -> 1,会话标识;1,统计值;2,发生时间;2,统计值;3,发生地址;3,统计值
		##data  ->	8385	2017-12-20	29	192.168.0.44	1	1,7,2
		#return {\"data\":\" \",\"rowspan\":7,\"eindex\":1}
		result ="";
		result_tmp = "";
		if stat: ##统计
			#line = dat.split('\t');
			while(True):
				ptr = line[t];
				group[t] = ptr[0];
				field[t] = ptr.split(',')[1];
				if((t +1 ) == field_count):
					break;
				t += 1;
			
			#if (isson):
			
			#if(line[t+1] == ""):
				#t +=1; 
			if(1):
				eindex = line[t+1].split(',')[0]; 
				#line.pop(0);
				
			for ptr in 	line[t+1].split(',')[1:]:
				row[n] = int(ptr);
				n += 1;
			i = 0;	
			for j in range(0,field_count):
				if (len(field[j]) >0 ):
					if(int(row[i]) <=0 ):
						row[i] = 1;
					result_tmp += "{\"field\":\"%s\",\"rowspan\":%s}," %((str(field[j])).replace('\\','\\\\').replace('\t',' ').replace('\n','<br>').replace('\r','<br>'),str(row[i]));
					if (j < (field_count-1) and group[j] != group[j+1]):
						i +=1 ;
			result_tmp = result_tmp[:-1];		
			result ="{\"data\":[%s],\"eindex\":\"%s\"}," %(result_tmp,str(eindex));
			
		else:
			for data in line:
				if len(data) == 0:
					continue;
				result_tmp += "{\"field\":\"%s\",\"rowspan\":1}," %((data.split(',')[1]).replace('\\','\\\\').replace('\r',' ').replace('\n','<br>'));
			result_tmp = result_tmp[:-1];	
			result ="{\"data\":[%s],\"eindex\":\"1\"}," %(result_tmp);
		return 0,result,'';
	except :
		return sys._getframe().f_lineno,None,ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1]));
	
	
###读取统计数据
@history_report.route('/get_data_report',methods=['GET', 'POST'])
def get_data_report():
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
	
	curpage = request.form.get('c_p1') ##当前 页码
	maxpage = int(request.form.get('m_p1')) ## 一页最大数量
	path_dir = request.form.get('p1') ## 读取文件的路径
	exp = int(request.form.get('e1'))##扩展文件标志
	index = int(request.form.get('i1')) ##文件标志
	field = request.form.get('f1') ###字段信息
	level = request.form.get('v1') ###
	stat = int(request.form.get('s1')) ### 统计 or 明细
	ifstatic = int(request.form.get('is'))
	if ifstatic:
		path = PREFIX_RPT_SRES + userCode +"/" + path_dir +"/";
	else:
		path = PREFIX_RPT_DRES + userCode +"/" + path_dir +"/";
	if curpage <0 or curpage == "":
		curpage = 1
	else:
		curpage = int(curpage)
		
	offset = maxpage*(curpage-1)
	
	##扩展文件标志
	max_index = offset/MAX_LINE + 1;
	offset = offset%MAX_LINE;
	
	##文件路径
	if exp == 1:# 扩展
		file_path = path  + "rpt.dat.%d.exp.%d"%(index,max_index)
	else:	
		file_path = path  + "rpt.dat.%d"%(max_index)
	
	if os.path.exists(path) == False:
		return "{\"Result\":false,\"info\":\"系统异常：路径不存在(%d)\"}" %(sys._getframe().f_lineno)
	if os.path.exists(file_path) == False:
		return "{\"Result\":false,\"info\":\"系统异常：文件不存在(%d)\"}" %(sys._getframe().f_lineno)
	file = open(file_path,'r');
	
	##{\"info\":,\"index\":1,\"row\"}
	#field  -> 1,会话标识;1,统计值;2,发生时间;2,统计值;3,发生地址;3,统计值
	##data  ->	8385	2017-12-20	29	192.168.0.44	1	1,7,2
	i = 0;
	##文件 跳过 offset
	field_count = 0;
	for ps in field.split(';'):
		if ps == "":
			continue;
		field_count += 1;
	
	while 1:		
		line = file.readline()
		if (not line) or (i >= offset):
			break
		i += 1;
	result = "";
	for i in range(0,maxpage):
		if not line: ##一个文件读取完毕 
			file.close();
			file = None;
			max_index += 1;
			if exp == 1:# 扩展
				file_path = path  + "rpt.dat.%d.exp.%d"%(index,max_index)
			else:	
				file_path = path  + "rpt.dat.%d"%(max_index)

			if os.path.exists(file_path) == False:
				break;
			file = open(file_path,'r');
			
		line=line[:-1];	
		ret,line = ChangeLine(line, level.split(';'), field_count);
		if ret :
			file.close();
			return "{\"Result\":false,\"info\":\"系统异常：解析失败(%d:%d)\"}" %(sys._getframe().f_lineno,ret)
		dat = line.split('\t');
		ret,result_tmp,error_msg = parse_line(dat,exp,stat,field_count);
		if ret :
			return "{\"Result\":false,\"info\":\"系统异常：%s(%d)\"}" %(error_msg,ret)
			
		result += result_tmp
		line = file.readline()
		
	result = result[:-1]	
	if file:
		file.close();
	return "{\"Result\":true,\"info\":[%s]}" %(result)
'''
2602 void StaticTask_getTotalDay(int year,int month,int *totalday){
2603     int day =0;
2604     char isyear = 0;
2605     if(((year%4==0)&&(year%100!=0))||(year%400==0)){
2606         isyear=1;
2607     }
2608     switch(month){ //根据月不同给day赋值进行计算 c
2609         case 1: //同时day还会用于保存当月天数后面的输出 ca
2610         case 3:
2611         case 5:
2612         case 7:
2613         case 8:
2614         case 10:
2615         case 12:day=31;break;
2616         case 4:
2617         case 6:
2618         case 9:
2619         case 11:day=30;break; // 根据是否闰年来决定2月多少天 c
2620         case 2:if(isyear==1){ day=29; break; }else{ day=28; break; }
2621     }
2622     *totalday = day;
2623 }
2561 void StaticTask_testweek(int year,int month,int *week,int *allday) {
2562     int totalDay=0, dayOfWeek, day=0, dayOfYear=0;
2563     char isyear =0;
2564     int i;
2565     if (((year%4==0)&&(year%100!=0))||(year%400==0)) isyear=1;
2566     for(i=1900; i<year; i++) {
2567         if (((i%4==0)&&(i%100!=0))||(i%400==0)) totalDay+=366;
2568         else totalDay+=365;
2569     }
2570     for (i=1; i<=month; i++) {
2571         switch (i) { //根据月不同给day赋值进行计算 c
2572             case 1: //同时day还会用于保存当月天数后面的输出 ca
2573             case 3:
2574             case 5:
2575             case 7:
2576             case 8:
2577             case 10:
2578             case 12:
2579                 day=31;
2580                 break;
2581             case 4:
2582             case 6:
2583             case 9:
2584             case 11:
2585                 day=30;
2586                 break;
2587             // 根据是否闰年来决定2月多少天 c
2588             case 2:
2589                 if (isyear==1) day=29;
2590                 else day=28;
2591                 break;
2592         }
2593         if (i<month) dayOfYear+=day;
2594     }
2595     //把用户输入的月份之前的所有天  /数进行加合  //将本年的天数加在之前计算的总天数上 
2596     totalDay += dayOfYear; // 把总天数对7取余计算出当月第一天是星期几 da
2597     dayOfWeek = (1+totalDay)%7;
2598     *week = dayOfWeek;
2599     *allday = totalDay;
2600 }
2625 void StaticTask_getTotalCol(int firstdayofweek,int totalday,int *totalcol){
2626     int open = 0;
2627     if(firstdayofweek==0)
2628         open = 7;
2629     else
2630         open = firstdayofweek;
2631     int colum = 1;
2632     int underday;
2633     if(open<8)
2634         underday = totalday - (7-open) ;
2635     else
2636         underday = totalday - (7-open) ;
2637     if(firstdayofweek==0)
2638         colum = 0;
2639     int undercol = underday/7;
2640     colum  = colum + undercol;
2641     int mod = underday%7;
2642     if(mod>0)
2643         colum ++;
2644     *totalcol = colum;
2645 }
2646 
'''	
###获取 当月的所有日子
def StaticTask_getTotalDay(year,month):
	isyear = 0;
	if(((year%4==0) and (year%100!=0)) or (year%400==0)):
		isyear = 1;
	if month== 1 or  month== 3 or  month== 5 or  month== 7 or  month== 8 or  month== 10 or  month== 12:
		day = 31;
	elif month== 4 or month== 6 or month== 9 or month== 11:
		day = 30;
	else:
		if isyear == 1:
			day = 29;
		else:
			day = 28;
	return day
###获取 报表名字和是否需要下载
def StaticTask_get_report_info(dir_path,one_dir,type):
	file_path = dir_path +'/' + one_dir;
	file_abs = file_path+'/' +'rpt.abs';
	file_xml = file_path+'/' +'rpt.xml';
	downfile = 0;
	filetype = 'HTML';
	if os.path.exists(file_abs) == False:
		if os.path.exists(file_path + '/' +'xls.tgz'):
			filetype = "XLS"
		elif os.path.exists(file_path + '/' +'pdf.tgz'):
			filetype = "PDF"
		elif os.path.exists(file_path + '/' +'xml.tgz'):
			filetype = "XML"
		elif os.path.exists(file_path + '/' +'rtf.tgz'):
			filetype = "RTF"
		elif os.path.exists(file_path + '/' +'doc.tgz'):
			filetype = "DOC"
		else:
			return sys._getframe().f_lineno,'',"tgz文件不存在";
		downfile = 1;
		file_path = '/'.join(file_path.split('/')[-3:]);
	else:
		file_path = '/'.join(file_path.split('/')[-3:])
	fp = open(file_xml,'r');
	line = '';
	while(True):
		line = fp.readline();
		if line.find('<RptName>')>=0:
			break;
	##		
	name = (line.split('<RptName>')[1]).split('</RptName>')[0];
	line = '';
	while(True):
		line = fp.readline();
		if not line:
			break;
		if line.find('<NextExecuteTime>')>=0:
			break;
	if line != '':
		NextExecuteTime = (line.split('<NextExecuteTime>')[1]).split('</NextExecuteTime>')[0].replace('T','');
	else:
		NextExecuteTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	
	fp.close();
	
	result="{\"path\":\"%s\",\"name\":\"%s\",\"downfile\":%d,\"type\":\"%s\",\"NextExecuteTime\":\"%s\",\"filetype\":\"%s\"}," %(file_path,name,downfile,type,NextExecuteTime,filetype)
	return 0,result,"";			
##获取静态数据列表
@history_report.route('/get_static_candler',methods=['GET', 'POST'])
def get_static_candler():
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
	year = int(request.form.get('y1'))
	month = int(request.form.get('m1'))
	total_day = StaticTask_getTotalDay(year,month);
	all_candler="";
	for day in range(0,total_day):
		#sprintf(dir, PREFIX_RPT_SRES"%s/%d-%02d-%02d", user, year, month, day+1);
		dir_path = PREFIX_RPT_SRES + "%s/%d-%02d-%02d" %(userCode,year,month,day+1);
		if os.path.exists(dir_path) == False:
			continue;	
		dir_list = os.listdir(dir_path);
		one_str = "";
		d_str = "";
		w_str = "";
		m_str = "";
		for one_dir in dir_list:
			###day 
			#one_str = "{\"date\":\"%d-%02d-%02d\"}"%(year,month,day+1);
			if one_dir.find('d') >=0:				 
				ret,res,error_msg = StaticTask_get_report_info(dir_path,one_dir,'green');
				if(ret):
					continue
					#return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(error_msg,sys._getframe().f_lineno)
					
				d_str +=res;
				#d_str = d_str[:-1];
			if one_dir.find('w') >=0:				 
				ret,res,error_msg = StaticTask_get_report_info(dir_path,one_dir,'red');
				if(ret):
					continue
					#return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(error_msg,sys._getframe().f_lineno)
				w_str +=res
				#w_str = w_str[:-1];
			if one_dir.find('m') >=0:				 
				ret,res,error_msg = StaticTask_get_report_info(dir_path,one_dir,'blue');
				if(ret):
					continue
					#return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(error_msg,sys._getframe().f_lineno)
				m_str +=res
				#m_str = m_str[:-1];
		d_str = d_str[:-1];
		w_str = w_str[:-1];
		m_str = m_str[:-1];
		one_str = "{\"date\":\"%d-%d-%d\",\"d\":[%s],\"w\":[%s],\"m\":[%s]},"%(year,month,day+1,d_str,w_str,m_str);
	
		all_candler +=  one_str;
	all_candler = all_candler[:-1];
	return "{\"Result\":true,\"info\":[%s]}" %(all_candler)
	
	
##删除静态报表数据
@history_report.route('/del_static_report_data',methods=['GET', 'POST'])
def del_static_report_data():	
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
	if check_role(userCode,'报表管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	path = request.form.get('p1')	
	path =  PREFIX_RPT_SRES + '/'+ str(path);
	oper = request.form.get('o1')
	module_name = '运维报表>计划任务'
	content = "[global]\nclass = taskglobal\ntype = deldirs\npath=%s\n" %(path)
	ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
	if ss == False:
		if not system_log(userCode,oper,'系统异常',module_name):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
	if not system_log(userCode,oper,'成功',module_name):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return "{\"Result\":true,\"info\":\"\"}"	

##取消
@history_report.route('/cancel_report',methods=['GET', 'POST'])
def cancel_report():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	module_name=request.form.get('z3')
	if module_name<0:
		module_name='运维报表>生成报表'
	else:
		module_name=module_name.replace('-','>')
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		id = request.form.get('z1')
		id_name=request.form.get('z2')
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "update private.\"DataReportTask\" set \"CancelStatus\" =1 where \"TaskId\" =%s ;" % (id)
			curs.execute(sql)
			conn.commit();
			if not system_log(userCode,'取消手动生成任务：%s'%(id_name),'成功',module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#(zqy_8)
@history_report.route('/update_material_name',methods=['GET', 'POST'])
def update_material_name():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	name = request.form.get('z1')
	f_id = request.form.get('z2')
	back_type = request.form.get('z3')
	back_type = str(back_type)
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(userCode,'报表管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if f_id.isdigit():
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if checkaccount(name) == False:
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "update public.\"DataReportGlobalCfg\" set \"ReportBGName\" =E\'%s\' where \"Id\" =%s ;" % (name,f_id)
			curs.execute(sql)
			conn.commit();
			task_content = '[global]\nclass=taskWaterMark\ntype=getWaterMark\nwatername=%s\n' % (name)
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				if(back_type=="1"):
					if not system_log(userCode,'编辑报表素材（水印背景：%s）' % name,'任务下发异常','运维报表>报表素材'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				elif(back_type=="0"):
					if not system_log(userCode,'编辑报表素材（水印背景：%s）' % name,'任务下发异常','运维报表>模板管理'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					if not system_log(userCode,'编辑报表素材（水印背景：%s）' % name,'任务下发异常','运维报表>生成报表'):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
			
			if(back_type=="1"):
				if not system_log(userCode,'编辑报表素材（水印背景：%s）' % (name),'成功','运维报表>报表素材'):	
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			elif(back_type=="0"):
				if not system_log(userCode,'编辑报表素材（水印背景：%s）' % (name),'成功','运维报表>模板管理'):	
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				if not system_log(userCode,'编辑报表素材（水印背景：%s）' % (name),'成功','运维报表>生成报表'):	
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	
###获取 当前任务的 下一次执行时间 和 报表类型 动态 or 静态 （天 周 月）
@history_report.route('/get_taskinfo',methods=['GET', 'POST'])
def get_taskinfo():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('id')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select "NextExecuteTime","Type" from private."DataReportTask" where "TaskId" =%d;' %(int(id))
			curs.execute(sql)
			result = curs.fetchall();
			nextExecTime = result[0][0]
			Type = result[0][1]
			return "{\"Result\":true,\"nextExecTime\":\"%s\",\"Type\":%d}" %(nextExecTime,Type);
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

		
##批量获取 任务列表的状态
@history_report.route("/get_report_status", methods=['GET', 'POST'])
def get_report_status():
	session = request.form.get('a0')
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
		taskstr = request.form.get('t1')
		taskjson = json.loads(taskstr)
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		taskstatus = []
		taskidlist = [];
		for taskid in taskjson:
			taskidlist.append(str(taskid['TaskId']))
			sql = 'select "Status","CancelStatus" from private."DataReportTask" where "TaskId" = %d;' %(taskid['TaskId'])
			curs.execute(sql)
			results = curs.fetchall()
			if results == None or results[0] == None:
				status = 3
				CancelStatus = 0;
			else:
				status = results[0][0]
				CancelStatus = results[0][1]
				
			taskstatus.append(str(status)+','+str(CancelStatus))
		new_dict = dict(zip(taskidlist, taskstatus))
		
		'''
		keys = [1, 2, 3, 4]
		values = [55, 56, 57, 58]	  
		new_dict = dict(zip(keys, values))
		'''
		return str(new_dict).replace('u','').replace('\'','"');
		
	except:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d:%s)\"}" %(ErrorEncode(str(sys.exc_info()[0])+str(sys.exc_info()[1])),sys._getframe().f_lineno)

@history_report.route("/get_manage_user", methods=['GET', 'POST'])
def get_manage_user():
	session = request.form.get('a0')
	_type = request.form.get('z1')
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
			curs.execute("select public.\"PGetUser\"(null,%s,E'%s');" % (_type,usercode))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
