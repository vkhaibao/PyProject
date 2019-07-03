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
connection_list = Blueprint('connection_list',__name__)

SIZE_PAGE = 20
def debug(c):
	return 0
        path = "/var/tmp/debug_ccp_connection.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
	
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
@connection_list.route('/connection_handle',methods=['GET','POST'])
def connection_handle():
	tasktype = request.form.get("tasktype")
	conn_d = request.form.get("conn_d")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	
	
	
	se = request.form.get("se")
	if tasktype < 0:
		tasktype = "1"
	if e < 0 or e==None:
		e = ":"
	
	
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
	if tasktype and str(tasktype).isdigit() == False:
		return '',403		
	if conn_d and str(conn_d).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
		
		
	if se < 0:
		se = request.args.get('se')
		if se<0:
			se=''
	if search_typeall < 0 or search_typeall==None:
		search_typeall = ""
	search_typeall = search_typeall.replace('(','').replace(')','');
	e = e.replace('(','').replace(')','');
	
	if tasktype == "1" or tasktype == "2":
		t = "connection_add.html"
	if tasktype == "3":
		t = "connection_list.html"
		conn_d="0"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==14 and i['SystemMenuId']==3:
			# perm=2
			perm=i['Mode']
			break
	return render_template(t,se=se,tasktype=tasktype,conn_d=conn_d,paging=paging,search_typeall=search_typeall,e=e,perm=perm)
#跳转至连接参数
@connection_list.route('/connection_show',methods=['GET', 'POST'])
def connection_show():		
	sess = request.form.get('se')
	if sess < 0:
		sess = request.args.get('se')
		if sess<0:
			sess=''
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
	return render_template('connection_list.html',se=sess,paging="1",search_typeall='',e=':',perm=perm)

