#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import time
import json
import re
import MySQLdb
import struct
import socket
import htmlencode
from generating_log import system_log
from logbase import common
from comm import CertGet
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from ctypes import *
from Crypto.Cipher import DES3
import base64
from htmlencode import checkaccount

from flask import Flask,Blueprint,request,render_template # 
from index import left_index
from htmlencode import parse_sess
host_add = Blueprint('host_add',__name__)
ERRNUM_MODULE_host = 1000

def debug(c):
	return 0
        path = "/var/tmp/debugyt.txt"
        fp = open(path,"a+")
        if fp :
			fp.write(c)		
			fp.write("\n")
			fp.close()
def debug1(c):
	return 0
        path = "/var/tmp/debugyt.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
	
#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	
#设备类型
@host_add.route("/Devicetype_add", methods=['GET', 'POST'])
def Devicetype_add():
	t = "hostdevicetype_add.html"	
	return render_template(t)
#协议	
@host_add.route("/AccessProtocol_add", methods=['GET', 'POST'])
def AccessProtocol_add():
	t = "hostaccessprotocol_add.html"	
	return render_template(t)
#账号	
@host_add.route("/Account_add", methods=['GET', 'POST'])
def Account_add():
	t = "hostaccount_add.html"	
	return render_template(t)

#添加主机基本信息	
@host_add.route("/save_data_host", methods=['GET', 'POST'])
def save_data_host():
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

	host = request.form.get('a1')
	AccessAuth = request.form.get('a2')
	FromFlag = request.form.get('a10')
	host_tmp = host
	debug1("sssssfffffff")
	###判断是否在管理授权内
	host_json =  json.loads(host)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)


	if host_json['HostId'] == 0:	#编辑的时候不用判断
		sql = 'select public."PGetManagedScope"(E\'%s\')' % userCode
		debug1(sql)
		curs.execute(sql)
		result = curs.fetchall()#[0][0]
		if len(result) != 0:
			manage_scope = json.loads(result[0][0])
		else:
			manage_scope = None
		debug1(str(manage_scope))
		mhost_flag = 0
		mip_flag = 0
		if manage_scope != None:
			'''
			if manage_scope['MHostList'] != None:
				for mhost in manage_scope['MHostList']:
					debug1(str(host_json['HostIP']))
					if mhost['HostIP'] == host_json['HostIP']:
						mhost_flag = 1
						break
			if manage_scope['MIPList'] != None:
				for mip in manage_scope['MIPList']:
					if mip['StartIP'] == mip['EndIP']:
						if host_json['HostIP'] == mip['StartIP']:
							mip_flag = 1
							break
					else:
						start_ip = socket.ntohl(struct.unpack("I",socket.inet_aton(str(mip['StartIP'])))[0])
						end_ip = socket.ntohl(struct.unpack("I",socket.inet_aton(str(mip['EndIP'])))[0])
						host_ip = socket.ntohl(struct.unpack("I",socket.inet_aton(str(host_json['HostIP'])))[0])
						if host_ip >= start_ip and host_ip <= end_ip:
							mip_flag = 1
							break
			'''
			if manage_scope['MSScopeList'] != None:
				for mhost in manage_scope['MSScopeList']:##遍历每条授权
					if mhost['EnableIPLimit'] == 0:		#停用IP限制  看按组授权有没有
						if mhost['HGroupList'] != None:
							for grp_h in host_json['HGroupSet']: #保存的主机信息中有一个组不在范围内就报错
								flag_g = 0
								for grp in mhost['HGroupList']:
									if grp_h['HGId'] == grp['Id']:
										flag_g = 1
										break
								if flag_g == 0:
									mhost_flag = 0
									mip_flag = 0
									break
								else:
									mhost_flag = 1
									mip_flag = 0
					else:	#启用IP限制 
						if mhost['IPList'] == None:
							mhost_flag = 0
							mip_flag = 0
							break
						for mip in mhost['IPList']:
							if mip['EndIP'] == mip['StartIP']:
								if mip['StartIP'] == host_json['HostIP']:
									mhost_flag = 1
									break
							else: #IP范围
								start_ip = socket.ntohl(struct.unpack("I",socket.inet_aton(str(mip['StartIP'])))[0])
								end_ip = socket.ntohl(struct.unpack("I",socket.inet_aton(str(mip['EndIP'])))[0])
								host_ip = socket.ntohl(struct.unpack("I",socket.inet_aton(str(host_json['HostIP'])))[0])
								if host_ip >= start_ip and host_ip <= end_ip:
									mip_flag = 1
									break
						if mhost_flag ==0 and mip_flag == 0: #有一条授权没通过 就跳出
							break
		else:
			mhost_flag = mip_flag = 1
		if mhost_flag ==0 and mip_flag == 0:
			return '{"Result":false,"ErrMsg":"IP不在管理授权内"}'
	#### 账号 密码 加密 IsClearText ->true 加密
	
	account = host_json['AccountSet'];
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	for one in account:		
		if one.has_key('IsClearText') == True and one['IsClearText'] == True:	
			pwd_rc4.value = "0"*512 # 初始化 指针
			lib.encrypt_pwd(one['Password'],pwd_rc4);#执行函数
			one['Password'] = pwd_rc4.value #获取变量的值
	host = json.dumps(host_json);

	#判断 是否 超过 托管上限
	server_id=common.get_server_id();
	try:
		crt_t = CertGet(int(server_id))
	except Exception,e:
		crt_t = None

	max_count = 0
	if crt_t != None:
		max_count = crt_t[7]
	else:
		max_count = -1

	sql = "select count(*) from public.\"Host\";"

	curs.execute(sql)
	OperationalHosts = int(curs.fetchall()[0][0])

	if int(max_count) <= OperationalHosts and host_json['HostId'] == 0 and max_count != 0:
		results = '{"Result":false,"ErrMsg":"主机数量已达到托管上限"}'
	else:
		md5_str = request.form.get('m1')
		if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		else:
			md5_json = StrMD5(host_tmp);##python中的json的MD5
			if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
				return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
		sql="select public.\"PSaveHost\"(E'%s');" %(MySQLdb.escape_string(host).decode('utf-8'))
		debug(sql)
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
		#插入数据	
		try:
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		results = curs.fetchall()[0][0].encode('utf-8')
		
	#send system log
	sql = "select \"DeviceTypeName\" from public.\"DeviceType\" where \"DeviceTypeId\"=%d" % int(host_json['DeviceTypeId'])
	debug(sql)
	curs.execute(sql)
	DeviceTypeName_tmp = curs.fetchall()[0][0]

	if host_json['ServiceSet'] == []:
		Service_str = "无"
	else:
		HostService_array = []
		for i in host_json['ServiceSet']:
			host_array_tmp = {"HostServiceName":"SSH1","Protocol":"SSH","Port":"21","Account":[]}
			host_array_tmp['HostServiceName'] = i['HostServiceName']
			host_array_tmp['Protocol'] = i['ProtocolName']
			host_array_tmp['Port'] = i['Port']
			AccountName_array = []
			for j in host_json['AccountSet']:
				for k in j['HostServiceSet']:
					if str(k['ProtocolName']) == str(i['ProtocolName']) and int(k['Port']) == int(i['Port']):
						id = j['HostAccount']['AccountId']
						sql = "select \"Name\" from public.\"Account\" where \"AccountId\"=%d" % int(id)
						curs.execute(sql)
						AccountName_array.append(curs.fetchall()[0][0])
			host_array_tmp['Account'] = AccountName_array
			HostService_array.append(host_array_tmp)
		debug(str(HostService_array))
		Service_str = "服务："
		for i in HostService_array:
			if Service_str == "服务：":
				Service_str += "(协议："+str(i['Protocol'])+"，端口："+str(i['Port'])+"，账号["+'、'.join(i['Account'])+"])"
			else:
				Service_str += "、"+"(协议："+str(i['Protocol'])+"，端口："+str(i['Port'])+"，账号["+'、'.join(i['Account'])+"])"
	debug(Service_str)
	AccessRate = ''
	if int(host_json['AccessRate']) == 1:
		AccessRate = '正常'
	elif int(host_json['AccessRate']) == 2:
		AccessRate = '较慢'
	elif int(host_json['AccessRate']) == 3:
		AccessRate = '很慢'

	#Status = '启用'
	#if int(host_json['Status']) == 2:
	#	Status = '停用'

	EnableLoginLimit = '是'
	if host_json['EnableLoginLimit'] == False:
		EnableLoginLimit = '否'
		
	HGroup_array = []
	if host_json['HGroupSet'] == []:
		host_json['HGroupSet'] = [{"HGId":1}]
	for i in host_json['HGroupSet']:
		id = i['HGId']
		path_arry = []
		sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % i['HGId']
		curs.execute(sql)
		results_1 = curs.fetchall()
		path_arry.insert(0,results_1[0][1])

		while results_1[0][0] != 0:
			sql = 'select "HGroup"."ParentHGId","HGroup"."HGName" from "HGroup" where "HGroup"."HGId" = %d;' % results_1[0][0]
			debug(sql)
			curs.execute(sql)
			results_1 = curs.fetchall()
			path_arry.insert(0,results_1[0][1])
		path_str = '/'+'/'.join(path_arry)

		HGroup_array.append(path_str)

	ContentStr = "主机IP："+host_json['HostIP']+", 设备类型："+DeviceTypeName_tmp+", 访问速度："+AccessRate+", 是否唯一登陆："+EnableLoginLimit+", "+Service_str+", 主机组："+'、'.join(HGroup_array)
	debug(ContentStr)
	#
	results_json = json.loads(results)
	
	if results_json['Result'] == True:
		AccessAuth_json = json.loads(AccessAuth)
		AccessAuth_json['HostId'] = results_json['HostId']
		AccessAuth = json.dumps(AccessAuth_json);
		sql = "select public.\"PAddHostToAccessAuth\"(E'%s');" %(MySQLdb.escape_string(AccessAuth).decode('utf-8'))
		debug(sql)
		try:
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		conn.commit()
		if host_json['HostId'] == 0:
			system_log(userCode,"创建主机：%s (%s)" % (host_json['HostName'],ContentStr),"成功",FromFlag)
		else:
			system_log(userCode,"编辑主机：%s (%s)" % (host_json['HostName'],ContentStr),"成功",FromFlag)
		AccessAuth_Name = ""
		for i in AccessAuth_json['AccessAuthSet']:
			id = i['AccessAuthId']
			sql = "select \"AccessAuthName\" from public.\"AccessAuth\" where \"AccessAuthId\"=%d" % int(id)
			curs.execute(sql)
			AccessAuth_Name = curs.fetchall()[0][0]
			system_log(userCode,"访问授权\"%s\"新增授权主机：%s" % (AccessAuth_Name,host_json['HostName']),"成功",FromFlag)
	else:
		if host_json['HostId'] == 0:
			system_log(userCode,"创建主机：%s (%s)" % (host_json['HostName'],ContentStr),"失败："+results_json['ErrMsg'],FromFlag)
		else:
			system_log(userCode,"编辑主机：%s (%s)" % (host_json['HostName'],ContentStr),"失败："+results_json['ErrMsg'],FromFlag)		
	curs.close()
	conn.close()
	return results

