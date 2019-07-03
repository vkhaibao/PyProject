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
from comm_function import get_user_perm_value
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
client_list = Blueprint('client_list',__name__)

SIZE_PAGE = 20
def debug(c):
	return 0
        path = "/var/tmp/debugrxl.txt"
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
#跳转至客户端IP范围
@client_list.route('/client_show',methods=['GET','POST'])
def client_show():
	sess=request.form.get('se')
	if sess<0:
		sess=request.args.get('se')
		if sess<0:
			sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_server=0
	for i in perm_json:
		if i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm_server:
			perm_server=i['Mode']
		elif i['SubMenuId']==13 and i['SystemMenuId']==3 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3:
			# perm=2
			if perm_server<i['Mode']:
				perm_server=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3:
			# perm=2
			if perm_server<i['Mode']:
				perm_server=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==18 and i['SystemMenuId']==3:
			# perm=2
			if perm_server<i['Mode']:
				perm_server=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif i['SubMenuId']==20 and i['SystemMenuId']==4 and i['Mode']>perm_server:
			perm_server=i['Mode']
		elif i['SubMenuId']==21 and i['SystemMenuId']==4 and i['Mode']>perm_server:
			perm_server=i['Mode']
		if perm==2 and perm_server==2:
			break
	return render_template('client_list.html',se=sess,perm_server=perm_server,paging="1",search_typeall="",e=':',perm=perm)

#1创建 2编辑 3列表
@client_list.route('/client_handle',methods=['GET','POST'])
def client_handle():
	tasktype = request.form.get("tasktype")
	clientId = request.form.get("clientId")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	if e<0 or e==None:
		e=''
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or tasktype == "2":
		t = "client_add.html"
	if tasktype == "3":
		t = "client_list.html"
		clientId="0"
	if tasktype and str(tasktype).isdigit() == False:
		return '',403	
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if clientId and str(clientId).isdigit() == False:
		return '',403
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
	e = e.replace('(','').replace(')','');
		
	sess=request.form.get('se')
	if sess<0:
		sess=request.args.get('se')
		if sess<0:
			sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_server=0
	for i in perm_json:
		if i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm_server:
			perm_server=i['Mode']
		if i['SubMenuId']==13 and i['SystemMenuId']==3 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3:
			# perm=2
			if perm_server<i['Mode']:
				perm_server=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3:
			if i['Mode']>perm:
				perm=i['Mode']
			if i['Mode']>perm_server:
				perm_server=i['Mode']
		elif  i['SubMenuId']==18 and i['SystemMenuId']==3:
			if i['Mode']>perm:
				perm=i['Mode']
			if i['Mode']>perm_server:
				perm_server=i['Mode']
		if i['SubMenuId']==20 and i['SystemMenuId']==4 and i['Mode']>perm_server:
                        perm_server=i['Mode']
		if i['SubMenuId']==21 and i['SystemMenuId']==4 and i['Mode']>perm_server:
                        perm_server=i['Mode']
		if perm==2 and perm_server==2:
			break
	return render_template(t,perm=perm,se=sess,tasktype=tasktype,perm_server=perm_server,clientId=clientId,paging=paging,search_typeall=search_typeall,e=e)
#显示 or 分页 or 搜索
@client_list.route('/get_client_list',methods=['GET', 'POST'])
def get_client_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	clientId = request.form.get('a1')
	search_typeall = request.form.get('a2')
	dsc = request.form.get('dsc')
	
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if clientId and str(clientId).isdigit() == False:
		return '',403
	if dsc and dsc != 'false' and dsc!='true':
		return '',403
		
	if dsc < 0 or dsc =='':
		dsc = 'false'
	
	if search_typeall<0:
		search_typeall=""
	if clientId<0 or clientId=="0" or clientId=="":
		clientId="null"
	if sess < 0:
		sess = ""
	
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
	Name=""
	Description=""
	Ip=''
	Mac=''
	searchstring=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="ClientScopeName":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			#searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="IP":
			Ip=Ip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="MAC":
			Mac=Mac+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	if Name=="":
		Name="null"
	else:
		Name="'%s'"%(Name[:-1])
	if searchstring!="":
		searchstring=searchstring[:-1]
	if Ip!="":
		Ip=Ip[:-1]
	if Mac!="":
		Mac=Mac[:-1]
	searchconn={}
	searchconn['searchstring']=searchstring
	searchconn['Ip']=Ip
	searchconn['Mac']=Mac
	searchconn=json.dumps(searchconn)
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetClientScope(clientscopeid,clientscopename,limitrow,offsetrow)
			sql="select public.\"PGetClientScope\"(%s,%s,%s,%s,%s);"%(clientId,Name,num,paging,dsc)
			# sql="select public.\"PGetClientScope\"(%s,%s,%s,%s,'%s');"%(clientId,Name,num,paging,searchconn)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#创建 or 编辑
