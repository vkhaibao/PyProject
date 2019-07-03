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
from logbase import task_client
from logbase import defines
from index import PGetPermissions
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
export_list = Blueprint('export_list',__name__)
module = "系统管理>网络设置"
SIZE_PAGE = 20
def debug(c):
	return 0
	path = "/var/tmp/debug_ccp.txt"
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
#创建 or 编辑
@export_list.route('/add_export',methods=['GET', 'POST'])
def add_export():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	oper = request.form.get('o1')
	_export = request.form.get('a1')
	_export=str(_export)
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
		
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(_export);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveServerIPV4(jsondata)
			sql="select public.\"PSaveServerIPV4\"(E'%s');" %(MySQLdb.escape_string(_export).decode("utf-8"))
			debug(str(_export))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			if 'false' in result:
				msg = json.loads(result)['ErrMsg']
				if not system_log(system_user,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			
			'''
			{
				"ipv4_id": 1,    
				"server_id": 1,
				"is_bond": 0,       --设备类型，0-Ether,1-Bond
				"netdev_id": 1,        
				"netdev_clas": 0,    --地址类型，0-物理地址，1-虚拟地址，2-Vlan
				"netdev_name": "eth0",
				"ip_addr": "192.168.0.160",
				"mask_addr": "255.255.255.0",       
				"memo": null        
			}
			'''
			conn.commit()
			
			##下发任务 
			debug(str(_export))
			net_json = json.loads(_export);
			debug(str(net_json));
			if(net_json['ipv4_id'] == 0):
				mod='add';
				sql = "update server_ipv4 set status=1 where ipv4_id = %d;" % (int(json.loads(result)['ipv4_id']))
			else:
				mod='edit';
				sql = "update server_ipv4 set status=3 where ipv4_id = %d;" % (int(net_json['ipv4_id']))
			curs.execute(sql)
			conn.commit()
			'''
			content1 = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=%s\n" %(mod)
			content = "[%s]\ntype=%d\naddr=%s\nmask=%s\n" %(net_json['netdev_name'],net_json['netdev_clas'],net_json['ip_addr'],net_json['mask_addr'])
			#ss = task_client.task_send(str(net_json['server_id']), content)
			#ss= True;
			debug(content);
			#if ss == False:
				#msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
				#if not system_log(system_user,oper,msg,module):
					#return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				#return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			route_strtmp = '';
			if mod =='edit':
				route_strtmp = 'gwaddr =\nnetdev =\n'
				###获取默认路由信息
				sql='select b."gw_addr",b."route_id",b."netmask",b."next_addr" from public."server_route" b where b."route_type"=\'default\' and b."ipv4_id" =%d ;' %(net_json['ipv4_id'])
				curs.execute(sql)
				result1 = curs.fetchall()
				if result1:
					gw_addr = result1[0][0]
					route_strtmp = 'gwaddr = %s\nnetdev = %s\n' %(gw_addr,net_json['netdev_name'])	
			ss = task_client.task_send(str(net_json['server_id']), content1 + route_strtmp +content)
			if ss == False:
				msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
				if not system_log(userCode,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			'''
			if not system_log(system_user,oper,"成功",module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result  
	except pyodbc.Error,e:
		msg = "系统异常(%d)" %(sys._getframe().f_lineno)
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	

#跳转至网口设置
@export_list.route('/export_show',methods=['GET','POST'])
def export_show():
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
	_power_mode = 1;
	for one in _power_json:
		if one['SystemMenuId'] == 6:
			_power_mode = one['Mode']
	'''
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select public.\"PGetDNSConfig\"();"
			debug(sql)
			curs.execute(sql)
			data = curs.fetchall()[0][0]
			if data :
				DNSIP = json.loads(data)['DNSIP'];
				DNSConfigId = json.loads(data)['DNSConfigId'];
			else:
				DNSIP='';
				DNSConfigId =0;

			#{"DNSConfigId": 1,"DNSIP": "192.168.0.0,192.168.0.1"} 

	except pyodbc.Error,e:
			error_msg = "系统繁忙(%d)" %(sys._getframe().f_lineno)
	'''
	return render_template('export_list.html',se=sess,paging="1",search_typeall="",e=':',error_msg=error_msg,_power_mode=_power_mode)
	return render_template('export_list.html',se=sess,paging="1",search_typeall="",e=':',error_msg=error_msg,_power_mode=_power_mode,DNSIP=DNSIP,DNSConfigId=DNSConfigId)
#1创建 2编辑 3列表
@export_list.route('/export_handle',methods=['GET','POST'])
def export_handle():
	if request.method == "GET":
		tasktype = request.args.get("tasktype")
		export_d = request.args.get("export_d")
		paging = request.args.get("paging")
		search_typeall = request.args.get("search_typeall")
		e = request.args.get("e")
		se=request.args.get('se')
		title_flag =  request.args.get('title_flag')
	else:
		tasktype = request.form.get("tasktype")
		export_d = request.form.get("export_d")
		paging = request.form.get("paging")
		search_typeall = request.form.get("search_typeall")
		e = request.form.get("e")
		se=request.form.get('se')
	if se<0:
		se=''
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or tasktype == "2":
		t = "export_add.html"
	if tasktype == "3":
		t = "export_list.html"
		export_d="0"
	if title_flag < 0:
		title_flag = "0"	
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
	
	return render_template(t,tasktype=tasktype,export_d=export_d,paging=paging,search_typeall=search_typeall,e=e,se=se,error_msg=error_msg,_power_mode=_power_mode,title_flag=title_flag)
#获取网口
@export_list.route('/get_ether_list',methods=['GET', 'POST'])
def get_ether_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	server_id = request.form.get('a1')
	if server_id<0 or server_id=="" or server_id=="0":
		server_id="null"
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetServerEther(serverid)
			sql="select public.\"PGetServerEther\"(%s);"%(server_id)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	
#获取服务器
@export_list.route('/get_serverglobal_list',methods=['GET', 'POST'])
def get_serverglobal_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetServerGlobal()
			'''
			{
				"serverid": ,       		--搜索条件，id
				"searchstring":,         	--模糊搜索条件，搜索ip、type、cpu
				"limitrow":10,              --返回多少条记录
				"offsetrow":0               --返回记录前忽略多少条记录 
			}
			'''
			
			sql="select public.\"PGetServerGlobal\"('{}');"
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常：%s(%d)\"}" %(ErrorEncode(str(e.args[1])),sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索
@export_list.route('/get_export_list',methods=['GET', 'POST'])
def get_export_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	export_d = request.form.get('a1')
	server_id =request.form.get('a5')
	netdev_name = ""
	ip_addr=""
	mask_addr=""
	memo=""
	if export_d<0 or export_d=="" or export_d=="0":
		export_d="null"
	if server_id<0 or server_id=="" or server_id=="0":
		server_id="null"
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	searchstring=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="netdev_name":
			netdev_name=netdev_name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ip_addr":
			ip_addr=ip_addr+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="mask_addr":
			mask_addr=mask_addr+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="memo":
			memo=memo+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="0":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"	
	if netdev_name=="":
		netdev_name="null"
	else:
		netdev_name="E'%s'"%netdev_name[:-1]
	if ip_addr=="":
		ip_addr="null"
	else:
		ip_addr="E'%s'"%ip_addr[:-1]
	if mask_addr=="":
		mask_addr="null"
	else:
		mask_addr="E'%s'"%mask_addr[:-1]
	if memo=="":
		memo="null"
	else:
		memo="E'%s'"%memo[:-1]
	searchconn={}
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	searchconn['searchstring']=searchstring
	searchconn=json.dumps(searchconn)
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	netdev_name=netdev_name.replace("\\\\","\\\\\\\\")
	netdev_name=netdev_name.replace(".","\\\\.")
	netdev_name=netdev_name.replace("?","\\\\?")
	netdev_name=netdev_name.replace("+","\\\\+")
	netdev_name=netdev_name.replace("(","\\\\(")
	netdev_name=netdev_name.replace("*","\\\\*")
	netdev_name=netdev_name.replace("[","\\\\[")
	ip_addr=ip_addr.replace("\\\\","\\\\\\\\")
	ip_addr=ip_addr.replace(".","\\\\.")
	ip_addr=ip_addr.replace("?","\\\\?")
	ip_addr=ip_addr.replace("+","\\\\+")
	ip_addr=ip_addr.replace("(","\\\\(")
	ip_addr=ip_addr.replace("*","\\\\*")
	ip_addr=ip_addr.replace("[","\\\\[")
	mask_addr=mask_addr.replace("\\\\","\\\\\\\\")
	mask_addr=mask_addr.replace(".","\\\\.")
	mask_addr=mask_addr.replace("?","\\\\?")
	mask_addr=mask_addr.replace("+","\\\\+")
	mask_addr=mask_addr.replace("(","\\\\(")
	mask_addr=mask_addr.replace("*","\\\\*")
	mask_addr=mask_addr.replace("[","\\\\[")
	memo=memo.replace("\\\\","\\\\\\\\")
	memo=memo.replace(".","\\\\.")
	memo=memo.replace("?","\\\\?")
	memo=memo.replace("+","\\\\+")
	memo=memo.replace("(","\\\\(")
	memo=memo.replace("*","\\\\*")
	memo=memo.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetServerIPV4(ipv4id,netdevname,ipaddr,maskaddr,description,serverid,limitrow,offsetrow)
			sql="select public.\"PGetServerIPV4\"(%s,%s,%s,%s,%s,%s,%s,%s,false,E'%s');"% (export_d,netdev_name,ip_addr,mask_addr,memo,server_id,num,paging,searchconn)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)

#保存LoadBalance
@export_list.route('/save_LoadBalance',methods=['GET','POST'])
def save_LoadBalance():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	LoadBalanceip=request.form.get('a1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	g_cluster_type = common.get_server_cluster_type();
	if g_cluster_type!='gluster':
		return "{\"Result\":true}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select * from public."LoadBalance";'
			curs.execute(sql)
			results = curs.fetchall()
			if len(results)==0:
				sql='INSERT INTO public."LoadBalance" ("IP") VALUES (\'%s\');'%(LoadBalanceip)
				curs.execute(sql)
				conn.commit()
			elif len(results)==1:
				if LoadBalanceip!=results[0][1]:
					sql='UPDATE public."LoadBalance" SET "IP" = \'%s\' WHERE "Id" = %s;'%(LoadBalanceip,results[0][0])
					curs.execute(sql)
					conn.commit()
			else:
				sql='DELETE FROM public."LoadBalance" WHERE "Id" != %s;'%results[0][0]
				curs.execute(sql)
				conn.commit()
				if LoadBalanceip!=results[0][1]:
					sql='UPDATE public."LoadBalance" SET "IP" = \'%s\' WHERE "Id" = %s;'%(LoadBalanceip,results[0][0])
					curs.execute(sql)
					conn.commit()
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)

#读取LoadBalance
@export_list.route('/get_LoadBalance',methods=['GET','POST'])
def get_LoadBalance():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	g_cluster_type = common.get_server_cluster_type();
	if g_cluster_type!='gluster':
		return "{\"Result\":true,\"info\":null,\"id\":null,\"type\":1}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select * from public."LoadBalance";'
			curs.execute(sql)
			results = curs.fetchall()
			if len(results)==0:
				return "{\"Result\":true,\"info\":null,\"id\":null,\"type\":2}"
			elif len(results)==1:
				return "{\"Result\":true,\"info\":\"%s\",\"id\":%s,\"type\":2}"%(results[0][1],results[0][0])
			else:
				sql='DELETE FROM public."LoadBalance" WHERE "Id" != %s;'%results[0][0]
				curs.execute(sql)
				conn.commit()
				return "{\"Result\":true,\"info\":\"%s\",\"id\":%s,\"type\":2}"%(results[0][1],results[0][0])
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)

#显示 or 分页 or 搜索 bond_list
@export_list.route('/get_bond_list',methods=['GET', 'POST'])
def get_bond_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	bond_d = request.form.get('a1')
	server_id = request.form.get('a5')
	bond_name = ""
	if bond_d<0 or bond_d=="" or bond_d=="0":
		bond_d="null"
	if server_id<0 or server_id=="" or server_id=="0":
		server_id="null"
	if sess < 0:
		sess = ""
	if search_typeall<0:
		search_typeall=""
	
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	searchstring=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="bond_name":
			bond_name=bond_name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="0":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			bond_name=bond_name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if bond_name=="":
		bond_name="null"
	else:
		bond_name="E'%s'"%bond_name[:-1]
	searchconn={}
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	searchconn['searchstring']=searchstring
	searchconn=json.dumps(searchconn)
	bond_name=bond_name.replace("\\\\","\\\\\\\\")
	bond_name=bond_name.replace(".","\\\\.")
	bond_name=bond_name.replace("?","\\\\?")
	bond_name=bond_name.replace("+","\\\\+")
	bond_name=bond_name.replace("(","\\\\(")
	bond_name=bond_name.replace("*","\\\\*")
	bond_name=bond_name.replace("[","\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetServerBond(bondid,bondname,serverid,limitrow,offsetrow)
			sql="select public.\"PGetServerBond\"(%s,%s,%s,%s,%s);"% (bond_d,bond_name,server_id,num,paging)
			#sql="select public.\"PGetServerBond\"(%s,%s,%s,%s,%s,'%s');"% (bond_d,bond_name,server_id,num,paging,searchconn)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	
#删除网口设置
@export_list.route('/del_export',methods=['GET', 'POST'])
def del_export():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	ids = id_str.split(',')
	oper ="删除网口："
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			for id in ids:
				id=int(id)
				
				sql = "select server_id,netdev_clas,netdev_name,ip_addr,mask_addr,is_bond,netdev_id from server_ipv4 where ipv4_id = %d;" % (id) 
				curs.execute(sql)
				sids = curs.fetchall()
				sid = sids[0][0]
				clas = sids[0][1]
				name = sids[0][2].encode('utf-8')
				ip = sids[0][3]
				mask = sids[0][4]
				isbond = sids[0][5]
				oper +=name+"，"
				#生效后 0:无处理 1:新增 2:删除
				sql = "update server_ipv4 set status=2 where ipv4_id = %d;" % (id)
				debug(sql)
				curs.execute(sql)
				sql = "update server_route set status=2 where ipv4_id = %d;" % (id)
				debug(sql)
				curs.execute(sql)
				# result = curs.fetchall()[0][0]
				# if "false" in result:
				# 	oper = oper[:-3] ###中文 逗号 占三个字符
				# 	msg = json.loads(result)['ErrMsg']
				# 	if not system_log(system_user,oper,msg,module):
				# 		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				# 	return result
			
			oper = oper[:-3]
			'''
			##发送任务
			content = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=del\n"
			content += "[%s]\ntype=%d\naddr=%s\nmask=%s\n" %(name,clas,ip,mask)
			ss = task_client.task_send(str(sid), content)
			#ss = True;
			debug(content)
			debug(oper)
			if ss == False:
				msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
				if not system_log(system_user,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			'''
			if not system_log(system_user,oper,"成功",module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			conn.commit()
			
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		msg = "系统异常(%d)" %(sys._getframe().f_lineno)
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	
#创建 or 编辑 bond
@export_list.route('/add_bond',methods=['GET', 'POST'])
def add_bond():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	bond = request.form.get('a1')
	oper = request.form.get('o1')
	bond=str(bond)
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			'''
			{
				"bond_id": 1,
				"server_id": 1,
				"bond_name": "bond0",
				"ether_id_1": 1,
				"ether_id_2": 2
			}
			'''
			bond_json = json.loads(bond);
			
			sql = "select ipv4_id from server_ipv4 where is_bond = 0 and (netdev_id = %d or netdev_id = %d);" %(bond_json['ether_id_1'],bond_json['ether_id_2'])
			curs.execute(sql)
			result_tmp = curs.fetchall()
			if result_tmp:
				try:
					ipv4_id1 = result_tmp[0][0]
				except:
					ipv4_id1 = None
				try:
					ipv4_id2 = result_tmp[1][0]
				except:
					ipv4_id2 = None
				if ipv4_id1 != None:
					sql = "select public.\"PDeleteServerIPV4\"(%d);" % (ipv4_id1)
					curs.execute(sql)
					result = curs.fetchall()[0][0]
					sql = "update server_route set status=2 where ipv4_id = %d;" % (ipv4_id1)
					debug(sql)
					curs.execute(sql)
					if "false" in result:
						msg = json.loads(result)['ErrMsg']
						if not system_log(system_user,oper,msg,module):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return result
				if ipv4_id2 != None:	
					sql = "select public.\"PDeleteServerIPV4\"(%d);" % (ipv4_id2)
					curs.execute(sql)
					result = curs.fetchall()[0][0]
					sql = "update server_route set status=2 where ipv4_id = %d;" % (ipv4_id1)
					debug(sql)
					curs.execute(sql)					
					if "false" in result:
						msg = json.loads(result)['ErrMsg']
						if not system_log(system_user,oper,msg,module):
							return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
						return result	
			
			# PSaveServerBond(jsondata)
			sql="select public.\"PSaveServerBond\"(E'%s');" %(MySQLdb.escape_string(bond).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			'''
			##发送任务
			sql = "select ether_name from server_ether where (ether_id = %d or ether_id = %d) and is_inner = 0;" %(bond_json['ether_id_1'],bond_json['ether_id_2'])
			curs.execute(sql)
			names = curs.fetchall()
			name1 = names[0][0]
			name2 = names[1][0]
			
			content_bond = "[global]\nclass = tasknetwork\ntype = config_bond\nop=add\n[%s]\nslave0=%s\nslave1=%s\n" %(bond_json['bond_name'],name1,name2)
			ss = task_client.task_send(str(bond_json['server_id']), content_bond)
			#ss= True;
			debug(content_bond)
			if ss == False:
				msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
				if not system_log(system_user,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			'''
			if json.loads(result)['Result'] == False:
				return results			
			sql = "update server_bond set status=1 where bond_id = %d;" % (int(json.loads(result)['bond_id']))
			curs.execute(sql)
			conn.commit()
			if not system_log(system_user,oper,'成功',module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	
#删除bond
@export_list.route('/del_bond',methods=['GET', 'POST'])
def del_bond():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	ids = id_str.split(',')
	oper = "删除Bond："
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			for id in ids:
				id=int(id)
				
				sql = "select ipv4_id,server_id,netdev_clas,netdev_name,ip_addr,mask_addr,is_bond,netdev_id from server_ipv4 where is_bond = 1 and netdev_id = %d;" %(int(id))
				curs.execute(sql)
				ret = curs.fetchall()
				if ret:
					result = ret[0]
					ipv4_id = result[0]
					server_id = result[1]
					netdev_clas = result[2]
					ipv4_name = result[3].encode('utf-8')
					s_id = result[1]
					ipv4_clas = result[2]
					ipv4_ip = result[4]
					ipv4_mask = result[5]
					netdev_id = result[7]
					_export = {
						"ipv4_id": 0,
						"server_id": server_id,
						"is_bond": 1,
						"netdev_id": netdev_id,
						"netdev_clas": netdev_clas, 
						"netdev_name": ipv4_name,
						"ip_addr": ipv4_ip,
						"mask_addr": ipv4_mask,
						"memo": ""
					}	
					# sql="select public.\"PSaveServerIPV4\"('%s');" %(MySQLdb.escape_string(json.dumps(_export)).decode("utf-8"))
					# curs.execute(sql)
					# result1 = curs.fetchall()[0][0]
					# id_tmp = json.loads(result1)['ipv4_id']
					sql = "update server_ipv4 set status=2 where ipv4_id = %d;" % int(ipv4_id)
					try:
						curs.execute(sql)
					except pyodbc.Error,e:
						return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					sql = "update server_route set status=2 where ipv4_id = %d;" % int(ipv4_id)
					debug(sql)
					curs.execute(sql)	
					'''	
					content = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=del\n"
					ipv4_name = ipv4_name.replace("\\\\", "\\").replace("\\_","_" ).replace("\\%","%" ).replace("\\.",".").replace("\\:",":")
					content1 = "[%s]\ntype=%d\naddr=%s\nmask=%s\n" %(str(ipv4_name),int(ipv4_clas),str(ipv4_ip),str(ipv4_mask))
					content = content + content1
					ss = task_client.task_send(str(s_id), content)
					if ss == False:
						return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
					'''
				
				
			sql = "select server_id from server_bond where bond_id = %d;" % int(id)
			curs.execute(sql)
			server_id = curs.fetchall()[0][0]

			
			# PDeleteServerBond(bondid)
			sql = "select bond_name,ether_id_1,ether_id_2 from server_bond where bond_id = %d;" % (id)				
			curs.execute(sql)
			result = curs.fetchall()[0]
			name = result[0]
			e_1 = result[1]
			e_2= result[2]
			
			oper +=name +'，'
			
			sql = "select ether_name from server_ether where is_inner = 0 and ether_id = %d;" %(e_1)
			curs.execute(sql)
			result = curs.fetchall()[0]
			name1 = result[0]
			
			sql = "select ether_name from server_ether where is_inner = 0 and ether_id = %d;" %(e_2)
			curs.execute(sql)
			result = curs.fetchall()[0]
			name2 = result[0]
			
			sql = "update server_bond set status=2 where bond_id = %d;" % (id)
			
			curs.execute(sql)
			# result = curs.fetchall()[0][0]
			# if "false" in result:
			# 	oper = oper[:-3] ###中文 逗号 占三个字符
			# 	msg = json.loads(result)['ErrMsg']
			# 	if not system_log(system_user,oper,msg,module):
			# 		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			# 	return result
					
			
			oper =oper[:-3]
			'''
			content_bond = "[global]\nclass = tasknetwork\ntype = config_bond\nop=del\n[%s]\nslave0=%s\nslave1=%s\n" %(name,name1,name2)
			ss = task_client.task_send(str(server_id), content_bond)
			debug(content_bond)
			if ss == False:
				msg = "系统异常: %s(%d)" %(task_client.err_msg,sys._getframe().f_lineno)
				if not system_log(system_user,oper,msg,module):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			'''
			conn.commit()
			if not system_log(system_user,oper,"成功",module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)	
	return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)

#重启网络
@export_list.route('/restart_net',methods=['GET', 'POST'])
def restart_net():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	ser_id = request.form.get('a1')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（非法访问）\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙：（系统超时）\"}"
		sys.exit()
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:

			####Bond
			debug("Bond")
			sql="select public.\"PGetServerBond\"(null,null,null,null,null);"
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			bond_json_all = json.loads(result)
			debug(str(bond_json_all['data']))
			if bond_json_all['totalrow'] != 0:
				for i in bond_json_all['data']:
					if i['status'] == 2:#删除
						id = int(i['bond_id'])
						
						sql = "select ipv4_id,server_id,netdev_clas,netdev_name,ip_addr,mask_addr,is_bond,netdev_id from server_ipv4 where is_bond = 1 and netdev_id = %d;" %(int(id))
						curs.execute(sql)
						ret = curs.fetchall()
						if ret:
							result = ret[0]
							ipv4_id = result[0]
							ipv4_name = result[3].encode('utf-8')
							s_id = result[1]
							ipv4_clas = result[2]
							ipv4_ip = result[4]
							ipv4_mask = result[5]
							
							sql = "DELETE from server_ipv4 where ipv4_id = %d;" % ipv4_id
							try:
								curs.execute(sql)
							except pyodbc.Error,e:
								return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno)
							
							content = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=del\n"
							ipv4_name = ipv4_name.replace("\\\\", "\\").replace("\\_","_" ).replace("\\%","%" ).replace("\\.",".").replace("\\:",":")
							content1 = "[%s]\ntype=%d\naddr=%s\nmask=%s\ndata_id=%d\n" %(str(ipv4_name),int(ipv4_clas),str(ipv4_ip),str(ipv4_mask),int(ipv4_id))
							content = content + content1
							ss = task_client.task_send(str(s_id), content)
							if ss == False:
								return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
							
						sql = "select server_id from server_bond where bond_id = %d;" % int(id)
						curs.execute(sql)
						server_id = curs.fetchall()[0][0]

						# PDeleteServerBond(bondid)
						sql = "select bond_name,ether_id_1,ether_id_2 from server_bond where bond_id = %d;" % (id)				
						curs.execute(sql)
						result = curs.fetchall()[0]
						name = result[0]
						e_1 = result[1]
						e_2= result[2]
						
						sql = "select ether_name from server_ether where is_inner = 0 and ether_id = %d;" %(e_1)
						curs.execute(sql)
						result = curs.fetchall()[0]
						name1 = result[0]
						
						sql = "select ether_name from server_ether where is_inner = 0 and ether_id = %d;" %(e_2)
						curs.execute(sql)
						result = curs.fetchall()[0]
						name2 = result[0]

						content_bond = "[global]\nclass = tasknetwork\ntype = config_bond\nop=del\n[%s]\nslave0=%s\nslave1=%s\ndata_id=%d\n" %(name,name1,name2,id)
						ss = task_client.task_send(str(server_id), content_bond)
						debug(content_bond)
						if ss == False:
							return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
				for i in bond_json_all['data']:
					if i['status'] == 1:#新增
						name1 = i['ether_name_1']
						name2 = i['ether_name_2']
						
						content_bond = "[global]\nclass = tasknetwork\ntype = config_bond\nop=add\n[%s]\nslave0=%s\nslave1=%s\ndata_id=%d\n" %(i['bond_name'],name1,name2,int(i['bond_id']))
						ss = task_client.task_send(str(i['server_id']), content_bond)
						#ss= True;
						debug(content_bond)
						if ss == False:
							return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
					elif i['status'] == 3:#修改
						name1 = i['ether_name_1']
						name2 = i['ether_name_2']
						
						content_bond = "[global]\nclass = tasknetwork\ntype = config_bond\nop=add\n[%s]\nslave0=%s\nslave1=%s\ndata_id=%d\n" %(i['bond_name'],name1,name2,int(i['bond_id']))
						ss = task_client.task_send(str(i['server_id']), content_bond)
						#ss= True;
						debug(content_bond)
						if ss == False:
							return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			debug("Bond结束")
			####Bond结束

			#### 网络
			debug("网络")
			sql="select public.\"PGetServerIPV4\"(null,null,null,null,null,null,null,null);"
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			export_json_all = json.loads(result)
			debug(str(export_json_all['data']))
			if export_json_all['totalrow'] != 0:
				##先处理要删除的配置
				for i in export_json_all['data']:
					if i['status'] == 2:#删除		
						sql = "select netdev_id,server_id,netdev_clas,netdev_name,ip_addr,mask_addr,is_bond from server_ipv4 where is_bond = 1 and ipv4_id = %d;" %(int(i['ipv4_id']))
						curs.execute(sql)
						ret = curs.fetchall()
						if ret:
							result = ret[0]
							netdev_id = result[0]
							server_id = result[1]
							# PDeleteServerBond(bondid)
							
							sql = "select bond_name,ether_id_1,ether_id_2 from server_bond where bond_id = %d;" % (netdev_id)				
							curs.execute(sql)
							result = curs.fetchall()[0]
							name = result[0]
							e_1 = result[1]
							e_2= result[2]
							
							sql = "select ether_name from server_ether where is_inner = 0 and ether_id = %d;" %(e_1)
							curs.execute(sql)
							result = curs.fetchall()[0]
							name1 = result[0]
							
							sql = "select ether_name from server_ether where is_inner = 0 and ether_id = %d;" %(e_2)
							curs.execute(sql)
							result = curs.fetchall()[0]
							name2 = result[0]

							content_bond = "[global]\nclass = tasknetwork\ntype = config_bond\nop=del\n[%s]\nslave0=%s\nslave1=%s\ndata_id=%d\n" %(name,name1,name2,netdev_id)
							ss = task_client.task_send(str(server_id), content_bond)
							debug(content_bond)
							if ss == False:
								return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
							
								
						##发送任务
						content = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=del\n"
						content += "[%s]\ntype=%d\naddr=%s\nmask=%s\ndata_id=%d\n" %(i['netdev_name'],i['netdev_clas'],i['ip_addr'],i['mask_addr'],i['ipv4_id'])
						ss = task_client.task_send(str(i['server_id']), content)
						#ss = True;
						debug(content)
						if ss == False:
							return "{\"Result\":false,\"info\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
				for i in export_json_all['data']:
					if i['status'] == 1:#新增
						mod='add';
						content1 = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=%s\n" %(mod)
						content = "[%s]\ntype=%d\naddr=%s\nmask=%s\ndata_id=%d\n" %(i['netdev_name'],i['netdev_clas'],i['ip_addr'],i['mask_addr'],i['ipv4_id'])
						route_strtmp = '';	
						debug(content)				
						ss = task_client.task_send(str(i['server_id']), content1 + route_strtmp +content)
						if ss == False:
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
					elif i['status'] == 3:#修改
						mod='edit';
						content1 = "[global]\nclass = tasknetwork\ntype = config_ipv4\nop=%s\n" %(mod)
						content = "[%s]\ntype=%d\naddr=%s\nmask=%s\ndata_id=%d\n" %(i['netdev_name'],i['netdev_clas'],i['ip_addr'],i['mask_addr'],i['ipv4_id'])
						route_strtmp = '';
						if mod =='edit':
							route_strtmp = 'gwaddr =\nnetdev =\n'
							###获取默认路由信息
							sql='select b."gw_addr",b."route_id",b."netmask",b."next_addr" from public."server_route" b where b."route_type"=\'default\' and b."ipv4_id" =%d ;' %(i['ipv4_id'])
							curs.execute(sql)
							result1 = curs.fetchall()
							if result1:
								gw_addr = result1[0][0]
								route_strtmp = 'gwaddr = %s\nnetdev = %s\n' %(gw_addr,i['netdev_name'])	
						debug(content)
						ss = task_client.task_send(str(i['server_id']), content1 + route_strtmp +content)
						if ss == False:
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			debug("网络结束")
			####网络结束

			####路由
			debug("路由")
			sql="select public.\"PGetServerRoute\"(null,null,null,null,null,null,null,null);"
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			route_json_all = json.loads(result)
			debug(str(route_json_all['data']))
			if route_json_all['totalrow'] != 0:
				for i in route_json_all['data']:
					if i['status'] == 2:#删除
						##发送任务
						route_strtmp = '[route%d]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\ndata_id=%d\n' %(i['route_id'],i['route_type'],i['next_addr'],i['netmask'],i['gw_addr'],i['netdev_name'],i['route_id'])
						task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = del\n' + route_strtmp
						ss = task_client.task_send(str(i['server_id']), task_content)
						debug(task_content)
						if ss == False:
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
				for i in route_json_all['data']:
					if i['status'] == 1:#新增
						route_id = i['route_id']
						sql = "select a.netdev_name from server_ipv4 a join  server_route b on b.ipv4_id = a.ipv4_id  where b.route_id = %d;" %(route_id)
						curs.execute(sql)
						#debug(sql)
						result_servers = curs.fetchall()
						i['netdev_name'] = result_servers[0][0]	
						route_strtmp = '[route%d]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\ndata_id=%d\n' %(route_id,i['route_type'],i['next_addr'],i['netmask'],i['gw_addr'],i['netdev_name'],i['route_id'])
						task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = add\n' + route_strtmp
						debug(task_content)
						ss = task_client.task_send(str(i['server_id']), task_content)
						if ss == False:
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
					elif i['status'] == 3:#修改
						route_id = i['route_id']
						sql = "select a.netdev_name from server_ipv4 a join  server_route b on b.ipv4_id = a.ipv4_id  where b.route_id = %d;" %(route_id)
						curs.execute(sql)
						#debug(sql)
						result_servers = curs.fetchall()
						i['netdev_name'] = result_servers[0][0]	
						route_strtmp = '[route%d]\nroutetype = %s\nnextaddr = %s\nmask = %s\ngwaddr = %s\nnetdev = %s\ndata_id=%d\n' %(route_id,i['route_type'],i['next_addr'],i['netmask'],i['gw_addr'],i['netdev_name'],i['route_id'])
						task_content = '[global]\nclass = tasknetwork\ntype = config_route\nop = add\n' + route_strtmp
						debug(task_content)
						ss = task_client.task_send(str(i['server_id']), task_content)
						if ss == False:
							return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
			debug("路由结束")
			####路由结束

		task_content = "[global]\nclass = taskLoadBalance\ntype=execute_setipvsadm\n"
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":true}"

			
