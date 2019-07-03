#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import time
import json
import re
import MySQLdb
import struct
import socket

import htmlencode
from generating_log import system_log

from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck

from flask import Flask,Blueprint,request,render_template #
from htmlencode import parse_sess,check_role 
b_host_manage = Blueprint('b_host_manage',__name__)
ERRNUM_MODULE_host = 3000

def debug(c):
	return 0
	path = "/var/tmp/debugyt.txt"
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
	
@b_host_manage.route('/host_manage',methods=['GET', 'POST'])
def host_manage():	
	tasktype = request.form.get('tasktype')
	debug('host_manage')
	debug(tasktype)
	if tasktype<0:
		tasktype=0
	if tasktype=='10':
		t="host_list_zdp.html"
	else:
		t = "host_list.html"
	session = request.form.get('se')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#
	try:
		sql = "select \"User\".\"MonitorBGColor\" from public.\"User\" where \"User\".\"UserCode\"='%s';" % (system_user);
		#debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	if (results & 4)>0:
		first_grp = 0
	else:
		first_grp = 1
	return render_template(t,result="{}",us=system_user,se=session,first_grp=first_grp)

@b_host_manage.route('/host_add',methods=['GET', 'POST'])
def host_add():	
	t = "host_add.html"
	session = request.form.get('se')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)	
	return render_template(t,us=system_user,se=session)	
	
