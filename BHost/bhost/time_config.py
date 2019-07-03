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

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from logbase import common
from logbase import defines
from logbase import task_client
from htmlencode import parse_sess,check_role

env = Environment(loader = FileSystemLoader('templates'))

from generating_log import system_log

app = Flask(__name__)
time_config = Blueprint('time_config',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 1000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
        path = "/var/tmp/debugrx_ccp.txt"
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
        return newStr
#跳转至时间设置
@time_config.route('/time_config_show',methods=['GET','POST'])
def time_config_show():
        sess=request.form.get('se')
        if sess<0:
            sess=""
        return render_template('time_config.html',se=sess)
#获取时间设置
@time_config.route('/get_time_config',methods=['GET','POST'])
def get_time_config():
	###session 检查
        reload(sys)
        sys.setdefaultencoding('utf-8')
        sess = request.form.get('se')
        if sess < 0:
            sess = ""
        client_ip = request.remote_addr
        (error,system_user,mac) = SessionCheck(sess,client_ip)
        if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
            	sys.exit()
        try:
            with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
                # PGetTimeConfig()
                sql = "select public.\"PGetTimeConfig\"();"
                curs.execute(sql)
                results = curs.fetchall()[0][0]
            #获取系统时间
                sysTimeStr = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime( time.time()) )
                return "{\"Result\":true,\"info\":%s,\"time\":\"%s\"}" % (results,sysTimeStr)	
        except pyodbc.Error,e:
            return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#获取时间设置
@time_config.route('/update_server_time',methods=['GET','POST'])
def update_server_time():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	time_str=request.form.get('a1')
	md5_str=request.form.get('m1')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(time_str);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	##[global]
	#class=taskupdate
	#type=update_run
	#time_str=time_str
	task_content = '[global]\nclass = taskupdate\ntype = update_run\ntime_str=%s\n' % (time_str)
	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
		if not system_log(system_user,'修改系统时间','系统异常(%d)'%(sys._getframe().f_lineno),'系统管理>系统时间'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	if not system_log(system_user,'修改系统时间','成功','系统管理>系统时间'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return '{"Result":true,"info":"修改成功"}'

# 同步时间
@time_config.route('/update_ntp_time',methods=['GET','POST'])
def update_ntp_time():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('se')
	ip_str=request.form.get('a1')
	oper = request.form.get('o1')
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
	
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	##[global]
	#class=taskntp
	#type=operation
	#ip_str=ip_str
	task_content = '[global]\nclass = taskntp\ntype = operation\nip_str=%s\n'%(ip_str)
	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
		if not system_log(system_user,oper,'系统异常(%d)'%sys._getframe().f_lineno,'系统管理>系统时间'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			
	if not system_log(system_user,oper,'成功','系统管理>系统时间'):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return '{"Result":true,"info":"同步成功"}'
#创建  编辑
@time_config.route('/add_timeconfig',methods=['GET','POST'])
def add_timeconfig():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	oper = request.form.get('o1')
	md5_str = request.form.get('m1')
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
	time = request.form.get('a1')
	time=str(time)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(time);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PSaveTimeConfig\"(E'%s')" %(MySQLdb.escape_string(time).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			
			if json.loads(result)['Result'] == False:
				msg = json.loads(result)['ErrMsg']
			else:	
				conn.commit()
				msg = '成功'
			if not system_log(system_user,oper,msg,'系统管理>系统时间'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"			
			return result  
	except pyodbc.Error,e:
		msg = '系统繁忙(%d)' %(sys._getframe().f_lineno)
		if not system_log(system_user,oper,msg,'系统管理>系统时间'):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"		
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

        
