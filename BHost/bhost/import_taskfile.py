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
import_taskfile = Blueprint('import_taskfile',__name__)

ERRNUM_MODULE_BATCH = 1000
ERRNUM_MODULE_host = 2000
#UPLOAD_FOLDER = '/var/tmp/zdp'
#UPLOAD_FOLDER = '/flash/system/storage/LOG/Webmanager/host'
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

@import_taskfile.route('/import_task',methods=['GET', 'POST'])
def import_task():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	cover = request.form.get('z1')
	name = request.form.get('z2')
	succ = request.form.get('z3')
	hostleadintaskid = request.form.get('z4')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_BATCH+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_BATCH+2,error)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_BATCH+2,error)

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(name);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	if check_role(system_user,'主机管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	file_pwd = UPLOAD_FOLDER + '/' + name + '.csv'
	task_content = '[global]\nclass = taskimport_hosttask\ntype = execute_cmd_hosttask\nfile_pwd=\"%s\"\ncover=\"%s\"\nsucc=\"%s\"\nusercode=\"%s\"\nhostleadintaskid=\"%s\"\n' % (file_pwd,cover,succ,system_user,str(hostleadintaskid))
	debug("import_task  task_content  ::"+str(task_content))
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		
		return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.err_msg))
	return "{\"Result\":true}"
