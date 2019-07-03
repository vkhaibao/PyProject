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
import base64
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from ctypes import *
from urllib import unquote
from logbase import defines
from logbase import common
from htmlencode import parse_sess
from htmlencode import check_role
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from Crypto.Cipher import DES3
from htmlencode import checkaccount

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
sshkey = Blueprint('sshkey',__name__)

SIZE_PAGE = 20
def debug(c):
    return 0
    path = "/var/tmp/debug_zqy_sshkey.txt"
    fp = open(path,"a+")
    if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
	
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
	return newStr;	

#跳转至密钥管理
@sshkey.route('/sshkey_show',methods=['GET', 'POST'])
def sshkey_show():		
	sess = request.form.get('se')
	if sess < 0:
		#sess = ""
		sess=request.args.get('se')
		if sess<0:
			sess=''
	type_value=request.form.get('type')
	if type_value<0:
		type_value=request.args.get('type')
		if type_value<0:
			type_value=''
	return render_template('sshkey.html',se=sess,paging="1",search_typeall='',e=':',type_value=type_value)

#1创建 2列表
@sshkey.route('/sshkey_handle',methods=['GET','POST'])
def sshkey_handle():
	tasktype = request.form.get("tasktype")
	sshkey_id = request.form.get("sshkey_id")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	type_value=request.form.get('type')
	
	if tasktype and str(tasktype).isdigit() == False:
		return '',403
	if type_value and str(type_value).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	search_typeall = search_typeall.replace('(','').replace(')','');
	if sshkey_id and str(sshkey_id).isdigit() == False:
		return '',403
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
	e = e.replace('(','').replace(')','');
		
		
	if tasktype < 0:
		tasktype = "1"
	if e < 0 or e==None:
		e = ":"
	if search_typeall < 0 or search_typeall==None:
		search_typeall = ""
	if tasktype == "1" or tasktype == "2":
		t = "sshkey_add.html"
	if tasktype == "3":
		t = "sshkey.html"
		sshkey_id="0"
	return render_template(t,type_value=type_value,tasktype=tasktype,sshkey_id=sshkey_id,paging=paging,search_typeall=search_typeall,e=e)	

#编辑跳转
@sshkey.route('/sshkey_update',methods=['GET','POST'])
def sshkey_update():
	tasktype = request.form.get("tasktype")
	sshkey_id = request.form.get("sshkey_id")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	type_value=request.form.get('type')
	keytypeid = request.form.get("keytypeid")
	
	if keytypeid and str(keytypeid).isdigit() == False:
		return '',403
	if tasktype and str(tasktype).isdigit() == False:
		return '',403
	if type_value and str(type_value).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	search_typeall = search_typeall.replace('(','').replace(')','');
	if sshkey_id and str(sshkey_id).isdigit() == False:
		return '',403
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
	e = e.replace('(','').replace(')','');
	
	if tasktype < 0:
		tasktype = "1"
		
	if 	tasktype != "2":
		keyname = request.form.get("keyname")
		keytype = request.form.get("keytype")
		keytypeid = request.form.get("keytypeid")
		keycontent = request.form.get("keycontent")
		enable = request.form.get("enable")
		enableid = request.form.get("enableid")
		passwork=request.form.get('passwork')
	else:
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
				sql = 'select "KeyName","KeyContent", "KeyType","IfValid","Password" from public."SshKey" where "SshKeyId"=%s ' %(sshkey_id)
				curs.execute(sql)
				results = curs.fetchall()
				keyname = results[0][0]
				keycontent = results[0][1].encode('utf-8');
				
				key='SafeT1Ba5eSafeT1'
				des3=DES3.new(key,DES3.MODE_ECB)
				keycontent=base64.b64decode(keycontent)
				keycontent=des3.decrypt(keycontent)
				while True:
					c=keycontent[-1];
					if ord(c)==0:
						keycontent=keycontent[:-1]
					else:
						break
				keytype = results[0][2]		
				enable = results[0][3]
				enableid = 0;
				passwork =  results[0][4];
				if passwork:
					lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
					pwd_rc4 = c_char_p()# 定义一个指针
					pwd_rc4.value = "0"*512 # 初始化 指针
					lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
					lib.decrypt_pwd.restype = None #定义函数返回值
					ret = lib.decrypt_pwd(passwork,pwd_rc4);#执行函数
					passwork = pwd_rc4.value #获取变量的值
				
		except pyodbc.Error,e:
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		
	if e < 0 or e==None:
		e = ":"
	if search_typeall < 0 or search_typeall==None:
		search_typeall = ""
	if tasktype == "1":
		t = "sshkey_add.html"
	if tasktype == "2":
		t = "sshkey_update.html"		
		
	if tasktype == "3":
		t = "sshkey.html"
		sshkey_id="0"
		
		
	pw_value=passwork
	return render_template(t,type_value=type_value,tasktype=tasktype,sshkey_id=sshkey_id,paging=paging,search_typeall=search_typeall,e=e,keyname=keyname,keytype=keytype,keytypeid=keytypeid,keycontent=keycontent,enable=enable,enableid=enableid,passwork=passwork,pw_value=pw_value)		

