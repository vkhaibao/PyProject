#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import MySQLdb
import json
import time

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionCheck
from htmlencode import parse_sess
from htmlencode import check_role
from ctypes import *
import htmlencode
from email_transmit import e_transmit
from index import PGetPermissions
from generating_log import system_log
from flask import Blueprint,request,render_template # 
mailserver = Blueprint('mailserver',__name__)
ERRNUM_MODULE = 2000
def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()

@mailserver.route('/mailserver_manage',methods=['GET', 'POST'])
def mailserver_manage():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	selectid = request.form.get('z3')
	if keyword == None:
		keyword = "[]"
	if selectid == None:
		selectid = "[]"
	
	if now and  str(now).isdigit() == False:
		return '',403
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
		
	
	sess = request.form.get('a0')
	if sess <0 or sess == '':
		sess = request.args.get('a0')
	if sess <0 or sess =='':
		sess ='';
	client_ip = request.remote_addr
	(error,us,mac) = SessionCheck(sess,client_ip)
	error_msg=''
	if error < 0:
		error_msg = "系统繁忙(%d)" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			error_msg = "非法访问"
		else:
			error_msg = "系统超时" 
	_power=PGetPermissions(us)
	_power=str(_power)
	_power_json = json.loads(_power);
	_power_mode = 2;
	for one in _power_json:
		if one['SystemMenuId'] == 6:
			_power_mode = one['Mode']
	return render_template('manage_mailserver.html',keyword=keyword,now=now,selectid=selectid,error_msg=error_msg,_power_mode=_power_mode);

@mailserver.route('/create_mailserver',methods=['GET', 'POST'])
def create_mailserver():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	edit = request.form.get('z3')
	selectid = request.form.get('z4')
	t = "create_mailserver.html"
	if selectid == None:
		selectid = "[]"
	if keyword == None:
		keyword = "[]"
	if now and  str(now).isdigit() == False:
		return '',403	
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
	#{"totalrow":1,"data":[{"Sender":"xuminjie@logbase.cn","SmtpConfigName":"xmj","Flag":2,"SenderEmail":"xuminjie@logbase.cn","SmtpConfigId":1,"DNS":null,"AttachMaxLimit":10hjltd(a)vh2we,"EnCode":0,"SmtpServer":"113.96.232.106","ServerVerify":true,"SenderEmailPass":"9QXhVWGveA9Lz4eR"}]}
	if edit != "None":
		try:
			edit_json = json.loads(edit);
			edit_id = edit_json['data'][0]['SmtpConfigId'];		
			if str(edit_id).isdigit() == False:
				return '',403 
		except:
			return '',403 
			
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				curs.execute("select public.\"PGetSmtpConfig\"(%d,%d,%d);"%(edit_id,10,0))
				edit = curs.fetchall()[0][0].encode('utf-8')
				edit_json = json.loads(edit);
				if edit_json['data'][0]['SenderEmailPass'] != None:
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
					pwd_rc4 = c_char_p()# 定义一个指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd(str(edit_json['data'][0]['SenderEmailPass']),pwd_rc4);#执行函数
					edit_json['data'][0]['SenderEmailPass'] = pwd_rc4.value #获取变量的值
				edit = json.dumps(edit_json);
				
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
		

	if edit != "None":
		return render_template(t,edit=edit,now=now,keyword=keyword,selectid=selectid)
	else:
		return render_template(t,edit='"None"',now=now,keyword=keyword,selectid=selectid)


##设备类型列表、过滤、分页
@mailserver.route('/get_mailserver_list',methods=['GET', 'POST'])
def get_mailserver_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	number = request.form.get('z1')
	curpage = request.form.get('z2')
	keyword = request.form.get('z3')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
			
	if keyword == None:
		keyword = "[]"
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
		
	if number and str(number).isdigit()	== False:
		return '',403
	if curpage and str(curpage).isdigit()	== False:
		return '',403
		
	number = int(number)
	curpage = int(curpage)
	if number < 0:
		number = 0
	if curpage < 0:
		curpage = 0
	row = number*(curpage-1)
	
	
	
	"""
	if keyword != "":
		keyword = json.loads(keyword);
		filter_name = ""
		filter_des = ""
		if len(keyword) != 0:
			for i in keyword:
				filter_arry = i.split('-',1)
				if filter_arry[0] == "名称":
					filter_name = filter_name + filter_arry[1] + '\n'
				if filter_arry[0] == "描述":
					filter_des = filter_des + filter_arry[1] + '\n'
			if filter_name != "":
				filter_name = filter_name[:-1]
			if filter_des != "":
				filter_des = filter_des[:-1]
			filter_name = filter_name.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
			filter_des = filter_des.replace("\\","\\\\\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		else:
			filter_name = ""
			filter_des = ""
	if filter_name != "":
		filter_name = "'%s'" % filter_name
	else:
		filter_name = "null"
	if filter_des != "":
		filter_des = "'%s'" % filter_des
	else:
		filter_des = "null"
		"""
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetSmtpConfig\"(null,%d,%d);"%(number,row))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))

