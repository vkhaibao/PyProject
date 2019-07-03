#!/usr/bin/python
#-coding: UTF-8-

import json
import time
import sys
import os
import base64
import csv
import pyodbc
import re
import codecs
import MySQLdb
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import defines
from logbase import task_client
from urllib import unquote
import platform
import thread
import logging
import socket
import cgi
import cgitb
import json
import datetime
import taskcommon
from werkzeug.utils import secure_filename
from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
from jinja2 import Environment,FileSystemLoader
import chardet
ERRNUM_MODULE_BATCH = 1000
ERRNUM_MODULE_host = 2000
UPLOAD_FOLDER = '/var/tmp/zdp'
pro_data = []
ad_data = []
con_data = []
dev_data = []
host_data = []
hg_data = []
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

def checkip(ip):
	p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
	if p.match(ip):
		return True
	else:
		return False

def checkmac(mac):  
	if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$",mac):
		return True 		
	else:
		return False

def checkpro(pro):  
    p = re.compile('^[\w\-\s]+$')  
    if p.match(pro):  
        return True  
    else:  
        return False

def checkname(name):
	p = re.compile(u'^[\w\.\-\u4e00-\u9fa5]+$')
	if p.match(name):
		return True
	else:
		return False

def checkpwd(pwd):
	p = re.compile(u'[^\u4e00-\u9fa5]+$')
	if not isinstance(pwd, unicode):
		pwd = unicode(pwd,'utf-8')
	if p.match(pwd):
		return True
	else:
		return False
		
#不包含特殊字符
def check_char(str):
	p = re.compile(r'^[^|@\/\'\\\"#$%&\^\*]+$')
	if p.match(str):
		return True
	else:
		return False	

def checkEmail(email):
	p = re.compile("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$")
	if p.match(email):
		return True
	else:
		return False
		

def encodePwd(pwd):
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd(str(pwd),pwd_rc4);#执行函数
	return pwd_rc4.value

def checkYmd(str):
	try:
		time.strptime(str,"%Y/%m/%d")
		return True
	except:
		return False

def checkHMS(str):
	try:
		time.strptime(str,"%H:%M:%S")
		return True
	except:
		return False

def filter_scope(type,scope,id):
	accord_scope_list = []
	if type == 1:
		for scope_item in scope:
			if scope_item['HostId'] == id:
				accord_scope_list.append(id)
	else:
		for scope_item in scope:
			if scope_item['HGId'] == id:
				accord_scope_list.append(id)
	return accord_scope_list

def debug(c):
	return 0
	path = "/var/tmp/debugzdp1.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
		
def system_log(user,oper,mesg,module,client_ip,_type=1):
	debug("1111111111111111")
	happen=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
	debug("11111111111111121")
	#client_ip=request.remote_addr
	debug("11111111111111113")
	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn,conn.cursor() as curs:
			debug("11111111111111114")
			sql="INSERT INTO \"public\".adm_table(\"int32_01\",\"int08_00\",\"xtime_02\",\"ip_00\",\"str32_22\",\"str32_02\",\"str32_01\",\"str32_04\",\"int08_12\") VALUES(%s,3,E'%s','%s','%s','%s','%s','%s',0);"%(_type,happen,client_ip,user,MySQLdb.escape_string(mesg).decode("utf-8"),
MySQLdb.escape_string(oper).decode("utf-8"),
MySQLdb.escape_string(module).decode("utf-8"))
			debug(str(sql))
			curs.execute(sql)
			conn.commit()
			return True
	except pyodbc.Error,e:
		#return str(e)
		return False
	return False

