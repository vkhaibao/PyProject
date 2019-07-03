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

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import SessionCheckLocal 
from comm import LogSet
from comm import *
from logbase import common
from urllib import unquote

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
from logbase import defines
from logbase import task_client
from ctypes import *
import base64
import csv
import codecs
from werkzeug.utils import secure_filename

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
colony_list = Blueprint('colony_list',__name__)

SIZE_PAGE = 20
def debug(c):
	return 0
        path = "/var/tmp/debugcolony_list.txt"
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
	
#显示 or 分页 or 搜索
@colony_list.route('/get_server_global',methods=['GET', 'POST'])
def get_server_global():
	debug('get_server_global')
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	get_server_global_json = request.form.get('a1')
	get_server_global_json=str(get_server_global_json)
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
	get_server_global_json=get_server_global_json.replace("\\\\","\\\\\\\\")
	get_server_global_json=get_server_global_json.replace(".","\\\\.")
	get_server_global_json=get_server_global_json.replace("?","\\\\?")
	get_server_global_json=get_server_global_json.replace("+","\\\\+")
	get_server_global_json=get_server_global_json.replace("(","\\\\(")
	get_server_global_json=get_server_global_json.replace("*","\\\\*")
	get_server_global_json=get_server_global_json.replace("[","\\\\[")
	# PGetServerGlobal(get_server_global_json)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql='select public."PGetServerGlobal"(E\'%s\');'%(MySQLdb.escape_string(get_server_global_json).decode("utf-8"))
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			return "{\"Result\":true,\"info\":%s}" % results
	except pyodbc.Error,e:
		debug(str(e))
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@colony_list.route('/get_server_HstGet',methods=['GET', 'POST'])
def get_server_HstGet():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	sid = request.form.get('a1')
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
	(error,_time)=HstGet(None,sid)
	debug("%s|%s HstGet"%(str(error),str(_time)))
	if error!=0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	if _time==None:
		return '{"Result":true,"info":0}'
	_time_local=time.time()
	debug(str(_time_local)+'time_local')
	if (_time_local-int(_time))<=300:
		_time='1'
	else:
		_time='0'
	return '{"Result":true,"info":"%s"}'%(_time)

@colony_list.route('/get_server_CpuUsed',methods=['GET', 'POST'])
def get_server_CpuUsed():
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	sid = request.form.get('a1')
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
	(error,_CpuUsed)=CpuUsed(None,sid)
	if error!=0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	if _CpuUsed==None:
		return '{"Result":true,"info":"0"}'
	return '{"Result":true,"info":"%s"}'%(_CpuUsed)

