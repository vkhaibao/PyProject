#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import sys
import os
import base64
import csv
import pyodbc
import re
import codecs
import htmlencode
from generating_log import system_log
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
import MySQLdb
import urllib
from logbase import defines
from logbase import task_client
from comm_function import PGetSecurityPasswd
from urllib import unquote
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
from jinja2 import Environment,FileSystemLoader
down_file_user = Blueprint('down_file_user',__name__)
from htmlencode import check_role
from htmlencode import parse_sess

ERRNUM_MODULE_BATCH = 1000
detail_data = []
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

def debug(c):
	return
	path = "/var/tmp/debuguseri.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

def down_templet():
	try:
		with open("/flash/system/storage/user/user.csv","w") as csvfile:
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
			down_path = "/flash/system/storage/user/user.csv"
			debug("12313213")
			return send_from_directory('/flash/system/storage/user','user.csv',as_attachment=True)
	except IOError,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

def down_user(userCode):
	debug("use down_user?")
	try:
		with open("/flash/system/storage/user/user.csv","w") as csvfile:
			csvfile.write(codecs.BOM_UTF8)
			writer = csv.writer(csvfile)
			#导出用户组
			title = ['*用户组名称','*组路径','描述','*管理员']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					sql = 'SELECT "UGroup"."UGName","UGroup"."UGId","UGroup"."Description" FROM "UGroup"'
					curs.execute(sql)
					all_ug = curs.fetchall()	
					for ug_data in all_ug:
						ug_list = []
						ug_list.append(ug_data[0])
						if ug_data[0] == '/':
							ug_list.append('')
							writer.writerow(ug_list)
							continue
						sql = 'select "UGroup"."ParentUGId" from "UGroup" where "UGroup"."UGId" = %d;' % ug_data[1] #取上一级组ID
						debug(sql)
						curs.execute(sql)
						results = curs.fetchall()

						if results[0][0] == 0:#第一层
							if ug_data[0] == '/':
								path = ug_data[0]
							else:
								path = '/' + ug_data[0]
							debug(path)
							ug_list.append(path)
						else:
							path_arry = []
							while results[0][0] != 0:
								sql = 'select "UGroup"."ParentUGId","UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results[0][0]
								debug(sql)
								curs.execute(sql)
								results = curs.fetchall()
								path_arry.insert(0,results[0][1])
							sql = 'select "UGroup"."UGName" from "UGroup" where "UGroup"."UGId" = %d;' % results[0][0]
							debug(sql)
							curs.execute(sql)
							results = curs.fetchall()
							path_arry.insert(0,results[0][0])
							path_arry.append(ug_data[0])
							path = '/'.join(path_arry)#路径
							path = path[1:]
							debug(path)
							ug_list.append(path)
						#Description
						ug_list.append(ug_data[2])
						#管理员
						sql = 'select public.\"PGetUGroup\"(%d);' %ug_data[1]
						curs.execute(sql)
						results = curs.fetchall()
						ug_admin_str = ""
						if results:
							if results[0][0] == None:
								ug_admin_array = []
							else:
								results = results[0][0].encode('utf-8')
								results_json = json.loads(results)
								ug_admins = results_json['AdminSet']
								for ug_admin in ug_admins:
									ug_admin_array.append(ug_admin['UserCode'])
								ug_admin_str = ';'.join(ug_admin_array)
						ug_list.append(ug_admin_str)

						writer.writerow(ug_list)
					curs.close()
					conn.close()
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
				
			#导出用户
			title = ['*用户账号','*用户姓名','认证方式','*密码','手机','描述','邮箱','部门','*角色','管理员','第三方认证账号','唯一登录','失效时间','用户组']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					curs.execute('select public."PGetUser"(null,0)')
					results = curs.fetchall()[0][0].encode('utf-8')
					all_user = json.loads(results)
					curs.close()
					conn.close()
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					for all_data in all_user:
						sql = 'select public."PGetUser"(%d)' % (all_data['UserId'])
						debug(sql)
						curs.execute(sql)
						results = curs.fetchall()[0][0].encode('utf-8')
						debug(results)
						user_data = json.loads(results)
						#detail_temp = json.loads(results)
						detail_temp = user_data.copy()
						rows_list = []

						if detail_temp['HGroupSet'] != None:
							hg_len = len(detail_temp['HGroupSet'])
						else:
							hg_len = 0
						max_len = hg_len
						i = 0
						while i < hg_len:
							rows_list.append([0])
							i = i + 1

						rows_list[0].append(detail_temp['UserCode'])
						rows_list[0].append(detail_temp['UserName'])
						rows_list[0].append(detail_temp['AuthTypeName'])
						rows_list[0].append(detail_temp['MobilePhone'])
						rows_list[0].append(detail_temp['Description'])
						rows_list[0].append(detail_temp['Email'])
						rows_list[0].append(detail_temp['Department'])
						#角色
						u_roles = detail_temp['RoleSet']
						u_role_array = []
						for u_role in u_roles:
							u_role_array.append(u_role['RoleName'])
						u_role_str = ';'.join(u_role_array)
						rows_list[0].append(u_role_str)
						#管理员
						u_admins = detail_temp['AdminSet']
						u_admin_array = []
						for u_admin in u_admins:
							sql = 'select public."PGetUser"(%d)' % (u_admin['AdminId'])
							curs.execute(sql)
							results_tmp = curs.fetchall()[0][0].encode('utf-8')
							user_data_tmp = json.loads(results_tmp)
							u_admin_array.append(user_data_tmp['UserCode'])
						u_admin_str = ';'.join(u_admin_array)
						rows_list[0].append(u_admin_str)
						#
						rows_list[0].append(detail_temp['ThirdUserCode'])
						if detail_temp['LoginUniqueIP'] == False:
							LoginUniqueIP = "否"
						else:
							LoginUniqueIP = "是"
						rows_list[0].append(LoginUniqueIP)
						if str(detail_temp['ExpireTime']) == 'None':
							rows_list[0].append('')
						else:
							rows_list[0].append(detail_temp['ExpireTime'])
						#用户组						
						if detail_temp['UGroupSet'] != None:
							for ug_index,ug in enumerate(detail_temp['UGroupSet']):	
								if ug_index > 0:
									k = 0
									while k < 4:
										rows_list[ug_index].append('')
										k = k + 1
								rows_list[hg_index].append(ug['UGroupNamePath'][1:])
						writer.writerows(rows_list)
						#writer.writerow(detail_data)
					csvfile.close()
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
			debug("1231313hhhh")
			down_path = "user.csv"
			debug("1231313hhhhjjjj")
			try:
				return send_from_directory('/flash/system/storage/user','user.csv',as_attachment=True)
			except Exception,e:
				debug(str(e))
	except IOError as err: 
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@down_file_user.route('/export_data_user',methods=['GET', 'POST'])
def export_data_user():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('a1')
	session = request.form.get('a0')
	choose = request.form.get('a2')
	format = request.form.get('a3')
	debug("abcde"+choose)
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
		return down_templet()
	else:
		task_content = '[global]\nclass = taskdown_user\ntype = execute_down_cmd\nusercode=\"%s\"\nclientip=\"%s\"\nse=\"%s\"\nchoose=\"%s\"\nformat=\"%s\"\ntime_value=%s\n' % (userCode,client_ip,session,choose,format,time_value)
		debug(task_content)
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			debug("hhhhhhh")
			return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.ErrMsg))
		return "true:user.%s.%s.%s"%(userCode,session,time_value)
			