@client_list.route('/add_client',methods=['GET', 'POST'])
def add_client():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client = request.form.get('a1')
	client=str(client)
	client_json=json.loads(client)
	fid = request.form.get('a3')
	cstype = request.form.get('a2')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>客户端集合'
	if session < 0:
		session = ""
	if cstype < 0 or cstype=="":
		cstype = "0"
	if fid < 0 or fid=="":
		fid = "null"
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
		
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(client);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveClientScope(jsondata,cstype,fid)
			sql="select public.\"PSaveClientScope\"(E'%s',%s,%s);" %(MySQLdb.escape_string(client).decode("utf-8"),cstype,fid)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if str(client_json['ClientScopeId'])=='0':
				oper='创建客户端集合：%s'%client_json['ClientScopeName']
			else:
				oper='编辑客户端集合：%s'%client_json['ClientScopeName']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			else:
				oper_arr=[]
				if client_json['IsApplyToServerScope']:
					oper_arr.append('应用于服务器集合')
				else:
					oper_arr.append('不应用于服务器集合')
				ip_arr=[]
				ipset_arr=[]
				mac_arr=[]
				macset_arr=[]
				for i in client_json['IPList']['Set']:
					if i['StartIP']==i['EndIP']:
						ip_arr.append(i['StartIP'])
					else:
						ipset_arr.append(i['StartIP']+'-'+i['EndIP'])
				for i in client_json['MACList']['Set']:
					if i['StartMACAddress']==i['EndMACAddress']:
						mac_arr.append(i['StartMACAddress'])
					else:
						mac_arr.append(i['StartMACAddress']+'-'+i['EndMACAddress'])
				if len(ip_arr)!=0:
					oper_arr.append('IP地址：%s'%('、'.join(ip_arr)))	
				if len(ipset_arr)!=0:
					oper_arr.append('IP区间：%s'%('、'.join(ipset_arr)))	
				if len(mac_arr)!=0:
					oper_arr.append('MAC地址：%s'%('、'.join(mac_arr)))	
				if len(macset_arr)!=0:
					oper_arr.append('MAC区间：%s'%('、'.join(macset_arr)))
				oper+=('（'+'，'.join(oper_arr)+'）')
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
				return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除认证方式
@client_list.route('/del_client',methods=['GET', 'POST'])
def del_client():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	cstype = request.form.get('a2')
	fid = request.form.get('a3')
	session = request.form.get('a0')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>客户端集合'
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	if fid < 0 or fid=="":
		fid = "null"
	if cstype < 0 or cstype=="":
		cstype = "0"
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			all_arr=[]
			success_arr=[]
			fail_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				all_arr.append(id_arr[1])
				value=int(id_arr[0])
				# PDeleteClientScope(clientscopeid,cstype,fid)
				sql = "select public.\"PDeleteClientScope\"(%d,%s,%s);" % (value,cstype,fid)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_num+=1
					fail_arr.append(id_arr[1])
					#return result
				else:
					success_num+=1
					fail_arr.append(id_arr[1])
					conn.commit()
			oper='删除客户端集合：%s'%('、'.join(all_arr))
			if (success_num+fail_num)==1:
				if success_num==1:
					mesg='成功'
				else:
					mesg=result_json['ErrMsg']
			else:
				if fail_num==0:
					mesg='成功'
					# mesg='成功：%s'%('、'.join(success_arr))
				elif success_num!=0:
					mesg='成功：%s，失败：%s'%('、'.join(success_arr),'、'.join(fail_arr))
				else:
					mesg='失败：%s'%('、'.join(fail_arr))
			if not system_log(system_user,oper,mesg,module_name):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}" %(success_num,fail_num,mesg)  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
	
