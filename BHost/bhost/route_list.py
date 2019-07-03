#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import MySQLdb
import base64
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common

from logbase import task_client
from logbase import defines
from index import PGetPermissions
from generating_log import system_log

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
from htmlencode import parse_sess,check_role,ErrorEncode
import re
route_list = Blueprint('route_list',__name__)
module_name = "系统管理"
module = "系统管理>网络设置"
ERRNUM_MODULE_route = 1000

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
def checkip(ip):
	p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
	if p.match(ip):
		return True
	else:
		return False
@route_list.route('/route_show',methods=['GET','POST'])
def route_show():
	ipage = request.form.get('z1')
	keyword = request.form.get('z2')
	filter_flag = request.form.get('z3')
	selectid = request.form.get('z4')
	if keyword == None:
		keyword = "[]"
	if filter_flag == None:
		filter_flag = 0
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
	_power=PGetPermissions(us)
	_power_json = json.loads(str(_power));
	_power_mode = 2;
	for one in _power_json:
		if one['SystemMenuId'] == 6:
			_power_mode = one['Mode']	
	return render_template('route_list.html',ipage=ipage,se=sess,keyword=keyword,filter_flag=filter_flag,selectid=selectid,error_msg=error_msg,_power_mode=_power_mode)
	
@route_list.route('/create_route',methods=['GET','POST'])
def create_route():
	if request.method == "GET":
		ipage = request.args.get('z1')
		id = request.args.get('z2')
		keyword = request.args.get('z3')
		filter_flag = request.args.get('z4')
		selectid = request.args.get('z5')
		sess = request.args.get('a0')
	else:
		ipage = request.form.get('z1')
		id = request.form.get('z2')
		keyword = request.form.get('z3')
		filter_flag = request.form.get('z4')
		selectid = request.form.get('z5')
		sess = request.form.get('a0')
	if sess <0 or sess == '':
		sess = request.args.get('a0')
	if sess <0 or sess =='':
		sess ='';
	return render_template('create_route.html',ipage=ipage,route_id=id,keyword=keyword,filter_flag=filter_flag,selectid=selectid,se=sess)

