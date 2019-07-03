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
import datetime

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from comm import *
from logbase import common
from urllib import unquote
from comm_function import get_user_perm_value
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from logbase import common
from logbase import defines
from logbase import task_client
from ctypes import *
import base64
import csv
import re
import codecs
from werkzeug.utils import secure_filename

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
authtype_list = Blueprint('authtype_list',__name__)

SIZE_PAGE = 20
def debug(c):
	return 0
        path = "/var/tmp/debugauthtype_list.txt"
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
	newStr = "";
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr
#1创建 2编辑 3列表
@authtype_list.route('/authtype_handle',methods=['GET','POST'])
def authtype_handle():
	is_user = 0;
	if request.method == "GET":
		tasktype = request.args.get("tasktype")
		authtypeId = request.args.get("authtypeId")
		paging = request.args.get("paging")
		search_typeall = request.args.get("search_typeall")
		e = request.args.get("e")
		se = request.args.get("se")
		is_user = request.args.get("i1")
	else:
		tasktype = request.form.get("tasktype")
		authtypeId = request.form.get("authtypeId")
		paging = request.form.get("paging")
		search_typeall = request.form.get("search_typeall")
		e = request.form.get("e")
		se = request.form.get("se")
	
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if authtypeId and str(authtypeId).isdigit() == False:
		return '',403
	if	(len(e) > 0 and e.find('-') < 0 and e.find(':') < 0):
		return '',403
	e = e.replace('(','').replace(')','');
	if is_user and str(is_user).isdigit() == False:
		return '',403
		
	if e < 0:
		e = ""
	if se<0:
		se=request.args.get('se')
		if se<0:
			se = ""
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or  tasktype == "2":
		t = "authtype_add.html"
	if tasktype == "3":
		t = "authtype_list.html"
		authtypeId="0"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==33 and i['SystemMenuId']==3:
			# perm=2
			perm=i['Mode']
			break
	return render_template(t,tasktype=tasktype,se=se,perm=perm,authtypeId=authtypeId,paging=paging,search_typeall=search_typeall,e=e,is_user=is_user)
	
#
@authtype_list.route('/authtype_module',methods=['GET','POST'])
def authtype_module():
	if request.method == "GET":
		se = request.args.get("se")
	else:
		se = request.form.get("se")
		
	t = "authtype_module.html"
	
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==33 and i['SystemMenuId']==3:
			# perm=2
			perm=i['Mode']
			break
	return render_template(t,se=se,perm=perm)
	
#跳转至认证方式
@authtype_list.route('/authtype_show',methods=['GET','POST'])
def authtype_show():
	sess = request.form.get('se')
	if sess<0:
		sess=request.args.get('se')
		if sess<0:
			sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==33 and i['SystemMenuId']==3:
			# perm=2
			perm=i['Mode']
			break
	return render_template('authtype_list.html',se=sess,paging="1",search_typeall="",e='',perm=perm)	