#添加主机协议	
@host_add.route("/save_data_AccessProtocol", methods=['GET', 'POST'])
def save_data_AccessProtocol():
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
	
	proto = request.form.get('a1')
	if proto <0:
		proto = "";
		
	dec="select public.\"PSaveAccessProtocol\"(E'%s')" % (MySQLdb.escape_string(proto).decode('utf-8'))
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs.execute(dec)  
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret=json.loads(results)		#json转python对象
	result=ret["Result"]
	if(result == True):
		conn.commit()
		curs.close()
		conn.close()
		return results		#返回的是json数据
	else:
		curs.close()
		conn.close()
		return results

#添加主机设备类型
@host_add.route("/save_data_devicetype", methods=['GET', 'POST'])
def save_data_devicetype():
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
	
	device = request.form.get('a1')
	if device< 0:
		device =""
	dec="select public.\"PSaveDeviceType\"(E'%s')" % (MySQLdb.escape_string(device).decode('utf-8'))
	#debug(dec)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs.execute(dec)  
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret=json.loads(results)		#json转python对象
	result=ret["Result"]
	if(result == True):
		conn.commit()
		curs.close()
		conn.close()
		return results		#返回的是json数据
	else:
		curs.close()
		conn.close()
		return results
		
#添加主机账号
@host_add.route("/save_data_account", methods=['GET', 'POST'])
def save_data_account():
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
			
	account = request.form.get('a1')
	if account < 0:
		account = ""
		
	dec="select public.\"PSaveAccount\"(E'%s')" %(MySQLdb.escape_string(account).decode('utf-8'))
	#debug(dec)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs.execute(dec)  
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret=json.loads(results)		#json转python对象
	result=ret["Result"]
	if(result == True):
		conn.commit()
		curs.close()
		conn.close()
		return results		#返回的是json数据
	else:
		curs.close()
		conn.close()
		return results
