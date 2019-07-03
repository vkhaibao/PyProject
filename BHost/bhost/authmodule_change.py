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
from generating_log import system_log
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from logbase import common
from logbase import defines
from logbase import task_client
from htmlencode import check_role
from htmlencode import parse_sess

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
authmodule_change = Blueprint('authmodule_change',__name__)
UPLOAD_FOLDER = '/usr/storage/.system/upload/'
SIZE_PAGE = 20
def debug(c):
	return 0
        path = "/var/tmp/debugrxl.txt"
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
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	
#跳转至认证配置
@authmodule_change.route('/authmodule_change_show',methods=['GET','POST'])
def authmodule_change_show():
	# sess=request.form.get('se')
	tasktype = request.form.get("tasktype")
	authtypeId = request.form.get("a")
	paging = request.form.get("c")
	search_typeall = request.form.get("b")
	search_typeall_new = request.form.get("e")
	if tasktype < 0:
		tasktype = "3"
	# if sess<0:
	# 	sess=""
	if authtypeId<0:
		authtypeId=0
	if paging<0:
		paging=1
	if search_typeall<0:
		search_typeall=''
	if search_typeall_new<0:
		search_typeall_new=':'
	if tasktype=="3":
		t='authmodule_list.html'
	else:
		t='authmodule_change.html'
	return render_template(t,tasktype=tasktype,a=authtypeId,b=search_typeall,c=paging,e=search_typeall_new)