##获取 当前目录层的数据
@b_host_manage.route('/getHostDir',methods=['GET', 'POST'])
def getHostDir():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	hgid = request.form.get('a1')
	if hgid < 0 or hgid=="":
		hgid = 0
	else:
		hgid = int(hgid)
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#
	'''
	sql = "select \"User\".\"UserId\" from public.\"User\" where \"User\".\"UserCode\"=E'%s';" %(userCode)
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	'''
	results=0
	debug(userCode)
	sql = "select public.\"PGetHostDirectory\"(E'%s',%d,10,%d,null,null)" %(userCode,hgid,results)
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
##获取服务或账号列表
@b_host_manage.route('/PGetAccountProtocolForAuth',methods=['GET','POST'])
def PGetAccountProtocolForAuth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	json_data = request.form.get('a1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	json_data_json=json.loads(json_data)
	json_data_json['LoginUserCode']=system_user
	json_data=json.dumps(json_data_json)
	json_data=str(json_data)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	sql ="select public.\"PGetAccountProtocolForAuth\"(E'%s');" %(json_data) 	
	#sql ="select public.\"PGetAccountProtocolForAuth\"(E'%s');" %(MySQLdb.escape_string(json_data).decode("utf-8")) 	
	try:
		debug(sql)
		debug('sql-----')
		curs.execute(sql)
		debug('---->>>>>')
	except Exception,e:
		debug(str(e))
	#except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	debug(str(results))	
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" % results
##获取共有服务或账号列表
@b_host_manage.route('/PGetSameAccountProtocolForAuth',methods=['GET','POST'])
def PGetSameAccountProtocolForAuth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	json_data = request.form.get('a1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	json_data_json=json.loads(json_data)
	json_data_json['LoginUserCode']=system_user
	json_data=json.dumps(json_data_json)
	json_data=str(json_data)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	sql ="select public.\"PGetSameAccountProtocolForAuth\"(E'%s');" %(MySQLdb.escape_string(json_data).decode("utf-8")) 	
	try:
		debug(sql)
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	debug("results")
	debug(str(results))
	if not results:
		results='[]'
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" % results
##批量保存服务
@b_host_manage.route('/PBatchSaveHostService',methods=['GET','POST'])
def PBatchSaveHostService():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	json_data = request.form.get('a1')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(json_data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	#json_data_json=json.loads(json_data)
	#json_data_json['LoginUserCode']=system_user
	#json_data=json.dumps(json_data_json)
	#json_data=str(json_data)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	#sql ="select public.\"PBatchSaveHostService\"('%s');" %(json_data) 	
	sql ="select public.\"PBatchSaveHostService\"(E'%s');" %(MySQLdb.escape_string(json_data).decode("utf-8")) 	
	try:
		debug(sql)
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	debug("results")
	debug(str(results))
	results_json=json.loads(results)
	json_data_json=json.loads(json_data)
	server_arr=[]
	if json_data_json['ServiceSet']!=None:
                        for i in json_data_json['ServiceSet']:
				debug(str(i))
				debug(str(i.get('ConnParamName')))
                                if i.get('ConnParamName')!=None:
                                        server_arr.append('%s-%s-%s'%(i['ProtocolName'],i['Port'],i['ConnParamName']))
                                else:
                                        server_arr.append('%s-%s'%(i['ProtocolName'],i['Port']))
	oper='批量添加服务：%s'%('、'.join(server_arr))
	debug(str(oper))
	if results_json['Result']:
		hg_arr=[]
		host_arr=[]
		#server_arr=[]
		#json_data_json=json.loads(json_data)
		if json_data_json['HGroupSet']!=None:
			for i in json_data_json['HGroupSet']:
				hg_arr.append(i['Name'])
		if json_data_json['HostSet']!=None:
                        for i in json_data_json['HostSet']:
                        	host_arr.append(i['Name'])
		'''
		if json_data_json['ServiceSet']!=None:
			for i in json_data_json['ServiceSet']:
				if i.get('ConnParamName')!=None:
					server_arr.append('%s-%s-%s')%(i['ProtocolName'],i['Port'],i['ConnParamName'])
				else:
					server_arr.append('%s-%s')%(i['ProtocolName'],i['Port'])
		'''
		oper_arr=[]
		debug(str(hg_arr))
		debug(str(host_arr))
		if len(hg_arr)>0:
			oper_arr.append('主机组：%s'%('、'.join(hg_arr)))
		if len(host_arr)>0:
			oper_arr.append('主机：%s'%('、'.join(host_arr)))
		'''
		if len(server_arr)>0:
			oper_arr.append('服务：%s'%('、'.join(server_arr)))
		'''
		oper+=('（%s）')%('，'.join(oper_arr))
		debug(str(oper))
		if results_json['FailCount']==0:
			if not system_log(system_user,oper,results_json['SuccLog'].replace("主机：","成功主机：").replace('; ','、'),'运维管理>主机管理'):
                        	curs.close()
        			conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		else:
			if results_json['SuccCount']==0:
				msg='%s'%(results_json['FailLog'].replace("主机：","失败主机：").replace('; ','、'))
			else:
				msg='%s，%s'%(results_json['SuccLog'].replace("主机：","成功主机：").replace('; ','、'),results_json['FailLog'].replace("主机：","失败主机：").replace('; ','、'))
			if not system_log(system_user,oper,msg,'运维管理>主机管理'):
                                curs.close()
                                conn.close()
                                return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		debug('--------->>>>>>>>>>>>>>>>>>>>>')
		curs.commit()
	else:
		if not system_log(system_user,oper,results_json['ErrMsg'],'运维管理>主机管理'):
			curs.close()
                        conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	curs.close()
	conn.close()
	debug('11')
	return results
##批量删除服务
@b_host_manage.route('/PBatchDeleteHostService',methods=['GET','POST'])
def PBatchDeleteHostService():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	json_data = request.form.get('a1')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return"{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(json_data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	json_data_json=json.loads(json_data)
	json_data_json['LoginUserCode']=system_user
        json_data=json.dumps(json_data_json)
	json_data=str(json_data)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	sql ="select public.\"PBatchDeleteHostService\"(E'%s');" %(MySQLdb.escape_string(json_data).decode("utf-8")) 	
	try:
		debug(sql)
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	debug("results")
	debug(str(results))
	results_json=json.loads(results)
	json_data_json=json.loads(json_data)
        server_arr=[]
        if json_data_json['ServiceSet']!=None:
                        for i in json_data_json['ServiceSet']:
                                debug(str(i))
                                debug(str(i.get('ConnParamName')))
                                if i.get('ConnParamName')!=None:
                                        server_arr.append('%s-%s-%s'%(i['ProtocolName'],i['Port'],i['ConnParamName']))
                                else:
                                        server_arr.append('%s-%s'%(i['ProtocolName'],i['Port']))
        oper='批量删除服务：%s'%('、'.join(server_arr))
	debug(str(oper))
	if results_json['Result']:
		hg_arr=[]
                host_arr=[]
                if json_data_json['HGroupSet']!=None:
                        for i in json_data_json['HGroupSet']:
                                hg_arr.append(i['Name'])
                if json_data_json['HostSet']!=None:
                        for i in json_data_json['HostSet']:
                                host_arr.append(i['Name'])
                oper_arr=[]
                debug(str(hg_arr))
                debug(str(host_arr))
                if len(hg_arr)>0:
                        oper_arr.append('主机组：%s'%('、'.join(hg_arr)))
                if len(host_arr)>0:
                        oper_arr.append('主机：%s'%('、'.join(host_arr)))
                oper+=('（%s）')%('，'.join(oper_arr))
                debug(str(oper))
                if results_json['FailCount']==0:
			if not system_log(system_user,oper,'成功','运维管理>主机管理'):
                        	curs.close()
                        	conn.close()
                        	return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		else:
			if not system_log(system_user,oper,'成功：%s，失败：%s'%(results_json['SuccCount'],results_json['FailCount']),'运维管理>主机管理'):
                                curs.close()
                                conn.close()
                                return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		curs.commit()
	else:
		if not system_log(system_user,oper,results_json['ErrMsg'],'运维管理>主机管理'):
                        curs.close()
                        conn.close()
                        return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	curs.close()
	conn.close()
	return results
##获取 主机 或者主机组的简要信息	
@b_host_manage.route('/getDetail',methods=['GET', 'POST'])
def getDetail():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	loginuc = request.form.get('a3')
	loginuc = "E'%s'" %(loginuc)
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	id = request.form.get('a1')
	flag = request.form.get('a2')
	
	if id < 0 or id=="":
		id = 0
	else:
		id = int(id)
	
	if flag < 0 or flag=="":
		flag = 'host'
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	
	debug(userCode)
	if flag == 'host':###获取主机信息
		sql ="select public.\"PGetHost\"(%d,false,%s)" %(id,loginuc) 		
	else: ###主机组信息
		sql ="select public.\"PGetHGroup\"(%d)" %(id) 	
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
##获取 主机 的详细信息
@b_host_manage.route('/getHost_info',methods=['GET', 'POST'])
def getHost_info():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	loginuc = request.form.get('a1')
	loginuc = "E'%s'" %(loginuc)
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	id = request.form.get('a1')
	
	if id < 0 or id=="":
		id = 0
	else:
		id = int(id)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		

	sql ="select public.\"PGetHost\"(%d,false,%s)" %(id,loginuc) 		
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
##保存 主机组
@b_host_manage.route('/save_hostgrp',methods=['GET', 'POST'])
def save_hostgrp():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	HostGrp = request.form.get('a1')
	AccessSet = request.form.get('a2')	
	Hgroup_json = json.loads(HostGrp)
	FromFlag = request.form.get('a10')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(HostGrp);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	if HostGrp < 0:
		HostGrp ="";
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		

	sql ="select public.\"PSaveHGroup\"(E'%s')" %(MySQLdb.escape_string(HostGrp).decode('utf-8')) 		
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	if ret['Result'] == False:
		if int(Hgroup_json['HGId']) == 0:
			system_log(userCode,"创建主机组：%s" % Hgroup_json['HGName'],"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(userCode,"编辑主机组：%s" % Hgroup_json['HGName'],"失败："+ret['ErrMsg'],FromFlag)	
		curs.close()
		conn.close()
		return results

	AccessSet_json = json.loads(AccessSet)
	AccessSet_json['HGId'] = ret['HGId']
	AccessSet = json.dumps(AccessSet_json)
	sql = "select public.\"PAddHostToAccessAuth\"(E'%s');" %(MySQLdb.escape_string(AccessSet).decode("utf-8"))
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: (%d)\"}" % (sys._getframe().f_lineno)
	conn.commit()
	if int(Hgroup_json['HGId']) == 0:
		system_log(userCode,"创建主机组：%s" % Hgroup_json['HGName'],"成功",FromFlag)
	else:
		system_log(userCode,"编辑主机组：%s" % Hgroup_json['HGName'],"成功",FromFlag)
	AccessAuth_Name = ""
	AccessSet_json = json.loads(AccessSet)
	for i in AccessSet_json['AccessAuthSet']:
		id = i['AccessAuthId']
		sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
		curs.execute(sql)
		AccessAuth_Name = curs.fetchall()[0][0]
		system_log(userCode,"访问授权\"%s\"新增授权对象：%s " % (AccessAuth_Name,Hgroup_json['HGName']),"成功",FromFlag)
	
	curs.close()
	conn.close()
	return results
##检查登录账号是否在管理授权之下（创建主机组的时候是否有访问授权）
@b_host_manage.route('/check_manageAuth',methods=['GET', 'POST'])
def check_manageAuth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		

	sql="select public.\"PGetManageAuth\"(null,null,E'%s',null,null,null);"%(userCode)	
	try:
		debug(sql)
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result_auth = ret['data']
	for index,auth in enumerate(result_auth):
		if auth['MScopeSet'] != None:
			return 'false'
	curs.close()
	conn.close()
	return 'true'
	
##回显 主机组信息
@b_host_manage.route('/getHostgrp_info',methods=['GET', 'POST'])
def getHostgrp_info():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	id = request.form.get('a1')
	if id < 0:
		id =0;
	else:
		id = int(id)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		

	sql ="select public.\"PGetHGroup\"(%d)" %(id) 		
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
	
##删除 主机、主机组
@b_host_manage.route('/delete_node',methods=['GET', 'POST'])
def delete_node():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	id = request.form.get('a1')
	pid = request.form.get('a2')
	ishost = request.form.get('a3')
	isdeletehost = request.form.get('a4')
	FromFlag = request.form.get('a10')
	
	if check_role(userCode,"主机管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if id < 0:
		id =0;
	else:
		id = int(id)
	if pid < 0:
		pid =0;
	else:
		pid = int(pid)
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
		
	if isdeletehost == "true":
		Type_delete_str = "删除组内主机"
	else:
		Type_delete_str = "移除组内主机"

	if int(pid) == 0:
		P_Name = '/'
	else:
		P_Name = ""
		path_arry = []
		sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % int(pid)
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])
	
		while results_1[0][0] != 0:
			sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results_1[0][0]
			debug(sql)
			curs.execute(sql)
			results_1 = curs.fetchall()
			path_arry.insert(0,results_1[0][1])
		P_Name = '/'+'/'.join(path_arry)
	
	Name = ""
	if ishost == "true":
		sql = "select \"HostName\",\"HostIP\" from public.\"Host\" where \"HostId\"=%d" % int(id)
		curs.execute(sql)
		result_tmp = curs.fetchall()
		if len(result_tmp) == 0:
			return "{\"Result\": true}"
		Name = result_tmp[0][0]+'('+result_tmp[0][1]+')'
	else:
		sql = "select public.\"PGetGroupMember\"(%d,2);" %(int(id))
		debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		mems_result = curs.fetchall()[0][0]
		if mems_result == None:
			mems_result = []
			Members_array = ['无']
		else:
			mems_result = json.loads(mems_result)
			Members_array = []
			for i in mems_result:
				MembersStr = i['HostName']+'('+i['HostIP']+')'
				Members_array.append(MembersStr)
	
		sql = "select \"HGName\" from public.\"HGroup\" where \"HGId\"=%d" % int(id)
		curs.execute(sql)
		Name = curs.fetchall()[0][0]


	sql ="select public.\"PDeleteHostDirectory\"(E'%s',%d,%d,%s,%s)" %(userCode,pid,id,ishost,isdeletehost);		
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	if ret['Result'] == False:
		if ishost == "true":
			if isdeletehost == "true":
				system_log(userCode,"删除主机：%s (所属组：%s)" % (Name,P_Name),"失败："+ret['ErrMsg'],FromFlag)
			else:
				system_log(userCode,"移除主机：%s (所属组：%s)" % (Name,P_Name),"失败："+ret['ErrMsg'],FromFlag)
		else:
			system_log(userCode,"删除主机组：%s (所属组：%s，%s：%s)" % (Name,P_Name,Type_delete_str,'、'.join(Members_array)),"失败："+ret['ErrMsg'],FromFlag)
	conn.commit();
	if ishost == "true":
		if isdeletehost == "true":
			system_log(userCode,"删除主机：%s (所属组：%s)" % (Name,P_Name),"成功",FromFlag)	
		else:
			system_log(userCode,"移除主机：%s (所属组：%s)" % (Name,P_Name),"成功",FromFlag)
	else:
		system_log(userCode,"删除主机组：%s (所属组：%s，%s：%s)" % (Name,P_Name,Type_delete_str,'、'.join(Members_array)),"成功",FromFlag)	
	curs.close()
	conn.close()
	return results

##粘贴主机、主机组
@b_host_manage.route('/paste_node',methods=['GET', 'POST'])
def paste_node():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	oldparentid = request.form.get('a1')
	newparentid = request.form.get('a2')
	ishost = request.form.get('a3')
	iscut = request.form.get('a4')
	id = request.form.get('a5')
	FromFlag = request.form.get('a10')
	if check_role(userCode,"主机管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if oldparentid < 0:
		oldparentid =0;
	else:
		oldparentid = int(oldparentid)
	if newparentid < 0:
		newparentid =0;
	else:
		newparentid = int(newparentid)
	if id < 0:
		id =0;
	else:
		id = int(id)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
		
	if ishost == "true":
		ishost_c = "主机"
	else:
		ishost_c = "主机组"	
	if iscut == "true":
		iscut_c = "剪切"
	else:
		iscut_c = "复制"
	debug("sssssssssss1")

	Name = ""
	if ishost == "true":
		sql = "select \"HostName\",\"HostIP\" from public.\"Host\" where \"HostId\"=%d" % int(id)
		curs.execute(sql)
		result_tmp = curs.fetchall()
		if len(result_tmp)==0:
			return "{\"Result\":false,\"ErrMsg\":\"主机不存在(%d)\"}" % (sys._getframe().f_lineno)
		Name = result_tmp[0][0]+'('+result_tmp[0][1]+')'
	else:
		sql = "select \"HGName\" from public.\"HGroup\" where \"HGId\"=%d" % int(id)
		curs.execute(sql)
		Name = curs.fetchall()
		if len(Name)==0:
			return "{\"Result\":false,\"ErrMsg\":\"主机组不存在(%d)\"}" % (sys._getframe().f_lineno)
		Name = Name[0][0]


	OP_Name = ""
	path_arry = []
	sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % int(oldparentid)
	curs.execute(sql)
	results_1 = curs.fetchall()
	path_arry.insert(0,results_1[0][1].replace('/',''))
	
	while results_1[0][0] != None and results_1[0][0] != 0:
		sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results_1[0][0]
		debug(sql)
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])
	OP_Name = '/'+'/'.join(path_arry)

	NP_Name = ""
	path_arry = []
	sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % int(newparentid)
	curs.execute(sql)
	results_1 = curs.fetchall()
	path_arry.insert(0,results_1[0][1].replace('/',''))
	
	while results_1[0][0] != None and results_1[0][0] != 0:
		sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results_1[0][0]
		debug(sql)
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])
	NP_Name = '/'+'/'.join(path_arry)

	ContentStr = iscut_c+ishost_c+":"+Name+"(原组："+OP_Name+"\t目标组："+NP_Name+")"
	debug(ContentStr)

	sql ="select public.\"PPasteHostDirectory\"(E'%s',%d,%d,%d,%s,%s)" %(userCode,oldparentid,newparentid,id,ishost,iscut);		
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	if ret['Result'] == False:
		system_log(userCode,"%s" % ContentStr,"失败："+ret['ErrMsg'],FromFlag)
	else:
		system_log(userCode,"%s" % ContentStr,"成功",FromFlag)
	conn.commit();
	curs.close()
	conn.close()
	return results

