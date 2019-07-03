#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
import MySQLdb
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from comm import ClientCheck
from comm import ServerCheck
from logbase import common
import httplib, urllib,urllib2
import hashlib
import uuid
import ssl
from Crypto.Cipher import DES3
import cookielib
from generating_log import system_log
import struct
import socket
import re
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
from htmlencode import parse_sess,check_role,checkserver,checkproto,checkserver1
host_grouping = Blueprint('host_grouping',__name__)

ERRNUM_MODULE_host_grouping = 1000

class _alarm_conf_(Structure):
	_fields_ = [("alarm_id",c_ulonglong),("alarm_val", c_int), ("alarm_type", c_int),("alarm_level", c_int),("alarm_action", c_int),("alarm_name",c_char_p),("alarm_dst",c_char_p),("alarm_msg",c_char_p)]

def debug(c):
	return 0
	path = "/var/tmp/debugzdp123.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

def checkip(ip):
	p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
	if p.match(ip):
		return True
	else:
		return False

def checkaccount(account):
	p = re.compile(u'^[\w\.\-]+$')
	if p.match(account):
		return True
	else:
		return False

def checkname(name):
        p = re.compile(u'^[\w\.\-\u4e00-\u9fa5]+$')
        if p.match(name):
                return True
        else:
                return False				
#ErrorEncode
def ErrorEncode(str1):
	newStr = "";
	if str1 == "":
			return "";
	newStr = str1.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;		
@host_grouping.route('/test_html',methods=['GET', 'POST'])
def test_html():
	clienttype = request.args.get('t1')
	if clienttype < 0 or clienttype == '':
		clienttype ='bhost'
	cmdstr = request.args.get('z1')
	#cmdstr = base64.b64encode(cmdstr)
	return render_template('test.html',clienttype=clienttype,cmdstr=cmdstr)

@host_grouping.route('/test_alert',methods=['GET', 'POST'])
def test_alert():
	se = request.args.get('a0')
	cmdstr = request.args.get('z1')
	return render_template('alert.html',se=se,cmdstr=cmdstr)
	
@host_grouping.route('/favorite_show',methods=['GET', 'POST'])
def favorite_show():
	se = request.args.get('a0')
	fid = request.args.get('z1')
	fname = request.args.get('z2')
	return render_template('favorite.html',se=se,fid=fid,fname=fname,cip=request.remote_addr)
		
@host_grouping.route('/Get_AuthObjectByLevel',methods=['GET','POST'])
def Get_AuthObjectByLevel():
	session = request.form.get('a0')
	hgid = request.form.get('z1')
	ip = request.form.get('z2')
	service_str = request.form.get('z3')
	account_name = request.form.get('z4')
	accounttype = request.form.get('z5')
	search_str = request.form.get('z6')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if mac == '' or mac == None:
		mac = 'null'
	else:
		mac = "%s" %str(mac)
		
	if ip == None:
		ip = "null"
	else:
		for i in ip.split('.'):
			if i and str(i).isdigit() == False:
				return '',403
		ip = "E'%s'" % ip
	if service_str == None:
		hostservicename = "null"
		proname = "null"
		port = "null"
		servicename = "null"
		conntype = "null"
		connparamvalue = "null"	
	else:
		service_obj = json.loads(service_str)
		if service_obj['HostServiceName'] == None:
			hostservicename = "null"
		else:
			if checkserver1(service_obj['HostServiceName'])==False:
				return '',403
				
			hostservicename = "E'%s'" % service_obj['HostServiceName']
		proname = "E'%s'" % service_obj['ProtocolName']
		if checkserver1(service_obj['ProtocolName'])==False:
			return '',403
		if str(service_obj['Port']).isdigit() == False:
			return '',403
		
		port = "E'%s'" % str(service_obj['Port'])
		if service_obj['ServiceName'] == None:
			servicename = "null"
		else:
			if checkserver1(service_obj['ServiceName'])==False:
				return '',403
			servicename = "E'%s'" % service_obj['ServiceName']
		if service_obj['ConnType'] == None:
			conntype = "null"
		else:
			if checkserver1(service_obj['ConnType'])==False:
				return '',403
			conntype = "E'%s'" % str(service_obj['ConnType'])
		if service_obj['ConnParamValue'] == None:
			connparamvalue = "null"
		else:
			if checkserver1(service_obj['ConnParamValue'])==False:
				return '',403
			connparamvalue = "E'%s'" % service_obj['ConnParamValue']
	
	if account_name == None:
		account_name = "null"
	else:
		account_name = "E'%s'" % account_name

	if accounttype == None:
		accounttype = "null"
	else:
		accounttype = "E'%s'" % accounttype	

	if search_str == None:
		search_str = "null"
	else:
		search_obj = json.loads(search_str)
		if len(search_obj) == 0:
			search_str = "null"
		else:
			search_dic = {"HostIP":"","HostName":"","ProtocolName":"","searchstring":""}
			hname = ""
			hip = ""
			pname = ""
			search_s = ""
			for search in search_obj:
				data = search.split('-',1)
				if data[0] == "hname":
					hname = hname + data[1] + '\n'
				elif data[0] == "IP":
					hip = hip + data[1] + '\n'
				elif data[0] == "pname":#协议
					pname = pname + data[1] + '\n'
				else:
					search_s = search_s + data[1] + '\n' 
			
			if hname != "":
				hname = hname[:-1]
			if hip != "":
				hip = hip[:-1]
			if pname != "":
				pname = pname[:-1]
			if search_s != "":
				search_s = search_s[:-1]
			search_s = search_s.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			search_dic['HostIP'] = hip
			search_dic['HostName'] = hname
			search_dic['ProtocolName'] = pname
			search_dic['searchstring'] = search_s
			search_dic = json.dumps(search_dic)
			search_str = MySQLdb.escape_string(search_dic).decode('utf-8')
			search_str = "E'%s'" % search_str
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"GetAuthObjectByLevel\"('%s','%s',null,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str))
			debug("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',%s,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip, mac,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str));
			curs.execute("select public.\"GetAuthObjectByLevel\"(E'%s',E'%s',%s,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip, mac,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str))
			
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/Pget_HostInfo',methods=['GET','POST'])
def Pget_HostInfo():
	session = request.form.get('a0')
	hid = request.form.get('z1')
	hgid = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetHostInfo\"('%s','%s',%s);" % (hid,usercode,hgid))
			curs.execute("select public.\"PGetHostInfo\"(E'%s',E'%s',%s);" % (hid,usercode,hgid))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
	
@host_grouping.route('/Find_HostForAccess',methods=['GET','POST'])
def Find_HostForAccess():
	session = request.form.get('a0')
	search = request.form.get('z1')
	hgid = request.form.get('z2')
	max_page = request.form.get('z3')
	offset_num = request.form.get('z4')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	search = json.loads(search)
	if len(search) != 0:
		search_str = '\n'.join(search)
		search_str = "E'%s'" % MySQLdb.escape_string(search_str).decode("utf-8")
	else:
		search_str = 'null'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PFindHostForAccess\"('%s','%s',null,null,%s,%s,%s,%s);" % (usercode,client_ip,hgid,search_str,max_page,offset_num))
			curs.execute("select public.\"PFindHostForAccess\"(E'%s',E'%s',null,null,%s,%s,%s,%s);" % (usercode,client_ip,hgid,search_str,max_page,offset_num))
			results = curs.fetchall()[0][0]#.encode('utf-8')
			#debug("%s" % str(results))
			if results == None:
				results = '[]'
			else:
				results = results.encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/save_favoritelist',methods=['GET','POST'])
