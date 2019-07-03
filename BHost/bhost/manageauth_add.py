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
import shutil
import time
from index import PGetPermissions 
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from htmlencode import parse_sess
from htmlencode import check_role
from comm_function import get_user_perm_value
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader 
from logbase import db
from logbase import defines
from comm_function import PGetSecurityPasswd
from logbase import task_client
from werkzeug.utils import secure_filename
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
manageauth_add = Blueprint('manageauth_add',__name__)
EXPOET_PATH = '/usr/storage/.system/dwload/'
UPLOAD_FOLDER = '/usr/storage/.system/upload/'
SIZE_PAGE = 20
ERRNUM_MODULE = 1000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
	path = "/var/tmp/debugrx_ccp.txt"
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
	return newStr
#打开管理权限创建页面
@manageauth_add.route('/manage_auth_add',methods=['GET','POST'])
def manage_auth_add():
	tasktype = request.form.get("tasktype")
	manageauthId = request.form.get("manageauthId")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	se = request.form.get("se")
	user = request.form.get("user")
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_1=0
	perm_2=0
	perm_3=0
	for i in perm_json:
		if i['SubMenuId']==18 and i['SystemMenuId']==3:
			perm=i['Mode']
		elif i['SubMenuId']==15 and i['SystemMenuId']==3:
			perm_1=i['Mode']
		elif i['SubMenuId']==16 and i['SystemMenuId']==3:
			perm_2=i['Mode']
		elif i['SubMenuId']==17 and i['SystemMenuId']==3:
			perm_3=i['Mode']
	if e<0:
		e=":"
	if se<0:
		se=''
	if user<0:
		user=''
	if tasktype < 0:
		tasktype = "1"
	if search_typeall < 0:
		search_typeall = ""
	if manageauthId < 0:
		manageauthId = "0"
	if paging < 0:
		paging = "1"
	if tasktype == "3":
		t = "manageauth_list.html"
	else:
		t = "manageauth_add.html"
	return render_template(t,paging=paging,manageauthId=manageauthId,tasktype=tasktype,search_typeall=search_typeall,e=e,se=se,user=user,perm=perm,perm_1=perm_1,perm_2=perm_2,perm_3=perm_3)
#判断同名
@manageauth_add.route('/getmanageauthbyname',methods=['GET', 'POST'])
def getmanageauthbyname():
	ManageAuthName = request.form.get('a1')
	sess=request.form.get('a0')
	if ManageAuthName<0:
		ManageAuthName="null"
	else:
		ManageAuthName="E'%s'"%ManageAuthName
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
			# PGetManageAuthByName (name)
			sql="select public.\"PGetManageAuthByName\"(%s);"%(ManageAuthName)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#搜索主机树
@manageauth_add.route('/find_usergroup',methods=['GET','POST'])
def find_hostgroup():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	user_find_json = request.form.get('a1')
	user_find_json=str(user_find_json)
	if sess < 0:
		sess = ""
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
	#PFindUserDirectory(user_find_json)
	user_find_json=user_find_json.replace("\\\\","\\\\\\\\")
	user_find_json=user_find_json.replace(".","\\\\.")
	user_find_json=user_find_json.replace("?","\\\\?")
	user_find_json=user_find_json.replace("+","\\\\+")
	user_find_json=user_find_json.replace("(","\\\\(")
	user_find_json=user_find_json.replace("*","\\\\*")
	user_find_json=user_find_json.replace("[","\\\\[")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PFindUserDirectory\"(E'%s');"%(MySQLdb.escape_string(user_find_json).decode("utf-8"))
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results==None:
				results="[]"
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
	
#显示 or 分页 or 搜索userdir
@manageauth_add.route('/get_userdirectory',methods=['GET', 'POST'])
def get_userdirectory():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	loginusercode = request.form.get('a1')
	ugid = request.form.get('a2')
	id = request.form.get('a5')
	type = request.form.get('a6')
	Name="";
	if ugid<0 or ugid=="":
		ugid="null"
	if sess < 0:
		sess = ""
	if id < 0:
		id = "0"
	if type < 0:
		type = "0"
	if loginusercode < 0:
		loginusercode = "null"
	else:
		loginusercode="E'%s'"% loginusercode
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
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		sys.exit()
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetUserDirectory (loginusercode,ugid,type,id,limitrow,offsetrow)
			sql="select public.\"PGetUserDirectory\"(E'%s',%s,%s,%s,%s,%s);"%(system_user,ugid,type,id,num,paging)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索manageauth
