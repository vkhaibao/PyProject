#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import pyodbc
import MySQLdb
import time
import json
import tempfile
import cgi
import datetime
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionClean
from htmlencode import parse_sess
import redis
from werkzeug.utils import secure_filename
import random
import string
import hmac, base64, struct, hashlib, time
from ctypes import *
import re
from logbase import common,defines,task_client,paths
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from comm import CertGet
from flask import Flask ,render_template,request,session, Response ,make_response
from index import PGetPermissions
from index import left_index
from access_control import access_control
from connection_list import connection_list
from host_add import host_add
from domain_list import domain_list
from user_add import user_add
from usbkey_c import usbkey_c
from user_list import user_list
from authtype_list import authtype_list
from user_data import user_data
from service_data import service_data
from user_manage import b_user_manage
#别名管理
from alias_show import alias_show
#access_global_setting
from access_global_setting import access_global_setting
#bhacc
from bhacc import bhacc
from pwdresult_list import pwdresult_list
from role_manage import b_role_manage
from host_manage import b_host_manage
from auth_manage import b_auth_manage
from access_sets import access_set 
from proto_manage import b_proto_manage
from proto_control import proto_control
from ip_list import ip_list
from authmodule_change import authmodule_change
from cmdset import cmdset
from certificate_generation import certificate_generation
from cmdset_add1 import cmdset_add1
from pwdchange_mode_py import pwdchange_mode_py
from devicetype import devicetype
from time_list import time_list
from mac import mac
from pwdchange_list import pwdchange_list
from pwd_export_py import pwd_export_py
from pwd_setting_py import pwd_setting_py
from search_log import search_log
from macset_add import macset_add
from eventinfo_list import eventinfo_list
from account import account
from account_add import account_add
from approve_strategy import approve_set
from client_list import client_list
from hostgroup_list import hostgroup_list
from pwdstrategy_change import pwdstrategy_change
from export_list import export_list
from syswarn import syswarn

#from protocol_data import protocol_data
#from system_outline_data import system_outline_data
from route_list import route_list
from acc_client import acc_client
from acc_client_add import acc_client_add
from pwd_manage import pwd_manage
from hostpwdstrategy_change import hostpwdstrategy_change
from host_test import host_test
from globalstrategy_change import globalstrategy_change
from time_config import time_config
from access_auth_z import access_auth_z
from manageauth_add import manageauth_add
from cmdAuth import cmdAuth
from manage_accessauth import manage_accessauth
from licensing import licensing
from manage_workorder import manage_workorder
from work_order_z import work_order_z
from time_out_change import time_out_change
from AccessProtocol_z import AccessProtocol_z
from password_entry import password_entry
from mailserver import mailserver
from smsm import smsm
from syslog import syslog
from snmp import snmp
from colony_list import colony_list
from smssvr import smssvr
from data_distribution import data_distribution
from config_manage import config_manage
#from module_app import module_app
from module_app_set import module_app_set
from system_update import system_update
from data_manage import data_manage
from find_host import find_host
from down_file import down_file
from down_file_user import down_file_user
from import_file import import_file
from import_file_user import import_file_user
from load_account import load_account
from protocol_lxz import protocol_lxz
from get_host_msg import get_host_msg
from pending_file import pending_file
from import_taskfile import import_taskfile

from search import search
from history_task import history_task
from get_qrcode import get_qrcode
from history_report import history_report
from upload import upload
from analysis import analysis
from playback import playback
from sshkey import sshkey
#相关下载
from related_downloads import related_downloads
from system_power import system_power
from ftpserver import ftpserver
from host_grouping import host_grouping
from batch_operation import batch_operation
from dns_list import dns_list
from tran import tran
from connect_session import connect_session

from generating_log import system_log
from email_transmit import e_transmit
from cluster import cluster

ERRNUM_MODULE = 1000
UPLOAD_FOLDER='/usr/storage/.system/upload/'
reload(sys)
sys.setdefaultencoding('utf-8')
module = '用户登录'
def debug(c):
	return 0;
	path = "/var/tmp/debugp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 * 1024
xss_arrar=['onabort=','onblur=','onchange=','onclick=','ondblclick=','onerror=','onfocus=','onkeydown=','onkeypress=','onkeyup=','onload=','onmousedown=','onmousemove=','onmouseout=','onmouseover=','onmouseup=','onreset=','onresize=','onselect=','onsubmit=','onunload=','alert(','confirm(','prompt(','document.']
csrf_exclude =['bhTranDownload','bhTranUpload','GetMd5','SaveClientPath','zkfp','/usbkey','GetCert','GetCaCert','GetData','/bhacc','/read_report','/analysis_index','/UpdateMac','/cluster_info','/get_ip','/get_net_ip']
res_tr = r'<(.*?)>'
def check_xss(param):
	for o in xss_arrar:
		if param.find(o) >=0:
			return False
	return True
@app.before_request
def request_check():
	args = request.args.to_dict();
	posts = request.form.to_dict();
	for i in args: 
		#debug(str(args[i]))
		param =  re.findall(res_tr,args[i],re.S|re.M)
		
		if (len(param) >0 or check_xss(args[i]) == False):
			#abort(403)
			return render_template('err403.html'),403
			sys.exit()
			
	for i in posts: 
		#debug(str(posts[i]))
		param =  re.findall(res_tr,posts[i],re.S|re.M)
		if (check_xss(posts[i]) == False) and (posts[i].lower()).find('batchwork') <0 and (posts[i].lower()).find('rptname') <0:
			#abort(403)			
			return render_template('err403.html'),403
			sys.exit()
	###csrf 获取当前url
	curr_url = request.url_root;
	path_url = request.path;
	n = False;
	for i in csrf_exclude:
		if path_url.find(i) >=0:
			n  = True;
			break;
	cluster_type = common.get_server_cluster_type();
	if False == n and path_url !='/' and (path_url !='/cluster' or cluster_type == 'single'):
		domain = curr_url.split("/")[2].split(':')[0];
		###获取 HTTP_REFERER 
		refer_url_tmp = request.referrer;
		if refer_url_tmp == None:
			if path_url == '/index':
				return render_template('err404.html',jump='/'),403
			else:
				return render_template('err403.html'),403
			sys.exit();
		else:
			refer_url = refer_url_tmp.split("/")[2].split(':')[0];
		n = False
		centerIP_str = request.form.get('a99')
		if centerIP_str < 0:
			centerIP_str = request.args.get('a99')
		if centerIP_str < 0 or centerIP_str == "" or centerIP_str == "0" or centerIP_str == "1":
			if domain != refer_url and path_url !='/index_cluster':
				if path_url == '/index':
					return render_template('err404.html',jump='/'),403
				else:
					return render_template('err403.html'),403
				sys.exit();
		else:
			centerIP_array = centerIP_str.split(',')
			for j in centerIP_array:
				if j.find(refer_url) >= 0:
					n = True
					break
			if False == n:
				if path_url == '/index':
					return render_template('err404.html',jump='/'),403
				else:
					return render_template('err403.html'),403
				sys.exit();

@app.after_request
def request_check(response):
	centerIP_str = request.form.get('a99')
	refer_url_tmp = request.referrer;
	#debug("tmp:" +str(refer_url_tmp))
	if(refer_url_tmp == None):
		return response

	else:
		refer_url = refer_url_tmp.split("/")[2].split(':')[0];
	#debug("domain1:" +str(refer_url))
	if centerIP_str < 0:
		return response
	else:
		centerIP_array = centerIP_str.split(',')
		IP_tmp = ""
		for index,i in enumerate(centerIP_array):
			if i.find(refer_url) >= 0:
				IP_tmp = "https://" + i.split(":")[0]
				break
		response.headers.add('Access-Control-Allow-Origin', IP_tmp)
		#response.headers.add('Access-Control-Allow-Origin', '*')
		response.headers.add('Access-Control-Allow-Headers', 'x-requested-with,content-type')
		if request.method == 'POST' or request.method == 'GET':
			response.headers['Access-Control-Allow-Methods'] = request.method;
			headers = request.headers.get('Access-Control-Request-Headers')
			if headers:
				response.headers['Access-Control-Allow-Headers'] = headers
				#response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, x-token';
			response.headers.add('Access-Allow-Credentials','true')
		#debug(str(response.headers))
	return response


@app.route("/", methods=['GET', 'POST'])
def login():
	#del_files();
	
	args = request.args.to_dict();
	posts = request.form.to_dict();
	if len(args) >0 or len(posts) > 0:
		return render_template('err403.html')
	
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return render_template('login.html',IfNeedCode = 0,error="系统异常: 数据库连接失败(%d)" %(sys._getframe().f_lineno),jumpcluster=0)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return render_template('login.html',IfNeedCode = 0,error="系统异常: 数据库连接失败(%d)" %(sys._getframe().f_lineno),jumpcluster=0)
		
	sql = "select \"IfNeedCode\" from public.\"PwdStrategy\" ;"
	#debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return render_template('login.html',IfNeedCode = 0,error="系统异常: %s(%d)" %(ErrorEncode(e.args[1]),sys._getframe().f_lineno),jumpcluster=0)
	result = curs.fetchall()
	if result:
		IfNeedCode = int(result[0][0]);
	else:
		IfNeedCode = 0; 
	t = 0
	system_type = common.get_server_cluster_type();
	if system_type == 'double':
		if common.is_server_master() == False:
			t = 1		
	curs.close()
	conn.close()
	#return render_template('licensing_import.html',IfNeedCode = IfNeedCode,error="")
	###设置cookie
	#ran =''.join(random.sample(string.ascii_letters + string.digits, 16));
	ran = StrMD5('safetybase');
	res = make_response(render_template('login.html',IfNeedCode = IfNeedCode,error="",hash =StrMD5(ran),cip=request.remote_addr,jumpcluster= t));
	res.set_cookie('bhost',ran,None,None,'/');
	return res

#ErrorEncode 
def ErrorEncode(str1):
	newStr = "";
	if str1 == "":
		return "";
	newStr = str1.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;	
	
#get passwd
def get_hotp_token(secret,intervals_no):
	key = base64.b32decode(secret, True)
	msg = struct.pack(">Q", intervals_no)
	h = hmac.new(key, msg, hashlib.sha1).digest()
	o = ord(h[19])&15
	h = (struct.unpack(">I",h[o:o+4])[0] & 0x7fffffff)%1000000
	return h

def get_totp_token(secret):
	intervals_no=int(time.time())//30
	valid_codes = []
	debug("intervals:%d" % intervals_no)
	for offset in [-1, 0, 1]:
		debug("%d" % get_hotp_token(secret, intervals_no+offset))
		valid_codes.append(get_hotp_token(secret, intervals_no+offset))
	count=0
	debug("begin")
	while count<3:
		l=str(valid_codes[count])
		if len(l)<6:
			s = 6-len(l)
			if s == 6:
				valid_codes[count] = "000000"
			if s == 5:
				valid_codes[count] = "00000"+l
			if s == 4:
				valid_codes[count] = "0000"+l
			if s == 3:
				valid_codes[count] = "000"+l
			if s == 2:
				valid_codes[count] = "00"+l
			if s == 1:
				valid_codes[count] = "0"+l
		count=count+1
	debug("12313zzz")
	debug(str(valid_codes))
	return valid_codes

