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
proto_control = Blueprint('proto_control',__name__)

@proto_control.route('/protolist_add',methods=['GET', 'POST'])
def protolist_add():
	return render_template('protolist_add.html')
	
		

	
	
	
