#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import MySQLdb
import json
import time
import socket
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionCheck
from htmlencode import parse_sess
from htmlencode import check_role
import htmlencode
import shutil
from ctypes import *
#from ftp_transmit import f_transmit
from ftplib import FTP
from index import PGetPermissions
from generating_log import system_log
from flask import Blueprint,request,render_template # 
import traceback
ftpserver = Blueprint('ftpserver',__name__)
ERRNUM_MODULE = 2000
reload(sys)
sys.setdefaultencoding('utf-8')

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

def f_upload(host, username, password,remotepath):
	try:
		timeout=5 # in seconds 
		socket.setdefaulttimeout(timeout)
		ftp = FTP()
		index = host.find(':')
		port = 21
		if index != -1 :
			port = host[index + 1:]
			host = host[0 : index]
		ftp.connect(host, port)
		ftp.login(username, password)
	except (socket.error,socket.gaierror,Exception),e:
		#print '{\"Result\":false,\"ErrMsg\":\"账号或密码错误\"}'
		return 1
	try:
		#print os.getcwd() #显示当前工作路径
		bufsize = 1024
		filepath = '/var/tmp/test.txt'
		try:
			with open(filepath, 'wb') as fp1:
				fp1.write("测试文件")
				fp1.flush()
				fp1.close()
		except IOError as err:
			#print "{\"Result\":false,\"ErrMsg\":\"文件打开失败\"}"
			return 2
		try:
			fp = open(filepath, 'rb')
		except:
			#print '{\"Result\":false,\"ErrMsg\":\"系统异常：（打开文件失败）\"}'
			return 2
		ftp.storbinary('STOR ' + remotepath, fp, bufsize)
		ftp.set_debuglevel(0)
		ftp.delete(remotepath)
		fp.close()
		return 0
	except:
		#print traceback.format_exc();
		#print '{\"Result\":false,\"ErrMsg\":\"发送异常\"}'
		return 3

def f_transmit(host, username, password, remotepath = "/"):
	try:
		ftp = FTP()
		ftp.connect(host, 21)
		ftp.login(username, password)
	except:
		print '{\"Result\":false,\"ErrMsg\":\"账号或密码错误\"}'
		return 1
	try:
		ftp.cwd(remotepath)
		ftp.set_debuglevel(0)
		return 0
	except:
		#print traceback.format_exc();
		#print '{\"Result\":false,\"ErrMsg\":\"发送异常\"}'
		return 3
		
@ftpserver.route('/manage_ftp',methods=['GET', 'POST'])
def manage_ftp():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	selectid = request.form.get('z3')
	if keyword == None:
		keyword = "[]"
	if selectid == None:
		selectid = "[]"
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
			
	_power=PGetPermissions(us)
	_power_json = json.loads(str(_power));
	_power_mode = 2;
	for one in _power_json:
		if one['SystemMenuId'] == 6:
			_power_mode = one['Mode']
	return render_template('manage_ftpserver.html',keyword=keyword,now=now,selectid=selectid,error_msg=error_msg,_power_mode=_power_mode);

@ftpserver.route('/create_ftp',methods=['GET', 'POST'])
def create_ftp():
	now = request.form.get('z1')
	keyword = request.form.get('z2')
	edit = request.form.get('z3')
	selectid = request.form.get('z4')
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
	t = "create_ftp.html"
	if edit != "None":
		try:
			edit_json = json.loads(edit);
			edit_id = edit_json['data'][0]['FTPServerId'];		
			if str(edit_id).isdigit() == False:
				return '',403 
		except:
			return '',403 
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				sql = "select public.\"PGetFTPServer\"(%s,null,%s,%s);"%(edit_id,10,0)
				curs.execute(sql)
				results = curs.fetchall()[0][0].encode('utf-8')
				data = json.loads(results)
				if os.path.exists('/usr/lib64/logproxy.so') == False:
					return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
				lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
				pwd_rc4 = c_char_p()# 定义一个指针
				lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
				lib.decrypt_pwd.restype = None #定义函数返回值
				pwd_rc4.value = "0"*512 # 初始化 指针
				lib.decrypt_pwd(str(data['data'][0]['ServerPasswd']),pwd_rc4);
				#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
				data['data'][0]['ServerPasswd'] = pwd_rc4.value #获取变量的值
				edit = json.dumps(data, encoding='utf-8')
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
		return render_template(t,edit=edit,now=now,keyword=keyword,selectid=selectid)
	else:
		return render_template(t,edit='"None"',now=now,keyword=keyword,selectid=selectid)