def mac_check(addr):
        valid = re.compile(r'''
                        (^([0-9A-F]{1,2}[-]){5}([0-9A-F]{1,2})$
                        |^([0-9A-F]{1,2}[:]){5}([0-9A-F]{1,2})$
                        |^([0-9A-F]{1,2}[.]){5}([0-9A-F]{1,2})$)
                        ''',
                        re.VERBOSE | re.IGNORECASE)
        return valid.match(addr) is not None	

#用来单独认证指纹
def fp_authmodule(user,pwd):
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	lib.pam_test.argtypes = [c_char_p,c_char_p,c_int,c_int,c_char_p]
	lib.pam_test.restype = c_int
	ret = lib.pam_test(user,pwd,13,0,"")
	#执行函数
	return ret

def make_res(strin):
	json_s = json.loads(strin);
	strout =json.dumps(json_s);
	htime = int(time.time() * 1000);
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	json_s['htime']=htime;				
	r.set("check:"+str(htime), StrMD5(StrMD5(json.dumps(json_s)).lower() +str(htime)).lower());
	r.expire("check:"+str(htime), 60 *10) ##10分钟之后超时 自动删除
	#print StrMD5(json.dumps(json_s)).lower();
	return json.dumps(json_s);
	
@app.route("/logincheck", methods=['GET', 'POST'])
def logincheck():
	debug('logincheck')
	oper = '用户登录'
	reload(sys)
	sys.setdefaultencoding('utf-8')
	#r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=3);
	#debug(str(r))
	#serial = r.hget('0','oldestsn')
	#debug(str(serial))
	auth_alert = "";
	server_id=common.get_server_id();
	try:
		crt_t = CertGet(server_id)
	except Exception,e:
		debug(str(e))
		crt_t=None
        g_is_virtual=False
        if (False == os.path.exists(paths.ROOT_VOL_PATH)):
                g_is_virtual=True
	end=1
	if crt_t == None or crt_t[0] == None:
		end=0
	else:
		end_time =int(crt_t[5])
		now_time=int(time.time())
		if end_time<now_time:
			end=0;
			if int(crt_t[6]) != 1: ## 供货
				# auth_alert ='证书已到期，请重新导入证书'
                                if g_is_virtual:
                                        auth_alert ='证书已到期，请重新导入证书'
                                        end=0

                                else:
                                        auth_alert ='证书已到期'
                                        end=1
                        else: ##试用
                                if g_is_virtual:
                                        auth_alert ='证书已到期，请重新导入证书'
                                        end=0
                                else:
                                        auth_alert ='证书已到期，请重新导入证书'
                                        end=0
			
	uCode = request.form.get('a0')
	pW = request.form.get('a1')
	mac = request.form.get('m1')
	if_mac_limit = request.form.get('i1')
	if mac <0 or mac =='':
		mac ="null";
	else:
		if mac_check(base64.b64decode(mac)) == False:
			return make_res('{"Result":False,"ErrMsg":"mac格式错误"}')
			
		mac = "'"+base64.b64decode(mac)+"'";
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
		if not system_log(uCode,oper,msg,module):
			return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
			
		return make_res("{\"result\":false,\"info\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");
	debug("pw:%s" % pW);
	pW = base64.b64decode(pW);	
	debug("code:%s" % uCode)
	debug("pw:%s" % pW)
	
	if checkaccount(uCode) == False:
		return make_res("{\"result\":false,\"info\":\"账号或密码错误\"}")
		
	client_ip = request.remote_addr#获取用户IP
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno))
	
	start_time = request.form.get('s1')
	cnone = request.form.get('c1')
	sign = request.form.get('si')
	
	if(sign < 0 or sign ==''  or cnone < 0 or cnone == ''  or start_time< 0 or start_time==''):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	if(int(time.time()) - int(start_time) > 60):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	if r.get(cnone):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		r.set(cnone, cnone);
		r.expire(cnone, 60) ##1分钟之后超时 自动删除
	
	if sign != StrMD5(str(start_time)+'safetybase'+cnone):
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
		
	#LastLoginTime
	try:
		sql='select "LastLoginTime" from "User" where "UserCode" = E\'%s\';'%(uCode)
		try:
			curs.execute(sql) 
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno))
		result2 = curs.fetchall()
		if len(result2) == 0:
			return make_res("{\"result\":false,\"info\":\"账号或密码错误(%d)\"}" % (sys._getframe().f_lineno))
		LastLoginTime_value = result2[0][0]
	except:
		return make_res("{\"result\":false,\"info\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))	
	#IsPermitLogin
	try:
		if if_mac_limit == '1' or if_mac_limit == '3':
			if mac =='null':
				return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"地址限制\"}")
			sql = "select public.\"IsPermitLogin\"(E'%s',E'%s',%s)" %(uCode,client_ip,mac)
		else:
			sql = "select public.\"IsPermitLogin\"(E'%s',E'%s',null)" %(uCode,client_ip)
		debug(sql)
		try:
			curs.execute(sql) 
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno))
		result = curs.fetchall()
		debug(str(result))
		ret = int(result[0][0])
		if ret == 2 :
			return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"账号或密码错误\"}")
		elif ret == 3:
			return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"地址限制\"}")
			
		conn.commit();
	except:
		return make_res("{\"result\":false,\"info\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))	
	
	debug('ddd')
	if_change_pwd = 'false'
	### int check_password_web(const char *user, const char *passwd)
	#判断密码中是否含有分隔符
	debug('------')
	lib.check_password_web.argtypes = [c_char_p,c_char_p];
	debug('------1')
	lib.check_password_web.restype = c_int
	debug('------2')
	ret = lib.check_password_web(uCode.encode('utf-8'),pW);
	debug(str(ret))
	#0正常 1密码中还有分隔符 -1 函数报错
	try:
		if int(ret) == 0:
			pass
		elif int(ret) == 1:
			auth_alert = "密码包含分隔符,清联系管理员";
		elif int(ret) == -1:
			auth_alert = "系统异常(%d)"% (sys._getframe().f_lineno)
		auth_perm = False	
		if int(ret)!=0:	
			curs.close()
			conn.close()
			msg = auth_alert
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"if_icode\":true,\"info\":\"%s\",\"if_change_pwd\":%s}" %(auth_alert,if_change_pwd))		
	except:
		msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
		if not system_log(uCode,oper,msg,module):
			return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
		return make_res("{\"result\":false,\"info\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))
	###int user_auth(const char *user, const char *passwd, char **name, char **server_pwd, int (*compar)(char *endpwd, char *pwd));

	################## 19-5-6
	# 如果fp_str != "" (有指纹):
		# 取用户认证方式-验证方式 -> 全部通过 先user_auth 通过后再 fp_authmodule
		#     -> 任一通过 先user_auth 通过 return 不通过再 fp_authmodule
	# fp_str == "":
		# 和原来逻辑一样	
	fp_str = request.form.get('f1')
	fp_flag = False
	if fp_str != "":
		sql = "select b.\"MustAllModulesSucc\" from public.\"AuthType\" b where b.\"AuthTypeId\"=(select a.\"AuthTypeId\" from public.\"User\" a where a.\"UserCode\"='%s');" %(uCode)
		debug(sql)
		curs.execute(sql)
		result = curs.fetchall()
		ret1 = int(result[0][0])# 0:任一通过   1:全部通过
		if ret1 == 0:
			ret = fp_authmodule(uCode,fp_str)
			if pW != "":
				if ret == -1 or ret == -2:
					lib.user_auth.argtypes = [c_char_p,c_char_p,c_char_p,c_char_p,c_char_p];
					lib.user_auth.restype = c_int
					ret = lib.user_auth(uCode.encode('utf-8'),pW,None,None,None);
					debug("user_auth")
					debug("ret:%d" % int(ret))
		else:
			ret = fp_authmodule(uCode,fp_str)
			if pW != "":
				if ret == 0 or ret == 1:
					lib.user_auth.argtypes = [c_char_p,c_char_p,c_char_p,c_char_p,c_char_p];
					lib.user_auth.restype = c_int
					ret = lib.user_auth(uCode.encode('utf-8'),pW,None,None,None);
					debug("user_auth")
					debug("ret:%d" % int(ret))
	else:
		lib.user_auth.argtypes = [c_char_p,c_char_p,c_char_p,c_char_p,c_char_p];
		lib.user_auth.restype = c_int
		ret = lib.user_auth(uCode.encode('utf-8'),pW,None,None,None);
		debug("user_auth")
		debug("ret:%d" % int(ret))

	if_change_pwd = 'false'

	##用户状态：0-停用，1-启用，2-锁定，6-用户过期，7-临时用户，8-需要修改密码，9-密码过期。
	try:
		if int(ret) <= 0 or int(ret) == 2 or  int(ret) == 6 or  int(ret) == 9:
			if int(ret) == 0:
				auth_alert = "该账号已停用";
			elif int(ret) == 2:
				auth_alert = "该账号已锁定";
			elif int(ret) == 6:
				auth_alert = "该帐号已过期";
			elif int(ret) == -2:
				auth_alert = "账号或密码错误";
			elif int(ret) == 9:
				auth_alert = "密码已过期，请修改密码";
				if_change_pwd = 'true'
			auth_perm = False			
		else:
			if int(ret) == 8:
				auth_alert = "密码即将过期，请修改密码";
			
			auth_perm = True
	except:
		msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
		if not system_log(uCode,oper,msg,module):
			return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
		return make_res("{\"result\":false,\"info\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))
	
	#判断 认证
	debug("%s" % str(auth_perm))
	#连接数据库 查询 该用户 尝试密码次数和时间 5分钟内尝试2次 则显示验证码
	#数据库连接
	if auth_perm == False:
		###判断即将锁定的次数 和 解锁的剩余时间
		# PGetPwdStrategy()
		
		sql = "select public.\"PGetPwdStrategy\"();"
		curs.execute(sql)
		results = curs.fetchall()[0][0].encode('utf-8')
		if results:
			results_json = json.loads(results)
			IfPwdErrorLock = results_json['IfPwdErrorLock'] ##是否开启锁定
			PwdErrorLockNumber = 5 if results_json['PwdErrorLockNumber'] == None else results_json['PwdErrorLockNumber'] ##密码错误次数
			
			IfAccountAutoUnLock = results_json['IfAccountAutoUnLock'] ##是否开启解锁
			AccountAutoUnLock = 10 * 60 if results_json['AccountAutoUnLock'] == None else results_json['AccountAutoUnLock'] * 60 ### 几分钟之后解锁 	
		else:
			IfPwdErrorLock = False
			PwdErrorLockNumber = 5;
			IfAccountAutoUnLock = False
			AccountAutoUnLock = 10 * 60;
		
		sql = "select \"LastLockedTime\",\"PwdErrTimesForLock\" from public.\"User\" where \"UserCode\"=E'%s';" %(MySQLdb.escape_string(uCode))
		curs.execute(sql)
		results = curs.fetchall()
		LastLockedTime = str(results[0][0]); ##锁定的时间
		PwdErrTimesForLock = 0 if  results[0][1] == None else results[0][1];## 密码输错的次数
		msg1 ='';
		if int(ret) == 2 and IfAccountAutoUnLock == True: ##已被锁定 判断剩余解锁时间
			LastPwdErrTimeForLock_ctime = time.mktime(time.strptime(LastLockedTime,'%Y-%m-%d %H:%M:%S')) #时间戳
			now_time = time.time();
			s_time = AccountAutoUnLock - (now_time - LastPwdErrTimeForLock_ctime);
			if s_time > 0:
				msg1 = "，剩余解锁时间：%d秒" %(s_time)
			
			
		###
		if auth_alert != "":			
			curs.close()
			conn.close()
			msg = auth_alert+msg1
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"if_icode\":true,\"info\":\"%s\",\"if_change_pwd\":%s}" %(auth_alert +msg1,if_change_pwd))			
		
		###
		msg2 = '';
		if IfPwdErrorLock == True:
			try_count = PwdErrorLockNumber - PwdErrTimesForLock 
			if try_count < 0 :
				try_count= 0;
			if try_count == 0:
				msg2 = "，该账号已锁定"
			else:
				msg2 = "，剩余尝试次数：%d次" %(try_count);
			
		sql = "select public.\"PSavePwdErrTime\"(E'%s')" %(uCode)
		try:
			curs.execute(sql) 
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno))
		conn.commit()
		result = curs.fetchall()[0][0]
		result_json = json.loads(result)
		if result_json['Result'] == True:
			sql = "select public.\"PGetPwdErrTime\"(E'%s')" %(uCode)
			try:
				curs.execute(sql) 
			except pyodbc.Error,e:
				curs.close()
				conn.close()
				msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
				if not system_log(uCode,oper,msg,module):
					return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
				return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno))
			result = curs.fetchall()[0][0]
			result_json = json.loads(result)
			if result_json['LastPwdErrTime'] == None:
				msg = '失败：账号或密码错误%s' %(msg2)
				if not system_log(uCode,oper,msg,module):
					return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
				return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"账号或密码错误%s\"}" %(msg2))
			else:
				last_time = time.mktime(time.strptime(result_json['LastPwdErrTime'],'%Y-%m-%d %H:%M:%S')) #时间戳
				now_time = time.time();
				if (not result_json['PwdErrTimes'] == None) and  result_json['PwdErrTimes'] >=2 and (now_time-last_time) <= 300: #显示验证码
					curs.close()
					conn.close()
					msg = '失败：账号或密码错误%s' %(msg2)
					if not system_log(uCode,oper,msg,module):
						return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
					return make_res("{\"result\":false,\"if_icode\":true,\"info\":\"账号或密码错误%s\"}" %(msg2))
				else:
					if(now_time-last_time)>=300:
						sql = "update public.\"User\" set \"PwdErrTimes\"=1 where \"UserCode\" = E\'%s\'" %(uCode)
						debug("sql:%s" % sql)
						try:
							curs.execute(sql)
						except pyodbc.Error,e:
							curs.close()
							conn.close()
							msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
							if not system_log(uCode,oper,msg,module):
								return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
							return make_res("{\"result\":false,\"info\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno))
						conn.commit();
					curs.close()
					conn.close()
					msg = '失败：账号或密码错误%s' %(msg2)
					if not system_log(uCode,oper,msg,module):
						return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
					return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"账号或密码错误%s\"}" %(msg2))
		else: 
			curs.close()
			conn.close()
			msg = '失败：账号或密码错误%s' %(msg2)
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"info\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"账号或密码错误%s\"}" %(msg2))
	else:	
		##
		'''
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(pW,pwd_rc4)#执行函数
		pW = pwd_rc4.value #获取变量的值

		sql = "update public.\"User\" set \"LoginPwd\"='%s' where \"UserCode\" =E'%s';" %(pW,uCode)
		curs.execute(sql)
		'''
		###
		sql = "select \"SecretKey\" from \"User\" where \"UserCode\" = E\'%s\'" %(uCode)
		debug("sql:%s" % sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"if_icode\":false,\"info\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno))			
		result = curs.fetchall()[0][0]
		conn.commit()
		curs.close()
		conn.close()
		sess ='';
		if result != None:
			if result == '':
				###暂时修改 ifChangeTotp 全部为false 
				return make_res("{\"result\":true,\"if_icode\":false,\"ifChangeTotp\":false,\"info\":\"%s\",\"auth_alert\":\"%s\",\"end\":%s,\"LastLoginTime\":\"%s\"}" %(sess,auth_alert,end,str(LastLoginTime_value)))
			else:
				return make_res("{\"result\":true,\"if_icode\":false,\"ifChangeTotp\":false,\"info\":\"%s\",\"auth_alert\":\"%s\",\"end\":%s,\"LastLoginTime\":\"%s\"}" %(sess,auth_alert,end,str(LastLoginTime_value)))
		else:
			return make_res("{\"result\":true,\"if_icode\":false,\"ifChangeTotp\":false,\"info\":\"%s\",\"auth_alert\":\"%s\",\"end\":%s,\"LastLoginTime\":\"%s\"}" %(sess,auth_alert,end,str(LastLoginTime_value)))
	'''
	r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=3);
        serial = r.hget('0','oldestsn')
        crt_t = CertGet()
	end=1
        if crt_t == None:
		end=0
	else:
		end_time =int(crt_t[5])
		now_time=int(time.time())
		if end_time<now_time:
			end=0
	'''
	return make_res("{\"result\":true,\"if_icode\":false,\"info\":\"%s\",\"auth_alert\":\"%s\",\"end\":%s,\"LastLoginTime\":\"%s\"}" %(sess,auth_alert,end,str(LastLoginTime_value)))
	
@app.route('/change_sys_user_secret',methods=['GET','POST'])
def change_sys_user_secret():
	uCode = request.form.get('a1')
	secret = request.form.get('a2')
	
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "{\"result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
		
	if checkaccount(uCode) == False:
		return "{\"result\":true,\"ErrMsg\":\"\"}"
		
	sql = "update public.\"User\" set \"SecretKey\"=E'%s' where \"UserCode\" =E'%s';" %(secret,uCode)
	curs.execute(sql)

	conn.commit()
	curs.close()
	conn.close()
	return "{\"result\":true,\"ErrMsg\":\"\"}"
	
@app.route('/licensing_import',methods=['GET','POST'])
def licensing_import():
	uCode = request.form.get('uCode')
	#sess = request.form.get('a0')
	a10 = request.form.get('a10')
	#debug(sess)
	debug(uCode)
	debug('=-============')
	is_guide = False;
	
	myCookie = request.cookies #获取所有cookie
	hash = '';
	if myCookie.has_key('bhost'):
		hash = StrMD5(myCookie['bhost']);
	
	###
	mm  = request.form.get('mm');
	if mm < 0 or mm =='':
		mm = request.args.get('mm')
	if mm < 0 or mm =='':
		return '',403
	htime  = request.form.get('ht');
	if htime < 0 or htime =='':
		htime = request.args.get('ht')
	if htime < 0 or htime =='':
		return '',403
	
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	info = r.get("check:"+htime);
	if info == None:
		return '',403
	r.delete("check:"+htime);
	if info.lower() != StrMD5(mm.lower() + htime).lower():
		return '',403
	
	if os.path.exists('/usr/etc/server.crt') == False:
		is_guide = True
		
	###
	mac = request.form.get('ma')
	if mac <0 or mac == ' ' or mac =='':
		mac ='';
	else:
		if mac_check(base64.b64decode(mac)) == False:
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'mac格式错误(%d)')</script></html>" % (sys._getframe().f_lineno)
		mac = "'"+base64.b64decode(mac)+"'";
	
	client_ip = request.remote_addr#获取用户IP
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	if checkaccount(uCode) == False:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	sql = "select \"PageTimeOut\" from public.\"TimeOutConfig\";"
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		result_TimeOut= result[0][0];
	else:
		result_TimeOut = 30;
	
	sql = "select \"LoginUniqueIP\" from public.\"GlobalStrategy\" ;"
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP= int(result[0][0])
	else:
		LoginUniqueIP = 0;
		
	sql = "select \"LoginUniqueIP\" from public.\"User\" where \"UserCode\"=E'%s';" %(uCode)
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP_user= int(result[0][0])
	else:
		LoginUniqueIP_user = 0;	
	
	if LoginUniqueIP_user == 1 or LoginUniqueIP == 1:
		LoginUniqueIPLimit = 1;
	else:
		LoginUniqueIPLimit = 0;
	
	#def SessionLogin(logn, dev, clas, outime, dbcode=3):
	##
	sess = SessionLogin(uCode,client_ip,0,result_TimeOut, mac, 0,LoginUniqueIPLimit)
	if isinstance(sess,tuple):
		sess_tmp = sess[0]
		ip_tmp = sess[1].replace("'","")
	else:
		sess_tmp = sess
	if sess_tmp == 1:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'当前用户已在%s上登录')</script></html>" % (ip_tmp)
	elif sess_tmp == 0:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'非法访问')</script></html>"
	if sess_tmp < 0 :
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常: 会话创建失败（%d）')</script></html>" %(sys._getframe().f_lineno)
		 
	sql = "update public.\"User\" set \"PwdErrTimes\"=0 where \"UserCode\" = E\'%s\';" %(uCode)
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()
	return render_template('licensing_import.html',uCode=uCode,a10=a10,sess=sess,is_guide=is_guide,hash=hash)