#创建 or 编辑
@connection_list.route('/add_connection',methods=['GET','POST'])
def add_connection():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	connection = request.form.get('a1')
	if sess<0:
		sess=""
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>连接参数'
		
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
		
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(connection);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	connection=str(connection)
	connection_json=json.loads(connection)
	# PSaveConnParam(connection)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PSaveConnParam\"(E'%s');" %(MySQLdb.escape_string(connection).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if connection_json['ConnParamId']==0 or connection_json['ConnParamId']==None:
				oper='创建连接参数：'+connection_json['ConnParamName']
			else:
				oper='编辑连接参数：'+connection_json['ConnParamName']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result 
			else:
				oper+='（'
				# <option value="1" text="RDP">RDP</option>
				if connection_json['ProtocolId']==1:
					oper+='协议：RDP，访问方式：%s）'%(connection_json['ConnType'])
				# <option value="2" text="SSH">SSH</option>
				if connection_json['ProtocolId']==2:
					oper+='协议：SSH，版本号：%s）'%(connection_json['ServiceName'])
				if connection_json['ProtocolId']==3:
					oper+='协议：SFTP，版本号：%s）'%(connection_json['ServiceName'])
				# <option value="3" text="ORACLE">ORACLE</option>
				if connection_json['ProtocolId']==4:
					if connection_json['ConnType']==None:
						connection_json['ConnType']='未指定'
					oper+='协议：ORACLE，指定：%s，实例名或服务名：%s，连接方式：%s）'%(connection_json['ConnParamValue'],connection_json['ServiceName'],connection_json['ConnType'])
				# <option value="4" text="MSSQL">MSSQL</option>
				if connection_json['ProtocolId']==5:
					if connection_json['ConnType']==None:
						connection_json['ConnType']='未指定'
					oper+='协议：MSSQL，实例名：%s，认证方式：%s）'%(connection_json['ServiceName'],connection_json['ConnType'])
				# <option value="5" text="MYSQL">MYSQL</option>
				if connection_json['ProtocolId']==6:
					if connection_json['ConnType']==0:
						connection_json['ConnType']='<7.5'
					else:
						connection_json['ConnType']='≥7.5'
					oper+='协议：MYSQL，数据库名：%s）'%(connection_json['ServiceName'])
				# <option value="6" text="HTTP">HTTP</option>
				if connection_json['ProtocolId']==7:
					oper_arr=[]
					oper_arr.extend(['协议：HTTP','URL：%s'%connection_json['ServiceName']])
					index=connection_json['ConnParamValue'].find('|')
					if connection_json['ConnParamValue'][:index]!='':
						oper_arr.append('账号元素：%s'%connection_json['ConnParamValue'][:index])
					connection_json['ConnParamValue']=connection_json['ConnParamValue'][index+1:]
					index=connection_json['ConnParamValue'].find('|')
					if connection_json['ConnParamValue'][:index]!='':
						oper_arr.append('密码元素：%s'%connection_json['ConnParamValue'][:index])
					if connection_json['ConnParamValue'][index+1:]!='':
						oper_arr.append('提交元素：%s'%connection_json['ConnParamValue'][index+1:])
					oper+=('，'.join(oper_arr)+'）')
				# <option value="7" text="HTTPS">HTTPS</option>
				if connection_json['ProtocolId']==8:
					oper_arr=[]
					oper_arr.extend(['协议：HTTPS','URL：%s'%connection_json['ServiceName']])
					index=connection_json['ConnParamValue'].find('|')
					if connection_json['ConnParamValue'][:index]!='':
						oper_arr.append('账号元素：%s'%connection_json['ConnParamValue'][:index])
					connection_json['ConnParamValue']=connection_json['ConnParamValue'][index+1:]
					index=connection_json['ConnParamValue'].find('|')
					if connection_json['ConnParamValue'][:index]!='':
						oper_arr.append('密码元素：%s'%connection_json['ConnParamValue'][:index])
					if connection_json['ConnParamValue'][index+1:]!='':
						oper_arr.append('提交元素：%s'%connection_json['ConnParamValue'][index+1:])
					oper+=('，'.join(oper_arr)+'）')
				# <option value="8" text="TELNET">TELNET</option>
				if connection_json['ProtocolId']==9:
					oper+='协议：TELNET）'
				# <option value="9" text="FTP">FTP</option>
				if connection_json['ProtocolId']==10:
					oper+='协议：FTP）'
				# <option value="10" text="VNC">VNC</option>
				if connection_json['ProtocolId']==11:
					oper+='协议：VNC）'
				# <option value="11" text="X11">X11</option>
				if connection_json['ProtocolId']==12:
					oper+='协议：X11）'
				# <option value="12" text="RADMIN">RADMIN</option>
				if connection_json['ProtocolId']==13:
					if connection_json['ConnType']==None:
						connection_json['ConnType']='未指定'
					oper+='协议：RADMIN，认证方式：%s）'%connection_json['ConnType']
				# <option value="13" text="SYBASE">SYBASE</option>
				if connection_json['ProtocolId']==14:
					oper+='协议：SYBASE，实例名：%s）'%connection_json['ServiceName']
				# <option value="14" text="DB2">DB2</option>
				if connection_json['ProtocolId']==15:
					oper+='协议：DB2，数据库名：%s）'%connection_json['ServiceName']
				# <option value="15" text="RLOGIN">RLOGIN</option>
				if connection_json['ProtocolId']==16:
					oper+='协议：RLOGIN）'
				# <option value="16" text="PCANY">PCANY</option>
				if connection_json['ProtocolId']==17:
					oper+='协议：PCANY）'
				# <option value="17" text="TN5250">TN5250</option>
				if connection_json['ProtocolId']==18:
					oper+='协议：TN5250）'
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
				return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#id位置