#显示 or 分页 or 搜索
@authtype_list.route('/get_authtype_list',methods=['GET', 'POST'])
def get_authtype_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	noset = request.form.get('a5')
	authtypeId = request.form.get('a1')
	isdefault=request.form.get('a6')
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
	if num and str(num).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if authtypeId and str(authtypeId).isdigit() == False:
		return '',403
	if dsc and dsc != 'false' and dsc!='true':
		return '',403
	if noset and noset != 'false' and noset!='true':
		return '',403
	if isdefault and isdefault != 'false' and  isdefault!='true':
		return '',403
		
	if isdefault<0 :
		isdefault="null"
	if noset<0 or noset=="":
		noset="false"
	if authtypeId<0 or authtypeId=="" or authtypeId=="0":
		authtypeId="null"
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
	MustAllModulesSucc=''
	AuthTypeName = ""
	AuthModuleName = ""
	searchstring=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="AuthTypeName":
			AuthTypeName=AuthTypeName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="AuthModuleName":
			AuthModuleName=AuthModuleName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="MustAllModulesSucc":
			MustAllModulesSucc=MustAllModulesSucc+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if AuthTypeName=="":
		AuthTypeName="null"
	else:
		AuthTypeName="E'%s'"%(AuthTypeName[:-1])
	if AuthModuleName=="":
		AuthModuleName="null"
	else:
		AuthModuleName="E'%s'"%(AuthModuleName[:-1])
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	if MustAllModulesSucc=="":
		MustAllModulesSucc=None
	else:
		MustAllModulesSucc=MustAllModulesSucc[:-1]
		if MustAllModulesSucc=='全部通过':
			MustAllModulesSucc=True
		elif MustAllModulesSucc=='任一通过':
			MustAllModulesSucc=False
		elif MustAllModulesSucc=='所有':
			MustAllModulesSucc=None
	searchconn['searchstring']=searchstring
	searchconn['MustAllModulesSucc']=MustAllModulesSucc
	searchconn=json.dumps(searchconn)
	AuthTypeName=AuthTypeName.replace("\\\\","\\\\\\\\")
	AuthTypeName=AuthTypeName.replace(".","\\\\.")
	AuthTypeName=AuthTypeName.replace("?","\\\\?")
	AuthTypeName=AuthTypeName.replace("+","\\\\+")
	AuthTypeName=AuthTypeName.replace("(","\\\\(")
	AuthTypeName=AuthTypeName.replace("*","\\\\*")
	AuthTypeName=AuthTypeName.replace("[","\\\\[")
	AuthModuleName=AuthModuleName.replace("\\\\","\\\\\\\\")
	AuthModuleName=AuthModuleName.replace(".","\\\\.")
	AuthModuleName=AuthModuleName.replace("?","\\\\?")
	AuthModuleName=AuthModuleName.replace("+","\\\\+")
	AuthModuleName=AuthModuleName.replace("(","\\\\(")
	AuthModuleName=AuthModuleName.replace("*","\\\\*")
	AuthModuleName=AuthModuleName.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	# PGetAuthType(authtypeId,noset,AuthTypeName,authmodulename,isdefault,limitrow,offsetrow)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetAuthType\"(%s,%s,%s,%s,%s,%s,%s,E'%s',%s);"%(authtypeId,noset,AuthTypeName,AuthModuleName,isdefault,num,paging,searchconn,dsc)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			
			result_json = json.loads(results)
			for dat in result_json['data']:
				for s in dat['Set']:
					sql = "select \"AuthMode\" from public.\"AuthModule\" where \"AuthModuleId\"=%d;" %(s['AuthModuleId'])
					debug(sql)
					curs.execute(sql)
					s['AuthMode'] = curs.fetchall()[0][0]
			results = json.dumps(result_json)		
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#获取主机组
@authtype_list.route('/get_usergroup',methods=['GET','POST'])
def get_hostgroup():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	if session < 0:
		session = ""
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
			debug('--------------------')
			sql='SELECT jsonb_pretty(array_to_json(array_agg(row_to_json(r)))::jsonb) FROM(\n\
WITH RECURSIVE subgroup("Id", "Name", "Path", "Parent") AS \n\
(	SELECT g."UGId", g."UGName", CAST(E\'/\'||g."UGName" AS VARCHAR), g."ParentUGId"\n\
			FROM "UGroup" g \n\
			JOIN "UGroupAdmin" uga ON uga."UGId"=g."UGId"\n\
			JOIN "User" u ON  u."UserId"=uga."AdminId"\n\
		WHERE g."ParentUGId"=0 and g."UGId">1 and u."UserCode"=\'%s\'\n\
	UNION ALL \n\
	SELECT g."UGId", g."UGName", CAST(s."Path"||E\'/\'||g."UGName" AS VARCHAR), g."ParentUGId"\n\
			FROM "UGroup" g\n\
			JOIN subgroup s ON g."ParentUGId"=s."Id"\n\
			JOIN "UGroupAdmin" uga ON uga."UGId"=g."UGId"\n\
                        JOIN "User" u ON  u."UserId"=uga."AdminId"\n\
		WHERE g."ParentUGId"=s."Id" and u."UserCode"=\'%s\'\n\
)select "Id","Name", "Path" from subgroup \n\
)AS r'%(system_user,system_user)
			debug(str(sql))
			curs.execute(sql)
			debug('-------------------------')
			#debug(str(result))
			result = curs.fetchall()[0][0]
			debug(str(result))
			if result==None:
				result=[]
			return "{\"Result\":true,\"info\":%s}" % str(result)
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#token导入
@authtype_list.route('/import_test_data',methods=['GET','POST'])
def import_test_data():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	f = request.files['file_change']
	new_file_name='%s.csv'%(str(UpdateGenerate()))
	if session < 0:
		session = ""
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
	fname = secure_filename(f.filename)
	file_pwd = os.path.join('/usr/storage/.system/upload/',new_file_name)
	f.save(file_pwd)
	return import_all(file_pwd,system_user)