#获取设备类型	
@host_add.route("/get_DeviceType", methods=['GET', 'POST'])
def get_DeviceType():
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
			
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs.execute("select public.\"PGetDeviceType\"(null,null,null,null,null,null,null);")
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	#debug("222222")
	conn.commit()
	curs.close()
	conn.close()
	return results		#返回的是json数据
#获取协议列表
@host_add.route("/get_protocol_list", methods=['GET', 'POST'])
def get_protocol_list():
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
	
	curpage = request.form.get('a2')
	if curpage <0 or curpage == "" or curpage == '0':
		curpage = 1
	ts = request.form.get('a3')
	if ts <0 or ts == "" or ts == '0':
		ts = 5
	
	all_list = request.form.get('a1')
	protocolid = request.form.get('a5')
	filter = request.form.get('a4')
	
	filter = filter.replace("'","''").replace('"','\"').replace('\\', '\\\\\\\\').replace("_", "\\\\_").replace("%", "\\\\%").replace("?", "\\\\?").replace(".", "\\\\.").replace("*", "\\\\*");
	debug(filter)
	filter = filter.replace('\\\\\\\\n','\\n')
	filter = filter.split(",")
	if(curpage!=""):
		ts = int(ts)
		startrow = (int(curpage)-1)*ts
	if(filter[0]!="")or(filter[1]!="")or(filter[2]!=""):
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if(all_list == 1):
			try:
				curs.execute("select public.\"PGetAccessProtocol\"(null,%s,%s,%s,null,null);"%(filter[0],filter[1],filter[2]))
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		elif(all_list == 0):
			try:
				curs.execute("select public.\"PGetAccessProtocol\"(%d,null,null,null,null,null);"%(protocolid))
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		else:
			try:
				#debug("ppppppppppppppppp")
				sql = "select public.\"PGetAccessProtocol\"(null,E'%s',E'%s',E'%s',%d,%d);"%(filter[0],filter[1],filter[2],ts,startrow)
				debug(sql)
				curs.execute(sql)
				
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	else:
		#debug("xtc")
		try:
			conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
		except pyodbc.Error,e:
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		try:
			curs = conn.cursor()
		except pyodbc.Error,e:
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		if(all_list == '1'):
			#debug("ffffffffffff")		
			try:
				curs.execute("select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);")
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		elif(all_list == '0'):
			#debug("eeeeeeeeee")
			protocolid=int(protocolid)
			try:
				curs.execute("select public.\"PGetAccessProtocol\"(%d,null,null,null,null,null);"%(protocolid))
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		else:
			try:
				curs.execute("select public.\"PGetAccessProtocol\"(null,null,null,null,%d,%d);"%(ts,startrow))
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	#debug("222222")
	conn.commit()
	curs.close()
	conn.close()
	return results		#返回的是json数据

