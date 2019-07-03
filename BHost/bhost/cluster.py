#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import MySQLdb
import json
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionClean
from comm import GetGlsterMaster
from htmlencode import parse_sess
import redis
import cgi
from werkzeug.utils import secure_filename
import random
import string
import hmac, base64, struct, hashlib, time
import re
import socket
from logbase import common,defines,task_client,paths,net
import urllib2
import ssl

from flask import Flask,Blueprint,request,session,render_template,make_response
from jinja2 import Environment,FileSystemLoader


ERRNUM_MODULE = 1000
UPLOAD_FOLDER='/usr/storage/.system/upload/'
reload(sys)
sys.setdefaultencoding('utf-8')
module = '用户登录'

cluster_path = "/var/run/bhcluster.cluster"		
cluster_info_path = "/var/tmp/bhcluster.cluster"
db_info_path = "/var/tmp/bhcluster.db"	
db_path = "/var/run/bhcluster.db"
socket_path = '/var/tunnel/bhcluster.sock';
'''
SIGUSR_STOP = 29	
SIGUSR_UP = 30
SIGUSR_INFO = 31
DB_MASTER_SIGUSR_UP = 29
DB_BACK_SIGUSR_UP = 30
DB_SIGUSR_STOP = 31
'''
SIGUSR_STOP = '1'	
SIGUSR_UP = '2'
SIGUSR_INFO = '3'
DB_MASTER_SIGUSR_UP = '4'
DB_BACK_SIGUSR_UP = '5'
DB_SIGUSR_STOP = '6'
S_SIGUSR_STOP = '7'

def debug(c):
	return 0; 
	path = "/var/tmp/debugp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
cluster = Blueprint('cluster',__name__)

#账号
def checkaccount(account):
	p = re.compile(u'^[\w\.\-\u4E00-\u9FA5]+$')
	if p.match(account.decode('utf-8')):
		return True
	else:
		return False
		
@cluster.route("/cluster", methods=['GET', 'POST'])
def glusterlogin():
	ran = StrMD5('safetybase');
	res = make_response(render_template('clusterlogin.html',hash =StrMD5(ran)));
	res.set_cookie('bhost',ran,None,None,'/');
	return res

@cluster.route("/gllogin", methods=['GET', 'POST'])
def gllogin():
	debug(str("Enter gllogin"))
	if request.method == 'POST':
		username = request.form.get('a0')
		password = request.form.get('a1')
		password = base64.b64decode(password)
		if username == "super":
			if password == "clustermanager":
				return "{\"Result\":true,\"LoginMsg\":\"用户验证通过\"}"
		return "{\"Result\":false, \"LoginMsg\":\"账号或密码错误\"}"
		
@cluster.route("/cluster_logout", methods=['GET', 'POST'])
def cluster_logout():
	#session.pop['username',None]
	#SessionClean
	session = request.form.get('a0')
	SessionClean(session);
	return "<html><head><body> <form name=\"frm\" action=\"\" method=\"post\"></form><script>top.location.href='/bhost/cluster';</script></body></head></html>\n"
	
@cluster.route("/login_link_cluster", methods=['GET', 'POST'])
def login_link_cluster():
	uCode = request.form.get('uCode');
	if uCode < 0:
		uCode = request.args.get('uCode')
	debug(uCode)
	sess = request.form.get('a0')
	if sess < 0 :
		sess = request.args.get('a0')
	sess = filter(str.isdigit, str(sess))
	uCode = cgi.escape(uCode.lower())
	
	hash  = request.form.get('ha');
	if hash < 0 :
			hash = request.args.get('ha')
	if checkaccount(uCode) == False:
		return '',403
		
	
	if hash < 0 or hash =='':
		pass
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();
	return "<html><head><body> <form name=\"frm\" action=\"/bhost/index\" method=\"post\"><input type=\"hidden\" name=\"se\" id=\"se\" value=\"\"></form><script> document.frm.se.value='%s';document.frm.action = \"/bhost/index_cluster\";document.frm.submit();</script></body></head></html>\n" % (sess)

