#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import sys
import os
import base64
import csv
import pyodbc
import re
import codecs
import shutil
import MySQLdb
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from htmlencode import parse_sess
from htmlencode import check_role
from logbase import common
from logbase import defines
from logbase import task_client
from urllib import unquote
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
import_file = Blueprint('import_file',__name__)

ERRNUM_MODULE_BATCH = 1000
ERRNUM_MODULE_host = 2000
#UPLOAD_FOLDER = '/var/tmp/zdp'
UPLOAD_FOLDER = '/usr/storage/.system/upload'
pro_data = []
ad_data = []
con_data = []
dev_data = []
host_data = []
hg_data = []
#HTMLEncode 
def HTMLEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

def checkip(ip):
	p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
	if p.match(ip):
		return True
	else:
		return False

def checkpro(pro):  
    p = re.compile('^[\w\-\s]+$')  
    if p.match(pro):  
        return True  
    else:  
        return False

def checkname(name):
	p = re.compile(u'^[\w\-\u4e00-\u9fa5]+$')
	if p.match(name):
		return True
	else:
		return False
		
def debug(c):
	return 0
	# path = "/var/tmp/debugzdp_test.txt"
	path = "/var/tmp/debughrj.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@import_file.route('/import_data',methods=['GET', 'POST'])
def import_data():
	debug("in import_data")
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	cover = request.form.get('z1')
	use_BH = request.form.get('a99')
	if use_BH=='0':
		f = request.files['file_change1']
		file_v=secure_filename(f.filename)
	else:
		file_v = request.form.get('file_v')
		file_change = request.form.get('file_change')
	client_ip = request.remote_addr;
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if check_role(system_user,'主机管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	fname = str(system_user) + '.' + str(se) + '.' + file_v
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	debug("file_pwd:"+file_pwd)
	debug("fname::"+fname)
	if use_BH=='0':
		f.save(os.path.join(UPLOAD_FOLDER, fname))
	else:
		shutil.move(file_change,file_pwd)
	debug("12313")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:#新建任务
			curs = conn.cursor()
			if len(fname.split('.')[-1]) == 4:
				taskname = secure_filename(file_v)[:-5]
			else:
				taskname = secure_filename(file_v)[:-4]
			data_json = '{"HostLeadInTaskId":0,"HostLeadInTaskName":"%s","Type":1,"Status":4,"UserCode": "%s"}' % (MySQLdb.escape_string(taskname).decode("utf-8"),system_user)
			sql = 'select public."PSaveHostLeadInTaskDetail"(E\'%s\')' % (MySQLdb.escape_string(data_json).decode("utf-8"))
			#debug("sql:%s" % sql)
			debug("import_data::"+sql)
			curs.execute(sql)
			result = curs.fetchall()[0][0].encode('utf-8')
			r_j = json.loads(result)
			debug(str(r_j))
			pwd_array = file_pwd.split('/')
			sql = "insert into private.\"HostImportTask\"(\"HostImportTaskId\",\"HostImportTaskName\") VALUES (%d,E\'%s\')" % (r_j['HostLeadInTaskId'],MySQLdb.escape_string(taskname).decode("utf-8"))
			curs.execute(sql)
			debug("insert sql:::"+sql);
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	task_content = '[global]\nclass = taskimport_host\ntype = execute_cmd\nfile_pwd=\"%s\"\ncover=\"%s\"\ntaskid=\"%s\"\nusercode=\"%s\"\nclientip=\"%s\"\n' % (file_pwd,cover,str(r_j['HostLeadInTaskId']),system_user,client_ip)
	debug(task_content)
	debug("-----------")
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		debug("hhhhhhh")
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
	#result = import_data_all(file_pwd,cover)
	#save_pro()
	#save_AD()
	#save_con()
	#save_dev()
	#save_host()
	debug("resultcccccccccc")
	return "{\"Result\":true}"
	debug("kkkkkkkkkkkkkkkkk")
	return render_template('host_list.html',result=result)
'''
if __name__=='__main__':
	save_data()
'''
