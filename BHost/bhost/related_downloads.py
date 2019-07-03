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
from logbase import defines
from logbase import task_client
from htmlencode import parse_sess,check_role
from generating_log import system_log

from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
related_downloads = Blueprint('related_downloads',__name__)
UPLOAD_FOLDER_IMG = '/var/www/manage/html/images/software/'
UPLOAD_FOLDER = '/usr/storage/.system/software/upload/'
UPLOAD_PATH = '/usr/storage/.system/upload/'

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0;
	path = "/var/tmp/debugrelated_downloads.txt"
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

#1创建 2编辑 3列表
@related_downloads.route('/related_downloads_show',methods=['GET','POST'])
def related_downloads_show():
	se = request.form.get("a0")
	if se == None:
		se = request.args.get("a0")
	
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
	
	tasktype=request.form.get("tasktype")
	if tasktype==None:
		tasktype = request.args.get('tasktype')
		
	if( str(tasktype) !=None and str(tasktype).isdigit() == False):
		return '',403 
	
	from_flag = request.form.get("s1")
	
	if from_flag< 0 or from_flag =='':
		from_flag = request.args.get("s1")
		if from_flag< 0 or from_flag =='':
			from_flag = "from_access"
			
	if from_flag !='from_access' and from_flag!='from_system':
		return '',403
	
	t = "related_downloads.html"
	
	##获取 上传的文件
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"img_class\",\"software_name\",\"id\" from public.\"SoftwareUpload\" order by id;";
			debug(sql);
			curs.execute(sql)
			result_tmp = curs.fetchall();
			res_str = '';
			for res in result_tmp:
				res_str += '{"id":%d,"img_class":"%s","software_name":"%s"},'%(res[2],res[0].encode('utf-8'),res[1].encode('utf-8'))
			res_str = res_str[:-1]
			default_str = "[%s]" %(res_str)
	except pyodbc.Error,e:
		default_str = '[]'
	return render_template(t,se=se,tasktype=tasktype,default_str=default_str,from_flag=from_flag)

@related_downloads.route('/exist_download_jre_exe',methods=['GET','POST'])
def exist_download_jre_exe():
	se = request.form.get("a0")
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
        if os.path.exists('/usr/storage/.system/software/jre-8u161-windows-x64.exe'):
                return '{\"Result\":true}'
        else:
                return '{\"Result\":false,"ErrMsg":"文件不存在"}'

@related_downloads.route('/download_jre_exe',methods=['GET','POST'])
def download_jre_exe():
	name = 'jre-8u161-windows-x64.exe'
        down_dir = '/usr/storage/.system/software/';
	return send_from_directory(down_dir,name,as_attachment=True,attachment_filename='jre-windows-x64.exe')

@related_downloads.route('/exist_download_pwdfile',methods=['GET','POST'])
def exist_download_pwdfile():
        se = request.form.get("a0")
	pwdfile=request.form.get("a1")
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
	#pwdfile_arr=pwdfile.split('_')
	#pwdfile=pwdfile_arr[0]+'_'+system_user+'_'+pwdfile_arr[-1]
        #if os.path.exists('/usr/storage/.system/passwd/'+pwdfile):
        if os.path.exists('/usr/storage/.system/passwd/'+pwdfile.split('/')[-1]):
                return '{\"Result\":true}'
        else:
                return '{\"Result\":false,"ErrMsg":"文件不存在"}'

@related_downloads.route('/download_pwdfile',methods=['GET','POST'])
def download_pwdfile():
        #name = 'jre-8u161-windows-x64.exe'
	se = request.form.get("a0")
	if se <0:
		se=request.args.get("a0")
	pwdfile=request.form.get("a1")
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
	if pwdfile<0:
		pwdfile=request.args.get("a1")
        down_dir = '/usr/storage/.system/passwd/';
	pwdfile=pwdfile.split('/')[-1]
	pwdfile_arr=pwdfile.split('_')
	#pwdfile=pwdfile_arr[0]+'_'+system_user+'_'+pwdfile_arr[-1]
	pwdfile_arr[-1]='.pwd'
	newpwdfile=pwdfile_arr[0]+'_'+system_user+pwdfile_arr[-1]
        return send_from_directory(down_dir,pwdfile,as_attachment=True,attachment_filename=newpwdfile)
