#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
import MySQLdb
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
account_add = Blueprint('account_add',__name__)

ERRNUM_MODULE_account = 1000

def debug(c):
	return 0
	path = "/var/tmp/debuglxz.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	

@account_add.route('/get_account_list',methods=['GET', 'POST'])
def get_account_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	page = request.form.get('z5')
	ipage = request.form.get('z6')
	keyword = request.form.get('z7')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
	if dsc!='false' and dsc!='true':
		return '',403
	
	keyword = json.loads(keyword)
	if page < 0:
		page = 0
	if ipage < 0:
		ipage = 0
	if ipage != "null":
		row = int(page)*(int(ipage)-1)
	else:
		row = "null"
	filter_v = ""
	filter_AD = ""
	filter_all = ""
	if len(keyword) != 0:
		for i in keyword:
			filter_arry = i.split('-',1)
			if filter_arry[0] == "账号":
				filter_v = filter_v + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "域名":
				filter_AD = filter_AD + MySQLdb.escape_string(filter_arry[1]) + '\n'
			if filter_arry[0] == "所有":
				filter_all = filter_all + MySQLdb.escape_string(filter_arry[1]) + '\n'
	if filter_v == "":
		filter_v = 'null'
	else:
		filter_v = filter_v[:-1]
		filter_v = MySQLdb.escape_string(filter_v).decode('utf-8')
		filter_v=filter_v.replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
		filter_v = "E'%s'" % filter_v
	if filter_AD == "":
			filter_AD = 'null'
        else:
			filter_AD = filter_AD[:-1]
			filter_AD = MySQLdb.escape_string(filter_AD).decode('utf-8')
			filter_AD = filter_AD.replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
			filter_AD = "E'%s'" % filter_AD
	if filter_all == "":
			filter_all = 'null'
        else:
			filter_all = filter_all[:-1]
			filter_all = MySQLdb.escape_string(filter_all).decode('utf-8')
			filter_all = filter_all.replace("\\","\\\\").replace(".","\\\\.").replace("?","\\\\?").replace("+","\\\\+").replace("(","\\\\(").replace("*","\\\\*").replace("[","\\\\[")
			filter_all = "E'{\"searchstring\":\"%s\"}'" % filter_all
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			debug("select public.\"PGetAccount\"(null,%s,%s,%s,%s,%s);"%(filter_v,filter_AD,page,str(row),filter_all))
			curs.execute("select public.\"PGetAccount\"(null,%s,%s,%s,%s,%s,%s);"%(filter_v,filter_AD,page,str(row),filter_all,dsc))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@account_add.route('/save_account', methods=['GET','POST'])
def save_account():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_arry = request.form.get('d5')
	md5_str = request.form.get('m1')
	
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(id_arry);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			id_arry = json.loads(id_arry)
			account_str = ""
			for i in id_arry:
				account_json = json.loads(i)
				if account_json['DomainId'] != None:
					sql = "select \"DomainName\" from public.\"Domain\" where \"DomainId\"=%d" % account_json['DomainId']
					curs.execute(sql)
					domain = curs.fetchall()[0][0]
					account_name = domain + '\\' + account_json['Name']
				else:
					domain = ""
					account_name = account_json['Name']
				if account_json['AccountId'] != 0:
					edit_flag = 1#编辑
				else:
					edit_flag = 0
				debug(str(i))
				debug("select public.\"PSaveAccount\"(E'%s');" %(i))
				curs.execute("select public.\"PSaveAccount\"(E'%s');"%(i))
				results = curs.fetchall()[0][0].encode('utf-8')
				ret = json.loads(results)
				
				if ret['Result'] == False:
					if account_json['AccountId'] == 0:
						
						system_log(userCode,"创建账号：%s" % account_name,"失败","运维管理>账号")
					else:
						system_log(userCode,"编辑账号：%s" % account_name,"失败","运维管理>账号")
					conn.rollback();
					ret['ErrMsg'] = ret['ErrMsg'] + '(%d)' % sys._getframe().f_lineno
					return json.dumps(ret)
				account_str = account_str + account_name + ','
					#return results
			account_str = account_str[:-1]
			if edit_flag == 0:
				system_log(userCode,"创建账号：%s" % account_str,"成功","运维管理>账号")
			else:
				system_log(userCode,"编辑账号：%s" % account_str,"成功","运维管理>账号")
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@account_add.route('/delete_account', methods=['GET','POST'])				
def delete_account():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	type = request.form.get('z9')
	id = request.form.get('z10')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			if (type == '1'):
				sql = "select \"AccountName\" from public.\"Account\" where \"AccountId\" in (%s)" % id[1:-1]
				curs.execute(sql)
				account_str = ""
				for row in curs.fetchall():
					account_str = account_str + row[0].encode('utf-8') + ","
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"AccountName\" from public.\"Account\" where \"AccountId\"=%d" % int(id)
					curs.execute(sql)
					account_name = curs.fetchall()[0][0].encode('utf-8')
					sql='select public."PIsAlreadyUsed"(%d,1);'%(int(id))
					curs.execute(sql)
					used = curs.fetchall()[0][0].encode('utf-8')
					if used=='1':
						system_log(userCode,"删除账号：%s" % account_name,"失败：该账号已被使用","运维管理>账号")
						conn.rollback();
						return '{"Result":false,"ErrMsg":"该账号已被使用"}'
					curs.execute("select public.\"PDeleteAccount\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除账号：%s" % account_name,"失败："+result['ErrMsg'],"运维管理>账号")
						conn.rollback();
						return result
				
				if account_str != "":
					system_log(userCode,"删除账号：%s" % account_str[:-1],"成功","运维管理>账号")
				return "{\"Result\":true}"		
			else:
				sql = "select \"AccountName\" from public.\"Account\" where \"AccountId\"=%s" % id
				curs.execute(sql)
				account_name = curs.fetchall()[0][0].encode('utf-8')
				sql='select public."PIsAlreadyUsed"(%d,1);'%(int(id))
				curs.execute(sql)
				used = curs.fetchall()[0][0].encode('utf-8')
				if used=='1':
					system_log(userCode,"删除账号：%s" % account_name,"失败：该账号已被使用","运维管理>账号")
					return '{"Result":false,"ErrMsg":"该账号已被使用"}'
				curs.execute("select public.\"PDeleteAccount\"(%d);"%(int(id)))
				result = curs.fetchall()[0][0].encode('utf-8')
				system_log(userCode,"删除账号：%s" % account_name,"成功","运维管理>账号")
				return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@account_add.route('/select_account_all', methods=['GET','POST'])
def select_account_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('z11')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if id != "-1":
				curs.execute("select public.\"PGetAccount\"(%d,null,null,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetAccount\"(null,null,null,null,null);")
			result = curs.fetchall()[0][0].encode('utf-8')
			debug("no error !-------")
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
@account_add.route('/get_ADregion',methods=['GET','POST'])
def get_ADregion():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs=conn.cursor()
				sql="select public.\"PGetDomain\"(null,null,null,null,null);"
				curs.execute(sql)
				result=curs.fetchall()[0][0].encode('utf-8')
				return result
        except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