###删除
@mailserver.route('/mailserver_delete',methods=['GET', 'POST'])
def mailserver_delete():
	type = request.form.get('z1')
	id = request.form.get('z2')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)

	if check_role(userCode,'系统管理') == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (ERRNUM_MODULE + 3)

	mail_title = "系统管理>输出设置>邮件"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"SmtpConfigName\" from public.\"SmtpConfig\" where \"SmtpConfigId\" in (%s)" % id[1:-1]
				curs.execute(sql)
				name_str = ""
				for row in curs.fetchall():
					name_str = name_str + row[0].encode('utf-8') + ","
					
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"SmtpConfigName\" from public.\"SmtpConfig\" where \"SmtpConfigId\"=%d" % int(id)
					curs.execute(sql)
					smtpname = curs.fetchall()[0][0].encode('utf-8')
					
					curs.execute("select public.\"PDeleteSmtpConfig\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除邮件：%s" % smtpname,"失败："+results['ErrMsg'],mail_title)
						return result
				
				if name_str != "":
					system_log(userCode,"删除邮件：%s" % name_str[:-1],"成功",mail_title)
				return "{\"Result\":true}"
			else:
				sql = "select \"SmtpConfigName\" from public.\"SmtpConfig\" where \"SmtpConfigId\"=%d" % int(id)
				curs.execute(sql)
				smtpname = curs.fetchall()[0][0].encode('utf-8')
				
				curs.execute("select public.\"PDeleteSmtpConfig\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				re_smtp = json.loads(results)
				if re_smtp['Result']:
					system_log(userCode,"删除邮件：%s" % smtpname,"成功",mail_title)
				else:
					system_log(userCode,"删除邮件：%s" % smtpname,"失败："+re_smtp['ErrMsg'],mail_title)
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
	
###保存
@mailserver.route('/save_mailserver',methods=['GET', 'POST'])
def save_mailserver():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	data = request.form.get('z1')
	session = request.form.get('a0')
	module_type = request.form.get('a10')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)

	if module_type == None or module_type == "":
		moudule_name = "系统管理"
	else:
		moudule_name = module_type.split('>')[1]

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	if check_role(userCode,moudule_name) == False:
			return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" %(sys._getframe().f_lineno)
	data = json.loads(data)
	if data['SenderEmailPass'] != None:
		if os.path.exists('/usr/lib64/logproxy.so') == False:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
		pwd_rc4 = c_char_p()# 定义一个指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd(str(data['SenderEmailPass']),pwd_rc4);#执行函数
		data['SenderEmailPass'] = pwd_rc4.value #获取变量的值
	save_data = json.dumps(data)
	save_data = MySQLdb.escape_string(save_data).decode("utf-8")
	if module_type == None or module_type == "":
		title = "系统管理>输出设置>邮件"
	else:
		title = module_type
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PSaveSmtpConfig\"(E'%s');"%(save_data))
			results = curs.fetchall()[0][0].encode('utf-8')
			
			re_smpt = json.loads(results)
			
			if data['SmtpServer'] != "" and data['SmtpServer'] != None:
				SmtpServer = "服务器地址：" + data['SmtpServer'] + '，'
			else:
				SmtpServer = ""
				
			if data['SenderEmail'] != "" and data['SenderEmail'] != None:
				SenderEmail = "发送邮箱地址：" + data['SenderEmail'] + '，'
			else:
				SenderEmail = ""
				
			if data['Sender'] != "" and data['Sender'] != None:
				Sender = "服务器账号：" + data['Sender'] + '，'
			else:
				Sender = ""
				
			if data['ServerVerify'] == True:
				ServerVerify = "服务器验证：是，"
			elif data['ServerVerify'] == False:
				ServerVerify = "服务器验证：否，"
			else:
				ServerVerify = ""
			
			if data['AttachMaxLimit'] != "" and data['AttachMaxLimit'] != None:
				AttachMaxLimit = "附件大小：" + str(data['AttachMaxLimit']) + '，'
			else:
				AttachMaxLimit = ""
			
			if data['EnCode'] == 0:
				EnCode = "编码方式：UTF-8，"
			elif data['EnCode'] == 1:
				EnCode = "编码方式：GBK，"
			else:
				EnCode = ""
				
			if data['Flag'] == 2:
				Flag = "方式：默认"
			elif data['Flag'] == 1:
				Flag = "方式：备用"
			else:
				Flag = "方式：其他"
				
			show_msg = SmtpServer + SenderEmail + Sender + ServerVerify + AttachMaxLimit + EnCode + Flag
	
			if re_smpt['Result']:
				if data['SmtpConfigId'] == 0:
					show_msg = "创建邮件：%s（%s）" % (data['SmtpConfigName'],show_msg)
					system_log(userCode,show_msg,"成功",title)
				else:
					show_msg = "编辑邮件：%s（%s）" % (data['SmtpConfigName'],show_msg)
					system_log(userCode,show_msg,"成功",title)
			else:
				if data['SmtpConfigId'] == 0:
					system_log(userCode,"创建邮件：%s" % data['SmtpConfigName'],"失败："+re_smpt['ErrMsg'],title)
				else:
					system_log(userCode,"编辑邮件：%s" % data['SmtpConfigName'],"失败："+re_smpt['ErrMsg'],title)
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d)\"}" %(ERRNUM_MODULE+11)

