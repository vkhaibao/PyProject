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
import chardet
import base64
import chardet
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import task_client
from logbase import defines

from werkzeug.utils import secure_filename
from urllib import unquote
import htmlencode
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
batch_operation = Blueprint('batch_operation',__name__)

SIZE_PAGE = 20
def debug(c):
    return 0
    path = "/var/tmp/debuglhbatch.txt"
    fp = open(path,"a+")
    if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
def debug1(c):
    return 0
    path = "/var/tmp/debuglhbatch.txt"
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
def HTMLEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	

#1创建 2编辑 3列表
@batch_operation.route('/batch_index',methods=['GET','POST'])
def batch_index():
	tasktype = request.form.get("tasktype")
	TaskId = request.form.get("taskid")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	
	if tasktype and str(tasktype).isdigit() == False:
		return '',403	
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if TaskId and str(TaskId).isdigit() == False:
		return '',403
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
	e = e.replace('(','').replace(')','');
	
	
	if tasktype < 0:
		tasktype = "1"
	if e < 0 or e==None:
		e = ":"
	if search_typeall < 0 or search_typeall==None:
		search_typeall = ""
	NewId = 0
	if tasktype == "1" or tasktype == "2":
		if tasktype == "1":
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
					sql="SELECT nextval('\"BatchPlan_BatchPlanId_seq\"'::regclass);"
					curs.execute(sql)
					NewId = curs.fetchall()[0][0]
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)			
		t = "batch_start.html"
	if tasktype == "3":
		t = "batch_list.html"
		TaskId="0"
	return render_template(t,tasktype=tasktype,TaskId=TaskId,paging=paging,search_typeall=search_typeall,e=e,NewId=NewId)

#创建 or 编辑
@batch_operation.route('/SaveBatchSTask',methods=['GET','POST'])
def SaveBatchSTask():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')
	taskid = request.form.get('a2')
	taskiname = request.form.get('a3')	
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
			
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(jsondata);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	data = json.loads(jsondata)
	data['ClientIp'] = client_ip
	Taskid = data['BatchPlanId']
	debug("before base64")
	data['BatchWork'] = base64.b64encode(data['BatchWork'])
	debug("after base64")
	jsondata = json.dumps(data)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PSaveBatchPlan\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if 'false' in result:
				return result
			# task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=11\nid=%s\n' % (Taskid)
			# debug(task_content)
			# if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			# 	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			conn.commit()
			'''
			srcinfo = {"usercode":"usercode","srcip":"srcip"}
			srcinfo['usercode'] = system_user
			srcinfo['srcip'] = client_ip
			srcinfo = json.dumps(srcinfo)
			sql="select public.\"PUpdateHNodeSelected\"(11,%s,'%s');" %(Taskid,MySQLdb.escape_string(srcinfo).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			'''
			##[global]
			#class=taskupdatehnodeselected
			#type=update_run
			#id_type=id_type
			#id=id
			task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=11\nid=%s\n' % (Taskid)
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			fdir = "/usr/storage/.system/batch/task/"+str(Taskid)+"/"
			debug(fdir)
			#创建文件夹
			if not os.path.exists(fdir):
				os.makedirs(fdir)

			BatchType_Str = ""
			if int(data['BatchType']) == 1:
				BatchType_Str = "Windows,*unix批处理"
				data['BatchWork'] = base64.b64decode(data['BatchWork'])
				BatchWork_array = data['BatchWork'].split(';')
				BatchWork = "，指令文件："+'、'.join(BatchWork_array)
			elif int(data['BatchType']) == 2:
				BatchType_Str = "MYSQL批处理"
				data['BatchWork'] = base64.b64decode(data['BatchWork'])
				BatchWork = "，指令："+str(data['BatchWork'])
			elif int(data['BatchType']) == 3:
				BatchType_Str = "ORACLE批处理"
				data['BatchWork'] = base64.b64decode(data['BatchWork'])
				BatchWork = "，指令："+str(data['BatchWork'])

			ExecuteTime = ""
			if str(data['Execution']) == "True":
				ExecuteTime = "立即执行"
			else:
				ExecuteTime = data['StartTime'].replace('T',' ')
				PeriodValue = ""
				if int(data['PeriodType']) == 1:
					PeriodValue = str(data['PeriodValue'])+"天"
				else:
					PeriodValue = str(data['PeriodValue'])+"分钟"
				ExecuteTime += '，重复周期'+PeriodValue

			debug(ExecuteTime)
			flag = 1
			if int(taskid) == 0:
				taskid = int(data['BatchPlanId'])
				flag = 0

			get_data = '{"LoginUserCode":"'+system_user+'","BatchPlanId":'+str(taskid)+'}'
			get_data = "'%s'" % get_data
			debug("select public.\"PGetBatchPlan\"(%s);"%(get_data))
			curs.execute("select public.\"PGetBatchPlan\"(%s);"%(get_data))
			re_data = curs.fetchall()[0][0].encode('utf-8')
			re_data = json.loads(re_data)

			auth_obj = []
			if re_data['data'][0]['AccountSet'] != None and len(re_data['data'][0]['AccountSet']) != 0:
				auth_account = ""
				flag_g = 0
				for authobj in re_data['data'][0]['AccountSet']:
					if flag_g >= 1000:
						break
					auth_account = '[' + authobj['HGName'] + ']-' + authobj['HostName'] + '-' + authobj['AccountName']
					auth_obj.append(auth_account)
					flag_g += 1
				auth_obj_str = '、'.join(auth_obj)
			else:
				auth_obj_str = ""
				for i in re_data['data'][0]['AuthScope'][0]['IPList']['Set']:
					auth_obj_str += i['StartIP'] + '-' + i['EndIP'] + '  '
			ContentStr = "协议："+BatchType_Str+"，开始时间："+ExecuteTime+BatchWork+"，范围："+auth_obj_str

			if flag == 0:
				system_log(system_user,"创建批量执行计划：%s (%s)" % (taskiname,ContentStr),"成功","批量执行")
			else:
				system_log(system_user,"编辑批量执行计划：%s (%s)" % (taskiname,ContentStr),"成功","批量执行")

			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#显示 or 分页 or 搜索
