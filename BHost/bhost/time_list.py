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

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from htmlencode import parse_sess,check_role
env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
time_list = Blueprint('time_list',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000

#
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
#1创建 2编辑 3列表
@time_list.route('/timeset_handle',methods=['GET','POST'])
def timeset_handle():
	tasktype = request.form.get("tasktype")
	timesetId = request.form.get("timesetId")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	se = request.form.get("se")
	if se<0:
		se=request.args.get('se')
		if se<0:
			se = ""
	e = request.form.get("e")
	
	if tasktype and str(tasktype).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if timesetId and str(timesetId).isdigit() == False:
		return '',403
	if	(len(e) > 0 and e.find(':') < 0):
		return '',403
		
	e = e.replace('(','').replace(')','');
	
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1" or tasktype == "2":
		t = "time_add.html"
	if tasktype == "3":
		t = "time_list.html"
		timesetId="0"
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(se,client_ip)
	perm=get_user_perm_value(system_user)
	perm_json=json.loads(perm)
	perm=0
	for i in perm_json:
		if i['SubMenuId']==15 and i['SystemMenuId']==3:
			perm=i['Mode']
		#elif i['SubMenuId']==16 and i['SystemMenuId']==3:
		#	perm=i['Mode']
		if perm==2:
			break
	return render_template(t,perm=perm,tasktype=tasktype,timesetId=timesetId,paging=paging,search_typeall=search_typeall,e=e,se=se)
#跳转至时间集合
@time_list.route('/time_show',methods=['GET','POST'])
def time_show():
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
	for i in perm_json:
		if i['SubMenuId']==15 and i['SystemMenuId']==3:
			perm=i['Mode']
		#elif i['SubMenuId']==16 and i['SystemMenuId']==3:
		#	perm=i['Mode']
		if perm==2:
			break
	return render_template('time_list.html',se=sess,paging="1",search_typeall="",e=':',perm=perm)
#删除
@time_list.route('/del_timeset',methods=['GET','POST'])
def del_timeset():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	timetype = request.form.get('a2')
	fid = request.form.get('a3')
	session = request.form.get('a0')
	module_name = request.form.get('a10')
	if module_name<0:
		module_name='运维管理>时间集合'
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
	if fid < 0 or fid=="":
		fid = "null"
	if timetype < 0 or timetype=="":
		timetype = "0"
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

	if check_role(system_user,"访问授权") == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			success_arr=[]
			all_arr=[]
			fail_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				value=int(id_arr[0])
				all_arr.append(id_arr[1])
			# PDeleteTimeSet(timesetid,timetype,fid)
				sql = "select public.\"PDeleteTimeSet\"(%d,%s,%s);" % (value,timetype,fid)
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
			oper='删除时间集合：%s'%('、'.join(all_arr))
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
	
#添加 or 编辑
@time_list.route('/add_timeset',methods=['GET','POST'])
def add_timeset():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	timeset = request.form.get('a1')
	type_name = request.form.get('a10')
	md5_str = request.form.get('m1')
	if type_name<0:
		type_name='运维管理>时间集合'
	timeset=str(timeset)
	timeset_json=json.loads(timeset)
	fid = request.form.get('a3')
	timetype = request.form.get('a2')
	if sess < 0:
		sess = ""
	if timetype < 0 or timetype=="":
		timetype = "0"
	if fid < 0 or fid=="":
		fid = "null"
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
		md5_json = StrMD5(timeset);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveTimeSet(jsondata,timetype,fid)
			sql="select public.\"PSaveTimeSet\"(E'%s',%s,%s);" %(MySQLdb.escape_string(timeset).decode("utf-8"),timetype,fid)
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if str(timeset_json['TimeSetId'])=='0':
				oper='创建时间集合：%s'%timeset_json['Name']
			else:
				oper='编辑时间集合：%s'%timeset_json['Name']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json["ErrMsg"],type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				return result
			else:
				oper_arr=[]
				if timeset_json['Description']!=None:
					oper_arr.append('描述：%s'%(timeset_json['Description']))
				timeset_arr=[]
				for i in timeset_json['Set']:
					if i['TimeSetType']==11:
						i['TimeSetType']='周期 每天 '
					elif i['TimeSetType']==12:
						i['TimeSetType']='周期 每周 '
						if i['StartPeriod']=='1':
							i['StartPeriod'] = "周一 "
						elif i['StartPeriod']=='2':
							i['StartPeriod'] = "周二 "
						elif i['StartPeriod']=='3':
							i['StartPeriod'] = "周三 "
						elif i['StartPeriod']=='4':
							i['StartPeriod'] = "周四 "
						elif i['StartPeriod']=='5':
							i['StartPeriod'] = "周五 "
						elif i['StartPeriod']=='6':
							i['StartPeriod'] = "周六 "
						elif i['StartPeriod']=='7':
							i['StartPeriod'] = "周日 "
						if i['EndPeriod']=='1':
							i['EndPeriod'] = "周一 ";
						elif i['EndPeriod']=='2':
							i['EndPeriod'] = "周二 ";
						elif i['EndPeriod']=='3':
							i['EndPeriod'] = "周三 ";
						elif i['EndPeriod']=='4':
							i['EndPeriod'] = "周四 ";
						elif i['EndPeriod']=='5':
							i['EndPeriod'] = "周五 ";
						elif i['EndPeriod']=='6':
							i['EndPeriod'] = "周六 ";
						elif i['EndPeriod']=='7':
							i['EndPeriod'] = "周日 ";
					elif i['TimeSetType']==13:
						i['TimeSetType']='周期 每月 '
						i['StartPeriod'] = str(i['StartPeriod']) + "日 "
						i['EndPeriod'] = str(i['EndPeriod']) + "日 "
					elif i['TimeSetType']==20:
						i['TimeSetType']='区间 '
					elif i['TimeSetType']==31:
						i['TimeSetType']='任务 当前 '
					elif i['TimeSetType']==32:
						i['TimeSetType']='任务 当天 '
					if i['StartDate']==None:
						i['StartDate'] = "";
					else:
						i['StartDate'] += " ";
					if i['EndDate']==None:
						i['EndDate'] = "";
					else:
						i['EndDate'] += " ";
					if i['StartTime']==None:
						i['StartTime'] = "";
					else:
						i['StartTime'] += " ";
					if i['EndTime']==None:
						i['EndTime'] = "";
					else:
						i['EndTime'] += " ";
					if i['EndPeriod']==None:
						i['EndPeriod'] = "";
					if i['StartPeriod']==None:
						i['StartPeriod'] = "";
					timeset_str = i['TimeSetType'] + i['StartDate'] + i['StartPeriod'] + i['StartTime'] + "至 " + i['EndDate'] + i['EndPeriod'] + i['EndTime']
					timeset_arr.append(timeset_str)
				oper_arr.append('设置：%s'%('、'.join(timeset_arr)))
				oper+=('（'+'，'.join(oper_arr)+'）')
				if not system_log(system_user,oper,'成功',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#显示 or 分页 or 搜索
@time_list.route('/get_timeset_list',methods=['GET', 'POST'])
def get_timeset_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	noset = request.form.get('a5')
	timesetId = request.form.get('a1')
	search_typeall = request.form.get('a2')
	dsc = request.form.get('dsc')
	
	if num and str(num).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if timesetId and str(timesetId).isdigit() == False:
		return '',403
	if dsc and dsc != 'false' and dsc!='true':
		return '',403
	if noset and noset != 'false' and noset!='true':
		return '',403
	
	Name="";
	Description="";
	if search_typeall<0:
		search_typeall=""
	if noset<0 or noset=="":
		noset="false"
	if timesetId<0 or timesetId=="0" or timesetId=="":
		timesetId="null"
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
	searchstring=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="Description":
			Description=Description+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	if Description=="":
		Description="null"
	else:
		Description="'%s'"%(Description[:-1])
	if searchstring=="":
		searchstring=""
	else:
		searchstring=searchstring[:-1]
	searchconn['searchstring']=searchstring
	searchconn=json.dumps(searchconn)
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	Description=Description.replace("\\\\","\\\\\\\\")
	Description=Description.replace(".","\\\\.")
	Description=Description.replace("?","\\\\?")
	Description=Description.replace("+","\\\\+")
	Description=Description.replace("(","\\\\(")
	Description=Description.replace("*","\\\\*")
	Description=Description.replace("[","\\\\[")
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
			# PGetTimeSet(timesetid,noset,limitrow,offsetrow)
			sql="select public.\"PGetTimeSet\"(%s,%s,%s,%s,%s,%s,E'%s',%s);"%(timesetId,Name,Description,noset,num,paging,searchconn,dsc)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