@related_downloads.route('/exist_download_python_exe',methods=['GET','POST'])
def exist_download_python_exe():
        se = request.form.get("a0")
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
        if os.path.exists('/usr/storage/.system/software/python-2.7.14.msi'):
                return '{\"Result\":true}'
        else:
                return '{\"Result\":false,"ErrMsg":"文件不存在"}'
@related_downloads.route('/download_python_exe',methods=['GET','POST'])
def download_python_exe():
        name = 'python-2.7.14.msi'
        down_dir = '/usr/storage/.system/software/';
        return send_from_directory(down_dir,name,as_attachment=True,attachment_filename='python-2.7.msi')
@related_downloads.route('/exist_download_ShowPasswd_exe',methods=['GET','POST'])
def exist_download_ShowPasswd_exe():
        se = request.form.get("a0")
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
        if os.path.exists('/usr/storage/.system/software/ShowPasswd.exe'):
                return '{\"Result\":true}'
        else:
                return '{\"Result\":false,"ErrMsg":"文件不存在"}'
@related_downloads.route('/download_ShowPasswd_exe',methods=['GET','POST'])
def download_ShowPasswd_exe():
        name = 'ShowPasswd.exe'
        down_dir = '/usr/storage/.system/software/';
        return send_from_directory(down_dir,name,as_attachment=True,attachment_filename='ShowPasswd.exe')
@related_downloads.route('/exist_download_BHostClient_exe',methods=['GET','POST'])
def exist_download_BHostClient_exe():
	if os.path.exists('/usr/storage/.system/software/BHostClient.exe'):
		UserCode = request.form.get("a1")
		if UserCode <0 or UserCode == '':
			pass
		else:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				now = int(time.time())
				timeArray = time.localtime(now)
				LastLoginTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
				sql='update "User" set "LastLoginTime"=\'%s\'  where "UserCode" = \'%s\';'%(LastLoginTime,UserCode)
				debug(sql)
				curs.execute(sql)
				conn.commit();
		return '{\"Result\":true}'
	else:
		return '{\"Result\":false,"ErrMsg":"文件不存在"}'

@related_downloads.route('/download_BHostClient_exe',methods=['GET','POST'])
def download_BHostClient_exe():
        name = 'BHostClient.exe'
        down_dir = '/usr/storage/.system/software/';
        return send_from_directory(down_dir,name,as_attachment=True,attachment_filename='BHostClient.exe')

@related_downloads.route('/exist_download_BHostReplay_exe',methods=['GET','POST'])
def exist_download_BHostReplay_exe():
        se = request.form.get("a0")
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
	if os.path.exists('/usr/storage/.system/software/BHostReplay.exe'):
		# UserCode = request.form.get("a1")
		# if UserCode <0 or UserCode == '':
		# 	pass
		# else:
		# 	with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
		# 		curs = conn.cursor()
		# 		now = int(time.time())
		# 		timeArray = time.localtime(now)
		# 		LastLoginTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
		# 		sql='update "User" set "LastLoginTime"=\'%s\'  where "UserCode" = \'%s\';'%(LastLoginTime,UserCode)
		# 		debug(sql)
		# 		curs.execute(sql)
		# 		conn.commit();
		return '{\"Result\":true}'
	else:
		return '{\"Result\":false,"ErrMsg":"文件不存在"}'

@related_downloads.route('/download_BHostReplay_exe',methods=['GET','POST'])
def download_BHostReplay_exe():
        name = 'BHostReplay.exe'
        down_dir = '/usr/storage/.system/software/';
        return send_from_directory(down_dir,name,as_attachment=True,attachment_filename='BHostReplay.exe')

@related_downloads.route('/exist_download_crt',methods=['GET','POST'])
def exist_download_crt():
	se = request.form.get("a0")
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
	if os.path.exists('/usr/ssl/certs/ca.crt'):
		return '{\"Result\":true}'
		#return '111'
		#return send_from_directory('/usr/etc','server.crt',as_attachment=True)
	else:
		return '{\"Result\":false,"ErrMsg":"文件不存在"}'
		
@related_downloads.route('/download_chrome_exe',methods=['GET','POST'])
def download_chrome_exe():
	typ = request.args.get("t1")
	if typ < 0 or typ == "":
		typ = 'Win7'
	if typ == 'Win7':		
		name = 'ChromeSetup.exe'
	elif typ=="WinXP":
		name = 'ChromeInstaller.exe'
	else:
		return "<script>未知类型</script>"
		
	down_dir = '/usr/storage/.system/software/';
	return send_from_directory(down_dir,name,as_attachment=True)
	