@manageauth_add.route('/get_manageauth_list',methods=['GET', 'POST'])
def get_manageauth_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	manageauthId = request.form.get('a1')
	search_typeall = request.form.get('a2')
	
	if search_typeall<0:
		search_typeall=""
	if manageauthId<0 or manageauthId=="0" or manageauthId=="":
		manageauthId="null"
	if sess < 0:
		sess = ""
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
	searchstring=''
	Name=""
	User=''
	userGroup=''
	ClientScopeName=''
	ServerScopeName=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="ManageAuthName":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=='user':
			User=User+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="userGroup":
			userGroup=userGroup+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ClientScopeName":
			ClientScopeName=ClientScopeName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ServerScopeName":
			ServerScopeName=ServerScopeName+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if Name=="":
		Name="null"
	else:
		Name="'%s'"%(Name[:-1])
	if User=="":
		User="null"
	else:
		User="'%s'"%(User[:-1])
	if searchstring!="":
		searchstring=searchstring[:-1]
	if userGroup!="":
		userGroup=userGroup[:-1]
	if ClientScopeName!="":
		ClientScopeName=ClientScopeName[:-1]
	if ServerScopeName!="":
		ServerScopeName=ServerScopeName[:-1]
	searchconn={}
	searchconn['searchstring']=searchstring
	searchconn['UGName']=userGroup
	searchconn['ClientScopeName']=ClientScopeName
	searchconn['ServerScopeName']=ServerScopeName
	searchconn=json.dumps(searchconn)
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	User=User.replace("\\\\","\\\\\\\\")
	User=User.replace(".","\\\\.")
	User=User.replace("?","\\\\?")
	User=User.replace("+","\\\\+")
	User=User.replace("(","\\\\(")
	User=User.replace("*","\\\\*")
	User=User.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetManageAuth(manageauthid,manageauthname,limitrow,offsetrow)
			sql="select public.\"PGetManageAuth\"(%s,%s,%s,%s,%s,E'%s');"%(manageauthId,Name,User,num,paging,searchconn)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
	#创建 or 编辑manageauth
