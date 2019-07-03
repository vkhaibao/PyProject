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
approve_set = Blueprint('approve_set',__name__)

SIZE_PAGE = 20
ErrorNum = 10000
def debug(c):
	return 0
	path = "/var/tmp/debugrxl.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	LogSet(None, sqlconf, 6)
	
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
#页面跳转函数
@approve_set.route('/approve_strategy',methods=['GET','POST'])
def approve_strategy():
	#页面跳转函数
	#参数 tasktype = 创建-3 编辑-2 列表-1
	#<!-- a=id b=当前显示个数 c=第几页 -->
	tasktype = request.form.get("tasktype")
	page = request.form.get("c")
	search = request.form.get("d")
	search2 = request.form.get("e")
	# se=request.form.get('se')
	if page < 0 or page == None:
		page = "1"
	if search < 0 or search == None:
		search = ""
	if search2 < 0 or search2 == None:
		search2 = ""
	
	if tasktype and str(tasktype).isdigit() == False:
		return '',403
	if page and str(page).isdigit() == False:
		return '',403
	if search and (len(search) > 0 and e.find('-') < 0):
		return '',403
	search = search.replace('(','').replace(')','');
	if	(len(search2) > 0 and search2.find(':') < 0):
		return '',403
	search2 = search2.replace('(','').replace(')','');
	
	
	id = 0
	if tasktype < 0 or tasktype == None:
		tasktype = "1"
	if tasktype == "1":
		t = "approve_list.html"
	elif tasktype=="3":
		t = "approve_add.html"
	elif tasktype=="2":
		id = request.form.get("a")
		if id < 0 or id == None:
			id = "0"
		t = "approve_add.html"
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
	return render_template(t,tasktype=tasktype,a=id,c=page,d=search,e=search2,se=sess,perm=perm,perm_1=perm_1)

#策略删除 
@approve_set.route('/del_approve',methods=['GET','POST'])
def del_approve():	
	global ERRNUM_MODULE
	ERRNUM_MODULE = 30000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	id_str = request.form.get('a1')
	session = request.form.get('a0')
	module_name = request.form.get('a10')
	if module_name<0:
		module_name='运维管理>审批策略'
	if session < 0:
		session = ""
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
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			success_num=0
			fail_num=0
			success_arr=[]
			fail_arr=[]
			all_arr=[]
			for id in ids:
				id_arr=id.split('\t')
				value=int(id_arr[0])
				all_arr.append(id_arr[1])
			# PDeleteApproveStrategy(approvestrategyid)
				sql = "select public.\"PDeleteApproveStrategy\"(%d);" % (value)
				curs.execute(sql)
				result = curs.fetchall()[0][0]
				result_json=json.loads(result)
				if not result_json['Result']:
					fail_num+=1
					fail_arr.append(id_arr[1])
					curs.close()
					conn.close()
					return result
				else:
					success_arr.append(id_arr[1])
					success_num+=1
			oper='删除审批策略：%s'%('、'.join(all_arr))
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
			conn.commit()
			return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}"%(success_num,fail_num,mesg) 
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#列表回显函数	
@approve_set.route('/get_approve_list',methods=['GET','POST'])
def get_approve_list():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	approveId = request.form.get('a1')
	num = request.form.get('a4')
	paging = request.form.get('a3')
	search_typeall = request.form.get('a2')
	dsc = request.form.get('dsc')
	
	if approveId and str(approveId).isdigit() == False:
		return '',403
	if num and str(num).isdigit() == False:
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
	if approveId<0 or approveId=="0" or approveId=="":
		approveId="null"
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
	# PGetApproveStrategy(approvestrategyid,approvestrategyname,limitrow,offsetrow)
	if search_typeall != "":
		search_typeall=search_typeall[:-1]
	typeall = search_typeall.split('\t')
	Name=""
	searchstring=''
	ApproveType=0
	ApproveNum=''
	UserSet=''
	for search in typeall:
		search_s = search.split('-',1)
		if search_s[0]=="Name":
			Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="all":
			#Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
			searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ApproveType":
			if search_s[1]=='消息':
                                ApproveType+=1
                        elif search_s[1]=='短信':
                                ApproveType+=4
                        elif search_s[1]=='邮件':
                                ApproveType+=8
			elif search_s[1]=='所有':
				ApproveType+=0
			#ApproveType=ApproveType+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="ApproveNum":
			ApproveNum=ApproveNum+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
		elif search_s[0]=="UserSet":
			UserSet=UserSet+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
	searchconn={}
	if Name=="":
		Name="null"
	else:
		Name="E'%s'"%(Name[:-1])
	if ApproveType!=0:
		#ApproveType=ApproveType[:-1]
		searchconn['ApproveType']=ApproveType
	#else:
	#	ApproveType=None
	if ApproveNum!='':
		ApproveNum=ApproveNum[:-1]
		searchconn['ApproveNum']=ApproveNum
	#else:
	#	ApproveNum=None
	if UserSet!='':
		UserSet=UserSet[:-1]
		searchconn['UserCode']=UserSet
	if searchstring!="":
		searchstring=searchstring[:-1]
		searchconn['searchstring']=searchstring
	#searchconn={}
	#searchconn['searchstring']=searchstring
	#searchconn['ApproveType']=ApproveType
	#searchconn['ApproveNum']=ApproveNum
	#searchconn['UserSet']=UserSet
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
	sql="select public.\"PGetApproveStrategy\"(%s,%s,%s,%s,0,E'%s',%s);"%(approveId,Name,num,paging,searchconn,dsc)
	#sql="select public.\"PGetApproveStrategy\"(%s,%s,%s,%s);"%(approveId,Name,num,paging)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