#删除协议
@host_add.route("/delete_protocol_list", methods=['GET', 'POST'])
def delete_protocol_list():
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
	
	protocolid = request.form.get('a1')
	#debug(protocolid)
	protocolid = protocolid.split(',')
	#debug("hhhhhhhhhhhhhhhhhh")
	#lenth = len(userid)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	for proid in protocolid:
		#debug("tttttttttttt")
		proid = int(proid)
		#debug(proid)
		try:
			#debug("11111111")
			curs.execute("select public.\"PDeleteAccessProtocol\"(%d);"%(proid))
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#results = curs.fetchall()[0][0].encode('utf-8')
	#debug("222222")
	conn.commit()
	curs.close()
	conn.close()
	return "{\"Result\":true}"		#返回的是json数据
#删除一条
@host_add.route("/delete_protocol", methods=['GET', 'POST'])
def delete_protocol():
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
	
	protocolid = request.form.get('proto_d')
	protocolid = int(protocolid)
	#lenth = len(userid)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs.execute("select public.\"PDeleteAccessProtocol\"(%d);"%(protocolid))
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	#results = curs.fetchall()[0][0].encode('utf-8')
	conn.commit()
	curs.close()
	conn.close()
	return "{\"Result\":true}"		#返回的是json数据		
#编辑保存协议		
@host_add.route("/save_protocol", methods=['GET', 'POST'])
def save_protocol():
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
	
	savedata = request.form.get('a1')
	dec="select public.\"PSaveAccessProtocol\"(E'%s');" %(MySQLdb.escape_string(savedata).decode('utf-8'))
	debug(dec)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs.execute(dec)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	ret=json.loads(results)		#json转python对象
	result=ret["Result"]
	if(result == True):
		conn.commit()
		curs.close()
		conn.close()
		return results		#返回的是json数据
	else:
		curs.close()
		conn.close()
		return results	
#获取连接参数	
@host_add.route("/get_ConnParam_list", methods=['GET', 'POST'])
def get_ConnParam_list():	 
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
	
	protocolid = request.form.get('a1')
	if protocolid <0 or protocolid =="":
		protocolid = 0;
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql="select public.\"PGetConnParam\"(%s,null,null,null,null,null,null);"% (int(protocolid))
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
#获取域名	
@host_add.route("/get_DomainName_list", methods=['GET', 'POST'])
def get_DomainName_list():
	 
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
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql="select public.\"PGetDomain\"(null,null,null,null,null);"
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
		
