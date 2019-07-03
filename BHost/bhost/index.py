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
import cgi
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionOnline
from comm import CertGet
from comm import SessionCheckLocal

from comm import LogSet
from logbase import common
from logbase import paths
import base64
from ctypes import *

from htmlencode import parse_sess,check_role
from socket import *
import struct 

ERRNUM_MODULE_top = 1000

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
def debug(c):
	return 0
        path = "/var/tmp/debugsession.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
left_index = Blueprint('left_index',__name__)
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	LogSet(None, sqlconf, 6)
	
#HTMLEncode 
def HTMLEncode(str_1):
	newStr = "";
	if str_1 == "":
		return "";
	newStr = str_1.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;
	
#ErrorEncode 
def ErrorEncode(str_1):
	newStr = "";
	if str_1 == "":
		return "";
	newStr = str_1.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;		
	
@left_index.route('/index',methods=['GET', 'POST'])
def index():
	debug('index')
	reload(sys)
        sys.setdefaultencoding('utf-8')
	us = request.args.get('us')
	sess = request.args.get('se')
	tasktype = request.args.get('tasktype')
	gid = request.args.get('gid')
	keyword = request.args.get('keyword')
	index=request.args.get('i10')
	client_ip = request.remote_addr
	if index<0:
		index=request.form.get('i10')
		if index < 0:
			index='0'
	if gid< 0:
		gid = request.form.get('gid')
		if gid < 0:
			gid = "0"
	if tasktype< 0:
		tasktype = request.form.get('tasktype')
		if tasktype< 0:
			tasktype="0"
	if keyword< 0:
		keyword = request.form.get('keyword')
		if keyword< 0:
			keyword=""
	if tasktype and str(tasktype).isdigit() == False and tasktype.find('_') < 0:	
		return '',403	
	if gid and str(gid).isdigit() == False:
		return '',403	
	if index and str(index).isdigit() == False:
		return '',403		
	if	(len(keyword) > 2 and keyword.find('-') < 0) or(len(keyword) == 2 and keyword.find(']') < 0 ) :
		return '',403	
	
	if sess < 0:
                sess = request.form.get('se')
                if sess <0:
                        sess = ""
        if str(sess).isdigit() == True or str(sess) == "":
                pass
        else:
                return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"
	if us< 0 or us =='' or us =='None':
		us = request.form.get('us')
		if us< 0 or us =='' or us =='None':
			#us="0"
			(error,us,mac) = SessionCheck(sess,client_ip)
			debug(str(us))
			if error < 0:
				return "<html><head><body> <form name=\"frm\" action=\"\" method=\"post\"></form><script>top.location.href='/';</script></body></head></html>\n"
				#return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				#sys.exit()
			elif error > 0:
				if error == 2:
					return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
				else:
					return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
				sys.exit()
	p = re.compile(u'^[\w\.\-]+$')
        if p.match(us):
                pass
        else:
                return "{\"Result\":false,\"ErrMsg\":\"账号格式不正确\"}"
	'''
	if sess < 0:
		sess = request.form.get('se')
		if sess <0:
			sess = ""
	'''
	(error,uss,mac) = SessionCheck(sess,client_ip)
	if us != uss:
		return '',403
	
	hash  = request.args.get('ha');
	
	debug(str(request.referrer));
	if hash < 0 or hash =='':
		hash  = request.form.get('ha');
		if hash < 0 or hash =='':
			pass
		else:
			myCookie = request.cookies #获取所有cookie
			if myCookie.has_key('bhost'):
				hashsrc = StrMD5(myCookie['bhost']);
				if(hashsrc != hash):
					exit();
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();
				
	user_perm ="11111111"
	role_perm = "11111111"
	user_perm = int(user_perm,2)
	role_perm = int(role_perm,2)
	perm = user_perm & role_perm
	perm = bin(perm)[2:]
	a = 8-len(perm)
	str_tmp =""
	for i in range(0, a):
		str_tmp = str_tmp + "0"
	perm = str_tmp + perm 	
	perm ={'0':perm[0],'1':perm[1],'2':perm[2],'3':perm[3],'4':perm[4],'5':perm[5],'6':perm[6],'7':perm[7]}
	
	flag = 0
	LastLoginTime=''
        end=1
	if tasktype == '0':
		t = "left.html"
		LastLoginTime=request.args.get('a10')
		if LastLoginTime<0:
			LastLoginTime=request.form.get('a10')
			if LastLoginTime < 0:
				LastLoginTime=''
		flag = 1
	elif tasktype == '1':
		t = "monitor.html"
	elif tasktype == '1_1':
		t = "monitorWhite.html"		
	elif tasktype == '2':
		t = "audit.html"

	elif tasktype == '3':
		'''
		if us == "lh":
			t = "access_control.html"
		elif us=="xtc":
			t = "access_control_xtc.html"
		elif us=="ccp":
			t = "access_control_ccp.html"
		elif us=="zdp":
			t = "access_control_zdp.html"
		elif us=="rxl":
			t = "access_control_rxl.html"
		else:
		'''
		t = "access_control.html"
		
	elif tasktype == '4':
		t = "pwd_manage.html"
		
	elif tasktype == '5':
		t = "colony_list.html"	
		
	elif tasktype == '6':
		t = "system.html"
                server_id=common.get_server_id();
                try:
                        crt_t = CertGet(server_id)
                except Exception,e:
                        crt_t=None
                g_is_virtual=False
                if (False == os.path.exists(paths.ROOT_VOL_PATH)):
                        g_is_virtual=True
                if crt_t == None or crt_t[0] == None:
                        pass
                else:
                        end_time =int(crt_t[5])
                        now_time=int(time.time())
                        if end_time<now_time:
                                if int(crt_t[6]) != 1: ## 供货
                                        if g_is_virtual:
                                                pass
                                        else:
                                                end=0
                                else: ##试用
                                        pass
        elif tasktype == '7':
                t = "recent.html"
        elif tasktype == '8':
                t = "batch_run.html"
        elif tasktype == '9':
                t = "host_groupingFrame.html"
        elif tasktype == '10':
                t = "work_apply.html"
        elif tasktype == '11':
                t = "favoriteFrame.html"
        elif tasktype == '12':
                t = "host_grouping.html"
        elif tasktype == '13':
                t = "favorite.html"
	elif tasktype == '14':
		t = "batch_list.html"
	elif tasktype =='20':
		t='access_tools.html'
	elif tasktype == '15':
		t='connect_session.html'

	_power=PGetPermissions(us)
	_power=str(_power)
	_power_json = json.loads(_power);
	monitor_flag1 = 0
	monitor_flag2 = 0
	for one in _power_json:
 		if one['SubMenuId'] == 1:#数据监控
 			if one['Mode'] == 2:#管理
   				monitor_flag1 = 2
                        else:
 				monitor_flag1 = 1
  		elif one['SubMenuId'] == 7:#系统监控
	                if one['Mode'] == 2:#管理
	                         monitor_flag2 = 2
	                else:
	                         monitor_flag2 = 1
	_power_sonid = [];
	_power_mode_id = [];
	for one in _power_json:
		_power_sonid.append(one['SubMenuId']);
		if one['Mode'] == 2:
			_power_mode_id.append(one['SubMenuId'])
	
	if (True == os.path.exists(paths.ROOT_VOL_PATH)):
		flag_cloud = 0
	else:
		flag_cloud = 1
	
	myCookie = request.cookies #获取所有cookie
	hash = '';
	if myCookie.has_key('bhost'):
		hash = StrMD5(myCookie['bhost']);
	
	##获取 相关下载的文件
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
		
	if( str(index) !='' and str(index).isdigit() == False):
		return '',403 
	system_type = common.get_server_cluster_type();
	
	return render_template(t,end=end,us=us,se=sess,perm=perm,flag=flag,first=0,tasktype=tasktype,_power=_power,index=index,_power_sonid=_power_sonid,_power_mode_id=_power_mode_id,client_ip=client_ip,monitor_flag1=monitor_flag1,monitor_flag2=monitor_flag2,LastLoginTime=LastLoginTime,flag_cloud=flag_cloud,hash=hash,default_str=default_str,gid=gid,keyword=keyword,system_type=system_type,cip=request.remote_addr)
	#return render_template(t,us=us,se=sess,perm=perm,flag=flag,first=0,tasktype=tasktype,_power=_power,index=index)
	#return render_template(t,us=us,se=sess,perm=perm,flag=flag,first=0,tasktype=tasktype)
	
