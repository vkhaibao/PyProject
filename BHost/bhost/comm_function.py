#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import cgi
import cgitb
import re
import pyodbc
import MySQLdb
import json
import time
import stat
import thread
import socket
import binascii
import ConfigParser
import smtplib
import signal
from urllib import unquote
from comm import SessionCheck,LogSet,SessionLogin,StrSqlConn,StrMD5
from logbase import common,task_client,defines
from ctypes import *
from struct import pack
from flask import Flask,Blueprint,request,session,render_template,send_from_directory # 
from jinja2 import Environment,FileSystemLoader 

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from ftplib import FTP

def debug(c):
	return 0
        path = "/var/tmp/debugcomm_function.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()

#email发送函数
def e_transmit(_server, _user, _pwd, _to, file): 
	#创建一个带附件的实例
	try:
		socket.setdefaulttimeout(5) 
		message = MIMEMultipart()
		message['From'] = Header(_user, 'utf-8')       #邮件发送者
		message['To'] =  Header(_to, 'utf-8')          #邮件接收者
		#邮件主题
		msg_sub='发送导出文件'
		message['Subject'] = Header(msg_sub, 'utf-8')  
		#邮件正文内容
		msg_text='发送导出文件，请注意查收'
		message.attach(MIMEText(msg_text, 'plain', 'utf-8'))
		# 构造附件1，传送当前目录下的 test.txt 文件
		att1 = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
		att1["Content-Type"] = 'application/octet-stream'
		# 这里的 filename 可以任意写，写什么名字，邮件中显示什么名字
		f_name=file[file.rfind("/")+1: ]
		att1["Content-Disposition"] = 'attachment; filename= '+f_name #自动追踪文件名字
		message.attach(att1)
		try:
			s = smtplib.SMTP_SSL(_server, 465) #端口用465，不可用默认端口25
		except Exception,e:
			#发送失败
			return (-2,"邮件服务器错误")
		try:
			s.login(_user, _pwd)
		except smtplib.SMTPException,e:
			return (-2,"邮件账号或密码错误")
		try:
			s.sendmail(_user, _to, message.as_string())
		except smtplib.SMTPException,e:
			return (-2,"邮件被拦截")
		s.quit()
	except socket.timeout as e:  
		return (-2,"邮件发送超时")  
	return (0,0)


#ftp发送函数
#主机 账号 密码 本地路径 远程路径 
def f_transmit(host, username, password, localpath, remotepath = "/"):
	file = localpath[localpath.rfind("/")+1: ]
	d_path = remotepath[ :remotepath.rfind("/")+1]
	d_path1 = remotepath[ remotepath.rfind("/")+1: ]
	if d_path1.rfind(".") < 1:
		d_path = remotepath + "/"
		if remotepath == "/":
			d_path = remotepath
	# debug('d_path')
	# debug(str(d_path))
	socket.setdefaulttimeout(5) 
	try:
		ftp = FTP()
		ftp.connect(host, 21)
		ftp.login(username, password)
	except:
		return (-1,"FTP服务器账号或密码错误") 
		return -1
	try:
		bufsize = 1024
		try:
			fp = open(localpath, 'rb')
		except:
			#打开文件失败
			return (-2,"FTP服务器打开文件失败") 
			return -2
		ftp.storbinary('STOR ' + d_path + file, fp, bufsize)
		ftp.set_debuglevel(0)
		fp.close()
		return (0,0)
	except:
		#发送异常
		return (-3,"FTP服务器未找到目标文件")
		return -3


#解密
def decrypt_pwd(passwork,pwd_rc4_value='0'*512):
	debug('decrypt_pwd')
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return (-1,"系统繁忙")
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = pwd_rc4_value # 初始化 指针
	lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.decrypt_pwd.restype = None #定义函数返回值
	ret = lib.decrypt_pwd(passwork,pwd_rc4);#执行函数
	return (0,pwd_rc4.value)