#获取来源主机		
@host_add.route("/get_fromhost", methods=['GET', 'POST'])
def get_fromhost():	
	reload(sys)
	sys.setdefaultencoding('utf-8')
	loginuc = request.form.get('a1')
	if checkaccount(loginuc) ==False:
		return '',403
	loginuc = "E'%s'" %(loginuc)
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
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql ="select public.\"PGetHost\"(null,null,%s);" %(loginuc) 
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
        result_tmp = curs.fetchall()
        if result_tmp[0][0] != None:
            results = result_tmp[0][0].encode('utf-8')
        else:
            results = "{}"
	curs.close()
	conn.close()
	return results
	
#获取来源服务	
@host_add.route("/get_FromHostServiceName", methods=['GET', 'POST'])
def get_FromHostServiceName():	
	reload(sys)
	sys.setdefaultencoding('utf-8')	
	loginuc = request.form.get('a2')
	if checkaccount(loginuc) ==False:
		return '',403
	
	loginuc = "E'%s'" %(loginuc)
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
	
	host_id = request.form.get('a1')
	if host_id<0 or host_id == "":
		host_id = 0
	if str(host_id).isdigit() == False:
		return '',403
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql ="select public.\"PGetHost\"(%d,null,%s)" %(int(host_id),loginuc) 
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0]
	if results:
		results = results.encode('utf-8')
	else:
		results = "{}"
	curs.close()
	conn.close()
	return results
	
#获取accIP
@host_add.route("/get_accIP", methods=['GET', 'POST'])
def get_accIP():
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
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql ="select public.\"PGetAccIP\"(null,null)"
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
		
#获取账号
@host_add.route("/get_account", methods=['GET', 'POST'])
def get_account():
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
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql ="select public.\"PGetAccount\"(null,null,null,null,null)"
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return results
	
#批量 增加主机
@host_add.route("/add_host_batch", methods=['GET', 'POST'])
def add_host_batch():	
	##socket.inet_ntoa(struct.pack("=I", 1077545662))
	##socket.ntohl(struct.unpack("I",socket.inet_aton(str('192.168.0.1')))[0])
	##socket.inet_ntoa(struct.pack('I',socket.htonl(3232235532)))
	debug('in')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_host + 3, ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}"% (ERRNUM_MODULE_host + 4, ErrorEncode(e.args[1]))		
	reload(sys)
	sys.setdefaultencoding('utf-8')	
	count_start = int(request.form.get('a0'))
	count_end = int(request.form.get('a1'))
	iplong = socket.ntohl(struct.unpack("I",socket.inet_aton(str('192.169.0.1')))[0])
	debug(str(iplong))
	for j in range(count_start, count_end+1):
		HostName = "testhostlong" + str(j)
		hostip = socket.inet_ntoa(struct.pack('I',socket.htonl(long(iplong + j)))) 
		debug(str(hostip))	
		host = {
			'HostId': 0,
			'HostName': HostName,
			'HostIP': hostip,
			'Description': None,
			'AccessRate': 1,   
			'EnableLoginLimit': False,  
			'Status': 0,
			'DeviceTypeId': 1,
			'HGroupSet': [
				{
					'HGId':2003
				}
			],
			'ServiceSet': None,
			'AccountSet':None
		}
		debug('begin_sql')
		sql="select public.\"PSaveHost\"(E'%s');" %(MySQLdb.escape_string(json.dumps(host)).decode('utf-8'))
	
		#插入数据	
		try:
			debug(sql);
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return "{\"Result\":false,\"ErrMsg\":\"插入主机失败(%d): %s\"}"% (ERRNUM_MODULE_host + 7, ErrorEncode(e.args[1]))
		results = curs.fetchall()[0][0].encode('utf-8')
		results_json = json.loads(results)
		if results_json['Result'] == False:
			debug(sql)
		
	conn.commit()
	curs.close()
	conn.close()
	return results	

#判断是否超过托管上限
@host_add.route("/exceed_hostLimit", methods=['GET', 'POST'])
def exceed_hostLimit():
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

	#判断 是否 超过 托管上限
	server_id = common.get_server_id()
	try:
		crt_t = CertGet(int(server_id))
	except Exception,e:
		crt_t = None

	max_count = 0
	if crt_t != None:
		max_count = crt_t[7]
	else:
		max_count = 0
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	sql = "select count(*) from public.\"Host\";"

	curs.execute(sql)
	OperationalHosts = int(curs.fetchall()[0][0])

	if int(max_count) <= OperationalHosts and max_count != 0:
		return '{"Result":false,"ErrMsg":"主机数量已达到托管上限"}'
	else:
		return '{"Result":true}'