def checkid(_id):
	p = re.compile(u'^[0-9]+$')
	if p.match(_id):
		return True
	else:
		return False
def checkkey(key):
	p=re.compile(u'^[0-9a-zA-Z]+$')
	if p.match(key):
		return True
	else:
		return False
def import_all(file_pwd,system_user):
	reload(sys)
	sys.setdefaultencoding('utf-8')
	fail=0
	succ=0
	try:
		with open(file_pwd,'rb') as csvfile:
			reader = csv.reader(csvfile)
			for index,rows in enumerate(reader):
				if index==0:
					continue
				rows[0]=rows[0].strip()
                                rows[1]=rows[1].strip()
				if len(rows[0])>32:
					fail+=1
					continue
				elif len(rows[0])<=0:
					fail+=1
					continue
				elif not checkid(rows[0]):
					fail+=1
					continue
				if len(rows[1])>128:
					fail+=1
					continue
				elif len(rows[1])<=0:
					fail+=1
					continue
				elif not checkkey(rows[1]):
					fail+=1
					continue
				try:
					with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
						sql='select public."PSaveToken"(E\'{"TokenId":"%s","Key":"%s"}\')'%(rows[0],rows[1])
						curs.execute(sql)
						result = curs.fetchall()[0][0]
						conn.commit()
						result_json=json.loads(result)
						if result_json["Result"]==True and result_json["RowCount"]>=1:
							succ+=1
						else:
							fail+=1	
				except pyodbc.Error,e:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)				
		os.remove(file_pwd)
		oper='导入令牌'
		if fail==0:
			if not system_log(system_user,oper,'成功','运维管理>认证方式'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"成功\"}"
		else:
			if not system_log(system_user,oper,'成功：%s，失败：%s'%(succ,fail),'运维管理>认证方式'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"成功：(%s)，失败：(%s)\"}"%(succ,fail)
	except IOError as err:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（文件打开失败）\"}"
	except Exception,ex:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（语法错误）\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#token列表
@authtype_list.route('/get_toten_list',methods=['GET','POST'])
def get_toten_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	_id=request.form.get('a1')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	searchstring=request.form.get('a5')
	if _id<0:
		_id='null'
	else:
		_id="'%s'"%_id
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	if session < 0:
		session = ""
	if searchstring<0:
		searchstring='null'
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
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
	if paging!="null":
		paging=(paging-1)*num
	searchstring=searchstring.replace("\\\\","\\\\\\\\")
	searchstring=searchstring.replace(".","\\\\.")
	searchstring=searchstring.replace("?","\\\\?")
	searchstring=searchstring.replace("+","\\\\+")
	searchstring=searchstring.replace("(","\\\\(")
	searchstring=searchstring.replace("*","\\\\*")
	searchstring=searchstring.replace("[","\\\\[")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select public."PGetToken"(%s,%s,%s,E\'%s\',%s)'%(_id,num,paging,MySQLdb.escape_string(searchstring).decode("utf-8"),dsc)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#添加token
@authtype_list.route('/add_token',methods=["GET",'POST'])
def add_token():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	json_Str = request.form.get('a1')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>认证方式'
	num = request.form.get('a2')
	json_Str=str(json_Str)
	json_Str_json=json.loads(json_Str)
	if session < 0:
		session = ""
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
			sql='select public."PSaveToken"(E\'%s\')'%(MySQLdb.escape_string(json_Str).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if num=='1':
				oper='创建令牌：%s'%json_Str_json['TokenId']
			else:
				oper='编辑令牌：%s'%json_Str_json['TokenId']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				conn.commit()
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#创建  编辑
@authtype_list.route('/add_authtype',methods=['GET','POST'])
def add_authtype():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	authtype = request.form.get('a1')
	module_name = request.form.get('a10')
	
	flag_init_pwd = request.form.get('a2')
	
	if flag_init_pwd <0 or flag_init_pwd=='':
		flag_init_pwd = 0
	else:
		flag_init_pwd = int(flag_init_pwd)
		
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(authtype);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	authtype=str(authtype)
	authtype_json=json.loads(authtype)
	if session < 0:
		session = ""
	if module_name<0:
		module_name='运维管理>认证方式'
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
			# PSaveAuthType(jsondata)
			sql="select public.\"PSaveAuthType\"(E'%s')" %(MySQLdb.escape_string(authtype).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if str(authtype_json['AuthTypeId'])=='0':
				oper='创建认证方式：%s'%authtype_json['AuthTypeName']
			else:
				oper='编辑认证方式：%s'%authtype_json['AuthTypeName']
			if result_json["Result"]:
				authtype_json["AuthTypeId"]=result_json["AuthTypeId"]
				sql="select public.\"PGetAuthType\"(%s,null,null,null,null,null,null);"%(result_json["AuthTypeId"])
				debug(str(sql))
				curs.execute(sql)
				result_item = curs.fetchall()[0][0]
				result_item_json=json.loads(result_item)
				oper_arr=[]
				debug(result_item)
				if result_item_json['data'][0]['IsDefault']:
					oper_arr.append('默认')
				if result_item_json['data'][0]['MustAllModulesSucc']:
					oper_arr.append('认证方式：全部通过')
				else:
					oper_arr.append('认证方式：部分通过')
				if result_item_json['data'][0]['Separator']==None:
					oper_arr.append('分隔符：长度')
				else:
					oper_arr.append('分隔符：%s'%result_item_json['data'][0]['Separator'])
				authmodule_arr=[]
				for i in result_item_json['data'][0]['Set']:
					authmodule_arr.append(i['AuthModuleName'])
				oper_arr.append('模块：'+'、'.join(authmodule_arr))
				oper+=('（'+'，'.join(oper_arr)+'）')
				##[global]
				#class=taskauth
				#type=write_fun
				#json_str=authtype_json
				task_content = '[global]\nclass = taskauth\ntype = write_fun\njson_str=%s\n' % (str(json.dumps(authtype_json)))
				if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				
				##
				if flag_init_pwd == 1:
					##result_json["AuthTypeId"]
					sql="update public.\"User\" set \"SecretKey\"=null where \"AuthTypeId\"=%d;" %(int(result_json["AuthTypeId"]))
					curs.execute(sql)				
					
				conn.commit()
				return result  
			else:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
	except pyodbc.Error,e:
		#return "{\"Result\":false,\"ErrMsg\":\"%s\"}" %(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

def encrypt_pwd(Password):
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	ret = lib.encrypt_pwd(Password,pwd_rc4);#执行函数
	return pwd_rc4.value

#ad ldap 同步
@authtype_list.route('/synchronization_ad_or_ldap',methods=['GET','POST'])
def synchronization_ad_or_ldap():
	debug('------------------------------------------------')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	search_ad_or_ldap = request.form.get('a1')
	pwd_ad_or_ldap = request.form.get('a2')
	synchronization_user = request.form.get('a3')
	synchronization_pwd = request.form.get('a4')
	authmode_value = request.form.get('a5')
	authmode_id = request.form.get('a6')
	HG_select = request.form.get('a7')
	authmode_name= request.form.get('a8')
	module_name = request.form.get('a10')
	if module_name<0:
		module_name='运维管理>认证方式'
	if session < 0:
		session = ""
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
	if HG_select=='0':
		HG_select=''
	if pwd_ad_or_ldap=='':
		pwd_ad_or_ldap='12345678'
	pwd_ad_or_ldap=encrypt_pwd(pwd_ad_or_ldap)
	debug(str(pwd_ad_or_ldap))
	if pwd_ad_or_ldap.find('"Result":false')!=-1:
		return pwd_ad_or_ldap
	debug(str(synchronization_pwd))
	synchronization_pwd=encrypt_pwd(synchronization_pwd)
	debug(str(synchronization_pwd))
	if synchronization_pwd.find('"Result":false')!=-1:
		return synchronization_pwd
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='SELECT "User"."UserId" FROM "public"."User" WHERE "User"."UserCode"=\'%s\'' %(system_user)
			curs.execute(sql)
			result = curs.fetchall()
		debug(str(result[0][0]))
		debug('----')
		debug("/flash/system/appr/ldapsync %s %s %s %s '%s' %s '%s' '/var/tmp/synchronization%s' %s"%(authmode_value,synchronization_user,synchronization_pwd,authmode_id,search_ad_or_ldap,str(result[0][0]),pwd_ad_or_ldap,session,HG_select))
		pr=os.popen("/flash/system/appr/ldapsync %s %s %s %s '%s' %s '%s' '/var/tmp/synchronization%s' %s"%(authmode_value,synchronization_user,synchronization_pwd,authmode_id,search_ad_or_ldap,str(result[0][0]),pwd_ad_or_ldap,session,HG_select))
		pt=pr.readlines()
		debug('pt:%s'%str(pt))
		ret=int(pt[-1].replace("\n", ""))
		os.remove('/var/tmp/synchronization%s'%session)
		oper='同步认证模块：%s'%authmode_name
		if ret>=0:
			if not system_log(system_user,oper,'成功',module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"info\":\"同步成功\",\"num\":%s}"%ret
		elif ret==-1:
			if not system_log(system_user,oper,'获取配置失败',module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"获取配置失败\"}"
		elif ret==-2:
			if not system_log(system_user,oper,'认证失败',module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"认证失败\"}"
		elif ret==-3:
			if not system_log(system_user,oper,'获取账号失败',module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"获取账号失败\"}"
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#get_ret
@authtype_list.route('/get_ret',methods=['GET','POST'])
def get_ret():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	update_token_json = request.form.get('a1')
	update_token_json=str(update_token_json)
	if session < 0:
		session = ""
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
	with open('/var/tmp/synchronization%s'%session,'r') as fp:
		str_arr=fp.readlines()
		debug(str(str_arr))
		if len(str_arr)!=0:
			ret=int(str_arr[-1].replace("\n", ""))
			debug('ret:%s'%ret)
			os.remove('/var/tmp/synchronization%s'%session)
			if ret>=0:
				return "{\"Result\":true,\"info\":\"同步成功\",\"num\":%s}"%ret
			elif ret==-1:
				return "{\"Result\":false,\"ErrMsg\":\"获取配置失败\"}"
			elif ret==-2:
				return "{\"Result\":false,\"ErrMsg\":\"认证失败\"}"
			elif ret==-3:
				return "{\"Result\":false,\"ErrMsg\":\"获取账号失败\"}"
		else:
			return "{\"Result\":true,\"info\":\"\",\"num\":0}"
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		
	

#update_token同步
@authtype_list.route('/update_token',methods=['GET','POST'])
def update_token():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	update_token_json = request.form.get('a1')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>认证方式'
	update_token_json=str(update_token_json)
	if session < 0:
		session = ""
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
	update_token_json=json.loads(update_token_json)
	if os.path.exists('/usr/lib64/libetotpverify.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" % (sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/libetotpverify.so")
	#ET_Syncz201(key,time(NULL),0,60,last_drift,40,last_succ,dpwd1,6,dpwd2,6,&cur_succ,&cur_drift);
	cur_succ=c_int(0)
	pcur_succ = pointer(cur_succ)
	cur_drift=c_int(0)
	pcur_drift = pointer(cur_drift)
	lib.ET_Syncz201.argtypes = (c_char_p,c_int,c_int,c_uint,c_int,c_int,c_int,c_char_p,c_int,c_char_p,c_int,c_void_p,c_void_p)
	#定义函数参数
	lib.ET_Syncz201.restype = c_int 
	#定义函数返回值
	ret = lib.ET_Syncz201(update_token_json["Key"],int(time.time()),0,60,update_token_json["last_drift"],120,update_token_json["last_succ"],update_token_json["dpwd1"],len(update_token_json["dpwd1"]),update_token_json["dpwd2"],len(update_token_json["dpwd2"]),pcur_succ,pcur_drift)
	oper='同步令牌：%s'%(update_token_json['TokenId'])
	if ret==1:
		if not system_log(system_user,oper,'参数无效',module_name):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"参数无效\"}"
	elif ret==2:
		if not system_log(system_user,oper,'认证失败',module_name):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"认证失败\"}"
	elif ret==3:
		if not system_log(system_user,oper,'同步失败',module_name):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"同步失败\"}"
	elif ret==4:
		if not system_log(system_user,oper,'动态口令被重放',module_name):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"动态口令被重放\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='UPDATE "public"."Token" SET "LastDriftValue"=%s,"LastSuccValue"=%s WHERE "TokenId"=\'%s\';'%(pcur_drift.contents.value,pcur_succ.contents.value,update_token_json["TokenId"])
			curs.execute(sql)
			conn.commit()
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	if not system_log(system_user,oper,'成功',module_name):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return "{\"Result\":true,\"info\":\"同步成功\"}"
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	


#删除token
@authtype_list.route('/del_token',methods=['GET', 'POST'])
def del_token():
	debug('--11---')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	debug(str(ids))
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
			success_num=0
			fail_num=0
			all_arr=[]
			success_arr=[]
			fail_arr=[]
			for id in ids:
				debug(str(id))
				if id==None or id=='':
					continue
				# PDeleteToken(id)

				all_arr.append(id)
				sql = "select public.\"PDeleteToken\"('%s');" % (id)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				debug(str(sql))
				if not result_json['Result']:
					fail_num+=1
					fail_arr.append(id)
					#return result
				else:
					success_num+=1
					success_arr.append(id)
					conn.commit()
			oper='删除令牌：%s'%('、'.join(all_arr))
			debug(str(oper))
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
			if not system_log(system_user,oper,mesg,'运维管理>认证方式'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
			return "{\"Result\":true,\"info\":\"删除成功\",\"fail_num\":%s,\"success_num\":%s,\"ErrMsg\":\"%s\"}"%(fail_num,success_num,mesg)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#测试认证模块
@authtype_list.route('/test_authmdule',methods=['GET', 'POST'])
def test_authmdule():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	test_json = request.form.get('a1')
	session = request.form.get('a0')
	athor=request.form.get('a2')
	test_name=request.form.get('a3')
	if session < 0:
		session = ""
	if athor<0:
		athor=''
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
	test_json=json.loads(str(test_json))
	
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	lib.pam_test.argtypes = [c_char_p,c_char_p,c_int,c_int,c_char_p]
	#定义函数参数
	lib.pam_test.restype = c_int 
	#定义函数返回值
	if(test_json["authmode"] == 6):
		ret = lib.pam_test(test_json["user"],test_json["pwd"],30+int(test_json["authmode"]),test_json["id"],athor)
	else:
		ret = lib.pam_test(test_json["user"],test_json["pwd"],int(test_json["authmode"]),test_json["id"],athor)
	
	'''
	pr=os.popen("./main %s '%s' %s %s"%(test_json["user"],test_json["pwd"],test_json["id"],test_json["authmode"]));
	pr=pr.readlines()
	ret=pr[-1].replace('ret:','').replace('\n','');
	'''
	#执行函数
	return '{"Result":true,"info":%s}'%(str(ret))
	return '{"Result":true,"info":%s}'%(data[-1].replace('ret:','').replace('\n',''))

#删除认证方式
@authtype_list.route('/del_authtype',methods=['GET', 'POST'])
def del_authtype():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	module_name=request.form.get('a10')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	if module_name<0:
		module_name='运维管理>认证方式'
	ids = id_str.split(',')
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
			success_num=0
			fail_num=0
			all_arr=[]
			fail_arr=[]
			success_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				all_arr.append(id_arr[1])
				value=int(id_arr[0])
				# PDeleteAuthType(authtypeid)
				sql = "select public.\"PDeleteAuthType\"(%d);" % (value)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_arr.append(id_arr[1])
					fail_num+=1
					#return result
				else:
					success_arr.append(id_arr[1])
					success_num+=1
					conn.commit()
					##[global]
                                	#class=taskauth
                                	#type=del_auth
                                	#authid=id
                                	task_content = '[global]\nclass = taskauth\ntype = del_auth\nauthid=%s\n' % (value)
                                	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                                	        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

			oper='删除认证方式：%s'%('、'.join(all_arr))
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
	
###更新 令牌的状态
@authtype_list.route('/update_token_status',methods=['GET', 'POST'])
def update_token_status():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	token_id = request.form.get('a1')
	session = request.form.get('a0')
	status=request.form.get('a2')
	if session < 0:
		session = ""	
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='update public."Token" set "Memo"=\'%s\' where "TokenId" =\'%s\';' %(status,token_id)
			debug(sql);
			curs.execute(sql)
			conn.commit();
			return "{\"Result\":true,\"ErrMsg\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