@app.route('/judge_code',methods=['GET','POST'])
def judge_code():
	reload(sys)
        sys.setdefaultencoding('utf-8')
        se = request.form.get("a0")
	id_value=request.form.get("a1")
	code_value=request.form.get("a2")
	client_ip = request.remote_addr
        (error,system_user,mac) = SessionCheck(se,client_ip)
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
			sql='select count(*) from private."Message" m where m."MessageId"=%s'%id_value
			curs.execute(sql)
			result_num = curs.fetchall()[0][0]
			if result_num==0:
				return "{\"Result\":false,\"ErrMsg\":\"该消息已被删除\"}" 
			
			sql='select m."VerificationCode",m."MessageType",m."SenderId" from private."Message" m where m."MessageId"=%s'%id_value
			curs.execute(sql)
			result=curs.fetchall()
			result_code = result[0][0]
			MessageType=result[0][1]
			SenderId=result[0][2]
			jsondata="{\"MessageId\":"+id_value+",\"ProcessStatus\":2,\"Status\":5}"
			NowTime=int(time.time())
			if result_code==None:
				return "{\"Result\":false,\"ErrMsg\":\"无需输入验证码\"}"
			
			if result_code==code_value:
				sql="select public.\"PSaveMessage\"(E'%s');" %(MySQLdb.escape_string(jsondata).decode('utf-8'))
				curs.execute(sql)
				conn.commit()
				if MessageType==13:
					sql='SELECT u."PwdFileApprove" FROM public."User" u where u."UserId"=%s;'%(SenderId)
					curs.execute(sql)
					PwdFileApprove = curs.fetchall()[0][0]
					VerificationCode = result_code
					new_arr=[]
					if PwdFileApprove!=None or PwdFileApprove!='':
						PwdFileApprove=PwdFileApprove.split('\n')
						for PwdFileApprove_i in PwdFileApprove:
							i_arr=PwdFileApprove_i.split(':')
							if i_arr[0]==VerificationCode:
								new_arr.append('%s:%s'%(NowTime,i_arr[1]))
							else:
								new_arr.append(PwdFileApprove_i)
					curs.execute("update \"User\" set \"PwdFileApprove\" = E'%s' where \"UserId\"=%s;" %('\n'.join(new_arr),SenderId))
					curs.commit()
				return "{\"Result\":true,\"info\":\"验证成功\"}"
			else:
				return "{\"Result\":false,\"ErrMsg\":\"验证码错误\"}"
			
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@app.route('/create_file_crt',methods=['GET', 'POST'])
def create_file_crt():
	debug('create_file_crt')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	se = request.form.get("a0")
	debug('se:'+str(se))
	f = request.files['file_change']
	debug(f.filename)
	client_ip = request.remote_addr
	debug(client_ip)
	(error,system_user,mac) = SessionCheck(se,client_ip)
	debug('error:'+str(error))
	
	hash  = request.form.get('ha');
	
	if hash < 0 or hash =='':
		pass
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	fname = secure_filename(f.filename)
	debug(str(fname))
	time_old=0
	debug(str(os.path.isfile("/usr/etc/server.crt")))
	if os.path.isfile("/usr/etc/server.crt"):
		time_old=os.path.getmtime('/usr/etc/server.crt')
	debug(str(time_old))
	debug('======')
	try:
		f.save(os.path.join(UPLOAD_FOLDER, fname))
		fname_path = os.path.join(UPLOAD_FOLDER,fname)
		debug(fname_path)
		task_content = '[global]\nclass = taskcrt\ntype = movecrt\npath=%s\n' % (fname_path)
		debug(str(task_content))
		server_id=common.get_server_id();
		if False == task_client.task_send(server_id, task_content):
			return "{\"Result\":false,\"info\":\"任务下发异常(%d)\"}" %(sys._getframe().f_lineno)
		debug('--- while True:---')
		time_new=0
		while True:
			debug(str('os.path.isfile("/usr/etc/server.crt")')+str(os.path.isfile("/usr/etc/server.crt")))
			if os.path.isfile("/usr/etc/server.crt"):
				time_new=os.path.getmtime('/usr/etc/server.crt')
				#os.remove(fname_path)
				debug(str(time_new))
				if time_new>time_old:
					break
			time.sleep(0.5)
			#r = redis.StrictRedis(host=common.get_inner_master_ip(), port=defines.REDIS_PORT, db=3);
			#debug(str(r))
        	#serial = r.hget('0','oldestsn')
        	#debug(str(serial))
		server_id=common.get_server_id();
		try:
			crt_t = CertGet(server_id)
		except Exception,e:
			debug(str(e))
			crt_t=None
		debug('----------------------1---------------------------')
		debug(str(crt_t))
		end=1
		if crt_t==None or crt_t[0] == None:
			end=0
			task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=/usr/etc/server.crt\n'
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":false,\"ErrMsg\":\"证书内容无效\"}"
		else:
			end=1;
			end_time =int(crt_t[5])
			now_time=int(time.time())
			if end_time<now_time:
				if int(crt_t[6]) != 1: ## 供货
					#auth_alert ='证书已到期，请重新导入证书'
					pass;
				else:
					return "{\"Result\":false,\"ErrMsg\":\"证书已到期，请重新导入证书\"}"
			
		return "{\"Result\":true,\"info\":\"\"}" 
	except IOError,e:
		return "{\"Result\":false,\"ErrMsg\":\"%s\"}" %(str(e))