@batch_operation.route('/GetBatchStart_list',methods=['GET', 'POST'])
def GetBatchStart_list():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')

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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetBatchPlan\"(E'%s');"% (MySQLdb.escape_string(jsondata).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results = json.loads(results)
			for i in results['data']:
				debug("before base64")
				debug(str(i['BatchWork']))
				i['BatchWork'] = base64.b64decode(i['BatchWork'])
				debug("after base64")
			results = json.dumps(results)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#删除batch start task
@batch_operation.route('/DelBatchStartTask',methods=['GET', 'POST'])
def DelBatchStartTask():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	FromFlag = request.form.get('a10')
	if session < 0:
		session=""
	if id_str < 0:
		id_str=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			Name_array = []
			for id in ids:
				id=int(id)
				# PDeleteConnParam(id)
				get_data = '{"LoginUserCode":"'+system_user+'","BatchPlanId":'+str(id)+'}'
				get_data = "E'%s'" % get_data
				debug("select public.\"PGetBatchPlan\"(%s);"%(get_data))
				curs.execute("select public.\"PGetBatchPlan\"(%s);"%(get_data))
				re_data = curs.fetchall()[0][0].encode('utf-8')
				re_data = json.loads(re_data)
				Name_array.append(re_data['data'][0]['BatchPlanName'])

				sql = "select public.\"PDeleteBatchPlan\"(%d);" % (id)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				if "false" in result:
					return result
				else:
					fdir = "/usr/storage/.system/batch/task/"+str(id)+"/"
					if os.path.exists(fdir):
						for file_name in os.listdir(fdir):
							fdir_file = "/usr/storage/.system/batch/task/"+str(id)+"/"+file_name+""
							os.remove(fdir_file)
						os.rmdir(fdir)
			conn.commit()
			if "false" in result:
				ret = json.loads(result)
				system_log(system_user,"删除批量执行计划：%s" % ('、'.join(Name_array)),"失败："+ret['ErrMsg'],FromFlag)
			else:
				system_log(system_user,"删除批量执行计划：%s" % ('、'.join(Name_array)),"成功",FromFlag)
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#import batch start file
@batch_operation.route('/ImportBstartFile',methods=['GET', 'POST'])
def ImportBstartFile():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	TaskID = request.form.get('a1')
	f = request.files['file_change']
	debug(f.filename)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"

	#创建文件夹
	if not os.path.exists(fdir):
		os.makedirs(fdir)

	fname = secure_filename(f.filename)
	file_pwd = os.path.join(fdir,fname)
	debug(file_pwd)
	f.save(os.path.join(fdir, fname))
	debug("12313")

	return "{\"Result\":true}"

#del batch start file
@batch_operation.route('/DeleteBstartFile',methods=['GET', 'POST'])
def DeleteBstartFile():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	TaskID = request.form.get('a1')
	filename = request.form.get('a2')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	filename = filename.replace(' ','_')
	fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"+filename+""

	#检查目录是否存在
	if not os.path.exists(fdir):
		return "{\"Result\":false,\"ErrMsg\":\"文件路径不存在(%d)\"}" %(sys._getframe().f_lineno)
	os.remove(fdir)
	return "{\"Result\":true}"

#read batch start file
@batch_operation.route('/ReadBstartFile',methods=['GET', 'POST'])
def ReadBstartFile():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	TaskID = request.form.get('a1')
	filename = request.form.get('a2')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)


	filename = filename.replace(' ','_')
	fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"+filename+""
	if filename.find('/') >=0:
		return '',403
		
	debug(fdir)

	if not os.path.exists(fdir):
		return "{\"Result\":false,\"ErrMsg\":\"文件路径不存在(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with open(fdir, 'r') as f:
			content = f.read()
			fencoding = chardet.detect(content)
			debug("fencoding %s" %(str(fencoding)))
			if fencoding['encoding'] != 'utf-8':
				content = content.decode('GB2312','ignore')
				content = content.replace("\\","\\\\")
				content = content.replace("/","\\/")
				content = content.replace('"',"\\\"")
			f.close()
			return "{\"Result\":true,\"Content\":\"%s\"}" %(content)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#edit batch start file
