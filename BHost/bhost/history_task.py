#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import time
import json
import MySQLdb

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from index import PGetPermissions

from flask import request,Blueprint,render_template # 

history_task = Blueprint('history_task',__name__)
ERRNUM_MODULE_history_task = 11000
reload(sys)
sys.setdefaultencoding('utf-8')

###检索任务列表
@history_task.route("/history_task_index", methods=['GET', 'POST'])
def history_task_index():
	session = request.args.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_history_task+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_history_task+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_history_task+3,error)
	task_page = request.args.get('tp1')
	if task_page <0 or task_page == "":
		task_page = 1
		
	_power=PGetPermissions(userCode)
	_power_json = json.loads(str(_power));
	_power_mode = 1;
	_power8=1;
	_power9=1;
	_power11=1;
	for one in _power_json:
		if one['SubMenuId'] == 8:
			_power8 = one['Mode']
		if one['SubMenuId'] == 9:
			_power9 = one['Mode']
		if one['SubMenuId'] == 11:
			_power11 = one['Mode']
	if _power8 == 2 or _power9 == 2 or _power11 ==2:
		_power_mode = 2;
	_power_mode =2;###备注 历史任务不做处理		
	return render_template('history_task.html',se=session,us=userCode,task_page=task_page,_power_mode=_power_mode)