#过滤
@b_host_manage.route('/FindHostDirectory',methods=['GET', 'POST'])
def FindHostDirectory():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	pid = request.form.get('a1')
	
	if pid< 0 or pid=="":
		pid = 0
	else:
		pid = int(pid)
		
	filter = request.form.get('a2')
	if filter< 0 or filter =="":
		filter = ""; ## ;;;;
		
	#filter = filter.replace("'","''").replace('"','\"').replace('\\', '\\\\\\\\').replace("_", "\\\\_").replace("%", "\\\\%").replace("?", "\\\\?").replace(".", "\\\\.").replace("*", "\\\\*");
	debug(filter)
	#filter = filter.replace('\\\\\\\\n','\\n')
	##filter_list = filter.split(';')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	
	sql = "select \"User\".\"UserId\" from public.\"User\" where \"User\".\"UserCode\"=E'%s';" %(userCode)
	debug(sql)
	try:
			curs.execute(sql)
	except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]

	
	if filter =='': #
		sql ="select public.\"PGetHostDirectory\"(E'%s',%d,10,%s,null,null)" %(userCode,pid,results);	
	else:
		filter_arr=filter.split('\t');
		'''
		filter_json = {
			"loginusercode": userCode,\
			"hgid": pid,\
			"istree": False,\
			"hgname": "",\
			"hostname": "",\
			"hostip": "",\
			"devicetypename": "",\
			"accountname":"",\
			"hostservicename":"",\
			"protocolname":"",\
			"searchstring":filter,\
			"limitrow":None,\
			"offsetrow":None\
		}
		'''
		filter_json = {
			"loginusercode": userCode,\
			"hgid": pid,\
			"istree": False,\
			"hgname": filter_arr[1],\
			"hostname": filter_arr[2],\
			"hostip": filter_arr[3],\
			"devicetypename": filter_arr[4],\
			"accountname":filter_arr[6],\
			"hostservicename":filter_arr[5],\
			"protocolname":filter_arr[7],\
			"searchstring":filter_arr[0].replace('.','\\\\.'),\
			"limitrow":None,\
			"offsetrow":None,\
			"isfilter":True
		}
		sql ="select public.\"PFindHostDirectory\"(E'%s')" %((json.dumps(filter_json)).decode('utf-8'));		
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()
	if results:
		if results[0][0] :
			result = results[0][0].encode('utf-8')
		else:
			result = '[]';
	else:
		result = '[]';
		
	curs.close()
	conn.close()
	return result