@app.route('/set_session',methods=['GET', 'POST'])
def set_session():       
	uCode = request.form.get('u1');
	mac = request.form.get('m1')
	if mac <0 or mac == ' ' or mac =='':
		mac ='';
	else:
		if mac_check(base64.b64decode(mac)) == False:
			return "{\"Result\":false,\"ErrMsg\":\"mac格式错误\"}"
		mac = "'"+base64.b64decode(mac)+"'";
	
	client_ip = request.remote_addr#获取用户IP
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	if checkaccount(uCode) == False:
		return "{\"result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	sql = "select \"PageTimeOut\" from public.\"TimeOutConfig\";"
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		result_TimeOut= result[0][0];
	else:
		result_TimeOut = 30;
	
	sql = "select \"LoginUniqueIP\" from public.\"GlobalStrategy\" ;"
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP= int(result[0][0])
	else:
		LoginUniqueIP = 0;
		
	sql = "select \"LoginUniqueIP\" from public.\"User\" where \"UserCode\"=E'%s';" %(uCode)
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP_user= int(result[0][0])
	else:
		LoginUniqueIP_user = 0;	
	
	if LoginUniqueIP_user == 1 or LoginUniqueIP == 1:
		LoginUniqueIPLimit = 1;
	else:
		LoginUniqueIPLimit = 0;
	
	#def SessionLogin(logn, dev, clas, outime, dbcode=3):
	##
	sess = SessionLogin(uCode,client_ip,0,result_TimeOut, mac, 0,LoginUniqueIPLimit)
	if isinstance(sess,tuple):
		sess_tmp = sess[0]
		ip_tmp = sess[1].replace("'","")
	else:
		sess_tmp = sess
	if sess_tmp == 1:
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"当前用户已在%s上登录\"}" %(ip_tmp)
	elif sess_tmp == 0:
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"非法访问\"}"
	if sess_tmp < 0 :
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: 会话创建失败(%d)\"}" %(sys._getframe().f_lineno)
		 
	sql = "update public.\"User\" set \"PwdErrTimes\"=0 where \"UserCode\" = E\'%s\';" %(uCode)
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"result\":false,\"info\":\"\",\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()
	return "{\"result\":true,\"info\":\"%s\",\"ErrMsg\":\"\"}"%(str(sess_tmp))
@app.route("/login_link", methods=['GET', 'POST'])
def login_link():
	uCode = request.form.get('uCode');
	if uCode < 0:
		uCode = request.args.get('uCode')
	debug(uCode)
	#sess = request.form.get('a0')
	#if sess < 0 :
	#	sess = request.args.get('a0')
	#sess = filter(str.isdigit, str(sess))
	uCode = cgi.escape(uCode.lower())
	LastLoginTime = request.form.get('a10')
	if LastLoginTime < 0 :
		LastLoginTime = request.args.get('a10')
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
	###
	mm  = request.form.get('mm');
	if mm < 0 or mm =='':
		mm = request.args.get('mm')
	if mm < 0 or mm =='':
		return '',403
	htime  = request.form.get('ht');
	if htime < 0 or htime =='':
		htime = request.args.get('ht')
	if htime < 0 or htime =='':
		return '',403
	
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	info = r.get("check:"+htime);
	if info == None:
		return '',403
	r.delete("check:"+htime);
	if info.lower() != StrMD5(mm.lower() + htime).lower():
		return '',403
		
	
	try:  
		if LastLoginTime == 'None' or time.strptime(LastLoginTime, "%Y-%m-%d %H:%M:%S"):
			pass
		else:
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'登录时间格式错误(%d)')</script></html>" % (sys._getframe().f_lineno)
	except:
		if LastLoginTime =='None':
			pass
		else:
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'登录时间格式错误(%d)')</script></html>" % (sys._getframe().f_lineno)
	###
	mac = request.form.get('ma')
	if mac <0 or mac == ' ' or mac =='':
		mac ='';
	else:
		if mac_check(base64.b64decode(mac)) == False:
			return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'mac格式错误(%d)')</script></html>" % (sys._getframe().f_lineno)
		mac = "'"+base64.b64decode(mac)+"'";
	
	client_ip = request.remote_addr#获取用户IP
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	if checkaccount(uCode) == False:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	sql = "select \"PageTimeOut\" from public.\"TimeOutConfig\";"
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		result_TimeOut= result[0][0];
	else:
		result_TimeOut = 30;
	
	sql = "select \"LoginUniqueIP\" from public.\"GlobalStrategy\" ;"
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP= int(result[0][0])
	else:
		LoginUniqueIP = 0;
		
	sql = "select \"LoginUniqueIP\" from public.\"User\" where \"UserCode\"=E'%s';" %(uCode)
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	result = curs.fetchall()
	if result:
		LoginUniqueIP_user= int(result[0][0])
	else:
		LoginUniqueIP_user = 0;	
	
	if LoginUniqueIP_user == 1 or LoginUniqueIP == 1:
		LoginUniqueIPLimit = 1;
	else:
		LoginUniqueIPLimit = 0;
	
	#def SessionLogin(logn, dev, clas, outime, dbcode=3):
	##
	sess = SessionLogin(uCode,client_ip,0,result_TimeOut, mac, 0,LoginUniqueIPLimit)
	if isinstance(sess,tuple):
		sess_tmp = sess[0]
		ip_tmp = sess[1].replace("'","")
	else:
		sess_tmp = sess
	if sess_tmp == 1:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'当前用户已在%s上登录')</script></html>" % (ip_tmp)
	
	elif sess_tmp == 0:
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'非法访问')</script></html>"
	if sess_tmp < 0 :
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常: 会话创建失败(%d)')</script></html>" %(sys._getframe().f_lineno)
		 
	sql = "update public.\"User\" set \"PwdErrTimes\"=0 where \"UserCode\" = E\'%s\';" %(uCode)
	debug("sql:%s" % sql)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'系统异常(%d)')</script></html>" % (sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()

	oper = '用户登录'
	msg = '成功'
	if not system_log(uCode,oper,msg,module):
		return "<html><head><meta http-equiv=\"Content-Type\" content=\"charset=utf-8\"></head><script>var userAgent = navigator.userAgent;var ie8 = userAgent.indexOf('Trident/4.0');if(ie8 != -1){document.write('<script src=\"/manage/js/jquery-IE8.js\"></' + 'script>');}else{document.write('<script src=\"/manage/js/jquery.min.js\"></' + 'script>');}</script><script src=\"/manage/js/jquery.easing.js\"></script><script src=\"/manage/js/layer.js\"></script><link rel=\"stylesheet\" href=\"/manage/css/style.css\"><script src=\"/manage/js/common.js\"></script><script src=\"/manage/js/common_e.js\"></script><body></body><script>_alert(1,'生成日志失败(%d)')</script></html>" % (sys._getframe().f_lineno)
		
	return "<html><head><body> <form name=\"frm\" action=\"/bhost/index\" method=\"post\"><input type=\"hidden\" name=\"se\" id=\"se\" value=\"\"><input type=\"hidden\" name=\"us\" id=\"us\" value=\"\"><input type=\"hidden\" name=\"a10\" id=\"a10\" value=\"\"></form><script> document.frm.se.value='%s';document.frm.a10.value ='%s';document.frm.action = \"/bhost/index\";document.frm.submit();</script></body></head></html>\n" % (sess_tmp,LastLoginTime)