def encrypt_pwd_make_file(user,str_write,path,module):
	#SELECT * FROM public.\"GetEncryptPwd\"('%s')
	debug('encrypt_pwd_make_file')
	debug(module)
	'''
	if module!='密码导出':
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql_pwd_all="SELECT * FROM public.\"GetEncryptPwd\"('%s')"%user
				debug(str(sql_pwd_all))
				curs.execute(sql_pwd_all)
				passwork_all = curs.fetchall()
				debug(str(passwork_all))
				passwork=passwork_all[0][0]
				debug(str(passwork))
				(error,passwork_decrypt)=decrypt_pwd(passwork)
				debug(str(passwork_decrypt))
				if error<0:
					return (error,passwork_decrypt)
				passwork1=passwork_all[0][1]
				debug(str(passwork1))
				debug('----')
				if passwork1==None:
					passwork_decrypt_all=passwork_decrypt
				else:
					(error,passwork1_decrypt)=decrypt_pwd(passwork1)
					debug(str(passwork1_decrypt))
					if error<0:
						return (error,passwork1_decrypt)
					else:
						passwork_decrypt_all=passwork_decrypt+passwork1_decrypt
		except pyodbc.Error,e:
			return (-1,"系统繁忙")
	else:
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql_login='select "Password" from public."User" where "UserCode"=\'%s\';'%user
				debug(str(sql_login))
				curs.execute(sql_login)
				result_login=curs.fetchall()
			if len(result_login)!=0 and result_login[0][0]!=None:
				(error,passwork_login)=decrypt_pwd(result_login[0][0])	
				if error<0:
                                        return (error,passwork_login)
			else:
				passwork_login=''
			debug(str(passwork_login))
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
                                sql_hp='select hp."Password" from public."User" u,public."HostPwdStrategy" hp where u."UserCode"=\'%s\' and u."UserId"=hp."UserId";'%user
				debug(str(sql_hp))
                                curs.execute(sql_hp)
                                result_hp=curs.fetchall()	
			if len(result_hp)!=0 and result_hp[0][0]!=None:
				(error,passwork_hp)=decrypt_pwd(result_hp[0][0])  
				if error<0:
					return (error,passwork_hp)
			else:
				passwork_hp=''
			debug(passwork_hp)
			passwork_decrypt_all=passwork_login+passwork_hp
		except pyodbc.Error,e:
                        return (-1,"系统繁忙")
	'''
	try:
        	with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
                	sql_login='select "Password" from public."User" where "UserCode"=\'%s\';'%user
                  	debug(str(sql_login))
                   	curs.execute(sql_login)
                    	result_login=curs.fetchall()
          	if len(result_login)!=0 and result_login[0][0]!=None:
                   	(error,passwork_login)=decrypt_pwd(result_login[0][0])  
                   	if error<0:
                         	return (error,passwork_login)
            	else:
                 	passwork_login=''
           	debug(str(passwork_login))
           	with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
                  	sql_hp='select hp."Password" from public."User" u,public."HostPwdStrategy" hp where u."UserCode"=\'%s\' and u."UserId"=hp."UserId";'%user
                     	debug(str(sql_hp))
                     	curs.execute(sql_hp)
                    	result_hp=curs.fetchall()       
          	if len(result_hp)!=0 and result_hp[0][0]!=None:
                     	(error,passwork_hp)=decrypt_pwd(result_hp[0][0])  
                    	if error<0:
                          	return (error,passwork_hp)
            	else:
                   	passwork_hp=''
          	debug(passwork_hp)
            	passwork_decrypt_all=passwork_login+passwork_hp
    	except pyodbc.Error,e:
           	return (-1,"系统繁忙")
	debug('------')
	debug(str(passwork_decrypt_all))
	with open(path,'wb+') as f:
		f.truncate()
	str_write=str_write.encode('gbk')
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return (-1,"系统繁忙")
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_p=c_char_p()
	pwd_p.value=str(passwork_decrypt_all)
	msg_p=c_char_p()
	msg_p.value=str(str_write)
	filedir=c_char_p()
	filedir.value=str(path)
	lib.pw_write_file.argtypes = [c_char_p,c_char_p,c_char_p]; #定义函数参数
	lib.pw_write_file.restype =  c_int#定义函数返回值
	ret = lib.pw_write_file(pwd_p,msg_p,filedir)#执行函数
	if ret!=0:
		return (-2,"系统异常：（文件加密失败）")
	return (ret,path)

def get_user_perm_value(us):
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			debug(str(sql))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			debug(str(result))
			if result==None:
				result='[]'
			return result
	except pyodbc.Error,e:
		debug(str(e))
		return "[]"
		return str(result)

def del_file_while_user_del(us):
	reload(sys)
        sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
                        sql="select log.\"FileName\" from private.\"LogBackupTask\" log where log.\"UserId\"=%s;" %(us)
                        debug(str(sql))
                        curs.execute(sql)
                        result = curs.fetchall()
                        debug(str(result))
			for i in result:
				debug(str(i))
				debug(str(i[0]))
				if i[0]!='' and i[0]!=None and os.path.exists(i[0]):
					debug(str(i[0]))
					os.remove(i[0])
			return 0
	except pyodbc.Error,e:
                debug(str(e))
                return -1
                return str(result)

def PGetSecurityPasswd(user,type_value):
        try:
                with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
                        curs.execute("select public.\"PGetSecurityPasswd\"(E'%s',%s);" % (user,type_value))
                        results = curs.fetchall()[0][0]
                        if results == None:
                                results = ''
                        else:
                                results = results.encode('utf-8')
                        return results
        except pyodbc.Error,e:
                return 0