#显示密钥
@host_add.route('/get_sshkey_host',methods=['GET', 'POST'])
def get_sshkey_host():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	KeyType = "1"	#0public 1private
	IfValid = 'null'
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	usercode = system_user
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
			# PGetSshKey(usercode,KeyType,IfValid,limitrow,offsetrow) 
			sql="select public.\"PGetSshKey\"(E'%s',%s,%s,null,null);"% (usercode,KeyType,IfValid)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results_json=json.loads(results)
			if len(results_json['data'])>10:
                                results=json.dumps(results_json)
			else:
				for i in results_json['data']:
                                        if i['Password']!=None:
                                                if os.path.exists('/usr/lib64/logproxy.so') == False:
                                                        return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
                                                lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
                                                pwd_rc4 = c_char_p()# 定义一个指针
                                                pwd_rc4.value = "0"*512 # 初始化 指针
                                                lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
                                                lib.decrypt_pwd.restype = None #定义函数返回值
                                                ret = lib.decrypt_pwd(i['Password'],pwd_rc4);#执行函数
                                                i['Password'] = pwd_rc4.value #获取变量的值
					try:
                                        	key='SafeT1Ba5eSafeT1'
                                        	des3=DES3.new(key,DES3.MODE_ECB)
                                        	i['KeyContent']=base64.b64decode(i['KeyContent'])
                                        	i['KeyContent']=des3.decrypt(i['KeyContent'])
						while True:
							c=i['KeyContent'][-1]
							if ord(c)==0:
								i['KeyContent']=i['KeyContent'][:-1]
							else:
								break
					except Exception,e:
						pass
                                results=json.dumps(results_json)	
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

def init_str(s):
    l=len(s) % 16
    print 'l',l
    if l!=0:
        c=16-l
        s+=chr(0)*c
    return s

#创建和编辑
@host_add.route('/add_sshkey_host',methods=['GET','POST'])
def add_sshkey_host():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	sshkey = request.form.get('a1')
	flag = request.form.get('a10')
	md5_str = request.form.get('m1')
	if sess<0:
		sess=""
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
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(sshkey);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	sshkey = json.loads(sshkey)
	sshkey['UserCode'] = system_user
	if(sshkey['Password'] != "" and sshkey['Password']!=None):
                if os.path.exists('/usr/lib64/logproxy.so') == False:
                	return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
                lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
                pwd_rc4 = c_char_p()# 定义一个指针
                pwd_rc4.value = "0"*512 # 初始化 指针
                lib.encrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
                lib.encrypt_pwd.restype = None #定义函数返回值
                ret = lib.encrypt_pwd(sshkey['Password'],pwd_rc4);#执行函数
                sshkey['Password'] = pwd_rc4.value #获取变量的值        
	key='SafeT1Ba5eSafeT1'
        des3=DES3.new(key,DES3.MODE_ECB)
        sshkey['KeyContent']=init_str(sshkey['KeyContent'])
        res2=des3.encrypt(sshkey['KeyContent'])
        sshkey['KeyContent']=base64.b64encode(res2)
	sshkey = json.dumps(sshkey)
	sshkey=str(sshkey)

	# PSaveSshKey(sshkey)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PSaveSshKey\"(E'%s');" %(MySQLdb.escape_string(sshkey).decode("utf-8"))
			debug(sql)
			curs.execute(sql)
			sshkey_json=json.loads(sshkey)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if sshkey_json['SshKeyId']==0:
				oper='创建密钥：%s'%sshkey_json['KeyName']
			else:
				oper='编辑密钥：%s'%sshkey_json['KeyName']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],flag):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				#return result 
				if not system_log(system_user,oper,'成功',flag):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			return result
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#显示密钥(运维)
@host_add.route('/get_sshkey_host_u',methods=['GET', 'POST'])
def get_sshkey_host_u():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	ip_str = request.form.get('a1')
	server_str = request.form.get('a2')
	account_str = request.form.get('a3')


	if ip_str < 0:
		ip_str = "null"
	else:
		ip_str = "'%s'" %ip_str

	if server_str < 0:
		server_str = "null"
	else:
		server_str = "'%s'" %server_str

	if account_str < 0:
		account_str = "null"
	else:
		account_str = "'%s'" %account_str	

	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	usercode = system_user
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
			# PGetSshKey(usercode,KeyType,IfValid,limitrow,offsetrow) 
			sql="select public.\"GetSshPrivateKey\"(E'%s',null,%s,%s,%s);"% (system_user,ip_str,server_str,account_str)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results == None:
				return "{\"Result\":true,\"info\":\"%s\"}" % results
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