@app.route("/_getIcode", methods=['GET', 'POST'])
def _getIcode():
	try:
		#字体的位置，不同版本的系统会有不同
		font_path = '/var/www/manage/html/yahei.ttf'
		#生成几位数的验证码
		number = 4
		#生成验证码图片的高度和宽度
		size = (70,24)
		#背景颜色，默认为灰色
		bgcolor = (108,108,108)
		#字体颜色，默认为白色
		fontcolor = (255,255,255)
		width,height = size #宽和高
		image = Image.new('RGBA',(width,height),bgcolor) #创建图片
		# 创建Font对象:
		font = ImageFont.truetype(font_path,16) #验证码的字体
		# 创建Draw对象:
		draw = ImageDraw.Draw(image)

		# 输出文字:
		idencode = ""
		for t in range(4):
			chr_code = chr(random.randint(65, 90))
			idencode = idencode + str(chr_code)
			draw.text((width * t / number + 4, 2),chr_code, font=font, fill=fontcolor)
		#删除
			
		image.save('/var/www/manage/html/images/icode.png') #保存验证码图片

		return "{\"result\":true,\"info\":\"%s\"}" %(idencode)
	except:
		return "{\"result\":false,\"info\":\"%s:%s\"}" %(str(sys.exc_info()[0]),str(sys.exc_info()[1]))