@cluster.route("/index_cluster", methods=['GET', 'POST'])
def index_cluster():

	sess = request.args.get('se')
	if sess < 0:
		sess = request.form.get('se')
		if sess <0:
			sess = ""
	if str(sess).isdigit() == True or str(sess) == "":
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"
	

	hash  = request.args.get('ha');
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
	
	return render_template('left_cluster.html',se=sess,hash=hash,us='super')
	
@cluster.route("/cluster_info", methods=['GET', 'POST'])
def cluster_info():	
	sess = request.args.get('a0')
	client_ip = request.remote_addr
	is_master = common.is_server_master()
	server_id=common.get_server_id();
	cluster_type = common.get_server_cluster_type();
	
	server_list = '';
	ip = net.get_netdevice_ip('eth0');
	if not ip:
		ip = net.get_netdevice_ip('eth3');
		
	if cluster_type =='double':
		if server_id == '1':
			if is_master == True:
				server_list = '[{"server_id":1,"is_master":true,"ip":"%s"},{"server_id":2,"is_master":false,"ip":"2.2.2.2"}]' %(ip)
			else:
				server_list = '[{"server_id":1,"is_master":false,"ip":"%s"},{"server_id":2,"is_master":true,"ip":"2.2.2.2"}]'%(ip)
		else:
			if is_master == True:
				server_list = '[{"server_id":1,"is_master":false,"ip":"2.2.2.1"},{"server_id":2,"is_master":true,"ip":"%s"}]' %(ip)
			else:
				server_list = '[{"server_id":1,"is_master":true,"ip":"2.2.2.1"},{"server_id":2,"is_master":false,"ip":"%s"}]' %(ip)
	elif cluster_type =='gluster':
		server_id_list = ['1','2','3']
		ip_t = '';
		for s_id in server_id_list:
			if s_id =='1':
				ip_t = '2.2.2.1'
			if s_id =='2':
				ip_t = '2.2.2.2'
			if s_id =='3':
				ip_t = '2.2.2.3'
				
			if s_id =='1' and server_id =='1':
				ip_t = ip
			elif s_id =='2' and server_id =='2':
				ip_t = ip
			elif s_id =='3' and server_id =='3':
				ip_t = ip
				
			(error,GlsterMaster)=GetGlsterMaster(None, s_id, server=common.get_inner_master_ip(), listen=6379, dbcode=2)
			if GlsterMaster == s_id:			
				result_str = '{"server_id":%s,"is_master":true,"ip":"%s"},'  %(s_id,ip_t)
			else:
				result_str = '{"server_id":%s,"is_master":false,"ip":"%s"},' %(s_id,ip_t)
			server_list = server_list +result_str
		server_list = '[%s]' %(server_list[:-1])	
			
	
	return render_template('cluster_info.html',se=sess,us='super',server_id=server_id,is_master=is_master,cluster_type=cluster_type,server_list=server_list,ip=ip)
	
	
@cluster.route("/cluster_status", methods=['GET', 'POST'])
def cluster_status():		
	sess = request.form.get('a0')
	if str(sess).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"
	typ = request.form.get('t1') # 0>停用 1>启用
	if str(typ).isdigit() == False:
		return "{\"Result\":false,\"ErrMsg\":\"访问拒绝\"}"
	if typ == '0':
		sig = SIGUSR_STOP;
	else:
		sig = SIGUSR_UP;
	try:
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  
		sock.connect(socket_path)  
		len1 = sock.send(sig)
		if not len1: 
			return "{\"Result\":false,\"ErrMsg\":\"send error(%s)\"}" %(sig) 
	except:
		return "{\"Result\":false,\"ErrMsg\":\"服务器异常(%s)\"}" %(sig) 
		
	sock.close()	
	
	return "{\"Result\":true,\"ErrMsg\":\"\"}"
	