@related_downloads.route('/SoftwareUpdate',methods=['GET','POST'])
def SoftwareUpdate():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
	
	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	software_name = request.form.get('z1');
	software_spath = request.form.get('z2');
	software_path_tmp = request.form.get('z3');
	img_class =request.form.get('z4');
	same_file_id =request.form.get('z5');
	oper = '上传软件：'+software_name;
	if same_file_id < 0 or same_file_id =='':
		same_file_id = 0;
	else:
		same_file_id = int(same_file_id)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if same_file_id ==0:
				sql = "insert into public.\"SoftwareUpload\"(\"img_class\",\"software_name\") values(E'%s',E'%s') " % (MySQLdb.escape_string(img_class).decode('utf-8'),MySQLdb.escape_string(software_name).decode('utf-8'));
				debug(sql);
				curs.execute(sql)
			else:
				sql = "update public.\"SoftwareUpload\" set \"img_class\"=E'%s' where \"id\" = %d; " % (MySQLdb.escape_string(img_class).decode('utf-8'),same_file_id);
				debug(sql);
				curs.execute(sql)
			###下发任务
			content = "[global]\nclass = taskglobal\ntype = cp_file\ndpath=%s\nspath=%s\n" %(UPLOAD_FOLDER+software_name,UPLOAD_PATH+software_spath)
			debug(content);
			ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
			if ss == False:
				if not system_log(userCode,oper,"系统异常: %s(%d)" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno),"相关下载"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
				
			content = "[global]\nclass = taskglobal\ntype = delfile\npath=%s\n" %(software_path_tmp)
			debug(content);
			ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
			if ss == False:
				if not system_log(userCode,oper,"系统异常: %s(%d)" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno),"相关下载"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
				
			if not system_log(userCode,oper,"成功","相关下载"):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true}"	
	except pyodbc.Error,e:
		if not system_log(userCode,oper,"系统异常: %s(%d)" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno),"相关下载"):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
		
@related_downloads.route('/download_default_file',methods=['GET','POST'])
def download_default_file():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
	
	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	id = request.form.get('a1');
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"software_name\" from public.\"SoftwareUpload\" where \"id\"=%s;" %(id);
			debug(sql);
			curs.execute(sql)
			result_tmp = curs.fetchall();
			if not result_tmp:
				return "{\"Result\":false,\"ErrMsg\":\"文件不存在(%d)\"}" % (sys._getframe().f_lineno)
			software_name = result_tmp[0][0].decode('utf-8');
			return "{\"Result\":true,\"software_name\":\"%s\"}" %(software_name)	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
@related_downloads.route('/del_default_file',methods=['GET','POST'])
def del_default_file():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
	
	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	
	id = request.form.get('a1');
	oper ='';
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"software_name\" from public.\"SoftwareUpload\" where \"id\"=%s;" %(id);
			debug(sql);
			curs.execute(sql)
			result_tmp = curs.fetchall();
			if not result_tmp:
				if not system_log(userCode,oper,"文件不存在(%d)" % (sys._getframe().f_lineno),"相关下载"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"文件不存在(%d)\"}" % (sys._getframe().f_lineno)
			software_name = result_tmp[0][0].decode('utf-8');
			oper = '删除软件：' +software_name
			sql = "delete from public.\"SoftwareUpload\" where \"id\"=%s;" %(id);
			curs.execute(sql)
			
			content = "[global]\nclass = taskglobal\ntype = delfile\npath=%s\n" %(UPLOAD_FOLDER + software_name)
			debug(content);
			ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
			if ss == False:
				if not system_log(userCode,oper,"系统异常: %s(%d)" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno),"相关下载"):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(ErrorEncode(task_client.err_msg),sys._getframe().f_lineno)
				
			if not system_log(userCode,oper,"成功","相关下载"):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				
			return "{\"Result\":true}"	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
		
@related_downloads.route('/same_file',methods=['GET','POST'])
def same_file():
	reload(sys)
	sys.setdefaultencoding('utf-8')
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
	
	if check_role(userCode,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)	
	
	software_name = request.form.get('a1');	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()	
			sql ='select "id" from public."SoftwareUpload" where "software_name"=E\'%s\';' %(MySQLdb.escape_string(software_name).decode('utf-8'))
			curs.execute(sql)
			result_tmp = curs.fetchall();
			if not result_tmp:
				return "{\"Result\":false,\"id\":0}"			
			return "{\"Result\":true,\"id\":%d}" %(result_tmp[0][0])	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	