def init_str(s):
    l=len(s) % 16
    #print 'l',l
    if l!=0:
        c=16-l
        s+=chr(0)*c
    return s
#创建和编辑
@sshkey.route('/add_sshkey',methods=['GET','POST'])
def add_sshkey():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	sshkey = request.form.get('a1')
	type_name=request.form.get('a10')
	md5_str=request.form.get('m1')
	if type_name=='1':
		type_name='运维管理>密钥管理'
	else:
		type_name='访问工具>密钥管理'
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

	# if check_role(system_user,'管理授权') == False:
	# 	return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
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
				if not system_log(system_user,oper,result_json['ErrMsg'],type_name):
                			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				#return result 
				if not system_log(system_user,oper,'成功',type_name):
                			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#id位置
@sshkey.route('/PGetRecordRownum',methods=['GET','POST'])
def PGetRecordRownum():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 1000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	recordid = request.form.get('a1')
	tableid = request.form.get('a2')
	pwdmodtype= request.form.get('a3')
	if sess<0:
		sess=""
	if pwdmodtype<0:
		pwdmodtype="null"
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
	if pwdmodtype<0:
		sql="select public.\"PGetRecordRownum\"(%s,%s);" %(recordid,tableid)
	elif tableid=='17' or tableid=='31' or tableid=='8':
		sql="select public.\"PGetRecordRownum\"(%s,%s,%s,'%s');" %(recordid,tableid,pwdmodtype,system_user)
	else:
		sql="select public.\"PGetRecordRownum\"(%s,%s,%s);" %(recordid,tableid,pwdmodtype)
	
	# PSaveConnParam(connection)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%d}" %(result)
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示密钥管理列表 or 分页 or 搜索
@sshkey.route('/get_sshkey',methods=['GET', 'POST'])
def get_sshkey():
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
	dsc = request.form.get('dsc')
	
	if KeyType and str(KeyType).isdigit() == False:
		return '',403
	if limitrow and str(limitrow).isdigit() == False:
		return '',403
	if offsetrow and str(offsetrow).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if sshkeyid and str(sshkeyid).isdigit() == False:
		return '',403
	if dsc and dsc != 'false' and dsc!='true':
		return '',403	
	
	if KeyType=='' or KeyType<0:
		KeyType='null'
	sshkeyname = ""
	IfValid ="null"
	#KeyType ="null"
	keyname = ""
	keycontent = ""
	all = ""
	
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
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
			sql="select public.\"PGetSshKey\"('%s',%s,%s,%s,%s,E'%s',%s);"% (usercode,KeyType,IfValid,limitrow,offsetrow,searchconn,dsc)
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
	
#删除密钥
@sshkey.route('/del_sshkey',methods=['GET', 'POST'])
def del_sshkey():
	debug('del_sshkey')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	type_name=request.form.get('a10')
	if type_name=='1':
                type_name='运维管理>密钥管理'
        else:
                type_name='访问工具>密钥管理'	
	debug(id_str)
	if session <0 :
		sesson=""
	if id_str <0 :
		id_str=""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	ids = id_str.split(',')
	debug(str(ids))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			all_arr=[]
			succ_num=0
			fail_num=0
			succ_arr=[]
			fail_arr=[]
			for sshkeyid in ids:
				debug('1111')
				id_arr=sshkeyid.split('\t')
				all_arr.append(id_arr[1])
				sshkeyid=int(id_arr[0])
				
				#PDeleteSshKey(sshkeyid)
				sql = "select public.\"PDeleteSshKey\"(%d);" % (sshkeyid)
				debug(sql)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_arr.append(id_arr[1])
					fail_num+=1
				else:
					succ_num+=1
					succ_arr.append(id_arr[1])
			oper='删除密钥：%s'%('、'.join(all_arr))
		        debug(str(oper))
			if (succ_num+fail_num)==1:
                		if succ_num==1:
                    			mesg='成功'
                		else:
                    			mesg=result_json['ErrMsg']
           	 	else:
                		if fail_num==0:
                    			mesg='成功'
                    			# mesg='成功：%s'%('、'.join(success_arr))
                		elif succ_num!=0:
                    			mesg='成功：%s，失败：%s'%('、'.join(succ_arr),'、'.join(fail_arr))
				else:
                    			mesg='失败：%s'%('、'.join(fail_arr))
            		debug(str(mesg))
			if not system_log(system_user,oper,mesg,type_name):
                		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
            		conn.commit()
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}"%(succ_num,fail_num,mesg)	
			conn.commit()
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