@batch_operation.route('/SaveBstartFile',methods=['GET', 'POST'])
def SaveBstartFile():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	TaskID = request.form.get('a1')
	filename = request.form.get('a2')
	filecontent = request.form.get('a3')
	fileNewName = request.form.get('a4')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"+filename+""
	fdir_n = "/usr/storage/.system/batch/task/"+TaskID+"/"+fileNewName+""

	if not os.path.exists(fdir):
		return "{\"Result\":false,\"ErrMsg\":\"文件路径不存在(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with open(fdir, 'w') as f:
			filecontent = filecontent.encode('utf-8')
			f.write(filecontent)
			f.close()
			os.rename(fdir,fdir_n)
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#edit batch start file
@batch_operation.route('/CreateBstartFile',methods=['GET', 'POST'])
def CreateBstartFile():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	TaskID = request.form.get('a1')
	filename = request.form.get('a2')
	filecontent = request.form.get('a3')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"
	#创建文件夹
	if not os.path.exists(fdir):
		os.makedirs(fdir)

	try:
		fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"+filename+""
		with open(fdir, 'w') as f:
			filecontent = filecontent.encode('utf-8')
			f.write(filecontent)
			f.close()
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#get batch start file list
@batch_operation.route('/GetBstartFileList',methods=['GET', 'POST'])
def GetBstartFileList():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	TaskID = request.form.get('a1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	fdir = "/usr/storage/.system/batch/task/"+TaskID+"/"

	#创建文件夹
	if not os.path.exists(fdir):
		return "{\"Result\":false,\"ErrMsg\":\"文件路径不存在(%d)\"}" %(sys._getframe().f_lineno)

	files = []
	for file_name in os.listdir(fdir):
		files.append(file_name)
	files = ','.join(files)
	return "{\"Result\":true,\"Files\":\"%s\"}" %(files)

#启用任务
@batch_operation.route('/StartBatchSTask',methods=['GET','POST'])
def StartBatchSTask():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	taskid = request.form.get('a1')
	debug("taskid")
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="update public.\"BatchPlan\" set \"Enabled\" = true,\"LastExecuteTime\" = Null where \"BatchPlanId\" = %s;" %(taskid)
			debug(sql)
			curs.execute(sql)
			conn.commit()

			Name = ""
			sql = 'select "BatchPlan"."BatchPlanName" from "BatchPlan" where "BatchPlan"."BatchPlanId" = %d;' % int(taskid)
			debug(sql)
			curs.execute(sql)
			Name = curs.fetchall()[0][0]

			system_log(system_user,"启用批量执行计划：%s" % Name,"成功","批量执行")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

		#创建 or 编辑

#停用计划
@batch_operation.route('/StopBatchSTask',methods=['GET','POST'])
def StopBatchSTask():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	taskid = request.form.get('a1')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="update public.\"BatchPlan\" set \"Enabled\" = false where \"BatchPlanId\" = %s;" %(taskid)
			debug(sql)
			curs.execute(sql)
			conn.commit()

			Name = ""
			sql = 'select "BatchPlan"."BatchPlanName" from "BatchPlan" where "BatchPlan"."BatchPlanId" = %d;' % int(taskid)
			debug(sql)
			curs.execute(sql)
			Name = curs.fetchall()[0][0]

			system_log(system_user,"停用批量执行计划：%s" % Name,"成功","批量执行")

			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#取访问页面主机信息
@batch_operation.route('/get_hostdirectory_b',methods=['GET','POST'])
def get_hostdirectory_b():
		session = request.form.get('a0')
		hid = request.form.get('a1')
		aid = request.form.get('a2')
		find_doing = request.form.get('a3')
		TaskType = request.form.get('a4')
		client_ip = request.remote_addr
		(error,usercode,mac) = SessionCheck(session,client_ip);
		if error < 0:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			aid = '-1'
		if TaskType < 0:
			TaskType = 0
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				if aid != '-1':
					if str(find_doing) == 'true':
						debug("select public.\"PGetHostDirectory\"(E'%s',%d,11,%d,null,null,%s,%d);" %(usercode,int(hid),int(aid),str(find_doing),int(TaskType)))
						curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,11,%d,null,null,%s,%d);" %(usercode,int(hid),int(aid),str(find_doing),int(TaskType)))
					else:
						debug("select public.\"PGetHostDirectory\"(E'%s',%d,11,%d,null,null,false,%d);" %(usercode,int(hid),int(aid),int(TaskType)))
						curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,11,%d,null,null,false,%d);" %(usercode,int(hid),int(aid),int(TaskType)))
				else:
					debug("select public.\"PGetHostDirectory\"(E'%s',%d,11,null,null,null,false,%d);" %(usercode,int(hid),int(TaskType)))
					curs.execute("select public.\"PGetHostDirectory\"(E'%s',%d,11,null,null,null,false,%d);" %(usercode,int(hid),int(TaskType)))
				results = curs.fetchall()[0][0].encode('utf-8')
				return results
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#取访问页面主机信息
@batch_operation.route('/GetAuthObject_B',methods=['GET','POST'])
def GetAuthObject_B():
	session = request.form.get('a0')
	hgid = request.form.get('a1')
	hostIP = request.form.get('a2')			# default -> null
	find_doing = request.form.get('a3')
	protoType = request.form.get('a4')
	serverName = request.form.get('a5')	# default -> null
	search_json = request.form.get('a6')# default -> null

	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		aid = '-1'

	if hostIP < 0:
		hostIP = 'null'
	else:
		hostIP = "'%s'" %(hostIP)
	if serverName < 0:
		serverName = 'null'
	else:
		serverName = "'%s'" %(serverName)			
	if search_json < 0:
		search_json = 'null'

	if protoType == '1':
		protoType = "'SYSBATCH'"
	elif protoType == '2':
		protoType = "'MYSQL'"
	elif protoType == '3':
		protoType = "'ORACLE'"
	elif protoType == '4':
		protoType = "'SYSBATCHSTART'"
	else:
		protoType = 'null'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#select public."GetAuthObjectByLevel"('lh','192.168.0.123',null,'SYSBATCH','4',192.168.0.84',RDP,null,null,null,null,null,null,null,null,null,null);
			if search_json == 'null':
				debug("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,%s,%s,null,null,null,null,null,null,null,null,null,null);" %(usercode,client_ip,protoType,int(hgid),hostIP,serverName))
				curs.execute("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,%s,%s,null,null,null,null,null,null,null,null,null,null);" %(usercode,client_ip,protoType,int(hgid),hostIP,serverName))
			else:
				debug("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,%s,%s,null,null,null,null,null,null,null,null,null,E'%s');" %(usercode,client_ip,protoType,int(hgid),hostIP,serverName,MySQLdb.escape_string(search_json).decode("utf-8")))
				curs.execute("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,%s,%s,null,null,null,null,null,null,null,null,null,E'%s');" %(usercode,client_ip,protoType,int(hgid),hostIP,serverName,MySQLdb.escape_string(search_json).decode("utf-8")))

			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#取批量执行计划任务