def import_data_all(file_pwd,cover,taskid,usercode,clientip):
	reload(sys)
	sys.setdefaultencoding('utf-8')
	#ipath = request.form.get('a1')
	#ipath = unicode(ipath,"utf8")
	print "zxcczczxc"
	all_data = []
	i = 0
	#0协议,1AD域,2连接参数,3邮件,4短信网关,5SYSLOG,6SNMP,7审批,8告警,9时间,10客户端,11服务器,12授权
	while i < 13:
		all_data.append([])
		i += 1
	debug(file_pwd)
	print "%s" % file_pwd
	title_list = ['协议','AD域','连接参数','邮件','短信网关','SYSLOG','SNMP','审批策略','事件告警','时间集合','客户端集合','服务器集合','访问授权']
	flag = 1
	p_t = 0
	with open(file_pwd,'rb') as f:
		read_data = f.read()
		debug(str(chardet.detect(read_data)))
		char_encode = chardet.detect(read_data)['encoding']
	try:
		with codecs.open(file_pwd,'rb',char_encode) as csvfile:
			print "start"
			reader = csv.reader(csvfile)
			for index_r,rows in enumerate(reader):
				if rows[0] == "类型":
					continue
				if rows[0] in title_list:
					data_index = title_list.index(rows[0])
					continue
				elif rows[0] == "":
					rows_flag = 0
					for rows_item in rows:
						if rows_item == "":
							rows_flag += 1
					if rows_flag != len(rows):
						all_data[data_index].append(rows[1:])
				else:
					return "{\"Result\":false,\"ErrMsg\":\"文件中第一列标题格式错误\"}"
				'''
				if index_r == 0:
					if rows[0] != "类型":
						return "{\"Result\":false,\"ErrMsg\":\"文件中第一列标题格式错误\"}"
					else:
						continue
				if rows[0] == "协议":
					continue
				if p_t != flag:
					all_data[p_t].append(rows[1:])
					if flag == len(title_list):
						continue
				if rows[0] == title_list[flag]:
					all_data[p_t].pop()
					i = 0
					while i < 3:
						for data in all_data[p_t][-1]:
							if data != "":
								return "{\"Result\":false,\"ErrMsg\":\"文件中%s格式错误（没有空三行）\"}" % title_list[flag]
						all_data[p_t].pop()
						i += 1
					p_t = flag
					flag += 1
					continue
				elif rows[0] != "":
					return "{\"Result\":false,\"ErrMsg\":\"文件中第一列格式错误\"}"
				if p_t < flag:
					continue
				'''	
			print "end"
			csvfile.close()
	except IOError as err:
		print "fail"
		return "{\"Result\":false,\"ErrMsg\":\"文件打开失败\"}"
	except Exception,ex:
		print Exception,":",ex
		return "{\"Result\":false,\"ErrMsg\":\"语法错误(%s)\"}" % (ex)
	debug("----------------")
	debug("all_data:%s" % str(all_data))
	debug("xieyi:%s" % str(all_data[0]))
	debug("xieyi")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetPermissions\"(E'%s')" % usercode.decode('utf-8')
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			perm_result = json.loads(result)
			perm_flag = []
			for perm_item in perm_result:
				if perm_item['SubMenuId'] == 15 and perm_item['Mode'] == 2:#访问授权管理权限
					perm_flag.append(15)
				elif perm_item['SubMenuId'] == 14 and perm_item['Mode'] == 2:#主机管理权限
					perm_flag.append(14)
				elif perm_item['SubMenuId'] == 24 and perm_item['Mode'] == 2:#系统管理权限
					perm_flag.append(24)
			if 14 in perm_flag:
				#导入协议
				for j,i in enumerate(all_data[0]):
					if i[0] != "":
						name = i[0].replace('\t','').decode('utf-8')
						if not checkpro(name):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中协议名称错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中协议名称错误\"}" % (j+1)
						if name != "PCANY":
							if not i[1].isdigit():
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1)
							else:
								if int(i[1]) < 1 or int(i[1]) > 65334:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1)
						if len(i) == 2:
							des = 'null'
						else:
							if i[2] == "":
								des = 'null'
							else:
								des = i[2].replace('\\','\\\\').replace("'","''").replace('"','\\\\"')
								des = '"%s"' % des.decode('utf-8')
						if cover == '1':
							curs.execute('select public."PGetAccessProtocolByName"(E\'%s\')' % (name))
							proid = curs.fetchall()[0][0]
						else:
							proid = 0
						if name == "PCANY":
							port1 = i[1].split(':')
							if len(port1) == 1:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1)
							if not port1[0].isdigit() and not port1[1].isdigit():
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1)
							else:
								if int(port1[0]) > 65534 or int(port1[0]) < 1 or int(port1[1]) > 65534 or int(port1[1]) < 1:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中端口错误\"}" % (j+1)
							sql = '{"ProtocolId":'+str(proid)+',"ProtocolName":"'+name+'","Port":'+port1[0]+',"Port1":'+port1[1]+',"Description":'+des+'}'
						else:
							sql = '{"ProtocolId":'+str(proid)+',"ProtocolName":"'+name+'","Port":'+i[1]+',"Description":'+des+'}'	
						sql = "'%s'" % sql
						debug('select public."PSaveAccessProtocol"(%s)' % (sql))
						curs.execute('select public."PSaveAccessProtocol"(%s)' % (sql))
					else:
						conn.rollback()
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中协议名称不能为空\"}" % (j+1))
						return "{\"Result\":false,\"ErrMsg\":\"第%d行协议信息中协议名称不能为空\"}" % (j+1)
				debug("AD域")
				#导入AD域
				ip_list = []
				for j,i in enumerate(all_data[1]):
					if i[0] == "" and j == 0:
						conn.rollback()
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中AD域名称不能为空\"}" % (j+1))
						return "{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中AD域名称不能为空\"}" % (j+1)
					if i[0] != "" and j != 0:
						debug("ip_list1:%s" % str(ip_list))
						ServerIP = ';'.join(ip_list)
						if cover == '1':
							curs.execute('select public."PGetDomainByName"(E\'%s\')' % (name))
							adid = curs.fetchall()[0][0]
							sql = '{"DomainId":'+str(adid)+',"DomainName":"'+name+'","ServerIP":"'+ServerIP+'"}'
						else:
							sql = '{"DomainId":0,"DomainName":"'+name+'","ServerIP":"'+ServerIP+'"}'
						debug(sql)
						sql = "E'%s'" % sql
						curs.execute('select public."PSaveDomain"(%s)' % (sql))
						ip_list = []
					if i[0] != "":
						name = i[0].replace("\t",'').decode('utf-8')
						if not checkname(name):
							conn.rollback()
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中名称格式错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中名称格式错误\"}" % (j+1)
					if i[1] != "":
						if not checkip(i[1]):
							conn.rollback()
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中IP格式错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中IP格式错误\"}" % (j+1)
						else:
							ip_list.append(i[1])
					else:
						conn.rollback()
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中IP不能为空\"}" % (j+1))
						return "{\"Result\":false,\"ErrMsg\":\"第%d行AD域信息中IP不能为空\"}" % (j+1)
					if j == len(all_data[1]) - 1:
						debug("ip_list1:%s" % str(ip_list))
						ServerIP = ';'.join(ip_list)
						if cover == '1':
							curs.execute('select public."PGetDomainByName"(E\'%s\')' % (name))
							adid = curs.fetchall()[0][0]
							sql = '{"DomainId":'+str(adid)+',"DomainName":"'+name+'","ServerIP":"'+ServerIP+'"}'
						else:
							sql = '{"DomainId":0,"DomainName":"'+name+'","ServerIP":"'+ServerIP+'"}'
						debug(sql)
						sql = "'%s'" % sql
						curs.execute('select public."PSaveDomain"(%s)' % (sql))	
				debug("连接参数")
				#导入连接参数
				pro_name_list = ["RDP","SSH","ORACLE","MSSQL","MYSQL","HTTP","HTTPS","TELNET","FTP","VNC","X11","RADMIN","SYBASE","DB2","RLOGIN","PCANY","TN5250"]
				data = {"ConnParamId":0,"ConnParamName":"","ProtocolId":1,"ServiceName":"","ConnType":"","ConnParamValue":""}
				pro_name_list1 = ["RDP","TELNET","FTP","VNC","X11","RLOGIN","PCANY","TN5250"]
				for j,i in enumerate(all_data[2]):
					if len(i) == 2:
						i.append('')
					if i[0] != "":
						debug("%s" % i[0])
						if not checkname(i[0].replace('\t','').decode('utf-8')):
							conn.rollback()
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中参数名称错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中参数名称错误\"}" % (j+1)	
						if i[1] != "":
							if i[1] not in pro_name_list:
								conn.rollback()
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中协议格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中协议格式错误\"}" % (j+1)
							else:
								if i[1] in pro_name_list1:
									ServiceName = None
									ConnParamValue = None
									ConnType = None	
									if i[1] == "RDP":
										pro_id = 1
									elif i[1] == "TELNET":
										pro_id = 8
									elif i[1] == "FTP":
										pro_id = 9
									elif i[1] == "VNC":
										pro_id = 10
									elif i[1] == "X11":
										pro_id = 11
									elif i[1] == "RLOGIN":
										pro_id = 15
									elif i[1] == "PCANY":
										pro_id = 16
									elif i[1] == "TN5250":
										pro_id = 17
									else:
										pass									
								else:
									if i[1] == "SSH":
										pro_id = 2
										ConnType = None
										ConnParamValue = None
										if i[2] == '1' or i[2] == '2':
											ServiceName = i[2]
										else:
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
									elif i[1] == "ORACLE":
										pro_id = 3
										pro_set = i[2].split('|')
										pro_set_len = len(pro_set)
										debug(i[2])
										debug(str(pro_set_len))
										if pro_set_len == 3:
											ConnParamValue = pro_set[0]#.upper()
											ServiceName = pro_set[1]
											if pro_set[2] == "未指定" or pro_set[2] == "":
												ConnType = None
											else:
												ConnType = pro_set[2]#.upper()
											debug('zz')
											debug(ConnParamValue)
											debug(ServiceName)
											if not check_char(ServiceName):
												conn.rollback()
												debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
												
											if ConnParamValue != "SID" and ConnParamValue != "SERVICE_NAME":
												conn.rollback()
												debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
											else:
												if ConnType != "NORMAL" and ConnType != "SYSDBA" and ConnType != "SYSOPER" and ConnType != "未指定" and ConnType != None:
													conn.rollback()
													debug( "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
													return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										elif pro_set_len == 2:
											ConnParamValue = pro_set[0]#.upper()
											ServiceName = pro_set[1]
											ConnType = None
											if not check_char(ServiceName):
												conn.rollback()
												debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
											if ConnParamValue != "SID" and ConnParamValue != "SERVICE_NAME":
												conn.rollback()
												debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										else:
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
									elif i[1] == "MSSQL":
										pro_id = 4
										pro_set = i[2].split('|')
										pro_set_len = len(pro_set)
										ServiceName = pro_set[0]
										ConnParamValue = None
										if ServiceName == "" or not check_char(ServiceName): #继续
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										if pro_set_len == 2:
											if pro_set[1] == "未指定" and pro_set[1] == "":
												ConnType = None
											else:
												ConnType = pro_set[1]#.upper()
											if ConnType != "SQL服务器验证" and ConnType != "Windows验证" and ConnType != "Windows单一登录" and  ConnType != "未指定" and ConnType != None:
												conn.rollback()
												debug( "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										else:
											ConnType = None
									elif i[1] == "SYBASE" or i[1] == "DB2":				
										if i[1] == "SYBASE":
											pro_id = 13
										else:
											pro_id = 14
										if i[2] == "" or not check_char(i[2]):
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										ServiceName = i[2]									
										ConnType = None
										ConnParamValue = None
									elif i[1] == "MYSQL":
										pro_id = 5
										ServiceName = i[2]
										ConnType = None
										ConnParamValue = None
									elif i[1] == "HTTP" or i[1] == "HTTPS":
										if i[1] == "HTTP":
											pro_id = 6
										else:
											pro_id = 7
				
										if i[2] == "":
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										pro_set = i[2].split('|')
										pro_set_len = len(pro_set)
										if pro_set[0] == "" or pro_set_len > 4:
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										#pro_set至少是2个时判断后面第二个的格式
										if pro_set_len > 1 and pro_set[1] != "" and not check_char(pro_set[1]):
											debug("pro_set[1]:%s" % pro_set[1])
											debug("pro_set_len:%d" % pro_set_len)
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										#pro_set至少是3个时判断后面第三个的格式
										if pro_set_len > 2 and pro_set[2] != "" and not check_char(pro_set[2]):
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										if pro_set_len == 4 and len(re.findall('(\|)',pro_set[3])) > 0:
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										ServiceName = pro_set[0]
										ConnType = None
										if pro_set_len == 1:
											ConnParamValue = "||"
										else:
											debug(i[2])
											ConnParamValue = i[2].split('|',1)[1]
									elif i[1] == "RADMIN":
										pro_id = 12
										ServiceName = None
										ConnParamValue = None
										if i[2] != "":
											if i[2] == "未指定" or i[2] == "":
												ConnType = None
											else:
												ConnType = i[2]#.upper()
											if ConnType !="未指定" and ConnType != "RADMIN" and ConnType != "Windows" and ConnType != None:
												conn.rollback()
												debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
										else:
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
											#ServiceName = None
									else:
										conn.rollback()
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1))
										return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中配置错误\"}" % (j+1)
							debug("zzz")
							if cover == '1':
								curs.execute('select public."PGetConnParamByName"(E\'%s\')' % (i[0].replace('\t','').decode('utf-8')))
								debug(('select public."PGetConnParamByName"(\'%s\')' % (i[0].replace('\t','').decode('utf-8'))))
								conid = curs.fetchall()[0][0]
								data['ConnParamId'] = conid
							else:
								data['ConnParamId'] = 0
							debug(str(data['ConnParamId']))
							data['ConnParamName'] = i[0].replace('\t','').decode('utf-8')
							data['ProtocolId'] = pro_id
							data['ServiceName'] = ServiceName
							data['ConnType'] = ConnType
							data['ConnParamValue'] = ConnParamValue
							sql = json.dumps(data)
							debug(sql)
							#sql = "'%s'" % sql
							#debug('select public."PSaveConnParam"(%s)' % (sql))
							debug('select public."PSaveConnParam"(E\'%s\')' % (MySQLdb.escape_string(sql).decode("utf-8")))
							curs.execute('select public."PSaveConnParam"(E\'%s\')' % (MySQLdb.escape_string(sql).decode("utf-8")))
						else:
							conn.rollback()
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中协议不能为空\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行连接参数信息中协议不能为空\"}" % (j+1)
					else:
						conn.rollback()
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行连接信息中连接参数名称不能为空\"}" % (j+1))
						return "{\"Result\":false,\"ErrMsg\":\"第%d行连接信息中连接参数名称不能为空\"}" % (j+1)
			
			if 24 in perm_flag:
				debug("邮件")
				#导入邮件
				json_data = {"SmtpConfigId":0,"SmtpConfigName":"","SmtpServer":"","DNS":None,"Sender":"","SenderEmail":"","AttachMaxLimit":0,"ServerVerify":False,"SenderEmailPass":None,"Flag":2,"EnCode":0}
				for j,i in enumerate(all_data[3]):
					if i[0] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中邮件名称不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中邮件名称不能为空\"}" % (j+1)
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中邮件名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中邮件名称格式错误\"}" % (j+1)
						
					if i[1] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器地址格式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器地址格式不能为空\"}" % (j+1)
					if not checkip(i[1]):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器地址格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器地址格式错误\"}" % (j+1)
					
					if i[2] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中发送邮箱地址不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中发送邮箱地址不能为空\"}" % (j+1)
					#检查邮箱格式
					if not checkEmail(i[2]):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中发送邮箱地址格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中发送邮箱地址格式错误\"}" % (j+1)
					
					#发送服务器账号
					if i[3] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中发送服务器账号不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中发送服务器账号不能为空\"}" % (j+1)
					#服务器验证
					'''
					if i[4] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器验证不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器验证不能为空\"}" % (j+1)
					'''
					if i[4] == "" or i[4] == "否":
						json_data['ServerVerify'] = False
						json_data['SenderEmailPass'] = None
					else:
						if not checkpwd(i[4]):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器验证格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中服务器验证格式错误\"}" % (j+1)
						if os.path.exists('/usr/lib64/logproxy.so') == False:
							return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
						lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
						pwd_rc4 = c_char_p()# 定义一个指针
						lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
						lib.encrypt_pwd.restype = None #定义函数返回值
						pwd_rc4.value = "0"*512 # 初始化 指针
						lib.encrypt_pwd(str(i[4]),pwd_rc4);#执行函数
						json_data['ServerVerify'] = True
						json_data['SenderEmailPass'] = pwd_rc4.value #获取变量的值
					
					#附件大小
					if i[5] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中附件大小不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中附件大小不能为空\"}" % (j+1)
					if not i[5].isdigit():
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中附件大小格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中附件大小格式错误\"}" % (j+1)
					#编码方式
					'''
					if i[6] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中编码方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中编码方式不能为空\"}" % (j+1)
					'''
					if i[6] == "" or i[6] == "UTF-8":
						json_data['EnCode'] = 0
					elif i[6] == "GBK":
						json_data['EnCode'] = 1
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中编码方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中编码方式格式错误\"}" % (j+1)
					#方式
					'''
					if i[7] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中方式不能为空\"}" % (j+1)
					'''
					if i[7] == "默认":
						json_data['Flag'] = 2
					elif i[7] == "备用":
						json_data['Flag'] = 1
					elif i[7] == "" or i[7] == "其他":
						json_data['Flag'] = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行邮件信息中方式格式错误\"}" % (j+1)
					
					if cover == '1':
						sql = "select \"SmtpConfigId\" from public.\"SmtpConfig\" where \"SmtpConfigName\"=E'%s'" % i[0].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['SmtpConfigId'] = 0
						else:
							json_data['SmtpConfigId'] = result[0][0]
					else:
						json_data['SmtpConfigId'] = 0

					json_data['SmtpConfigName'] = i[0]
					json_data['SmtpServer'] = i[1]
					json_data['SenderEmail'] = i[2]
					json_data['Sender'] = i[3]
					json_data['AttachMaxLimit'] = i[5]
					curs.execute('select public."PSaveSmtpConfig"(E\'%s\')' % (MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")))
				
				#return "{\"Result\":true}"
				#导入短信网关
				#debug(str(all_data[4]))
				json_data = {"SmsSvrConfigId":0,"SmsSvrConfigName":"","SmsSvrDBType":"1","SmsSvrDBServerIP":"1.1.1.1","SmsSvrDBPort":22,"SmsSvrDBUserName":"21","SmsSvrDBPassword":"1","SmsSvrDBDatabase":"2","SmsSvrDBInsertTemp":"insert into cjd values('%content%','%phone%')","Flag":0,"EnCode":1}
				data_base_list = ['ORACLE','MYSQL','MSSQL','SYSBASE']
				for j,i in enumerate(all_data[4]):
					if i[0] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信网关名称不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信网关名称不能为空\"}" % (j+1)
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信网关名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信网关名称格式错误\"}" % (j+1)
						
					if i[1] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中数据库类型不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中数据库类型不能为空\"}" % (j+1)
					
					if i[1] == "ORACLE":
						json_data['SmsSvrDBType'] = 1
					elif i[1] == "MSSQL":
						json_data['SmsSvrDBType'] = 2
					elif i[1] == "MYSQL":
						json_data['SmsSvrDBType'] = 3
					elif i[1] == "SYSBASE":
						json_data['SmsSvrDBType'] = 4
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中数据库类型格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中数据库类型格式错误\"}" % (j+1)
					
					if i[2] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中服务器地址不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中服务器地址不能为空\"}" % (j+1)
					
					if not checkip(i[2]):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中服务器地址格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中服务器地址格式错误\"}" % (j+1)
					
					if i[3] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中端口不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中端口不能为空\"}" % (j+1)
						
					if not i[3].isdigit():
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中端口格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中端口格式错误\"}" % (j+1)
					
					if i[4] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中账号不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中账号不能为空\"}" % (j+1)
					if not checkname(i[4].decode('utf-8')):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中账号格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中账号格式错误\"}" % (j+1)
						
					
					if i[5] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中密码不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中密码不能为空\"}" % (j+1)
					else:
						if not checkpwd(i[5]):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中密码格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中密码格式错误\"}" % (j+1)	
					
					if i[6] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中数据库不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中数据库不能为空\"}" % (j+1)
					if i[7] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信sql语句模板不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信sql语句模板不能为空\"}" % (j+1)
					if i[7].find("%phone%") == -1 or i[7].find("%content%") == -1:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信sql语句模板格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中短信sql语句模板格式错误\"}" % (j+1)
					
					#编码方式
					'''
					if i[8] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中编码方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中编码方式不能为空\"}" % (j+1)
					'''
					if i[8] == "" or i[8] == "UTF-8":
						json_data['EnCode'] = 0
					elif i[8] == "GBK":
						json_data['EnCode'] = 1
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中编码方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中编码方式格式错误\"}" % (j+1)
					#方式
					'''
					if i[9] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中方式不能为空\"}" % (j+1)
					'''
					if i[9] == "默认":
						json_data['Flag'] = 2
					elif i[9] == "备用":
						json_data['Flag'] = 1
					elif i[9] == "" or i[9] == "其他":
						json_data['Flag'] = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行短信网关信息中方式格式错误\"}" % (j+1)

					if cover == '1':
						sql = "select \"SmsSvrConfigId\" from public.\"SmsSvrConfig\" where \"SmsSvrConfigName\"=E'%s'" % i[0].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['SmsSvrConfigId'] = 0
						else:
							json_data['SmsSvrConfigId'] = result[0][0]
					else:
						json_data['SmsSvrConfigId'] = 0

					json_data['SmsSvrConfigName'] = i[0]
					json_data['SmsSvrDBServerIP'] = i[2]
					json_data['SmsSvrDBPort'] = i[3]
					json_data['SmsSvrDBUserName'] = i[4]
					json_data['SmsSvrDBPassword'] = encodePwd(i[5])
					json_data['SmsSvrDBDatabase'] = i[6]
					json_data['SmsSvrDBInsertTemp'] = base64.b64encode(i[7])
					curs.execute('select public."PSaveSmsSvrConfig"(E\'%s\')' % (MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")))
				
				debug("SYSLOG")
				#导入SYSLOG
				json_data = {"SyslogConfigId":14,"SyslogConfigName":"eeeee","SyslogServerIP":"192.168.0.114","SyslogPort":514,"Flag":"2","EnCode":"0"}
				for j,i in enumerate(all_data[5]):
					if i[0] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中SYSLOG名称不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中SYSLOG名称不能为空\"}" % (j+1)
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中SYSLOG名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中SYSLOG名称格式错误\"}" % (j+1)
		
					if i[1] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中服务器地址不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中服务器地址不能为空\"}" % (j+1)
					
					if not checkip(i[1]):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中服务器地址格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中服务器地址格式错误\"}" % (j+1)
					
					if i[2] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中端口不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中端口不能为空\"}" % (j+1)
					if not i[2].isdigit():
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中端口格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中端口格式错误\"}" % (j+1)
					
					#编码方式
					'''
					if i[3] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中编码方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中编码方式不能为空\"}" % (j+1)
					'''
					if i[3] == "" or i[3] == "UTF-8":
						json_data['EnCode'] = 0
					elif i[3] == "GBK":
						json_data['EnCode'] = 1
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中编码方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中编码方式格式错误\"}" % (j+1)
					#方式
					'''
					if i[4] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG关信息中方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中方式不能为空\"}" % (j+1)
					'''
					if i[4] == "默认":
						json_data['Flag'] = 2
					elif i[4] == "备用":
						json_data['Flag'] = 1
					elif i[4] == "" or i[4] == "其他":
						json_data['Flag'] = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SYSLOG信息中方式格式错误\"}" % (j+1)

					if cover == '1':
						sql = "select \"SyslogConfigId\" from public.\"SyslogConfig\" where \"SyslogConfigName\"=E'%s'" % i[0].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['SyslogConfigId'] = 0
						else:
							json_data['SyslogConfigId'] = result[0][0]
					else:
						json_data['SyslogConfigId'] = 0

					json_data['SyslogConfigName'] = i[0]
					json_data['SyslogServerIP'] = i[1]
					json_data['SyslogPort'] = i[2]
					curs.execute('select public."PSaveSyslogConfig"(E\'%s\')' % (MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")))
				
				debug("SNMP")
				#导入SNMP
				json_data = {"SnmpConfigId":0,"SnmpConfigName":"eeeee","SnmpServerIP":"192.168.0.114","SnmpPort":514,"Flag":"2","EnCode":"0"}
				for j,i in enumerate(all_data[6]):
					if i[0] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中名称不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中名称不能为空\"}" % (j+1)
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中名称格式错误\"}" % (j+1)
					
						
					if i[1] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中服务器地址不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中服务器地址不能为空\"}" % (j+1)
					
					if not checkip(i[1]):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中服务器地址格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中服务器地址格式错误\"}" % (j+1)
					
					if i[2] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中端口不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中端口不能为空\"}" % (j+1)
					if not i[2].isdigit():
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中端口格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中端口格式错误\"}" % (j+1)
					
					#编码方式
					'''
					if i[3] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中编码方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中编码方式不能为空\"}" % (j+1)
					'''
					if i[3] == "" or i[3] == "UTF-8":
						json_data['EnCode'] = 0
					elif i[3] == "GBK":
						json_data['EnCode'] = 1
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中编码方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中编码方式格式错误\"}" % (j+1)
					#方式
					'''
					if i[4] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中方式不能为空\"}" % (j+1)
					'''
					if i[4] == "默认":
						json_data['Flag'] = 2
					elif i[4] == "备用":
						json_data['Flag'] = 1
					elif i[4] == "" or i[4] == "其他":
						json_data['Flag'] = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行SNMP信息中方式格式错误\"}" % (j+1)
					
					if cover == '1':
						sql = "select \"SnmpConfigId\" from public.\"SnmpConfig\" where \"SnmpConfigName\"=E'%s'" % i[0].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['SnmpConfigId'] = 0
						else:
							json_data['SnmpConfigId'] = result[0][0]
					else:
						json_data['SnmpConfigId'] = 0

					json_data['SnmpConfigName'] = i[0]
					json_data['SnmpServerIP'] = i[1]
					json_data['SnmpPort'] = i[2]
					curs.execute('select public."PSaveSnmpConfig"(E\'%s\')' % (MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")))
			debug("审批策略")
			debug(str(all_data[7]))
			#导入审批策略
			#ApproveType 13:消息邮件短信网关,9消息邮件 1，消息，5消息短信网关
			json_data = {"ApproveStrategyId":0,"ApproveStrategyName":"删除3-2","ApproveNum":1,"ApproveType":1,"UserSet":[],"MasterSmsMConfigId":None,"StandBySmsMConfigId":None,"MasterSmsSvrConfigId":0,"StandBySmsSvrConfigId":0,"MasterSmtpConfigId":0,"StandBySmtpConfigId":0}
			approve_user = {"UserId":29}
			invalid_approve_strategy = []#无效审批策略list
			for j,i in enumerate(all_data[7]):
				debug("i:%s" % str(i))
				if j == 0 and i[0] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中名称不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中名称不能为空\"}" % (j+1)
				
				if i[0] != "" and j != 0:#保存审批策略
					if len(json_data['UserSet']) != 0:
						if cover == '1':
							sql = "select \"ApproveStrategyId\" from public.\"ApproveStrategy\" where \"ApproveStrategyName\"=E'%s'" % json_data['ApproveStrategyName'].decode('utf-8')
							debug("sql:%s" % sql)
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) == 0:
								json_data['ApproveStrategyId'] = 0
							else:
								json_data['ApproveStrategyId'] = result[0][0]
						else:
							json_data['ApproveStrategyId'] = 0
						debug("----------:%s" % str(json_data))
						sql = "select public.\"PSaveApproveStrategy\"(E'%s')" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
						debug("sql:%s" % sql)
						curs.execute(sql)
					else:
						invalid_approve_strategy.append(json_data['ApproveStrategyName'])
					json_data = {"ApproveStrategyId":0,"ApproveStrategyName":"删除3-2","ApproveNum":1,"ApproveType":1,"UserSet":[],"MasterSmsMConfigId":None,"StandBySmsMConfigId":None,"MasterSmsSvrConfigId":0,"StandBySmsSvrConfigId":0,"MasterSmtpConfigId":0,"StandBySmtpConfigId":0}
				debug("begin")
				if i[0] != "":#新的审批策略
					debug("begin1")
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中名称格式错误\"}" % (j+1)
					debug("begin2")
					ApproveType = 1
					if i[1] != "" or i[2] != "":#短信网关
						ApproveType += 4
					if i[3] != "" or i[4] != "":#邮件
						ApproveType += 8
					debug("begin3")
					if i[1] != "" and i[1] != "全局指定":
						sql = "select \"SmsSvrConfigId\" from public.\"SmsSvrConfig\" where \"SmsSvrConfigName\"=E'%s'" % i[1].decode('utf-8')
						debug(sql)
						curs.execute(sql)
						debug("execute")
						result = curs.fetchall()#[0][0]
						debug("result:%s" % str(result))
						if len(result) != 0:
							json_data['MasterSmsSvrConfigId'] = result[0][0]
						else:
							json_data['MasterSmsSvrConfigId'] = 0
					else:
						json_data['MasterSmsSvrConfigId'] = 0
					debug("begin4")
					if i[2] != "" and i[2] != "全局指定":
						sql = "select \"SmsSvrConfigId\" from public.\"SmsSvrConfig\" where \"SmsSvrConfigName\"=E'%s'" % i[2].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) != 0:
							json_data['StandBySmsSvrConfigId'] = result[0][0]
						else:
							json_data['StandBySmsSvrConfigId'] = 0
					else:
						json_data['StandBySmsSvrConfigId'] = 0
					
					if i[1] == i[2] and i[1] != "全局指定":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中短信网关默认不能与备用重复\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中短信网关默认不能与备用重复\"}" % (j+1)
					debug("begin5")
					if i[3] != "" and i[3] != "全局指定":
						sql = "select \"SmtpConfigId\" from public.\"SmtpConfig\" where \"SmtpConfigName\"=E'%s'" % i[3].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['MasterSmtpConfigId'] = 0
						else:
							json_data['MasterSmtpConfigId'] = result[0][0]
					else:
						json_data['MasterSmtpConfigId'] = 0
					debug("begin6")
					if i[4] != "" and i[4] != "全局指定":
						sql = "select \"SmtpConfigId\" from public.\"SmtpConfig\" where \"SmtpConfigName\"=E'%s'" % i[4].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['StandBySmtpConfigId'] = 0
						else:
							json_data['StandBySmtpConfigId'] = result[0][0]
					else:
						json_data['StandBySmtpConfigId'] = 0
					
					if i[3] == i[4] and i[3] != "全局指定":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中邮件默认不能与邮件备用重复\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中邮件默认不能与邮件备用重复\"}" % (j+1)
					debug("shenpizhe")
					#审批者
					if i[5] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批者不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批者不能为空\"}" % (j+1)
					if i[6] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批人数不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批人数不能为空\"}" % (j+1)
					if not i[6].isdigit():
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批人数格式不正确\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批人数格式不正确\"}" % (j+1)
					json_data['ApproveStrategyName'] = i[0]
					json_data['ApproveType'] = ApproveType
					json_data['ApproveNum'] = i[6]
					#continue
				else:
					x = 1
					while x < 5:
						if i[x] != "":
							debug("1111111111111")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中格式错误\"}" % (j+1)
						x += 1
				debug("shenpizhe1")
				#审批者
				if i[5] != "":
					if json_data['ApproveType'] == 13:#消息邮件短信网关
						sql = 'select "UserId" from public."User" where "UserCode"=\'%s\' and "Email" is not NULL and "MobilePhone" is not NULL' % i[5].decode('utf-8')
					elif json_data['ApproveType'] == 9:#消息邮件
						sql = 'select "UserId" from public."User" where "UserCode"=\'%s\' and "Email" is not NULL' % i[5].decode('utf-8')
					elif json_data['ApproveType'] == 5:#消息短信网关
						sql = 'select "UserId" from public."User" where "UserCode"=\'%s\' and "Email" is not NULL and "MobilePhone" is not NULL' % i[5].decode('utf-8')
					else:
						sql = "select \"UserId\" from public.\"User\" where \"UserCode\"=E'%s'" % i[5].decode('utf-8')
					curs.execute(sql)
					result = curs.fetchall()#[0][0]
					if len(result) == 0:
						continue
						'''
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批者不存在\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中审批者不存在\"}" % (j+1)
						'''
					else:
						approve_user['UserId'] = result[0][0]
						json_data['UserSet'].append(approve_user.copy())
					if i[6] != "" and i[0] == "":
						debug("111111111111122222")
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中格式错误\"}" % (j+1)
				else:
					debug("11111111111113333333")
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中格式错误\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行审批策略信息中格式错误\"}" % (j+1)
				debug("j:%d" % j)
				debug("len:%d" % len(all_data[7]))
				if j == len(all_data[7]) - 1:
					if len(json_data['UserSet']) != 0:
						if cover == '1':
							sql = "select \"ApproveStrategyId\" from public.\"ApproveStrategy\" where \"ApproveStrategyName\"=E'%s'" % json_data['ApproveStrategyName'].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) == 0:
								json_data['ApproveStrategyId'] = 0
							else:
								json_data['ApproveStrategyId'] = result[0][0]
						else:
							json_data['ApproveStrategyId'] = 0
						sql = "select public.\"PSaveApproveStrategy\"(E'%s')" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
						curs.execute(sql)
					else:
						invalid_approve_strategy.append(json_data['ApproveStrategyName'])
				debug("end")
			debug("事件告警")
			#导入事件告警
			json_data = {"EventAlarmInfoId":"0","Name":"231","EventLevel":0,"EventType":0,"EventDescription":"","AlarmAction":1,"AlarmReceiver":"123456@qq.com","UserSet":[],"MasterConfig":0,"StandByConfig":0,"MasterConfigName":"全局指定","StandByConfigName":"全局指定"}
			receive_userset = {"UserId":29}
			receive_user = []
			receive_user_flag = 0
			user_set_len = 0
			user_len = 0
			#debug("%s" % str(all_data[8]))
			invalid_alarm_strategy = []#无效事件告警list
			for j,i in enumerate(all_data[8]):
				debug("i:%s" % str(i))
				while len(i) < 9:
					i.append("")
				receive_user_flag += 1
				if j == 0 and i[0] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中名称不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中名称不能为空\"}" % (j+1)
				
				if i[0] != "" and j != 0:#保存事件告警
					receive_user_flag = 1
					if len(json_data['UserSet']) != 0:
						if cover == '1':
							sql = "select \"EventAlarmInfoId\" from public.\"EventAlarmInfo\" where \"Name\"=E'%s'" % json_data['Name'].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) == 0:
								json_data['EventAlarmInfoId'] = 0
							else:
								json_data['EventAlarmInfoId'] = result[0][0]
						else:
							json_data['EventAlarmInfoId'] = 0
						if len(receive_user) != 0:
							json_data['AlarmReceiver'] = ';'.join(receive_user)
						sql = "select public.\"PSaveEventAlarmInfo\"(E'%s')" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
						debug("sq1111l:%s" % str(sql))
						curs.execute(sql)
					else:
						invalid_alarm_strategy.append(json_data['Name'])
					json_data = {"EventAlarmInfoId":"0","Name":"231","EventLevel":0,"EventType":0,"EventDescription":"","AlarmAction":1,"AlarmReceiver":"123456@qq.com","UserSet":[],"MasterConfig":0,"StandByConfig":0,"MasterConfigName":"全局指定","StandByConfigName":"全局指定"}
					receive_user = []
					user_set_len = 0
					user_len = 0
				debug("begin")
				if i[0] != "":#新的事件告警
					debug("begin1")
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中名称格式错误\"}" % (j+1)
					debug("begin2")
					'''
					if i[4] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中方式不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中方式不能为空\"}" % (j+1)
					'''
					if i[4] == "" or i[4] == "无":
						json_data['AlarmAction'] = 0
						if i[5] != "" or i[6] != "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中方式格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中方式格式错误\"}" % (j+1)
						table_name = ""
					elif i[4] == "邮件":
						json_data['AlarmAction'] = 1
						table_name = "SmtpConfig"
						field_name = "SmtpConfigName"
						field_id = "SmtpConfigId"
					elif i[4] == "短信网关":
						json_data['AlarmAction'] = 3
						table_name = "SmsSvrConfig"
						field_name = "SmsSvrConfigName"
						field_id = "SmsSvrConfigId"
					elif i[4] == "SNMP":
						json_data['AlarmAction'] = 4
						table_name = "SnmpConfig"
						field_name = "SnmpConfigName"
						field_id = "SnmpConfigId"
					elif i[4] == "SYSLOG":
						json_data['AlarmAction'] = 5
						table_name = "SyslogConfig"
						field_name = "SyslogConfigName"
						field_id = "SyslogConfigId"
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中方式格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中方式格式错误\"}" % (j+1)
					
					if i[4] != "无" and i[1] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中描述不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中描述不能为空\"}" % (j+1)
					'''
					if i[2] == "":		
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中等级不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中等级不能为空\"}" % (j+1)
					'''
					if i[2] == "" or i[2] == "无":
						json_data['EventLevel'] = 0
					elif i[2] == "低":
						json_data['EventLevel'] = 1
					elif i[2] == "中":
						json_data['EventLevel'] = 2
					elif i[2] == "高":
						json_data['EventLevel'] = 3
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中等级格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中等级格式错误\"}" % (j+1)
					'''
					if i[3] == "":		
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中类型不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中类型不能为空\"}" % (j+1)
					'''
					if i[3] == "" or i[3] == "无":
						json_data['EventType'] = 0
					elif i[3] == "违规操作":
						json_data['EventType'] = 1
					elif i[3] == "高危操作":
						json_data['EventType'] = 2
					elif i[3] == "登录异常":
						json_data['EventType'] = 3
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中类型格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中类型格式错误\"}" % (j+1)
				
					if table_name != "":
						if i[5] != "" and i[5] != "全局指定":
							sql = "select \""+field_id+"\" from public.\""+table_name+"\" where \""+field_name+"\"=E\'%s\'" % i[5].decode('utf-8')
							debug("sql:%s" % sql)
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) != 0:
								json_data['MasterConfig'] = result[0][0]
								json_data['MasterConfigName'] = i[5]
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中默认不存在\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中默认不存在\"}" % (j+1)
						else:
							json_data['MasterConfig'] = 0
							json_data['MasterConfigName'] = '全局指定'
						#备用
						if i[6] != "" and i[6] != "全局指定":
							sql = "select \""+field_id+"\" from public.\""+table_name+"\" where \""+field_name+"\"=E\'%s\'" % i[6].decode('utf-8')
							debug("sql:%s" % sql)
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) != 0:
								json_data['StandByConfig'] = result[0][0]
								json_data['StandByConfigName'] = i[5]
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中默认不存在\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中默认不存在\"}" % (j+1)
						else:
							json_data['StandByConfig'] = 0
							json_data['StandByConfigName'] = '全局指定'
						
						if i[5] == i[6] and i[5] != "全局指定":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中默认与备用不能相同\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中默认与备用不能相同\"}" % (j+1)
					debug("----------")
					debug("AlarmAction----------------:%d" % json_data['AlarmAction'])
					if json_data['AlarmAction'] == 1 or json_data['AlarmAction'] == 3:
						if i[7] == "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接收者不能为空\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接收者不能为空\"}" % (j+1)
						else:
							sql = "select \"UserId\" from public.\"User\" where \"UserCode\"=E'%s'" % i[7].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) == 0:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件信息中已定义接收者不存在\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行事件信息中已定义接收者不存在\"}" % (j+1)
							'''
							else:
								receive_userset['UserId'] = result[0][0]
								debug("111111111111222222222")
								debug('%s' % str(json_data['UserSet']))
								json_data['UserSet'].append(receive_userset.copy())
							'''
						debug("1111111111111111111")
						'''
						if i[8] != "":
							receive_user.append(i[8])
						else:
							json_data['AlarmReceiver'] = None
						'''
					else:
						debug("----------111")
						if i[7] != "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接受者格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接受者格式错误\"}" % (j+1)
						if i[8] != "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中自定义接受者格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中自定义接受者格式错误\"}" % (j+1)
					json_data['Name'] = i[0]
					json_data['EventDescription'] = i[1]
					#debug("continue")
					#continue
				else:
					x = 1
					while x < 7:
						if i[x] != "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中格式错误\"}" % (j+1)
						x += 1
				debug("jieshouzhe")
				debug("receive_user_flag:%d" % receive_user_flag)
				debug("%d" % len(json_data['UserSet']))
				debug("%s" % str(json_data['UserSet']))
				#接收者
				if i[7] != "":
					if receive_user_flag == user_set_len + 1:
						user_set_len += 1
						if json_data['AlarmAction'] == 1:#邮件
							sql = 'select "UserId" from public."User" where "UserCode"=E\'%s\' and "Email" is not NULL' % i[7].decode('utf-8')
						else:#短信网关
							sql = 'select "UserId" from public."User" where "UserCode"=E\'%s\' and "MobilePhone" is not NULL' % i[7].decode('utf-8')
						#sql = "select \"UserId\" from public.\"User\" where \"UserCode\"='%s'" % i[7].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							continue
							'''
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接收者不存在\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接收者不存在\"}" % (j+1)
							'''
						else:
							receive_userset['UserId'] = result[0][0]
							json_data['UserSet'].append(receive_userset.copy())
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接收者格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中已定义接收者格式错误\"}" % (j+1)
				
				
				debug("%d" % len(receive_user))
				if i[8] != "":
					if receive_user_flag == user_len + 1:
						user_len += 1
						receive_user.append(i[8])
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中自定义接受者格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行事件告警信息中自定义接受者格式错误\"}" % (j+1)
				debug("j:%d" % j)
				debug("lendata:%d" % len(all_data[8]))
				if j == len(all_data[8]) - 1:
					if json_data['UserSet'] != 0:
						if cover == '1':
							sql = "select \"EventAlarmInfoId\" from public.\"EventAlarmInfo\" where \"Name\"=E'%s'" % json_data['Name'].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) == 0:
								json_data['EventAlarmInfoId'] = 0
							else:
								json_data['EventAlarmInfoId'] = result[0][0]
						else:
							json_data['EventAlarmInfoId'] = 0
						if len(receive_user) != 0:
							json_data['AlarmReceiver'] = ';'.join(receive_user)
						sql = "select public.\"PSaveEventAlarmInfo\"(E'%s')" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
						debug("sql:%s" % sql)
						curs.execute(sql)
					else:
						invalid_alarm_strategy.append(json_data['Name'])
				debug("end")
			debug("end11111111")
			
			#导入时间集合
			json_data = {"TimeSetId":0,"Name":"11","Description":None,"Set":[]}
			set = {"TimeSetMemberId":11,"Order":1,"TimeSetType":11,"StartDate":None,"EndDate":None,"StartTime":"00:00:00","EndTime":"23:59:59","StartPeriod":None,"EndPeriod":None}
			time_day = ['周一','周二','周三','周四','周五','周六','周日']
			order = 0
			for j,i in enumerate(all_data[9]):
			
				if j == 0 and i[0] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中名称不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中名称不能为空\"}" % (j+1)
				if i[0] != "" and j != 0:#保存时间集合
					if cover == '1':
						sql = "select \"TimeSetId\" from public.\"TimeSet\" where \"Name\"=E'%s'" % json_data['Name'].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['TimeSetId'] = 0
						else:
							json_data['TimeSetId'] = result[0][0]
					else:
						json_data['TimeSetId'] = 0
					sql = "select public.\"PSaveTimeSet\"(E'%s',0,null)" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
					debug("sql:%s" % sql)
					curs.execute(sql)
					
					json_data = {"TimeSetId":0,"Name":"11","Description":None,"Set":[]}
			
				if i[0] != "":#新的时间集合
					debug("begin1")
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中名称格式错误\"}" % (j+1)
					debug("begin2")
					if i[1] != "":
						json_data['Description'] = i[1]
					else:
						json_data['Description'] = None
					debug("timename")
					json_data['Name'] = i[0]
					debug("timename1111")
				else:
					if i[1] != "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中格式错误\"}" % (j+1)
						
				if i[2] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置不能为空\"}" % (j+1)
				else:
					set = {"TimeSetMemberId":0,"Order":1,"TimeSetType":11,"StartDate":None,"EndDate":None,"StartTime":"00:00:00","EndTime":"23:59:59","StartPeriod":None,"EndPeriod":None}
					set['Order'] = order + 1
					time_set = i[2].split(' ')
					
					if time_set[0] == "任务":
						if len(time_set) != 3:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						if time_set[1] == "当天":#任务 当天 00:00:00-12:12:12
							set['TimeSetType'] = 32
							start_end = time_set[2].split('-')
							if len(start_end) != 2:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
								
							if not checkHMS(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['StartTime'] = start_end[0]
							if not checkHMS(start_end[1]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['EndTime'] = start_end[1]
						elif time_set[1] == "当前":#任务 当前 00:00:00
							set['TimeSetType'] = 31
							if len(time_set) != 3:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							if not checkHMS(time_set[2]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['EndTime'] = time_set[2]	
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
					elif time_set[0] == "区间":#区间 2018/03/27 00:00:00-2018/03/27 23:59:59
						set['TimeSetType'] = 20
						if len(time_set) != 4:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						if not checkYmd(time_set[1]):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						else:
							set['StartDate'] = time_set[1].replace('/','-')
						
						start_end = time_set[2].split('-')
						if len(start_end) != 2:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						if not checkHMS(start_end[0]):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						else:
							set['StartTime'] = start_end[0]
						if not checkYmd(start_end[1]):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						else:
							set['EndDate'] = start_end[1].replace('/','-')
						
						if not checkHMS(time_set[3]):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						else:
							set['EndTime'] = time_set[3]
					elif time_set[0] == "周期":#周期 每天 00:00:00-12:12:12
						if len(time_set) < 2:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
						if time_set[1] == "每天":
							set['TimeSetType'] = 11
							if len(time_set) != 3:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							start_end = time_set[2].split('-')
							if len(start_end) != 2:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							if not checkHMS(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['StartTime'] = start_end[0]
							if not checkHMS(start_end[1]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['EndTime'] = start_end[1]
						elif time_set[1] == "每周":#周期 每周 周一 00:00:00-周日 11:11:11
							set['TimeSetType'] = 12
							if len(time_set) != 5:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							
							if time_set[2] in time_day:
								set['StartPeriod'] = time_day.index(time_set[2]) + 1
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							start_end = time_set[3].split('-')
							if len(start_end) != 2:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							if not checkHMS(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['StartTime'] = start_end[0]
							
							if start_end[1] in time_day:
								set['EndPeriod'] = time_day.index(start_end[1]) + 1
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							if not checkHMS(time_set[4]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['EndTime'] = time_set[4]
						elif time_set[1] == "每月":#周期 每月 1日 00:00:00-31日 00:00:00
							set['TimeSetType'] = 13
							if len(time_set) != 5:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							
							num_list = re.findall(r"\d+\.?\d*",time_set[2])
							if len(num_list) == 0:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['StartPeriod'] = num_list[0]
							start_end = time_set[3].split('-')
							if len(start_end) != 2:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							if not checkHMS(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['StartTime'] = start_end[0]
							num_list = re.findall(r"\d+\.?\d*",start_end[1])
							if len(num_list) == 0:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['EndPeriod'] = num_list[0]
							if not checkHMS(time_set[4]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
							else:
								set['EndTime'] = time_set[4]
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置错误\"}" % (j+1)
					if str(json_data['Set']).find(str(set)) != -1:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置重复\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行时间集合信息中配置重复\"}" % (j+1)
					else:
						order += 1
						json_data['Set'].append(set.copy())
				if j == len(all_data[9]) - 1:
					if cover == '1':
						sql = "select \"TimeSetId\" from public.\"TimeSet\" where \"Name\"=E'%s'" % json_data['Name'].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['TimeSetId'] = 0
						else:
							json_data['TimeSetId'] = result[0][0]
					else:
						json_data['TimeSetId'] = 0
					sql = "select public.\"PSaveTimeSet\"(E'%s',0,null)" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
					debug("sql11111:%s" % sql)
					curs.execute(sql)
			debug("endtime")
			#导入客户端集合
			json_data = {"ClientScopeId":0,"ClientScopeName":"雨天","IsApplyToServerScope":False,"IPList":{"IPSetId":0,"Set":[]},"MACList":{"MACSetId":0,"Set":[]}}
			ip_set = {"IPSetMemberId":0,"Order":1,"StartIP":"192.168.0.114","EndIP":"192.168.0.114"}
			mac_set = {"MACSetMemberId":0,"Order":1,"StartMACAddress":"00:ff:5a:4c:b3:11","EndMACAddress":"00:ff:5a:4c:b3:11"}
			ip_order = 0
			mac_order = 0
			for j,i in enumerate(all_data[10]):
				if j == 0 and i[0] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中名称不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中名称不能为空\"}" % (j+1)
				if i[0] != "" and j != 0:#保存客户端集合
					if cover == '1':
						sql = "select \"ClientScopeId\" from public.\"ClientScope\" where \"ClientScopeName\"=E'%s'" % json_data['ClientScopeName'].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['ClientScopeId'] = 0
						else:
							json_data['ClientScopeId'] = result[0][0]
					else:
						json_data['ClientScopeId'] = 0
					sql = "select public.\"PSaveClientScope\"(E'%s',0,null)" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
					debug("sql:%s" % sql)
					curs.execute(sql)
					json_data = {"ClientScopeId":0,"ClientScopeName":"雨天","IsApplyToServerScope":False,"IPList":{"IPSetId":0,"Set":[]},"MACList":{"MACSetId":0,"Set":[]}}
			
				if i[0] != "":#新的客户端集合
					debug("begin1")
					name = i[0].replace('\t','').decode('utf-8')
					if not checkname(name):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中名称格式错误\"}" % (j+1)
					debug("begin2")
					json_data['ClientScopeName'] = i[0]
				if i[1] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围不能为空\"}" % (j+1)
				else:
					start_end = i[1].split('-')
					if len(start_end) > 2:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
					elif len(start_end) == 2:
						if '.' in start_end[0]:#jixu
							if not checkip(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
							else:
								if not checkip(start_end[1]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
								else:
									ip_set['Order'] = ip_order + 1
									ip_set['StartIP'] = start_end[0]
									ip_set['EndIP'] = start_end[1]
									ip_order += 1
									json_data['IPList']['Set'].append(ip_set.copy())
						elif ':' in start_end[0]:#jixu
							if not checkmac(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
							else:
								if not checkmac(start_end[1]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
								else:
									mac_set['Order'] = mac_order + 1
									mac_set['StartMACAddress'] = start_end[0]
									mac_set['EndMACAddress'] = start_end[1]
									mac_order += 1
									json_data['MACList']['Set'].append(mac_set.copy())
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
					else:
						if '.' in start_end[0]:
							if not checkip(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
							else:
								ip_set['Order'] = ip_order + 1
								ip_set['StartIP'] = start_end[0]
								ip_set['EndIP'] = start_end[0]
								ip_order += 1
								json_data['IPList']['Set'].append(ip_set.copy())
						elif ':' in start_end[0]:
							if not checkmac(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
							else:
								mac_set['Order'] = mac_order + 1
								mac_set['StartMACAddress'] = start_end[0]
								mac_set['EndMACAddress'] = start_end[0]
								mac_order += 1
								json_data['MACList']['Set'].append(mac_set.copy())
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
				if j == len(all_data[10]) - 1:
					if cover == '1':
						sql = "select \"ClientScopeId\" from public.\"ClientScope\" where \"ClientScopeName\"=E'%s'" % json_data['ClientScopeName'].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['ClientScopeId'] = 0
						else:
							json_data['ClientScopeId'] = result[0][0]
					else:
						json_data['ClientScopeId'] = 0
					sql = "select public.\"PSaveClientScope\"(E'%s',0,null)" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
					debug("sql:%s" % sql)
					curs.execute(sql)
			
			#导入服务器集合
			json_data = {"ServerScopeId":0,"ServerScopeName":"yt_server2","IsApplyToClientScope":False,"HostList":[],"IPList":{"IPSetId":0,"Set":[]}}
			ip_set = {"IPSetMemberId":0,"Order":1,"StartIP":"1.1.1.1","EndIP":"255.255.255.253"}
			host_set = {"HGId":36,"HostId":3034}
			hg_set = {"HGId":73,"HostId":None,"IsGroupAuth":False}
			ip_order = 0
			hg_host_flag = 0
			server_flag = 0
			hostlist_len = 0
			for j,i in enumerate(all_data[11]):
				server_flag += 1
				if j == 0 and i[0] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中名称不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中名称不能为空\"}" % (j+1)
				if i[0] != "" and j != 0:#保存服务器集合
					server_flag = 1
					hostlist_len = 0
					if cover == '1':
						sql = "select \"ServerScopeId\" from public.\"ServerScope\" where \"ServerScopeName\"=E'%s'" % json_data['ServerScopeName'].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							json_data['ServerScopeId'] = 0
						else:
							json_data['ServerScopeId'] = result[0][0]
					else:
						json_data['ServerScopeId'] = 0
					sql = "select public.\"PSaveServerScope\"(E'%s',0,null)" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
					debug("sql:%s" % sql)
					curs.execute(sql)
					json_data = {"ServerScopeId":0,"ServerScopeName":"yt_server2","IsApplyToClientScope":False,"HostList":[],"IPList":{"IPSetId":0,"Set":[]}}
					ip_order = 0
					
				if i[0] != "":#新的服务器集合
					if i[1] != "":
						pass
					else:
						#hg_host_flag = 1
						if i[2] == "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP和主机组不能同时为空\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP和主机组不能同时为空\"}" % (j+1)
					json_data['ServerScopeName'] = i[0]
				'''
				if hg_host_flag == 1:
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中主机组格式错误\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中主机组格式错误\"}" % (j+1)
				'''
				if i[1] != "":
					if server_flag == len(json_data['IPList']['Set']) + 1:
						if '-' in i[1]:
							start_end = i[1].split('-')
							if not checkip(start_end[0]):
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1)
							else:
								if not checkip(start_end[1]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1)
								else:
									ip_order += 1
									ip_set['Order'] = ip_order
									ip_set['StartIP'] = start_end[0]
									ip_set['EndIP'] = start_end[1]
									json_data['IPList']['Set'].append(ip_set.copy())
						else:
							if not checkip(i[1]):
								debug("iiiiiiiiiii111111111")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1)
							else:
								ip_order += 1
								ip_set['Order'] = ip_order
								ip_set['StartIP'] = i[1]
								ip_set['EndIP'] = i[1]
								json_data['IPList']['Set'].append(ip_set.copy())
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器集合信息中IP格式错误\"}" % (j+1)
				if i[2] != "":
					debug("server_flag:%d" % server_flag)
					debug("hostlist_len:%d" % hostlist_len)
					if server_flag == hostlist_len + 1:
						path = i[2].split('/')#/qin500/qinzhu44*主机  /qin500/qinzhu44按主机 /qin500/qinzhu44/*组 /qin500/qinzhu44/按组
						debug("path:%s" % str(path))
						if len(path) < 2:
							conn.rollback()
							debug("path<2")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中组路径格式错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中组路径格式错误\"}" % (j+1)
						else:
							if path[0] != "":
								conn.rollback()
								debug("path1111111")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中组路径格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中组路径格式错误\"}" % (j+1)
							if path[-1] == '*':#主机组
								hg_flag = 1
								hg_set['IsGroupAuth'] == False
							elif path[-1] == "":
								hg_flag = 1
								hg_set['IsGroupAuth'] == True
							else:
								hg_flag = 0
								if path[-1][-1] == '*':
									#hname = path[-1][:-1]
									hip = path[-1][:-1]
								else:
									#hname = path[-1]
									hip = path[-1]
								if not checkip(hip):
									conn.rollback()
									debug("path1111111")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中服务器/服务器范围格式错误\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中服务器/服务器范围格式错误\"}" % (j+1)
								#sql = 'select "HostId" from public."Host" where "HostName"=\'%s\'' % hname.decode('utf-8')
								sql = 'select "HostId" from public."Host" where "HostIP"=E\'%s\'' % hip
								curs.execute(sql)
								result = curs.fetchall()#[0][0]
								if len(result) != 0:
									host_set['HostId'] = result[0][0]
								else:
									hostlist_len += 1
									continue
						'''
						if hg_flag == 1:
							Iter_obj = path[1:-1]
						else:
							Iter_obj = path[1:-1]
						'''
						for hg_i,hg_name in enumerate(path[1:-1]):
							if not checkname(hg_name.decode('utf-8')):
								conn.rollback()
								debug("path333333333")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中组路径格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中组路径格式错误\"}" % (j+1)
							if hg_i == 0:
								sql = 'select "HGroup"."HGId" from "HGroup" where "HGroup"."ParentHGId" = 0 and "HGroup"."HGName" = E\'%s\';' % hg_name.decode('utf-8') #判断第一层是否存在
							else:
								sql = 'select "HGroup"."HGId" from "HGroup" where "HGroup"."ParentHGId" = %d and "HGroup"."HGName" = E\'%s\';' % (hgid_list[0][0],hg_name.decode('utf-8'))
							debug("uuuuuuuuuuuuuu")
							debug("sql1:%s" % sql)
							curs.execute(sql)
							hgid_list = curs.fetchall()
							debug(str(hgid_list))
							if len(hgid_list) == 0:
								hostlist_len += 1
								break
							if hg_i == len(path[1:-1]) - 1:
								hostlist_len += 1
								if hg_flag == 0:
									host_set['HGId'] = hgid_list[0][0]
									debug("host---------")
									debug("hostlist:%s" % str(json_data['HostList']))
									json_data['HostList'].append(host_set.copy())
								else:
									hg_set['HGId'] = hgid_list[0][0]
									hg_set['HostId'] = None
									debug("hg---------")
									debug("%s" % (json_data['HostList']))
									json_data['HostList'].append(hg_set.copy())
						debug("j:%d" % j)
						debug("datalen:%d" % len(all_data[11]))
						if j == len(all_data[11]) - 1:
							if cover == '1':
								sql = "select \"ServerScopeId\" from public.\"ServerScope\" where \"ServerScopeName\"=E'%s'" % json_data['ServerScopeName'].decode('utf-8')
								curs.execute(sql)
								result = curs.fetchall()#[0][0]
								if len(result) == 0:
									json_data['ServerScopeId'] = 0
								else:
									json_data['ServerScopeId'] = result[0][0]
							else:
								json_data['ServerScopeId'] = 0
							sql = "select public.\"PSaveServerScope\"(E'%s',0,null)" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
							debug("sql:%s" % sql)
							curs.execute(sql)
					else:
						if i[1] == "":
							conn.rollback()
							debug("path444444444")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中IP和组路径不能同时为空\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行服务器信息中IP和组路径不能同时为空\"}" % (j+1)
			debug("server_end")
			#导入授权
			json_data = {"AccessAuthId":0,"AccessAuthName":"zzzzz","IsHigherLevelSend":False,"Action":1,"AuthMode":1,"AuthService":None,"AuthAccountId":"","AuthConnParamId":None,"EffectiveTime":"2018-3-30 13:35:41","Enabled":True,"AdminSet":[],"AuthUserSet":[],"AuthScope":[],"AuthServiceSet":[],"AuthObject":[],"AccessStrategyInfo":{"Type":2,"AccessStrategyId":0,"AccessStrategyType":1,"AccessStrategyName":None,"EnableRDPClipboard":3,"EnableRDPDiskMap":True,"EnableRDPKeyRecord":True,"EnableRDPFileRecord":False,"EnableSSHFileTrans":3,"EnableSSHFileRecord":False,"EnableFTPFileTrans":3,"EnableFTPFileRecord":False,"EnableApprove":False,"EnableAccessInfo":False,"EnableAlarm":False,"EnableDoubleCollaboration":False,"EnableWorkOrderApprove":False,"ClientScopeAction":None,"TimeAction":None,"PreCmd":None,"ApproveStrategyId":None,"ApproveStrategyName":None,"EventAlarmInfoId":None,"EventAlarmInfoName":None,"WorkOrderApproveStrategyId":None,"WorkOrderApproveStrategyName":None,"ClientScopeConfig":[],"TimeConfig":[]},"DeleteAuthObject":[],"LoginUserCode":"zdp","AuthAccountName":None}
			json_data['LoginUserCode'] = usercode
			admin_set = {"AdminId":22}
			user_set = {"Id":202,"Type":1}
			ug_set = {"Id":441,"Type":2,"IsGroupAuth":False}
			host_set = {"HGId":1,"HostId":56400,"IsGroupAuth":False}
			hg_set = {"HGId":1,"HostId":None,"IsGroupAuth":False}
			account_set = {"HGId":1,"HostId":56400,"HostServiceId":5808,"AccountId":6}
			Service_Set = {"ProtocolId":2,"Port":22,"ConnParamId":None}
			AuthScope = {"ServerScopeId":96,"Type":1,"HostList":None,"IPList":None}
			account_list = []
			timeconfig = {"Order":1,"TimeSetId":0,"Type":1,"Set":[]}
			clientconfig = {"Order":0,"ClientScopeId":0,"Type":1,"IPList":{"IPSetId":0,"Set":[]},"MACList":{"MACSetId":0,"Set":[]}}
			ip_set = {"IPSetMemberId":0,"Order":1,"StartIP":"1.1.1.1","EndIP":"1.1.1.1"}
			mac_set = {"MACSetMemberId":0,"Order":1,"StartMACAddress":"12:21:21:21:21:21","EndMACAddress":"12:21:21:21:21:21"}
			order = 0
			auth_flag = 0#一行授权行数
			userlist_len = 0
			auth_hostlist_len = 0
			ip_order = 0
			mac_order = 0
			auth_service_flag = 0
			auth_account_flag = 0
			save_auth_succ = 0
			save_auth_fail = 0
			auth_scope_len = 0
			auth_admin_len = 0
			warn_info_list = []
			debug("%s" % all_data[12])
			sql = 'select public."PGetManagedScope"(E\'%s\')' % usercode
			curs.execute(sql)
			result = curs.fetchall()#[0][0]
			debug("zzz:%s" % str(result))
			if len(result) != 0:
				manage_scope = json.loads(result)
			else:
				manage_scope = None
			
			for j,i in enumerate(all_data[12]):
				x = 0
				while len(i) < 31:
					i.append('')
				auth_flag += 1
				if j == 0 and i[0] == "":
					debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中名称不能为空\"}" % (j+1))
					conn.rollback()
					return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中名称不能为空\"}" % (j+1)
				if i[0] != "" and j != 0:#保存访问授权
					auth_isexist = 0
					auth_flag = 1
					if len(json_data['AdminSet']) == 0:
						sql = "select \"UserId\" from public.\"User\" where \"UserCode\"=E\'%s\'" % usercode
						curs.execute(sql)
						debug("sql:%s" % sql)
						admin_set['AdminId'] = curs.fetchall()[0][0]
						json_data['AdminSet'].append(admin_set.copy())
					if time_action_flag == 1:
						json_data['AccessStrategyInfo']['TimeConfig'].append(timeconfig.copy())
					if client_action_flag == 1:#自定义
						json_data['AccessStrategyInfo']['ClientScopeConfig'].append(clientconfig.copy())
					if len(account_list) != 0:
						json_data['AuthAccountId'] = ','.join(account_list)
					sql = "select \"AccessAuthId\" from public.\"AccessAuth\" where \"AccessAuthName\"=E'%s'" % json_data['AccessAuthName'].decode('utf-8')
					curs.execute(sql)
					result = curs.fetchall()#[0][0]
					debug("result----------:%s" % str(result))
					if json_data['AccessStrategyInfo']['ApproveStrategyName'] != None:
						if json_data['AccessStrategyInfo']['ApproveStrategyName'] in invalid_approve_strategy:
							warn_info_list.append("登录审批策略无效，该授权停用")
							json_data['Enabled'] = False
					
					if json_data['AccessStrategyInfo']['WorkOrderApproveStrategyName'] != None:
						if json_data['AccessStrategyInfo']['WorkOrderApproveStrategyName'] in invalid_approve_strategy:
							warn_info_list.append("工单审批策略无效，该授权停用")
							json_data['Enabled'] = False
					
					if json_data['AccessStrategyInfo']['EventAlarmInfoName'] != None:
						if json_data['AccessStrategyInfo']['EventAlarmInfoName'] in invalid_alarm_strategy:
							warn_info_list.append("事件告警策略无效，该授权停用")
							json_data['Enabled'] = False
					
					if cover == '1':
						if len(result) == 0:
							json_data['AccessAuthId'] = 0
							AccessAuthId = 0
							if json_data['AccessStrategyInfo']['AccessStrategyName'] == None:
								json_data['AccessStrategyInfo']['AccessStrategyId'] = 0
							else:
								sql = "select public.\"PGetAccessStrategyByName\"(E'%s')" % json_data['AccessStrategyInfo']['AccessStrategyName'].decode('utf-8')
								curs.execute(sql)
								result = curs.fetchall()[0][0]
								json_data['AccessStrategyInfo']['AccessStrategyId'] = result
						else:
							json_data['AccessAuthId'] = result[0][0]
							AccessAuthId = json_data['AccessAuthId']
							get_data = '{"loginusercode":"'+usercode+'","accessauthid":'+str(json_data['AccessAuthId'])+',"limitrow":null,"offsetrow":null}'
							get_data = "E'%s'" % get_data
							curs.execute('select public."PGetAccessAuth"(%s)' % get_data)
							results = curs.fetchall()[0][0].encode('utf-8')
							debug("resultssssss:%s" % results)
							re_result = json.loads(results)
							#re_result['data'][0]['AuthObject']jixu
							#same_list = []
							#dif_list = []
							if len(re_result['data']) != 0:
								debug("straname:%s" % str(json_data['AccessStrategyInfo']['AccessStrategyName']))
								if json_data['AccessStrategyInfo']['AccessStrategyName'] == None:		
									if re_result['data'][0]['AccessStrategyInfo'] != None and re_result['data'][0]['AccessStrategyInfo']['AccessStrategyName'] == None:
										json_data['AccessStrategyInfo']['AccessStrategyId'] = re_result['data'][0]['AccessStrategyInfo']['AccessStrategyId']
									else:
										json_data['AccessStrategyInfo']['AccessStrategyId'] = 0
								else:
									sql = "select public.\"PGetAccessStrategyByName\"(E'%s')" % json_data['AccessStrategyInfo']['AccessStrategyName'].decode('utf-8')
									curs.execute(sql)
									result = curs.fetchall()[0][0]
									debug("result11111:%s" % result)
									json_data['AccessStrategyInfo']['AccessStrategyId'] = result	
								
								debug("obj1:%s" % str(re_result['data'][0]['AuthObject']))
								debug("obj2:%s" % str(json_data['AuthObject']))
								if re_result['data'][0]['AuthObject'] != None:
									for item in re_result['data'][0]['AuthObject']:
										for index,item1 in enumerate(json_data['AuthObject']):
											if item['HGId'] == item1['HGId']:
												if item['HostId'] == item1['HostId']:
													if item['HostId'] == None:#主机组按组
														#same_list.append(item1)
														json_data['AuthObject'].pop(index)
													else:
														if item1.has_key('AccountId'):#账号
															if item['HostServiceId'] == item1['HostServiceId'] and item['AccountId'] == item1['AccountId']:
																#same_list.append(item1)
																json_data['AuthObject'].pop(index)
															else:
																#dif_list.append(item)
																json_data['DeleteAuthObject'].append(item)
														else:
															#same_list.append(item1)#主机按组
															json_data['AuthObject'].pop(index)
												else:
													#dif_list.append(item)
													json_data['DeleteAuthObject'].append(item)
											else:
												#dif_list.append(item)
												json_data['DeleteAuthObject'].append(item)
							else:
								auth_isexist = 1
								ErrorLog = "该授权已存在且不属于该账号"
								status = 1
					else:
						json_data['AccessAuthId'] = 0
						if len(result) != 0:
							AccessAuthId = result[0][0]
					if auth_isexist != 1:
						json_data['EffectiveTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						sql = "select public.\"PSaveAccessAuth\"(E'%s')" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
						debug("sql:%s" % sql)
						curs.execute(sql)
						result = curs.fetchall()[0][0].encode('utf-8')
						auth_result = json.loads(result)
						if auth_result['Result']:
							save_auth_succ += 1
							ErrorLog = '，'.join(warn_info_list)
							status = 0
							AccessAuthId = auth_result['AccessAuthId']
						else:
							save_auth_fail += 1
							ErrorLog = auth_result['ErrMsg']
							status = 1
						debug("auth_result:%s" % str(auth_result))
					
					sql = "insert into private.\"AuthImportTaskDetail\"(\"AuthName\",\"AuthId\",\"ErrorLog\",\"AuthImportTaskId\",\"Status\")values(E'%s',%d,E'%s',%d,%d)" % (json_data['AccessAuthName'].decode('utf-8'),AccessAuthId,ErrorLog,int(taskid),status)
					debug("insert_sq1111l:%s" % sql)
					curs.execute(sql)
					json_data = {"AccessAuthId":0,"AccessAuthName":"zzzzz","IsHigherLevelSend":False,"Action":1,"AuthMode":1,"AuthService":None,"AuthAccountId":"","AuthConnParamId":None,"EffectiveTime":"2018-3-30 13:35:41","Enabled":True,"AdminSet":[],"AuthUserSet":[],"AuthScope":[],"AuthServiceSet":[],"AuthObject":[],"AccessStrategyInfo":{"Type":2,"AccessStrategyId":0,"AccessStrategyType":1,"AccessStrategyName":None,"EnableRDPClipboard":3,"EnableRDPDiskMap":True,"EnableRDPKeyRecord":True,"EnableRDPFileRecord":False,"EnableSSHFileTrans":3,"EnableSSHFileRecord":False,"EnableFTPFileTrans":3,"EnableFTPFileRecord":False,"EnableApprove":False,"EnableAccessInfo":False,"EnableAlarm":False,"EnableDoubleCollaboration":False,"EnableWorkOrderApprove":False,"ClientScopeAction":None,"TimeAction":None,"PreCmd":None,"ApproveStrategyId":None,"ApproveStrategyName":None,"EventAlarmInfoId":None,"EventAlarmInfoName":None,"WorkOrderApproveStrategyId":None,"WorkOrderApproveStrategyName":None,"ClientScopeConfig":[],"TimeConfig":[]},"DeleteAuthObject":[],"LoginUserCode":"zdp","AuthAccountName":None}
					json_data['LoginUserCode'] = usercode
					account_list = []
					timeconfig = {"Order":1,"TimeSetId":0,"Type":1,"Set":[]}
					clientconfig = {"Order":0,"ClientScopeId":0,"Type":1,"IPList":{"IPSetId":0,"Set":[]},"MACList":{"MACSetId":0,"Set":[]}}
					ip_set = {"IPSetMemberId":0,"Order":1,"StartIP":"1.1.1.1","EndIP":"1.1.1.1"}
					mac_set = {"MACSetMemberId":0,"Order":1,"StartMACAddress":"12:21:21:21:21:21","EndMACAddress":"12:21:21:21:21:21"}
					userlist_len = 0
					order = 0
					auth_hostlist_len = 0
					ip_order = 0
					mac_order = 0
					auth_service_flag = 0
					auth_account_flag = 0
					auth_scope_len = 0
					auth_admin_len = 0
					warn_info_list = []
				if i[0] != "":#新的访问授权
					debug("i[0]:%s" % i[0])
					if not checkname(i[0].decode('utf-8')):
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中名称格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中名称格式错误\"}" % (j+1)
					
					if i[1] == "" or i[1] == "是":
						json_data['Enabled'] = True
					elif i[1] == "否":
						json_data['Enabled'] = False
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中启用授权格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中启用授权格式错误\"}" % (j+1)
					
					if i[2] == "" or i[2] == "允许":
						json_data['Action'] = 1
					elif i[2] == "拒绝":
						json_data['Action'] = 2
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中授权动作格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中授权动作格式错误\"}" % (j+1)
					#管理者、用户组用户稍后加
					'''
					if i[3] == "":
						sql = "select \"UserId\" from public.\"User\" where \"UserCode\"='%s'" % usercode.decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()
						if len(result) != 0:
							AdminId = result[0][0]
							sql = "select public.\"PGetPermissions\"('%s')" % usercode.decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()[0][0]
							perm_result = json.loads(result)#jixu
							perm_flag = 0
							for perm_item in perm_result:
								if perm_item['SubMenuId'] == 15 and perm_item['Mode'] == 2:
									perm_flag = 1
									break
							if perm_flag == 1:
								admin_set['AdminId'] = AdminId
								json_data['AdminSet'].append(admin_set.copy())
					'''
					'''
					if i[3] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中管理者不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中管理者不能为空\"}" % (j+1)
					else:
						if not checkname(i[3].decode('utf-8')):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中管理者格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中管理者格式错误\"}" % (j+1)
					'''		
					if i[4] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组/用户不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组/用户不能为空\"}" % (j+1)
					if i[5] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定不能为空\"}" % (j+1)
					debug("55555555555555555555555555")
					if i[5] == "对象指定":
						json_data["AuthMode"] = 1
						if i[6] == "" and i[7] == "" and i[8] == "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围、服务、账号不能同时为空\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围、服务、账号不能同时为空\"}" % (j+1)
					else:
						mode_list = i[5].split('|')#范围指定|已定义|所有
						if len(mode_list) == 2:
							if mode_list[0] == "范围指定" and mode_list[1] == "自定义":
								json_data["AuthMode"] = 4#范围自定义
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1)
						elif len(mode_list) == 3:
							if mode_list[0] == "范围指定":
								if mode_list[1] == "已定义":
									if mode_list[2] == "所有":
										json_data["AuthMode"] = 3
									elif mode_list[2] == "共有":
										json_data["AuthMode"] = 2
									else:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1)
								else:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1)
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定/范围指定格式错误\"}" % (j+1)
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定//范围指定格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中对象指定//范围指定格式错误\"}" % (j+1)
						if i[6] == "" or i[7] == "" or i[8] == "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围、服务、账号不能同时为空\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围、服务、账号不能同时为空\"}" % (j+1)
							
					debug("55555555555555555555555555end")
						
					if i[9] == "":
						json_data['AccessStrategyInfo']['Type'] = 2
						json_data['AccessStrategyInfo']['AccessStrategyName'] = None
					else:
						json_data['AccessStrategyInfo']['Type'] = 1
						if not checkname(i[9].decode('utf-8')):
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中访问策略名称格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中访问策略名称格式错误\"}" % (j+1)
						else:
							'''
							sql = "select public.\"PGetAccessStrategyByName\"('%s')" % i[9].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()[0][0]
							debug("resultzzzzzuuuuuuuuuuuuuu:%s" % result)
							if result != 0:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中访问策略名称已存在\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中访问策略名称已存在\"}" % (j+1)
							else:
							'''
							json_data['AccessStrategyInfo']['AccessStrategyName'] = i[9]
					debug("2999999999999999999999yhnyn")		
					#稍后添加（服务器范围/主机组/主机/服务/账号）
					if i[10] == "" or i[10] == "否":
						json_data['AccessStrategyInfo']['EnableApprove'] = False
					else:
						json_data['AccessStrategyInfo']['EnableApprove'] = True
						sql = "select \"ApproveStrategyId\" from \"ApproveStrategy\" where \"ApproveStrategyName\"=E'%s'" % i[10].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中登录审批策略不存在\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中登录审批策略不存在\"}" % (j+1)
						else:
							json_data['AccessStrategyInfo']['ApproveStrategyId'] = result[0][0]
					
					if i[11] == "" or i[11] == "否":
						json_data['AccessStrategyInfo']['EnableDoubleCollaboration'] = False
					elif i[11] == "是":
						json_data['AccessStrategyInfo']['EnableDoubleCollaboration'] = True
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中协同登录格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中协同登录格式错误\"}" % (j+1)
					
					if i[12] == "" or i[12] == "否":
						json_data['AccessStrategyInfo']['EnableAccessInfo'] = False
					elif i[12] == "是":
						json_data['AccessStrategyInfo']['EnableAccessInfo'] = True
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中访问备注格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中访问备注格式错误\"}" % (j+1)
					
					if i[13] == "" or i[13] == "否":
						json_data['AccessStrategyInfo']['EnableWorkOrderApprove'] = False
						json_data['AccessStrategyInfo']['WorkOrderApproveName'] = None
					else:
						json_data['AccessStrategyInfo']['EnableWorkOrderApprove'] = True
						sql = "select \"ApproveStrategyId\" from \"ApproveStrategy\" where \"ApproveStrategyName\"=E'%s'" % i[13].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中工单审批策略不存在\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中工单审批策略不存在\"}" % (j+1)
						else:
							json_data['AccessStrategyInfo']['WorkOrderApproveStrategyId'] = result[0][0]
							json_data['AccessStrategyInfo']['WorkOrderApproveName'] = i[13]
					if i[14] == "" or i[14] == "否":
						json_data['AccessStrategyInfo']['EnableAlarm'] = False
						json_data['AccessStrategyInfo']['EventAlarmInfoName'] = None
					else:
						json_data['AccessStrategyInfo']['EnableAlarm'] = True
						sql = "select \"EventAlarmInfoId\" from \"EventAlarmInfo\" where \"Name\"=E'%s'" % i[14].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中事件告警不存在\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中事件告警不存在\"}" % (j+1)
						else:
							json_data['AccessStrategyInfo']['EventAlarmInfoId'] = result[0][0]
							json_data['AccessStrategyInfo']['EventAlarmInfoName'] = i[4]
					#是否1 否是2 是是3
					if i[15] == "" or i[15] == "是":
						EnableRDPClipboard = 1
					elif i[15] == "否":
						EnableRDPClipboard = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中RDP剪贴板上传格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中RDP剪贴板上传格式错误\"}" % (j+1)
					if i[16] == "" or i[16] == "是":
						EnableRDPClipboard += 2
					elif i[16] == "否":
						EnableRDPClipboard += 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中RDP剪贴板下载格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中RDP剪贴板下载格式错误\"}" % (j+1)
					
					if i[17] == "是":
						json_data['AccessStrategyInfo']['EnableRDPFileRecord'] = True
					elif i[17] == "" or i[17] == "否":
						json_data['AccessStrategyInfo']['EnableRDPFileRecord'] = False
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中RDP文件记录格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中RDP文件记录格式错误\"}" % (j+1)
					
					if i[18] == "" or i[18] == "是":
						json_data['AccessStrategyInfo']['EnableRDPDiskMap'] = True
					elif i[18] == "否":
						json_data['AccessStrategyInfo']['EnableRDPDiskMap'] = False
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中磁盘映射格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中磁盘映射格式错误\"}" % (j+1)
					
					if i[19] == "" or i[19] == "是":
						json_data['AccessStrategyInfo']['EnableRDPKeyRecord'] = True
					elif i[19] == "否":
						json_data['AccessStrategyInfo']['EnableRDPKeyRecord'] = False
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中键盘记录格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中键盘记录格式错误\"}" % (j+1)
					
					if i[20] == "" or i[20] == "是":
						EnableSSHFileTrans = 1
					elif i[20] == "否":
						EnableSSHFileTrans = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中SSH文件上传格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中SSH文件上传格式错误\"}" % (j+1)
					
					if i[21] == "" or i[21] == "是":
						EnableSSHFileTrans += 2
					elif i[21] == "否":
						EnableSSHFileTrans += 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中SSH文件下载格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中SSH文件下载格式错误\"}" % (j+1)
					debug("2999999999999999999999zzzzzzzz")
					if i[22] == "是":
						json_data['AccessStrategyInfo']['EnableSSHFileRecord'] = True
					elif i[22] == "" or i[22] == "否":
						json_data['AccessStrategyInfo']['EnableSSHFileRecord'] = False
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中SSH文件记录格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中SSH文件记录格式错误\"}" % (j+1)
					
					if i[23] == "" or i[23] == "是":
						EnableFTPFileTrans = 1
					elif i[23] == "否":
						EnableFTPFileTrans = 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中FTP文件上传格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中FTP文件上传格式错误\"}" % (j+1)
					
					if i[24] == "" or i[24] == "是":
						EnableFTPFileTrans += 2
					elif i[24] == "否":
						EnableFTPFileTrans += 0
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中FTP文件下载格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中FTP文件下载格式错误\"}" % (j+1)
					
					if i[25] == "是":
						json_data['AccessStrategyInfo']['EnableFTPFileRecord'] = True
					elif i[25] == "" or i[25] == "否":
						json_data['AccessStrategyInfo']['EnableFTPFileRecord'] = False
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中FTP文件记录格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中FTP文件记录格式错误\"}" % (j+1)
					debug("299999999999999999999911111111")
					#不限制/允许|自定义/例外|自定义
					'''
					if i[26] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\"}" % (j+1)
					'''
					if i[26] == "" or i[26] == "不限制":
						json_data['AccessStrategyInfo']['TimeAction'] = 3
						if i[27] != "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间范围格式错误\"}" % (j+1)
						time_action_flag = 0
					else:
						time_action = i[26].split('|')
						debug("i26:%s" % i[26])
						if len(time_action) != 2:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno)
						if time_action[0] == "允许" or time_action[0] == "例外":
							if time_action[0] == "允许":
								json_data['AccessStrategyInfo']['TimeAction'] = 1
							else:
								json_data['AccessStrategyInfo']['TimeAction'] = 2
							if time_action[1] == "自定义":
								time_action_flag = 1
							elif time_action[1] == "已定义":
								time_action_flag = 2
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno)			
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间生效范围不能为空\",%d}" % (j+1,sys._getframe().f_lineno)
						if i[27] == "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间范围不能为空\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间范围不能为空\"}" % (j+1)
					debug("2999999999999999999999")
					#时间范围(时间集合/时间设置)稍后添加
					'''
					if i[28] == "":
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围不能为空\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围不能为空\"}" % (j+1)
					'''
					if i[28] == "" or i[28] == "不限制":
						json_data['AccessStrategyInfo']['ClientScopeAction'] = 3
						if i[29] != "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1)
						client_action_flag = 0
					else:
						client_action = i[28].split('|')
						if len(client_action) != 2:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1)
						if client_action[0] == "允许" or client_action[0] == "例外":
							if client_action[0] == "允许":
								json_data['AccessStrategyInfo']['ClientScopeAction'] = 1
							else:
								json_data['AccessStrategyInfo']['ClientScopeAction'] = 2
							if client_action[1] == "自定义":
								client_action_flag = 1
							elif client_action[1] == "已定义":
								if not checkname(i[29].decode('utf-8')):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1)
								client_action_flag = 2
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1)			
						else:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围格式错误\"}" % (j+1)
						if i[29] == "":
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围不能为空\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端范围不能为空\"}" % (j+1)
					debug("2999999999999999999999end")	
					json_data['AccessAuthName'] = i[0]
					json_data['AccessStrategyInfo']['EnableRDPClipboard'] = EnableRDPClipboard
					json_data['AccessStrategyInfo']['EnableSSHFileTrans'] = EnableSSHFileTrans
					json_data['AccessStrategyInfo']['EnableFTPFileTrans'] = EnableFTPFileTrans
					debug("3030303030303030303033")
					if i[30] != "":
						json_data['AccessStrategyInfo']['PreCmd'] = base64.b64encode(i[30])
					else:
						json_data['AccessStrategyInfo']['PreCmd'] = None
					debug("3030303030303030303033end")
				#管理者
				debug("guanlizhe")
				if i[3] != "":
					if auth_flag == auth_admin_len + 1:
						auth_admin_len += 1
						sql = "select \"UserId\" from public.\"User\" where \"UserCode\"=E'%s'" % i[3].decode('utf-8')
						debug("sql:%s" % sql)
						curs.execute(sql)
						result = curs.fetchall()
						debug("resulttttttttttttttttt:%s" % result)
						if len(result) != 0:
							AdminId = result[0][0]
							sql = "select public.\"PGetPermissions\"(E'%s')" % i[3].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()[0][0]
							debug("resultzzzzz:%s" % result)
							perm_admin_result = json.loads(result)#jixu
							perm_admin_flag = 0
							for perm_item in perm_admin_result:
								if perm_item['SubMenuId'] == 15 and perm_item['Mode'] == 2:
									perm_admin_flag = 1
									break
							if perm_admin_flag == 1:
								admin_set['AdminId'] = AdminId
								json_data['AdminSet'].append(admin_set.copy())
					else:
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中管理者格式错误\"}" % (j+1))
						conn.rollback()
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中管理者格式错误\"}" % (j+1)
				debug("i[4]")
				debug("userlist_len:%d" % userlist_len)
				if i[4] != "":
					if auth_flag == userlist_len + 1:
						if '/' in i[4]:#用户组 /用户组1/ 按组 /用户组1/* 组 
							path = i[4].split('/')
							debug("yonghuL:%s" % str(path))
							if path[0] != "":
								conn.rollback()
								debug("path1111111")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1)
							if path[-1] == '*':#用户组\*
								ug_set['IsGroupAuth'] == False
							elif path[-1] == "":
								ug_set['IsGroupAuth'] == True
							else:
								conn.rollback()
								debug("path1111111")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1)
							
							for ug_i,ug_name in enumerate(path[1:-1]):
								if not checkname(ug_name.decode('utf-8')):
									conn.rollback()
									debug("path333333333")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1)
								if ug_i == 0:
									sql = 'select "UGroup"."UGId" from "UGroup" where "UGroup"."ParentUGId" = 0 and "UGroup"."UGName" = E\'%s\';' % ug_name.decode('utf-8') #判断第一层是否存在
								else:
									sql = 'select "UGroup"."UGId" from "UGroup" where "UGroup"."ParentUGId" = %d and "UGroup"."UGName" = E\'%s\';' % (ugid_list[0][0],ug_name.decode('utf-8'))
								debug("uuuuuuuuuuuuuu")
								debug("sql2:%s" % sql)
								curs.execute(sql)
								ugid_list = curs.fetchall()
								debug(str(ugid_list))
								if len(ugid_list) == 0:
									userlist_len += 1
									break
								if ug_i == len(path[1:-1]) - 1:
									userlist_len += 1
									ug_set['Id'] = ugid_list[0][0]
									debug("ug---------")
									json_data['AuthUserSet'].append(ug_set.copy())					
						else:
							if not checkname(i[4].decode('utf-8')):
								conn.rollback()
								debug("path333333333")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户格式错误\"}" % (j+1)
							userlist_len += 1
							sql = "select \"UserId\" from public.\"User\" where \"UserCode\"=E'%s'" % i[4].decode('utf-8')
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) != 0:
								user_set['Id'] = result[0][0]
								json_data['AuthUserSet'].append(user_set.copy())
					else:
						conn.rollback()
						debug("path333333333444445555555")
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1))
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中用户组路径格式错误\"}" % (j+1)
				debug("i[6]")
				
				if i[6] != "":
					debug("AuthMode:%d" % json_data["AuthMode"])
					if json_data["AuthMode"] == 1:#对象
						if i[7] == "" or i[8] == "":
							conn.rollback()
							debug("path<2")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务账号不能为空\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务账号不能为空\"}" % (j+1)
						if auth_flag == auth_hostlist_len + 1:
							auth_hostlist_len += 1
							if not checkip(i[6]):
								path = i[6].split('/')
								debug("path:%s" % str(path))
								if len(path) < 2:
									conn.rollback()
									debug("path<2")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
								else:
									if path[0] != "":
										conn.rollback()
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1))
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
									debug("uuuuuuuuuuuuuuuuuuuuuuuu")
									save_obj_type = 0
									if path[-1] == "":#主机组
										auth_hg_flag = 1
										if i[7] == "*":#按组
											if i[8] == "*":#按组
												save_obj_type = 1
												hg_set['IsGroupAuth'] == True
											else:
												conn.rollback()
												debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1))
												return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
										else:#指定服务下账号
											if i[8] == '*':
												save_obj_type = 2#该服务下所有账号
											else:
												save_obj_type = 3#该服务下指定账号
									else:#主机
										auth_hg_flag = 0
										#hname = path[-1]
										#sql = 'select "HostId" from public."Host" where "HostName"=\'%s\'' % hname.decode('utf-8')
										hip = path[-1]
										sql = 'select "HostId" from public."Host" where "HostIP"=E\'%s\'' % hip
										debug("sql:%s" % sql)
										curs.execute(sql)
										HostId_list = curs.fetchall()
										debug("result11111111:%s" % str(HostId_list))
										if len(HostId_list) != 0:
											if manage_scope != None:
												accord_scope = filter_scope(1,manage_scope,HostId_list[0][0])
												if len(accord_scope) == 0:
													#auth_hostlist_len += 1
													pass
												else:
													host_set['HostId'] = HostId_list[0][0]
													account_set['HostId'] = HostId_list[0][0]
											else:
												host_set['HostId'] = HostId_list[0][0]
												account_set['HostId'] = HostId_list[0][0]
										else:
											#auth_hostlist_len += 1
											pass
										if i[7] == '*':#主机按主机
											save_obj_type = 1
											host_set['IsGroupAuth'] = True
										else:#主机指定服务
											if i[8] == '*':#该服务下所有账号
												save_obj_type = 2
											else:#该服务下指定账号
												save_obj_type = 3
									if save_obj_type == 1:#按组
										pass
									elif save_obj_type == 2:#按该服务下所有账号
										if auth_hg_flag == 0:#主机
											'''
											curs.execute('select public."PGetHost"(%d,false,null)' % (HostId_list[0][0]))
											host_json = curs.fetchall()[0][0].encode('utf-8')
											host_json = json.loads(host_json)
											effect_ser_list = []
											ser_list = i[7].split('/')
											#获取所有的服务
											for serviceset in host_json['ServiceSet']:
												for sername in ser_list:
													if serviceset['HostServiceName'] == sername:
														effect_ser_list.append(sername)
														break
											
											#服务下的账号
											for accountset in host_json['AccountSet']:
												for host_service_set in accountset['HostServiceSet']:
													if host_service_set['HostServiceName'] in effect_ser_list:
														account_set['HostServiceId'] = host_service_set['HostServiceId']
														account_set['AccountId'] = accountset['HostAccount']['AccountId']
														json_data['AuthObject'].append(account_set.copy())
														break
											'''
										else:#主机组
											ser_list = i[7].split('/')
											#取该主机组下所有该服务下的所有账号
									elif save_obj_type == 3:#该服务下指定账号
										if auth_hg_flag == 0:
											'''
											account_ser_list = i[8].split('|')
											#ser_list = i[7].split('/')
											curs.execute('select public."PGetHost"(%d,false,null)' % (HostId_list[0][0]))
											host_json = curs.fetchall()[0][0].encode('utf-8')
											host_json = json.loads(host_json)
											for account_ser in account_ser_list:
												a_s_list = account_ser.split(':')
												s_list = a_s_list[1].split('&')
												if len(a_s_list) != 2:
													conn.rollback()
													debug("path1111111")
													debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1))
													return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
												for accountset in host_json['AccountSet']:
													if accountset['HostAccount']['AccountName'] == a_s_list[0]:
														for account_ser in accountset['HostServiceSet']:
															if account_ser['HostServiceName'] in s_list:
																account_set['HostServiceId'] = account_ser['HostServiceId']
																account_set['AccountId'] = accountset['HostAccount']['AccountId']
																json_data['AuthObject'].append(account_set.copy())
																break
											'''
										else:#主机组下的该服务下指定账号
											#account_ser_list = i[8].split('|')
											pass
								debug("11111111111111111")
								debug("path[1:-1]:%s" % str(path[1:-1]))
								for hg_i,hg_name in enumerate(path[1:-1]):
									if not checkname(hg_name.decode('utf-8')):
										conn.rollback()
										debug("path333333333")
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1))
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
									if hg_i == 0:
										sql = 'select "HGroup"."HGId" from "HGroup" where "HGroup"."ParentHGId" = 0 and "HGroup"."HGName" = E\'%s\';' % hg_name.decode('utf-8') #判断第一层是否存在
									else:
										sql = 'select "HGroup"."HGId" from "HGroup" where "HGroup"."ParentHGId" = %d and "HGroup"."HGName" = E\'%s\';' % (hgid_list[0][0],hg_name.decode('utf-8'))
									debug("uuuuuuuuuuuuuu")
									debug("sql3:%s" % sql)
									curs.execute(sql)
									hgid_list = curs.fetchall()
									debug(str(hgid_list))
									if len(hgid_list) == 0:
										#auth_hostlist_len += 1
										break
									if hg_i == len(path[1:-1]) - 1:
										#auth_hostlist_len += 1
										if auth_hg_flag == 0:
											host_set['HGId'] = hgid_list[0][0]
											account_set['HGId'] = hgid_list[0][0]
											if save_obj_type == 1:	
												debug("host---------")
												json_data['AuthObject'].append(host_set.copy())
											elif save_obj_type == 2:
												curs.execute('select public."PGetHost"(%d,false,null)' % (HostId_list[0][0]))
												host_json = curs.fetchall()[0][0].encode('utf-8')
												host_json = json.loads(host_json)
												effect_ser_list = []
												ser_list = i[7].split('/')
												#获取所有的服务
												for serviceset in host_json['ServiceSet']:
													for sername in ser_list:
														if serviceset['HostServiceName'] == sername:
															effect_ser_list.append(sername)
															break
												
												#服务下的账号
												for accountset in host_json['AccountSet']:
													for host_service_set in accountset['HostServiceSet']:
														if host_service_set['HostServiceName'] in effect_ser_list:
															account_set['HostServiceId'] = host_service_set['HostServiceId']
															account_set['AccountId'] = accountset['HostAccount']['AccountId']
															json_data['AuthObject'].append(account_set.copy())
															break
											elif save_obj_type == 3:
												account_ser_list = i[8].split('|')
												#ser_list = i[7].split('/')
												curs.execute('select public."PGetHost"(%d,false,null)' % (HostId_list[0][0]))
												host_json = curs.fetchall()[0][0].encode('utf-8')
												host_json = json.loads(host_json)
												for account_ser in account_ser_list:
													a_s_list = account_ser.split(':')
													if len(a_s_list) != 2:
														conn.rollback()
														debug("path1111111")
														debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1))
														return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
													s_list = a_s_list[1].split('&')
													for accountset in host_json['AccountSet']:
														if accountset['HostAccount']['AccountName'] == a_s_list[0]:
															for account_ser in accountset['HostServiceSet']:
																if account_ser['HostServiceName'] in s_list:
																	account_set['HostServiceId'] = account_ser['HostServiceId']
																	account_set['AccountId'] = accountset['HostAccount']['AccountId']
																	json_data['AuthObject'].append(account_set.copy())
																	#break
												#json_data['AuthObject'].append(account_set.copy())
										else:
											hg_accord_flag = 0
											if manage_scope != None:
												if hg_set['IsGroupAuth']:
													accord_scope = filter_scope(2,manage_scope,hgid_list[0][0])
													if len(accord_scope) == 0:
														hg_accord_flag = 1
											if hg_accord_flag == 0:
												if save_obj_type == 2:#取该主机组下所有该服务下的所有账号
													sql = "select public.\"PGetHostList\"(%d)" % hgid_list[0][0]
													curs.execute(sql)
													host_result = curs.fetchall()[0][0].encode('utf-8')
													host_list = json.loads(host_result)
													account_set['HGId'] = hgid_list[0][0]
													for host_data in host_list:
														sql = "select from public.\"PGetHost\"(%d,false,null)" % host_data['HostId']
														curs.execute(sql)
														host_detail = curs.fetchall()[0][0].encode('utf-8')
														host_detail = json.loads(host_detail)
														effect_ser_list = []
														for host_ser in host_detail['ServiceSet']:
															if host_ser['HostServiceName'] in ser_list:
																effect_ser_list.append(host_ser['HostServiceName'])
														for accountset in host_detail['AccountSet']:
															for account_ser in accountset['HostServiceSet']:
																if account_ser['HostServiceName'] in effect_ser_list:
																	account_set['HostServiceId'] = account_ser['HostServiceId']
																	account_ser['AccountId'] = accountset['HostAccount']['AccountId']
																	account_set['HostId'] = host_data['HostId']
																	json_data['AuthObject'].append(account_set.copy())
																	break
												elif save_obj_type == 3:#取该主机组下所有指定服务下的所有账号
													account_set['HGId'] = hgid_list[0][0]
													account_ser_list = i[8].split('|')
													curs.execute('select public."PGetHost"(%d,false,null)' % (HostId_list[0][0]))
													host_json = curs.fetchall()[0][0].encode('utf-8')
													host_json = json.loads(host_json)
													for account_ser in account_ser_list:
														a_s_list = account_ser.split(':')
														if len(a_s_list) != 2:
															conn.rollback()
															debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1))
															return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中组路径格式错误\"}" % (j+1)
														s_list = a_s_list[1].split('&')
														for accountset in host_json['AccountSet']:
															if accountset['HostAccount']['AccountName'] == a_s_list[0]:
																for account_ser in accountset['HostServiceSet']:
																	if account_ser['HostServiceName'] in s_list:
																		account_set['HostServiceId'] = account_ser['HostServiceId']
																		account_set['AccountId'] = accountset['HostAccount']['AccountId']
																		json_data['AuthObject'].append(account_set.copy())
																		break
												else:
													hg_set['HGId'] = hgid_list[0][0]
													hg_set['HostId'] = None
													debug("hg---------")
													json_data['AuthObject'].append(hg_set.copy())	
							else:#填的是主机
								sql = "select \"HostId\" from public.\"Host\" where \"HostIP\"=E'%s'" % i[6]
								curs.execute(sql)
								hostid_list = curs.fetchall()#[0][0]
								if len(hostid_list) != 0:
									curs.execute('select public."PGetHost"(%d,false,null)' % (hostid_list[0][0]))
									host_json = curs.fetchall()[0][0].encode('utf-8')
									host_json = json.loads(host_json)
									
									if i[7] == "":
										conn.rollback()
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务不能为空\"}" % (j+1))
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务不能为空\"}" % (j+1)
									elif i[7] == "*":#按主机
										if i[8] == "":
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务不能为空\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务不能为空\"}" % (j+1)
										else:
											host_set['HostId'] = hostid_list[0][0]
											for item in host_json['data']['HGroupSet']:
												host_set['HGId'] = item['HGId']
												json_data['AuthObject'].append(host_set.copy())
									else:#账号 
										account_set['HostId'] = hostid_list[0][0]
										service_name_list = i[7].split('/')	
										service_name_flag = 0
										for service_name in service_name_list:
											for host_service in host_json['data']['ServiceSet']:
												if service_name == host_service['data']['HostServiceName']:
													service_name_flag = 0
													break
												else:
													service_name_flag = 1
											if service_name_flag == 1:
												inconfrom_service_list.append(service_name)
										if len(inconfrom_service_list) == len(service_name_list):
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务全部不存在\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务全部不存在\"}" % (j+1)
										
										if i[8] == "":
											conn.rollback()
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号不能为空\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号不能为空\"}" % (j+1)
										else:#账号
											account_service_list = i[8].split('|')
											for account_service in account_service_list:
												account_sername_list = account_service.split(':')
												if len(account_sername_list) != 2:
													conn.rollback()
													debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1))
													return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1)
												else:
													for host_data in host_json['data']['AccountSet']:
														if host_data['HostAccount']['AccountName'] == account_sername_list[0]:
															service_list = account_sername_list[1].split('&')
															for service in service_list:
																for serviceset in host_data['HostServiceSet']:
																	if serviceset['HostServiceName'] == service:
																		account_set['HostServiceId'] = serviceset['HostServiceId']
																		account_set['AccountId'] = host_data['HostAccount']['AccountId']
																		for item in host_json['data']['HGroupSet']:
																			account_set['HGId'] = item['HGId']
																			json_data['AuthObject'].append(account_set.copy())
																		break
						else:
							conn.rollback()
							debug("path333333333")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中主机组路径格式错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中主机组路径格式错误\"}" % (j+1)
					else:
						if auth_flag == auth_scope_len + 1:
							auth_scope_len += 1
							debug("8888888888888888888888888")
							debug("i[6]:%s" % i[6])
							if not checkname(i[6].decode('utf-8')):
								conn.rollback()
								debug("path33333333344444")
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围格式错误\"}" % (j+1))
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围格式错误\"}" % (j+1)
							else:
								sql = "select \"ServerScopeId\" from \"ServerScope\" where \"ServerScopeName\"=E'%s'" % i[6].decode('utf-8')
								debug("sql:%s" % sql)
								curs.execute(sql)
								result = curs.fetchall()#[0][0]
								if len(result) == 0:
									conn.rollback()
									debug("path33333333344444")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围不存在\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器范围不存在\"}" % (j+1)
								else:
									curs.execute("select public.\"PGetServerScope\"(null,null,true,null,null,E'%s',null);" % usercode)
									scope_result = curs.fetchall()[0][0].encode('utf-8')
									scope_flag = 0
									#debug("scope_result:%s" % scope_result)
									#debug("result:%s" % result)
									scope_result = json.loads(scope_result)
									for gather_scope in scope_result['data']:
										#debug("start_scope")
										#debug("%d" % gather_scope['ServerScopeId'])
										if gather_scope['ServerScopeId'] == result[0][0]:
											scope_flag = 1
											break
									if scope_flag == 1:
										#debug("ttttttttttttttttttttttt")
										#AuthScope = {"ServerScopeId":96,"Type":1,"HostList":None,"IPList":None}
										AuthScope['ServerScopeId'] = result[0][0]
										#debug("ttttttttttttttttttttttt11111")
										AuthScope['Type'] = 1
										json_data['AuthScope'].append(AuthScope.copy())
				else:
					if json_data["AuthMode"] == 1:#对象
						if i[7] != "" or i[8] != "":
							conn.rollback()
							debug("path<2")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器不能为空\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务器不能为空\"}" % (j+1)
				#服务
				debug("i[7]")
				debug("auth_service_flag:%d" % auth_service_flag)
				debug("auth_flag:%d" % auth_flag)
				
				if json_data["AuthMode"] != 1:#范围
					if i[7] != "":
						if auth_flag == auth_service_flag + 1:
							auth_service_flag += 1
							if json_data['AuthMode'] == 2 or json_data['AuthMode'] == 3:
								if i[7] == "*":#已定义服务所有
									json_data['AuthServiceSet'] = i[7]
							if json_data['AuthServiceSet'] != "*":
								pro_port_con = i[7].split('|')
								if len(pro_port_con) != 2:
									conn.rollback()
									debug("path33333333344444")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务错误\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务错误\"}" % (j+1)
								pro_port = pro_port_con[0].split(':')
								sql = "select \"ProtocolId\" from \"AccessProtocol\" where \"ProtocolName\"=E'%s'" % pro_port[0].decode('utf-8')
								debug("pro_sql:%s" % sql)
								curs.execute(sql)
								result = curs.fetchall()#[0][0]
								if len(result) != 0:
									Service_Set['ProtocolId'] = result[0][0]
									if not pro_port[1].isdigit():
										conn.rollback()
										debug("path33333333344444")
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务端口错误\"}" % (j+1))
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务端口错误\"}" % (j+1)
									if int(pro_port[1]) < 1 or int(pro_port[1]) > 65534:
										conn.rollback()
										debug("path33333333344444")
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务端口错误\"}" % (j+1))
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务端口错误\"}" % (j+1)
									Service_Set['Port'] = int(pro_port[1])
									if pro_port_con[1] == "":
										Service_Set['ConnParamId'] = None
									else:
										sql = "select \"ConnParamId\" from \"ConnParam\" where \"ConnParamName\"=E'%s'" % pro_port_con[1].decode('utf-8')
										debug("con_sql:%s" % sql)
										curs.execute(sql)
										result = curs.fetchall()#[0][0]
										if len(result) == 0:
											conn.rollback()
											debug("path33333333344444")
											debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务连接参数不存在\"}" % (j+1))
											return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务连接参数不存在\"}" % (j+1)
										else:
											Service_Set['ConnParamId'] = result[0][0]
											#Service_Set = {"ProtocolId":2,"Port":22,"ConnParamId":None}
									json_data['AuthServiceSet'].append(Service_Set.copy())
								else:
									conn.rollback()
									debug("path33333333344444")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务协议不存在\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务协议不存在\"}" % (j+1)
						else:
							conn.rollback()
							debug("path33333333344444")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务格式错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中服务格式错误\"}" % (j+1)
					if i[8] != "":
						if auth_flag == auth_account_flag + 1:
							auth_account_flag += 1
							if i[8] == "[*]":#已定义账号所有
								json_data['AuthAccountId'] = i[8]
							if i[8] != "[*]":
								sql = "select \"AccountId\" from \"Account\" where \"AccountName\"=E'%s'" % i[8].replace('\\','\\\\').decode('utf-8')
								debug("account_sql:%s" % sql)
								curs.execute(sql)
								accountid = curs.fetchall()#[0][0]
								if len(accountid) != 0:
									account_list.append(str(accountid[0][0]))
								else:
									conn.rollback()
									debug("path33333333344444")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号不存在\"}" % (j+1))
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号不存在\"}" % (j+1)
						else:
							conn.rollback()
							debug("path33333333344444")
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1))
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中账号格式错误\"}" % (j+1)
				
				
				debug("i[27]")
				#时间范围
				if i[27] != "":
					if auth_flag == order + 1:
						if time_action_flag == 1:#自定义
							set = {"TimeSetMemberId":0,"Order":1,"TimeSetType":11,"StartDate":None,"EndDate":None,"StartTime":"00:00:00","EndTime":"23:59:59","StartPeriod":None,"EndPeriod":None}
							set['Order'] = order + 1
							time_set = i[27].split(' ')
							
							if time_set[0] == "任务":
								if len(time_set) != 3:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								if time_set[1] == "当天":#任务 当天 00:00:00-12:12:12
									set['TimeSetType'] = 32
									start_end = time_set[2].split('-')
									if len(start_end) != 2:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
										
									if not checkHMS(start_end[0]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['StartTime'] = start_end[0]
									if not checkHMS(start_end[1]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['EndTime'] = start_end[1]
								elif time_set[1] == "当前":#任务 当前 00:00:00
									set['TimeSetType'] = 31
									if len(time_set) != 3:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									if not checkHMS(time_set[2]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['EndTime'] = time_set[2]	
								else:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
							elif time_set[0] == "区间":#区间 2018/03/27 00:00:00-2018/03/27 23:59:59
								debug("112223445666777区间")
								set['TimeSetType'] = 20
								if len(time_set) != 4:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								debug("timeset:%s" % str(time_set))
								if not checkYmd(time_set[1]):
									debug("checkYmd111111111")
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								else:
									set['StartDate'] = time_set[1].replace('/','-')
								
								start_end = time_set[2].split('-')
								if len(start_end) != 2:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								if not checkHMS(start_end[0]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								else:
									set['StartTime'] = start_end[0]
								if not checkYmd(start_end[1]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								else:
									set['EndDate'] = start_end[1].replace('/','-')
								
								if not checkHMS(time_set[3]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								else:
									set['EndTime'] = time_set[3]
								debug("112223445666777")
							elif time_set[0] == "周期":#周期 每天 00:00:00-12:12:12
								if len(time_set) < 2:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
								if time_set[1] == "每天":
									set['TimeSetType'] = 11
									if len(time_set) != 3:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									start_end = time_set[2].split('-')
									if len(start_end) != 2:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									if not checkHMS(start_end[0]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['StartTime'] = start_end[0]
									if not checkHMS(start_end[1]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['EndTime'] = start_end[1]
								elif time_set[1] == "每周":#周期 每周 周一 00:00:00-周日 11:11:11
									set['TimeSetType'] = 12
									if len(time_set) != 5:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									
									if time_set[2] in time_day:
										set['StartPeriod'] = time_day.index(time_set[2]) + 1
									else:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									start_end = time_set[3].split('-')
									if len(start_end) != 2:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									if not checkHMS(start_end[0]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['StartTime'] = start_end[0]
									
									if start_end[1] in time_day:
										set['EndPeriod'] = time_day.index(start_end[1]) + 1
									else:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									if not checkHMS(time_set[4]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['EndTime'] = time_set[4]
								elif time_set[1] == "每月":#周期 每月 1日 00:00:00-31日 00:00:00
									set['TimeSetType'] = 13
									if len(time_set) != 5:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									
									num_list = re.findall(r"\d+\.?\d*",time_set[2])
									if len(num_list) == 0:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['StartPeriod'] = num_list[0]
									start_end = time_set[3].split('-')
									if len(start_end) != 2:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									if not checkHMS(start_end[0]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['StartTime'] = start_end[0]
									num_list = re.findall(r"\d+\.?\d*",start_end[1])
									if len(num_list) == 0:
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['EndPeriod'] = num_list[0]
									if not checkHMS(time_set[4]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
									else:
										set['EndTime'] = time_set[4]
								else:
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
							debug("timeconfig:%s" % str(timeconfig))
							debug("%s" % str(set))
							if str(timeconfig['Set']).find(str(set)) != -1:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间配置错误\"}" % (j+1)
							else:
								order += 1
								timeconfig['Order'] = order
								timeconfig['Set'].append(set.copy())
								timeconfig['TimeSetId'] = 0
								timeconfig['Type'] = 2
						else:#已定义						
							sql = "select \"TimeSetId\" from public.\"TimeSet\" where \"Name\"=E'%s'" % i[27].decode('utf-8')
							debug("timeset:%s" % sql)
							curs.execute(sql)
							result = curs.fetchall()#[0][0]
							if len(result) == 0:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间集合不存在\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间集合不存在\"}" % (j+1)
							else:
								#{"Order":1,"TimeSetId":0,"Type":2,"Set":[]}
								order += 1
								timeconfig['Order'] = order
								timeconfig['TimeSetId'] = result[0][0]
								timeconfig['Type'] = 1
								timeconfig['Set'] = None
								json_data['AccessStrategyInfo']['TimeConfig'].append(timeconfig.copy())
					else:
						conn.rollback()
						debug("path33333333344444")
						debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间范围格式错误\"}" % (j+1))
						return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中时间范围格式错误\"}" % (j+1)
				debug("i[29]")
				if i[29] != "":
					debug("client_action_flag:%d" % client_action_flag)
					if client_action_flag == 1:#自定义
						clientconfig['Type'] = 2
						start_end = i[29].split('-')
						if len(start_end) > 2:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
						elif len(start_end) == 2:
							if '.' in start_end[0]:#jixu
								if not checkip(start_end[0]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
								else:
									if not checkip(start_end[1]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
									else:
										debug("ip_order1:%d" % ip_order)
										ip_order += 1
										ip_set['Order'] = ip_order
										ip_set['StartIP'] = start_end[0]
										ip_set['EndIP'] = start_end[1]
										clientconfig['IPList']['Set'].append(ip_set.copy())
							elif ':' in start_end[0]:#jixu
								if not checkmac(start_end[0]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
								else:
									if not checkmac(start_end[1]):
										debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
										conn.rollback()
										return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
									else:
										mac_order += 1
										mac_set['Order'] = mac_order
										mac_set['StartMACAddress'] = start_end[0]
										mac_set['EndMACAddress'] = start_end[1]
										clientconfig['MACList']['Set'].append(mac_set.copy())
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
						else:
							if '.' in start_end[0]:
								if not checkip(start_end[0]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
								else:
									debug("ip_order2:%d" % ip_order)
									ip_order += 1
									ip_set['Order'] = ip_order
									ip_set['StartIP'] = start_end[0]
									ip_set['EndIP'] = start_end[0]
									clientconfig['IPList']['Set'].append(ip_set.copy())
							elif ':' in start_end[0]:
								if not checkmac(start_end[0]):
									debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
									conn.rollback()
									return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
								else:
									mac_order += mac_order + 1
									mac_set['Order'] = mac_order
									mac_set['StartMACAddress'] = start_end[0]
									mac_set['EndMACAddress'] = start_end[0]
									clientconfig['MACList']['Set'].append(mac_set.copy())
							else:
								debug("{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1))
								conn.rollback()
								return "{\"Result\":false,\"ErrMsg\":\"第%d行客户端集合信息中客户端范围格式错误\"}" % (j+1)
						debug("clientconfig:%s" % str(clientconfig))
					else:
						sql = "select \"ClientScopeId\" from \"ClientScope\" where \"ClientScopeName\"=E'%s'" % i[29].decode('utf-8')
						curs.execute(sql)
						result = curs.fetchall()#[0][0]
						if len(result) == 0:
							debug("{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端集合不存在\"}" % (j+1))
							conn.rollback()
							return "{\"Result\":false,\"ErrMsg\":\"第%d行访问授权信息中客户端集合不存在\"}" % (j+1)
						else:
							mac_order += 1
							clientconfig['Order'] = mac_order
							clientconfig['ClientScopeId'] = result[0][0]
							clientconfig['Type'] = 1
							clientconfig['IPList'] = None
							clientconfig['MACList'] = None
							json_data['AccessStrategyInfo']['ClientScopeConfig'].append(clientconfig.copy())
				debug("j:%d" % j)
				debug("%d" % len(all_data[12]))
				if j == len(all_data[12]) - 1:#保存访问授权	
					auth_isexist = 0
					if len(json_data['AdminSet']) == 0:
						sql = "select \"UserId\" from public.\"User\" where \"UserCode\"=E\'%s\'" % usercode
						curs.execute(sql)
						admin_set['AdminId'] = curs.fetchall()[0][0]
						json_data['AdminSet'].append(admin_set.copy())
					
					if time_action_flag == 1:
						json_data['AccessStrategyInfo']['TimeConfig'].append(timeconfig.copy())
					if client_action_flag == 1:#自定义
						json_data['AccessStrategyInfo']['ClientScopeConfig'].append(clientconfig.copy())
					if len(account_list) != 0:
						json_data['AuthAccountId'] = ','.join(account_list)
						
					sql = "select \"AccessAuthId\" from public.\"AccessAuth\" where \"AccessAuthName\"=E'%s'" % json_data['AccessAuthName'].decode('utf-8')
					debug("sql:%s" % sql)
					curs.execute(sql)
					result = curs.fetchall()#[0][0]
					
					if json_data['AccessStrategyInfo']['ApproveStrategyName'] != None:
						if json_data['AccessStrategyInfo']['ApproveStrategyName'] in invalid_approve_strategy:
							warn_info_list.append("登录审批策略无效，该授权停用")
							json_data['Enabled'] = False
					
					if json_data['AccessStrategyInfo']['WorkOrderApproveStrategyName'] != None:
						if json_data['AccessStrategyInfo']['WorkOrderApproveStrategyName'] in invalid_approve_strategy:
							warn_info_list.append("工单审批策略无效，该授权停用")
							json_data['Enabled'] = False
					
					if json_data['AccessStrategyInfo']['EventAlarmInfoName'] != None:
						if json_data['AccessStrategyInfo']['EventAlarmInfoName'] in invalid_alarm_strategy:
							warn_info_list.append("事件告警策略无效，该授权停用")
							json_data['Enabled'] = False
					
					if cover == '1':
						if len(result) == 0:
							json_data['AccessAuthId'] = 0
							AccessAuthId = 0
							if json_data['AccessStrategyInfo']['AccessStrategyName'] == None:
								json_data['AccessStrategyInfo']['AccessStrategyId'] = 0
							else:
								sql = "select public.\"PGetAccessStrategyByName\"(E'%s')" % json_data['AccessStrategyInfo']['AccessStrategyName'].decode('utf-8')
								curs.execute(sql)
								result = curs.fetchall()[0][0]
								json_data['AccessStrategyInfo']['AccessStrategyId'] = result
						else:
							debug("result11111:%s" % str(result))
							json_data['AccessAuthId'] = result[0][0]
							AccessAuthId = json_data['AccessAuthId']
							get_data = '{"loginusercode":"'+usercode+'","accessauthid":'+str(json_data['AccessAuthId'])+',"limitrow":null,"offsetrow":null}'
							get_data = "E'%s'" % get_data
							curs.execute('select public."PGetAccessAuth"(%s)' % get_data)
							results = curs.fetchall()[0][0].encode('utf-8')
							debug("%s" % results)
							re_result = json.loads(results)
							#re_result['data'][0]['AuthObject']jixu
							#same_list = []
							#dif_list = []
							if len(re_result['data']) != 0:
								if json_data['AccessStrategyInfo']['AccessStrategyName'] == None:		
									if re_result['data'][0]['AccessStrategyInfo'] != None and re_result['data'][0]['AccessStrategyInfo']['AccessStrategyName'] == None:
										json_data['AccessStrategyInfo']['AccessStrategyId'] = re_result['data'][0]['AccessStrategyInfo']['AccessStrategyId']
									else:
										json_data['AccessStrategyInfo']['AccessStrategyId'] = 0
								else:
									sql = "select public.\"PGetAccessStrategyByName\"(E'%s')" % json_data['AccessStrategyInfo']['AccessStrategyName'].decode('utf-8')
									debug("sqlzzzz:%s" % sql)
									curs.execute(sql)
									debug("------------------")
									result = curs.fetchall()[0][0]
									debug("result11111:%s" % result)
									json_data['AccessStrategyInfo']['AccessStrategyId'] = result
								
								debug("obj2222:%s" % str(re_result['data'][0]['AuthObject']))
								debug("obj3333:%s" % str(json_data['AuthObject']))
								
								if re_result['data'][0]['AuthObject'] != None:
									for item in re_result['data'][0]['AuthObject']:
										for index,item1 in enumerate(json_data['AuthObject']):
											if item['HGId'] == item1['HGId']:
												if item['HostId'] == item1['HostId']:
													if item['HostId'] == None:#主机组按组
														#same_list.append(item1)
														json_data['AuthObject'].pop(index)
													else:
														if item1.has_key('AccountId'):#账号
															if item['HostServiceId'] == item1['HostServiceId'] and item['AccountId'] == item1['AccountId']:
																#same_list.append(item1)
																json_data['AuthObject'].pop(index)
															else:
																#dif_list.append(item)
																json_data['DeleteAuthObject'].append(item)
														else:
															if item['IsGroupAuth'] == False:#按组->不按组
																json_data['AuthObject'][index]['IsDelOld'] = True
															else:
																#same_list.append(item1)#主机按组
																json_data['AuthObject'].pop(index)
												else:
													#dif_list.append(item)
													json_data['DeleteAuthObject'].append(item)
											else:
												#dif_list.append(item)
												json_data['DeleteAuthObject'].append(item)
							else:
								auth_isexist = 1
								ErrorLog = "该授权已存在且不属于登录该账号"
								status = 1
							debug("-------------------")
					else:
						json_data['AccessAuthId'] = 0
						if len(result) != 0:
							AccessAuthId = result[0][0]
					if auth_isexist != 1:
						debug("---------111111111111111111")
						json_data['EffectiveTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
						debug("json_data:%s" % str(json_data))
						sql = "select public.\"PSaveAccessAuth\"(E'%s')" % MySQLdb.escape_string(json.dumps(json_data)).decode("utf-8")
						debug("sql:%s" % sql)
						curs.execute(sql)
						result = curs.fetchall()[0][0].encode('utf-8')
						auth_result = json.loads(result)
						if auth_result['Result']:
							save_auth_succ += 1
							ErrorLog = '，'.join(warn_info_list)
							status = 0
							AccessAuthId = auth_result['AccessAuthId']
						else:
							save_auth_fail += 1
							ErrorLog = auth_result['ErrMsg']
							status = 1
					sql = "insert into private.\"AuthImportTaskDetail\"(\"AuthName\",\"AuthId\",\"ErrorLog\",\"AuthImportTaskId\",\"Status\")values(E'%s',%d,E'%s',%d,%d)" % (json_data['AccessAuthName'].decode('utf-8'),AccessAuthId,ErrorLog,int(taskid),status)
					debug("insert_sq2222l:%s" % sql)
					curs.execute(sql)
			#return "{\"Result\":true}"
			sql = "update private.\"AuthImportTask\" set \"SuccCount\" = %d, \"FailCount\" = %d, \"Status\" = 1, \"Type\" = 1 where \"AuthImportTaskId\" = %d" % (save_auth_succ,save_auth_fail,int(taskid))
			debug(sql)
			curs.execute(sql)
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		conn.rollback()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
	except Exception,ex:
		print Exception,":",ex
		return "{\"Result\":false,\"ErrMsg\":\"语法错误(%s)\"}" % (ex)
try:
	file_pwd = sys.argv[1]
	cover = sys.argv[2]
	taskid = sys.argv[3]
	usercode = sys.argv[4]
	clientip = sys.argv[5]
	print "eeeeeeee"
	print "%s" % sys.argv[0]
	print "%s" % file_pwd
	print "%s" % cover
	#print "%s" % sys.argv[4]
	print "123133333"
	errmsg = import_data_all(file_pwd,cover,taskid,usercode,clientip)
	print "%s" % errmsg
	reload(sys)
	sys.setdefaultencoding('utf-8')
	if errmsg != "{\"Result\":true}":
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				errmsg = errmsg[26:-2].decode('utf-8').replace('\\','\\\\').replace("\"","\"").replace(".","\\.").replace("'","''").replace("?","\\?").replace("$","\\$").replace("*","\\*").replace(")","\\)").replace("(","\\(").replace("+","\\+").replace("{","\\{").replace("}","\\}").replace("]","\\]").replace("[","\\[").replace("^","\\^")
				sql = "update private.\"AuthImportTask\" set \"Status\" = 2,\"ErrorLog\" = E\'%s\' where \"AuthImportTaskId\" =%d" % (errmsg,int(taskid))
				debug(sql)
				curs.execute(sql)
				system_log(usercode,"导入授权","失败："+errmsg,"访问授权>访问授权",clientip)
				#conn.commit()
		except pyodbc.Error,e:
			conn.rollback()
			print "error"
	debug("222222222222222222222")
	system_log(usercode,"导入授权","成功","访问授权>访问授权",clientip)
	debug("222222222222222222222111")
	os.remove(file_pwd)
# 打开文件失败时
except IOError:
    print "Bind port failed!"

# 调用系统命令失败
except OSError:
    print "Command failed!"

except KeyError:
    print "No such item!"

# 使用Ctrl+c退出时
except KeyboardInterrupt:
    print "User quitted!"

except pyodbc.Error,e:
	print "sql error"
	print str(e)

finally:
    exit(0)
