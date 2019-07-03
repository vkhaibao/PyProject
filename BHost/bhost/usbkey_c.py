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
usbkey_c = Blueprint('usbkey_c',__name__)

ERRNUM_MODULE_mac = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugdyw.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

@usbkey_c.route('/usbkey',methods=['GET', 'POST'])
def usbkey():
	debug('start')
	debug(str(time.strftime('%Y-%m-%d %H-%M-%S',time.localtime(time.time()))))
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.args.get('msg')
	debug(str(id))	
	debug('end')
	return str(id)
