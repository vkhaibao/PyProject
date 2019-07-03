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
from htmlencode import check_role
from htmlencode import parse_sess

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
eventinfo_list = Blueprint('eventinfo_list',__name__)

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

#跳转至告警信息
@eventinfo_list.route('/eventinfo_show',methods=['GET','POST'])
def eventinfo_show():
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
	perm_1=1
	for i in perm_json:
		if i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==32 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==24 and i['SystemMenuId']==6 and i['Mode']>perm_1:
			perm_1=2
		if perm==2 and perm_1==2:
			break
	return render_template('eventinfo_list.html',se=sess,paging="1",search_typeall="",e=':',perm=perm,perm_1=perm_1)

#1创建 2编辑 3列表
@eventinfo_list.route('/eventinfo_handle',methods=['GET','POST'])
def eventinfo_handle():
	tasktype = request.form.get("tasktype")
	eventinfoId = request.form.get("eventinfoId")
	paging = request.form.get("paging")
	search_typeall = request.form.get("search_typeall")
	e = request.form.get("e")
	if e<0:
		e=''
	if tasktype < 0:
		tasktype = "1"
	if tasktype == "1":
		t = "eventinfo_add.html"
	if tasktype == "2":
		t = "eventinfo_add.html"
	if tasktype == "3":
		t = "eventinfo_list.html"
		eventinfoId="0"
		
	if eventinfoId and str(eventinfoId).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
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
	perm_1=1
	for i in perm_json:
		if i['SubMenuId']==17 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==15 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==16 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==32 and i['SystemMenuId']==3 and i['Mode']>perm:
			perm=i['Mode']
		elif  i['SubMenuId']==24 and i['SystemMenuId']==6 and i['Mode']>perm_1:
			perm_1=2
		if perm==2 and perm_1==2:
			break
	return render_template(t,tasktype=tasktype,se=sess,perm=perm,eventinfoId=eventinfoId,paging=paging,search_typeall=search_typeall,e=e,perm_1=perm_1)
