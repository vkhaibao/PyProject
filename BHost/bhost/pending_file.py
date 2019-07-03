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
import MySQLdb
import shutil
from unicodedata import normalize
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import defines
from logbase import task_client
from urllib import unquote
from werkzeug.utils import secure_filename
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
pending_file = Blueprint('pending_file',__name__)

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
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@pending_file.route('/pending_data',methods=['GET', 'POST'])
def pending_data():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	use_BH = request.form.get("a99")
	if use_BH=='0':
		f = request.files['file_change1']
		file_v=secure_filename(f.filename)
	else:
		file_v = request.form.get("file_v")
		file_change = request.form.get("file_change")
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	fname = file_v
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	if use_BH=='0':
		f.save(os.path.join(UPLOAD_FOLDER, fname))
	else:
		shutil.move(file_change,file_pwd)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#新建测试任务
			pwd_array = file_pwd.split('/')
			if len(fname.split('.')[-1]) == 4:
				taskname = fname[:-5]
			else:
				taskname = fname[:-4]
			data_json = '{"HostLeadInTaskId":0,"HostLeadInTaskName":"'+taskname+'","Type":1,"Status":0}'
			sql = 'select public."PSaveHostLeadInTaskDetail"(E\'%s\')' % MySQLdb.escape_string(data_json).decode("utf-8")
			curs.execute(sql)
			result = curs.fetchall()[0][0].encode('utf-8')
			r_j = json.loads(result)				
			HostLeadInTaskId = r_j['HostLeadInTaskId']
			#conn.commit()
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	task_content = '[global]\nclass = taskpending_host\ntype = execute_cmd_pending\nfile_pwd=\"%s\"\ntaskid=\"%s\"\n' % (file_pwd,str(HostLeadInTaskId))
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		if not system_log(system_user,'审核主机任务','失败','访问授权>主机管理'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		debug("hhhhhhh")
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
	debug("resultcccccccccc")
	if not system_log(system_user,'审核主机任务','成功','访问授权>主机管理'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return "{\"Result\":true,\"HostLeadInTaskId\":\"%s\"}" % str(HostLeadInTaskId)
'''
if __name__=='__main__':
	pending_data_all()
'''