@manageauth_add.route('/add_manageauth',methods=['GET', 'POST'])
def add_manageauth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	manageauth = request.form.get('a1')
	manageauth=str(manageauth)
	manageauth_json=json.loads(manageauth)
	#fid = request.form.get('a3')
	newuserid = request.form.get('a2')
	module_name = request.form.get('a10')
	md5_str = request.form.get('m1')
	if module_name<0:
		module_name='运维管理>管理授权'
	if session < 0:
		session = ""
	if newuserid < 0 or newuserid=="":
		newuserid = "null"
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

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(manageauth);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(system_user,'管理授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveManageAuth(newuserid,jsondata)
			sql="select public.\"PSaveManageAuth\"(%s,E'%s');" %(newuserid,MySQLdb.escape_string(manageauth).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)

                        task_content = '[global]\nclass = taskupdatehnodeselected\ntype = update_run\nid_type=1001\nid=%s\n' % (str(result_json["ManageAuthId"]))
                        if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                                if manageauth_json['ManageAuthId'] == 0:
                                        system_log(usercode,"创建管理授权:%s" % manageauth_json['WorkOrderName'],"失败","运维管理>管理授权")
                                else:
                                        system_log(usercode,"编辑管理授权:%s" % manageauth_json['WorkOrderName'],"失败","运维管理>管理授权")
                                return "{\"Result\":false,\"ErrMsg\":\"扫描任务下发异常(%d)\"}" %(sys._getframe().f_lineno)

			if manageauth_json['ManageAuthId']==0:
				oper='创建管理授权：%s'%manageauth_json['ManageAuthName']
			else:
				oper='编辑管理授权：%s'%manageauth_json['ManageAuthName']
			if result_json['Result']:
				sql="select public.\"PGetManageAuth\"(%s,null,null,null,null);" %result_json['ManageAuthId']
				curs.execute(sql)
				ManageAuth=curs.fetchall()[0][0]
				ManageAuth_json=json.loads(ManageAuth)
				if ManageAuth_json['totalrow']==0:
					if not system_log(system_user,oper,'生成日志失败',module_name):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				else:
					ManageAuth=ManageAuth_json['data'][0]
					ManageAuth_oper=[]
					#if ManageAuth['ManageAuthName']!=None and ManageAuth['ManageAuthName']!='':
					#	ManageAuth_oper.append('名称：%s'%ManageAuth['ManageAuthName'])
					if ManageAuth['UserSet']!=None and len(ManageAuth['UserSet'])>0:
						u_arr=[]
						ug_arr=[]
						for item in ManageAuth['UserSet']:
							if item['Type']==1:
								u_arr.append(item['Name'])
							elif item['Type']==2:
								ug_arr.append(item['Name'])
						if len(ug_arr)>0:
							ManageAuth_oper.append('用户组：%s'%('、'.join(ug_arr)))
						if len(u_arr)>0:
							ManageAuth_oper.append('用户：%s'%('、'.join(u_arr)))
					if ManageAuth['CScopeSet']!=None and len(ManageAuth['CScopeSet'])>0:
						CScopeSet=[]
						for item in ManageAuth['CScopeSet']:
							CScopeSet.append(item['ClientScopeName'])
						ManageAuth_oper.append('客户端登录：%s'%('、'.join(CScopeSet)))
					if ManageAuth['MScopeSet']!=None and len(ManageAuth['MScopeSet'])>0:
						MScopeSet=[]
						for item in ManageAuth['MScopeSet']:
							MScopeSet.append(item['ServerScopeName'])
						ManageAuth_oper.append('服务器管理：%s'%('、'.join(MScopeSet)))
					oper+=('（'+'，'.join(ManageAuth_oper)+'）')
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			else:
				if not system_log(system_user,oper,result_json['Result'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除manageauth
@manageauth_add.route('/del_manageauth',methods=['GET', 'POST'])
def del_manageauth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	module_name = request.form.get('a10')
	if module_name<0:
		module_name='运维管理>管理授权'
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
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

	if check_role(system_user,'管理授权') == False:
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
				value=int(id_arr[0])
				all_arr.append(id_arr[1])
			# PDeleteManageAuth(manageauthid)
			# return
			# {"Result":false,"info":"传入参数不正确"}或
			# {"Result":true,"RowCount":1}
				sql = "select public.\"PDeleteManageAuth\"(%d);" % (value)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_num+=1
					fail_arr.append(id_arr[1])
				else:	
					success_arr.append(id_arr[1])
					success_num+=1
					conn.commit()
			oper='删除管理授权：%s'%('、'.join(all_arr))
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
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
###########管理授权
####导入

@manageauth_add.route('/import_data_pwd',methods=['GET', 'POST'])
def import_data_pwd():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    se = request.form.get("a0")
    cover = request.form.get('a1')
    use_BH = request.form.get('a99')
    if use_BH=='0':
        f = request.files['file_change1']
        file_v = secure_filename(f.filename)
    else:
        file_change = request.form.get('file_change')
        file_v = request.form.get('file_v')
    client_ip = request.remote_addr
    (error,system_user,mac) = SessionCheck(se,client_ip)
    if error < 0:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    elif error > 0:
        if error == 2:
            return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
        else:
            return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
            
    if check_role(system_user,'管理授权') == False:
        return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

    fname = file_v
    if len(fname.split('.')[-1]) == 4:
            taskname = fname[:-5]
    else:
            taskname = fname[:-4]
    time_str=str(int(time.time()))
    fname_arr=fname.split('.')
    fname_arr.insert(-1,time_str)
    file_pwd = os.path.join(UPLOAD_FOLDER,'.'.join(fname_arr))
    if use_BH=='0':
        f.save(file_pwd)
    else:
        shutil.move(file_change,file_pwd)
    # f.save(os.path.join(UPLOAD_FOLDER, fname))
    taskid = 0;
    try:
        with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:#新建任务
            sql = "SELECT nextval('private.\"AuthImportTask_AuthImportTaskId_seq\"'::regclass);"
            curs.execute(sql)
            taskid = curs.fetchall()[0][0]
            sql = "SELECT \"UserId\" from public.\"User\" where \"UserCode\"='%s';"%(MySQLdb.escape_string(system_user).decode("utf-8"))
            curs.execute(sql)
            userid=curs.fetchall()[0][0]
            sql = "insert into private.\"AuthImportTask\"(\"AuthImportTaskId\",\"AuthImportTaskName\",\"Type\",\"UserId\") values(%d,E'%s',5,%s);" %(taskid,MySQLdb.escape_string(taskname).decode("utf-8"),userid)			
            debug(sql)
            curs.execute(sql)
            conn.commit();
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

    task_content = '[global]\nclass = taskdown_manage_auth\ntype = execute_import_pwd_cmd\nfile_pwd=%s\ncover=%s\ntaskid=%s\nuserid=%s\n' % (file_pwd,cover,str(taskid),system_user)
    debug(task_content)
    if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
        system_log(system_user,"创建密码导入任务：%s" % fname,"失败：任务下发异常","密码管理>密码录入")
        return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)

    system_log(system_user,"创建密码导入任务：%s" % fname,"成功","密码管理>密码录入")
    return "{\"Result\":true}"


###########管理授权
####导入

@manageauth_add.route('/import_data_manage_auth',methods=['GET', 'POST'])
def import_data__manage_auth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	cover = request.form.get('a1')
	use_BH = request.form.get('a99')
	if use_BH=='0':
		f = request.files['file_change1']
		file_v = secure_filename(f.filename)
	else:
		file_change = request.form.get('file_change')
		file_v = request.form.get('file_v')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
			
	if check_role(system_user,'管理授权') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	fname = file_v
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
	file_pwd = os.path.join(UPLOAD_FOLDER,fname)
	debug(file_pwd)
	if use_BH=='0':
		f.save(os.path.join(UPLOAD_FOLDER, fname))
	else:
		shutil.move(file_change,file_pwd)
	# f.save(os.path.join(UPLOAD_FOLDER, fname))
	debug("12313")
	taskid = 0;
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:#新建任务
			curs = conn.cursor()
			sql = "SELECT nextval('private.\"AuthImportTask_AuthImportTaskId_seq\"'::regclass);"
			debug(sql)
			curs.execute(sql)
			taskid = curs.fetchall()[0][0]
			sql = "SELECT \"UserId\" from public.\"User\" where \"UserCode\"='%s';"%(MySQLdb.escape_string(system_user).decode("utf-8"))
                        curs.execute(sql)
                        userid=curs.fetchall()[0][0]
			sql = "insert into private.\"AuthImportTask\"(\"AuthImportTaskId\",\"AuthImportTaskName\",\"Type\",\"UserId\") values(%d,E'%s',4,%s);" %(taskid,MySQLdb.escape_string(taskname).decode("utf-8"),userid)			
			debug(sql)
			curs.execute(sql)
			conn.commit();
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	task_content = '[global]\nclass = taskdown_manage_auth\ntype = execute_import_cmd\nfile_pwd=%s\ncover=%s\ntaskid=%s\nuserid=%s\n' % (file_pwd,cover,str(taskid),system_user)
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		system_log(system_user,"创建管理授权导入任务：%s" % fname,"失败：任务下发异常","运维管理>管理授权")
		return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)

	system_log(system_user,"创建管理授权导入任务：%s" % fname,"成功","运维管理>管理授权")
	return "{\"Result\":true}"

@manageauth_add.route('/del_manage_auth_task',methods=['GET', 'POST'])		
def del_manage_auth_task():
	se = request.form.get('a0')
	del_id = request.form.get('a1')
	debug(str(del_id))
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
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
			id_array = str(del_id).split(',')
			debug(str(id_array))
			Name_arry = []
			for id_v in id_array:
				debug(str(id_v))
				curs.execute("select \"AuthImportTaskName\" from private.\"AuthImportTask\" where \"AuthImportTaskId\" = %d;" % int(id_v))
				result_1 = curs.fetchall()[0][0].encode('utf-8')
				Name_arry.append(result_1)
				sql ="delete from private.\"AuthImportTask\" where  \"AuthImportTaskId\" = %d;" % int(id_v)
				debug(sql)
				curs.execute(sql)
				
			system_log(userCode,"删除管理授权导入任务：%s" % ('、'.join(Name_arry)),"成功","运维管理>管理授权")
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manageauth_add.route('/get_manage_auth_task_detail',methods=['GET', 'POST'])
def get_manage_auth_task_detail():	
	se = request.form.get('a0')
	cur = request.form.get('a1')
	page_total = request.form.get('a2')

	taskid = request.form.get('a4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if page_total == 'null':
		offsetrow = 'null'
	else:
		offsetrow = str((int(cur)-1)*(int(page_total)))


	data = '{"AuthImportTaskId":'+taskid+',"Status":'+status+',"limitrow": '+page_total+',"offsetrow": '+offsetrow+',"UserCode": "'+userCode+'"}'
	#data = '{"hostleadintaskid":'+taskid+',"HostLeadInTaskName":null,"hostleadintaskdetailid": null,"limitrow": '+page_total+',"offsetrow": '+offsetrow+'}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manageauth_add.route('/get_manage_auth_task_data',methods=['GET', 'POST'])
def get_manage_auth_task_data():
	se = request.form.get('a0')
	cur = request.form.get('a1')
	page_total = request.form.get('a2')
    	type_value = request.form.get('a3')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if page_total == 'null':
		offsetrow = 'null'
	else:
		offsetrow = str((int(cur)-1)*(int(page_total)))
    	if type_value<0 or type_value==None:
        	type_value='4'
    	data = '{"AuthImportTaskId":null,"Type":'+type_value+',"limitrow":'+page_total+',"offsetrow":'+offsetrow+',"UserCode": "'+userCode+'"}'

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manageauth_add.route('/isexist_import_manage_auth',methods=['GET', 'POST'])
def isexist_import_manage_auth():
	se = request.form.get('a0')
	file_v = request.form.get('file_v')
	debug("1231313")
	fname = file_v
	debug('fname:%s' % fname);
	f_name = fname[:-4]
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
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
			sql = "select * from private.\"AuthImportTask\" where \"AuthImportTaskName\" = E\'%s\' and \"Type\"=4 and \"Status\"=0;" % MySQLdb.escape_string(taskname).decode("utf-8")
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				return "{\"Result\":true}"
			else:
				system_log(userCode,"创建管理授权导入任务：%s" % fname,"失败：该任务已存在","运维管理>管理授权")
				return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manageauth_add.route('/isexist_import_pwd',methods=['GET', 'POST'])
def isexist_import_pwd():
	se = request.form.get('a0')
	file_v = request.form.get('file_v')
	fname = file_v
	f_name = fname[:-4]
	if len(fname.split('.')[-1]) == 4:
			taskname = fname[:-5]
	else:
			taskname = fname[:-4]
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select * from private.\"AuthImportTask\" where \"AuthImportTaskName\" = E\'%s\' and \"Type\"=5 and \"Status\"=0;" % MySQLdb.escape_string(taskname).decode("utf-8")
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) == 0:
				return "{\"Result\":true}"
			else:
				system_log(userCode,"创建密码导入任务：%s" % fname,"失败：该任务已存在","密码管理>密码录入")
				return "{\"Result\":false}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)


@manageauth_add.route('/get_import_detail_manage_auth',methods=['GET', 'POST'])
def get_import_detail_manage_auth():
	se = request.form.get('a0')
	t_id = request.form.get('a1')
	keyword = request.form.get('a2')
	limitrow = request.form.get('a3')
	offsetrow = request.form.get('a4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if keyword < 0 or keyword == "":
		keyword = 0
	if keyword == 0:
		status = "null"
	else:
		status = str(keyword)
	if limitrow == "null":
		offsetrow = "null"
	data = '{"AuthImportTaskId":'+t_id+',"Status":'+status+',"limitrow": '+limitrow+',"offsetrow": '+offsetrow+',"UserCode": "'+userCode+'"}'
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetAuthImportTask\"(E'%s')" % data
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#####导出
def down_templet(session):
	try:
		with open(EXPOET_PATH+"manageAuth."+session+".csv","w") as csvfile:
			debug("open")
			csvfile.write(codecs.BOM_UTF8)
			writer = csv.writer(csvfile)
			ugroup_title = ['*用户组名称','*组路径','描述','*管理员']
			writer.writerow(ugroup_title)
			ug_prompt = [['非空且同组下名称唯一','不填为根部目录下','','1.非必填，若没填，默认为导入该账号的管理员为配置它的管理员；2.多个管理员用;分割'],['特殊字符仅支持下划线、横杠、小数点','格式：用户组的绝对路径,即若用户组a在用户组b下，则填/b/a','','']]
			writer.writerows(ug_prompt)
			debug("zzzzzzzzz")

			user_title = ['*用户账号','*用户姓名','认证方式','*密码','手机','描述','邮箱','部门','*角色','*管理员','第三方认证账号','唯一登录','失效时间','用户组','是否启用']
			writer.writerow(user_title)
			u_prompt = [['非空唯一','非空','不填为默认认证方式','非空','','','','','多个角色用;分割','1.非必填，若没填，默认为导入该账号的管理员为配置它的管理员；2.多个管理员用;分割','','是/否','1.不填为不启用；2.格式：yyyy-mm-ddThh:mm:ss；3.T为分割日期和时间的分隔符','默认未分组','是/否'],['特殊字符仅支持下划线、横杠、小数点','特殊字符仅支持下划线、横杠、小数点','特殊字符仅支持下划线、横杠、小数点','','','','','','','','','','','','不填为启动']]
			writer.writerows(u_prompt)
			csvfile.close()
			down_path = EXPOET_PATH+"/manageAuth."+session+".csv"
			debug("12313213")
			return send_from_directory(EXPOET_PATH,'manageAuth.'+session+'.csv',as_attachment=True,attachment_filename='manageAuth.csv')
	except IOError,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manageauth_add.route('/export_data_manage_auth',methods=['GET', 'POST'])
def export_data_manage_auth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('a1')
	session = request.form.get('a0')
	type_value=request.form.get('z2')
	format_value=request.form.get('z3')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	time_value=int(time.time()*1000)
	if type == '1':
		return down_templet(session)
	else:
		task_content = '[global]\nclass = taskdown_manage_auth\ntype = execute_down_cmd\nusercode=%s\nsession=%s\ntype_value=%s\nformat_value=%s\ntime_value=%s\n' % (userCode,session,type_value,format_value,time_value)
		debug(task_content)
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			system_log(userCode,"导出管理授权" ,"失败：任务下发异常(%d): %s"%(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.ErrMsg)),"运维管理>管理授权")
			return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.ErrMsg))
		system_log(userCode,"导出管理授权","成功","运维管理>管理授权")
		return "true:manageAuth.%s.%s"%(session,time_value)
			