@cluster.route("/s_stop", methods=['GET', 'POST'])
def s_stop():		
	sess = request.form.get('a0')
	if str(sess).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"
		
	sig = S_SIGUSR_STOP;
	try:
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  
		sock.connect(socket_path)  
		len1 = sock.send(sig)
		if not len1: 
			return "{\"Result\":false,\"ErrMsg\":\"send error(%s)\"}" %(sig) 
	except:
		return "{\"Result\":false,\"ErrMsg\":\"服务器异常(%s)\"}" %(sig) 
		
	sock.close()	
	
	return "{\"Result\":true,\"ErrMsg\":\"\"}"
	
@cluster.route("/db_status_change", methods=['GET', 'POST'])
def db_status_change():		
	sess = request.form.get('a0')
	if str(sess).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"
	typ = request.form.get('t1') # 0>停用 1>启用
	if str(typ).isdigit() == False:
		return "{\"Result\":false,\"ErrMsg\":\"访问拒绝\"}"
		
	up_mode = request.form.get('u1') # 模式  备 1 主 2
	if str(up_mode).isdigit() == False:
		return "{\"Result\":false,\"ErrMsg\":\"访问拒绝\"}"
		
	if typ == '0':
		sig = DB_SIGUSR_STOP;
	else:
		if up_mode =='1':
			sig = DB_BACK_SIGUSR_UP;
		else:
			sig = DB_MASTER_SIGUSR_UP;
	try:		
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  
		sock.connect(socket_path)  
		len1 = sock.send(sig)
		if not len1: 
			return "{\"Result\":false,\"ErrMsg\":\"send error(%s)\"}" %(sig) 
	except:
		return "{\"Result\":false,\"ErrMsg\":\"服务器异常(%s)\"}" %(sig) 
		
	sock.close()
	
	return "{\"Result\":true,\"ErrMsg\":\"\"}"	
	
	
@cluster.route("/cluster_all", methods=['GET', 'POST'])
def cluster_all():		
	sess = request.form.get('a0')
	if str(sess).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"	
		
	## pacemakerd corosync   1个黄色 2个绿色 0个红色 
	command ='ps aux | grep pacemakerd';
	f = os.popen(command)
	pacemakerd = f.read().replace('grep pacemakerd','');
	debug(str(pacemakerd));
	f.close()
	status_online = 0;
	if len(pacemakerd.split('pacemakerd')) > 1:
		status_online = status_online + 1;
	
	
	
	command ='ps aux | grep corosync';
	f = os.popen(command)
	corosync = f.read().replace('grep corosync','');
	debug(str(corosync));
	f.close()
	if len(corosync.split('corosync')) > 1:
		status_online = status_online + 1;
	###数据库
	db_status_online = 0;
	command ='ps aux | grep postgres';
	f = os.popen(command)
	postgres = f.read().replace('grep postgres','');
	debug(str(postgres));
	f.close()
	if len(postgres.split('postgres')) > 1:
		db_status_online = db_status_online + 1; 

	return "{\"Result\":true,\"status_online\":%d,\"db_status_online\":%d}" %(status_online,db_status_online);	
	
@cluster.route("/cluster_status_info", methods=['GET', 'POST'])
def cluster_status_info():		
	try:
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  
		sock.connect(socket_path)  
		len1 = sock.send(SIGUSR_INFO)
		if not len1:
			return "{\"Result\":false,\"ErrMsg\":\"send error(%s)\"}" %(SIGUSR_INFO) 
	except:
		return "{\"Result\":false,\"ErrMsg\":\"获取服务器状态失败(%s)\"}" %(SIGUSR_INFO) 
	sock.close()
	
	i = 0;
	while(True):
		if i >= 30:
			crm_status = '';
			break;
		if os.path.exists(cluster_info_path) == True:
			fp = open(cluster_info_path,"r");
			if fp:
				crm_status = fp.read();
				debug(str(crm_status))
				fp.close();
				if len(str(crm_status)) == 0:
					i = i+1;
					time.sleep(0.5)
					continue;
			break;
		time.sleep(0.5)
		i = i+1;
	
	return "{\"Result\":true,\"crm_status\":\"%s\"}" %(crm_status.replace('\n',"\\n").replace('\t',"&nbsp;&nbsp;&nbsp;&nbsp;").replace('"','\\"'));

	
