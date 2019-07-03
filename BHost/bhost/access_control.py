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
from index import PGetPermissions
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
access_control = Blueprint('access_control',__name__)

@access_control.route('/access_user_index',methods=['GET', 'POST'])
def access_user_index():
        tasktype = request.form.get('tasktype') # 1->创建 2->编辑 3 列表 
        user = request.form.get('user') # 1->创建 2->编辑 3 列表 
        se = request.form.get('se')
	if se < 0:
		se = request.args.get('se')
		if se < 0 :
			se = "";
	
	if tasktype < 0:
                tasktype = "1"
        if user < 0:
		user = request.args.get('user')
		if user < 0:
			user = ''
	
	
	if tasktype == '1':
		t =  "user_add.html"
        elif tasktype == '2':
                t = "user_edit.html"
        elif tasktype == '4':
                t = "host_add.html"
        elif tasktype == '5':
                t = "hostdevicetype_add.html"
        elif tasktype == '6':
                t = "hostaccessprotocol_add.html"
        elif tasktype == '7':
                t = "role_add.html"
	elif tasktype == '8':
                t = "hostaccount_add.html"

        else:
                t = "user_list.html"

        return render_template(t,tasktype=tasktype,us=user,se=se)
		
@access_control.route('/access_switch',methods=['GET', 'POST'])
def access_switch():	
	tasktype = request.form.get('tasktype') # 1->创建 2->编辑 3 列表 
	if tasktype < 0:
		tasktype = "0"
	if tasktype == '0':
		t = "resources.html"
	else:
		t = "access_control.html"
		
	return render_template(t,tasktype=tasktype)

@access_control.route('/role_manage',methods=['GET','POST'])
def role_manage():
        sess = request.form.get('se')
        if sess<0:
                sess=""
        return render_template('role_manage.html',se=sess)
@access_control.route('/user_manage',methods=['GET','POST'])
def user_manage():
	sess = request.form.get('se')
	us = request.form.get('user')
	if sess<0:
		sess=""		
	client_ip = request.remote_addr
	(error,us,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	_power=PGetPermissions(us)
        _power=str(_power)
        _power_json = json.loads(_power);
	_power_sonid = [];
        _power_mode_id = [];
        for one in _power_json:
                _power_sonid.append(one['SubMenuId']);
                if one['Mode'] == 2:
                        _power_mode_id.append(one['SubMenuId'])
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	#
	try:
		sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (us);
		#debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	if (results & 16)>0:
		first_grp = 0
	else:
		first_grp = 1
	return render_template('user_manage.html',se=sess,us=us,first_grp=first_grp,_power_mode_id=_power_mode_id,_power_sonid=_power_sonid)