@b_host_manage.route('/get_h_Dir',methods=['GET', 'POST'])
def get_h_Dir():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	hgid = request.form.get('a1')
	c_id = request.form.get('a2')
	typ = request.form.get('t0')
	if hgid < 0 or hgid=="":
		hgid = 0
	else:
		hgid = int(hgid)
		
	if c_id < 0 or c_id=="":
		c_id = 0
	else:
		c_id = int(c_id)
	
	if(typ <0 or typ==''):
		typ = 7
	else:
		typ = int(typ)
	
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	#typ = 7;		
	debug(userCode)
	sql = "select public.\"PGetHostDirectory\"('%s',%d,%d,%d,null,null)" %(userCode,hgid,typ,c_id)
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
	
##回放
@b_host_manage.route('/replay',methods=['GET', 'POST'])
def replay():
	t = "replay.html"
	return render_template(t)
	
#添加主机内的连接测试
@b_host_manage.route("/conn_test", methods=['GET', 'POST'])
def conn_test():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	param = request.form.get('a1')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(param);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	#### 账号 密码 加密 IsClearText ->true 加密
	param_json =  json.loads(param);
	
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值	

	if param_json.has_key('IsClearText1') == True and param_json['IsClearText1'] == True:	
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd(param_json['Password'],pwd_rc4);#执行函数
		param_json['Password'] = pwd_rc4.value #获取变量的值i

	if param_json.has_key('IsClearText2') == True and param_json['IsClearText2'] == True:	
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd(param_json['FromPassword'],pwd_rc4);#执行函数
		param_json['Password'] = pwd_rc4.value #获取变量的值

	param = json.dumps(param_json);
	sql="select public.\"PSaveHostConnectTest\"(E'%s');" %(MySQLdb.escape_string(param).decode('utf-8'))
	debug(sql)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	#插入数据	
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit();
	curs.close()
	conn.close()
	return results

#取主机内的连接测试结果
@b_host_manage.route("/get_conn_test", methods=['GET', 'POST'])
def get_conn_test():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	a1 = request.form.get('a1')

	sql="select public.\"PGetHostConnectTest\"(%s);" %(a1)
	debug(sql)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	#插入数据	
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')

	curs.close()
	conn.close()
	return results

#删除主机内的连接测试
@b_host_manage.route("/del_conn_test", methods=['GET', 'POST'])
def del_conn_test():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	a1 = request.form.get('a1')
	if check_role(userCode,'主机管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if not a1.isdigit():
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
	sql="select public.\"PDeleteHostConnectTest\"(%s);" %(a1)
	debug(sql)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#插入数据	
	try:
		debug(sql);
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return results