@app.route("/test_qr", methods=['GET', 'POST'])
def test_qr():
	uCode = request.form.get('z1')
	qr_code = request.form.get('z2')
	if checkaccount(uCode) == False:
		return "{\"result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = "select \"SecretKey\" from \"User\" where \"UserCode\" = E\'%s\'" %(uCode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			valid_codes = get_totp_token(results)
			if int(qr_code) in valid_codes:
				return "{\"Result\":true}"
			else:
				sql = "select \"LastKeyErrTime\",\"KeyErrTimes\" from public.\"User\" where \"UserCode\" = E'%s'" % uCode
				debug("sqltt:%s" % sql)
				curs.execute(sql)
				result = curs.fetchall()
				debug("%d" % result[0][1])
				if result[0][1] == 2:#5分钟内出错3次，返回登录界面
					sql = "update public.\"User\" set \"LastKeyErrTime\" = null,\"KeyErrTimes\" = 0 where \"UserCode\" = E'%s'" % uCode
					debug(sql)
					curs.execute(sql)
					return "{\"Result\":false,\"info\":1}"
				if result[0][0] == None: #第一次输错
					err_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
					sql = "update public.\"User\" set \"LastKeyErrTime\" = E'%s',\"KeyErrTimes\" = 1 where \"UserCode\" = E'%s'" % (err_time,uCode)
					debug(sql)
					curs.execute(sql)
				else:
					debug("777777777")
					debug("result:%s" % result[0][0])
					sql_time = "'%s'" % result[0][0]
					debug("sql_time:%s" % sql_time)
					last_time = time.mktime(time.strptime(str(result[0][0]),'%Y-%m-%d %H:%M:%S')) #时间戳
					debug("1231313")
					now_time = time.time()
					debug("last_time:%d" % last_time)
					debug("now_time:%d" % now_time)
					if last_time - now_time <= 300:#5分钟之内
						sql = "update public.\"User\" set \"KeyErrTimes\" = %d where \"UserCode\" = E'%s'" % (result[0][1]+1,uCode)
						debug(sql)
						curs.execute(sql)
					else:#超过5分钟出错，更新时间和次数
						err_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
						debug("err_time:%s" % err_time)
						sql = "update public.\"User\" set \"LastKeyErrTime\" = E'%s',\"KeyErrTimes\" = 1 where \"UserCode\" = E'%s'" % (err_time,uCode)
						debug(sql)
						curs.execute(sql)
				return "{\"Result\":false,\"info\":2}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))

@app.route("/logout", methods=['GET', 'POST'])
def logout():
	#session.pop['username',None]
	#SessionClean
	session = request.form.get('a0')
	SessionClean(session);
	return "<html><head><body> <form name=\"frm\" action=\"\" method=\"post\"></form><script>top.location.href='/';</script></body></head></html>\n"
@app.route("/report_png", methods=['GET', 'POST'])
def report_png():
	return render_template('server.html')
def del_files(path='/var/tmp'):
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.find("debug")>=0:
				file_path = os.path.join(root, name)
				if os.path.getsize(file_path) > 1024:
					os.remove(file_path)

###向导
@app.route("/guide_flow", methods=['GET', 'POST'])
def guide_flow():
	sess = request.form.get('a0')
	if sess < 0 :
		sess = request.args.get('a0')
		
	return render_template('guide.html',se=sess)

#guide_yunwei
@app.route("/guide_yunwei", methods=['GET', 'POST'])
def guide_yunwei():
	sess = request.form.get('a0')
	if sess < 0 :
		sess = request.args.get('a0')
	myCookie = request.cookies #获取所有cookie
	hash = '';
	if myCookie.has_key('bhost'):
		hash = StrMD5(myCookie['bhost'])
		
	return render_template('guide_yunwei.html',se=sess,hash=hash)

### 重启httpd
@app.route("/restart_web", methods=['GET', 'POST'])
def restart_web(): 
	content = "[global]\nclass = taskglobal\ntype = restartWebServer"
	ss = task_client.task_send(defines.MASTER_SERVER_ID, content)
	if ss == False:
		return "{\"Result\":false,\"ErrMsg\":\"重启httpd失败：%s(%d)\"}" %(task_client.err_msg,sys._getframe().f_lineno)
	return "{\"Result\":true,\"ErrMsg\":\"\"}"
	
@app.route("/if_exists_webcrt", methods=['GET', 'POST'])
def if_exists_webcrt(): 
	if os.path.exists('/usr/ssl/certs/ca.crt') == True:
		return "{\"Result\":true,\"info\":true}"	
	else:
		return "{\"Result\":true,\"info\":false}"

##获取认证方式 并且查看是否初始化过 初始密码
@app.route("/get_user_authtype", methods=['GET', 'POST'])
def get_user_authtype():
	UserCode = request.form.get('a0')
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":[]}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select "AuthTypeId","CertCn" from public."User" where "UserCode" =E\'%s\';' %(UserCode)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			if not results:
				return "{\"Result\":true,\"info\":[]}"
			if results[0][0] == None:
				sql = 'select a."AuthModuleName",b."Order",b."PwdLen",a."AuthMode",a."UserObject",a."Csp" from public."AuthModule" a join public."AuthTypeMember" b on a."AuthModuleId" = b."AuthModuleId" where b."AuthTypeId" in (select "AuthTypeId" from public."AuthType" where "IsDefault" =true) ORDER by b."Order";'
			else:
				sql = 'select a."AuthModuleName",b."Order",b."PwdLen",a."AuthMode",a."UserObject",a."Csp" from public."AuthModule" a join public."AuthTypeMember" b on a."AuthModuleId" = b."AuthModuleId" where b."AuthTypeId" in (select "AuthTypeId" from public."User" where "UserCode" =\'%s\') ORDER by b."Order";' %(UserCode);
				
			CertCn = '' if results[0][1] == None else base64.b64encode(results[0][1].encode('gb2312'));
			
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			result_str = ""
			for result in results:
				if result[2] == None:
					result[2] = -1;
				CSP = '';
				CN = '';
				if result[3] == 9: ##第三方key
				
					Csp_json = json.loads(result[5].decode('utf-8'));
				
					for o in Csp_json:
						CSP += (o['CSP']) +'	'
						CN += (o['CN']) +'	'
					CSP = base64.b64encode(CSP[:-1])
					CN = base64.b64encode(CN[:-1])
				result_str +="{\"AuthModuleName\":\"%s\",\"Order\":%d,\"PwdLen\":%d,\"AuthMode\":%d,\"UserObject\":\"%s\",\"CSP\":\"%s\",\"CN\":\"%s\",\"CertCn\":\"%s\"}," %(result[0].decode('utf-8'),result[1],result[2],result[3],result[4],CSP,CN,CertCn)
			result_str = result_str[:-1]
				
			if result_str == "":
				return "{\"Result\":true,\"info\":[]}"
			sql = "select \"SecretKey\" from \"User\" where \"UserCode\" = E\'%s\'" %(UserCode)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			initpwd = 'false' 
			if results == None:
				initpwd = 'true'
			return "{\"Result\":true,\"info\":[%s],\"initpwd\":%s}" % (result_str,initpwd)		
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
#账号
def checkaccount(account):
	p = re.compile(u'^[\w\.\-\u4E00-\u9FA5]+$')
	if p.match(account.decode('utf-8')):
		return True
	else:
		return False
				
@app.route("/check_init_pwd", methods=['GET', 'POST'])
def check_init_pwd():		
	uCode = request.form.get('a0')
	pW = request.form.get('a1')	
	pW = base64.b64decode(pW);
	client_ip = request.remote_addr#获取用户IP
	oper = '用户登录'
	if checkaccount(uCode) == False:
		return make_res("{\"result\":false,\"ErrMsg\":\"账号或密码错误\"}")
	try:
		conn = pyodbc.connect(StrSqlConn("BH_CONFIG"))
	except pyodbc.Error,e:
		return make_res("{\"result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return make_res("{\"result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% (ErrorEncode(e.args[1]),sys._getframe().f_lineno))
	#IsPermitLogin
	try:
		sql = "select public.\"IsPermitLogin\"(E'%s',E'%s',null)" %(uCode,client_ip)
		debug(sql)
		try:
			curs.execute(sql) 
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			return make_res("{\"result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}"% ( ErrorEncode(e.args[1]),sys._getframe().f_lineno))
		result = curs.fetchall()
		debug(str(result))
		ret = int(result[0][0])
		if ret == 2 :
			return make_res("{\"result\":false,\"ErrMsg\":\"账号或密码错误\"}")
		elif ret == 3:
			return make_res("{\"result\":false,\"ErrMsg\":\"IP限制\"}")
			
		conn.commit();
	except:
		return make_res("{\"result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))	
	curs.close()
	conn.close()	
	##int user_auth_for_init(char *bhuser, char *pass)
	if os.path.exists('/usr/lib64/logproxy.so') == False:
		msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
		if not system_log(uCode,oper,msg,module):
			return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
		return make_res("{\"result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so");	
	lib.user_auth_for_init.argtypes = [c_char_p,c_char_p];
	lib.user_auth_for_init.restype = c_int	
	ret = lib.user_auth_for_init(uCode,pW);
	auth_alert = "";
	auth_perm =True
	##用户状态：0-停用，1-启用，2-锁定，6-用户过期，7-临时用户，8-需要修改密码，9-密码过期。
	try:
		if int(ret) <= 0 or int(ret) == 2 or  int(ret) == 6:
			if int(ret) == 0:
				auth_alert = "该账号已停用";
			elif int(ret) == 2:
				auth_alert = "该账号已锁定";
			elif int(ret) == 6:
				auth_alert = "该帐号已过期";
			else:
				auth_alert = "账号或密码错误";
			auth_perm = False			
		else:
			if int(ret) == 8:
				auth_alert = "请修改密码";
			elif int(ret) == 9:
				auth_alert = "密码已过期，请修改密码";
			auth_perm = True
	except:
		msg = '失败：系统异常(%d)'% (sys._getframe().f_lineno)
		if not system_log(uCode,oper,msg,module):
			return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
		return make_res("{\"result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (sys._getframe().f_lineno))
	
	if auth_perm == False:
		###
		if auth_alert != "":		
			msg = auth_alert
			if not system_log(uCode,oper,msg,module):
				return make_res("{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}")
			return make_res("{\"result\":false,\"ErrMsg\":\"%s\"}" %(auth_alert))
	else:
		return make_res("{\"result\":true,\"info\":\"\"}")

@app.route("/init_auth", methods=['GET', 'POST'])
def init_auth():		
	uCode = request.form.get('a0')
	pW = request.form.get('a1')	
	pW = base64.b64decode(pW);
	lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
	pwd_rc4 = c_char_p()# 定义一个指针
	pwd_rc4.value = "0"*512 # 初始化 指针
	lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
	lib.encrypt_pwd.restype = None #定义函数返回值
	ret = lib.encrypt_pwd(pW,pwd_rc4)#执行函数
	pW = pwd_rc4.value #获取变量的值
	
	###
	mm  = request.form.get('mm');
	if mm < 0 or mm =='':
		mm = request.args.get('mm')
	if mm < 0 or mm =='':
		return '',403
	htime  = request.form.get('ht');
	if htime < 0 or htime =='':
		htime = request.args.get('ht')
	if htime < 0 or htime =='':
		return '',403
	
	r = redis.StrictRedis(common.get_inner_master_ip(), defines.REDIS_PORT, 9);
	info = r.get("check:"+htime);
	if info == None:
		return '',403
	r.delete("check:"+htime);
	if info.lower() != StrMD5(mm.lower() + htime).lower():
		return '',403
	
	return render_template('init_auth.html',uCode = uCode,pW=pW);

@app.route("/update_pwd", methods=['GET', 'POST'])
def update_pwd():
	UserCode = request.form.get('a0')
	Password = request.form.get('a1')
	Password = base64.b64decode(Password);
	SecretKey = request.form.get('a2')
	flag_new_pwd = request.form.get('a3')
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":\"\"}"
	if flag_new_pwd == '0':
		lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
		pwd_rc4 = c_char_p()# 定义一个指针
		pwd_rc4.value = "0"*512 # 初始化 指针
		lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
		lib.encrypt_pwd.restype = None #定义函数返回值
		ret = lib.encrypt_pwd(Password,pwd_rc4)#执行函数
		Password = pwd_rc4.value #获取变量的值
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			#获取当前时间
			time_now = int(time.time())
			#转换成localtime
			time_local = time.localtime(time_now)
			#转换成新的时间格式(2018/04/02 10:59:20)
			dt = time.strftime("%Y/%m/%d %H:%M:%S",time_local)
			sql = 'update public."User" set "Password"=E\'%s\',\"SecretKey\"=E\'%s\',"LastPwdModifyTime"=E\'%s\' where "UserCode"=E\'%s\';' %(MySQLdb.escape_string(Password).decode("utf-8"),SecretKey,dt,UserCode);
			debug(sql)
			curs.execute(sql)
			conn.commit();
			return "{\"Result\":true,\"info\":\"\"}"		
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
###获取当前用户的 认证方式是否存在短信认证   短信验证码的时间
@app.route("/check_sms", methods=['GET', 'POST'])
def check_sms():	
	UserCode = request.form.get('a0')
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":{\"is_sms\":false,\"VcodeCreateTime\":\"\",\"is_local\":false,\"VcodeCreateTime1\":\"\"}}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select "AuthTypeId" from public."User" where "UserCode" =E\'%s\';' %(UserCode)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			if not results:
				return "{\"Result\":true,\"info\":{\"is_sms\":false,\"VcodeCreateTime\":\"\",\"is_local\":false,\"VcodeCreateTime1\":\"\"}}"
			if results[0][0] == None:
				sql = 'select a."AuthMode" from public."AuthModule" a join public."AuthTypeMember" b on a."AuthModuleId" = b."AuthModuleId" where b."AuthTypeId" in (select "AuthTypeId" from public."AuthType" where "IsDefault" =true) ORDER by b."Order";'
			else:
				sql = 'select a."AuthMode" from public."AuthModule" a join public."AuthTypeMember" b on a."AuthModuleId" = b."AuthModuleId" where b."AuthTypeId" in (select "AuthTypeId" from public."User" where "UserCode" =E\'%s\') ORDER by b."Order";' %(UserCode);
				
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			result_str = ""
			flag_sms = 'false'
			flag_local = 'false'
			flag_mail = 'false'
			VcodeCreateTime = int(time.time());
			for result in results:
				if result[0] == 11: ##短信
					flag_sms = 'true'
					sql = 'select "VcodeCreateTime" from public."User" where "UserCode" =E\'%s\';' %(UserCode)
					curs.execute(sql)
					result_tmp = curs.fetchall()
					if result_tmp[0][0] == None:
						VcodeCreateTime = int(time.time() - 60);
					else:
						VcodeCreateTime = time.mktime(time.strptime(str(result_tmp[0][0]),'%Y-%m-%d %H:%M:%S')) #时间戳					
				if result[0] == 1:	##本地认证
					flag_local = 'true'
				if result[0] == 12:
					flag_mail ='true'
					sql = 'select "VcodeCreateTime" from public."User" where "UserCode" =E\'%s\';' %(UserCode)
					curs.execute(sql)
					result_tmp = curs.fetchall()
					if result_tmp[0][0] == None:
						VcodeCreateTime = int(time.time() - 60);
					else:
						VcodeCreateTime = time.mktime(time.strptime(str(result_tmp[0][0]),'%Y-%m-%d %H:%M:%S')) #时间戳	
					
			sql = 'select "VcodeCreateTime2" from public."User" where "UserCode" =E\'%s\';' %(UserCode)
			curs.execute(sql)
			result_tmp = curs.fetchall()
			if result_tmp[0][0] == None:
				VcodeCreateTime2 = int(time.time() - 60);
			else:
				VcodeCreateTime2 = time.mktime(time.strptime(str(result_tmp[0][0]),'%Y-%m-%d %H:%M:%S')) #时间戳
			return "{\"Result\":true,\"info\":{\"is_sms\":%s,\"VcodeCreateTime\":\"%s\",\"is_local\":%s,\"VcodeCreateTime2\":\"%s\",\"is_mail\":%s}}"	%(flag_sms,VcodeCreateTime,flag_local,VcodeCreateTime2,flag_mail);
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))

###发送短信
@app.route("/send_sms", methods=['GET', 'POST'])
def send_sms():	
	UserCode = request.form.get('z1')
	flag_sec = request.form.get('f1')
	if flag_sec< 0 or flag_sec == '':
		flag_sec = 0
	else:
		flag_sec = int(flag_sec)
	if flag_sec == 3:
		VerificationCode_sms = ''.join(random.sample('0123456789',6))
		VerificationCode_mail = ''.join(random.sample('0123456789',6))
		VerificationCode = VerificationCode_sms + VerificationCode_mail
	else:
		VerificationCode = ''.join(random.sample('0123456789',6))
		VerificationCode_sms = VerificationCode;
		VerificationCode_mail = VerificationCode;
		
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":\"\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			OptTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
			if flag_sec == 3 or flag_sec == 1:
				Content = "【堡垒机】 验证码为" + VerificationCode_sms+"，有效时间为10分钟，请妥善保管。";
				sql = 'insert into private."WarnPool"("Receiver","Content","Type","Ifprocess","OptTime","FromType","RuleId","IfApprove") values(E\'%s\',E\'%s\',%d,%d,E\'%s\',%d,null,null)' %(UserCode,MySQLdb.escape_string(Content).decode("utf-8"),3,0,OptTime,4)
				debug(sql)
				curs.execute(sql)
			
			if flag_sec == 3 or flag_sec == 2 :
				Content = "【堡垒机】 验证码为" + VerificationCode_mail+"，有效时间为10分钟，请妥善保管。";
				
				sql ='select "Email" from public."User" where "UserCode" =E\'%s\';' %(UserCode)		
				curs.execute(sql)
				results = curs.fetchall()
				if results[0][0] == None:
					return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败,该用户未配置邮箱(%d)\"}" %(sys._getframe().f_lineno)
				_to = results[0][0].encode('utf-8')
				debug(_to)
				curs.execute("select public.\"PGetSmtpConfig\"(null,null,null);")
				results = curs.fetchall()[0][0].encode('utf-8')
				results_json = json.loads(results)
				if len(results_json['data']) == 0:
					return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败,未配置邮件服务器(%d)\"}" %(sys._getframe().f_lineno)
				_server=_user=_pwd=_server1=_user1=_pwd1='';
				for i in results_json['data']:
					if i['Flag'] == 2:
						_server = i['SmtpServer']
						_user = i['SenderEmail']
						_pwd = i['SenderEmailPass']
					if i['Flag'] == 1:
						_server1 = i['SmtpServer']
						_user1 = i['SenderEmail']
						_pwd1 = i['SenderEmailPass']
				if _server == '':
					_server = _server1
					_user = _user1
					_pwd = _pwd1 
				
				if os.path.exists('/usr/lib64/logproxy.so') == False:
					return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
				lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
				pwd_rc4 = c_char_p()# 定义一个指针
				pwd_rc4.value = "0"*512 # 初始化 指针
				lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
				lib.decrypt_pwd.restype = None #定义函数返回值
				ret = lib.decrypt_pwd(_pwd,pwd_rc4);#执行函数
				_pwd = pwd_rc4.value #获取变量的值

				result = e_transmit(_server,_user,_pwd,_to,"验证码",Content)
				if result == 1:
					return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
				elif result == 2:
					return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
				elif result == 3:
					return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
				elif result == 4:
					return "{\"Result\":false,\"ErrMsg\":\"邮件发送超时\"}"
				
			
			sql = 'update public."User" set "VerificationCode" = E\'%s\',"VcodeCreateTime"=E\'%s\' where "UserCode" =E\'%s\';' %(VerificationCode,OptTime,UserCode)
			debug(sql)
			curs.execute(sql)		
			conn.commit();		
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))

		#----->短信登录验证

#找回密码		
@app.route("/send_sms1", methods=['GET', 'POST'])
def send_sms1():
	UserCode = request.form.get('z1')
	VerificationCode = ''.join(random.sample('0123456789',6))
	Content = "【堡垒机】 验证码为" + VerificationCode+"，有效时间为10分钟，请妥善保管。";
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":\"\"}"

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetSmsSvrConfig\"(null,null,null)")
			results = curs.fetchall()[0][0].encode('utf-8')
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))	
	results_json = json.loads(results)
	if len(results_json['data']) == 0:
		return "{\"Result\":false,\"ErrMsg\":\"短信发送失败(%d)\"}" %(sys._getframe().f_lineno)

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			OptTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
			sql = 'insert into private."WarnPool"("Receiver","Content","Type","Ifprocess","OptTime","FromType","RuleId","IfApprove") values(E\'%s\',E\'%s\',%d,%d,E\'%s\',%d,null,null)' %(UserCode,MySQLdb.escape_string(Content).decode("utf-8"),3,0,OptTime,4)
			debug(sql)
			curs.execute(sql)
			
			sql = 'update public."User" set "VerificationCode2" = E\'%s\',"VcodeCreateTime2"=E\'%s\' where "UserCode" =E\'%s\';' %(VerificationCode,OptTime,UserCode)
			curs.execute(sql)
			conn.commit()
			
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
@app.route("/send_email", methods=['GET', 'POST'])
def send_email():
	UserCode = request.form.get('z1')
	_to = request.form.get('z2')
	VerificationCode = ''.join(random.sample('0123456789',6))
	Content = "【堡垒机】 验证码为" + VerificationCode+"，有效时间为10分钟，请妥善保管。";
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":\"\"}"

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetSmtpConfig\"(null,null,null);")
			results = curs.fetchall()[0][0].encode('utf-8')
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))	
	results_json = json.loads(results)
	if len(results_json['data']) == 0:
		return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
	for i in results_json['data']:
		if i['Flag'] == 2:
			_server = i['SmtpServer']
			_user = i['SenderEmail']
			_pwd = i['SenderEmailPass']

	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			OptTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
			sql = 'update public."User" set "VerificationCode2" = E\'%s\',"VcodeCreateTime2"=E\'%s\' where "UserCode" =E\'%s\';' %(VerificationCode,OptTime,UserCode)
			curs.execute(sql)
			conn.commit()

			if os.path.exists('/usr/lib64/logproxy.so') == False:
				return "{\"Result\":false,\"info\":\"系统繁忙(%d): %s\"}" % (ERRNUM_MODULE + 0, ErrorEncode(e.args[1]))
			lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
			pwd_rc4 = c_char_p()# 定义一个指针
			pwd_rc4.value = "0"*512 # 初始化 指针
			lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
			lib.decrypt_pwd.restype = None #定义函数返回值
			ret = lib.decrypt_pwd(_pwd,pwd_rc4);#执行函数
			_pwd = pwd_rc4.value #获取变量的值

			result = e_transmit(_server,_user,_pwd,_to,"验证码",Content)
			if result == 0:
				return "{\"Result\":true}"
			elif result == 1:
				return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
			elif result == 2:
				return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
			elif result == 3:
				return "{\"Result\":false,\"ErrMsg\":\"邮件发送失败(%d)\"}" %(sys._getframe().f_lineno)
			elif result == 4:
				return "{\"Result\":false,\"ErrMsg\":\"发送超时\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
