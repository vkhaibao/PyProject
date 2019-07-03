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
from ctypes import *
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
import MySQLdb
from logbase import defines
from logbase import task_client
from urllib import unquote
from werkzeug.utils import secure_filename
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
from jinja2 import Environment,FileSystemLoader
down_file = Blueprint('down_file',__name__)

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
	return 0
	path = "/var/tmp/debugzdpg.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

def down_templet():
	try:
		with open("/usr/stoage/host/temp/host.csv","w") as csvfile:
			debug("open")
			csvfile.write(codecs.BOM_UTF8)
			writer = csv.writer(csvfile)
			pro_title = ['*协议名称','*端口','描述']
			writer.writerow(pro_title)
			pro_prompt = [['非空唯一','非空',''],['特殊字符仅支持下划线、横杠','0-65535','']]
			writer.writerows(pro_prompt)
			AD_title = ['*AD域名称','*服务器IP（多个IP用;分隔）']
			writer.writerow(AD_title)
			AD_prompt = [['非空唯一','非空唯一'],['特殊字符仅支持下划线、横杠、小数点','0.0.0.0-255.255.255.255之间']]
			writer.writerows(AD_prompt)
			con_title = ['*连接参数名称','*协议','配置']
			writer.writerow(con_title)
			con_prompt = [['非空唯一','非空','RDP/TELNET/FTP/VNC/X11/RLOGIN/PCANY协议，配置为空即不填'],['特殊字符仅支持下划线、横杠、小数点','RDP,TELNET,FTP,VNC,X11,RLOGIN,PCANY,TN5250','SSH：1.版本：1/2；2.格式：1/2'],['','','ORACLE:1.指定：SID/SERVICE_NAME；2.实例名或服务名：不能含有特殊字符；3.连接方式：未指定/NORMAL/SYSDBA/SYSOPER；4.格式：指定|实例名/服务名|连接方式'],['','','MSSQL：1.实例名：不能含有特殊字符；2.认证方式：未指定/SQL服务器验证/Windows验证/Windows单一登录；3.格式：实例名|认证方式'],['','','MYSQL/DB2：1.数据库名：不能含有特殊字符；2.格式：数据库名'],['','','SYBASE：1.实例名：不能含有特殊字符；2.格式：实例名'],['','','HTTP/HTTPS：1.URL；2.账号：不能含有特殊字符；3.密码：不能含有特殊字符；4.提交元素：不能含有\'|\'；5.格式：URL|账号|密码|提交元素'],['','','RADMIN；1.认证方式：未指定/RADMIN/Windows；2.格式：认证方式']]
			writer.writerows(con_prompt)
			debug("zzzzzzzzz")
			dev_title = ['*设备类型名称','*类型','账号切换命令','切换密码提示','描述','*服务名称','*协议:端口','连接参数','前置机']
			writer.writerow(dev_title)
			dev_prompt = [['非空唯一','非空','','','','非空唯一','非空','',''],['特殊字符仅支持下划线、横杠、小数点','Windows/Linux/Unix/Aix/As400/Cisco/H3c/Huawei/Ruijie/Network/Host/Server/Cluster/Switchboard/Firewall','','','','','','','']]
			writer.writerows(dev_prompt)
			debug("zzzzzzzzz1")
			hg_title = ['*主机组','组路径']
			writer.writerow(hg_title)
			debug("zzzzzzzzz2")
			hg_prompt = [['非空',''],['特殊字符仅支持下划线、横杠、小数点','格式：主机组的绝对路径,即若主机组a在主机组b下，则填/b/a']]
			writer.writerows(hg_prompt)
			host_title = ['*主机名','*主机IP','*设备类型','描述','主机组','*访问速度（正常、较慢、很慢）','*同时登陆（允许、限制）','*服务名称','*协议','*端口','连接参数','账号切换命令','切换密码提示','前置机','跳转来源主机','跳转来源服务','跳转来源账号','跳转命令','命令提示符','登录密码提示','登陆成功提示','换行符','登录名提示','*账号','AD域','*对应服务（多个服务用;分隔）','密码','特权账号（是、否）','切换自账号','账号切换命令','切换命令提示']
			writer.writerow(host_title)
			host_prompt = [['非空唯一','非空唯一','非空','','默认未分组','正常/较慢/很慢','允许/限制','非空','非空','非空','','','','多个前置机用;分隔','','','','','','','','','','非空','','非空','1.不填即为由用户输入密码；2.填入空密码；3.填入密码；密码：不能为中文','是/否','','',''],['特殊字符仅支持下划线、横杠、小数点','0.0.0.0-255.255.255.255之间','','','','','','','','','','','','','','','','','','','','','','','','','','','','','']]
			writer.writerows(host_prompt)
			csvfile.close()
			down_path = "/flash/system/storage/host/host.csv"
			debug("12313213")
			'''
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					debug("**********************")
					sql = "select * from private.\"HostExportInfo\""
                        		debug(sql)
                       			curs.execute(sql)
                        		results = curs.fetchall()
                        		debug("results:%s" % results)
                        		if len(results) != 0:
                                		sql = "delete from private.\"HostExportInfo\""
                                		curs.execute(sql)
					sql = "insert into private.\"HostExportInfo\"(\"FileName\") VALUES(\'host.csv\')"
					debug(sql)
					curs.execute(sql)
					conn.commit()
					sql = "select * from private.\"HostExportInfo\""
                                        debug(sql)
                                        curs.execute(sql)
					debug("pppp:%s" % curs.fetchall())
				return "true" + str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
			except pyodbc.Error,e:
                		conn.rollback()
			'''
			return send_from_directory('/flash/system/storage/host/temp','host.csv',as_attachment=True)
	except IOError,e:
		return "{\"Result\":false,\"ErrMsg\":\"文件错误(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))