#get user
@approve_set.route('/get_user_list_app',methods=['GET','POST'])
def get_user_list_app():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 10000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	userid = request.form.get('a1')
	type = request.form.get('a2')
	if userid<0 or approveId=="":
		userid="null"
	if sess < 0:
		sess = ""
	if type <0:
		type = "0"
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetUser\"(%s,%s);"%(userid,type)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)


	
#审批策略保存	
@approve_set.route('/add_approve',methods=['GET','POST'])
def add_approve():		
	global ERRNUM_MODULE;
	ERRNUM_MODULE = 10000
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	approve = request.form.get('a1')
	module_name = request.form.get('a10')
	md5_str = request.form.get('m1')
	if module_name<0:
		module_name='运维管理>审批策略'
	approve=str(approve)
	approve_json=json.loads(approve)
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
		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(approve);##python中的json的MD5
		if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
		
		
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PSaveApproveStrategy\"(E'%s');" %(MySQLdb.escape_string(approve).decode("utf-8"))
			curs.execute(sql)
			result = curs.fetchall()[0][0]
			result_json=json.loads(result)
			if 'UsedForPwdMod' in approve_json and approve_json['UsedForPwdMod']==1:
				return result 
			if approve_json['ApproveStrategyId']==0:
				oper='创建审批策略：%s'%approve_json['ApproveStrategyName']
			else:
				oper='编辑审批策略：%s'%approve_json['ApproveStrategyName']
			if result_json['Result']:
				sql="select public.\"PGetApproveStrategy\"(%s,null,null,null);" %(result_json['ApproveStrategyId'])
				curs.execute(sql)
				ApproveStrategy=curs.fetchall()[0][0]
				ApproveStrategy_json=json.loads(ApproveStrategy)
				ApproveStrategy=ApproveStrategy_json['data'][0]
				ApproveStrategy_oper=[]
				if ApproveStrategy['ApproveType']>=1:
					ApproveType_arr=[]
					if ApproveStrategy['ApproveType'] & 1:
						ApproveType_arr.append('消息')
					if ApproveStrategy['ApproveType'] & 4:
						ApproveType_arr.append('短信')
					if ApproveStrategy['ApproveType'] & 8:
						ApproveType_arr.append('邮件')
					ApproveStrategy_oper.append('方式：%s'%('、').join(ApproveType_arr))
				
				ApproveStrategy_oper.append('审批人数：%s'%(ApproveStrategy['ApproveNum']))
				if len(ApproveStrategy['UserSet'])>0:
					UserSet=[]
					for item in ApproveStrategy['UserSet']:
						UserSet.append(item['UserCode'])
					ApproveStrategy_oper.append('审批者：%s'%('、').join(UserSet))
				if ApproveStrategy['MasterSmsSvrConfigId']!=None:
					ApproveStrategy_oper.append('短信默认：%s'%(approve_json['MasterSmsSvrConfig']))
				if ApproveStrategy['StandBySmsSvrConfigId']!=None:
                                        ApproveStrategy_oper.append('短信备用：%s'%(approve_json['StandBySmsSvrConfig']))
				if ApproveStrategy['MasterSmtpConfigId']!=None:
                                        ApproveStrategy_oper.append('邮件默认：%s'%(approve_json['MasterSmtpConfig']))
				if ApproveStrategy['StandBySmtpConfigId']!=None:
                                        ApproveStrategy_oper.append('邮件备用：%s'%(approve_json['StandBySmtpConfig']))
				oper+=('（'+'，'.join(ApproveStrategy_oper)+'）')
				if not system_log(system_user,oper,'成功',module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
				conn.commit()
			else:	
				if not system_log(system_user,oper,result_json['ErrMsg'],module_name):
					return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"	
			return result 
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	
