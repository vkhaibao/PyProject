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
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from comm_function import get_user_perm_value
from htmlencode import parse_sess,check_role
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
hostgroup_list = Blueprint('hostgroup_list',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
        path = "/var/tmp/dccp123.txt"
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
	return newStr;	
#跳转至管理范围
@hostgroup_list.route('/hostgroup_show',methods=['GET','POST'])
def hostgroup_show():
	sess=request.form.get('se')
	if sess<0:
		sess=request.args.get('se')
		if sess<0:
			sess = ""
	a10 = request.form.get("a10")
	if a10<0:
		a10= request.args.get("a10")
		if a10<0:
			a10='运维管理-服务器集合'
		else:
			a10='密码管理-服务器集合'
	else:
		a10='密码管理-服务器集合'
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(sess,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_client=0
	for i in perm_json:
		if i['SubMenuId']==13 and i['SystemMenuId']==3 and i['Mode']>perm_client:
			perm_client=i['Mode']
		elif i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3:
			# perm=2
			if perm_client<i['Mode']:
				perm_client=i['Mode']
			
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3:
			# perm=2
			if perm_client<i['Mode']:
				perm_client=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==18 and i['SystemMenuId']==3:
			# perm=2
			if perm_client<i['Mode']:
				perm_client=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==20 and i['SystemMenuId']==4 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		elif  i['SubMenuId']==21 and i['SystemMenuId']==4 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		if perm==2 and perm_client==2:
			break
	return render_template('hostgroup_list.html',perm_client=perm_client,se=sess,paging="1",search_typeall="",e=':',perm=perm,module_name=a10)

#获取改组下所有主机组
@hostgroup_list.route('/get_all_hg',methods=['GET','POST'])
def get_all_hg():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	hg_id = request.form.get('a1')
	hg_id=int(hg_id)
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
	hg_arr=[]
	hg_test_arr=[]
	hg_test_arr.append(hg_id)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			while True:
				hg_result_arr=[]
				for i in hg_test_arr:
					debug(str(i))
					sql='select h."HGId" from public."HGroup" h where h."ParentHGId"=%d;'%i
					debug(sql)
					curs.execute(sql)
					result = curs.fetchall()
					if len(result)>0:
						for item in result:
							hg_result_arr.append(item[0])
				hg_arr.extend(hg_test_arr)	
				debug(str(hg_test_arr))	
				debug(str(hg_result_arr))	
				debug(str(len(hg_result_arr)))	
				if len(hg_result_arr)>0:
					hg_test_arr=hg_result_arr
					hg_result_arr=[]
				else:
					break
				debug(str(hg_test_arr))	
				debug(str(hg_result_arr))
		return "{\"Result\":true,\"info\":%s}" %(str(hg_arr))  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

#1创建 2编辑 3列表
@hostgroup_list.route('/server_handle',methods=['GET','POST'])
def server_handle():
	tasktype = request.form.get("tasktype")
	serverId = request.form.get("serverId")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	a10 = request.form.get("a10")
	if a10<0:
		a10= request.args.get("a10")
		if a10<0:
			a10='运维管理-服务器集合'
		#else:
		#	a10='密码管理-服务器集合'
	#else:
	#	a10='密码管理-服务器集合'
	e = request.form.get("e")
	se = request.form.get("se")
	if e<0:
		e=''
	if se<0:
		se=request.args.get('se')
		if se<0:
			se = ""
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or tasktype == "2":
		t = "hostgroup_add.html"
	if tasktype == "3":
		t = "hostgroup_list.html"
		serverId="0"
		
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if serverId and str(serverId).isdigit() == False:
		return '',403
		
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	perm_client=0
	for i in perm_json:
		if i['SubMenuId']==13 and i['SystemMenuId']==3 and i['Mode']>perm_client:
			perm_client=i['Mode']
		elif i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3:
			# perm=2
			if perm_client<i['Mode']:
				perm_client=i["Mode"]
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3:
			# perm=2
			if perm_client<i['Mode']:
				perm_client=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==18 and i['SystemMenuId']==3:
			# perm=2
			if perm_client<i['Mode']:
				perm_client=i['Mode']
			if perm<i['Mode']:
				perm=i['Mode']
		elif  i['SubMenuId']==20 and i['SystemMenuId']==4 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		elif  i['SubMenuId']==21 and i['SystemMenuId']==4 and i['Mode']>perm:
			# perm=2
			perm=i['Mode']
		if perm==2 and perm_client==2:
			break
	return render_template(t,se=se,tasktype=tasktype,perm_client=perm_client,serverId=serverId,paging=paging,search_typeall=search_typeall,e=e,perm=perm,module_name=a10)
#显示 or 分页 or 搜索serverscope
@hostgroup_list.route('/get_server_list',methods=['GET', 'POST'])
def get_server_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	serverId = request.form.get('a1')
	search_typeall = request.form.get('a2')
	nodetails=request.form.get('a5')
	dsc = request.form.get('dsc')
	
	if num and str(num).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if serverId and str(serverId).isdigit() == False:
		return '',403
	if dsc and dsc != 'false' and dsc!='true':
		return '',403
	if nodetails and nodetails != 'false' and nodetails!='true':
		return '',403
	
	Name=""
	Ip=""
	Hostname=""
	Hgname=""
	searchstring=""
	if search_typeall<0:
		search_typeall=""
	if serverId<0 or serverId=="0" or serverId=="":
		serverId="null"
	if sess < 0:
		sess = ""
	if nodetails<0 or nodetails=="":
		nodetails='false'
	if paging <0:
		paging = "null"
	else:
		paging=int(paging)
	if num < 0:
		num = "null"
	else:
		num=int(num)
	
	
	
	if dsc < 0 or dsc =='':
		dsc = 'false'
		
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
	searchconn={}
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="ServerScopeName":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			
		elif search_s[0]=="IP":
			Ip=Ip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			
		elif search_s[0]=="HostName":
			Hostname=Hostname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			
		elif search_s[0]=="HGName":
			Hgname=Hgname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	if searchstring != "":
		searchstring = searchstring[:-1]
		searchconn['searchstring'] = searchstring
	if Ip != "":
		Ip = Ip[:-1]
		searchconn['IP'] = Ip
	if Hostname != "":
		Hostname = Hostname[:-1]
		searchconn['HostName'] = Hostname
	if Hgname != "":
		Hgname = Hgname[:-1]
		searchconn['HGName'] = Hgname
	searchconn=json.dumps(searchconn)
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	debug("searchconn:"+searchconn)
	searchconn=searchconn.replace("\\","\\\\")
	searchconn=searchconn.replace(".","\\\\\\\\.")
	searchconn=searchconn.replace("?","\\\\\\\\?")
	searchconn=searchconn.replace("+","\\\\\\\\+")
	searchconn=searchconn.replace("(","\\\\\\\\(")
	searchconn=searchconn.replace("*","\\\\\\\\*")
	searchconn=searchconn.replace("[","\\\\\\\\[")
	debug("searchconn:"+searchconn)
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetServerScope(serverscopeid,serverscopename,limitrow,offsetrow)
			sql="select public.\"PGetServerScope\"(%s,%s,%s,%s,%s,E'%s',E'%s',%s);"%(serverId,Name,nodetails,num,paging,system_user,searchconn,dsc)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
	
#创建 or 编辑serverscope
@hostgroup_list.route('/add_server',methods=['GET', 'POST'])
def add_server():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	server = request.form.get('a1')
	server=str(server)
	fid = request.form.get('a3')
	sstype = request.form.get('a2')
	type_name=request.form.get('a4')
	md5_str=request.form.get('m1')
	if session < 0:
		session = ""
	if sstype < 0 or sstype=="":
		sstype = "0"
	if fid < 0 or fid=="":
		fid = "null"
	if type_name<0:
		type_name='运维管理>服务器集合'
	else:
		type_name=type_name.replace('-','>')
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
	
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(server);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveServerScope(jsondata)
			sql="select public.\"PSaveServerScope\"(E'%s',%s,%s);" %(MySQLdb.escape_string(server).decode("utf-8"),sstype,fid)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			conn.commit()
			result_json=json.loads(result)
			server=json.loads(server)
			if server['ServerScopeId']==0:
				oper='创建服务器集合：%s'%server['ServerScopeName']
			else:
				oper='编辑服务器集合：%s'%server['ServerScopeName']
			if result_json["Result"]:
				sql="select public.\"PGetServerScope\"(%s,null,null,null,null,null);" %(result_json["ServerScopeId"])
				curs.execute(sql)
				result_item = curs.fetchall()[0][0]
				result_item=json.loads(result_item)
				ip=''
				ip_set=''
				host=''
				hostg=''
				if server['IsApplyToClientScope']:
					oper+='（应用于客户端集合，'
				else:
					oper+='（不应用于客户端集合，'
				if result_item['data'][0]['IPList']['Set']!=None:
					for i in result_item['data'][0]['IPList']['Set']:
						if i['StartIP']==i['EndIP']:
							ip+=('%s、'%i['StartIP'])
						else:
							ip_set+=('%s-%s、'%(i['StartIP'],i['EndIP']))
				if result_item['data'][0]['HostList']!=None:
					i_num=0
					for i in result_item['data'][0]['HostList']:
						i_num+=1
						if i_num>1000:
							break
						if i['HostId']==None:
							hostg+='[%s]、'%i['HGName']
						else:
							host+='[%s]-%s、'%(i['HGName'],i['HostName'])
				if server['EnableIPLimit'] == 0:
					oper += '不启用IP限制，'
				else:
					oper += '启用IP限制，'
				if ip!='':
					ip=ip[:-1]
					oper+='IP：%s，'%ip
				if ip_set!='':
					ip_set=ip_set[:-1]
					oper+='IP区间：%s，'%ip_set
				if hostg!='':
					hostg=hostg[:-1]
					oper+='主机组：%s，'%hostg
				if host!='':
					host=host[:-1]
					oper+='主机：%s，'%host
				oper=oper[:-1]
				oper+='）'
				if not system_log(system_user,oper,'成功',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			else:
				if not system_log(system_user,oper,result_json["ErrMsg"],type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#搜索主机树
@hostgroup_list.route('/find_hostgroup',methods=['GET','POST'])
def find_hostgroup():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	server_find_json = request.form.get('a1')
	if sess < 0:
		sess = ""
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
	server_find_json=str(server_find_json)
	server_find_json=server_find_json.replace("\\\\","\\\\\\\\")
	server_find_json=server_find_json.replace(".","\\\\.")
	server_find_json=server_find_json.replace("?","\\\\?")
	server_find_json=server_find_json.replace("+","\\\\+")
	server_find_json=server_find_json.replace("(","\\\\(")
	server_find_json=server_find_json.replace("*","\\\\*")
	server_find_json=server_find_json.replace("[","\\\\[")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PFindHostDirectory\"(E'%s');"%(MySQLdb.escape_string(server_find_json).decode("utf-8"))
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			if results==None:
				results="[]"
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#删除serverscope
@hostgroup_list.route('/del_server',methods=['GET', 'POST'])
def del_server():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	sstype = request.form.get('a2')
	fid = request.form.get('a3')
	session = request.form.get('a0')
	module_name=request.form.get('a10')
	if module_name<0:
		module_name='运维管理>服务器集合'
	else:
		module_name=module_name.replace('-','>')
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	if fid < 0 or fid=="":
		fid = "null"
	if sstype < 0 or sstype=="":
		sstype = "0"
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
	
	if check_role(system_user,"访问授权,工单授权,指令授权,管理授权") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if fid != "null" and not fid.isdigit():
		return "{\"Result\":false,\"ErrMsg\":\"非法访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			all_arr=[]
			success_arr=[]
			fail_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				value=int(id_arr[0])
				all_arr.append(id_arr[1])
				# PDeleteServerScope(serverscopeid,sstype,fid)
				# return
				# {"Result":false,"info":"传入参数不正确"}或
				# {"Result":true,"RowCount":1}
				sql = "select public.\"PDeleteServerScope\"(%d,%s,%s);" % (value,int(sstype),fid)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_num+=1
					fail_arr.append(id_arr[1])
					#return result
				else:
					success_num+=1
					success_arr.append(id_arr[1])
				conn.commit()
			oper='删除服务器集合：%s'%('、'.join(all_arr))
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
	
#显示 or 分页 or 搜索hostdirectory
@hostgroup_list.route('/get_hostdirectory',methods=['GET', 'POST'])
def get_hostdirectory():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	loginusercode = request.form.get('a1')
	hgid = request.form.get('a2')
	id = request.form.get('a5')
	type = request.form.get('a6')
	callishnodeselected=request.form.get('a7')
	Name=""
	if hgid<0 or hgid=="":
		hgid="null"
	if sess < 0:
		sess = ""
	if type < 0:
		type = "0"
	if id < 0:
		id = "0"
	if id == '0' and hgid=='0':
		type='0'
	if loginusercode < 0:
		loginusercode = "null"
	else:
		loginusercode="E'%s'"% loginusercode
	if callishnodeselected<0:
		callishnodeselected='false'
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
	if paging!="null":
		paging=(paging-1)*num
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PGetHostDirectory (loginusercode,hgid,type,id,limitrow,offsetrow)
			sql="select public.\"PGetHostDirectory\"(E'%s',%s,%s,%s,%s,%s,%s);"%(system_user,hgid,type,id,num,paging,callishnodeselected)
			debug(str(sql))
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