@mailserver.route('/select_mailserver_all',methods=['GET', 'POST'])
def select_mailserver_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id = request.form.get('z1')
	if id and id !='-1' and str(id).isdigit()	== False:
		return '',403
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if id != '-1':
				curs.execute("select public.\"PGetSmtpConfig\"(%d,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetSmtpConfig\"(null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			data = json.loads(results)
			if id != '-1' and data['data'][0]['SenderEmailPass'] != None:
				if os.path.exists('/usr/lib64/logproxy.so') == False:
					return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
				lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
				pwd_rc4 = c_char_p()# 定义一个指针
				lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
				lib.decrypt_pwd.restype = None #定义函数返回值
				pwd_rc4.value = "0"*512 # 初始化 指针
				lib.decrypt_pwd(str(data['data'][0]['SenderEmailPass']),pwd_rc4);#执行函数
				data['data'][0]['SenderEmailPass'] = pwd_rc4.value #获取变量的值
			results = json.dumps(data)
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d)\"}" % (ERRNUM_MODULE + 3)
		
@mailserver.route('/get_mail_flag',methods=['GET', 'POST'])
def get_mail_flag():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
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
			sql = "select count(*) from \"SmtpConfig\""
			curs.execute(sql)
			count_mail = curs.fetchall()[0][0]
			sql = "select count(*) from \"SmtpConfig\" where \"Flag\" = 2"
			curs.execute(sql)
			def_mail = curs.fetchall()[0][0]
			sql = "select count(*) from \"SmtpConfig\" where \"Flag\" = 1"
			curs.execute(sql)
			spare_mail = curs.fetchall()[0][0]
			return "{\"Result\":true,\"count_mail\":%s,\"def_mail\":%s,\"spare_mail\":%s}" % (count_mail,def_mail,spare_mail)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@mailserver.route('/test_mail',methods=['GET', 'POST'])
def test_mail():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	_server = request.form.get('z1')
	_user = request.form.get('z2')
	_pwd = request.form.get('z3')
	_to = request.form.get('z4')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip)
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	result = e_transmit(_server,_user,_pwd,_to,"测试邮件","查收测试邮件")
	if result == 0:
		return "{\"Result\":true}"
	elif result == 1:
		return "{\"Result\":false,\"ErrMsg\":\"服务器错误(%d)\"}" %(sys._getframe().f_lineno)
	elif result == 2:
		return "{\"Result\":false,\"ErrMsg\":\"账号或密码错误(%d)\"}" %(sys._getframe().f_lineno)
	elif result == 3:
		return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
	elif result == 4:
		return "{\"Result\":false,\"ErrMsg\":\"发送超时\"}"
	
