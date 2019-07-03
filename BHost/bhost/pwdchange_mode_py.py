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
from generating_log import system_log

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
pwdchange_mode_py = Blueprint('pwdchange_mode_py',__name__)

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
#保存
@pwdchange_mode_py.route('/save_pwdchange_mode_item',methods=['GET','POST'])
def save_pwdchange_mode_item():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess=request.form.get('a0')
	type_name=request.form.get('a2')
	json_str=request.form.get('a3')
	json_str=json.loads(json_str)
	if type_name=='del':
		type_name='删除'
		oper='%s改密配置：%s'%(type_name,json_str['Name'])
	else:
		if type_name=='add':
			type_name='创建'
		else:
			type_name='编辑'
		if json_str['Type']==1:
			json_str['Type']='默认'
			oper='%s改密配置：%s（改密脚本：%s，参数：%s）'%(type_name,json_str['Name'],json_str['Type'],json_str['Config'])
		else:
			json_str['Type']='自定义'
			oper='%s改密配置：%s（改密脚本：%s，内容：%s）'%(type_name,json_str['Name'],json_str['Type'],json_str['Config'])
		
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
	sql="select public.\"PSavePwdModConfig\"(E'%s');" %(MySQLdb.escape_string(json_data).decode("utf-8"))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if 'false' in result:
				if not system_log(system_user,'%s改密配置：%s'%(type_name,json_str['Name']),'登录用户不存在','密码管理>主机设定'):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			if not system_log(system_user,oper,'成功','密码管理>主机设定'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			conn.commit()
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#列表
@pwdchange_mode_py.route('/get_pwdchange_mode_list',methods=['GET','POST'])
def get_pwdchange_mode_list():
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
	if id<0 or id==None or id=='0':
		id='null'
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
	devicetypename=''
	typeall = search_typeall.split('\t')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="devicetypename":
			devicetypename=devicetypename+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if devicetypename=="":
		devicetypename="null"
	else:
		devicetypename="E'%s'"%(devicetypename[:-1])
	devicetypename=devicetypename.replace("\\\\","\\\\\\\\")
	devicetypename=devicetypename.replace(".","\\\\.")
	devicetypename=devicetypename.replace("?","\\\\?")
	devicetypename=devicetypename.replace("+","\\\\+")
	devicetypename=devicetypename.replace("(","\\\\(")
	devicetypename=devicetypename.replace("*","\\\\*")
	devicetypename=devicetypename.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPwdModConfig\"(%s,%s,%s,%s);"%(id,devicetypename,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#页面跳转函数
@pwdchange_mode_py.route('/pwdchange_mode',methods=['GET','POST'])
def pwdchange_mode():
	#页面跳转函数
	#参数 tasktype = 创建-3 编辑-2 列表-1
	#<!-- a=id b=当前显示个数 c=第几页 -->
	tasktype = request.form.get("tasktype")
	page = request.form.get("c")
	search = request.form.get("d")
	search2 = request.form.get("e")
	# se=request.form.get('se')
	if page < 0 or page == None:
		page = "1"
	if search < 0 or search == None:
		search = ""
	if search2 < 0 or search2 == None:
		search2 = ""
	id = 0
	if tasktype < 0 or tasktype == None:
		tasktype = "1"
	if tasktype == "1":
		t = "pwdchange_mode_list.html"
	elif tasktype=="3":
		t = "pwdchange_mode_add.html"
	elif tasktype=="2":
		id = request.form.get("a")
		if id < 0 or id == None:
			id = "0"
		t = "pwdchange_mode_add.html"
	return render_template(t,tasktype=tasktype,a=id,c=page,d=search,e=search2)