#修改认证模块
@authmodule_change.route('/update_authmodule',methods=['GET','POST'])
def update_authmodule():
	debug('update_authmodule')
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	authmodule = request.form.get('a1')
	userca_check=request.form.get('a2')
	if userca_check<0 or userca_check==None:
		userca_check='false'
	module_name = request.form.get('a10')
	if module_name<0:
		module_name='运维管理>认证方式'
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
		
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(authmodule);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	authmodule=str(authmodule)
	authmodule_json=json.loads(authmodule)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PSaveAuthModule\"(E'%s');" % (MySQLdb.escape_string(authmodule).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if authmodule_json['AuthModuleId']==0:
				oper='创建认证模块：%s'%authmodule_json['AuthModuleName']
			else:
				oper='编辑认证模块：%s'%authmodule_json['AuthModuleName']
			if result_json["Result"] and result_json["RowCount"]>=1:
				conn.commit()
				oper_arr=[]
				if authmodule_json['AuthModuleId']>1000 or authmodule_json['AuthModuleId']==0:
					if authmodule_json['AuthMode']==2:
						oper_arr.append('方式：AD域')
					elif authmodule_json['AuthMode']==3:
						oper_arr.append('方式：LDAP')
					elif authmodule_json['AuthMode']==4:
						oper_arr.append('方式：RADIUS')
					elif authmodule_json['AuthMode']==9:
						oper_arr.append('方式：USBKey')
					elif authmodule_json['AuthMode']==11:
						oper_arr.append('方式：短信')
				if authmodule_json['PwdLen']!=None and authmodule_json['PwdLen']!='':
					oper_arr.append('长度：%s'%authmodule_json['PwdLen'])
				if authmodule_json['AuthMode']==2:
					oper_arr.append('IP：%s'%authmodule_json['ServerIp'])
					oper_arr.append('端口：%s'%authmodule_json['ServerPort'])
					oper_arr.append('域名：%s'%authmodule_json['BaseDn'])
				elif authmodule_json['AuthMode']==3:
					oper_arr.append('IP：%s'%authmodule_json['ServerIp'])
					oper_arr.append('端口：%s'%authmodule_json['ServerPort'])
					oper_arr.append('Base_DN：%s'%authmodule_json['BaseDn'])
					oper_arr.append('用户标识：%s'%authmodule_json['UserObject'])
					oper_arr.append('用户组标识：%s'%authmodule_json['GroupObject'])
					oper_arr.append('管理员DN：%s'%authmodule_json['AuthUser'])
					if authmodule_json['IsSsl']:
						authmodule_json['IsSsl']='启用'
					else:
						authmodule_json['IsSsl']='不启用'
					oper_arr.append('Ldaps：%s'%authmodule_json['IsSsl'])
				elif authmodule_json['AuthMode']==4:
					oper_arr.append('IP：%s'%authmodule_json['ServerIp'])
					oper_arr.append('端口：%s'%authmodule_json['ServerPort'])
				if authmodule_json['AuthMode']==4:
					authmodule_json['AuthModuleId']=result_json['AuthModuleId']
					authmodule=json.dumps(authmodule_json)
					##[global]
					#class=taskauthmodule
					#type=write_conf_fun
					#json_str=authmodule_json
					task_content = '[global]\nclass = taskauthmodule\ntype = write_conf_fun\njson_str=%s\n' % (str(authmodule))
					if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				elif authmodule_json['AuthModuleId']==8 and userca_check=='true':
						#[global]
						#class = taskUserKey
						#type = setUserKey
						task_content ='[global]\nclass = taskUserKey\ntype = setUserKey\n'
						debug(str(task_content))
						if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
							return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				elif authmodule_json['AuthMode']==9:
					authmodule_json['AuthModuleId']=result_json['AuthModuleId']
					debug("authmodule_json['AuthMode']:"+str(authmodule_json['AuthMode']))
					f = request.files['file_change_1']	
					debug('f:'+str(f))
					debug('2222')
					fname = secure_filename(f.filename);
					debug(fname)
					if fname=='':
						pass
					else:
						fname_r='auth%s_userkey.%s'%(result_json['AuthModuleId'],fname.split('.')[-1])
						f.save(os.path.join(UPLOAD_FOLDER, fname_r))
						debug(fname_r)
						authmodule_json['UserObject']=fname_r
						sql = "select public.\"PSaveAuthModule\"(E'%s');" % (MySQLdb.escape_string(json.dumps(authmodule_json)).decode("utf-8"))
						debug(sql)
						curs.execute(sql)
						conn.commit()
						task_content = '[global]\nclass = taskauthmodule\ntype = move_cert\nfile_name=%s\n' % (str(fname_r))
						debug(task_content)
						if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
							return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				if len(oper_arr)!=0:
					oper+=('（'+'，'.join(oper_arr)+'）')
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				
			else:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				# return result
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#修改认证模块tmp
@authmodule_change.route('/update_authmodule_tmp',methods=['GET','POST'])
def update_authmodule_tmp():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	authmodule = request.form.get('a1')
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
		
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(authmodule);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	authmodule=str(authmodule)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select public.\"PSaveAuthModuleTmp\"(E'%s');" % (MySQLdb.escape_string(authmodule).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if result_json["Result"]==True and result_json["RowCount"]>=1:
				authmodule_json=json.loads(authmodule)
				authmodule_json['AuthModuleId']==result_json['AuthModuleId']
				if authmodule_json['AuthMode']==4:
					##[global]
					#class=taskauthmodule
					#type=write_conf_fun
					#json_str=authmodule_json
					task_content = '[global]\nclass = taskauthmodule\ntype = write_conf_fun1\njson_str=%s\nsess=%s\n' % (str(authmodule),sess)
					if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
					time.sleep(1)
				conn.commit()
				return result
			return "{\"Result\":false,\"ErrMsg\":\"保存失败\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@authmodule_change.route('/delect_authmodule',methods=['GET','POST'])
def delect_authmodule():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	_id = request.form.get('a1')
	AuthMode=request.form.get('a2')
	if sess < 0:
		sess = ""
	if AuthMode < 0:
		AuthMode = ""
	else:
		AuthMode=int(AuthMode)
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
	if AuthMode==4:
		##[global]
		#class=taskauthmodule
		#type=del_radius
		#session=se
               	task_content = '[global]\nclass = taskauthmodule\ntype = del_radius\nsession=%s\n' % (sess)
               	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "DELETE FROM \"public\".\"AuthModuleTmp\" WHERE \"AuthModuleId\" = %s;" % (_id)
			curs.execute(sql)
			conn.commit()
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#获取认证模块
@authmodule_change.route('/get_authmodule_list',methods=['GET','POST'])
def get_authmodule_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	authmoduleid = request.form.get('a1')
	search_typeall=request.form.get('a2')
	paging=request.form.get('a4')
	num = request.form.get('a5')
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
	authmodulename=''
	authmode=''
	if sess < 0:
		sess = ""
	if authmoduleid < 0 or authmoduleid=="0" or authmoduleid=="":
		authmoduleid = "null"
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	if search_typeall<0:
		search_typeall="null"
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
		if search_s[0]=="authmodulename" or search_s[0]=="all":
			authmodulename=authmodulename+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="authmode":
			authmode=authmode+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if authmodulename=="":
		authmodulename="null"
	else:
		authmodulename="E'%s'"%(authmodulename[:-1])
	if authmode=="":
		authmode="null"
	else:
		authmode=authmode[:-1]
		if authmode=='所有':
			authmode='null'
		elif authmode=='本地认证':
			authmode='1'
		elif authmode=='AD域':
			authmode='2'
		elif authmode=='LDAP':
			authmode='3'
		elif authmode=='RADIUS':
			authmode='4'
		elif authmode=='令牌':
			authmode='6'
		elif authmode=='BHost USBKey':
			authmode='8'
		elif authmode=='TOTP':
			authmode='10'
		elif authmode=='短信认证':
			authmode='11'
		elif authmode=='邮箱认证':
			authmode='12'
	authmodulename=authmodulename.replace("\\","\\\\")
	authmodulename=authmodulename.replace(".","\\\\.")
	authmodulename=authmodulename.replace("?","\\\\?")
	authmodulename=authmodulename.replace("+","\\\\+")
	authmodulename=authmodulename.replace("(","\\\\(")
	authmodulename=authmodulename.replace("*","\\\\*")
	authmodulename=authmodulename.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetAuthModule(authmoduleid,authmodulename,authmode,limitrow,offsetrow)
			sql = "select public.\"PGetAuthModule\"(%s,%s,%s,%s,%s,%s);" % (authmoduleid,authmodulename,authmode,num,paging,dsc)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除认证模块
@authmodule_change.route('/del_authmodule',methods=['GET', 'POST'])
def del_authmodule():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
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
			success_arr=[]
			fail_arr=[]
			all_arr=[]
			for id in ids:
				debug(str(id))
				id_arr=id.split('\t')
				all_arr.append(id_arr[1])
				sql='select a."AuthMode",a."UserObject" from public."AuthModule" a where a."AuthModuleId"=%s;'%id_arr[0]
				curs.execute(sql)
				result_AuthMode=curs.fetchall();
				if len(result_AuthMode)==0:
					AuthMode=0
					UserObject=""
				else:
					AuthMode=result_AuthMode[0][0]
					UserObject=result_AuthMode[0][1]
				sql = "select public.\"PDeleteAuthModule\"(%s);" % (id_arr[0])
				debug(str(sql))
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				debug(str(result_json))
				if not result_json['Result']:
					fail_num+=1
					fail_arr.append(id_arr[1])
					#return result
				elif result_json['RowCount']>0:
					success_num+=1
					success_arr.append(id_arr[1])
					conn.commit()
					if AuthMode==4:
                				##[global]
                				#class=taskauthmodule
                				#type=del_radius
                				#session=se
                				task_content = '[global]\nclass = taskauthmodule\ntype = del_radius_true\nid=%s\n' % (id_arr[0])
                				if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                        				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)	
					elif AuthMode==9:
						if UserObject!='' and UserObject!=None:
							task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/etc/%s\n' % (UserObject)
							if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
								return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)	
			oper='删除认证模块：%s'%('、'.join(all_arr))
			if (success_num+fail_num)==1:
				if success_num==1:
					mesg='成功'
				else:
					mesg=result_json['ErrMsg']
			else:
				if fail_num==0:
					mesg='成功'
					# mesg='成功：%s'%('、'.join(success_arr))
				else:
					mesg='成功：%s，失败：%s'%('、'.join(success_arr),'、'.join(fail_arr))
			if not system_log(system_user,oper,mesg,'运维管理>认证方式'):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
			return "{\"Result\":true,\"info\":\"删除成功\",\"fail_num\":%s,\"success_num\":%s,\"ErrMsg\":\"%s\"}"%(fail_num,success_num,mesg)
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s}"%(success_num,fail_num)
	except pyodbc.Error,e:
		if "foreign key" in str(e.args[1]):
			return "{\"Result\":false,\"ErrMsg\":\"模块已被占用\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