@down_file_user.route('/download_temp_user',methods=['GET', 'POST'])
def download_temp():
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
	return down_templet()


@down_file_user.route('/get_down_ok_user',methods=['GET', 'POST'])
def get_down_ok_user():
	se = request.form.get('a0')
	type = request.form.get('a1')
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
			sql = "select * from private.\"UserExportInfo\" where \"FileName\" like '%"+file_name+"%';"
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				sql = "delete from private.\"UserExportInfo\" where \"FileName\" like '%"+file_name+"%';"
				curs.execute(sql)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
			return "{\"Result\":true,\"ErrMsg\":\""+str(results[0][2])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"file_name\":\""+str(results[0][1])+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@down_file_user.route('/download_file_user',methods=['GET', 'POST'])
def download_file_user():
	se = request.form.get('a0')
	file_name = request.form.get('a1')
	format = request.form.get('z1')
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
	file_name_arr.pop(-2)
	if use_BH=='0':
		return send_from_directory('/usr/storage/.system/dwload',file_name,as_attachment=True,attachment_filename=('.'.join(file_name_arr)))
	else:
		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"%s","filenewname":"%s"}'% (file_name,('.'.join(file_name_arr)))

@down_file_user.route('/del_user_file',methods=['GET', 'POST'])
def del_user_file():
        se = request.form.get('a0')
        filename = request.form.get('z1')
        client_ip = request.remote_addr
        (error,userCode,mac) = SessionCheck(se,client_ip);
        if error < 0:
                return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
        elif error > 0:
                if error == 2:
                        return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
                else:
                        return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
        task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(filename))
        if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
                return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return 'true'
	