#删除
@eventinfo_list.route('/del_eventinfo',methods=['GET','POST'])
def del_eventinfo():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	module_name = request.form.get('a10')
	if module_name<0:
		module_name='运维管理>事件告警'
	if session < 0:
		session = ""
	if id_str < 0:
		id_str = ""
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
	if check_role(system_user,'访问授权,工单授权,指令授权,全局策略') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			all_arr=[]
			success_num=0
			fail_num=0
			success_arr=[]
			fail_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				value=int(id_arr[0])
				all_arr.append(id_arr[1])
				# PDeleteEventAlarmInfo(eventalarminfoid)
				sql = "select public.\"PDeleteEventAlarmInfo\"(%d);" % (value)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_arr.append(id_arr[1])
					fail_num+=1
				else:
					success_arr.append(id_arr[1])
					success_num+=1
					conn.commit()
			oper='删除事件告警：%s'%('、'.join(all_arr))
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
			return result  
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
#添加 or 编辑
@eventinfo_list.route('/add_eventinfo',methods=['GET','POST'])
def add_eventinfo():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	eventinfo = request.form.get('a1')
	type_name = request.form.get('a10')
	if type_name<0:
		type_name='运维管理>事件告警'
	eventinfo=str(eventinfo)
	eventinfo_json=json.loads(eventinfo)
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
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(eventinfo);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			# PSaveEventAlarmInfo(jsondata)
			sql="select public.\"PSaveEventAlarmInfo\"(E'%s');" %(MySQLdb.escape_string(eventinfo).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if str(eventinfo_json['EventAlarmInfoId'])=='0':
				oper='创建事件告警：%s'%eventinfo_json['Name']
			else:
				oper='编辑事件告警：%s'%eventinfo_json['Name']
			if not result_json['Result']:
				if not system_log(system_user,oper,result_json["ErrMsg"],type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			else:
				oper_arr=[]
				if eventinfo_json['EventDescription']!=None:
					oper_arr.append('描述：%s'%( eventinfo_json['EventDescription']))
				if eventinfo_json['EventLevel']==0:
					oper_arr.append('等级：无')
				elif eventinfo_json['EventLevel']==1:
					oper_arr.append('等级：低')
				elif eventinfo_json['EventLevel']==2:
					oper_arr.append('等级：中')
				elif eventinfo_json['EventLevel']==3:
					oper_arr.append('等级：高')
				if eventinfo_json['EventType']==0:
					oper_arr.append('类型：无')
				elif eventinfo_json['EventType']==1:
					oper_arr.append('类型：违规操作')
				elif eventinfo_json['EventType']==2:
					oper_arr.append('类型：高危操作')
				elif eventinfo_json['EventType']==3:
					oper_arr.append('类型：登录异常')
				
				if eventinfo_json['AlarmAction']==0:
					oper_arr.append('方式：无')
				else:
					if eventinfo_json['AlarmAction']==1:
						oper_arr.append('方式：邮件')
					elif eventinfo_json['AlarmAction']==2:
						oper_arr.append('方式：短信猫')
					elif eventinfo_json['AlarmAction']==3:
						oper_arr.append('方式：短信')
					elif eventinfo_json['AlarmAction']==4:
						oper_arr.append('方式：snmp')
					elif eventinfo_json['AlarmAction']==5:
						oper_arr.append('方式：syslog')
					oper_arr.append('默认：%s'%(eventinfo_json['MasterConfigName']))
					oper_arr.append('备用：%s'%(eventinfo_json['StandByConfigName']))
				oper+=('（'+'，'.join(oper_arr)+')')
				if not system_log(system_user,oper,'成功',type_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
				conn.commit()
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#显示 or 分页 or 搜索
@eventinfo_list.route('/get_eventinfo_list',methods=['GET', 'POST'])
def get_eventinfo_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	eventinfoId = request.form.get('a1')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	dsc = request.form.get('dsc')
	
	if num and str(num).isdigit() == False:
		return '',403
	if eventinfoId and str(eventinfoId).isdigit() == False:
		return '',403
	if paging and str(paging).isdigit() == False:
		return '',403
	if search_typeall and (len(search_typeall) > 0 and search_typeall.find('-') < 0):
		return '',403
	if search_typeall:
		search_typeall = search_typeall.replace('(','').replace(')','');
	if dsc and dsc != 'false' and dsc!='true':
		return '',403
		
	
	if search_typeall<0:
		search_typeall=""
	if eventinfoId<0 or eventinfoId=="0" or eventinfoId=="":
		eventinfoId="null"
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
	Name=""
	EventDescription=""
	EventLevel=''
	EventType=''
	AlarmAction=''
	UserSet=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="EventDescription":
			EventDescription=EventDescription+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="EventLevel":
			EventLevel=EventLevel+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="EventType":
			EventType=EventType+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="AlarmAction":
			AlarmAction=AlarmAction+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="UserSet":
			UserSet=UserSet+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	if EventDescription=="":
		EventDescription="null"
	else:
		EventDescription="E'%s'"%(EventDescription[:-1])
	if EventLevel!="":
		EventLevel=EventLevel[:-1]
		if EventLevel=='无':
			EventLevel=0
		elif EventLevel=='低':
			EventLevel=1
		elif EventLevel=='中':
			EventLevel=2
		elif EventLevel=='高':
			EventLevel=3
		elif EventLevel=='所有':
			EventLevel=None
	else:
		EventLevel=None
	if EventType!="":
		EventType=EventType[:-1]
		if EventType=='无':
			EventType=0
		elif EventType=='违规操作':
			EventType=1
		elif EventType=='高危操作':
			EventType=2
		elif EventType=='登录异常':
			EventType=3
		elif EventType=='所有':
			EventType=None
	else:
		EventType=None
	if AlarmAction!='':
		AlarmAction=AlarmAction[:-1]
		if AlarmAction=='无':
			AlarmAction=0
		elif AlarmAction=='邮件':
			AlarmAction=1
		elif AlarmAction=='短信':
			AlarmAction=3
		elif AlarmAction=='SNMP':
			AlarmAction=4
		elif AlarmAction=='SYSLOG':
			AlarmAction=5
		elif AlarmAction=='所有':
			AlarmAction=None
	else:
		AlarmAction=None
	if UserSet!="":
		UserSet=UserSet[:-1]
	if searchstring!="":
		searchstring=searchstring[:-1]
	searchconn['searchstring']=searchstring
	searchconn['EventLevel']=EventLevel
	searchconn['EventType']=EventType
	searchconn['AlarmAction']=AlarmAction
	searchconn['UserCode']=UserSet
	searchconn=json.dumps(searchconn)
	Name=Name.replace("\\\\","\\\\\\\\")
	Name=Name.replace(".","\\\\.")
	Name=Name.replace("?","\\\\?")
	Name=Name.replace("+","\\\\+")
	Name=Name.replace("(","\\\\(")
	Name=Name.replace("*","\\\\*")
	Name=Name.replace("[","\\\\[")
	EventDescription=EventDescription.replace("\\\\","\\\\\\\\")
	EventDescription=EventDescription.replace(".","\\\\.")
	EventDescription=EventDescription.replace("?","\\\\?")
	EventDescription=EventDescription.replace("+","\\\\+")
	EventDescription=EventDescription.replace("(","\\\\(")
	EventDescription=EventDescription.replace("*","\\\\*")
	EventDescription=EventDescription.replace("[","\\\\[")
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
			# PGetEventAlarmInfo(eventalarminfoid,name,description,limitrow,offsetrow)
			sql="select public.\"PGetEventAlarmInfo\"(%s,%s,%s,%s,%s,E'%s',%s);"%(eventinfoId,Name,EventDescription,num,paging,searchconn,dsc)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
	
	
	