def save_favoritelist():
	session = request.form.get('a0')
	name = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if check_role(usercode,'设备访问') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if checkname(name):
		pass
	else:
		return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select count(*) from private.\"FavoriteList\" where \"FavoriteName\"=E'%s'" % name)
			results = curs.fetchall()[0][0]
			if results == 0:
				#debug("insert into private.\"FavoriteList\"(\"FavoriteName\",\"UserId\")values('%s',(select \"UserId\" FROM public.\"User\" where \"UserCode\" = '%s'))RETURNING \"FavoriteId\";" % (name,usercode))
				curs.execute("insert into private.\"FavoriteList\"(\"FavoriteName\",\"UserId\")values(E'%s',(select \"UserId\" FROM \"User\" where \"UserCode\"=E'%s'))RETURNING \"FavoriteId\";" % (name,usercode))
				results = curs.fetchall()[0][0]
				system_log(usercode,"创建收藏夹:%s" % name,"成功","收藏夹")
				return "{\"Result\":true,\"FavoriteId\":%s}" % str(results)
			else:
				system_log(usercode,"创建收藏夹:%s" % name,"失败：收藏夹名称已存在","收藏夹")
				return "{\"Result\":false,\"ErrMsg\":\"收藏夹名称已存在\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/modify_favoritelist',methods=['GET','POST'])
def modify_favoritelist():
	session = request.form.get('a0')
	name = request.form.get('z1')
	fid = request.form.get('z2')
	oldname = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select \"FavoriteId\" from private.\"FavoriteList\" where \"FavoriteName\"='%s'" % MySQLdb.escape_string(name).decode('utf-8'))
			curs.execute("select \"FavoriteId\" from private.\"FavoriteList\" where \"FavoriteName\"=E'%s' and \"UserId\"=(select \"UserId\" FROM \"User\" where \"UserCode\"=E'%s')" % (MySQLdb.escape_string(name).decode('utf-8'),usercode))
			results = curs.fetchall()
			#debug("%s" % results)
			if len(results) == 0 or results[0][0] == int(fid):
				#debug("update private.\"FavoriteList\" set \"FavoriteName\" = '%s' where \"FavoriteId\"=%s" % (MySQLdb.escape_string(name).decode("utf-8"),fid))
				curs.execute("update private.\"FavoriteList\" set \"FavoriteName\" = E'%s' where \"FavoriteId\"=%s" % (MySQLdb.escape_string(name).decode('utf-8'),fid))
				system_log(usercode,"修改收藏夹%s名称：%s" % (oldname,name),"成功","收藏夹")
				return "{\"Result\":true}"
			else:
				system_log(usercode,"编辑收藏夹:%s" % name,"失败：收藏夹名称已存在","收藏夹")
				return "{\"Result\":false,\"ErrMsg\":\"收藏夹名称已存在\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/PGetHost_ByFavorite',methods=['GET','POST'])
def PGetHost_ByFavorite():
	session = request.form.get('a0')
	json_data = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetHostByFavorite\"('%s');" % (MySQLdb.escape_string(json_data).decode("utf-8")))
			curs.execute("select public.\"PGetHostByFavorite\"(E'%s');" % (MySQLdb.escape_string(json_data).decode("utf-8")))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d)\"}" % (sys._getframe().f_lineno)
		
@host_grouping.route('/PGet_FavoriteList',methods=['GET','POST'])
def PGet_FavoriteList():
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetFavoriteList\"('%s');" % (usercode))
			curs.execute("select public.\"PGetFavoriteList\"(E'%s');" % (usercode))
			results = curs.fetchall()[0][0]#.encode('utf-8')
			if results == None:
				results = '[]'
			else:
				results = results.encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
	
@host_grouping.route('/save_favoritehost',methods=['GET','POST'])
def save_favoritehost():
	session = request.form.get('a0')
	hgid = request.form.get('z1')
	fid = request.form.get('z2')
	hostid = request.form.get('z3')
	hname = request.form.get('z4')
	fname = request.form.get('z5')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	
	if check_role(usercode,'设备访问') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if checkname(hname):
		pass
	else:
		return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if checkname(fname.replace(',','')):
		pass
	else:
		return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	
	if hostid.isdigit() and hgid.isdigit():
		pass
	else:
		return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		
	
	fid_array = json.loads(fid)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			for fid in fid_array:
				#debug("insert into private.\"FavoriteHostList\"(\"UserId\",\"FavoriteId\",\"HGId\",\"HostId\")values((select \"UserId\" FROM \"User\" where \"UserCode\"='%s'),%s,%s,%s)" % (usercode,fid,hgid,hostid))
				curs.execute("insert into private.\"FavoriteHostList\"(\"UserId\",\"FavoriteId\",\"HGId\",\"HostId\")values((select \"UserId\" FROM \"User\" where \"UserCode\"=E'%s'),%s,%s,%s)" % (usercode,fid,hgid,hostid))
			system_log(usercode,"添加主机：%s到收藏夹：%s" % (hname,fname),"成功","主机分组")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		conn.rollback();
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/del_favorite',methods=['GET','POST'])
def del_favorite():
	session = request.form.get('a0')
	fid = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("delete from private.\"FavoriteList\" where \"FavoriteId\"=%s" % (fid))
			curs.execute("delete from private.\"FavoriteList\" where \"FavoriteId\"=%s" % (fid))
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/cancel_favoritehost',methods=['GET','POST'])
def cancel_favoritehost():
	session = request.form.get('a0')
	hgid = request.form.get('z1')
	hid = request.form.get('z2')
	fid = request.form.get('z3')
	hname = request.form.get('z4')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if fid != None:
				#debug("delete from private.\"FavoriteHostList\" where \"FavoriteId\"=%s and \"HGId\"=%s and \"HostId\"=%s and \"UserId\"=(select \"UserId\" FROM \"User\" where \"UserCode\"='%s')" % (fid,hgid,hid,usercode))
				curs.execute("delete from private.\"FavoriteHostList\" where \"FavoriteId\"=%s and \"HGId\"=%s and \"HostId\"=%s and \"UserId\"=(select \"UserId\" FROM \"User\" where \"UserCode\"=E'%s')" % (fid,hgid,hid,usercode))
				system_log(usercode,"取消收藏主机:%s" % hname,"成功","收藏夹")
			else:
				#debug("delete from private.\"FavoriteHostList\" where \"HGId\"=%s and \"HostId\"=%s and \"UserId\"=(select \"UserId\" FROM \"User\" where \"UserCode\"='%s')" % (hgid,hid,usercode))
				curs.execute("delete from private.\"FavoriteHostList\" where \"HGId\"=%s and \"HostId\"=%s and \"UserId\"=(select \"UserId\" FROM \"User\" where \"UserCode\"=E'%s')" % (hgid,hid,usercode))
				system_log(usercode,"取消收藏主机:%s" % hname,"成功","主机分组")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
