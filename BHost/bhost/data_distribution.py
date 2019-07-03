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

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
data_distribution = Blueprint('data_distribution',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
        path = "/var/tmp/debugrxl.txt"
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
#获取数据分布data
@data_distribution.route('/get_data_distribution',methods=['GET','POST'])
def get_data_distribution():
    global ERRNUM_MODULE
    ERRNUM_MODULE = 30000
    reload(sys)
    sys.setdefaultencoding('utf-8')
    session = request.form.get('a0')
    return '{"Result":true,"data":[["08.15","08.16","08.17","08.18","08.19","08.20"],[200,130,124,352,256,89]]}'
    authtype = request.form.get('a1')
    authtype=str(authtype)
    if session < 0:
        session = ""
    try:
        conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+11,ErrorEncode(e.args[1]))
    try:
        curs = conn.cursor()
    except pyodbc.Error,e:
        conn.close()
        return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(ERRNUM_MODULE+12,ErrorEncode(e.args[1]))
    # PSaveAuthType(jsondata)
    sql="select public.\"PSaveAuthType\"(E'%s')" %(MySQLdb.escape_string(authtype).decode("utf-8"))
    try:
        curs.execute(sql)
    except pyodbc.Error,e:
        curs.close()
        conn.close()
        return "{\"Result\":false,\"ErrMsg\":\"添加异常(%d):%s\"}" %(ERRNUM_MODULE+79,ErrorEncode(e.args[1]))
    result = curs.fetchall()[0][0]
    conn.commit()
    curs.close()
    conn.close()
    return result  
    