@connection_list.route('/PGetRecordRownum',methods=['GET','POST'])
def PGetRecordRownum():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	recordid = request.form.get('a1')
	tableid = request.form.get('a2')
	pwdmodtype= request.form.get('a3')
	if sess<0:
		sess=""
	if pwdmodtype<0:
		pwdmodtype="null"
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
	if pwdmodtype<0:
		sql="select public.\"PGetRecordRownum\"(%s,%s);" %(recordid,tableid)
	elif tableid=='17' or tableid=='31' or tableid=='8' or tableid=='33' or tableid=='34' or tableid=='36':
		sql="select public.\"PGetRecordRownum\"(%s,%s,%s,'%s');" %(recordid,tableid,pwdmodtype,system_user)
	else:
		sql="select public.\"PGetRecordRownum\"(%s,%s,%s);" %(recordid,tableid,pwdmodtype)
	
	# PSaveConnParam(connection)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			curs.execute(sql)
			debug(str(sql))
			result = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%d}" %(result)
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示连接参数 or 分页 or 搜索
@connection_list.route('/get_connection_list',methods=['GET', 'POST'])
def get_connection_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	id = request.form.get('a5')
	connparamid = request.form.get('a1')
	
	if id<0 or id=="" or id=="0":
		protocolid="null"
	if connparamid<0 or connparamid=="" or connparamid=="0":
		connparamid="null"
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
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
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
	connparamname = ""
	protocolname = ""
	servicename = ""
	searchstring=''
	ConnType=''
	ConnParamValue=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="ConnParamName":
			connparamname=connparamname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ServiceName":
			servicename=servicename+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ProtocolName":
			protocolname=protocolname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ConnType":
			ConnType=ConnType+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ConnParamValue":
			ConnParamValue=ConnParamValue+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if connparamname=="":
		connparamname="null"
	else:
		connparamname="E'%s'"%connparamname[:-1]
	if servicename=="":
		servicename="null"
	else:
		servicename="E'%s'"%servicename[:-1]
	if protocolname=="":
		protocolname="null"
	else:
		protocolname="E'%s'"%protocolname[:-1]
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	if ConnType=="":
		ConnType=""
	else:
		ConnType=ConnType[:-1]
	if ConnParamValue=="":
		ConnParamValue=""
	else:
		ConnParamValue=ConnParamValue[:-1]
	searchconn['searchstring']=searchstring
	searchconn['ConnType']=ConnType
	searchconn['ConnParamValue']=ConnParamValue
	searchconn=json.dumps(searchconn)
	protocolname=protocolname.replace("\\","\\\\")
	protocolname=protocolname.replace(".","\\\\.")
	protocolname=protocolname.replace("?","\\\\?")
	protocolname=protocolname.replace("+","\\\\+")
	protocolname=protocolname.replace("(","\\\\(")
	protocolname=protocolname.replace("*","\\\\*")
	protocolname=protocolname.replace("[","\\\\[")
	servicename=servicename.replace("\\","\\\\")
	servicename=servicename.replace(".","\\\\.")
	servicename=servicename.replace("?","\\\\?")
	servicename=servicename.replace("+","\\\\+")
	servicename=servicename.replace("(","\\\\(")
	servicename=servicename.replace("*","\\\\*")
	servicename=servicename.replace("[","\\\\[")
	connparamname=connparamname.replace("\\","\\\\")
	connparamname=connparamname.replace(".","\\\\.")
	connparamname=connparamname.replace("?","\\\\?")
	connparamname=connparamname.replace("+","\\\\+")
	connparamname=connparamname.replace("(","\\\\(")
	connparamname=connparamname.replace("*","\\\\*")
	connparamname=connparamname.replace("[","\\\\[")
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetConnParam(protocolid,connparamid,connparamname,protocolname,servicename,limitrow,offsetrow) 
			sql="select public.\"PGetConnParam\"(%s,%s,%s,%s,%s,%s,%s,E'%s',%s);"% (protocolid,connparamid,connparamname,protocolname,servicename,num,paging,searchconn,dsc)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除连接参数
@connection_list.route('/del_connection',methods=['GET', 'POST'])
def del_connection():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>连接参数'
	if session <0 :
		sesson=""
	if id_str <0 :
		id_str=""
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
		
	if check_role(system_user,'主机管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			success_arr=[]
			fail_num=0
			fail_arr=[]
			all_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				all_arr.append(id_arr[1])
				id_value=int(id_arr[0])
				# PDeleteConnParam(id)
				sql = "select public.\"PDeleteConnParam\"(%d);" % (id_value)
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
			oper='删除连接参数：%s'%('、'.join(all_arr))
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
			return "{\"Result\":true,\"info\":\"\",\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}"%(success_num,fail_num,mesg)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#检查连接参数重名
@connection_list.route('/CheckConnName',methods=['GET', 'POST'])
def CheckConnName():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	name_str = request.form.get('a1')
	session = request.form.get('a0')
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PGetConnParamByName\"(E'%s');" % (name_str)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			return "{\"Result\":true,\"Id\":\"%d\"}"%(result)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