@left_index.route("/logout", methods=['GET', 'POST'])
def logout():
	#session.pop['username',None]
	return "<html><head><body> <form name=\"frm\" action=\"\" method=\"post\"></form><script>top.location.href='/';</script></body></head></html>\n" 

@left_index.route("/get_msg", methods=['GET', 'POST'])
def get_msg():
	sess = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,us,mac) = SessionCheckLocal(sess,client_ip);
	#(error,us,mac) = SessionCheck(sess,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常\"}"
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d): %d\"}" % (ERRNUM_MODULE_top + 2,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时\"}"

	error_1=SessionOnline(sess)

	if error_1 <0:
		return "{\"Result\":false,\"info\":\"系统异常\"}"
	elif error_1>0:
		return "{\"Result\":false,\"info\":\"系统超时\"}"
	
	return "{\"Result\":true,\"time\":\"%s\"}" %(str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
	
#@left_index.route("/PGetPermissions", methods=['GET', 'POST'])
def PGetPermissions(us):
        global ERRNUM_MODULE
        ERRNUM_MODULE = 3000
	#sess = request.form.get('a0')
        reload(sys)
        sys.setdefaultencoding('utf-8')
        #if sess < 0:
        #        sess = ""
        #client_ip = request.remote_addr
        #(error,us,mac) = SessionCheckLocal(sess,client_ip);
        #(error,us,mac) = SessionCheck(sess,client_ip);
        #if error < 0:
        #        return "{\"Result\":false,\"info\":\"系统异常(%d): %d\"}" %  (ERRNUM_MODULE_top + 1,error)
        #elif error > 0:
        #        if error == 2:
        #                return "{\"Result\":false,\"info\":\"非法访问(%d): %d\"}" % (ERRNUM_MODULE_top + 2,error)
        #        else:
        #                return "{\"Result\":false,\"info\":\"系统超时(%d): %d:%s\"}" % (ERRNUM_MODULE_top + 2,error,str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetPermissions\"(E'%s');" %(MySQLdb.escape_string(us))
			debug(str(sql))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			#debug('result:%s'%result)
			if result==None:
				result='[]'
			else:
				result_json = json.loads(result);
				json_list_mode1 = [];
				json_list_mode2 = [];
				json_list_mode = [];
				json_list_all = []
				result = []
				for one in result_json:
					if one['Mode'] == 2:
						json_list_mode2.append(one['SubMenuId'])
					if one['Mode'] == 1:
						json_list_mode1.append(one['SubMenuId'])
				for one in json_list_mode1:
					if one in json_list_mode2:
						json_list_mode.append(one)
				#json_list_mode = json_list_mode + json_list_mode2
				debug(str(json_list_mode))
				
				for one in result_json:
					if one['SubMenuId'] in json_list_mode and one['Mode'] == 1:
						#one['SubMenuId'] = -1
						pass
					else:
						json_list_all.append(one)
				result = json.dumps(json_list_all)
				#result = str(result_json)
	except pyodbc.Error,e:
		return "[]"
	return str(result)

#获取 协同信息  yt 0917
@left_index.route("/get_cowork_param", methods=['GET', 'POST'])
def get_cowork_param():
	sess = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,us,mac) = SessionCheckLocal(sess,client_ip);
	SessionId = request.form.get('z1')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"GetAuthObjectByLevel\"('%s','%s',null,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str))
			sql = 'select "HostAccessCfgId","UserCode","ServerIP","ProtocolName","ServerUser","ServerPort","ServiceName","ConnMode","ConnParam","ExePath","Pwd","ClientName","SSHType","RDPScreen","RDPClipboard","RDPDiskMap","RDPDiskMapList","LastAccessTime","ConnParamName","ConnModeName","AppRelease","AppChannel","ConnWay","ConnParamId" from private."HostAccessCfg" where "SessionId"=E\'%s\';' %(SessionId)
			debug(sql)
			curs.execute(sql);		
			results = curs.fetchall();
			result_list1 = ["HostAccessCfgId","UserCode","ServerIP","ProtocolName","ServerUser","ServerPort","ServiceName","ConnMode","ConnParam","ExePath","Pwd","ClientName","SSHType","RDPScreen","RDPClipboard","RDPDiskMap","RDPDiskMapList","LastAccessTime","ConnParamName","ConnModeName","AppRelease","AppChannel","ConnWay","ConnParamId"]
			
			dictionary = dict(zip(result_list1, results[0]))
			debug(str(dictionary))
			return json.dumps(dictionary)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_top + 3, ErrorEncode(e.args[1]))
		
