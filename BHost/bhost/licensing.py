#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
import pyodbc
import MySQLdb
import json
import time
import base64
import csv
from comm import CertGet

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
from htmlencode import parse_sess
from htmlencode import check_role

from flask import Flask,Blueprint,request,session,render_template  
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
licensing = Blueprint('licensing',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 1000
ERRNUM_MODULE_host = 2000
ERRNUM_MODULE_BATCH = 1000
ERRNUM_MODULE_top = 36000
UPLOAD_FOLDER = '/usr/storage/.system/upload/'
pro_data = []
ad_data = []
con_data = []
dev_data = []
host_data = []
hg_data = []
def debug(c):
    return 0;
    path = "/var/tmp/debugrx_ccp.txt"
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
#跳转至授权许可
@licensing.route('/licensing_show',methods=['GET','POST'])
def licensing_show():
    sess=request.form.get('se')
    if sess<0:
        sess=""
    return render_template('licensing_change.html',se=sess)


@licensing.route('/upload_file_crt',methods=['GET', 'POST'])
def upload_file_crt():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	md5_str = request.form.get("m1")
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

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(se);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" %(sys._getframe().f_lineno)

	fname = secure_filename(f.filename);
	time_old=0
	debug(str(os.path.isfile("/usr/etc/server.crt")))
	if os.path.isfile("/usr/etc/server.crt"):
		time_old=os.path.getmtime('/usr/etc/server.crt')
	try:
		f.save(os.path.join(UPLOAD_FOLDER, fname))
		fname_path = os.path.join(UPLOAD_FOLDER,fname)
		debug(fname_path)
		task_content = '[global]\nclass = taskcrt\ntype = movecrt\npath=%s\n' % (fname_path)
		server_id=common.get_server_id();
		
		if False == task_client.task_send(server_id, task_content):
			return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
			
		debug('--- while True:---')
		time_new=0
		while True:
			debug(str('os.path.isfile("/usr/etc/server.crt")')+str(os.path.isfile("/usr/etc/server.crt")))
			if os.path.isfile("/usr/etc/server.crt"):
				time_new=os.path.getmtime('/usr/etc/server.crt')
				#os.remove(fname_path)
				debug(str(time_new))
				if time_new>time_old:
					break
			time.sleep(0.5)
			#r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=3);
			#debug(str(r))
        	#serial = r.hget('0','oldestsn')
        	#debug(str(serial))
		try:
			crt_t = CertGet(server_id)
		except Exception,e:
			debug(str(e))
			crt_t=None
		debug('----------------------1---------------------------')
		debug(str(crt_t))
		end=1
		if crt_t==None or crt_t[0] == None:
			end=0
			task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/etc/server.crt\n'
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

			return "{\"Result\":false,\"ErrMsg\":\"证书内容无效\"}"
		else:
			end=1;
			end_time =int(crt_t[5])
			now_time=int(time.time())
			if end_time<now_time:
				if int(crt_t[6]) != 1: ## 供货
					#auth_alert ='证书已到期，请重新导入证书'
					pass;
				else:
					return "{\"Result\":false,\"ErrMsg\":\"证书已到期，请重新导入证书\"}"	
			
			
		return "{\"Result\":true,\"info\":\"\"}" 
	except IOError,e:
		return "{\"Result\":false,\"ErrMsg\":\"%s\"}" %(str(e))
       