@route_list.route('/get_serverglobal',methods=['GET','POST'])
def get_serverglobal():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetServerGlobal\"('{}');")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@route_list.route('/get_server_ipv4',methods=['GET','POST'])
def get_server_ipv4():
	reload(sys)
	sys.setdefaultencoding('utf-8')	
	id = request.form.get('z1')
	type = request.form.get('z2')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if type == '0':
				curs.execute("select public.\"PGetServerIPV4\"(null,null,null,null,null,%d,null,null);"%(int(id)))
			else:
				curs.execute("select public.\"PGetServerIPV4\"(%d,null,null,null,null,null,null,null);"%(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@route_list.route('/get_route_list',methods=['GET', 'POST'])
def get_route_list():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	page = request.form.get('z4')
	ipage = request.form.get('z5')
	keyword = request.form.get('z6')
	server_id = request.form.get('z7')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	
	filter_cond_arry = [[],[],[],[],[],[]]#所有、网口、网关、下一跳转地址、掩码、类型
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
		elif i == 0:
			filter_cond_arry[i] = 'E"%s"' % filter_cond_arry[i]
		else:
			filter_cond_arry[i] = "E'%s'" % filter_cond_arry[i]
		i += 1
	searchstring = "'{\"searchstring\":%s}'" % (filter_cond_arry[0])
	if filter_cond_arry[5] == "'0'":
		filter_cond_arry[5] = "null"
	if page < 0:
		page = 0
	if ipage < 0:
		ipage = 0
	if page != "null":
		row = int(page)*(int(ipage)-1)
	else:
		row = "null"
        if server_id<0 or server_id=="" or server_id=="0":
                server_id="null"
        else:
                server_id = str(server_id)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"PGetServerRoute\"(null,%s,%s,%s,%s,%s,%s,%s,%s);"%(filter_cond_arry[1],filter_cond_arry[2],filter_cond_arry[3],filter_cond_arry[4],filter_cond_arry[5],page,str(row),searchstring))
			curs.execute("select public.\"PGetServerRoute\"(null,%s,%s,%s,%s,%s,%s,%s,%s,%s);"%(filter_cond_arry[1],filter_cond_arry[2],filter_cond_arry[3],filter_cond_arry[4],filter_cond_arry[5],page,str(row),searchstring,server_id))
			conn.commit()
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@route_list.route('/save_route', methods=['GET','POST'])
def save_route():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	rid = request.form.get('z1')
	ipid = request.form.get('z2')
	gw = request.form.get('z3')
	naddr = request.form.get('z4')
	netmask = request.form.get('z5')
	route_type = request.form.get('z6')
	server_id = request.form.get('z7')
	session = request.form.get('a0')
	oper = request.form.get('o1')
	
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if rid == '':
		rid = 'null'
	else:
		rid = "%s" % rid
	if ipid == '':
		ipid = 'null'
	else:
		ipid = "%s" % ipid
	if gw == '':
		gw = 'null'
	else:
		if not checkip(gw):
			return "{\"Result\":false,\"ErrMsg\":\"网关地址格式错误\"}"
		gw = '"%s"' % gw
	if naddr == '':
		naddr = 'null'
	else:
		if not checkip(naddr):
			return "{\"Result\":false,\"ErrMsg\":\"下一跳转地址格式错误\"}"
		naddr = '"%s"' % naddr
	if netmask == '':
		netmask = 'null'
	else:
		if not checkip(netmask):
			return "{\"Result\":false,\"ErrMsg\":\"子网掩码格式错误\"}"
		netmask = '"%s"' % netmask
	if route_type != "net" and route_type != "default":
		return "{\"Result\":false,\"ErrMsg\":\"类型错误\"}"
	
	if check_role(userCode, module_name) == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	data = "E'{\"route_id\":"+rid+",\"ipv4_id\":"+ipid+",\"gw_addr\":"+gw+",\"next_addr\":"+naddr+",\"netmask\":"+netmask+",\"route_type\":\""+route_type+"\",\"server_id\":"+server_id+"}'"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			##如果是编辑 先删除之前的路由设置
			if rid != '0':
				curs.execute("update server_route set status=2 where route_id = %d;" % (int(rid)))
				# sql = "select public.\"PGetServerRoute\"(%d,null,null,null,null,null,null,null,null);" %(int(rid))
				# curs.execute(sql)
				# result = curs.fetchall()[0][0]
				# export_json_all = json.loads(result)
				# export_json = export_json_all['data'][0]
				# export_json['route_id'] = 0
				# curs.execute("select public.\"PSaveServerRoute\"(%s);"%(data))
				# results1 = curs.fetchall()[0][0].encode('utf-8')
				# curs.execute("update server_route set status=3 where route_id = %d;" % (int(json.loads(results1)['route_id'])))
				'''
				route_strtmp = '[route%s]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\n' %(rid,route_type1,naddr1,netmask1,gw1,netdev_name)
				task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = del\n' + route_strtmp
				#debug(task_content)
				ss = task_client.task_send(str(server_id), task_content)
				if ss == False:
					msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
					if not system_log(userCode,oper,msg,module):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
				'''
			
			###	
				
			curs.execute("select public.\"PSaveServerRoute\"(%s);"%(data))
			results = curs.fetchall()[0][0].encode('utf-8')
			if 'false' in results:
				return results
			curs.execute("update server_route set status=3 where route_id = %d;" % (int(json.loads(results)['route_id'])))
			'''		
			###下发任务
			results_json = json.loads(results)
			if results_json['Result'] == True:
				route_id = results_json['route_id']
				sql = "select a.netdev_name from server_ipv4 a join  server_route b on b.ipv4_id = a.ipv4_id  where b.route_id = %d;" %(route_id)
				curs.execute(sql)
				#debug(sql)
				result_servers = curs.fetchall()
				netdev_name = result_servers[0][0]	
				route_type = '-net' if route_type=='net' else route_type
				naddr = 'None' if naddr =="null" else naddr
				netmask = 'None' if netmask =="null" else netmask
				route_strtmp = '[route%d]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\n' %(route_id,route_type,naddr,netmask,gw,netdev_name)
				task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = add\n' + route_strtmp
				#debug(task_content)
				ss = task_client.task_send(str(server_id), task_content)
				if ss == False:
					msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
					if not system_log(userCode,oper,msg,module):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
				conn.commit();	
			else:
				msg = results_json['ErrMsg']
				if not system_log(userCode,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			'''
			if rid == '0':
				curs.execute("update server_route set status=1 where route_id = %d;" % (int(json.loads(results)['route_id'])))
			if not system_log(userCode,oper,"成功",module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			conn.commit()
			return results
	except pyodbc.Error,e:
		msg = "数据库连接异常(%d): %s"% (sys._getframe().f_lineno, ErrorEncode(e.args[1]))
		if not system_log(userCode,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_route + 3, ErrorEncode(e.args[1]))

@route_list.route('/select_route_all', methods=['GET','POST'])
def select_route_all():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	routeid = request.form.get('z1')
	#type = request.form.get('z2')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if routeid != '-1':
				curs.execute("select public.\"PGetServerRoute\"(%d,null,null,null,null,null,null,null);"%(int(routeid)))
			else:
				curs.execute("select public.\"PGetServerRoute\"(null,null,null,null,null,null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (sys._getframe().f_lineno, ErrorEncode(e.args[1]))

@route_list.route('/delete_route', methods=['GET','POST'])
def delete_route():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	type = request.form.get('z10')
	id = request.form.get('z9')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	oper ="删除路由："
  	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
	if check_role(userCode, module_name) == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if (type == '1'):
				id_array = id[1:-1].split(',')
				for id in id_array:
					sql = "select server_id from server_ipv4 where ipv4_id in (select ipv4_id from server_route where route_id = %s);" % id
					curs.execute(sql)
					result_servers = curs.fetchall()				
					server_id =  result_servers[0][0]
					
					sql = "select b.route_id,b.route_type,b.next_addr,b.netmask ,b.gw_addr,a.netdev_name from server_ipv4 a join  server_route b on b.ipv4_id = a.ipv4_id  where b.route_id = %s;" %(id)
					curs.execute(sql)
					#debug(sql)
					result_server = curs.fetchall()[0]
					route_id =  result_server[0]
					route_type = '-net' if result_server[1].encode('utf-8')=='net' else result_server[1].encode('utf-8')
					next_addr = 'None' if result_server[2] ==None else result_server[2].encode('utf-8')
					netmask = 'None' if result_server[3] ==None else result_server[3].encode('utf-8')
					gw_addr = result_server[4].encode('utf-8')
					netdev_name = result_server[5].encode('utf-8')
					oper += netdev_name +"，"
					'''
					route_strtmp = '[route%d]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\n' %(route_id,route_type,next_addr,netmask,gw_addr,netdev_name)
					
					task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = del\n' + route_strtmp
					ss = task_client.task_send(str(server_id), task_content)
					#debug(task_content)
					if ss == False:
						oper = oper[:-3] ###中文 逗号 占三个字符
						msg = "系统异常: %s(%d)"%(task_client.err_msg,sys._getframe().f_lineno)
						if not system_log(userCode,oper,msg,module):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
					'''

					curs.execute("update server_route set status=2 where route_id = %d;" % (int(id)))
					# results = curs.fetchall()[0][0].encode('utf-8')
					# if json.loads(results)['Result'] == False:
					# 	oper = oper[:-3] ###中文 逗号 占三个字符
					# 	msg = json.loads(results)['ErrMsg']
					# 	if not system_log(userCode,oper,msg,module):
					# 		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					# 	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(json.loads(results)['ErrMsg'],sys._getframe().f_lineno)
				conn.commit()
				oper = oper[:-3] ###中文 逗号 占三个字符
				if not system_log(userCode,oper,"成功",module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return results 
			else:
				##下发任务
				sql = "select server_id from server_ipv4 where ipv4_id in (select ipv4_id from server_route where route_id = %s);" % id
				curs.execute(sql)
				result_server = curs.fetchall()				
				server_id =  result_server[0][0]
				
				sql = "select b.route_id,b.route_type,b.next_addr,b.netmask ,b.gw_addr,a.netdev_name from server_ipv4 a join  server_route b on b.ipv4_id = a.ipv4_id  where b.route_id = %s;" %(id)
				curs.execute(sql)
				result_server = curs.fetchall()[0]
				route_id =  result_server[0]
				route_type = '-net' if result_server[1].encode('utf-8')=='net' else result_server[1].encode('utf-8')
				next_addr = 'None' if result_server[2] ==None else result_server[2].encode('utf-8')
				netmask = 'None' if result_server[3] ==None else result_server[3].encode('utf-8')
				gw_addr = result_server[4].encode('utf-8')
				netdev_name = result_server[5].encode('utf-8')
				oper +=netdev_name
				'''
				route_strtmp = '[route%d]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\n' %(route_id,route_type,next_addr,netmask,gw_addr,netdev_name)
				task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = del\n' + route_strtmp
				ss = task_client.task_send(str(server_id), task_content)
				#debug(task_content)
				if ss == False:
					if not system_log(userCode,oper,"成功",module):
						return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
					return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)			
				'''
				curs.execute("update server_route set status=2 where route_id = %d;" % (int(id)))
				
				# results = curs.fetchall()[0][0].encode('utf-8')
				# if json.loads(results)['Result'] == False:
				# 	msg = json.loads(results)['ErrMsg']
				# 	if not system_log(userCode,oper,msg,module):
				# 		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				# 	return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(json.loads(results)['ErrMsg'],sys._getframe().f_lineno)
				# else:
				conn.commit()
				if not system_log(userCode,oper,"成功",module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_route + 3, ErrorEncode(e.args[1]))

		