#指令授权
@down_file_user.route('/export_data_cmd',methods=['GET', 'POST'])
def export_data_cmd():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('a1')
	session = request.form.get('a0')
	type_value = request.form.get('z2')
	format_value = request.form.get('z3')
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
		return down_templet()
	else:
		task_content = '[global]\nclass = taskdown_user\ntype = execute_down_cmdauth\nusercode=\"%s\"\nclientip=\"%s\"\nse=\"%s\"\ntype_value=%s\nformat_value=%s\ntime_value=%s\n' % (userCode,client_ip,session,type_value,format_value,time_value)
		debug(task_content)
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.ErrMsg))
		return "true:cmd.%s.%s.%s"%(userCode,session,time_value)
			
@down_file_user.route('/download_temp_cmd',methods=['GET', 'POST'])
def download_temp_cmd():
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
	return down_templet()

@down_file_user.route('/get_down_ok_cmd',methods=['GET', 'POST'])
def get_down_ok_cmd():
	se = request.form.get('a0')
	format_value=request.form.get('a1')
	file_name=request.form.get('a2')
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
			sql = "select * from private.\"UserExportInfo\" where \"FileName\" like '%"+file_name+"%';"
			curs.execute(sql)
			results = curs.fetchall()
			if len(results) != 0:
				sql = "delete from private.\"UserExportInfo\" where \"FileName\" like '%"+file_name+"%';"
				curs.execute(sql)
			else:
				return "{\"Result\":false,\"ErrMsg\":\"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\"}"
			return "{\"Result\":true,\"ErrMsg\":\""+str(results[0][2])+"\",\"time\":\""+str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))+"\",\"file_name\":\""+str(results[0][1])+"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@down_file_user.route('/download_file_cmd',methods=['GET', 'POST'])
def download_file_cmd():
	se = request.form.get('a0')
	file_name = request.form.get('a1')
	format_value=request.form.get('z1')
	use_BH=request.form.get('a99')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	# system_log(userCode,"导出指令授权","成功","运维管理>授权管理>指令授权")
	system_log(userCode,"导出指令授权","成功","运维管理>指令授权")
	file_name_arr=file_name.split('.')
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	file_name_arr.pop(-2)
	if use_BH=='0':
		return send_from_directory('/usr/storage/.system/dwload',file_name,as_attachment=True,attachment_filename=('.'.join(file_name_arr)))
	else:
		return '{"Result":true,"path":"/usr/storage/.system/dwload/","filename":"%s","filenewname":"%s"}'% (file_name,'.'.join(file_name_arr))

@down_file_user.route('/del_cmd_file',methods=['GET', 'POST'])
def del_cmd_file():
	se = request.form.get('a0')
	#type = request.form.get('z1')
	format_value=request.form.get('a1')
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
			filename='cmd.%s.%s.zip' % (userCode,se)
	else:
			if format_value == '1':
					filename='cmd.%s.%s.xls' % (userCode,se)
			elif format_value == '2':
					filename='cmd.%s.%s.xlsx' % (userCode,se)
			else:
					filename='cmd.%s.%s.csv' % (userCode,se)
	# filename='cmd.%s.%s.csv' % (userCode,se)
	task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/storage/.system/dwload/%s\n' % (str(filename))
	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return 'true'