@manageauth_add.route('/download_temp_manage_auth',methods=['GET', 'POST'])
def download_temp_manage_auth():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	#type = request.form.get('a1')
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
	return down_templet(session)


@manageauth_add.route('/get_down_ok_manage_auth',methods=['GET', 'POST'])
def get_down_ok_manage_auth():
	se = request.form.get('a0')
	format_value = request.form.get('a1')
	file_name = request.form.get('a2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select * from private.\"AuthExportInfo\" where \"FileName\" like E'%"+file_name+"%';"
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				sql = "delete from private.\"AuthExportInfo\" where \"FileName\" like E'%"+file_name+"%';"
				curs.execute(sql)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
			return "{\"Result\":true,\"ErrMsg\":\""+str(results[0][2])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"file_name\":\""+str(results[0][1])+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@manageauth_add.route('/download_file_user_manage_auth',methods=['GET', 'POST'])
def download_file_user_manage_auth():
	se = request.form.get('a0')
	file_name = request.form.get('a1')
	format_value = request.form.get('z1')
	use_BH = request.form.get('a99')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	system_log(userCode,"导出用户","成功","运维管理>用户管理")
	file_name_arr=file_name.split('.')
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	if use_BH=='0':
		return send_from_directory(EXPOET_PATH,file_name,as_attachment=True,attachment_filename=('.'.join(file_name_arr)))
	else:
		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"%s","filenewname":"%s"}'% (file_name,('.'.join(file_name_arr)))