@app.route("/check_ucode", methods=['GET', 'POST'])
def check_ucode():
	UserCode = request.form.get('a0')
	uCode = request.form.get('a1')
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"info\":{\"is_sms\":false,\"VcodeCreateTime\":\"\"}}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()

			sql = 'select a."VerificationCode2",a."VcodeCreateTime2" from public."User" a where "UserCode" =E\'%s\';' %(UserCode)
			curs.execute(sql)
			Result = curs.fetchall()[0]
			ucode_tmp = Result[0]
			time_tmp = Result[1]
			if time_tmp == None:
				VcodeCreateTime = int(time.time() - 60);
			else:
				VcodeCreateTime = time.mktime(time.strptime(str(time_tmp),'%Y-%m-%d %H:%M:%S')) #时间戳
			t = time.time()
			if int(t)-int(VcodeCreateTime) > 600:
				return "{\"Result\":false,\"ErrMsg\":\"验证码错误\"}"
			else:
				if str(ucode_tmp) == str(uCode):
					ucode = UserCode
					pwd = request.form.get('a2')
					repeat = request.form.get('a3')
					if os.path.exists('/usr/lib64/logproxy.so') == False:
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.encrypt_pwd.argtypes = [c_char_p,c_char_p] #定义函数参数
					lib.encrypt_pwd.restype = None #定义函数返回值
					ret = lib.encrypt_pwd(pwd,pwd_rc4)#执行函数
					pwd = pwd_rc4.value #获取变量的值
					
					try:
						conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
					except pyodbc.Error,e:
						conn.close()
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					try:
						curs = conn.cursor()
					except pyodbc.Error,e:
						conn.close()
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
						
					sql = "select  \"OldPassword\",\"Password\" from public.\"User\" where \"UserCode\" ='%s';" %(ucode)
					try:
						curs.execute(sql)
					except pyodbc.Error,e:
						curs.close()
						conn.close()
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					results = curs.fetchall()
					
					if results == None:
						oldPwdArray = [];
					else:
						oldPwdArray = str(results[0][0]).split(',');
					Password = results[0][1];
					debug(str(oldPwdArray))
					i = 0
					if repeat != '0':
						for oldPwd in reversed(oldPwdArray):
							debug("i:%d" %i)
							debug("repeat:%s" %repeat)
							if i < int(repeat)+1:
								i += 1
								#if str(oldPwd) == str(pwd_rc4.value):
								debug(str(oldPwd))
								if str(oldPwd) == str(pwd):
									if i == 1:
										return "{\"Result\":false,\"ErrMsg\":\"不能和当前密码一致\"}"							
									return "{\"Result\":false,\"ErrMsg\":\"密码不能与前%s次密码重复\"}" % (repeat)
									
					if len(oldPwdArray) == 6:
						del oldPwdArray[0]
					oldPwdArray.append(pwd)
					OldPassword = str(','.join(oldPwdArray))

					nowTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')#现在
					sql = "update public.\"User\" set \"Password\"= E'%s',\"LastPwdModifyTime\"=E'%s',\"UserStatus\"=1,\"OldPassword\"=E'%s' where \"UserCode\" ='%s';" %(pwd,nowTime,OldPassword,ucode)
					try:
						curs.execute(sql)
					except pyodbc.Error,e:
						curs.close()
						conn.close()
						return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % ( ErrorEncode(e.args[1]),sys._getframe().f_lineno)
					
					conn.commit();
					curs.close();
					conn.close();
					return "{\"Result\":true,\"ErrMsg\":\"\"}"
					return "{\"Result\":true}"
				else:
					return "{\"Result\":false,\"ErrMsg\":\"验证码错误\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))

def get_usbkey(order_list,usbkey_order,pW):
	pwdlist = [];
	try:
		i = order_list.index(None)
		prev_list = order_list[:i];
		slen = 0;
		next_list = order_list[(i+1):];
		for i, element in enumerate(prev_list):
			if (usbkey_order-1) == i:
				return pW[slen:element+slen]
			pwdlist.append(pW[slen:element+slen]);
			slen +=element;

		#print pwdlist
		slen = 0;
		pwd_next = []
		for element in reversed(next_list):
			#print element
			if slen == 0:
				pwd_next.append(pW[(0-element):]);
			else:
				pwd_next.append(pW[(0-element + slen):slen])
			slen +=(0-element);
		#print list(reversed(pwd_next))
		#print pW[len(''.join(pwdlist)):(0-len(''.join(list(reversed(pwd_next)))))]
		if len(pwd_next) == 0:
			pwdlist.append(pW[len(''.join(pwdlist)):])
		else:
			pwdlist.append(pW[len(''.join(pwdlist)):(0-len(''.join(list(reversed(pwd_next)))))])
		allpwdlist = pwdlist+list(reversed(pwd_next))
		return allpwdlist[usbkey_order-1]
	except:
		pwd_list=[];
		slen=0;
		for i, element in enumerate(order_list):
			if (usbkey_order-1) == i:
				return pW[slen:element+slen]
			pwdlist.append(pW[slen:element+slen]);
			slen +=element;
		return pwd_list[usbkey_order-1]
			
	
	
###获取usbkey和证书
@app.route("/get_usbkey_cert", methods=['GET', 'POST'])
def get_usbkey_cert():	
	
	UserCode = request.form.get('a0')
	pW = request.form.get('a1')
	if pW < 0 or pW == None:
		pW = '';
	usbkey_order = int(request.form.get('a2'))
	UserId = 0;
	usbkey='';
	auth_user = request.form.get('a3');
	login_user = request.form.get('a4')
	
	pW = base64.b64decode(pW);
	if auth_user < 0 or auth_user =='':
		auth_user = 0;
	else:
		auth_user= 1;
		
	if login_user < 0 or login_user =='':
		login_user = 0;
	else:
		login_user= 1;
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			
			sql = 'select "UserId" from public."User" where "UserCode" =E\'%s\';' %(UserCode)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			UserId = results[0][0]
			if usbkey_order > 0:
				sql = 'select public."GetPwdSeparator"(E\'%s\');' %(UserCode)
				debug(sql)
				curs.execute(sql)
				results = curs.fetchall()
				debug(str(results))
				if results == None:
					usbkey = pW
				elif results[0][0] == None:
					###长度分隔
					if len(results) == 1 or len(results) == 2: 
						usbkey = pW
					else:
						em_list = []					
						for s in results[1:]:
							if s[0] != None:
								s[0] = int(s[0])
							em_list.append(s[0])						
						usbkey = get_usbkey(em_list,usbkey_order,pW);
				else:
					###字符分隔
					tm = pW.split(results[0][0])
					if len(tm) == 1:
						usbkey = pW
					else:
						try:
							usbkey = tm[usbkey_order-1];
						except:
							usbkey = pw;
			
			
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))
		
	fdir = "/usr/ssl/usrca/cert_%d.crt" %(UserId)	
		
	if login_user == 1: ##下发任务 获取用户证书
		task_content = '[global]\nclass = taskUserKey\ntype = getUserKey\nuserId = %d\nuserName = %s' %(UserId,UserCode)
		debug(task_content)
		if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
			conn.rollback()
			return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE + 40,ErrorEncode(task_client.ErrMsg))
		t = 0;
		while(True):
			if os.path.exists(fdir) == False:
				time.sleep(1)
			else:
				break;
			t +=1;
			if t > 10:
				return "{\"Result\":false,\"ErrMsg\":\"用户证书生成失败(%d)\"}" %(ERRNUM_MODULE + 42)
			
	if os.path.exists(fdir) == False:
		return "{\"Result\":false,\"ErrMsg\":\"用户证书不存在(%d)\"}" %(ERRNUM_MODULE + 42)
		
	if auth_user == 0:	
		f = open("/usr/ssl/usrca/cert_%d.crt" %(UserId),'r')
	else:
		f = open("/usr/ssl/usrca/userca.crt",'r')
	lines = f.readlines()
	f.close()
	Content ='';
	if ("-----BEGIN CERTIFICATE-----\n" in lines) and ("-----END CERTIFICATE-----\n" in lines):
		flag = 0

		for i in lines:
			if i == "-----BEGIN CERTIFICATE-----\n":
				flag = 1
			elif i == "-----END CERTIFICATE-----\n":
				Content += "-----END CERTIFICATE-----\n"
				flag = 0
			if flag == 1:
				Content += i
	else:
		return "{\"Result\":false,\"ErrMsg\":\"用户证书错误(%d): %s\"}" %(ERRNUM_MODULE + 43)
	###从 密码pW中 获取usbkey
	return json.dumps({"Result":True,"usbkey":usbkey,"Content":base64.b64encode(Content),"UserId":UserId})