@batch_operation.route('/get_batch_task',methods=['GET','POST'])
def get_batch_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
			sys.exit()

	jsondata = request.form.get('a1')
	try:
		with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sqlStr = "select public.\"PGetBatchTask\"(E'%s');" % (MySQLdb.escape_string(jsondata).decode("utf-8"))
			curs.execute(sqlStr)           
			result = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#取批量执行计划任务结果
@batch_operation.route('/get_batch_taskdetails',methods=['POST','GET'])
def get_batch_taskdetails():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
			sys.exit()

	jsondata = request.form.get('a1')
	try:
		with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sqlStr = "select public.\"PGetBatchResult\"(E'%s');" % (MySQLdb.escape_string(jsondata).decode("utf-8"))
			curs.execute(sqlStr)
			result = curs.fetchall()[0][0].encode('utf-8')
			result = json.loads(result)
			for i in result['data']:
				#debug("before base64")
				#debug(str(i['ExeResultLog']))
				if i['ExeResultLog'] == None:
					i['ExeResultLog'] = ''
				else:
					try:				
						i['ExeResultLog'] =base64.b64decode(i['ExeResultLog']).decode('utf-8')
					except:
						i['ExeResultLog'] =base64.b64decode(i['ExeResultLog']).decode('gbk','ignore')	
					#i['ExeResultLog'] = base64.b64decode(i['ExeResultLog']).decode('gbk').encode('utf-8')
					#i['ExeResultLog'] = base64.b64decode(i['ExeResultLog']).decode('utf-8').replace('\r','').replace('\n','').replace('\t','')
				#debug("after base64")
			result = json.dumps(result)
			return "{\"Result\":true,\"info\":%s}" % result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

