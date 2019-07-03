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
import struct
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from comm import *
from logbase import common
from urllib import unquote

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from logbase import defines
from logbase import task_client
from ctypes import *
import base64
import csv
import codecs
from werkzeug.utils import secure_filename

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
bhacc = Blueprint('bhacc',__name__)

SIZE_PAGE = 20
def debug(c):
	return 0
        path = "/var/tmp/debugbhacc.txt"
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
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	

@bhacc.route('/bhacc',methods=['GET', 'POST'])
def bhacc_cgi():
	msg_return=''
	debug('bhacc')
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	msg='Cache-Control: no-cache, must-revalidate\nContent-type:text/html; charset=gb2312\n\n'
	#REQUEST_METHOD = request.form.get('REQUEST_METHOD')
	#QUERY_STRING = request.form.get('QUERY_STRING')
	time_value=request.form.get('time')
	if time_value==None:
		time_value=request.args.get('time')
	if time_value!=None:
		time_value=time_value.replace('_',' ')
	debug('time_value:%s'%time_value)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			if time_value==None or time_value=='0':
				sql='SELECT COUNT(DISTINCT u."UserCode") FROM public."User" u\n\
				JOIN public."UserRole" ur ON ur."UserId"=u."UserId"\n\
   	 			JOIN public."RolePermissions" rp ON rp."RoleId"=ur."RoleId" and rp."SubMenuId"=25;'
			else:
				sql='SELECT COUNT(DISTINCT u."UserCode") FROM public."User" u \n\
				JOIN public."UserRole" ur ON ur."UserId"=u."UserId"\n\
                                JOIN public."RolePermissions" rp ON rp."RoleId"=ur."RoleId" and rp."SubMenuId"=25\n\
				WHERE u."LastPwdModifyTime">\'%s\' or u."CreateTime">\'%s\';'%(time_value,time_value)
			debug(str(sql))
			curs.execute(sql)
			result_count = curs.fetchall()[0][0]
			debug(str(result_count))
			if result_count==0:
				debug('result_count=0')
				msg_return+=SendStr('')
                                #SendStr('')
				debug(msg_return)
                                return msg_return
			else:
				#print msg
				#sys.stdout.write(msg)
				msg=''
				if time_value==None or time_value=='0':
                                	sql='SELECT DISTINCT u."UserCode",u."Password",u."LastPwdModifyTime" FROM public."User" u\n\
                                        JOIN public."UserRole" ur ON ur."UserId"=u."UserId"\n\
                                        JOIN public."RolePermissions" rp ON rp."RoleId"=ur."RoleId" and rp."SubMenuId"=25\n\
					ORDER BY u."LastPwdModifyTime" ASC;'
                        	else:
                                	sql='SELECT DISTINCT u."UserCode",u."Password",u."LastPwdModifyTime" FROM public."User" u \n\
                                        JOIN public."UserRole" ur ON ur."UserId"=u."UserId"\n\
                                        JOIN public."RolePermissions" rp ON rp."RoleId"=ur."RoleId" and rp."SubMenuId"=25\n\
                                        WHERE u."LastPwdModifyTime">\'%s\' or u."CreateTime">\'%s\'\n\
					ORDER BY u."LastPwdModifyTime" ASC;'%(time_value,time_value)
				debug(str(sql))
                        	curs.execute(sql)
                        	result_userall = curs.fetchall()
				debug(str(result_userall))
				#if os.path.exists('/usr/lib64/logproxy.so') == False:
				#	debug(str("os.path.exists('/usr/lib64/logproxy.so') == False"))
				#	return ''
				#	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				#lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
                		#pwd_rc4 = c_char_p()# 定义一个指针
                		#pwd_rc4.value = "0"*512 # 初始化 指针
				#lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]#定义函数参数
                		#lib.decrypt_pwd.restype = None #定义函数返回值
				for user_item in result_userall:
					usercode=user_item[0]
					password=user_item[1]
					#pwd_rc4 = c_char_p()# 定义一个指针
                                	#pwd_rc4.value = "0"*512 # 初始化 指针
					#ret = lib.decrypt_pwd(password,pwd_rc4)#执行函数
                			#password = pwd_rc4.value #获取变量的值
					debug('usercode:%s\t\tpassword:%s'%(usercode,password))
					usercode=base64.b64encode(usercode)
					password=base64.b64encode(password)
					debug('usercode:%s\t\tpassword:%s'%(usercode,password))
					msg+=('%s\t%s\n'%(usercode,password))
				now_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
				msg+=('Time\t%s\n')%(now_time)
				debug('---------------------->>>')
				debug(str(msg))
				debug(str(len(msg)))
				msg_return+=SendStr(msg)
				debug(str(msg_return))
				return_str=msg_return
				msg_return=''
				debug('=================1====================')
				return return_str
	except pyodbc.Error,e:
		debug(str(e))
		return ''
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)


def SendStr(msg):
	msg_return=''
	len_msg=len(msg)
	msg_return+=(struct.pack('i',len_msg))
	if len_msg>0:
		msg_return+=(msg)
	return msg_return
