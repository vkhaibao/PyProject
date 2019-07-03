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
account = Blueprint('account',__name__)

ERRNUM_MODULE_account = 1000

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

def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
	
@account.route('/account_list',methods=['GET', 'POST'])
def account_list():			
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get('a0')
	page = request.form.get('z2')
	ipage = request.form.get('z3') 
	keyword = request.form.get('z4')
	filter_flag = request.form.get('z5')
	selectid = request.form.get('z6')
	
	
	
	if se == "" or se < 0:
		se = request.args.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
		
	hash  = request.args.get('ha');
	if hash < 0 or hash =='':
		hash  = request.form.get('ha');
		if hash < 0 or hash =='':
			pass
		else:
			myCookie = request.cookies #获取所有cookie
			if myCookie.has_key('bhost'):
				hashsrc = StrMD5(myCookie['bhost']);
				if(hashsrc != hash):
					exit();
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();

	
	if keyword == None:
		keyword = "[]"
	if filter_flag == None:
		filter_flag = 0
	if selectid == None:
		selectid = "[]"
	if(str(filter_flag).isdigit() == False):
		return '',403	
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 			
	if page and  (str(page).isdigit() == False):
		return '',403
	if ipage and  (str(ipage).isdigit() == False):
		return '',403
	
	
	_power=PGetPermissions(usercode)
	_power=str(_power)
	_power_json = json.loads(_power)
	_power_mode = 1;
	
	
				
	myCookie = request.cookies #获取所有cookie
	hash = '';
	if myCookie.has_key('bhost'):
		hash = StrMD5(myCookie['bhost'])
			
	for one in _power_json:
		if one['SubMenuId'] == 14 :
			_power_mode = one['Mode']
	return render_template('account_list.html',page=page,ipage=ipage,keyword=keyword,filter_flag=filter_flag,selectid=selectid,_power_mode = _power_mode,hash=hash)
	
@account.route('/create_account',methods=['GET', 'POST'])
def create_account():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z2')
	type = request.form.get('z1')
	page = request.form.get('z3')
	ipage = request.form.get('z4')
	keyword = request.form.get('z5')
	filter_flag = request.form.get('z6')
	selectid = request.form.get('z7')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	
	
	if keyword == None:
		keyword = "[]"
	if filter_flag == None:
		filter_flag = 0
	if selectid == None:
		selectid = "[]"
	if(str(filter_flag).isdigit() == False):
		return '',403	
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 			
	if page and  (str(page).isdigit() == False):
		return '',403
	if ipage and  (str(ipage).isdigit() == False):
		return '',403
	if type and  (str(type).isdigit() == False):
		return '',403
	_power=PGetPermissions(userCode)
	_power=str(_power)
	_power_json = json.loads(_power)
	manage_power_id = [];
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	if (type == '1'):
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				curs.execute("select public.\"PGetAccount\"(%d,null,null,1,0);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				results = json.loads(results)
				Name = results["data"][0]["Name"]
				AccountType = results["data"][0]["AccountType"]
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_account + 3, ErrorEncode(e.args[1]))
		return render_template('create_account.html',AccountName=Name,AccountType=AccountType,tasktype=type,accountid=id,page=page,ipage=ipage,keyword=keyword,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id)
	else:
		return render_template('create_account.html',AccountName="",AccountType="",tasktype=type,accountid=id,page=page,ipage=ipage,keyword=keyword,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id)

@account.route('/get_host_v',methods=['GET', 'POST'])
def get_host_v():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	hid = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)	
	return '{"HostIP": "192.166.5.196","HostId": 1768,"Status": 0,"HostName": "testhost1475","HGroupSet": [{"HGId": 1731,"HGName": "TDY1","HGroupNamePath": "//TDY1"}],"AccessRate": 1,"AccountSet": [{"Password": "8405f597c447bba19f7abc6e","HostAccount": {"AccountId": 3,"AccountName": "administrator","IsSuperAcct": false,"AcctSwitchCmd": null,"FromAccountId": null,"FromAccountName": null,"SwitchPasswdPrompt": null},"PasswordType": 1,"HostServiceSet": [{"Port": 22,"ProtocolId": 2,"ConnParamId": null,"ServiceName": null,"ProtocolName": "SSH","ConnParamName": null,"HostServiceId": 1796,"HostServiceName": "test"}],"PasswordAuthId": 980927},{"Password": "8405f597c447bba19f7abc6e","HostAccount": {"AccountId": 2,"AccountName": "system-view","IsSuperAcct": false,"AcctSwitchCmd": null,"FromAccountId": null,"FromAccountName": null,"SwitchPasswdPrompt": null},"PasswordType": 1,"HostServiceSet": [{"Port": 22,"ProtocolId": 2,"ConnParamId": null,"ServiceName": null,"ProtocolName": "SSH","ConnParamName": null,"HostServiceId": 1796,"HostServiceName": "test"}],"PasswordAuthId": 980926},{"Password": "8405f597c447bba19f7abc6e","HostAccount": {"AccountId": 1,"AccountName": "enable","IsSuperAcct": false,"AcctSwitchCmd": null,"FromAccountId": null,"FromAccountName": null,"SwitchPasswdPrompt": null},"PasswordType": 1,"HostServiceSet": [{"Port": 22,"ProtocolId": 2,"ConnParamId": null,"ServiceName": null,"ProtocolName": "SSH","ConnParamName": null,"HostServiceId": 1796,"HostServiceName": "test"}],"PasswordAuthId": 980928}],"ServiceSet": [{"Port": 22,"AccIPSet": null,"LineBreak": 3,"ExtraReply": null,"FromHostId": null,"ProtocolId": 2,"ConnParamId": null,"ExtraPrompt": null,"SuperPrompt": null,"FromHostName": null,"FromLoginCmd": null,"NormalPrompt": null,"ProtocolName": "SSH","AcctSwitchCmd": null,"ConnParamName": null,"FromAccountId": null,"HostServiceId": 1796,"FromAccountName": null,"HostServiceName": "test","LoginSuccPrompt": null,"LoginUserPrompt": null,"FromHostServiceId": null,"LoginPasswdPrompt": null,"SwitchPasswdPrompt": null,"FromHostServiceName": null}],"Description": null,"DeviceTypeId": 1,"DeviceTypeName": "Windows","EnableLoginLimit": false}'