###获取客户端IP
@batch_operation.route('/GetIPAddr',methods=['GET','POST'])
def GetIPAddr():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	return "{\"Result\":true,\"info\":\"%s\"}" %(client_ip)

#批量启动：获取选中账号
@batch_operation.route('/Get_EnabledAccount',methods=['GET', 'POST'])
def Get_EnabledAccount():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	jsondata = request.form.get('a1')

	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	data = json.loads(jsondata)
	data['SrcIp'] = client_ip
	data['LoginUserCode'] = system_user
	jsondata = json.dumps(data)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetAccountForBatchStart\"(E'%s');"% (MySQLdb.escape_string(jsondata).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if str(results) == 'None':
				results = []
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@batch_operation.route('/save_WorkOrder_Apply',methods=['GET','POST'])
def save_WorkOrder_Apply():
	data = request.form.get('a1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			#curs = conn.cursor()
			data_json = json.loads(data)
			data_json['LoginUserCode'] = usercode
			data_json['SrcIp'] = client_ip
			data = json.dumps(data_json)
			debug("select public.\"PSaveApplyWorkOrder\"(E\'%s\');"%(data))
			curs.execute("select public.\"PSaveApplyWorkOrder\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0]
			debug(str(results))
			results_json=json.loads(results)
			if results == None or results_json['Result'] == False:
				debug("111111111")
				system_log(usercode,"发起工单申请:%s" % data_json['WorkOrderName'],"失败","工单申请")
				debug("22222222")
				return results

			id_array = []
			a_tmp = results_json['AdminSet']
			for i in a_tmp:
				id_dic = {"Admin":0,"Id":0}
				id_dic['Admin'] = int(i['AdminSet'][0]['AdminId'])
				curs.execute("select \"User\".\"UserCode\" from public.\"User\" where \"User\".\"UserId\"=%d;" %(id_dic['Admin']))
				id_tmp = curs.fetchall()[0][0]
				id_dic['Admin'] = str(id_tmp)
				id_dic['Id'] = int(i['WorkOrderId'])
				id_array.append(id_dic)
			debug(str(id_array))
			for i in id_array:
				get_data = '{"loginusercode":"'+str(i['Admin'])+'","workorderid":'+str(i['Id'])+',"limitrow":null,"offsetrow":null}'
				get_data = "E'%s'" % get_data
				curs.execute("select public.\"PGetWorkOrder\"(%s);"%(get_data))
				debug("select public.\"PGetWorkOrder\"(%s);"%(get_data))
				curs.execute("select public.\"PGetWorkOrder\"(%s);"%(get_data))
				a = curs.fetchall()
				debug(str(a))
				re_data = a[0][0].encode('utf-8')
				debug(str(re_data))
				re_data = json.loads(re_data)
				_obj = ""

				scopename = ""
				if re_data['data'][0]['AuthScope'] != None and len(re_data['data'][0]['AuthScope']) != 0:
					for scope in re_data['data'][0]['AuthScope']:
						scopename = scopename + scope['ServerScopeName'] + ','
					scopename = scopename[:-1]

				auth_obj = []
				if re_data['data'][0]['AuthObject'] != None and len(re_data['data'][0]['AuthObject']) != 0:
					auth_hg = ""
					auth_host = ""
					auth_account = ""
					flag_n = 0
					for authobj in re_data['data'][0]['AuthObject']:
						if flag_n >= 1000:
							break
						if authobj['AccountName'] != None:
							auth_account = auth_account + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + '-' + authobj['AccountName'] + ','
						elif authobj['HostName'] != None:
							auth_host = auth_host + '[' + authobj['HGName'] + ']-' + authobj['HostName'] + ','
						else:
							auth_hg = auth_hg + '[' + authobj['HGName'] + '],'
						flag_n += 1
					if auth_hg != "":
						auth_hg = "指定主机组：" + auth_hg[:-1]
						auth_obj.append(auth_hg)
					if auth_host != "":
						auth_host = "指定主机：" + auth_host[:-1]
						auth_obj.append(auth_host)
					if auth_account != "":
						auth_account = "指定账号：" + auth_account[:-1]
						auth_obj.append(auth_account)
					auth_obj_str = '，'.join(auth_obj)

				auth_obj_str = '，'.join(auth_obj)
				if scopename != "":
					_obj = _obj + '，' + "服务器范围：" + scopename
					
				if auth_obj_str != "":
					_obj = auth_obj_str

				if re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName'].find('#') != -1:
					_obj = _obj + "，工单策略：#私有"
				else:
					_obj = _obj + "，工单策略：" + re_data['data'][0]['AccessStrategyInfo']['AccessStrategyName']

				data0 = json.loads(data)
				system_log(usercode,"发起工单申请:%s（%s）" % (data0['WorkOrderName'],_obj),"成功","工单申请")

			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###获取hostname
@batch_operation.route('/get_hostName',methods=['GET','POST'])
def get_hostName():
	session = request.form.get('a0')
	ip_str = request.form.get('a1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
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
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select \"Host\".\"HostName\" from public.\"Host\" where \"Host\".\"HostIP\"='%s';" %(str(ip_str))
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	curs.close()
	conn.close()
	return "{\"info\":\"%s\"}" %results

#过滤访问页面主机信息
@batch_operation.route('/FindAuthObject_B',methods=['GET','POST'])
def FindAuthObject_B():
	debug('FindAuthObject_B')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	filter = request.form.get('a1')
	protoType = request.form.get('a2')
	iType = request.form.get('a3')
	##++

	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if protoType == '1':
		protoType = "'SYSBATCH'"
	elif protoType == '2':
		protoType = "'MYSQL'"
	elif protoType == '3':
		protoType = "'ORACLE'"
	elif protoType == '4':
		protoType = "'SYSBATCHSTART'"
	else:
		protoType = 'null'

	filter = json.loads(filter)
	filter_hgname = ""
        filter_hname = ""
        filter_ip = ""
        filter_ser = ""
        filter_account = ""
        filter_all = ""
        if len(filter) != 0:
                for i in filter:
			debug(i)
                        index_i=i.index('-')
			debug(str(index_i))
			debug(i[0:index_i])
                        if i[0:index_i] == "0":
                                filter_all = filter_all + MySQLdb.escape_string(i[index_i+1:]) + '\n'
                        elif i[0:index_i] == "hgname":
                                filter_hgname = filter_hgname + MySQLdb.escape_string(i[index_i+1:]) + '\n'
                        elif i[0:index_i] == "hostname":
                                filter_hname = filter_hname + MySQLdb.escape_string(i[index_i+1:]) + '\n'
                        elif i[0:index_i] == "ip":
                                filter_ip = filter_ip + MySQLdb.escape_string(i[index_i+1:]) + '\n'
                        elif i[0:index_i] == "hostservicename":
                                filter_ser = filter_ser + MySQLdb.escape_string(i[index_i+1:]) + '\n'
                        elif i[0:index_i] == "accountname":
                                filter_account = filter_account + MySQLdb.escape_string(i[index_i+1:]) + '\n'
        if filter_all != "":
                filter_all = filter_all[:-1]
                filter_all = MySQLdb.escape_string(filter_all).decode('utf-8')
                filter_all=filter_all.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
        if filter_hgname != "":
                filter_hgname = filter_hgname[:-1]
                filter_hgname = MySQLdb.escape_string(filter_hgname).decode('utf-8')
                filter_hgname = filter_hgname.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
        if filter_hname != "":
                filter_hname = filter_hname[:-1]
		filter_hname=filter_hname.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
        if filter_ip != "":
                filter_ip = filter_ip[:-1]
                filter_ip = MySQLdb.escape_string(filter_ip).decode('utf-8')
                filter_ip = filter_ip.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
        if filter_ser != "":
                filter_ser = filter_ser[:-1]
                filter_ser = MySQLdb.escape_string(filter_ser).decode('utf-8')
                filter_ser = filter_ser.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
        if filter_account != "":
                filter_account = filter_account[:-1]
                filter_account = MySQLdb.escape_string(filter_account).decode('utf-8')
                filter_account = filter_account.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
	searchconn={
		"HGName":filter_hgname,
		"HostName":filter_hname,
		"HostIP":filter_ip,
		"HostServiceName":filter_ser,
		"AccountName":filter_account
	}
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PFindHostForAccess\"('%s','%s',null,%s,0,'%s',null,null,%s,'%s');" %(usercode,client_ip,protoType,filter_all,iType,json.dumps(searchconn)))
			curs.execute("select public.\"PFindHostForAccess\"(E'%s',E'%s',null,%s,0,E'%s',null,null,%s,E'%s');" %(usercode,client_ip,protoType,filter_all,iType,json.dumps(searchconn)))
			result = curs.fetchall()
			debug(str(result))
			if len(result) == 0:
				return "None"
			else:
				if result[0][0]==None:
					return 'None'
				results = result[0][0].encode('utf-8')
				results = json.loads(results)
				for index,item in enumerate(results):
					if item['HostIP'] != None:
						item['Name'] = item['Name'] +'\t'+ item['HostIP']
				return json.dumps(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#取搜索主机信息
@batch_operation.route('/get_hosts_B',methods=['GET','POST'])
def get_hosts_B():
	session = request.form.get('a0')
	hgid = request.form.get('a1')
	protoType = request.form.get('a2')
	debug1("get_hosts_B")

	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	debug1("param ok")
	if protoType == '1':
		protoType = "'SYSBATCH'"
	elif protoType == '2':
		protoType = "'MYSQL'"
	elif protoType == '3':
		protoType = "'ORACLE'"
	elif protoType == '4':
		protoType = "'SYSBATCHSTART'"
	else:
		protoType = 'null'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			a = []	#HGID
			b = []	#HOSTID
			debug1(str(hgid))
			c = hgid.split(',')
			debug1(str(c))
			for index1,item in enumerate(c):
				a.append(str(item.split(':')[0]))
				b.append(item.split(':')[1])
			debug1(str(a))
			group_str = ','.join(a)
			host_tmp = {"HostIP": "192.168.0.158","HostId": 2981,"HostName": "192.168.0.158","HGroupSet": [],"AccountSet": [],"ServiceSet": []}
			account_tmp = {"HostAccount":{"AccountId": 7,"AccountName": "SSO","AccountType": 3},"HostServiceSet":[]}
			result_data = []
			for index,item in enumerate(a):
				debug1("1111111111111111111111111111111111")
				hgid = item
				hid = b[index]
				sql = "select \"HostIP\",\"HostName\" from public.\"Host\" where \"HostId\"=%s" %(str(hid))
				curs.execute(sql)
				debug1(sql)
				result_host = curs.fetchall()
				host_tmp['HostIP'] = result_host[0][0]
				host_tmp['HostName'] = result_host[0][1]
				
				conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
				curs = conn.cursor()
				debug1("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,E'%s',null,null,null,null,null,null,null,null,null,null,null);" %(usercode,client_ip,protoType,int(hgid),str(host_tmp['HostIP'])))
				curs.execute("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,E'%s',null,null,null,null,null,null,null,null,null,null,null);" %(usercode,client_ip,protoType,int(hgid),str(host_tmp['HostIP'])))
				result_service = curs.fetchall()[0][0]
				service_json = json.loads(result_service)
				host_tmp['ServiceSet'] = service_json['data']
				for index1,item1 in enumerate(service_json['data']):
					debug1("enumerate")
					debug1(str(item1))

					sql = "select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',null,%s,%d,E'%s',E'%s',E'%s',null,null,null,null,null,null,null,null,null);" %(usercode,client_ip,protoType,int(hgid),str(host_tmp['HostIP']),item1['HostServiceName'],item1['ProtocolName'])
					debug1("755555555555")
					debug1(sql)
					conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
					curs = conn.cursor()
					curs.execute(sql)
					debug1("76666666666666")
					result_account = curs.fetchall()[0][0]
					account_json = json.loads(result_account)
					debug1(str(account_json))
					account_tmp = {"HostAccount":{"AccountId": 7,"AccountName": "SSO","AccountType": 3},"HostServiceSet":[]}
					debug1("fffff")
					for index2,item2 in enumerate(account_json['data']):
						debug1(str(item2))
						account_tmp['HostAccount'] = item2
						account_tmp['HostServiceSet'].append(item1)
						host_tmp['AccountSet'].append(account_tmp)
				result_data.append(host_tmp)
			result_all = {"Result": True,"info": [],"grp": "1"}
			result_all['info'] = result_data
			result_all['grp'] = group_str
			return json.dumps(result_all)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)


#取授权内账号
@batch_operation.route('/_get_Access',methods=['GET','POST'])
def _get_Access():
	session = request.form.get('a0')
	protoType = request.form.get('a1')

	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	  	return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)

	iType = 2
	if protoType == '1':
		protoType = "'SYSBATCH'"
	elif protoType == '2':
		protoType = "'MYSQL'"
	elif protoType == '3':
		protoType = "'ORACLE'"
	elif protoType == '4':
		protoType = "'SYSBATCHSTART'"
	else:
		iType = 1
		protoType = 'null'

	tmp_all = []
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#sql = "select public.\"GetAuthObject\"('%s','%s',null,%s);" %(usercode,client_ip,protoType)
                        sql = '''SELECT * FROM public."GetAuthObject"(E'%s',E'%s',null,%s) t
                                                WHERE 
                                                        (%d IS NULL OR
                                                                        (%d=1 AND t."AuthLevel" IN (2,3) AND 
                                                                                (EXISTS(
                                                                                        SELECT 1
                                                                                                FROM "AccessAuth" a
                                                                                                        JOIN "AccessStrategy" astr ON astr."AccessStrategyId" = a."AccessStrategyId"
                                                                                                        WHERE a."AccessAuthId" = t."Id" AND 
                                                                                                        astr."EnableWorkOrderApprove" IS TRUE AND astr."WorkOrderApproveStrategyId" IS NOT NULL
                                                                                )) 
                                                                        ) OR
                                                                (%d=2 AND t."AccountType" <> 0
                                                                ) OR
                                                                (%d=3 AND t."AccountType" <> 0
                                                                )
                                                        )''' %(usercode,client_ip,protoType,iType,iType,iType,iType)
			curs.execute(sql)
			result_all = curs.fetchall()
			for index,item in enumerate(result_all):
				item_array = item
				#sql = 'select "HostId" from public."Host" where "HostIP"=\'%s\'' %(item_array[5])
				#curs.execute(sql)
				#hostid = curs.fetchall()[0][0]

				account_tmp = {"HGId":'1',"HostId":1,"HostIP":'192.168.1.1',"AuthId":1,"AuthLevel":1,"AccountId": 7,"AccountName": "SSO","AccountType": 3,"HostServiceSet":{"Port": 24,"ServiceName": None,"ProtocolName": "TELNET","ProtocolId":1,"HostServiceId": 4882,"HostServiceName": "TELNET1"}}
				if str(item_array[1]) != '0':

					account_tmp['AccountId'] = item_array[6]
					account_tmp['HGId'] = item_array[4]
					account_tmp['HostId'] = item_array[25]
					account_tmp['HostServiceSet']['ProtocolId'] = item_array[17]
					account_tmp['HostServiceSet']['HostServiceId'] = item_array[15]
					account_str = 'G'+str(account_tmp['HGId'])+'@H'+str(account_tmp['HostId'])+'@S'+str(account_tmp['HostServiceSet']['HostServiceId'])+'@A'+str(account_tmp['AccountId'])
					tmp_all.append(account_str)

			return json.dumps(tmp_all)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#保存批量启动配置
@batch_operation.route('/Save_BatchCmd',methods=['GET','POST'])
def Save_BatchCmd():
	session = request.form.get('a0')
	CmdStr = request.form.get('z1')
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(CmdStr);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	
	server_ip = request.form.get('z2')
	sesstimet = request.form.get('z19')
	Cmdstr = base64.b64encode(CmdStr)
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	
	jsondata = {"ParamContent":"test1"}
	jsondata['ParamContent'] = Cmdstr
	debug1(str(jsondata))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql="select public.\"PSaveBatchStartParam\"(E'%s');" %(MySQLdb.escape_string(json.dumps(jsondata)).decode("utf-8"))
			debug1(sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result = json.loads(result)
			return_data = {"Id":0,"Session":123,"URL":'192.168.0.1'}
			return_data['Id'] = result['Id']
			return_data['Session'] = session
			return_data['UrlIp'] = server_ip
			return_data['sesstimet'] = sesstimet
			return_data = json.dumps(return_data)
			return_data = base64.b64encode(return_data)
			return return_data
	except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@batch_operation.route('/get_AccountProtocolForAuth_B',methods=['GET','POST'])
def get_AccountProtocolForAuth_B():
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
	data['ClientIp']=client_ip
	data=json.dumps(data)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetAccountProtocolForBatch\"(\'%s\');"%(data))
			curs.execute("select public.\"PGetAccountProtocolForBatch\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@batch_operation.route('/Get_SameAccountProtocolForAuth_B',methods=['GET','POST'])
def Get_SameAccountProtocolForAuth_B():
	data = request.form.get('z1')
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
	data=json.loads(data)
	data['LoginUserCode']=usercode
	data['ClientIp']=client_ip
	data=json.dumps(data)			
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetSameAccountProtocolForBatch\"(E\'%s\');"%(data))
			curs.execute("select public.\"PGetSameAccountProtocolForBatch\"(E\'%s\');"%(data))
			results = curs.fetchall()[0][0]
			if(not results):
				return "None"
			else:
				results = results.encode('utf-8')
				return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
