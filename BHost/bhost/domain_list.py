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
from comm_function import get_user_perm_value
from generating_log import system_log

from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
domain_list = Blueprint('domain_list',__name__)

SIZE_PAGE = 20
def debug(c):
    return 0
    return 0
    path = "/var/tmp/debugdomain.txt"
    fp = open(path,"a+")
    if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
# def sendlog(oper,desc,cname):
	# client_ip = request.remote_addr    #获取客户端IP
	# happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	# sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	# LogSet(None, sqlconf, 6)
	
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
#1创建 2编辑 3列表
@domain_list.route('/domain_handle',methods=['GET','POST'])
def domain_handle():
	sess = request.form.get('se')
	if sess < 0:
		sess=request.args.get('se')
		if sess<0:
			sess = ""
	tasktype = request.form.get("tasktype")
	DomainId = request.form.get("DomainId")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	
	
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or tasktype == "2":
		t = "domain_add.html"
	if tasktype == "3":
		t = "domain_list.html"
		DomainId="0"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==14 and i['SystemMenuId']==3:
			# perm=2
			perm=i['Mode']
			break
			
	if e < 0 or e==None:
		e = ":"
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
	if tasktype and str(tasktype).isdigit() == False:
		return '',403		
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	search_typeall = search_typeall.replace('(','').replace(')','');
	e = e.replace('(','').replace(')','');
	return render_template(t,tasktype=tasktype,se=sess,DomainId=DomainId,paging=paging,search_typeall=search_typeall,e=e,perm=perm)
#跳转至AD域
@domain_list.route('/domain_show',methods=['GET', 'POST'])
def domain_show():		
	sess = request.form.get('se')
	if sess < 0:
		sess=request.args.get('se')
		if sess<0:
			sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==14 and i['SystemMenuId']==3:
			# perm=2
			perm=i['Mode']
			break
	return render_template('domain_list.html',se=sess,paging="1",search_typeall="",e=':',perm=perm)
#显示 or 分页 or 搜索
@domain_list.route('/get_domain_list',methods=['GET', 'POST'])
def get_domain_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	DomainId = request.form.get('a1')
	dsc = request.form.get('dsc')
	
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if DomainId and str(DomainId).isdigit() == False:
		return '',403
	if dsc and dsc != 'false' and dsc!='true':
		return '',403
	if num and str(num).isdigit() == False:
		return '',403
		
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
	DomainName = ""
	ServerIP = ""
	searchstring=''
	if DomainId<0 or DomainId=="" or DomainId=="0":
		DomainId="null"
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
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
	
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="DomainName":
			DomainName=DomainName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ServerIP":
			ServerIP=ServerIP+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	searchconn['searchstring']=searchstring
	searchconn=json.dumps(searchconn)
	if ServerIP=="":
		ServerIP="null"
	else:
		ServerIP="E'%s'"%ServerIP[:-1]
	if DomainName=="":
		DomainName="null"
	else:
		DomainName="E'%s'"%DomainName[:-1]
	DomainName=DomainName.replace("\\","\\\\")
	DomainName=DomainName.replace(".","\\\\.")
	DomainName=DomainName.replace("?","\\\\?")
	DomainName=DomainName.replace("+","\\\\+")
	DomainName=DomainName.replace("(","\\\\(")
	DomainName=DomainName.replace("*","\\\\*")
	DomainName=DomainName.replace("[","\\\\[")
	ServerIP=ServerIP.replace("\\","\\\\")
	ServerIP=ServerIP.replace(".","\\\\.")
	ServerIP=ServerIP.replace("?","\\\\?")
	ServerIP=ServerIP.replace("+","\\\\+")
	ServerIP=ServerIP.replace("(","\\\\(")
	ServerIP=ServerIP.replace("*","\\\\*")
	ServerIP=ServerIP.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
			sql="select public.\"PGetDomain\"(%s,%s,%s,%s,%s,E'%s',%s);"% (DomainId,DomainName,ServerIP,num,paging,searchconn,dsc)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#创建主机域		
@domain_list.route('/add_domain',methods=['GET','POST'])
def add_domain():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	domain=request.form.get('a1')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>AD域'
	jsondata={}
	if session<0:
		session=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	domain=str(domain)
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(domain);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	domain_json=json.loads(domain)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveDomain(jsondata)
			sql="select public.\"PSaveDomain\"(E'%s');" %(MySQLdb.escape_string(domain).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if str(domain_json['DomainId'])=='0':
				oper='创建AD域：%s'%domain_json['DomainName']
			else:
				oper='编辑AD域：%s'%domain_json['DomainName']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result  
			else:
				ip_arr=domain_json['ServerIP'].split(';')
				oper+=('（服务器IP：'+'、'.join(ip_arr)+'）')
				conn.commit()
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除主机域
@domain_list.route('/del_domain',methods=['GET', 'POST'])
def del_domain():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	module_name= request.form.get('a10')
	if session<0:
		session=""
	if id_str<0:
		id_str=""
	if module_name<0:
		module_name='运维管理>AD域'
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	if check_role(system_user,"主机管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			all_arr=[]
			success_arr=[]
			fail_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				all_arr.append(id_arr[1])
				sql = "select public.\"PDeleteDomain\"(%d);" % (int(id_arr[0]))
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if result_json['Result']:
					conn.commit()
					success_num+=1
					success_arr.append(id_arr[1])
				else:
					fail_num+=1
					fail_arr.append(id_arr[1])
			oper='删除AD域：%s'%('、'.join(all_arr))
			if (success_num+fail_num)==1:
				if success_num==1:
					mesg='成功'
				else:
					mesg=result_json['ErrMsg']
			else:
				if fail_num==0:
					mesg='成功'
					# mesg='成功：%s'%('、'.join(success_arr))
				elif success_num!=0:
					mesg='成功：%s，失败：%s'%('、'.join(success_arr),'、'.join(fail_arr))
				else:
					mesg='失败：%s'%('、'.join(fail_arr))
			if not system_log(system_user,oper,mesg,module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}"%(success_num,fail_num,mesg) 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