#最近访问	
@host_grouping.route('/PGet_RecentAccessHost',methods=['GET','POST'])
def PGet_RecentAccessHost():
	session = request.form.get('a0')
	max_page = request.form.get('z1')
	offset_num = request.form.get('z2')
	search_str = request.form.get('z3')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if search_str == "[]":
		search_str = {"srcip":""}
		search_str['srcip'] = client_ip
		search_str = json.dumps(search_str)
	else:
		search_obj = json.loads(search_str)
		if isinstance(search_obj, list) == False:
			if search_obj.has_key('HostServiceName') == True:
				search_dic = {"hostip":"","HostServiceName":"","srcip":client_ip}
				search_dic['hostip'] = search_obj['hostip']
				search_dic['HostServiceName'] = search_obj['HostServiceName']
		else:
			search_dic = {"HostIP":"","HostName":"","ProtocolName":"","searchstring":"","srcip":client_ip}
			hname = ""
			ip = ""
			pname = ""
			search_s = ""
			for search in search_obj:
				data = search.split('-',1)
				if data[0] == "hname":
					hname = hname + data[1] + '\n'
				elif data[0] == "IP":
					ip = ip + data[1] + '\n'
				elif data[0] == "pname":#协议
					pname = pname + data[1] + '\n'
				else:
					search_s = search_s + data[1] + '\n' 
			
			if hname != "":
				hname = hname[:-1]
			if ip != "":
				ip = ip[:-1]
			if pname != "":
				pname = pname[:-1]
			if search_s != "":
				search_s = search_s[:-1]
			search_dic['HostIP'] = ip
			search_dic['HostName'] = hname
			search_dic['ProtocolName'] = pname
			search_dic['searchstring'] = search_s
		search_dic = json.dumps(search_dic)
		#search_str = MySQLdb.escape_string(search_dic).decode('utf-8')
		search_str = "%s" % search_dic
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."PGetRecentAccessHost"(E\'%s\',%s,%s,E\'%s\')' % (usercode,max_page,offset_num,search_str)
			curs.execute(sql)
			#debug("123" + sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		
@host_grouping.route('/PGet_HostAccessCfg',methods=['GET','POST'])
def PGet_HostAccessCfg():
	session = request.form.get('a0')
	ip = request.form.get('z1')
	proname = request.form.get('z2')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."PGetHostAccessCfg"(E\'%s\',E\'%s\',E\'%s\',null,null)' % (usercode,ip,proname)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d)\"}" % (sys._getframe().f_lineno)
		
@host_grouping.route('/get_token_remote',methods=['GET','POST'])
def get_token_remote():
	session = request.form.get('a0')
	param_str = request.form.get('z1')
	ip = request.form.get('z2')
	pname = request.form.get('z3')
	username = request.form.get('z4')
	pwd = request.form.get('z5')
	url_str = request.form.get('z6')
	user = request.form.get('z7')
	host_set = request.form.get('z8')
	save_flag = request.form.get('z9')
	diskmap = request.form.get('z10')
	#save_set = request.form.get('z11')#SavePrivatePassword
	cmd_set = request.form.get('z12')
	#mac=request.form.get('m1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if mac == '' or mac == None:
		mac = 'null'
	else:
		mac = "%s" %str(mac)		
	
	host_set_json = json.loads(host_set)

	json_data = {"username":"","password_hash":"","password_salt":"","connection_name":"","protocol":"","diskmap":False,"param":[]}
	json_data['username'] =  username
	serverpwd = pwd
	#password_salt
	key = hashlib.sha256(uuid.uuid4().hex).hexdigest().upper();
	#password_hash
	pwd = hashlib.sha256(session + str(key)).hexdigest().upper();
	json_data['password_hash'] = pwd
	json_data['password_salt'] = key
	json_data['connection_name'] = session
	json_data['protocol'] = pname

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select \"ColorScheme\" from public.\"User\" where \"UserCode\" = '%s';" %(usercode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results == 1:
				ColorScheme = {"name":"color-scheme","value":"green-black"}
			elif results == 2:
				ColorScheme = {"name":"color-scheme","value":""}
			elif results == 0:
				ColorScheme = {"name":"color-scheme","value":"white-black"}
			param_str = json.loads(param_str)
			param_str.append(ColorScheme)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

	json_data['param'] = param_str
	if diskmap == 'true':
		json_data['diskmap'] = True
	else:
		json_data['diskmap'] = False
	debug("json_data1: "+str(json_data))
	if pname == "RDP" or pname == "VNC" or pname == "X11" or host_set_json['ConnModeName'] == 'web_con|mfs':
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		session_id = c_ulonglong()
		pro_name = c_char_p()
		pro_name.value = "0"*512 # 初始化 指针
		lib.replay_name_get.argtypes = [c_int,c_char_p,POINTER(c_ulonglong)]#定义函数参数
		lib.replay_name_get.restype = None#定义函数返回值
		p_id = 0
		if pname == "RDP":
			p_id = 2
		elif pname == "VNC":
			p_id = 3
		elif pname == "X11":
			p_id = 12
		elif pname == "ORACLE":
			p_id = 7
		elif pname == "MSSQL":
			p_id = 8
		elif pname == "MYSQL":
			p_id = 9
		elif pname == "HTTP(S)":
			p_id = 13
		elif pname == "RADMIN":
			p_id = 14
		elif pname == "SYBASE":
			p_id = 10	
		elif pname == "DB2":
			p_id = 16	
		elif pname == "PCANY":
			p_id = 15														

		debug("diskmap: "+str(diskmap))
		debug("json_data: "+str(json_data))
		debug("ClientName: "+str(host_set_json['ClientName']))
		if diskmap == "false":
			for params in json_data['param']:
				if params['name'] == "username":
					user_name = params['value'] + '*0*0'
					if host_set_json['ClientName'] != "":
						user_name = user_name + '*' + host_set_json['ClientName'] + '*0'
					else:
						user_name = user_name + '*default*0'
					params['value'] = user_name;
		else:
			if p_id == 0:
				pro_name = create_string_buffer(pname,512)
				debug("pro_name: "+str(pro_name))
				debug("pro_name1: "+str(pro_name.value))
			lib.replay_name_get(p_id,pro_name,byref(session_id))
			session_id = session_id.value
			debug("session_id: "+str(session_id))
			cmd_set = json.loads(cmd_set)
			for params in json_data['param']:
				if params['name'] == "username":
					user_name = params['value'] + '*' + str(session_id) + '*1'
					cmd_set['username'] = params['value'] + '*' + str(session_id) + '*2'
					if host_set_json['ClientName'] != "":
						user_name = user_name + '*' + host_set_json['ClientName'] + '*0'
						cmd_set['username'] = cmd_set['username'] + '*' + host_set_json['ClientName'] + '*0'
					else:
						user_name = user_name + '*default*0'
						cmd_set['username'] = cmd_set['username'] + '*default*0'
					params['value'] = user_name
		debug("Part 1 user_name: " +str(user_name))
		debug("Part 1 over")
		if host_set_json['ConnModeName'] != '':
			if diskmap == "true":
                                if pname == "HTTP(S)":
					if host_set_json['ConnMode'] == "||":
						host_set_json['ConnMode'] = ""
                                        cmd_set['username'] = cmd_set['username'] +'\t'+ host_set_json['ServiceName'] +'\t'+ host_set_json['ConnParam'] +'\t'+ host_set_json['ConnMode'] +'\t'+ host_set_json['ClientName'] +'\t'
                                else:
                                        cmd_set['username'] = cmd_set['username'] +'\t'+ host_set_json['ServiceName'] +'\t'+ host_set_json['ConnMode'] +'\t'+ host_set_json['ConnParam'] +'\t'+ host_set_json['ClientName'] +'\t' 
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn3:
					curs3 = conn3.cursor()
					sql = "select \"ServicePort\" from public.\"ApplicationConfig\" where \"ApplicationName\"='RDP|VNC|X11'"
					curs3.execute(sql)
					port_rdp = curs3.fetchall()[0][0]
					debug("Part 2-1 port_rdp: " +str(port_rdp))
					if diskmap == "true":
						cmd_set['Port']	= port_rdp
					for params in json_data['param']:
						if params['name'] == "port":
							params['value'] = port_rdp
							debug("Part 2-1 over: " +str(params))
						if params['name'] == "username":
							debug("Part 2-2 host_set_json['ServiceName']: " +str(host_set_json['ServiceName']))
							debug("Part 2-2 host_set_json['ConnMode']: " +str(host_set_json['ConnMode']))
							debug("Part 2-2 host_set_json['ConnParam']: " +str(host_set_json['ConnParam']))
							debug("Part 2-2 host_set_json['ClientName']: " +str(host_set_json['ClientName']))
                                                        if host_set_json['ConnMode'] == None:
                                                                host_set_json['ConnMode'] = ""
                                                        if pname == "HTTP(S)":
								if host_set_json['ConnMode'] == "||":
									host_set_json['ConnMode'] = ""
                                                                if diskmap == "false":
                                                                        params['value'] = params['value'] +'\t'+ host_set_json['ServiceName'] +'\t'+ host_set_json['ConnParam'] +'\t'+ host_set_json['ConnMode'] +'\t'+ host_set_json['ClientName'] +'\t'
                                                                else:
                                                                        params['value'] = user_name +'\t'+ host_set_json['ServiceName'] +'\t'+ host_set_json['ConnParam'] +'\t'+ host_set_json['ConnMode'] +'\t'+ host_set_json['ClientName'] +'\t'
                                                        else:
                                                                if diskmap == "false":
                                                                        params['value'] = params['value'] +'\t'+ host_set_json['ServiceName'] +'\t'+ host_set_json['ConnMode'] +'\t'+ host_set_json['ConnParam'] +'\t'+ host_set_json['ClientName'] +'\t'
                                                                else:
                                                                        params['value'] = user_name +'\t'+ host_set_json['ServiceName'] +'\t'+ host_set_json['ConnMode'] +'\t'+ host_set_json['ConnParam'] +'\t'+ host_set_json['ClientName'] +'\t'
							debug("Part 2-2 over: " +str(params))
					json_data['protocol'] = "RDP"
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
		debug("Part 2 over")
		debug("save_flag: "+str(save_flag))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn1,conn1.cursor() as curs1:
			'''
			if save_flag == '1':
				set_list = json.loads(save_set)
				sql = "select public.\"SavePrivatePassword\"(E'%s',E'%s',E'%s',E'%s',%s,E'%s',E'%s',%s,E'%s',E'%s',E'%s',E'%s')" % (set_list[0],set_list[1],set_list[2],set_list[3],set_list[4],set_list[5],set_list[6],set_list[7],set_list[8],set_list[9],set_list[10],set_list[11])
				curs1.execute(sql)
			'''
			if mac !='null':
				sql ="insert into private.\"IPMACMap\"(\"ClientMAC\", \"ClientIP\", \"LastModifyTime\")values(%s, '%s', CURRENT_TIMESTAMP);" % (mac, client_ip);
				curs1.execute(sql)
				conn1.commit()
			if save_flag == '0':
				#host_set_json = json.loads(host_set)
				sql = "select \"Pwd\" from private.\"HostAccessCfg\" where \"UserCode\"=E'%s' and \"ServerIP\"=E'%s' and \"ProtocolName\"=E'%s' and \"ServerUser\"=E\'%s\'" %  (usercode,host_set_json['ServerIP'],host_set_json['ProtocolName'],host_set_json['ServerUser'])
				curs1.execute(sql)
				re_pwd = curs1.fetchall()
				#debug("re_pwd:%s" % str(re_pwd))
				if len(re_pwd) == 0:
					host_set_json['Pwd'] = None
				else:
					host_set_json['Pwd'] = re_pwd[0][0]
				host_set = json.dumps(host_set_json)
			
			host_set_json = json.loads(host_set)
			sql = "select public.\"SaveRecentAccessHost\"(E'%s',E'%s')" %(usercode,host_set_json['ServerIP'])
			debug("Part 3 saverecentaccesshost sql1: "+sql)
			curs1.execute(sql)
			debug("Sql1 execute success")
			saveflag = curs1.fetchall()
			saveflag = json.loads(saveflag[0][0].encode('utf-8'))['Result']
			if saveflag != True:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
			#保存到最近访问
			sql = 'select public."PSaveHostAccessCfg"(E\'%s\')' % (MySQLdb.escape_string(host_set).decode('utf-8'))
			#debug("sql:%s" % sql)
			debug("Part 3 savehostaccesscfg sql2: "+sql)
			curs1.execute(sql)
			debug("Sql2 execute success")
			debug("Part 3 over")
		with pyodbc.connect(StrSqlConn('BH_REMOTE')) as conn:
			curs = conn.cursor()
			#创建web连接
			sql = 'select public."PCreateNewConnection"(E\'%s\')' % (MySQLdb.escape_string(json.dumps(json_data)).decode('utf-8'))
			#debug("sql:%s" % sql)
			debug("Part 4 createnewconnection sql1: "+sql)
			curs.execute(sql)
			debug("Part 4 sql1 success ")
			conn.commit()
			try:
				ssl._create_default_https_context = ssl._create_unverified_context
				#url = url_str + '/bhremote/api/tokens'
				port = url_str.split(':')[-1];
				#post_data = "username="+user+"&password="+serverpwd
				url = 'https://127.0.0.1:'+port+'/bhremote/api/tokens'
				post_data = "username="+username+"&password="+session
				
				debug("Part 4 post_data:%s" % post_data)
				#debug("url_str:%s" % url)
				#cookieJar=cookielib.CookieJar()
				#opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
				try:
					#urllib2.install_opener(opener)
					req = urllib2.urlopen(url, post_data)
					debug("Part 4 urlopen success")
					#debug("%s" % str(cookieJar))
					#result = opener.open(req)
					#debug(str(result.read()))
					# 访问主页 自动带着cookie信息
					#result = opener.open(url)
					#debug(str(result.read()))
				except Exception,e:
					conn.rollback()
				content = req.read()
				debug("Content read success")
				debug("Content: "+str(content))
				
				if pname == "RDP" or pname == "VNC" or pname == "X11" or host_set_json['ConnModeName'] == 'web_con|mfs':
					debug("username: "+str(user_name))
					debug("cmdset: "+str(cmd_set))
					content_json = json.loads(content)
					content_json['UserName'] = user_name
					if diskmap == "true":
						debug("username2: "+str(cmd_set['username']))
						debug("sessionid: "+str(session_id))
						content_json['SessionId'] = session_id
						content_json['UserName2'] = cmd_set['username']
					content_json['CmdSet'] = base64.b64encode(json.dumps(cmd_set))
					debug("content_json: "+str(content_json))
					if os.path.exists("/etc/webext.conf"):
						content_json['Flag'] = 1
					else:
						content_json['Flag'] = 0
					return json.dumps(content_json)
				else:
					return content
			except Exception,e:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
				#debug(str(e))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
		
@host_grouping.route('/rc4_decrypt',methods=['GET','POST'])
def rc4_decrypt():
	se = request.form.get('a0')
	pwd = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.decrypt_pwd.restype = None #定义函数返回值
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.decrypt_pwd(pwd,pwd_rc4);
	return "{\"Result\":true,\"info\": \"%s\"}" % pwd_rc4.value
	
@host_grouping.route('/rc4_encrypt',methods=['GET','POST'])
def rc4_encrypt():
	se = request.form.get('a0')
	pwd = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd(pwd.encode('utf-8'),pwd_rc4);#执行函数
	return "{\"Result\":true,\"info\": \"%s\"}" % pwd_rc4.value
	
@host_grouping.route('/Save_HostAccessCfg',methods=['GET','POST'])
def Save_HostAccessCfg():
	se = request.form.get('a0')
	json_data = request.form.get('z1')
	remark_json = request.form.get('z2')
	save_flag = request.form.get('z3')
	cmd_set = request.form.get('z4')
	md5_str = request.form.get('m1')
	#mac=request.form.get('m2')
	#save_set = request.form.get('z5')#SavePrivatePassword
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if mac == '' or mac == None:
		mac = 'null'
	else:
		mac = "%s" %str(mac)	
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(json_data);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			'''
			if save_flag == '1':
				set_list = json.loads(save_set)
				sql = "select public.\"SavePrivatePassword\"(E'%s',E'%s',E'%s',E'%s',%s,E'%s',E'%s',%s,E'%s',E'%s',E'%s',E'%s')" % (set_list[0],set_list[1],set_list[2],set_list[3],set_list[4],set_list[5],set_list[6],set_list[7],set_list[8],set_list[9],set_list[10],set_list[11])
				curs.execute(sql)
				results = curs.fetchall()[0][0].encode('utf-8')
				re_pwd = json.loads(results)
				if re_pwd['Result'] == False:
					return "{\"Result\":false,\"ErrMsg\":\"密码保存失败\"}" % (sys._getframe().f_lineno)
			'''
			if mac != 'null':
				sql ="insert into private.\"IPMACMap\"(\"ClientMAC\", \"ClientIP\", \"LastModifyTime\")values(%s, '%s', CURRENT_TIMESTAMP);" % (mac, client_ip);
				curs.execute(sql)
				conn.commit()
			if save_flag == '0':
				host_set_json = json.loads(json_data)
				sql = "select \"Pwd\" from private.\"HostAccessCfg\" where \"UserCode\"=E'%s' and \"ServerIP\"=E'%s' and \"ProtocolName\"=E'%s' and \"ServerUser\"=E\'%s\'" %  (usercode,host_set_json['ServerIP'],host_set_json['ProtocolName'],host_set_json['ServerUser'])
				curs.execute(sql)
				re_pwd = curs.fetchall()
				#debug("re_pwd:%s" % str(re_pwd))
				if len(re_pwd) == 0:
					host_set_json['Pwd'] = None
				else:
					host_set_json['Pwd'] = re_pwd[0][0]
				json_data = json.dumps(host_set_json)
			host_set_json = json.loads(json_data)
			sql = "select public.\"SaveRecentAccessHost\"(E'%s',E'%s')" %(usercode,host_set_json['ServerIP'])
			curs.execute(sql)
			saveflag = curs.fetchall()
			saveflag = json.loads(saveflag[0][0].encode('utf-8'))['Result']
			if saveflag != True:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

			sql = 'select public."PSaveHostAccessCfg"(E\'%s\')' % (MySQLdb.escape_string(json_data).decode('utf-8'))
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			re_json = json.loads(results)
			cmd_set_json = json.loads(cmd_set)
			if cmd_set_json['ConnMode'] == "||":
				cmd_set_json['ConnMode'] = ""
			cmd_set = json.dumps(cmd_set_json)
			re_json['CmdSet'] = base64.b64encode(cmd_set)
			if os.path.exists("/etc/webext.conf"):
				re_json['Flag'] = 1
			else:
				re_json['Flag'] = 0
			results = json.dumps(re_json)
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@host_grouping.route('/save_remark',methods=['GET','POST'])
def save_remark():
	se = request.form.get('a0')
	remark_json = request.form.get('z1')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(remark_json);##python中的json的MD5
		if(parse_sess(md5_str,se,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."PSavePlan"(E\'%s\')' % (MySQLdb.escape_string(remark_json).decode('utf-8'))
			curs.execute(sql)
			conn.commit()
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@host_grouping.route('/get_plan',methods=['GET','POST'])
def get_plan():
	se = request.form.get('a0')
	hostip = request.form.get('z1')
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."PGetPlan"(E\'%s\',E\'%s\',null,null)' % (usercode,hostip)
			curs.execute(sql)
			conn.commit()
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@host_grouping.route('/Get_AuthObjectByInput',methods=['GET','POST'])
def Get_AuthObjectByInput():
	se = request.form.get('a0')
	hostip = request.form.get('z1')
	pro_name = request.form.get('z2')
	port = request.form.get('z3')
	account_name = request.form.get('z4')
	service_name = request.form.get('z5')
	conntype = request.form.get('z6')
	
	
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if mac == '' or mac == None:
		mac = 'null'
	else:
		mac = "%s" %str(mac)
	
	if service_name == "":
		service_name = 'null'
	else:
		if checkserver1(service_name) == False:
			return '',403
		service_name = "'%s'" % service_name
		
	if conntype == "":
		conntype = 'null'
	else:
		if checkserver1(conntype) == False:
			return '',403
			
		conntype = "'%s'" %conntype

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."GetAuthObjectByInput"(E\'%s\',E\'%s\',%s,E\'%s\',null,E\'%s\',%s,E\'%s\',%s,%s)' % (usercode,client_ip,mac,pro_name,hostip,port,account_name,service_name,conntype)
			curs.execute(sql)
			results = curs.fetchall()#[0][0]
			if results == []:
				results = None
			else:
				results = results[0][0]
			if results == None:
				sql = 'select public."PGetGlobalStrategy"()'
				curs.execute(sql)
				results = curs.fetchall()[0][0].encode('utf-8')
				global_s = json.loads(results)
				if global_s['EnableAlarm'] == 0:
					return ""
				else:
					#void send_login_alert_log(uint cip, ushort cport, uint sip, ushort sport, const char *bhuser, const char *bhname, const char *serveruser, const char *proto, alarm_conf alarm, int error)
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					c_ip = struct.unpack("!L",socket.inet_aton(client_ip))[0]
					s_ip = struct.unpack("!L",socket.inet_aton(hostip))[0]
					c_ip = socket.ntohl(c_ip)
					cip = c_uint(c_ip)
					cport = c_ushort(0)
					s_ip = socket.ntohl(s_ip)
					sip = c_uint(s_ip)
					sport = c_ushort(int(port))
					bhuser = usercode
					sql = "select \"UserName\" from public.\"User\" where \"UserCode\"=E'%s'" % usercode
					curs.execute(sql)
					bhname = curs.fetchall()[0][0].encode('utf-8')
					bhname = bhname
					serveruser = account_name
					proto = pro_name
					#_fields_ = [("alarm_id",c_ulonglong),("alarm_val", c_int), ("alarm_type", c_int),("alarm_level", c_int),("alarm_action", c_int),("alarm_name",c_char_p),("alarm_dst",c_char_p),("alarm_msg",c_char_p)]
					alarm_conf = _alarm_conf_()
					sql= "select public.\"PGetEventAlarmInfo\"(%d,null,null,null,null,null);" % global_s['EventAlarmInfoId']
					curs.execute(sql)
					alarm_str = curs.fetchall()[0][0].encode('utf-8')
					alarm_data = json.loads(alarm_str)
					alarm_conf.alarm_id = alarm_data['data'][0]['EventAlarmInfoId']
					alarm_conf.alarm_val = global_s['EnableAlarm']
					alarm_conf.alarm_type = alarm_data['data'][0]['EventType']
					alarm_conf.alarm_level = alarm_data['data'][0]['EventLevel']
					if alarm_data['data'][0]['AlarmAction'] == 1:#邮件
						alarm_conf.alarm_action = 0x00000080
					elif alarm_data['data'][0]['AlarmAction'] == 3:#短信网关
						alarm_conf.alarm_action = 0x00000100
					elif alarm_data['data'][0]['AlarmAction'] == 4:#snmp
						alarm_conf.alarm_action = 0x00008000
					elif alarm_data['data'][0]['AlarmAction'] == 5:#syslog
						alarm_conf.alarm_action = 0x00004000
					alarm_conf.alarm_name = alarm_data['data'][0]['Name']
					dst_str = ""
					for dst in alarm_data['data'][0]['UserSet']:
						dst_str = dst_str + dst['UserCode'] + ';'
					if dst_str != "":
						alarm_conf.alarm_dst = dst_str[:-1]
					alarm_conf.alarm_msg = "访问权限检查失败"
					lib.send_login_alert_log.argtypes = [c_uint,c_ushort,c_uint,c_ushort,c_char_p,c_char_p,c_char_p,c_char_p,_alarm_conf_,c_int]#定义函数参数
					lib.send_login_alert_log.restype = None#定义函数返回值
					lib.send_login_alert_log(cip,cport,sip,sport,bhuser,bhname,serveruser,proto,alarm_conf,5)
				return ""
			return results.encode('utf-8')
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@host_grouping.route('/GetData',methods=['GET','POST'])
def GetData():
	'''
	receive_headers = str(request.headers)
	session_index = str(receive_headers).find('Session')
	'''
	session_index = request.args.get('a0')
	Paramid = request.args.get('a1')
	#debug("receive_headers:%s" % receive_headers)
	'''
	if session_index < 0:
		return ""
	else:
		end_index = receive_headers[session_index+9:].find('\n')
		Session = receive_headers[session_index+9:session_index+9+end_index]
		Paramid_index = str(receive_headers).find('Paramid')
		if Paramid_index < 0:
			return ""
		else:
			end_index = receive_headers[Paramid_index+9:].find('\n')
			Paramid = receive_headers[Paramid_index+9:Paramid_index+9+end_index]
	'''
	
	client_ip = request.remote_addr
	'''
	(error,usercode,mac) = SessionCheck(str(Session),client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	'''
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."PGetBatchStartParam"(%s)' % Paramid
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)

@host_grouping.route('/PGet_SshKey',methods=['GET','POST'])
def PGet_SshKey():

	se = request.form.get('a0')
	KeyName = request.form.get('z1')
	KeyContent = request.form.get('z2')	
	#keytype = request.form.get('z3')
	#ifvalid = request.form.get('z4')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetSshKey\"(E'%s',null,null,null,0,E'{\"KeyContent\":\"%s\",\"KeyName\":\"%s\"}')" % (usercode, KeyContent,KeyName)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
			
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@host_grouping.route('/Get_SshPrivateKey',methods=['GET','POST'])
def Get_SshPrivateKey():
	se = request.form.get('a0')
	KeyName = request.form.get('z1')
	HostIP = request.form.get('z2')	
	ProtocolName = request.form.get('z3')
	AccountName = request.form.get('z4')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if KeyName == "":
		KeyName = "null"
	else:
		KeyName = "E'%s'" % KeyName
	if ProtocolName == "":
		ProtocolName = "null"
	else:
		ProtocolName = "E'%s'" % ProtocolName
	if AccountName == "":
		AccountName = "null"
	else:
		AccountName = "E'%s'" % AccountName
	if HostIP == "":
		HostIP = "null"
	else:
		HostIP = "E'%s'" % HostIP
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"GetSshPrivateKey\"(E'%s',%s,%s,%s,%s)" % (usercode, KeyName,HostIP,ProtocolName,AccountName)
			curs.execute(sql)
			results = curs.fetchall()
			if results[0][0] == None:
				return "[]"
			results_json=json.loads(results[0][0].encode('utf-8'))
			index=0
                        for i in results_json:
					if index==0 and i['KeyName']=='托管配置':
                                                continue
                                        index+=1
                                        if i['Password']!=None:
                                                if os.path.exists('/usr/lib64/logproxy.so') == False:
                                                        return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
                                                lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
                                                pwd_rc4 = c_char_p()# 定义一个指针
                                                pwd_rc4.value = "0"*512 # 初始化 指针
                                                lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
                                                lib.decrypt_pwd.restype = None #定义函数返回值
                                                ret = lib.decrypt_pwd(i['Password'],pwd_rc4);#执行函数
                                                i['Password'] = pwd_rc4.value #获取变量的值
                                        try:
                                                key='SafeT1Ba5eSafeT1'
                                                des3=DES3.new(key,DES3.MODE_ECB)
                                                i['KeyContent']=base64.b64decode(i['KeyContent'])
                                                i['KeyContent']=des3.decrypt(i['KeyContent'])
                                                while True:
                                                        c=i['KeyContent'][-1]
                                                        if ord(c)==0:
                                                                i['KeyContent']=i['KeyContent'][:-1]
                                                        else:
                                                                break
                                        except Exception,e:
                                                pass
                        results=json.dumps(results_json)
			return results
			
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d)\"}" % (sys._getframe().f_lineno)

def delete_view(usercode):
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'SELECT a.table_name FROM  information_schema.tables a WHERE a.table_schema=\'public\' AND a.table_type=\'VIEW\' AND a.table_name like E\'%s%%\';' %(usercode)
			#debug(str(sql))
			curs.execute(sql)
			results = curs.fetchall()
			for res in results:
				time_tmp = int(res[0].split('_')[1])/1000			
				curr_time = int(time.time())
				#debug(str(time_tmp))
				#debug(str(curr_time))
				if curr_time - time_tmp > 24 * 60 * 60:
					sql = 'DROP view %s;' %(res[0])
					debug(sql)
					curs.execute(sql)		
			return results
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))		
		
###yt 20180913 全局检索
@host_grouping.route('/PFindHostForPageAccess',methods=['GET','POST'])
def PFindHostForPageAccess():
	session = request.form.get('a0')
	hgid = request.form.get('z1')
	ip = request.form.get('z2')
	service_str = request.form.get('z3')
	account_name = request.form.get('z4')
	accounttype = request.form.get('z5')
	search_str = request.form.get('z6')
	search_time = request.form.get('z7')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	##删除超过一天的检索视图
	
	delete_view(usercode);
	
	if ip == None:
		ip = "null"
	else:
		ip = "E'%s'" % ip
	if service_str == None:
		hostservicename = "null"
		proname = "null"
		port = "null"
		servicename = "null"
		conntype = "null"
		connparamvalue = "null"	
	else:
		service_obj = json.loads(service_str)
		if service_obj['HostServiceName'] == None:
			hostservicename = "null"
		else:
			hostservicename = "E'%s'" % service_obj['HostServiceName']
		proname = "E'%s'" % service_obj['ProtocolName']
		port = "E'%s'" % str(service_obj['Port'])
		if service_obj['ServiceName'] == None:
			servicename = "null"
		else:
			servicename = "E'%s'" % service_obj['ServiceName']
		if service_obj['ConnType'] == None:
			conntype = "null"
		else:
			conntype = "E'%s'" % str(service_obj['ConnType'])
		if service_obj['ConnParamValue'] == None:
			connparamvalue = "null"
		else:
			connparamvalue = "E'%s'" % service_obj['ConnParamValue']
	
	if account_name == None:
		account_name = "null"
	else:
		account_name = "E'%s'" % account_name

	if accounttype == None:
		accounttype = "null"
	else:
		accounttype = "E'%s'" % accounttype	

	if search_str == None:
		search_str = "null"
	else:
		search_obj = json.loads(search_str)
		if len(search_obj) == 0:
			search_str = "null"
		else:
			search_dic = {"HostIP":"","HostName":"","ProtocolName":"","searchstring":""}
			hname = ""
			hip = ""
			pname = ""
			search_s = ""
			for search in search_obj:
				data = search.split('-',1)
				debug(str(data[1]))
				data1 = data[1].split(' ');## 去除多余的空格
				data1tmp = [];
				for o in data1:
					if o != '':
						data1tmp.append(o);
				
				data[1] = ' '.join(data1tmp)
				debug(str(data[1]))
				if data[0] == "hname":
					hname = hname + data[1] + '\n'
				elif data[0] == "IP":
					hip = hip + data[1] + '\n'
				elif data[0] == "pname":#协议
					pname = pname + data[1] + '\n'
				else:
					search_s = search_s + data[1] + '\n' 
			
			if hname != "":
				hname = hname[:-1]
			if hip != "":
				hip = hip[:-1]
			if pname != "":
				pname = pname[:-1]
			if search_s != "":
				search_s = search_s[:-1]
			search_s = search_s.replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			search_dic['HostIP'] = hip
			search_dic['HostName'] = hname
			search_dic['ProtocolName'] = pname
			search_dic['searchstring'] = search_s
			search_dic['SearchTime'] = search_time
			search_dic['LoginUserCode'] = usercode
			search_dic['srcip'] = client_ip
			search_dic['srcmac'] = None
			search_dic['hgid'] = int(hgid)
			search_dic['Type'] = None
			
			search_dic = json.dumps(search_dic)
			search_str = MySQLdb.escape_string(search_dic).decode('utf-8')
			search_str = "E'%s'" % search_str
	try:
		'''
			{
				"LoginUserCode":,
				"SearchTime":,
				"srcip":,
				"srcmac":,
				"hgid":,
				"HostIP":,
				"HostName":,
				"ProtocolName":,
				"searchstring":,
				"Type":,   --1.工单申请，2-批量启动, 3-批量执行    	
			}
		'''
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"GetAuthObjectByLevel\"('%s','%s',null,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str))
			curs.execute("select public.\"PFindHostForPageAccess\"(%s);" %(search_str))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))		

		
###yt 20180913 获取全局检索信息
@host_grouping.route('/PGetHostForPageAccess',methods=['GET','POST'])
def PGetHostForPageAccess():
	session = request.form.get('a0')
	search_str = request.form.get('z6')
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
			
	search_obj = json.loads(search_str)
	search_obj['LoginUserCode'] = usercode;
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"GetAuthObjectByLevel\"('%s','%s',null,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str))
			sql = "select public.\"PGetHostForPageAccess\"(E'%s');" %(json.dumps(search_obj))
			debug(sql)
			curs.execute(sql)
			results_tmp = curs.fetchall()[0]
			if results_tmp[0] == None:
				results='[]'
			else:
				results = results_tmp[0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

#最近访问删除记录
@host_grouping.route('/delHost', methods=['GET', 'POST'])
def delHost():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ip_str = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(system_user,'设备访问') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if ip_str < 0:
		ip_str = ""
	ips = ip_str.split(',')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	for ip in ips:
		sql = "select public.\"PDeleteRecentAccessHost\"(E'%s',E'%s');" %(system_user,ip)
		# debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()
	return "{\"Result\":true}"

#最近访问删除记录（指定到账号）
@host_grouping.route('/delHostAccount', methods=['GET', 'POST'])
def delHostAccount():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ServerIP = request.form.get('a1')
	ProtocolName = request.form.get('a2')
	ServerName = request.form.get('a3')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if check_role(system_user,'设备访问') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	if checkip(ServerIP) and checkname(ProtocolName) and checkname(ServerName):
		pass
	else:
		if checkip(ServerIP) and checkaccount(ProtocolName) and ServerName == '*':
			pass
		else:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "delete from private.\"HostAccessCfg\" a where a.\"UserCode\"=E'%s' and a.\"ServerIP\"=E'%s' and a.\"ProtocolName\"=E'%s' and a.\"ServerUser\"=E'%s';" %(system_user,ServerIP,ProtocolName,ServerName)
	# debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()
	return "{\"Result\":true}"

#唯一登陆检测
@host_grouping.route('/DevChk', methods=['GET', 'POST'])
def DevChk():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ip = request.form.get('a1')
	proto = request.form.get('a2')
	if session < 0:
		session = ""
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
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select \"LoginUniqueIP\" from public.\"GlobalStrategy\" ;"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP= int(result[0][0])
	else:
		LoginUniqueIP = 0

	sql = "select \"LoginUniqueIP\" from public.\"User\" where \"UserCode\"=E'%s';" %(system_user)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP_user= int(result[0][0])
	else:
		LoginUniqueIP_user = 0

	if LoginUniqueIP_user == 1 or LoginUniqueIP == 1:
		LoginUniqueIPLimit = 1
	else:
		LoginUniqueIPLimit = 0

	try:
		if LoginUniqueIPLimit == 1:
			Chktype = 2
			ret = ClientCheck(system_user,client_ip,proto,None);
			if isinstance(ret,tuple)!= 0:
				retResult = str(ret[0]) + ',' + str(ret[1].replace("'",""))
				return "{\"Result\":true,\"info\":\"%s\",\"type\":\"%d\"}" %(retResult,Chktype)
			else:
				retResult = str(ret)
		Chktype = 1
		ret = ServerCheck(system_user,ip,proto,None)
		if ret[0] != 0:
			retResult = str(ret[0]) + ',' + str(ret[1].replace("'",""))
			return "{\"Result\":true,\"info\":\"%s\",\"type\":\"%d\"}" %(retResult,Chktype)
		else:
			retResult = str(ret[0])
			return "{\"Result\":true,\"info\":\"0\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)


def ipToBinary(ip):
	ip_num = ip.split('.')
	x = 0
	for i in range(len(ip_num)):
		num = int(ip_num[i]) << (24 - i*8)
		x = x | num
	brnary = str(bin(x).replace('0b',''))
	return brnary

def maskToBinary(mask):
	mask_list = str(mask).split('.')
	if len(mask_list) == 1:
		binary32 = []
		for i in range(32):
			binary32.append('0')
		for i in range(int(mask)):
			binary32[i] = '1'
		binary = ''.join(binary32)
	elif len(mask_list) == 4:
		binary = ipToBinary(mask)
	return binary

def ipInSubnet(ip1,ip2,network_mask):
	ip_num1 = int(ipToBinary(ip1),2)
	ip_num2 = int(ipToBinary(ip2),2)
	mask_bin = int(maskToBinary(network_mask),2)
	if (ip_num1 & mask_bin) == (ip_num2 & mask_bin):
		return True
	else:
		return False
def getIP(domain):
	myaddr = socket.getaddrinfo(domain, 'http')
	return myaddr[0][4][0]
#获取真正IP
@host_grouping.route('/RealIPGet', methods=['GET', 'POST'])
def RealIPGet():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ip_str = request.form.get('a1')
	if session < 0:
		session = ""
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
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	dev_type = common.get_server_cluster_type()
	server_id = common.get_server_id()
	sql = 'select a."ip_addr",a."mask_addr" from public."server_ipv4" a where a."server_id"=%d and a."status"!=2;' %(int(server_id))
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
        if len(result) == 0:
                return "{\"result\":true,\"info\":\"\",\"dev_type\":\"%s\"}" %(dev_type)
	if result:
		try:
			RealIP= result[0][0]
			network_mask= result[0][1]
			if ipInSubnet(getIP(ip_str),RealIP,network_mask) == True:
				return "{\"result\":true,\"info\":\"%s\",\"dev_type\":\"%s\"}" %(RealIP, dev_type)
			else:
				return "{\"result\":true,\"info\":\"\",\"dev_type\":\"%s\"}" %(dev_type)
		except pyodbc.Error,e:
			return "{\"result\":false,\"info\":\"\",\"dev_type\":\"%s\"}" %(dev_type)
	else:
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
