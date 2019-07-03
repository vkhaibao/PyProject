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
from logbase import common
from logbase import defines
from logbase import task_client
from urllib import unquote
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
get_host_msg = Blueprint('get_host_msg',__name__)


UPLOAD_FOLDER = '/var/tmp/zdp'

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@get_host_msg.route('/get_over_msg',methods=['GET', 'POST'])
def get_over_msg():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_BATCH+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_BATCH+2,error)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_BATCH+2,error)
	#fname = system_user + '.txt'
	fname =	se + '.txt'
	file_name = os.path.join(UPLOAD_FOLDER,fname)
	if not os.path.exists(file_name):
		return "1"
	try:
		with open(file_name,'r') as fp:
			f_text = fp.read()
			fp.close()
			if f_text == "":
				os.remove(file_name)
			r_v = json.loads(f_text)
			if r_v['Result']:
				if r_v['info'] == 2:
					if os.path.exists(file_name):
						os.remove(file_name)
			else:
				if os.path.exists(file_name):
					os.remove(file_name)
			return f_text
	except IOError as err:  
		return "{\"Result\":false,\"ErrMsg\":\"文件打开失败\"}"