##获取 主机 或者主机组的简要信息        
@host_add.route('/getDetail_u',methods=['GET', 'POST'])
def getDetail_u():
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

	ip = request.form.get('a1')
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)

	sql = "select \"Host\".\"HostId\" from public.\"Host\" where \"Host\".\"HostIP\"=E'%s';" %(ip)
	debug(sql)
	curs.execute(sql)

	host_id = curs.fetchall()[0][0]
	host_id = str(host_id)
	debug(host_id)
	sql = "select public.\"PGetHost\"(%s,false,E'%s')" %(host_id,userCode)
	debug(sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"data\":%s}" % (results)
	
@host_add.route('/DeRc4',methods=['GET', 'POST'])
def DeRc4():
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

	pwd = request.form.get('a1')
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	pwd_rc4 = c_char_p()# 定义一个指针
	lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
	lib.decrypt_pwd.restype = None #定义函数返回值
	pwd_rc4.value = "0"*512 # 初始化 指针
	debug(str(pwd))
	lib.decrypt_pwd(str(pwd),pwd_rc4);
	#lib.decrypt_pwd(pwd_rc4,acc['Password']);#执行函数
	debug('hhhhhhhhjjj')
	debug(pwd_rc4.value)
	return "{\"Result\":true,\"data\":%s}" % (pwd_rc4.value)


@host_add.route('/get_sshkey_u',methods=['GET', 'POST'])
def get_sshkey_u():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	limitrow = request.form.get('a4')
	offsetrow = request.form.get('a3')
	search_typeall = request.form.get('a2')
	sshkeyid = request.form.get('a1')
	KeyType=request.form.get('a5')
	if KeyType=='' or KeyType<0:
		KeyType='null'
	sshkeyname = ""
	IfValid ="null"
	#KeyType ="null"
	keyname = ""
	keycontent = ""
	all = ""
	if sshkeyid<0 or sshkeyid=="" or sshkeyid=="0":
		sshkeyid=None
	else:
		sshkeyid=int(sshkeyid)
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	
	if offsetrow <0:
		offsetrow = "null"
	else:
		offsetrow=int(offsetrow)
	if limitrow < 0:
		limitrow = "null"
	else:
		limitrow=int(limitrow)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	usercode = system_user
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
		if search_s[0]=="keyname":
			keyname=keyname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="keycontent":
			keycontent=keycontent+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			all=all+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if keyname!="":	
		keyname="%s"%keyname[:-1]
	if keycontent!="":
		keycontent="%s"%keycontent[:-1]
	if all!="":	
		all="%s"%all[:-1]
	all=all.replace("\\\\","\\\\\\\\")
	all=all.replace(".","\\\\.")
	all=all.replace("?","\\\\?")
	all=all.replace("+","\\\\+")
	all=all.replace("(","\\\\(")
	all=all.replace("*","\\\\*")
	all=all.replace("[","\\\\[")
	all=all.replace("\n","\\n")
	keycontent=keycontent.replace("\\\\","\\\\\\\\")
	keycontent=keycontent.replace(".","\\\\.")
	keycontent=keycontent.replace("?","\\\\?")
	keycontent=keycontent.replace("+","\\\\+")
	keycontent=keycontent.replace("(","\\\\(")
	keycontent=keycontent.replace("*","\\\\*")
	keycontent=keycontent.replace("[","\\\\[")
	keycontent=keycontent.replace("\n","\\n")
	keyname=keyname.replace("\\\\","\\\\\\\\")
	keyname=keyname.replace(".","\\\\.")
	keyname=keyname.replace("?","\\\\?")
	keyname=keyname.replace("+","\\\\+")
	keyname=keyname.replace("(","\\\\(")
	keyname=keyname.replace("*","\\\\*")
	keyname=keyname.replace("[","\\\\[")
	keyname=keyname.replace("\n","\\n")
	data = {"SshKeyId":sshkeyid,"KeyName":keyname,"KeyContent":keycontent,"searchstring":all}
	searchconn = json.dumps(data)
	debug(searchconn)
	if offsetrow!="null":
		offsetrow=(offsetrow-1)*limitrow
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetSshKey(usercode,KeyType,IfValid,limitrow,offsetrow) 
			sql="select public.\"PGetSshKey\"(E'%s',%s,%s,%s,%s,E'%s');"% (usercode,KeyType,IfValid,limitrow,offsetrow,searchconn)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results_json=json.loads(results)
			if len(results_json['data'])>10:
				results=json.dumps(results_json)
			else:
				
				for i in results_json['data']:
					if i['Password']!=None:
						if os.path.exists('/usr/lib64/logproxy.so') == False:
							return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
						lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
						pwd_rc4 = c_char_p()# 定义一个指针
						pwd_rc4.value = "0"*512 # 初始化 指针
						lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
						lib.decrypt_pwd.restype = None #定义函数返回值
						ret = lib.decrypt_pwd(i['Password'],pwd_rc4);#执行函数
						i['Password'] = pwd_rc4.value #获取变量的值
				
				results=json.dumps(results_json)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)