@manageauth_add.route('/del_manageAuth_file',methods=['GET', 'POST'])
def del_manageAuth_file():
        se = request.form.get('a0')
        format_value = request.form.get('a1')
        #type = request.form.get('z1')
        client_ip = request.remote_addr
        (error,userCode,mac) = SessionCheck(se,client_ip);
        if error < 0:
                return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        elif error > 0:
                if error == 2:
                        return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
                else:
                        return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        passwd=PGetSecurityPasswd(userCode,1)
        if passwd==0:
                return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
        if passwd!='':
                filename='manageAuth.%s.zip' % (se)
        else:
                if format_value == '1':
                        filename='manageAuth.%s.xls' % (se)
                elif format_value == '2':
                        filename='manageAuth.%s.xlsx' % (se)
                else:
                       	filename='manageAuth.%s.csv' % (se)
		# filename='manageAuth.%s.csv' % (se)
        task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(filename))
        if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return 'true'

@manageauth_add.route('/get_authname_m',methods=['GET','POST'])
def get_authname_m():
	session = request.form.get('a0')
	name = request.form.get('z1')
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(session,client_ip);
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
			#debug("select public.\"PGetManageAuthByName\"('%s');"%(name))
			curs.execute("select public.\"PGetManageAuthByName\"(E'%s');"%(name))
			results = curs.fetchall()[0][0]
			return str(results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
