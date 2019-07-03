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

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

def debug(c):
	return 0
        path = "/var/tmp/debuggenerating_log.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
#日志属性				int08_00	系统
#日志类型				int32_01	none
#发生时间				xtime_02	happen
#发生地址				ip_00		client_ip
#运维用户				str32_22	user
#结果信息				str32_02	mesg
#日志操作				str32_01	oper
#模块					str32_04	module	
#是否告警				int08_12	none
#告警信息				str32_30	none
def system_log(user,oper,mesg,module,_type=1):
	happen=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	client_ip=request.remote_addr    #获取客户端IP
	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn,conn.cursor() as curs:
			debug("11111111111111111111222222222")
			debug("happen:%s" % happen)
			debug("mesg:%s" % mesg)
			debug("oper:%s" % oper)
			debug("module:%s" % module)
			sql="INSERT INTO \"public\".adm_table(\"int32_01\",\"int08_00\",\"xtime_02\",\"ip_00\",\"str32_22\",\"str32_02\",\"str32_01\",\"str32_04\",\"int08_12\") VALUES(%s,3,E'%s',E'%s',E'%s',E'%s',E'%s',E'%s',0);"%(_type,happen,client_ip,user,MySQLdb.escape_string(mesg).decode("utf-8"),MySQLdb.escape_string(oper).decode("utf-8"),MySQLdb.escape_string(module).decode("utf-8"))
			debug(str(sql))
			curs.execute(sql)
			conn.commit()
			return True
	except pyodbc.Error,e:
		#return str(e)
		return False
	return False