def down_host(userCode):
	try:
		with open("/var/tmp/zdp/host.csv","w") as csvfile:
			csvfile.write(codecs.BOM_UTF8)
			writer = csv.writer(csvfile)
			#导出协议
			title = ['*协议名称','*端口','描述']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					debug('select public."PGetAccessProtocol"(null,null,null,null,null,null)')
					curs.execute('select public."PGetAccessProtocol"(null,null,null,null,null,null)')
					results = curs.fetchall()[0][0].encode('utf-8')
					pro_data = json.loads(results)
					debug("111111111")
					for pro_set in pro_data['data']:
						pro_list = []
						debug("123133")
						debug(str(pro_set))
						debug(pro_set['ProtocolName'])
						pro_list.append(pro_set['ProtocolName']+"\t")
						if pro_set['ProtocolName'] == "PCANY":
							p_port = str(pro_set['Port']) + ':' + str(pro_set['Port1'])
							pro_list.append(p_port)
						else:
							pro_list.append(pro_set['Port'])
						debug("zxczc")
						if pro_set['Description'] != None:
							pro_list.append(pro_set['Description'])
						debug(str(pro_list))
						writer.writerow(pro_list)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
			#导出AD域
			title = ['*AD域名称','*服务器IP（多个IP用;分隔）']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					curs.execute('select public."PGetDomain"(null,null,null,null,null)')
					results = curs.fetchall()[0][0].encode('utf-8')
					AD_data = json.loads(results)
					for AD_set in AD_data['data']:
						AD_list = []
						debug(str(AD_list))
						AD_list.append(AD_set['DomainName']+"\t")
						AD_list.append(AD_set['ServerIP'])
						debug(str(AD_list))
						writer.writerow(AD_list)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
			#导出连接参数	
			title = ['*连接参数名称','*协议','配置']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					debug('select public."PGetConnParam"(null,null,null,null,null,null,null)')
					curs.execute('select public."PGetConnParam"(null,null,null,null,null,null,null)')
					results = curs.fetchall()[0][0].encode('utf-8')
					con_data = json.loads(results)
					debug('123zzz')
					for con_set in con_data['data']:
						con_list = []
						con_list.append(con_set['ConnParamName']+"\t")
						con_list.append(con_set['ProtocolName'])
						debug(con_set['ConnParamName'])
						if con_set['ServiceName'] != None:
							if con_set['ConnType'] != None and con_set['ConnParamValue'] != None and con_set['ServiceName'] != None:
								con_set_v = con_set['ConnParamValue'] + '|' + con_set['ServiceName'] + '|' + con_set['ConnType']
							elif con_set['ConnType'] != None:
								con_set_v = con_set['ServiceName'] + '|' + con_set['ConnType']
							elif con_set['ConnParamValue'] != None:
								if con_set['ProtocolName'] == "HTTPS":
									debug(con_set['ProtocolName'])
									debug(con_set['ConnParamValue'])
									conp_v = json.loads(con_set['ConnParamValue'])
									debug(con_set['ServiceName'])
									con_set_v = con_set['ServiceName'] + '|' + conp_v['UserName'] + '|' + conp_v['UserPwd'] + '|' + conp_v['Submit']
								elif con_set['ProtocolName'] == "HTTP":
									con_set_v = con_set['ServiceName'] + '|' + con_set['ConnParamValue']
								else:
									if con_set['ProtocolName'] == "ORACLE":
										con_set_v = con_set['ConnParamValue'] + '|' + con_set['ServiceName'] + 	'|未指定' 
									else:
										con_set_v = con_set['ConnParamValue'] + '|' + con_set['ServiceName']	
							else:
								if con_set['ProtocolName'] == "MSSQL":
									con_set_v = "未指定"		
								con_set_v = con_set['ServiceName']
							con_list.append(con_set_v)
						else:
							if con_set['ProtocolName'] == "RADMIN":
								con_set_v = "未指定"
							con_list.append(con_set_v)
						writer.writerow(con_list)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
			#导出设备类型
			title = ['*设备类型名称','*类型','账号切换命令','切换密码提示','描述','*服务名称','*协议:端口','连接参数','前置机']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					debug('select public."PGetDeviceType"(null,null,null,null,null,null,null)')
					curs.execute('select public."PGetDeviceType"(null,null,null,null,null,null,null)')
					results = curs.fetchall()[0][0].encode('utf-8')
					dev_data = json.loads(results)
					debug("123zzzhhh")
					debug(results)
					for dev_set in dev_data['data']:
						debug("123zzzz")
						dev_list = []
						i = 0
						if dev_set['ServiceSet'] == None:
							continue
						while i < len(dev_set['ServiceSet']):
							dev_list.append([0])
							i = i + 1
						dev_list[0].append(dev_set['DeviceTypeName'])
						dev_list[0].append(dev_set['DeviceTypeIcon'])
						if dev_set['AcctSwitchCmd'] != None:
							dev_list[0].append(dev_set['AcctSwitchCmd'])
						else:
							dev_list[0].append('')
						if dev_set['SwitchPasswdPrompt'] != None:
							dev_list[0].append(dev_set['SwitchPasswdPrompt'])
						else:
							dev_list[0].append('')
						if dev_set['Description'] != None:
							dev_list[0].append(dev_set['Description'])
						else:
							dev_list[0].append('')
						debug('123zxcewqe')
						if dev_set['ServiceSet'] != None:
							debug(str(dev_set['ServiceSet']))
							for ser_index,ser in enumerate(dev_set['ServiceSet']):
								if ser_index > 0:
									k = 0
									while k < 5:
										dev_list[ser_index].append('')
										k = k + 1
								debug(ser['DeviceServiceName'])
								debug(ser['ProtocolName'])
								dev_list[ser_index].append(ser['DeviceServiceName'])
								ser_p = ser['ProtocolName']+':'+str(ser['Port'])
								dev_list[ser_index].append(ser_p)
								dev_list[ser_index].append(ser['ConnParamName'])
								#dev_list[ser_index].append(ser['DomainName'])
								#dev_list[ser_index].append(ser['AccIPSet'])
								IP_str = ""
								if ser['AccIPSet'] != None:
									for IP in ser['AccIPSet']:
										IP_str = IP_str + IP['AccIP'] + ';'
									if IP_str != "":
										IP_str = IP_str[:-1]
								debug(IP_str)
								dev_list[ser_index].append(IP_str)
							debug("sdaddsd")
							b = 0
							while b < len(dev_list):
								dev_list[b].pop(0)
								b = b + 1
							writer.writerows(dev_list)
						else:
							debug("sdaddsd1")
							dev_list[0].append('')
							writer.writerows(dev_list)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
			debug("123133zzz")
			#导出主机组
			title = ['*主机组','组路径']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					sql = 'SELECT "HGroup"."HGName","HGroup"."HGId" FROM "HGroup"'
					debug(sql)
					curs.execute(sql)
					all_hg = curs.fetchall()
					debug("jjjjjjjjjjjjjjkkkkkk")
					for hg_data in all_hg:
						hg_list = []
						debug(hg_data[0])
						hg_list.append(hg_data[0])
						if hg_data[0] == '/':
							hg_list.append('')
							writer.writerow(hg_list)
							continue
						sql = 'select "HGroup"."ParentHGId" from "HGroup" where "HGroup"."HGId" = %d;' % hg_data[1] #取上一级组ID
						debug(sql)
						curs.execute(sql)
						results = curs.fetchall()
						#debug(results[0][1])
						debug(str(results[0][0]))
						if results[0][0] == 0:#第一层
							if hg_data[0] == '/':
								path = hg_data[0]
							else:
								path = '/' + hg_data[0]
							debug(path)
							hg_list.append(path)
						else:
							path_arry = []
							while results[0][0] != 0:
								sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results[0][0]
								debug(sql)
								curs.execute(sql)
								results = curs.fetchall()
								path_arry.insert(0,results[0][1])
							sql = 'select "HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results[0][0]
							debug(sql)
							curs.execute(sql)
							results = curs.fetchall()
							path_arry.insert(0,results[0][0])
							path_arry.append(hg_data[0])
							path = '/'.join(path_arry)#路径
							path = path[1:]
							debug(path)
							hg_list.append(path)
						writer.writerow(hg_list)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
				
			#导出主机
			title = ['*主机名','*主机IP','*设备类型','描述','主机组','*访问速度（正常、较慢、很慢）','*同时登陆（允许、限制）','*服务名称','*协议','*端口','连接参数','账号切换命令','切换密码提示','前置机','跳转来源主机','跳转来源服务','跳转来源账号','跳转命令','命令提示符','登录密码提示','登陆成功提示','换行符','登录名提示','*账号','AD域','*对应服务','密码','特权账号（是、否）','切换自账号','账号切换命令','切换命令提示']
			writer.writerow(title)
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					debug('select public."PGetHost"(null,null,\'%s\')' % userCode)
					curs.execute('select public."PGetHost"(null,null,E\'%s\')' % userCode)
					results = curs.fetchall()[0][0].encode('utf-8')
					all_host = json.loads(results)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
			debug("2222222")
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					for all_data in all_host:
						sql = 'select public."PGetHost"(%d,false,E\'%s\')' % (all_data['HostId'],userCode)
						debug(sql)
						curs.execute(sql)
						debug("ggggggjjjjjjj")
						results = curs.fetchall()[0][0].encode('utf-8')
						debug(results)
						debug("ggggggjjjjjjjassdsd")
						host_data = json.loads(results)
						debug("hhhhhhhhhhhhhhkkkkkkk")
						#detail_temp = json.loads(results)
						detail_temp = host_data.copy()
						debug("mmmmmmmmmmmm")
						rows_list = []
						debug("gfgfggggggggggggggggg")
						if detail_temp['ServiceSet'] != None:
							ser_len = len(detail_temp['ServiceSet'])
						else:
							ser_len = 0
						debug("hhhhhhhhhhhhhh1111111")
						if detail_temp['AccountSet'] != None:
							acc_len = len(detail_temp['AccountSet'])
							'''
							acc_len = 0
							for acc_ser_len in detail_temp['AccountSet']:
								acc_len = acc_len + len(acc_ser_len['HostServiceSet'])
							'''
							#acc_len = len(detail_temp['AccountSet']['HostServiceSet'])
						else:
							acc_len = 0
						debug("hhhhhhhhhhhhhh")
						if detail_temp['HGroupSet'] != None:
							hg_len = len(detail_temp['HGroupSet'])
						else:
							hg_len = 0
						debug("bbbbbbbbbbbbbb")
						if ser_len == 0 and acc_len == 0:
							continue
						max_len = max(ser_len,acc_len,hg_len)
						i = 0
						while i < max(ser_len,acc_len,hg_len):
							debug("jjjjjjjjjjjj")
							rows_list.append([0])
							i = i + 1
						debug("len:%d" % max(ser_len,acc_len))
						rows_list[0].append(detail_temp['HostName'])

						rows_list[0].append(detail_temp['HostIP'])

						rows_list[0].append(detail_temp['DeviceTypeName'])

						rows_list[0].append(detail_temp['Description'])
						if detail_temp['HGroupSet'] != None:
							for hg_index,hg in enumerate(detail_temp['HGroupSet']):		
								'''
								sql = 'select "HGroup"."ParentHGId" from "HGroup" where "HGroup"."HGId" = %d;' % hg['HGId'] #取上一级组ID
								curs.execute(sql)
								results = curs.fetchall()
								debug(str(results[0][0]))
								if results[0][0] == 0:#第一层
									#path = '/' + hg['HGName']
									rows_list[0].append(hg['HGName'])
								else:
									while results[0][0] != 0:
										sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results[0][0]
										curs.execute(sql)
										results = curs.fetchall()
										path_arry.insert(0,results[0][1])
									sql = 'select "HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results[0][0]
									curs.execute(sql)
									results = curs.fetchall()
									path_arry.insert(0,results[0][1])
									path = ''.join(path_arry)#路径
									rows_list[0].append(path)
								'''
								if hg_index > 0:
									k = 0
									while k < 4:
										rows_list[hg_index].append('')
										k = k + 1
								debug(hg['HGroupNamePath'])
								rows_list[hg_index].append(hg['HGroupNamePath'][1:])
						else:
							continue
						if detail_temp['AccessRate'] == 1:
							AccessRate = "正常"
						elif detail_temp['AccessRate'] == 2:
							AccessRate = "较慢"
						else:
							AccessRate = "很慢"
						rows_list[0].append(AccessRate)
						if detail_temp['EnableLoginLimit'] == False:
							EnableLoginLimit = "限制"
						else:
							EnableLoginLimit = "允许"
						rows_list[0].append(EnableLoginLimit)
						
						debug("1111111111111")
						for ser_index,ser in enumerate(detail_temp['ServiceSet']):
							if ser_index > hg_len-1:
								k = 0
								while k < 7:
									rows_list[ser_index].append('')
									k = k + 1
							elif ser_index < hg_len and ser_index != 0:
								k = 0
								while k < 2:
									rows_list[ser_index].append('')
									k = k + 1
							rows_list[ser_index].append(ser['HostServiceName'])
							rows_list[ser_index].append(ser['ProtocolName'])
							rows_list[ser_index].append(ser['Port'])
							rows_list[ser_index].append(ser['ConnParamName'])
							#rows_list[ser_index].append(ser['DomainName'])
							rows_list[ser_index].append(ser['AcctSwitchCmd'])
							rows_list[ser_index].append(ser['SwitchPasswdPrompt'])
							all_ip = ""
							if ser['AccIPSet'] != None:
								for ip in ser['AccIPSet']:
									all_ip = all_ip + ip['AccIP'] + ';'
								if all_ip != "":
									all_ip = all_ip[:-1]
							rows_list[ser_index].append(all_ip) #前置机
							
							rows_list[ser_index].append(ser['FromHostName'])
							rows_list[ser_index].append(ser['FromHostServiceName'])
							rows_list[ser_index].append(ser['FromAccountName'])
							rows_list[ser_index].append(ser['FromLoginCmd'])
							rows_list[ser_index].append(ser['NormalPrompt'])
							rows_list[ser_index].append(ser['LoginPasswdPrompt'])
							rows_list[ser_index].append(ser['LoginSuccPrompt'])
							if ser['LineBreak'] == 1:
								LineBreak = "LF"
							elif ser['LineBreak'] == 2:
								LineBreak = "CR"
							else:
								LineBreak = "CRLF"
							rows_list[ser_index].append(LineBreak) #换行符
							rows_list[ser_index].append(ser['LoginUserPrompt'])
						
						
						
						debug("2222222222222222")
						a = ser_index + 1
						if a < max_len:
							while a < max_len:
								k = 0
								while k < 23: 
									rows_list[a].append('')
									k = k + 1
								a = a + 1
						debug("1333333333333")
						debug("len:%d" % len(rows_list))	
						list_len = len(rows_list[0])
						i = 0
						space_f = 0
						if detail_temp['ServiceSet'] != None and detail_temp['AccountSet'] != None:
							for acc in detail_temp['AccountSet']:
								debug("d_s:%d" % len(detail_temp['ServiceSet']))
								debug("d_a:%d" % len(detail_temp['AccountSet']))
								debug("a_s:%d" % len(acc['HostServiceSet']))
								debug("oppppppppppppppppppppppppppppp")
								debug(acc['HostAccount']['AccountName'])
								if '\\' in acc['HostAccount']['AccountName']:
									debug("hhhhhhhhhhhhhhhhhhhhhhjjjjjjjjjj")
									debug(acc['HostAccount']['AccountName'])
									Name_AD = acc['HostAccount']['AccountName'].split('\\')
									rows_list[i].append(Name_AD[1]) 
									rows_list[i].append(Name_AD[0]) #添加AD域
								else:
									debug(acc['HostAccount']['AccountName'])
									debug("--------------")
									debug("i:%d" % i)
									rows_list[i].append(acc['HostAccount']['AccountName']) #添加账号
									debug("uuuuuuuuuu")
									rows_list[i].append('')
								acc_ser_list = ""
								for acc_ser in acc['HostServiceSet']:
									acc_ser_list = acc_ser_list + acc_ser['HostServiceName'] + ';'
								acc_ser_list = acc_ser_list[:-1]
								rows_list[i].append(acc_ser_list)
								#rows_list[i].append(acc_ser['HostServiceName'])
								debug(str(acc['Password']))
								if acc['Password'] != None:
									if os.path.exists('/usr/lib64/logproxy.so') == False:
										debug("{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (ERRNUM_MODULE_host + 0))
										return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (ERRNUM_MODULE_host + 0)

									lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
									pwd_rc4 = c_char_p()# 定义一个指针
									debug("uuuiiii")
									lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
									lib.decrypt_pwd.restype = None #定义函数返回值
									debug('123')
									pwd_rc4.value = "0"*512 # 初始化 指针
									debug(str(acc['Password']))
									lib.decrypt_pwd(str(acc['Password']),pwd_rc4);
									debug("kkkkkkkk")
									#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
									debug('hhhhhhhhjjj')
									debug(pwd_rc4.value)
									rows_list[i].append(pwd_rc4.value) #获取变量的值
								else:
									debug(str(acc['Password']))
									debug("bbbbbbbbbbb")
									#rows_list[i].append(acc['Password'])
									rows_list[i].append('')
								if acc['HostAccount']['IsSuperAcct'] == True:
									IsSuperAcct = "是"
								else:
									IsSuperAcct = "否"
								rows_list[i].append(IsSuperAcct)#特权账号
								rows_list[i].append(acc['HostAccount']['FromAccountName'])
								rows_list[i].append(acc['HostAccount']['AcctSwitchCmd'])
								rows_list[i].append(acc['HostAccount']['SwitchPasswdPrompt'])
								i = i + 1				
						debug("1333333333333")
						debug("len:%d" % len(rows_list))
				
						b = 0
						while b < len(rows_list):
							rows_list[b].pop(0)
							b = b + 1
						debug("zzxccc")
						#rows_list.insert(0,title)
						writer.writerows(rows_list)
						#writer.writerow(detail_data)
					csvfile.close()
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
			debug("1231313hhhh")
			down_path = "/var/tmp/zdp/host.csv"
			debug("1231313hhhhjjjj")
			try:
				return send_from_directory('/var/tmp/zdp','host.csv',as_attachment=True)
			except Exception,e:
				debug(str(e))
	except IOError as err:  
		debug("1231zzxcxcx")
		return "{\"Result\":false,\"ErrMsg\":\"文件错误(%d): %s\"}" % (ERRNUM_MODULE_BATCH+3, ErrorEncode(e.args[1]))
@down_file.route('/export_data',methods=['GET', 'POST'])
def export_data():
	debug("zxcccexport")
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('z1')
	session = request.form.get('a0')
	choose = request.form.get('z2')
	format = request.form.get('z3')
	time1 = request.form.get('z4')
	debug("cccccccccc"+str(choose))
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	if type == '1':
		return down_templet()
	else:
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				sql = "delete from private.\"HostExportInfo\" where \"FileName\"=\'host.%s.%s.csv\'" % (userCode,session)
				curs.execute(sql)
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_account+3, ErrorEncode(e.args[1]))
			
		task_content = '[global]\nclass = taskdown_host\ntype = execute_down_cmd\nusercode=\"%s\"\nclientip=\"%s\"\nse=\"%s\"\nchoose=\"%s\"\nformat=\"%s\"\ntime1=\"%s\"\n' % (userCode,client_ip,session,choose,format,time1)
		debug(task_content)
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			debug("hhhhhhh")
			return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE_BATCH + 40,ErrorEncode(task_client.err_msg))
		return "true"
		#return down_host(userCode)
		
	

@down_file.route('/download_temp',methods=['GET', 'POST'])
def download_temp():
	debug("zxcccexport")
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('z1')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE_account+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE_account+2,error)
	return down_templet()
