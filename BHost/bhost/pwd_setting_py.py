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
from htmlencode import parse_sess
from htmlencode import check_role
from logbase import common
from comm_function import get_user_perm_value

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from generating_log import system_log


env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
pwd_setting_py = Blueprint('pwd_setting_py',__name__)

SIZE_PAGE = 20
ErrorNum = 10000
def debug(c):
	return 0
        path = "/var/tmp/debugccp.txt"
        fp = open(path,"a+")
        if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values (E'%s',E'%s',E'%s',E'%s',E'%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	LogSet(None, sqlconf, 6)
	
#HTMLEncode 
def HTMLEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	
#页面跳转函数
@pwd_setting_py.route('/pwd_setting',methods=['GET','POST'])
def pwd_setting():
	debug('pwd_setting')
	#页面跳转函数
	#参数 tasktype = 创建-3 编辑-2 列表-1
	#<!-- a=id b=当前显示个数 c=第几页 -->
	reload(sys)
	sys.setdefaultencoding('utf-8')
	tasktype = request.form.get("tasktype")
	page = request.form.get("c")
	se=request.form.get('se')
	if page < 0 or page == None:
		page = "1"
	id = 0
	if tasktype < 0 or tasktype == None:
		tasktype = "1"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	t = "hostpwd_ot_pwd.html"
	perm=0
	for i in perm_json:
		if i['SubMenuId']==30 and i['SystemMenuId']==4:
			t = "pwd_setting_list.html"
			perm=i['Mode']
			break
	return render_template(t,tasktype=tasktype,a=id,c=page,se=se,perm=perm)

#页面跳转函数
@pwd_setting_py.route('/hostpwd_showing',methods=['GET','POST'])
def hostpwd_showing():
	#页面跳转函数
	se = request.form.get("se")
	t = "hostpwd_ot_pwd.html"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm=json.loads(perm)
	n=0
	perm_1=1
	for i in perm:
		if i['SubMenuId']==30 and i['SystemMenuId']==4:
			n=i['Mode']
		elif i['SubMenuId']==24 and i['SystemMenuId']==6 and perm_1<i['Mode']:
                        perm_1=i['Mode']
	return render_template(t,se=se,perm=n,perm_1=perm_1)

#页面跳转函数
@pwd_setting_py.route('/hostsend_showing',methods=['GET','POST'])
def hostsend_showing():
	#页面跳转函数
	se = request.form.get("se")
	t = "hostpwd_ot_send.html"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm=json.loads(perm)
	n=0
	perm_1=1
	for i in perm:
		if i['SubMenuId']==30 and i['SystemMenuId']==4:
			n=i['Mode']
		elif i['SubMenuId']==24 and i['SystemMenuId']==6 and perm_1<i['Mode']:
			perm_1=i['Mode']

	return render_template(t,se=se,perm=n,perm_1=perm_1)

#主机列表
@pwd_setting_py.route('/get_pwd_setting_list',methods=['GET','POST'])
def get_pwd_setting_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	if sess<0 or sess==None:
		sess=''
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	id=request.form.get('a1')
	if id<0 or id==None:
		id='null'
	elif id!='null':
		id="'%s'"%id
	search_typeall=request.form.get('a2')
	if search_typeall<0 or search_typeall==None:
		search_typeall=''
	paging=request.form.get('a3')
	if paging<0 or paging==None:
		paging='null'
	else:
		paging=int(paging)
	num=request.form.get('a4')
	if num<0 or num==None:
		num='null'
	else:
		num=int(num)
	nodetails=request.form.get('a5')
	if nodetails<0 or nodetails==None:
		nodetails='true'
	hostip=''
	hostname=''
	searchstring=''
	DeviceTypeName=''
	Name=''
	typeall = search_typeall.split('\t')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="hostip":
			hostip=hostip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="hostname":
			hostname=hostname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="DeviceTypeName":
			DeviceTypeName=DeviceTypeName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if hostip=="":
		hostip="null"
	else:
		hostip="E'%s'"%(hostip[:-1])
	if searchstring!="":
		searchstring=searchstring[:-1]
	if DeviceTypeName!="":
		DeviceTypeName=DeviceTypeName[:-1]
	if Name!="":
		Name=Name[:-1]
	searchconn={}
	searchconn['searchstring']=searchstring
	searchconn['Name']=Name
	searchconn['DeviceTypeName']=DeviceTypeName
	searchconn['LoginUserCode']=system_user
	searchconn=json.dumps(searchconn)
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	hostip=hostip.replace("\\\\","\\\\\\\\")
	hostip=hostip.replace(".","\\\\.")
	hostip=hostip.replace("?","\\\\?")
	hostip=hostip.replace("+","\\\\+")
	hostip=hostip.replace("(","\\\\(")
	hostip=hostip.replace("*","\\\\*")
	hostip=hostip.replace("[","\\\\[")
	if hostname=="":
		hostname="null"
	else:
		hostname="E'%s'"%(hostname[:-1])
	hostname=hostname.replace("\\\\","\\\\\\\\")
	hostname=hostname.replace(".","\\\\.")
	hostname=hostname.replace("?","\\\\?")
	hostname=hostname.replace("+","\\\\+")
	hostname=hostname.replace("(","\\\\(")
	hostname=hostname.replace("*","\\\\*")
	hostname=hostname.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetHostPwdModConfig\"(%s,%s,%s,%s,%s,%s,E'%s');"%(id,hostip,hostname,nodetails,num,paging,searchconn)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#获取用户详细信息
@pwd_setting_py.route('/get_user_all_admin',methods=['GET','POST'])
def get_user_all_admin():
	'''
	SELECT jsonb_pretty(array_to_json(array_agg(row_to_json(r)))::jsonb) FROM(
			SELECT adminu."UserId",adminu."UserCode"
			FROM "User" u
			JOIN "UserAdmin" ua on ua."UserId"=u."UserId"
			JOIN	"User" adminu on adminu."UserId"=ua."AdminId"
			WHERE u."UserCode"='ccp'
			UNION
			SELECT u."UserId",u."UserCode"
			FROM "User" u
			WHERE u."UserCode"='ccp'
	) as r
	'''
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	type_name=request.form.get('a1')
	if type_name<0:
		type_name=''
	if sess<0 or sess==None:
		sess=''
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			if type_name!='':
				sql='select public."PGetUser"(null,4,null);'
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				if results==None:
					result_json=[]
				else:
					result_json=json.loads(results)
			else:
				sql='select public."PGetUser"(null,4,\'%s\');'%(system_user)
				debug(sql)
				curs.execute(sql)
				results = curs.fetchall()[0][0]
				if results==None:
					result_json=[]
				else:
					result_json=json.loads(results)
			results=json.dumps(result_json)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#保存
@pwd_setting_py.route('/save_pwd_setting_item',methods=['GET','POST'])
def save_pwd_setting_item():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	if sess<0 or sess==None:
		sess=''
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	json_data=request.form.get('a1')
	md5_str = request.form.get('m1')
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(json_data);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(system_user,'主机设定') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	json_data=str(json_data)
	json_data_js=json.loads(json_data)
	json_data_js["LoginUserCode"]=system_user
	json_data=json.dumps(json_data_js)
	sql="select public.\"PSaveHostPwdModConfig\"(E'%s');" %(MySQLdb.escape_string(json_data).decode("utf-8"))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if not result_json['Result']:
				oper='编辑[%s-%s]主机的改密配置'%(json_data_js['HostName'],json_data_js['HostIP'])
				if not system_log(system_user,oper,result_json['ErrMsg'],'密码管理>主机设定'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			if json_data_js["Name"]==None:
				json_data_js["Name"]='跟随设备类型'
				oper='编辑[%s-%s]主机的改密配置（设备类型：%s，改密方式：跟随设备类型'%(json_data_js['HostName'],json_data_js['HostIP'],json_data_js['DeviceTypeName'])
			else:
				oper='编辑[%s-%s]主机的改密配置（设备类型：%s，改密方式：自定义，改密模式：%s'%(json_data_js['HostName'],json_data_js['HostIP'],json_data_js['DeviceTypeName'],json_data_js["Name"])
			acc_pwdconfig=''
			for i in json_data_js['AcctPwdModConfigSet']:
				acc_pwdconfig+=('%s[%s](改密模式：%s)、'%(i['AccountName'],i['ProtocolName'],i['Name']))
			if acc_pwdconfig!='':
				acc_pwdconfig=acc_pwdconfig[:-1]
				oper+=('，账号：%s）'%acc_pwdconfig)
			if not system_log(system_user,oper,'成功','密码管理>主机设定'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			conn.commit()
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
