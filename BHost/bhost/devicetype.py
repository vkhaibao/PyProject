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
import htmlencode
from index import PGetPermissions
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Blueprint,request,render_template # 
devicetype = Blueprint('devicetype',__name__)
ERRNUM_MODULE = 2000
def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()

def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;
'''
def PGetPermissions(us):
	global ERRNUM_MODULE
	ERRNUM_MODULE = 3000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(us)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if result==None:
				result='[]'
	except pyodbc.Error,e:
		return "[]"
	return str(result)
'''	

@devicetype.route('/devicetype_manage',methods=['GET', 'POST'])
def devicetype_manage():
	se = request.form.get('a0')
	now = request.form.get('z1')
	keyword = request.form.get('z4')
	filter_flag = request.form.get('z5')
	selectid = request.form.get('z6')
	
	if se == "" or se == None:
		se = request.args.get('a0')

	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)

	if keyword == None:
		keyword = "[]"
	if filter_flag == None:
		filter_flag = 0
	if selectid == None:
		selectid = "[]"
	
	if(str(filter_flag).isdigit() == False):
		return '',403
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
	
	
	_power = PGetPermissions(usercode)
	_power = str(_power)
	_power_json = json.loads(_power)
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	
	return render_template('manage_devicetype.html',keyword=keyword,tasktype="2",now=now,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id);

@devicetype.route('/add_devicetype',methods=['GET', 'POST'])
def add_devicetype():
	se = request.form.get('a0')
	now = request.form.get('z1')
	edit = request.form.get('z2')
	type = request.form.get('z3')
	keyword = request.form.get('z4')
	filter_flag = request.form.get('z5')
	selectid = request.form.get('z6')
	
	client_ip = request.remote_addr
	(error,usercode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	if selectid == None:
		selectid = "[]"
	
	if(str(filter_flag).isdigit() == False):
		return '',403
		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403
	
	if	selectid.find(']') < 0:
		return '',403
	select_tmp = selectid[1:-1]
	for a in select_tmp.split(','):
		if( str(a) !='' and str(a).isdigit() == False):
			return '',403 
	
	if edit !="None":
		try:
			edit_json = json.loads(edit);
		except:
			return '',403
		
	t = "add_devicetype.html"
	
	_power = PGetPermissions(usercode)
	_power = str(_power)
	_power_json = json.loads(_power)
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	
	if edit != "None":
		return render_template(t,edit=edit,now=now,tasktype=type,keyword=keyword,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id)
	else:
		return render_template(t,edit='"None"',now=now,tasktype=type,keyword=keyword,filter_flag=filter_flag,selectid=selectid,manage_power_id=manage_power_id)


##设备类型列表、过滤、分页
@devicetype.route('/get_devicetype_list',methods=['GET', 'POST'])
def get_devicetype_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session =request.form.get('a0')
	number = request.form.get('z1')
	curpage = request.form.get('z2')
	keyword = request.form.get('z3')
	dsc = request.form.get('dsc')
	if dsc < 0 or dsc =='':
		dsc = 'false'
	elif dsc!='false' and dsc!='true':
		return '',403
		
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if number < 0:
		number = 0
	if curpage < 0:
		curpage = 0
	if number != "null":
		row = int(number)*(int(curpage)-1)
	else:
		row = "null"
	filter_cond_arry = [[],[],[],[],[],[]]#所有、名称、描述、状态、账号切换、切换密码
	if keyword != "":
		keyword = json.loads(keyword);
		if len(keyword) != 0:
			for i in keyword:
				filter_arry = i.split('-',1)
				filter_cond_arry[int(filter_arry[0])].append(MySQLdb.escape_string(filter_arry[1]).decode("utf-8"))
	i = 0
	while i < 6:
		filter_cond_arry[i] = '\n'.join(filter_cond_arry[i])
		filter_cond_arry[i] = MySQLdb.escape_string(filter_cond_arry[i]).decode("utf-8")
		if i == 0:
			filter_cond_arry[i] = filter_cond_arry[i].replace("\\","\\\\").replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		else:
			filter_cond_arry[i] = filter_cond_arry[i].replace(".","\\\\.").replace("'","''").replace("?","\\\\?").replace("$","\\\\$").replace("*","\\\\*").replace(")","\\\\)").replace("(","\\\\(").replace("+","\\\\+").replace("{","\\\\{").replace("}","\\\\}").replace("]","\\\\]").replace("[","\\\\[").replace("^","\\\\^")
		
		if filter_cond_arry[i] == "":
			filter_cond_arry[i] = 'null'
		else:
			if i == 4 or i == 5 or i == 0:
				filter_cond_arry[i] = '"%s"' % filter_cond_arry[i]
			else:
				filter_cond_arry[i] = "E'%s'" % filter_cond_arry[i]
		i += 1
	searchstring = '{\"AcctSwitchCmd\":%s,\"SwitchPasswdPrompt\":%s,\"searchstring\":%s}' % (filter_cond_arry[4],filter_cond_arry[5],filter_cond_arry[0])
	if filter_cond_arry[3] == '3':
		filter_cond_arry[3] = "null"
	searchstring = "E'%s'" % MySQLdb.escape_string(searchstring).decode("utf-8")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetDeviceType\"(null,%s,%s,%s,false,%s,%s,%s,%s);"%(filter_cond_arry[1],filter_cond_arry[2],filter_cond_arry[3],number,str(row),searchstring,dsc))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