@ftpserver.route('/get_ftp_list',methods=['GET', 'POST'])
def get_ftp_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	number = request.form.get('z1')
	curpage = request.form.get('z2')
	keyword = request.form.get('z3')
	ftpserverid = request.form.get('z4')
	
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
	if number == None:
		number = "null"
	else:
		if int(number) < 0:
			number = 0
	if curpage == None:
		curpage = "null"
	else:
		if int(curpage) < 0:
			curpage = 0
	if number != "null" and curpage != "null":
		row = int(number)*(int(curpage)-1)
	else:
		row = "null"
	if ftpserverid == None:
		ftpserverid = "null"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetFTPServer\"(%s,null,%s,%s);"%(ftpserverid,number,row)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			if ftpserverid != "null":
				data = json.loads(results)
				if os.path.exists('/usr/lib64/logproxy.so') == False:
					return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
				lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
				pwd_rc4 = c_char_p()# 定义一个指针
				lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
				lib.decrypt_pwd.restype = None #定义函数返回值
				pwd_rc4.value = "0"*512 # 初始化 指针
				lib.decrypt_pwd(str(data['data'][0]['ServerPasswd']),pwd_rc4);
				#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
				data['data'][0]['ServerPasswd'] = pwd_rc4.value #获取变量的值
				results = json.dumps(data, encoding='utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###删除
@ftpserver.route('/ftp_delete',methods=['GET', 'POST'])
def ftp_delete():
	type = request.form.get('z1')
	id = request.form.get('z2')
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

	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	ftp_title = "系统管理>输出设置>FTP"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"FTPServerName\" from public.\"FTPServer\" where \"FTPServerId\" in (%s)" % id[1:-1]
				curs.execute(sql)
				name_str = ""
				for row in curs.fetchall():
					name_str = name_str + row[0].encode('utf-8') + ","
					
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"FTPServerName\" from public.\"FTPServer\" where \"FTPServerId\" in (%d)" % int(id)
					curs.execute(sql)
					ftpname = curs.fetchall()[0][0].encode('utf-8')
					
					curs.execute("select public.\"PDeleteFTPServer\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除FTP：%s" % ftpname,"失败："+results['ErrMsg'],ftp_title)
						conn.rollback()
						return result
				if name_str != "":
					system_log(userCode,"删除FTP：%s" % name_str[:-1],"成功",ftp_title)
				return "{\"Result\":true}"
			else:
				sql = "select \"FTPServerName\" from public.\"FTPServer\" where \"FTPServerId\"=%d" % int(id)
				curs.execute(sql)
				ftpname = curs.fetchall()[0][0].encode('utf-8')
				
				curs.execute("select public.\"PDeleteFTPServer\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')

				re_ftp = json.loads(results)
				
				if re_ftp['Result']:
					system_log(userCode,"删除FTP：%s" % ftpname,"成功",ftp_title)
				else:
					system_log(userCode,"删除FTP：%s" % ftpname,"失败："+re_ftp['ErrMsg'],ftp_title)
				
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
###保存
@ftpserver.route('/save_ftp',methods=['GET', 'POST'])
def save_ftp():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	data = request.form.get('z1')
	pwd_flag = request.form.get('z2')
	module_type = request.form.get('a10')
	md5_str = request.form.get('m1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)

	ftpserver_json = json.loads(data)
	
	#if pwd_flag == '0':#不同
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"info\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	ret = lib.encrypt_pwd(ftpserver_json['ServerPasswd'],pwd_rc4);#执行函数
	ftpserver_json['ServerPasswd'] = pwd_rc4.value #获取变量的值
	data = json.dumps(ftpserver_json)
	if module_type == None or module_type == "":
		title = "系统管理>输出设置>FTP"
	else:
		title = module_type
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PSaveFTPServer\"(E'%s');"%(MySQLdb.escape_string(data).decode("utf-8")))
			results = curs.fetchall()[0][0].encode('utf-8')
			re_ftp = json.loads(results)
			
			#{"FTPServerId":1,"FTPServerName":"151","ServerIP":"192.168.0.151","DNS":null,"ServerUser":"administrator","ServerPasswd":"12345678","ServerPath":"/","Flag":2,"IfPasv":true}
			if ftpserver_json['ServerIP'] != "" and ftpserver_json['ServerIP'] != None:
				ServerIP = "服务器地址：" + ftpserver_json['ServerIP'] + '，'
			else:
				ServerIP = ""
			
			if ftpserver_json['ServerUser'] != "" and ftpserver_json['ServerUser'] != None:
				ServerUser = "用户名：" + ftpserver_json['ServerUser'] + '，'
			else:
				ServerUser = ""
			
			if ftpserver_json['ServerPath'] != "" and ftpserver_json['ServerPath'] != None:
				ServerPath = "上传路径：" + ftpserver_json['ServerPath'] + '，'
			else:
				ServerPath = ""
			
			if ftpserver_json['Flag'] == 2:
				Flag = "方式：默认，"
			elif ftpserver_json['Flag'] == 1:
				Flag = "方式：备用，"
			else:
				Flag = "方式：其他，"
				
			if ftpserver_json['IfPasv'] == True:
				IfPasv = "模式：被动"
			else:
				IfPasv = "模式：主动"
			
			show_msg = ServerIP + ServerUser + ServerPath + Flag + IfPasv
			
			if re_ftp['Result']:
				if int(ftpserver_json['FTPServerId']) == 0:
					show_msg = "创建FTP：%s（%s）" % (ftpserver_json['FTPServerName'],show_msg)
					system_log(userCode,show_msg,"成功",title)
				else:
					show_msg = "编辑FTP：%s（%s）" % (ftpserver_json['FTPServerName'],show_msg)
					system_log(userCode,show_msg,"成功",title)
			else:
				if int(ftpserver_json['FTPServerId']) == 0:
					system_log(userCode,"创建FTP：%s" % ftpname,"失败："+re_ftp['ErrMsg'],title)
				else:
					system_log(userCode,"编辑FTP：%s" % ftpname,"失败："+re_ftp['ErrMsg'],title)
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
@ftpserver.route('/get_ftp_flag',methods=['GET', 'POST'])
def get_ftp_flag():
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
			sql = "select count(*) from \"FTPServer\""
			curs.execute(sql)
			count_ftp = curs.fetchall()[0][0]
			sql = "select count(*) from \"FTPServer\" where \"Flag\" = 2"
			curs.execute(sql)
			def_ftp = curs.fetchall()[0][0]
			sql = "select count(*) from \"FTPServer\" where \"Flag\" = 1"
			curs.execute(sql)
			spare_ftp = curs.fetchall()[0][0]
			return "{\"Result\":true,\"count_ftp\":%s,\"def_ftp\":%s,\"spare_ftp\":%s}" % (count_ftp,def_ftp,spare_ftp)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

#主机 账号 密码 本地路径 远程路径 
@ftpserver.route('/test_ftp',methods=['GET', 'POST'])
def test_ftp():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	host = request.form.get('z1')
	username = request.form.get('z2')
	password = request.form.get('z3')
	remotepath = request.form.get('z4')
	
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	'''
	filepath = '/var/www/manage/bhost/test.txt'
	try:
		with open(filepath, 'wb') as fp:
			fp.write("测试文件")
			fp.flush()
			fp.close()
	except IOError as err:
		return "{\"Result\":false,\"ErrMsg\":\"文件打开失败\"}"
	'''
	remotepath = remotepath + '/test.txt'
	result = f_upload(host,username,password,remotepath)
	#result = f_transmit(host,username,password,remotepath)
	#task_content = '[global]\nclass = tasktest_output\ntype = execute_cmd_ftp\nhost=\"%s\"\nuser=\"%s\"\npwd=\"%s\"se=\"%s\"\n' % (host,username,password,session)
	
	if result == 0:
		return "{\"Result\":true}"
	elif result == 1:
		return "{\"Result\":false,\"ErrMsg\":\"连接失败(%d)\"}" %(sys._getframe().f_lineno)
	elif result == 2:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif result == 3:
		return "{\"Result\":false,\"ErrMsg\":\"发送异常(%d)\"}" %(sys._getframe().f_lineno)
