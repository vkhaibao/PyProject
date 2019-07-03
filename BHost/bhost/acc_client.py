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
import base64

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
acc_client = Blueprint('acc_client',__name__)

ERRNUM_MODULE_acc_client = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

@acc_client.route('/acc_client_list',methods=['GET', 'POST'])
def acc_client_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	ipage = request.form.get('z2')	
	keyword = request.form.get('z3')
	filter_flag = request.form.get('z4')
	if keyword == None or keyword=='':
		keyword = "[]"
	if filter_flag == None or filter_flag=='':
		filter_flag = 0
		
	if(str(filter_flag).isdigit() == False):
		return '',403
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
		
	
			
	if ipage ==None or ipage=='':
		ipage='1';
	return render_template('acc_client_list.html',ipage=ipage,keyword=keyword,filter_flag=filter_flag)
	
@acc_client.route('/create_acc_client',methods=['GET', 'POST'])
def create_acc_client():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('t1')
	ipage = request.form.get('z1')
	clientid = request.form.get('z4')
	keyword = request.form.get('z5')
	filter_flag = request.form.get('z6')
	if filter_flag == None or filter_flag=='':
		filter_flag = 0
	
	if(type !=None and str(type).isdigit() == False):
		return '',403	
		
	if(str(filter_flag).isdigit() == False):
		return '',403
		
	if(str(ipage).isdigit() == False):
		return '',403
		
	if(str(clientid).isdigit() == False):
		return '',403
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
		
	return render_template('create_acc_client.html',tasktype=type,ipage=ipage,clientid=clientid,keyword=keyword,filter_flag=filter_flag)