@left_index.route("/base64_encode", methods=['GET', 'POST'])
def base64_encode():		
	cmdstr = request.form.get('a1')
	return base64.b64encode(cmdstr)
	
@left_index.route("/get_ClientPath", methods=['GET', 'POST'])
def get_ClientPath():	
	sess = request.form.get('a0')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,us,mac) = SessionCheckLocal(sess,client_ip);
	proto = request.form.get('a1')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#debug("select public.\"GetAuthObjectByLevel\"('%s','%s',null,null,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s);" %(usercode,client_ip,int(hgid),ip,hostservicename,proname,port,servicename,conntype,connparamvalue,account_name,accounttype,search_str))
			sql = 'select "ClientProgram","ClientName" from public."LocalClient"  where "ProtocolId" in (select "ProtocolId" from public."AccessProtocol" where "ProtocolName"=E\'%s\' and \"UserId\" in(select \"UserId\" from public."User" where "UserCode"=E\'%s\')) and \"ClientIP\"=E\'%s\' ;' %(proto,us,client_ip)
			debug(sql)
			curs.execute(sql);		
			results = curs.fetchall();
			if not results :
				sql = 'select "ClientProgram","ClientName" from public."LocalClient"  where "ProtocolId" in (select "ProtocolId" from public."AccessProtocol" where "ProtocolName"=E\'%s\' and \"UserId\" in(select \"UserId\" from public."User" where "UserCode"=E\'%s\')) and \"ClientIP\" is NULL  ;' %(proto,us)
				debug(sql)
				curs.execute(sql);		
				results = curs.fetchall();
				if not results :
					ClientProgram = '';
					ClientName ='';
				else:
					if results[0]== None:
						ClientProgram = '';
						ClientName ='';
					else:
						ClientProgram = results[0][0].decode('utf-8');
						ClientName = results[0][1].decode('utf-8')
			else:
				if results[0]== None:
					ClientProgram = '';
					ClientName ='';
				else:
					ClientProgram = results[0][0].decode('utf-8');
					ClientName = results[0][1].decode('utf-8')
					
			return "{\"Result\":true,\"ClientProgram\":\"%s\",\"ClientName\":\"%s\"}" % (ClientProgram, ClientName)
			
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE_top + 3, ErrorEncode(e.args[1]))
	
