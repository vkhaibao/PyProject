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
mac = Blueprint('mac',__name__)

ERRNUM_MODULE_mac = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

@mac.route('/mac_list',methods=['GET', 'POST'])
def mac_list():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	page = request.form.get('z2')
	ipage = request.form.get('z3')		
	return render_template('mac_list.html',page=page,ipage=ipage)
	
@mac.route('/create_macset',methods=['GET', 'POST'])
def create_mac():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z2')
	type = request.form.get('z1')
	page = request.form.get('z3')
	ipage = request.form.get('z4')		
	debug(id)
	debug(type)
	return render_template('create_macset.html',tasktype=type,macsetid=id,page=page,ipage=ipage)
"""	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor();
			if(type == '1'):
				curs.execute("select public.\"PGetMACSet\"(%d,null,null,false,1,0);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				results = json.loads(results)
				#MACSetName = results["data"][0]["Name"]
				#Description = results["data"][0]["Description"]
				Set = results["data"][0]["Set"]
				Set_length = len(Set)
				MACAddress = ""
				for i in Set:
					MACAddress = MACAddress + i["MACAddress"]+";"
				MACAddress = MACAddress[:-1]
				return render_template('create_macset.html',MACAddress=MACAddress,tasktype=type,macsetid=id)
			else:
				return render_template('create_macset.html',MACAddress="1",tasktype=type,macsetid=id)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_mac + 3, ErrorEncode(e.args[1]))
"""