###删除
@devicetype.route('/devicetype_delete',methods=['GET', 'POST'])
def devicetype_delete():
	session = request.form.get('a0')
	type = request.form.get('z1')
	id = request.form.get('z2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(ERRNUM_MODULE+1,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(ERRNUM_MODULE+2,error)
			
	if check_role(userCode,"主机管理") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				sql = "select \"DeviceTypeName\" from public.\"DeviceType\" where \"DeviceTypeId\" in (%s)" % id[1:-1]
				curs.execute(sql)
				dev_str = ""
				for row in curs.fetchall():
					dev_str = dev_str + row[0].encode('utf-8') + ","	
				
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select \"DeviceTypeName\" from public.\"DeviceType\" where \"DeviceTypeId\"=%d" % int(id)
					curs.execute(sql)
					dev_name = curs.fetchall()[0][0].encode('utf-8')
					
					curs.execute("select public.\"PDeleteDeviceType\"(%d);"%(int(id)))
					result = curs.fetchall()[0][0].encode('utf-8')
					results = json.loads(result)
					if results['Result'] == False:
						system_log(userCode,"删除设备类型:%s" % dev_name,"失败："+result['ErrMsg'],"运维管理>设备类型")
						conn.rollback();
						return result
				if dev_str != "":
					system_log(userCode,"删除设备类型:%s" % dev_str[:-1],"成功","运维管理>设备类型")
				return "{\"Result\":true}"
			else:
				sql = "select \"DeviceTypeName\" from public.\"DeviceType\" where \"DeviceTypeId\"=%d" % int(id)
				curs.execute(sql)
				dev_name = curs.fetchall()[0][0].encode('utf-8')
				
				curs.execute("select public.\"PDeleteDeviceType\"(%d);"%(int(id)))
				results = curs.fetchall()[0][0].encode('utf-8')
				re_dev = json.loads(results)
				if re_dev['Result']:
					system_log(userCode,"删除设备类型:%s" % dev_name,"成功","运维管理>设备类型")
				else:
					system_log(userCode,"删除设备类型:%s" % dev_name,"失败："+re_dev['ErrMsg'],"运维管理>设备类型")
				return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
###保存
@devicetype.route('/save_devicetype',methods=['GET', 'POST'])
def save_devicetype():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	global_data = request.form.get('a1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if global_data < 0:
		global_data = ""
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(global_data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
			
	dev_json = json.loads(global_data)
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)	
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)		
	try:
		sql = "select public.\"PSaveDeviceType\"(E'%s')" %(MySQLdb.escape_string(global_data).decode("utf-8"))
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')
	result_json = json.loads(result)
	
	detail_msg = ""
	if dev_json['Description'] != "" and dev_json['Description'] != None:
		Description = "描述：" + dev_json['Description'] + '，'
	else:
		Description = "";
	
	if dev_json['DeviceTypeIcon'] != "" and dev_json['DeviceTypeIcon'] != None:
		DeviceTypeIcon = "主机图标：" + dev_json['DeviceTypeIcon'] + '，'
	else:
		DeviceTypeIcon = "";
	
	if dev_json['Status'] == 0:
		status = "状态：显示，"
	elif dev_json['Status'] == 1:
		status = "状态：隐藏，"
	else:
		status = ""
		
	if dev_json['AcctSwitchCmd'] != "" and dev_json['AcctSwitchCmd'] != None:
		AcctSwitchCmd = "账号切换命令：" + dev_json['AcctSwitchCmd'] + '，'
	else:
		AcctSwitchCmd = "";
		
	if dev_json['SwitchPasswdPrompt'] != "" and dev_json['SwitchPasswdPrompt'] != None:
		SwitchPasswdPrompt = "切换密码提示：" + dev_json['SwitchPasswdPrompt'] + '，'
	else:
		SwitchPasswdPrompt = "";
	
	service_list = []
	for service in dev_json['ServiceSet']:
		DeviceServiceName = service['DeviceServiceName']
		ProtocolName = "协议：" + service['ProtocolName']
		Port = "端口：" + str(service['Port'])
		service_msg = DeviceServiceName + '（' + ProtocolName + ', ' + Port + '）'
		service_list.append(service_msg)
	
	if len(service_list) != 0:
		service_str = "服务：" + ('、').join(service_list)
	else:
		service_str = ""
		
	detail_msg = Description + DeviceTypeIcon + status + AcctSwitchCmd + SwitchPasswdPrompt + service_str
	
	if result_json['Result'] == False:
		if dev_json['DeviceTypeId'] == 0:
			system_log(userCode,"创建设备类型：%s" % dev_json['DeviceTypeName'],"失败："+result_json['ErrMsg'],"运维管理>设备类型")
		else:
			system_log(userCode,"编辑设备类型：%s" % dev_json['DeviceTypeName'],"失败："+result_json['ErrMsg'],"运维管理>设备类型")
		result_json['ErrMsg'] = result_json['ErrMsg'] + '(%d)' % sys._getframe().f_lineno
		conn.commit()
		curs.close()
		conn.close()
		return json.dumps(result_json)
	if dev_json['DeviceTypeId'] == 0:
		show_msg = "创建设备类型：%s（%s）" % (dev_json['DeviceTypeName'],detail_msg)
		system_log(userCode,show_msg,"成功","运维管理>设备类型")
	else:
		show_msg = "编辑设备类型：%s（%s）" % (dev_json['DeviceTypeName'],detail_msg)
		system_log(userCode,show_msg,"成功","运维管理>设备类型")
	conn.commit()
	curs.close()
	conn.close()
	return result
	
###回显
@devicetype.route('/get_data',methods=['GET', 'POST'])
def get_data():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('a2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if id <0 or id == '':
		id = 0
	else:
		id = int(id)
		
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	
	try:
		sql = "select public.\"PGetDeviceType\"(%d,null,null,null,5,0)" %(id)
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return result

@devicetype.route('/check_edit_devicetype',methods=['GET', 'POST'])
def check_edit_devicetype():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id = request.form.get('z1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if id != '-1':
				curs.execute("select public.\"PGetDeviceType\"(%d,null,null,null,false,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetDeviceType\"(null,null,null,null,false,null,null);")	
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	
	
	
	