@left_index.route("/get_rc4encode", methods=['GET', 'POST'])
def get_rc4encode():	
	pW = request.form.get('a1')	
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	ret = lib.encrypt_pwd(pW,pwd_rc4)#执行函数
	return pwd_rc4.value #获取变量的值

@left_index.route("/GetNoAlert", methods=['GET', 'POST'])
def GetNoAlert():	
	sess = request.form.get('a0')
	us = request.form.get('a1')
	if sess < 0 or sess == '' or sess ==' ' or sess =='+':
		pass
	else:
		client_ip = request.remote_addr
		(error,us,mac) = SessionCheck(sess,client_ip)
	if us < 0 :
		us ='';
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select "UpdateNoAlert" from public."User" where "UserCode" =E\'%s\';' %(us)
			debug(sql)
			curs.execute(sql);		
			results = curs.fetchall();	
			if results == None:
				results = 1;
			else:
				if(results[0][0] == None):
					results[0][0] = 1;
			return "{\"Result\":true,\"info\":%d}" % (results[0][0])
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库异常(%d): %s\"}" % (ERRNUM_MODULE_top + 3, ErrorEncode(e.args[1]))
		
@left_index.route("/UpdateNoAlert", methods=['GET', 'POST'])
def UpdateNoAlert():	
	sess = request.form.get('a0')
	UpdateNoAlert = request.form.get('a1')
	us = request.form.get('a2')
	if sess < 0 or sess == '' or sess ==' ':
		pass
	else:
		client_ip = request.remote_addr
		(error,us,mac) = SessionCheck(sess,client_ip)		
	if us < 0 :
		us ='';	
	
	if  UpdateNoAlert < 0 or UpdateNoAlert =='':
		UpdateNoAlert = 1;
	else:
		UpdateNoAlert = int(UpdateNoAlert)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'UPDATE  public."User" set "UpdateNoAlert" =%d where "UserCode" =E\'%s\';' %(int(UpdateNoAlert),us)
			debug(sql)
			curs.execute(sql);		
			return "{\"Result\":true}" 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库异常(%d): %s\"}" % (ERRNUM_MODULE_top + 3, ErrorEncode(e.args[1]))
		