@cluster.route("/db_status_info", methods=['GET', 'POST'])
def db_status_info():		
	sess = request.form.get('a0')
	if str(sess).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"	
	
	db_status = '';
	if os.path.exists(db_info_path) == True:
		mtime = os.stat(db_info_path).st_mtime;
		while(True):
			if time.time()-mtime > 10:
				time.sleep(1);
				break;
				
		fp = open(db_info_path,"r");
		if fp:
			db_status = fp.read();
			fp.close();	
	return "{\"Result\":true,\"db_status\":\"%s\"}" %(db_status.replace('\n',"\\n").replace('\r',"\\n").replace('\t',"&nbsp;&nbsp;&nbsp;&nbsp;").replace('"','\\"').replace('^','').replace(b'\x1b','').replace(b'\x00',''));
	
@cluster.route("/refresh_cluster", methods=['GET', 'POST'])
def refresh_cluster():	
	sess = request.form.get('a0')
	if str(sess).isdigit() == True:
		pass
	else:
		return "{\"Result\":false,\"ErrMsg\":\"Session格式错误\"}"	
			
	typ = request.form.get('t1') # 0>停用 1>启用
	if str(typ).isdigit() == False:
		return "{\"Result\":false,\"ErrMsg\":\"访问拒绝\"}"
	
	uflag = request.form.get('u1') # 0>服务器 1>数据库
	if str(uflag).isdigit() == False:
		return "{\"Result\":false,\"ErrMsg\":\"访问拒绝\"}"
		
	succ_str = ''
	if(uflag == '0'):
		## pacemakerd corosync   1个黄色 2个绿色 0个红色 
		command ='ps aux | grep pacemakerd';
		f = os.popen(command)
		pacemakerd = f.read().replace('grep pacemakerd','');
		debug(str(pacemakerd));
		f.close()
		status_online = 0;
		if len(pacemakerd.split('pacemakerd')) > 1:
			status_online = status_online + 1;
			
		command ='ps aux | grep corosync';
		f = os.popen(command)
		corosync = f.read().replace('grep corosync','');
		debug(str(corosync));
		f.close()
		if len(corosync.split('corosync')) > 1:
			status_online = status_online + 1;
	else:
		###数据库
		status_online = 0;
		command ='ps aux | grep postgres';
		f = os.popen(command)
		postgres = f.read().replace('grep postgres','');
		debug(str(postgres));
		f.close()
		if len(postgres.split('postgres')) > 1:
			status_online = status_online + 1; 
			
	
	if typ == '0':# 0>停用
		if status_online > 0:
			succ_str = 'fail'
		else:
			succ_str = 'succ'
	else:
		if status_online > 0:
			succ_str = 'succ'
		else:
			succ_str = 'fail'
	

	return "{\"Result\":true,\"info\":\"%s\"}" %(succ_str);	
	
@cluster.route("/get_ip", methods=['GET', 'POST'])
def get_ip():
	ip = net.get_netdevice_ip('eth0');
	if not ip:
		ip = net.get_netdevice_ip('eth3');
	return ip;
	
@cluster.route("/get_net_ip", methods=['GET', 'POST'])
def get_net_ip():	
	ip = request.form.get('i')
	url = 'https://%s/bhost/get_ip' %(ip)
	content ='';
	try:
		ssl._create_default_https_context = ssl._create_unverified_context
		req = urllib2.urlopen(url, '')
		content = req.read()
	except Exception,e:
		print e
	
	return content;
	
	
	
	