###获取证书
@app.route("/GetCert", methods=['GET', 'POST'])
def GetCert():	
	'''
	headers  = str(request.headers) ;
	debug(headers)
	if str(headers).find('Sesstime')< 0:
		return '',400;
	'''
	try:
		headers  = str(request.headers) ;
		if str(headers).find('a1')< 0:
			sesstime = request.args.get('a1');
		else:
			sesstime = headers.split('a1',0)[1].split()[1];
		
		if(str(sesstime).isdigit() == False):
			return '',403
		
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			
			sql = 'select "CertInfo" from private."USBKeyResult" where "SessTime" =E\'%s\';' %(sesstime)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()
			CertInfo = results[0][0]
			return CertInfo,200
	except pyodbc.Error,e:
		return '',400
	
###设置根证书
@app.route("/set_user_crt", methods=['GET', 'POST'])
def set_user_crt():	
	task_content = '[global]\nclass = taskUserKey\ntype = setUserKey\n;'
	debug(task_content)
	if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
		conn.rollback()
		return "{\"Result\":false,\"info\":\"任务下发异常(%d): %s\"}" %(ERRNUM_MODULE + 40,ErrorEncode(task_client.ErrMsg))
	

@app.route("/get_first_time", methods=['GET', 'POST'])
def get_first_time():		
	UserCode = request.form.get('a0')
	with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
		curs = conn.cursor()
		
		sql='select "LastLoginTime" from "User" where "UserCode" = E\'%s\';'%(UserCode)
		debug(sql)
		curs.execute(sql)
		results = curs.fetchall()
		LastLoginTime = results[0][0]
		if LastLoginTime == None:
			return 'true'
		else:
			return 'false'

##获取 第三方key ca根证书

@app.route("/GetCaCert", methods=['GET', 'POST'])
def GetCaCert():
	headers  = str(request.headers) ;
	debug(headers)
	'''
	if str(headers).find('Name')< 0:
		return '',400;
	
	Name = headers.split('Name')[1].split()[1];
	'''
	if headers.find("a1") < 0:
		Name = request.args.get('a1')
	else:
		Name = headers.split('a1',0)[1].split()[1];
	
	try:
		if os.path.exists('/usr/etc/'+Name):
			fp = open('/usr/etc/'+Name,'r');
			a = base64.b64encode(fp.read());
			return a,200
		else:
			return '',400
	except pyodbc.Error,e:
		return '',400
	
##找回密码相关函数
@app.route("/get_user_info", methods=['GET', 'POST'])
def get_user_info():
	UserCode = request.form.get('a0')
	if checkaccount(UserCode) == False:
		return "{\"Result\":true,\"ErrMsg\":[]}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select "UserId" from public."User" where "UserCode" =E\'%s\';' %(MySQLdb.escape_string(UserCode))
			curs.execute(sql)
			uid = curs.fetchall()
			if uid == []:
				return "{\"Result\":false,\"ErrMsg\":\"用户不存在%s\"}" % (ErrorEncode(e.args[1]))			
			else:
				uid = uid[0][0]
			sql = "select public.\"PGetUser\"(%d,0);" %(uid)
			curs.execute(sql)
			results = curs.fetchall()[0][0].encode('utf-8')
			return "{\"Result\":true,\"info\":%s}" % (results)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d): %s\"}" % (ERRNUM_MODULE + 3, ErrorEncode(e.args[1]))

@app.route("/iai", methods=['GET', 'POST'])
def if_mac_and_if_manager():
	UserCode = request.form.get('c1')
	if checkaccount(UserCode) == False:
		return '',403
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			sql = 'select public."PMACLimit"(\'%s\');' %(MySQLdb.escape_string(UserCode))
			curs.execute(sql)
			results = curs.fetchall()
			if_mac_limit = results[0][0]	
			_power=PGetPermissions(UserCode)
			_power_json = json.loads(_power);
			if_manager = 'false'
			if_operation ='false'
			for one in _power_json:
				if one['SystemMenuId'] == 7 and one['Mode'] >0:
					if_operation = 'true'
				else:
					if one['Mode'] >0:
						if_manager = 'true'
			sql = 'select "UpdateNoAlert" from public."User" where "UserCode"=E\'%s\';' %(UserCode)
			curs.execute(sql)
			results = curs.fetchall()
			if results:
				UpdateNoAlert = results[0][0]
			else:
				UpdateNoAlert = 0;
			if  UpdateNoAlert == None:
				UpdateNoAlert = 0;
			return "{\"Result\":true,\"imi\":%d,\"UpdateNoAlert\":%d}" % (if_mac_limit,UpdateNoAlert)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (ERRNUM_MODULE + 3)

@app.route('/check_permission',methods=['GET', 'POST'])
def check_permission():
	UserCode = request.form.get('a0')

	try:
		_power=PGetPermissions(UserCode)
		_power_json = json.loads(_power);
		if_operation ='false'
		if_manager = 'false'
		if_exist = 'false'
		auth_str = ''
		auth_array = []
		if len(_power_json) == 0:#没有这个用户
		 if_exist = 'false'
		else:
			if_exist = 'true'
			try:
				with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
					curs = conn.cursor()
					sql = 'select a."UserStatus" from public."User" a where a."UserCode"=\'%s\'' %(UserCode)
					curs.execute(sql)
					results = curs.fetchall()
					status = results[0][0]
					if status == 0 or status == 6 or status == 7:
						if_exist = 'false' #停用 过期
					else:
						for one in _power_json:
							if one['SystemMenuId'] == 7 and one['Mode'] >0:#是运维用户
								if_operation = 'true'
							else:
								if_manager = 'true'

					sql = 'select a."AuthTypeId" from public."User" a where a."UserCode"=\'%s\'' %(UserCode)
					curs.execute(sql)
					authtypeId = curs.fetchall()[0][0]
					isdefault = 'false'
					if authtypeId == None: #默认认证方式
						sql = 'select a."AuthTypeId" from public."AuthType" a where a."IsDefault"=True'
						curs.execute(sql)
						authtypeId = curs.fetchall()[0][0]
						isdefault = 'true'
					sql='select public."PGetAuthType"(%s,false,null,null,null,null,null);' %(str(authtypeId))
					curs.execute(sql)
					results = curs.fetchall()[0][0]

					result_json = json.loads(results)
					for dat in result_json['data']:
						for s in dat['Set']:
							sql = "select \"AuthMode\" from public.\"AuthModule\" where \"AuthModuleId\"=%d;" %(s['AuthModuleId'])
							debug(sql)
							curs.execute(sql)
							s['AuthMode'] = curs.fetchall()[0][0]
							#1.本地认证 2. AD域 3. openldap 4.Radius 9.USBKEY 11.短信 12.邮箱 13.指纹
							auth_array.append(str(s['AuthMode']))
					auth_str = ','.join(auth_array)
			except pyodbc.Error,e:
				return "{\"Result\":false,\"ErrMsg\":\"系统异常(%d)\"}" % (ERRNUM_MODULE + 3)

		return "{\"Result\":true,\"if_exist\":\"%s\",\"if_operation\":\"%s\",\"if_manager\":\"%s\",\"auth_type\":\"%s\"}" %(if_exist,if_operation,if_manager,auth_str)
	except Exception,e:
		return "{\"Result\":false,\"ErrMsg\":\"请求用户信息失败\"}"

		
app.register_blueprint(left_index)
app.register_blueprint(access_control)
app.register_blueprint(connection_list)
app.register_blueprint(host_add)
app.register_blueprint(domain_list)
app.register_blueprint(user_add)
app.register_blueprint(user_list)
app.register_blueprint(authtype_list)
app.register_blueprint(pwd_export_py)
app.register_blueprint(b_user_manage)
app.register_blueprint(b_role_manage)
app.register_blueprint(b_host_manage)
app.register_blueprint(b_auth_manage)
app.register_blueprint(access_set)
app.register_blueprint(b_proto_manage)
#app.register_blueprint(system_outline_data)
app.register_blueprint(proto_control)
#bhacc
app.register_blueprint(bhacc)
app.register_blueprint(user_data)
app.register_blueprint(ip_list)
app.register_blueprint(cmdset)
app.register_blueprint(cmdset_add1)
app.register_blueprint(data_distribution)
app.register_blueprint(certificate_generation)
app.register_blueprint(devicetype)
app.register_blueprint(time_list)
app.register_blueprint(mac)
app.register_blueprint(macset_add)
app.register_blueprint(eventinfo_list)
app.register_blueprint(licensing)
app.register_blueprint(account)
app.register_blueprint(account_add)
app.register_blueprint(pwdchange_list)
app.register_blueprint(approve_set)
app.register_blueprint(client_list)
app.register_blueprint(host_test)
app.register_blueprint(hostgroup_list)
#app.register_blueprint(protocol_data)
app.register_blueprint(pwdstrategy_change)
app.register_blueprint(export_list)
app.register_blueprint(service_data)
app.register_blueprint(syswarn)
app.register_blueprint(route_list)
app.register_blueprint(acc_client)
app.register_blueprint(acc_client_add)
app.register_blueprint(pwd_manage)
app.register_blueprint(hostpwdstrategy_change)
app.register_blueprint(globalstrategy_change)
app.register_blueprint(time_config)
app.register_blueprint(access_auth_z)
app.register_blueprint(manageauth_add)
app.register_blueprint(time_out_change)
app.register_blueprint(cmdAuth)
app.register_blueprint(manage_accessauth)
app.register_blueprint(manage_workorder)
app.register_blueprint(pwdresult_list)
app.register_blueprint(colony_list)
app.register_blueprint(work_order_z)
app.register_blueprint(authmodule_change)
app.register_blueprint(AccessProtocol_z)
app.register_blueprint(password_entry)
app.register_blueprint(mailserver)
app.register_blueprint(smsm)
app.register_blueprint(syslog)
app.register_blueprint(snmp)
#相关下载
app.register_blueprint(related_downloads)
#别名管理
app.register_blueprint(alias_show)
#access_global_setting
app.register_blueprint(access_global_setting)
app.register_blueprint(smssvr)
app.register_blueprint(config_manage)
#app.register_blueprint(module_app)
app.register_blueprint(module_app_set)
app.register_blueprint(system_update)
app.register_blueprint(data_manage)
app.register_blueprint(find_host)
app.register_blueprint(pwdchange_mode_py)
app.register_blueprint(down_file)
app.register_blueprint(down_file_user)
app.register_blueprint(import_file)
app.register_blueprint(import_file_user)
app.register_blueprint(pwd_setting_py)
app.register_blueprint(search_log)
app.register_blueprint(load_account)
app.register_blueprint(protocol_lxz)
app.register_blueprint(get_host_msg)
app.register_blueprint(pending_file)
app.register_blueprint(import_taskfile)
app.register_blueprint(usbkey_c)
app.register_blueprint(search)
app.register_blueprint(history_task)
app.register_blueprint(get_qrcode)
app.register_blueprint(history_report)
#app.register_blueprint(upload)
app.register_blueprint(system_power)
app.register_blueprint(ftpserver)
app.register_blueprint(host_grouping)
app.register_blueprint(batch_operation)
app.register_blueprint(analysis)
app.register_blueprint(playback)
app.register_blueprint(sshkey)
app.register_blueprint(dns_list)
app.register_blueprint(tran)
app.register_blueprint(connect_session)
app.register_blueprint(cluster)
if __name__  == '__main__':
	app.run(debug=True)