@left_index.route("/terminal", methods=['GET', 'POST'])
def terminal():	
	session = request.form.get('a0')
	cmd = request.form.get('c1')
	md5_str = request.form.get('m1')
	count = int(request.form.get('co'))
	
	md5_json = StrMD5(cmd);##python中的json的MD5
	if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面cmd数据的md5值
		return '{"Result":false,"info":"","count":%d,"error_msg":"拒绝访问"}'%(count)
	cmd = base64.b64decode(cmd);
	
	HOST ='127.0.0.1';
	PORT = 8077;
	BUFFSIZE=65535;
	ADDR = (HOST,PORT);
	tcpClient = socket(AF_INET,SOCK_STREAM);
	try:
		tcpClient.connect(ADDR);
	except:
		return '{"Result":false,"info":"","count":%d,"error_msg":"连接失败"}'%(count)
	if count == 0:
		fmt = "ii%ds" %(len(cmd));
		data = struct.pack(fmt, count, len(cmd),cmd);
	else:
		fmt = "i"
		data = struct.pack(fmt, count);
	tcpClient.send(data);
	
	data = tcpClient.recv(BUFFSIZE);
	tcpClient.close();
	if len(data) == 4:
		c = struct.unpack('i', data);
		if c[0] > 1:
			return '{"Result":false,"info":"","count":%d,"error_msg":"暂不支持该命令"}'%(count)
		else:
			return '{"Result":false,"info":"","count":%d,"error_msg":"系统异常"}'%(count)
	elif len(data) < 8:
		return '{"Result":false,"info":"","count":%d,"error_msg":"系统异常"}'%(count)
	json_data={"count":0,"state":-1,"msg":""};
	if count  == 0:
		c = struct.unpack("2i", data)
		json_data["state"] = c[0];
		json_data["count"] = c[1];
	else:
		json_data["count"] = count;
		fmt = "2i%ds" %(len(data)-8);
		c = struct.unpack(fmt, data);
		json_data["state"] = c[0];
		len_data = c[1];
		json_data["msg"] = c[2].decode('utf-8');
		
	if 	json_data["state"] == 0:
		return '{"Result":true,"info":"%s","count":%d,"error_msg":""}'%(base64.b64encode(json_data['msg']),json_data['count'])
	elif json_data["state"] == 1:
		return '{"Result":true,"info":"end","count":%d,"error_msg":"%s"}'%(json_data['count'],base64.b64encode(json_data['msg']))
	else:
		return '{"Result":false,"info":"%s","count":%d,"error_msg":"暂不支持该命令"}'%(base64.b64encode(json_data['msg']),json_data['count'])
	
	
	













	
		
		
		

		