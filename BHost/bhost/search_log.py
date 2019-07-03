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
from bhcomm import StrClas
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

from htmlencode import checkproto
from htmlencode import checkaccount
from htmlencode import checkhostaccount

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
search_log = Blueprint('search_log',__name__)

ERRNUM_MODULE=3000
SIZE_PAGE = 20
ErrorNum = 10000
def debug(c):
	return 0
        path = "/var/tmp/debugrx_ccp123.txt"
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
	return newStr

##检索结果
@search_log.route("/search_log", methods=['GET', 'POST'])
def _search_log():
	debug('=======================')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip)
	tasktype=request.form.get('tasktype')
	taskid=request.form.get('a1')
	logtype=request.form.get('a2')
	btn_status=request.form.get('a4')
	name=request.form.get('a5')
	f1=request.form.get('f1')
	t1=request.form.get('t1')
	#页码
	p1=request.form.get('p1')
	tp1=request.form.get('tp1')
	i1=request.form.get('i1')
	v1=request.form.get('v1')
	
	hash  = request.form.get('ha');
	
	if hash < 0 or hash =='':
		pass
	else:
		myCookie = request.cookies #获取所有cookie
		if myCookie.has_key('bhost'):
			hashsrc = StrMD5(myCookie['bhost']);
			if(hashsrc != hash):
				exit();
			
	
	if i1 < 0:
		i1 = ""
	if p1 < 0:
		p1 = "1"
	if tp1 <0:
		tp1='1'
	if tasktype < 0:
		tasktype = ""
	if btn_status < 0:
		btn_status = ""
	if taskid < 0:
		taskid = 0
	if name < 0:
		name = ""
	if logtype < 0:
		logtype = 0
	s=0
	if logtype=='NORMAL':
		logtype=1
	elif logtype=='SESSION':
		logtype=2
	elif logtype=='SYSTEM':
		logtype=3
	
	if str(taskid).isdigit() == False:
		return '',403 
		
	if btn_status != '' and str(btn_status).isdigit() == False:
		return '',403 
		
	if name != '' and checkhostaccount(name) == False:
		return '',403 
	
	if f1 and checkhostaccount(f1) == False:
		return '',403 
	
	if t1 and checkhostaccount(t1) == False:
		return '',403 
	if i1:
		i1_tmp = i1.split(',');
		for n in i1_tmp:
			if n.isdigit() == False:
				return '',403 
	if p1:
		tmp = p1.split(',');
		for n in tmp:
			if n.isdigit() == False:
				return '',403 
	if tasktype:
		if str(tasktype).isdigit() == False:
			return '',403
	
	if tp1:
		if str(tp1).isdigit() == False:
			return '',403
	
	debug('session:%s|taskid:%s|logtype:%s|error:%s'%(session,taskid,logtype,error))
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
			sql="select public.\"PGetLogFieldConfig\"(%s);" %(logtype)
			curs.execute(sql)
			config = curs.fetchall()[0][0]
			sql = "select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
			curs.execute(sql)
			proto_list = curs.fetchall()[0][0].encode('utf-8')
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	debug(str(config))
	proto_list = json.loads(proto_list)['data']
	debug('-----------------')
	if proto_list == None:
        	proto_list = []
        pro_l = []
        for proto in proto_list:
                pro_l.append([])
                pro_l[-1].append(proto['ProtocolId'])
                pro_l[-1].append(proto['ProtocolName'])
	debug('--->>>>11')
	try:
		with pyodbc.connect(StrSqlConn('BH_DATA')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetLogDetail\"(%s,%s);" %(taskid,logtype)
			curs.execute(sql)
			detail = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	detail=json.loads(detail)
	debug('--->>>ll')
	if detail['int08_12']==None:
		detail['int08_12']=0
	debug('--->>>aa')
	if(detail['int08_12'] > 0): ##未启用告警
        	clas = 1
        else:
                clas = 0
	debug('clas:'+str(clas))
	debug('logtype:'+str(logtype))
	if detail['xtime_02']==None:
		detail['int08_03']='1'
	else:
		time_now=time.time();
		time_old=time.mktime(time.strptime(detail['xtime_02'].split('+')[0].replace('T',' '),'%Y-%m-%d %H:%M:%S'))
		if (time_now-time_old)>300 and str(detail['int08_03'])=='0':
			detail['int08_03']='2'
	if logtype != 3 and logtype != '3':
		for pro in pro_l:
                	if pro[0] == detail['int32_01']:
                        	detail['int32_01'] = pro[1]
              	debug('---->:>2')
		for o in detail:
                        if o == "orderitem":
                                continue
                        field = o.split('_')[0];
                        index = o.split('_')[1];
                        if (o.find('int08') >=0 and (index == '11' or index == '14' or index == '03' or index == '15')) or o=='str32_31':
                               	detail[o] = StrClas(field,index,str(detail[o]),0,clas)
                        if o == 'int64_15':
                                detail[o] = StrClas(field,index,detail[o],0,clas)
			if o == 'int08_11':
                                if detail[o] == 1:
                                        detail[o] = '已处理'
                                elif detail[o] == 0:
                                        detail[o] = '未处理'
       	else:
            	for o in detail:
			if o == 'int08_11':
				if detail['int08_12'] >0:
					if detail[o] == 1:
						detail[o] = '已处理'
					elif detail[o] == 0:
						detail[o] = '未处理'
				else:
					detail[o] = ''
			if o == 'int32_01' or o=='int08_12':
                                field = o.split('_')[0];
                                index = o.split('_')[1];
                                detail[o] = StrClas(field,index,int(detail[o]),1,1)
	'''
	detail_key_arr=detail.keys()
	debug(str(detail_key_arr))
	debug('s:'+str(s))
	for i in detail_key_arr:
		if s==1 and (('int32_01' in i) or ('str32' in i)):
			debug(str(i))
			keys_value=i.split('_')
			debug(str(keys_value))
			debug('%s'%(str(detail['int08_12'])))
			debug('%s:%s:%s:%s:%s'%(str(keys_value[0]),str(keys_value[1]),detail[i],str(s),str(detail['int08_12'])))			
			if detail[i]==None:
				detail[i]=''
			else:
				detail[i]=StrClas(keys_value[0],keys_value[1],detail[i],s,detail['int08_12'])
				debug(StrClas(keys_value[0],keys_value[1],detail[i],s,detail['int08_12']))
	'''
	detail["xtime_03"]=str(detail["xtime_03"])
	detail["xtime_00"]=str(detail["xtime_00"])
	detail['DownloadEnable']=False
	detail['DeleteEnable']=False
	debug('str32_28:'+str(detail['str32_28']))
	debug('int32_01:'+str(detail['int32_01']))
	
	detail['IfReplay'] = False ##是否使用控件回放
	detail['IfReplayDrawing'] = False ##回放  字符回放（ssh等） 图形回放（RDP等）
	if detail['str32_28']!=None:
		if detail['str32_28']!='':
			detail['DownloadEnable']=True
			##
			detail['IfReplay'] = True;							
			pro = detail['str32_28'].split('/')[-2].upper()
			if pro =="RDP" or pro =="ACC" or pro =="VNC" or pro =="X11":
				detail['IfReplayDrawing'] = True	
		else:
			if detail['int32_01']=='FTP' or detail['int32_01']=='SSH' or detail['int32_01']=='SFTP' or detail['int32_01']=='RDP':
				debug('str32_01:'+str(detail['str32_01']))
				if detail['str32_01'].find('Save')!=-1:
					filename=detail['str32_01'].split(' ',1)[1]
					debug('filename:'+str(filename))
					filepath='/usr/storage/.system/transf/ftp/'
					debug('filepath:'+str(filepath))
					# if detail['int32_01']=='FTP':
					# 	filepath='/usr/storage/.system/transf/ftp/'
					# elif detail['int32_01']=='SFTP':
					# 	filepath='/usr/storage/.system/transf/ssh/'
					# else:
					# 	filepath='/usr/storage/.system/transf/rdp/'
						
					f_all=filepath+filename
					debug(str(f_all)+'>>>'+str(os.path.exists(f_all)))
					if os.path.exists(f_all):
						detail['DownloadEnable']=True
						detail['DeleteEnable']=True
						
	debug(str(detail['DownloadEnable']))
	debug(str(detail['DeleteEnable']))
	detail = json.dumps(detail)
	detail=str(detail)
	debug(str(detail))
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql="select public.\"PGetAccessProtocol\"(null,null,null,null,null,null);"
			curs.execute(sql)
			protocol = curs.fetchall()[0][0]
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	if v1!='1':
		perm=get_user_perm_value(userCode)
		perm_json=json.loads(perm)
		perm=0
		for i in perm_json:
			if i['SubMenuId']==1 and i['SystemMenuId']==1:
				# perm=2
				perm=i['Mode']
				break
	else:
		perm=2
	return render_template('search_log.html',tp1=tp1,p1=p1,i1=i1,se=session,us=userCode,taskid=taskid,logtype=logtype,config=config,detail=detail,f1=f1,t1=t1,protocol=protocol,btn_status=btn_status,tasktype=tasktype,name=name,perm=perm,v1=v1)