@host_add.route('/get_sshkey_u_plus',methods=['GET', 'POST'])
def get_sshkey_u_plus():
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	limitrow = request.form.get('a4')
	offsetrow = request.form.get('a3')
	search_typeall = request.form.get('a2')
	sshkeyid = request.form.get('a1')
	KeyType=request.form.get('a5')
	if KeyType=='' or KeyType<0:
		KeyType='null'
	sshkeyname = ""
	IfValid ="null"
	#KeyType ="null"
	keyname = ""
	keycontent = ""
	all = ""
	if sshkeyid<0 or sshkeyid=="" or sshkeyid=="0":
		sshkeyid=None
	else:
		sshkeyid=int(sshkeyid)
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	
	if offsetrow <0:
		offsetrow = "null"
	else:
		offsetrow=int(offsetrow)
	if limitrow < 0:
		limitrow = "null"
	else:
		limitrow=int(limitrow)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	usercode = system_user
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
		if search_s[0]=="keyname":
			keyname=keyname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="keycontent":
			keycontent=keycontent+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			all=all+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if keyname!="":	
		keyname="%s"%keyname[:-1]
	if keycontent!="":
		keycontent="%s"%keycontent[:-1]
	if all!="":	
		all="%s"%all[:-1]
	all=all.replace("\\\\","\\\\\\\\")
	all=all.replace(".","\\\\.")
	all=all.replace("?","\\\\?")
	all=all.replace("+","\\\\+")
	all=all.replace("(","\\\\(")
	all=all.replace("*","\\\\*")
	all=all.replace("[","\\\\[")
	all=all.replace("\n","\\n")
	keycontent=keycontent.replace("\\\\","\\\\\\\\")
	keycontent=keycontent.replace(".","\\\\.")
	keycontent=keycontent.replace("?","\\\\?")
	keycontent=keycontent.replace("+","\\\\+")
	keycontent=keycontent.replace("(","\\\\(")
	keycontent=keycontent.replace("*","\\\\*")
	keycontent=keycontent.replace("[","\\\\[")
	keycontent=keycontent.replace("\n","\\n")
	keyname=keyname.replace("\\\\","\\\\\\\\")
	keyname=keyname.replace(".","\\\\.")
	keyname=keyname.replace("?","\\\\?")
	keyname=keyname.replace("+","\\\\+")
	keyname=keyname.replace("(","\\\\(")
	keyname=keyname.replace("*","\\\\*")
	keyname=keyname.replace("[","\\\\[")
	keyname=keyname.replace("\n","\\n")
	data = {"SshKeyId":sshkeyid,"KeyName":keyname,"KeyContent":keycontent,"searchstring":all}
	searchconn = json.dumps(data)
	debug(searchconn)
	if offsetrow!="null":
		offsetrow=(offsetrow-1)*limitrow
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select b."UserCode" from public."User" b where b."UserId"=(select a."UserId" from public."SshKey" a where a."SshKeyId" = %d);' % (sshkeyid)
			curs.execute(sql)
			usercode = curs.fetchall()[0][0]
			# PGetSshKey(usercode,KeyType,IfValid,limitrow,offsetrow) 
			sql="select public.\"PGetSshKey\"(E'%s',%s,%s,%s,%s,E'%s');"% (usercode,KeyType,IfValid,limitrow,offsetrow,searchconn)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			results_json=json.loads(results)
			if len(results_json['data'])>10:
				results=json.dumps(results_json)
			else:
				
				for i in results_json['data']:
					if i['Password']!=None:
						if os.path.exists('/usr/lib64/logproxy.so') == False:
							return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
						lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
						pwd_rc4 = c_char_p()# 定义一个指针
						pwd_rc4.value = "0"*512 # 初始化 指针
						lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
						lib.decrypt_pwd.restype = None #定义函数返回值
						ret = lib.decrypt_pwd(i['Password'],pwd_rc4);#执行函数
						i['Password'] = pwd_rc4.value #获取变量的值
				
				results=json.dumps(results_json)
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)	
	
	