def split_str(netstat):
	###
	tmp = netstat.split("duplex=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		duplex = tmp_list[0]
	else:
		duplex = ""
	###
	tmp = netstat.split("speed=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		speed = tmp_list[0]
	else:
		speed ="0"
	####
	tmp = netstat.split("mtu=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		mtu = tmp_list[0][:-1]
	else:
		mtu="0"
	####
	tmp = netstat.split("bytes_sent=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		bytes_sent = tmp_list[0]
	else:
		bytes_sent="0"
	#####
	tmp = netstat.split("bytes_recv=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		bytes_recv = tmp_list[0]
	else:
		bytes_recv="0"
	####
	tmp = netstat.split("packets_sent=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		packets_sent = tmp_list[0]
	else:
		packets_sent="0"
	####
	tmp = netstat.split("packets_recv=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		packets_recv = tmp_list[0]
	else:
		packets_recv="0"
	###
	tmp = netstat.split("errin=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		errin = tmp_list[0]
	else:
		errin="0"
	###
	tmp = netstat.split("errout=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		errout = tmp_list[0]
	else:
		errout="0"
	####
	tmp = netstat.split("dropin=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(",")
		dropin = tmp_list[0]
	else:
		dropin ="0"
	###
	tmp = netstat.split("dropout=")
	if len(tmp) > 1:
		tmp_list = tmp[1].split(")")
		dropout = tmp_list[0]
	else:
		dropout="0"
		
	return   "'duplex':'%s','speed':'%s','mtu':'%s','bytes_sent':'%s','bytes_recv':'%s','packets_sent':'%s','packets_recv':'%s','errin':'%s','errout':'%s','dropin':'%s','dropout':'%s'" % (duplex,speed,mtu,bytes_sent,bytes_recv,packets_sent,packets_recv,errin,errout,dropin,dropout)

@colony_list.route('/get_server_all_data',methods=['GET', 'POST'])
def get_server_all_data():
	debug('---get_server_all_data---')
	###session 检查
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	sid = request.form.get('a1')
	g_cluster_type = common.get_server_cluster_type();
	if sess < 0:
		sess = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheckLocal(sess,client_ip)
	#(error,system_user,mac) = SessionCheck(sess,client_ip)
	if error < 0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"ErrMsg\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"ErrMsg\":\"系统超时\"}"
		sys.exit()
	all_data={}
	(error,_CpuUsed)=CpuUsed(None,sid,common.get_inner_master_ip())
	if error!=0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	#all_data["CpuUsed"]=[];
	all_data["CpuUsed"]=_CpuUsed
	#all_data["CpuUsed"][1]=_CpuUsed[1]
	(error,_MemUsed)=MemUsed(None,sid,common.get_inner_master_ip())
	if error!=0:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	all_data["MemUsed"]=_MemUsed
	# PGetServerEther(sid)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			#获取前置机
			#sql='select DISTINCT b."AccIPId",a."AccIP",a."IsBuildin" from public."AccIP" a join public."HostServiceAccIP" b on b."AccIPId"=a."AccIPId" order by b."AccIPId"'
			#sql='select DISTINCT a."AccIPId",a."AccIP",a."IsBuildin" from public."AccIP" a,public."HostServiceAccIP" b,public."GlobalStrategyAccIP" c where b."AccIPId"=a."AccIPId" or c."AccIPId"=a."AccIPId" order by a."AccIPId";'
			sql='SELECT DISTINCT a."AccIPId",a."AccIP",a."IsBuildin" from public."AccIP" a WHERE a."AccIPId" IN ( SELECT c."AccIPId" FROM public."GlobalStrategyAccIP" c where c."AccIPId" IS NOT NULL UNION select b."AccIPId" from public."HostServiceAccIP" b left OUTER JOIN public."GlobalStrategyAccIP" c ON 1=1 where c."AccIPId" IS NULL ) order by a."AccIPId";';
			debug(sql)
			curs.execute(sql)
			results_AccIP_lines = curs.fetchall()
			AccIP=[]
			debug(str(results_AccIP_lines))
			for results_AccIP_line in results_AccIP_lines:
				AccIP_json={}
				AccIP_json['AccIPId']=(results_AccIP_line[0])
				AccIP_json['AccIP']=(results_AccIP_line[1])
				AccIP_json['IsBuildin']=(results_AccIP_line[2])
				AccIP_json['stat']=0
				if AccIP_json['IsBuildin']=='0':
					(error,_AccStat)=AccStat(None,'0:%s'%AccIP_json['AccIP'],common.get_inner_master_ip())
				else:
					(error,_AccStat)=AccStat(None,'%s:%s'%(sid,AccIP_json['AccIP']),common.get_inner_master_ip())
				#(error,_AccStat)=AccStat(None,AccIP_json['AccIP'],common.get_inner_master_ip())
				debug('error'+str(error))
				debug('_AccStat:%s'%str(_AccStat))
				AccIP_json['stat']=0
				if error==0:
					_AccStat=json.loads(_AccStat.replace('L',''))
					_time_local=time.time()
					debug('_time_local:%d'%int(_time_local))
					if (_time_local-int(_AccStat[1]))<=300 and _AccStat[0]==1:
						AccIP_json['stat']=1
				debug(str(AccIP_json))
				AccIP.append(AccIP_json)
			all_data['acc']=AccIP
			debug(str(all_data))
			#PGetServerGlobal
			sql='select public."PGetServerGlobal"(E\'{"serverid":%s,"searchstring":null,"limitrow":null,"offsetrow":null}\');'%(sid)
			debug(sql)
			curs.execute(sql)
			results_serverglobal = curs.fetchall()[0][0]
			all_data['serverglobal']=json.loads(results_serverglobal)['data'][0]
			debug(str(all_data))
			#PGetServerDisk
			sql='select public."PGetServerDisk"(%s);'%sid
			debug(sql)
			curs.execute(sql)
			result_Disk = curs.fetchall()[0][0]
			debug(str(result_Disk))
			if result_Disk==None:
				result_Disk='[]'
			result_Disk=json.loads(result_Disk)
			m=0
			n=0
			for i in result_Disk:
				(error,_DskStat)=DskStat(None,sid,i['disk_sn'],common.get_inner_master_ip())
				debug('_DskStaterror'+str(error))
				debug('_DskStat:%s'%str(_DskStat))
				i['diskstat']=0 #0 异常 1 正常
				if error==0:
					_DskStat=json.loads(_DskStat.replace('L',''))
					_time_local=time.time()
					debug('_time_local:%d'%int(_time_local))
					if (_time_local-int(_DskStat[1]))<=300 and _DskStat[0]==1:
						i['diskstat']=1
				i["xy"]='%s,%s'%(m,n)
				if n==5:
					m+=1
					n=0
				else:
					n+=1
			all_data['disk']=result_Disk
			debug(str(all_data))
			#PGetApplicationConfig
			sql='select public."PGetApplicationConfig"(null,null);'
			debug(sql)
			curs.execute(sql)
			result_ApplicationConfig = curs.fetchall()[0][0]
			debug(result_ApplicationConfig)
			result_ApplicationConfig=json.loads(result_ApplicationConfig)
			for i in result_ApplicationConfig['data']:
				debug(str(i['ApplicationName']))
				debug(str(i['EnableServicePort']))
				debug(str(i['EnableMap']))
				i['PORT']=0
				if i['EnableServicePort']==True:
					(error,_AppStat)=AppStat(None,sid,i['ApplicationName'],'PORT',common.get_inner_master_ip())
					debug(str(error)+','+str(_AppStat)+'=AppStat(None,'+str(sid)+','+str(i['ApplicationName'])+',PORT)')
					debug(str(_AppStat))
					if error==0:
						_AppStat=json.loads(_AppStat.replace('L',''))
						_time_local=time.time()
						debug('_time_local:%d'%int(_time_local))
						if (_time_local-int(_AppStat[1]))<=300 and _AppStat[0]==1:
							i['PORT']=1
				else:
					i['PORT']='off'
				i['SOCK']=0
				if i['EnableMap']==True:
					(error,_AppStat)=AppStat(None,sid,i['ApplicationName'],'SOCK',common.get_inner_master_ip())
					debug(str(error)+','+str(_AppStat)+'=AppStat(None,'+str(sid)+','+str(i['ApplicationName'])+',SOCK)')
					debug(str(_AppStat))
					if error==0:
						_AppStat=json.loads(_AppStat.replace('L',''))
						_time_local=time.time()
						debug('_time_local:%d'%int(_time_local))
						if (_time_local-int(_AppStat[1]))<=300 and _AppStat[0]==1:
							i['SOCK']=1
				else:
					i['SOCK']='off'
			(error,_DATABASE)=DskStat(None,sid,'DATABASE',common.get_inner_master_ip())
			debug('DATABASE:%s'%str(_DATABASE))
			all_data['DATABASE']=0
			if error==0:
				_DATABASE=json.loads(_DATABASE.replace('L',''))
				_time_local=time.time()
				debug('DATABASE_time_local:%d'%int(_time_local))
				if (_time_local-int(_DATABASE[1]))<=300 and _DATABASE[0]==1:
					all_data['DATABASE']=1
			debug(str(result_ApplicationConfig['data']))
			result_ApplicationConfig['data'].sort(key = lambda x:x["ApplicationName"])
			all_data['app']=result_ApplicationConfig['data']
			#PGetServerEther
			sql='select public."PGetServerEther"(%s);'%(sid)
			debug(sql)
			curs.execute(sql)
			results = curs.fetchall()[0][0]
			debug(str(results))
			if results!=None:
				sql='select public."PGetServerBond"(null,null,%s,null,null);'%(sid)
				curs.execute(sql)
				result_bond=curs.fetchall()[0][0]
				result_bond=json.loads(result_bond)
				bond_eth_id=[]
				for i in result_bond['data']:
					if not i['ether_id_1'] in bond_eth_id:
						bond_eth_id.append(i['ether_id_1'])
					if not i['ether_id_2'] in bond_eth_id:
						bond_eth_id.append(i['ether_id_2'])
				results=json.loads(results)
				debug(str(results))
				for i in results:
					if i['ether_id'] in bond_eth_id:
						i['bond_include']=1
					else:
						i['bond_include']=0
					debug(str(i))
					sql='select public."PGetServerIPV4"(null,E\'%s\',null,null,null,%s,null,null,true);'%(i["ether_name"],sid)
					debug(sql)
					curs.execute(sql)
					result = curs.fetchall()[0][0]
					debug(str(result))
					result=json.loads(result)
					debug(str(result))
					i['ip_addr']=''
					i['mask_addr']=''
					str_tmp = "'duplex':'0','speed':'0','mtu':'0','bytes_sent':'0','bytes_recv':'0','packets_sent':'0','packets_recv':'0','errin':'0','errout':'0','dropin':'0','dropout':'0'"
					debug(str(str_tmp))
					str_tmp='{%s}'%(str_tmp)
					i['str_tmp']=str_tmp
					for j in result["data"]:
						if j['netdev_clas']!=0:
							continue
						i['ip_addr']=j['ip_addr']
						i['mask_addr']=j['mask_addr']
					debug('NetStat')
					(error,_NetStat)=NetStat(None,sid,i["ether_name"],common.get_inner_master_ip())
					debug(str(_NetStat))
					debug(str(error))
					eth_stat=0
					if error!=0:
						isrun=0
						isup=0
					else:
						tmp = _NetStat.split("isup=")
						if len(tmp) > 1:
							tmp_list = tmp[1].split(",")
							isup = 1 if tmp_list[0]=="True" else 0
						else:
							isup = 0
						####
						tmp = _NetStat.split("isrun=") 
						if len(tmp) > 1:
							tmp_list = tmp[1].split("'")
							isrun = 1 if tmp_list[0]=="True" else 0
						else:
							isrun = 0
						tmp = _NetStat.split(" ")
						_time=tmp[-1].split('L')[0]
						debug('_time:%s'%_time)
						debug('_time:%d'%int(_time))
						if len(_time)==10:
							_time_local=time.time()
							debug('_time_local:%d'%int(_time_local))
							if (_time_local-int(_time))<=300:
								eth_stat=1
						debug(str(tmp))
						debug('split_str')
						str_tmp = split_str(_NetStat)
						debug(str(str_tmp))
						str_tmp='{%s}'%(str_tmp)
						i['str_tmp']=str_tmp
						i['isrun']=isrun
						i['isup']=isup
						i['eth_stat']=eth_stat
					debug('f_display_none')
					f_display_none = 0 ##显示网卡状态
					if isup == 0 and i['ip_addr'] == "": ##表示 该网卡 异常
						f_display_none = 1 # 不显示网卡状态
					i["f_display_none"]=f_display_none
				all_data['eth_list']=results
			else:
				all_data['eth_list']=[]
			all_data['gluster_type']=g_cluster_type
			all_data['gluster_status']=False
			all_data['GlsterPeer']=''
			all_data['GlsterInfo']=''
			if g_cluster_type=='gluster':
				(error,GlsterPeer)=GetGlsterPeer(None, sid, server=common.get_inner_master_ip(), listen=6379, dbcode=2)
				if error==0:
					all_data['GlsterPeer']=GlsterPeer
				else:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				(error,GlsterInfo)=GetGlsterInfo(None, sid, server=common.get_inner_master_ip(), listen=6379, dbcode=2)
				if error==0:
					all_data['GlsterInfo']=GlsterInfo
					GlsterInfo_arr=GlsterInfo.split('\n')
					for i in GlsterInfo_arr:
						if 'Status: ' in i and  i.index('Status: ')==0:
							if i[len('Status: '):]=='Started':
								all_data['gluster_status']=True
				else:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			if g_cluster_type=='gluster' or g_cluster_type=='double':
				sql='select client_addr, pg_xlog_location_diff(pg_current_xlog_location(),replay_location) from pg_stat_replication;'
				curs.execute(sql)
				result = curs.fetchall()
				sql='select * from pg_replication_slots;'
				curs.execute(sql)
				node_result = curs.fetchall()
				all_data['is_server_master']=None;
				if g_cluster_type=='double':
					all_data['is_server_master']=True
				else:
					(error,GlsterMaster)=GetGlsterMaster(None, sid, server=common.get_inner_master_ip(), listen=6379, dbcode=2)
					if error==0:
						all_data['is_server_master']=(GlsterMaster==sid)
					else:
						return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				all_data['replication_slots']=[];
				if g_cluster_type=='double':
					if len(node_result)<1:
						pg_xlog_item={"node":1,"active":False}
					else:
                                        	node_result_item=node_result[0]
                                        	pg_xlog_item={"node":1,"active":(node_result_item[5]!=u'0')}
                                        debug(str(pg_xlog_item))
                                        if pg_xlog_item['active']:
						if len(result)<1:
							pg_xlog_item["value"]=999999999
						else:
                                                	result_item=result[0]
                                                	pg_xlog_item["value"]=int(result_item[1])
                                        all_data['replication_slots'].append(pg_xlog_item)
                                else:
					for node_result_item in node_result:
						pg_xlog_item={"node":int(node_result_item[0][4:5]),"active":(node_result_item[5]!=u'0')}
						if pg_xlog_item['active']:
							for result_item in result:
								if node_result_item[0][4:5]==result_item[0].split('.')[-1]:
									pg_xlog_item["value"]=int(result_item[1])
									break
						all_data['replication_slots'].append(pg_xlog_item)
			else:
				pass
			
			_time_local=time.time()
			all_data['local_time'] = _time_local
			
			drbd_status0= '';
			drbd_status1= '';
			if g_cluster_type=='double':
				try:
					result = DrbdStat(None, int(sid), server=common.get_inner_master_ip(), listen=6379, dbcode=2);
					#result ='[["本地1234ssd","对端adsasdda"],["本地adasd","对端asdasdad"]]'
					result_list = json.loads(str(result).replace("'",'"'))
					if len(result_list) > 1:
						drbd_status0 = result_list[0][0] +'/'+result_list[0][1];
						drbd_status1 = result_list[1][0] +'/'+result_list[1][1];
					else:
						drbd_status0 = result_list[0][0] +'/'+result_list[0][1];
				except pyodbc.Error,e:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				
			all_data['drbd_status0'] = drbd_status0.replace('\n',"</br>").replace('\r',"</br>").replace('\t',"&nbsp;&nbsp;&nbsp;&nbsp;").replace('"','\\"').replace('^','').replace(b'\x1b','');
			all_data['drbd_status1'] = drbd_status1.replace('\n',"</br>").replace('\r',"</br>").replace('\t',"&nbsp;&nbsp;&nbsp;&nbsp;").replace('"','\\"').replace('^','').replace(b'\x1b','');
			debug(str(json.dumps(all_data)))
			return '{"Result":true,"info":%s}'%(str(json.dumps(all_data)))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@colony_list.route('/delect_disk',methods=['GET','POST'])
def delect_disk():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	disk_str = request.form.get('a1')
	serverid = request.form.get('a2')
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
	snlist = disk_str.split(",")
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			for index in snlist:
				sql = "delete from server_disk where disk_sn = '%s';" %(index)
				curs.execute(sql)
			conn.commit()
			task_content = "[global]\nclass = taskdisk\ntype = get_sql_data\ns_id = %d\n" %(int(serverid))
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@colony_list.route('/flash_disk',methods=['GET','POST'])
def flash_disk():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	sn_arr = request.form.get('a1')
	id_arr = request.form.get('a2')
	serverid = request.form.get('a3')
	num = request.form.get('a4')
	if(num < 0):
		num = 1
	else:
		num = int(num)
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
			if id_arr == "":
				fin_ids = []
			else:
				fin_ids = id_arr.split(',')
			for sid in fin_ids:
				sql = "select disk_loc,disk_sn from server_disk where disk_id = %d;" %(int(sid))# in (select disk_id from server_osd where osd_id
				curs.execute(sql)
				results = curs.fetchall()
				if results :
					loc = results[0][0].encode('utf-8')
					sn = results[0][1].encode('utf-8')
				else:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				if(1 == num):
					task_content = '[global]\nclass=taskdisk\ntype=blink_function\nsn=%s\ndevice=%s\n' % (sn,loc)
				else:
					task_content = '[global]\nclass=taskdisk\ntype=self_kill_process\nsn=%s\ndevice=%s\n' % (sn,loc)
				
				if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			if sn_arr == "":
				fin_sns = []
			else:		
				fin_sns = sn_arr.split(',')
			for sn in fin_sns:
				sql = "select disk_loc from server_disk where disk_sn = '%s';" %(str(sn))
				curs.execute(sql)
				results = curs.fetchall()
				if results :
					loc = results[0][0].encode('utf-8')
				else:
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
				if(1 == num):
					task_content = '[global]\nclass=taskdisk\ntype=blink_function\nsn=%s\ndevice=%s\n' % (sn,loc)
				else:
					task_content = '[global]\nclass=taskdisk\ntype=self_kill_process\nsn=%s\ndevice=%s\n' % (sn,loc)
				if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
					return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
@colony_list.route('/update_disk',methods=['GET','POST'])
def update_disk():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	wrong = request.form.get('a1')
	ready = request.form.get('a2')
	serverid = request.form.get('a3')
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select disk_sn,disk_stat from server_disk where disk_id = %s;" % (MySQLdb.escape_string(wrong))
			curs.execute(sql)
			result = curs.fetchall()
			old_sn = result[0][0].encode('utf-8')
			disk_stat = result[0][1]
			sql = "select disk_size from server_disk where disk_sn ='%s';" % ready
			curs.execute(sql)
			disk_size = int(curs.fetchall()[0][0])
			task_content = '[global]\nclass = taskdisk\ntype = replace_req\noldsn=%s\nnewsn=%s\noldstat=%d\nnew_size=%d\n' % (old_sn,ready,disk_stat,disk_size)
			if False == task_client.task_send(str(serverid), task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
@colony_list.route('/add_disk',methods=['GET','POST'])
def add_disk():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	sess = request.form.get('a0')
	disk_str = request.form.get('a1')
	serverid = request.form.get('a2')
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
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "select count(*) from server_disk where server_id=%s and disk_stat = 0;" % (MySQLdb.escape_string(serverid))
			curs.execute(sql)
			disk_count = int(curs.fetchall()[0][0])
			listtmp = disk_str.split(',')
			disklen = len(listtmp)
			sql = "select raid_disk_count from server_global where server_id=%s;" % (MySQLdb.escape_string(serverid))
			curs.execute(sql)
			limitdsk = int(curs.fetchall()[0][0])
			if limitdsk > disklen:
				return "{\"Result\":false,\"ErrMsg\":\"配置错误\"}"
			task_content = "[global]\nclass = taskdisk\ntype = get_sql_data\ns_id = %d\n" %(int(serverid))
			if False == task_client.task_send(defines.MASTER_SERVER_ID, task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			task_content = '[global]\nclass = taskdisk\ntype = add_req\nsns=%s\n' % (disk_str)
			if False == task_client.task_send(str(serverid), task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":true,\"info\":\"\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
