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
from generating_log import system_log
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from htmlencode import parse_sess
from htmlencode import check_role
from logbase import common
from comm_function import get_user_perm_value
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
host_test = Blueprint('host_test',__name__)

SIZE_PAGE = 20
ErrorNum = 10000
ERRNUM_MODULE = 1000

def debug(c):
	return 0
        path = "/var/tmp/debug_ccp_host_test.txt"
        fp = open(path,"a+")
        if fp :
		fp.write(str(c))
		fp.write('\n')
		fp.close()
def sendlog(oper,desc,cname):
	client_ip = request.remote_addr    #获取客户端IP
	happen = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))  #获取当前时间
	sqlconf = "insert into logs_conf (usr,client,happen,oper,mesg,level) values ('%s','%s','%s','%s','%s','');" %(cname,client_ip,happen,oper.decode("utf-8"),desc.decode("utf-8"))
	LogSet(None, sqlconf, 6)
	
#HTMLEncode111 
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
@host_test.route('/host_test_trust',methods=['GET','POST'])
def host_test_trust():
    #页面跳转函数
    #参数 tasktype = 添加-1
    #a=id
    session = request.form.get("se")
    tasktype = request.form.get("tasktype")
    page = request.form.get("c")
    search_typeall=request.form.get("d")
    search_typeall_new=request.form.get('e')
    if page < 0 or page == None:
        page = "1"
    if tasktype < 0 or tasktype == None:
        tasktype = "1"
    if search_typeall < 0 or search_typeall == None:
        search_typeall = ""
    if search_typeall_new < 0 or search_typeall_new == None:
        search_typeall_new = ":"
    if tasktype == "3":
        id='0'
        t = "host_test_list.html"
    else:
        id = request.form.get("a")
        if id < 0 or id == None:
            id = "0"
        t = "host_test_add.html"
    client_ip = request.remote_addr
    (error,system_user,mac) = SessionCheck(session,client_ip)
    perm=get_user_perm_value(system_user)
    perm_json=json.loads(perm)
    perm=0
    for i in perm_json:
        if i['SubMenuId']==14 and i['SystemMenuId']==3:
            perm=i['Mode']
            break
    return render_template(t,tasktype=tasktype,a=id,c=page,d=search_typeall,e=search_typeall_new,se=session,perm=perm)

#从"连接测试"跳转到"主机管理"
@host_test.route('/goto_host_manage',methods=['GET','POST'])
def goto_host_manage():
    return render_template('host_list.html')

#退出"连接测试"
@host_test.route('/goto_access_control',methods=['GET','POST'])
def goto_access_control():
    return render_template('access_control.html')

#重新进入"连接测试"
@host_test.route('/reload_host_test_list',methods=['GET','POST'])
def reload_host_test_list():
    pageStat = request.form.get("pageStat")
    return render_template("host_test_list.html",pageStat=pageStat)
@host_test.route('/stop_connectplan',methods=['GET','POST'])
def stop_connectplan():
    reload(sys)
    sys.setdefaultencoding('utf-8')
####  检验会话  ####
    session = request.form.get('a0')
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
    if check_role(system_user,'主机管理') == False:
        return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
####  检验结束  ####
    planId =  request.form.get('a1')
    planname =  request.form.get('a2')
    debug(planId)                     #计划id
    if planId<0 or planId=="0" or planId=="":
        planId="null"
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PStopBatchConnectPlan\"(%s);" % (planId)
            curs.execute(sqlStr)
            results = curs.fetchall()[0][0]
            if not system_log(system_user,'停用计划：%s'%planname,'成功','运维管理>连接测试'):
                return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
            return '{"Result":true,"info":%s}' % str(results)  # results:{"totalrow":2,data:[2 len array]}
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/start_connectplan',methods=['GET','POST'])
def start_connectplan():
    reload(sys)
    sys.setdefaultencoding('utf-8')
####  检验会话  ####
    session = request.form.get('a0')
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
    if check_role(system_user,'主机管理') == False:
        return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)        
####  检验结束  ####
    planId =  request.form.get('a1')
    planname =  request.form.get('a2')
    if planId<0 or planId=="0" or planId=="":
        planId="null"
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PstartBatchConnectPlan\"(%s);" % (planId)
            debug(sqlStr)    
            curs.execute(sqlStr)
            results = curs.fetchall()[0][0]
            if not system_log(system_user,'启用计划：%s'%planname,'成功','运维管理>连接测试'):
                return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
            return '{"Result":true,"info":%s}' % str(results)  # results:{"totalrow":2,data:[2 len array]}
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/start_connecttask',methods=['GET','POST'])
def start_connecttask():
    reload(sys)
    sys.setdefaultencoding('utf-8')
####  检验会话  ####
    session = request.form.get('a0')
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
    if check_role(system_user,'主机管理') == False:
        return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
####  检验结束  ####
    task_id =  request.form.get('a1')
    task_name =  request.form.get('a2')
    debug(task_id)                     #计划id
    if task_id<0 or task_id=="0" or task_id=="":
        task_id="null"
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PStartBatchConnectTask\"(%s);" % (task_id)
            curs.execute(sqlStr)
            results = curs.fetchall()[0][0]
            if not system_log(system_user,'二次测试计划：%s'%task_name,'成功','运维管理>连接测试'):
                return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
            return '{"Result":true,"info":%s}' % str(results)  # results:{"totalrow":2,data:[2 len array]}
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/get_connect_plan',methods=['GET','POST'])
def get_connect_plan():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    ####  检验会话  ####
    session = request.form.get('a0')
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
    ####  检验结束  ####
    planId =  request.form.get('a1')                     #计划id
    search_typeall = request.form.get('a2')                   #计划名称
    paging = request.form.get('a3')                      #获得每页要显示的条目数
    page_num = request.form.get('a4')    
    if search_typeall<0:
        search_typeall=""
    if planId<0 or planId=="0" or planId=="":
        planId="null"
    if paging <0:
        paging = "null"
    else:
        paging=int(paging)
    if page_num < 0:
        page_num = "null"
    else:
        page_num=int(page_num)
    if search_typeall != "":
        search_typeall=search_typeall[:-1]
    Name=''
    searchstring=''
    Period=''
    Execution=''
    Status=''
    Enabled=''
    typeall = search_typeall.split('\t')
    for search in typeall:
        search_s = search.split('-',1)
        if search_s[0]=="Name":
            Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="all":
            #Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
            searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="Period":
            Period=Period+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="Execution":
            Execution=Execution+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="Status":
            Status=Status+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="Enabled":
            Enabled=Enabled+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
    if Name=="":
        Name="null"
    else:
        Name="'%s'"%(Name[:-1])
    if searchstring!="":
        searchstring=searchstring[:-1]
    if Period!="":
        Period=Period[:-1]
	if '天' in Period:
		PeriodType=1
		PeriodValue=int(Period[:-1])
	elif '分钟' in Period:
		PeriodType=2
		PeriodValue=int(Period[:-2])
	elif Period=='所有':
		Period=None
		PeriodType=None
		PeriodValue=None
    else:
	Period=None
	PeriodType=None
	PeriodValue=None
    if Execution!="":
        Execution=Execution[:-1]
	if Execution=='是':
		Execution=True
	elif Execution=='否':
		Execution=False
	elif Execution=='所有':
		Execution=None
    else:
	Execution=None
    if Status!="":
        Status=Status[:-1]
	if '未执行'==Status:
		Status=0
	elif '正在执行'==Status:
		Status=1
	elif '执行完成'==Status:
		Status=2
	elif Status=='所有':
		Status=None
    else:
	Status=None
    if Enabled!="":
        Enabled=Enabled[:-1]
	if '启用'==Enabled:
		Enabled=True
	elif '停用'==Enabled:
		Enabled=False
	elif '所有'==Enabled:
		Enabled=None
    else:
	Enabled=None
    searchconn={}
    searchconn['searchstring']=searchstring
    searchconn['Period']=Period
    searchconn['PeriodType']=PeriodType
    searchconn['PeriodValue']=PeriodValue
    searchconn['Execution']=Execution
    searchconn['Status']=Status
    searchconn['Enabled']=Enabled
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
        paging=(paging-1)*page_num
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PGetBatchConnectPlan\"(%s,%s,E'%s',%s,%s,E'%s');" % (planId,Name,system_user,page_num,paging,searchconn)
            #sqlStr = "select public.\"PGetBatchConnectPlan\"(%s,%s,'%s',%s,%s);" % (planId,Name,system_user,page_num,paging)
            curs.execute(sqlStr)
            results = curs.fetchall()[0][0]
            return '{"Result":true,"info":%s}' % results  # results:{"totalrow":2,data:[2 len array]}
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/save_conn_plan',methods=['GET','POST'])
def save_conn_plan():
    module_name=request.form.get('a10')
    if module_name<0:
        module_name='运维管理>连接测试'
    reload(sys)
    sys.setdefaultencoding('utf-8')
####  检验会话  ####
    session = request.form.get('a0')
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
####  检验结束  ####
    plan_info = request.form.get('a1')
    md5_str = request.form.get('m1')
    if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
        return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
    else:
        md5_json = StrMD5(plan_info);##python中的json的MD5
        if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
            return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

    if check_role(system_user,'主机管理') == False:
        return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)    
    plan_info_json=json.loads(plan_info)
    try:
    	with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
        	debug('------')
		sqlStr = "select public.\"PSaveBatchConnectPlan\"(E'%s')" %(plan_info)
        	debug(str(sqlStr))
        	curs.execute(sqlStr)
        	debug('1111')
		results = curs.fetchall()[0][0]
        	debug(str(results))
		results_json=json.loads(results)
        	if plan_info_json['BatchConnectPlanId']==0:
        	    oper='创建计划：%s'%plan_info_json['BatchConnectPlanName']
        	else:
        	    oper='编辑计划：%s'%plan_info_json['BatchConnectPlanName']
        	if results_json['Result']:
        	    if not system_log(system_user,oper,'成功',module_name):
        	        return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
        	else:
        	    if not system_log(system_user,oper,results_json['ErrMsg'],module_name):
        	        return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
        	return results
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	return '{"Result":false,"ErrMsg":"连接数据库失败"}'

@host_test.route('/del_conn_plan',methods=['GET','POST'])
def del_conn_plan():
    reload(sys)
    sys.setdefaultencoding('utf-8')
####  检验会话  ####
    session = request.form.get('a0')
    module_name=request.form.get('a10')
    if module_name<0:
        module_name='运维管理>连接测试'
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
    if check_role(system_user,'主机管理') == False:
        return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno) 
####  检验结束  ####
    idList = request.form.get('a1').split(',')     #存有计划id的数组
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            all_arr=[]
            success_num=0
            fail_num=0
            fail_arr=[]
            success_arr=[]
            for planid in idList:
                if planid=='':
                    continue
                id_arr=planid.split('\t')
                value=id_arr[0]
                all_arr.append(id_arr[1])
                sqlStr = "select public.\"PDeleteBatchConnectPlan\"(%s);" % str(value)
                curs.execute(sqlStr)
                result = curs.fetchall()[0][0]
                result_json=json.loads(result)
                if result_json['Result']:
                    success_num+=1
                    success_arr.append(id_arr[1])
                    curs.commit()   #提交修改
                else:
                    fail_num+=1
                    fail_arr.append(id_arr[1])
            oper='删除计划：%s'%('、'.join(all_arr))
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
            return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}"%(success_num,fail_num,mesg) 
            return result
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/get_conn_task',methods=['GET','POST'])
def get_conn_task_arr():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    ####  检验会话  ####
    session = request.form.get('a0')
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
    ####  检验结束  ####
    ConnectTaskId = request.form.get('a1')
    search_typeall=request.form.get('a2')
    paging=request.form.get('a3')
    page_num=request.form.get('a4')
    if ConnectTaskId<0 or ConnectTaskId=='0' or ConnectTaskId==None:
        ConnectTaskId='null'
    if page_num<0 or page_num==None:
        page_num='null'
    else:
        page_num=int(page_num)
    if search_typeall<0 or search_typeall==None:
        search_typeall=''
    if paging<0 or paging==None:
        paging='null'
    else:
        paging=int(paging)
    if search_typeall != "":
        search_typeall=search_typeall[:-1]
    typeall = search_typeall.split('\t')
    Name=''
    searchstring=''
    Status=''
    for search in typeall:
        search_s = search.split('-',1)
        if search_s[0]=="Name":
            Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="all":
            #Name=Name+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
            searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="Status":
            Status=Status+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
    if Name=="":
        Name="null"
    else:
        Name="E'%s'"%(Name[:-1])
    if Status!='':
	Status=Status[:-1]  
	if Status=='未执行':
		Status=0
	elif Status=='正在执行':
		Status=1
	elif Status=='执行完成':
		Status=2
    else:
	Status=None
    searchconn={}
    searchconn['searchstring']=searchstring
    searchconn['Status']=Status
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
        paging=(paging-1)*page_num
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PGetBatchConnectTask\"(%s,%s,null,null,%s,%s,E'%s');" % (ConnectTaskId,Name,page_num,paging,searchconn)
            #sqlStr = "select public.\"PGetBatchConnectTask\"(%s,%s,null,null,%s,%s);" % (ConnectTaskId,Name,page_num,paging)
            curs.execute(sqlStr)           
            result = curs.fetchall()[0][0]
            return "{\"Result\":true,\"info\":%s}" % result
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/get_conn_taskdetails',methods=['POST','GET'])
def get_conn_taskdetails():
    reload(sys)
    sys.setdefaultencoding('utf-8')
    ####  检验会话  ####
    session = request.form.get('a0')
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
    ####  检验结束  ####
    ConnectTaskId = request.form.get('a1')
    search_typeall=request.form.get('a2')
    paging=request.form.get('a3')
    page_num=request.form.get('a4')
    if ConnectTaskId<0 or ConnectTaskId=='0' or ConnectTaskId==None:
        ConnectTaskId='null'
    if page_num<0 or page_num==None:
        page_num='null'
    else:
        page_num=int(page_num)
    if search_typeall<0 or search_typeall==None:
        search_typeall=''
    if paging<0 or paging==None:
        paging='null'
    else:
        paging=int(paging)
    hostip=''
    hostname=''
    protocolname=''
    accountname=''
    Status=''
    searchstring=''
    if search_typeall != "":
        search_typeall=search_typeall[:-1]
    typeall = search_typeall.split('\t')
    for search in typeall:
        search_s = search.split('-',1)
        if search_s[0]=="hostip":
            hostip=hostip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="hostname":
            hostname=hostname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="protocolname":
            protocolname=protocolname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="accountname":
            accountname=accountname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="Status":
            Status=Status+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="all":
            searchstring=searchstring+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
    if hostip=="":
        hostip="null"
    else:
        hostip="E'%s'"%(hostip[:-1])
    if hostname=="":
        hostname="null"
    else:
        hostname="E'%s'"%(hostname[:-1])
    if protocolname=="":
        protocolname="null"
    else:
        protocolname="E'%s'"%(protocolname[:-1])
    if accountname=="":
        accountname="null"
    else:
        accountname="E'%s'"%(accountname[:-1])
    if searchstring!="":
        searchstring=searchstring[:-1]
    if Status!="":
        Status=Status[:-1]
	if Status=='未执行':
		Status=0
	elif Status=='正在执行':
		Status=1
	elif Status=='测试成功':
		Status=2
	elif Status=='连接失败':
		Status=3
	elif Status=='登录失败':
		Status=4
    else:
	Status=None
    searchconn={}
    searchconn['searchstring']=searchstring
    searchconn['Status']=Status
    searchconn=json.dumps(searchconn)
    hostip=hostip.replace("\\\\","\\\\\\\\")
    hostip=hostip.replace(".","\\\\.")
    hostip=hostip.replace("?","\\\\?")
    hostip=hostip.replace("+","\\\\+")
    hostip=hostip.replace("(","\\\\(")
    hostip=hostip.replace("*","\\\\*")
    hostip=hostip.replace("[","\\\\[")
    hostname=hostname.replace("\\\\","\\\\\\\\")
    hostname=hostname.replace(".","\\\\.")
    hostname=hostname.replace("?","\\\\?")
    hostname=hostname.replace("+","\\\\+")
    hostname=hostname.replace("(","\\\\(")
    hostname=hostname.replace("*","\\\\*")
    hostname=hostname.replace("[","\\\\[")
    protocolname=protocolname.replace("\\\\","\\\\\\\\")
    protocolname=protocolname.replace(".","\\\\.")
    protocolname=protocolname.replace("?","\\\\?")
    protocolname=protocolname.replace("+","\\\\+")
    protocolname=protocolname.replace("(","\\\\(")
    protocolname=protocolname.replace("*","\\\\*")
    protocolname=protocolname.replace("[","\\\\[")
    accountname=accountname.replace("\\\\","\\\\\\\\")
    accountname=accountname.replace(".","\\\\.")
    accountname=accountname.replace("?","\\\\?")
    accountname=accountname.replace("+","\\\\+")
    accountname=accountname.replace("(","\\\\(")
    accountname=accountname.replace("*","\\\\*")
    accountname=accountname.replace("[","\\\\[")
    searchconn=searchconn.replace("\\","\\\\")
    searchconn=searchconn.replace(".","\\\\\\\\.")
    searchconn=searchconn.replace("?","\\\\\\\\?")
    searchconn=searchconn.replace("+","\\\\\\\\+")
    searchconn=searchconn.replace("(","\\\\\\\\(")
    searchconn=searchconn.replace("*","\\\\\\\\*")
    searchconn=searchconn.replace("[","\\\\\\\\[")
    if paging!="null":
        paging=(paging-1)*page_num
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PGetBatchConnectTaskDetails\"(%s,%s,%s,%s,%s,null,null,%s,%s,E'%s');" % (ConnectTaskId,hostip,hostname,protocolname,accountname,page_num,paging,searchconn)
            #sqlStr = "select public.\"PGetBatchConnectTaskDetails\"(%s,%s,%s,%s,%s,null,null,%s,%s);" % (ConnectTaskId,hostip,hostname,protocolname,accountname,page_num,paging)
            curs.execute(sqlStr)           
            result = curs.fetchall()[0][0]
            return "{\"Result\":true,\"info\":%s}" % result
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/get_details_data',methods=['POST','GET'])
def get_details_data():
    debug('get_details_data')
    reload(sys)
    sys.setdefaultencoding('utf-8')
    ####  检验会话  ####
    session = request.form.get('a0')
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
    ####  检验结束  ####
    ConnectTaskId = request.form.get('a1')
    id_value_str=request.form.get('a3')
    search_typeall=request.form.get('a2')
    if ConnectTaskId<0 or ConnectTaskId=='0' or ConnectTaskId==None:
        ConnectTaskId='null'
    if search_typeall<0 or search_typeall==None:
        search_typeall=''
    hostip=''
    hostname=''
    protocolname=''
    accountname=''
    if search_typeall != "":
        search_typeall=search_typeall[:-1]
    typeall = search_typeall.split('\t')
    for search in typeall:
        search_s = search.split('-',1)
        if search_s[0]=="hostip":
            hostip=hostip+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="hostname":
            hostname=hostname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="protocolname":
            protocolname=protocolname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
        elif search_s[0]=="accountname":
            accountname=accountname+MySQLdb.escape_string(search_s[1]).decode("utf-8")+"\n"
    if hostip=="":
        hostip="null"
    else:
        hostip="E'%s'"%(hostip[:-1])
    if hostname=="":
        hostname="null"
    else:
        hostname="E'%s'"%(hostname[:-1])
    if protocolname=="":
        protocolname="null"
    else:
        protocolname="E'%s'"%(protocolname[:-1])
    if accountname=="":
        accountname="null"
    else:
        accountname="E'%s'"%(accountname[:-1])
    hostip=hostip.replace("\\\\","\\\\\\\\")
    hostip=hostip.replace(".","\\\\.")
    hostip=hostip.replace("?","\\\\?")
    hostip=hostip.replace("+","\\\\+")
    hostip=hostip.replace("(","\\\\(")
    hostip=hostip.replace("*","\\\\*")
    hostip=hostip.replace("[","\\\\[")
    hostname=hostname.replace("\\\\","\\\\\\\\")
    hostname=hostname.replace(".","\\\\.")
    hostname=hostname.replace("?","\\\\?")
    hostname=hostname.replace("+","\\\\+")
    hostname=hostname.replace("(","\\\\(")
    hostname=hostname.replace("*","\\\\*")
    hostname=hostname.replace("[","\\\\[")
    protocolname=protocolname.replace("\\\\","\\\\\\\\")
    protocolname=protocolname.replace(".","\\\\.")
    protocolname=protocolname.replace("?","\\\\?")
    protocolname=protocolname.replace("+","\\\\+")
    protocolname=protocolname.replace("(","\\\\(")
    protocolname=protocolname.replace("*","\\\\*")
    protocolname=protocolname.replace("[","\\\\[")
    accountname=accountname.replace("\\\\","\\\\\\\\")
    accountname=accountname.replace(".","\\\\.")
    accountname=accountname.replace("?","\\\\?")
    accountname=accountname.replace("+","\\\\+")
    accountname=accountname.replace("(","\\\\(")
    accountname=accountname.replace("*","\\\\*")
    accountname=accountname.replace("[","\\\\[")
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PGetBatchConnectTaskDetails\"(%s,%s,%s,%s,%s,null,null,null,null);" % (ConnectTaskId,hostip,hostname,protocolname,accountname)
            curs.execute(sqlStr)           
            detail_data_all = curs.fetchall()[0][0]
            #return "{\"Result\":true,\"info\":%s}" % result
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    detail_data_all=json.loads(detail_data_all)['data']
    detail_data=[]
    host_id_arr=[]
    '''
        host_value_arr=[]
        for i,item in enumerate(detail_data_all):
            host_index_value='%s:%s'%(str(item['HostId']),str(item['HostName']))
            if not (host_index_value in host_id_arr):
                if item['HostId']==None:
                    detail_item={
                        #主机ip
                        "HostIP": item['HostIP'],
                        #主机名
                        "HostName": item['HostName'],
                        #设备类型
                        "DeviceTypeName": '',
                        #描述
                        "Description": '',
                        #访问速度
                        "AccessRate": '',
                        #唯一登陆
                        "EnableLoginLimit": '',
                        #主机组
                        "HGroupSet": '',
                        #账号详情
                        "detail_data":[]
                    }
                else:
                    try:
                        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
                        sqlStr = "select public.\"PGetHost\"(%s,null,null);" % (item['HostId'])
                        curs.execute(sqlStr)           
                        host_item = curs.fetchall()[0][0]
                        #return "{\"Result\":true,\"info\":%s}" % result
                    except pyodbc.Error,e:
                        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
                    if host_item！=None:
                        host_item=json.loads(host_item)
                        if host_item['AccessRate']==1:
                            host_item['AccessRate']='正常'
                        elif host_item['AccessRate']==2:
                            host_item['AccessRate']='较慢'
                        elif host_item['AccessRate']==3:
                            host_item['AccessRate']='很慢'
                        if host_item['EnableLoginLimit']:
                            host_item['EnableLoginLimit']='启用'
                        else:
                            host_item['EnableLoginLimit']='不启用'
                        HGroupSet=[]
                        if host_item['HGroupSet']!=None:
                            for j in host_item['HGroupSet']:
                                HGroupSet.append(j['HGName'])
                        detail_item={
                            #主机ip
                            "HostIP": host_item['HostIP'],
                            #主机名
                            "HostName": host_item['HostName'],
                            #设备类型
                            "DeviceTypeName": host_item['DeviceTypeName'],
                            #描述
                            "Description": host_item['Description'],
                            #访问速度
                            "AccessRate": host_item['AccessRate'],
                            #唯一登陆
                            "EnableLoginLimit": host_item['EnableLoginLimit'],
                            #主机组
                            "HGroupSet": '/'.join(HGroupSet)
                        }
                    else:
                        detail_item={
                            #主机ip
                            "HostIP": item['HostIP'],
                            #主机名
                            "HostName": item['HostName'],
                            #设备类型
                            "DeviceTypeName": '',
                            #描述
                            "Description": '',
                            #访问速度
                            "AccessRate": '',
                            #唯一登陆
                            "EnableLoginLimit": '',
                            #主机组
                            "HGroupSet": ''
                        }
                detail_data.append(detail_item)
                host_id_arr.append(host_index_value)
                host_value_arr.append(host_item)
            host_index=host_id_arr.index(host_index_value)
            detail_data[host_index]['detail_data']
    '''
    debug(str(id_value_str))
    id_value_arr=id_value_str.split(',')
    debug(str(len(detail_data_all)))
    for i in detail_data_all:
	debug('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        #debug(str(i))
	debug(str(i['BatchConnectTaskDetailId']))
	#debug(str(id_value_arr))
	debug(str(str(i['BatchConnectTaskDetailId']) in id_value_arr))
	if str(i['BatchConnectTaskDetailId']) in id_value_arr:
	    debug('-------------------------------------if')
	    debug(str(i['HostId']))
	    debug(str(i['HostName']))
    	    debug(str(i['HostIP']))
	    debug(str(i['HostId'])+str(i['HostName'])+str(i['HostIP']))
	    host_index_value=str(i['HostId'])+':'+str(i['HostName'])+':'+str(i['HostIP'])
            debug(str(host_index_value))
	    if not (host_index_value in host_id_arr):
                debug('------------------------')
		detail_item={
                    #主机ip
                    "HostIP": i['HostIP'],
                    #主机名
                    "HostName": i['HostName'],
                    # #设备类型
                    # "DeviceTypeName": '',
                    # #描述
                    # "Description": '',
                    # #访问速度
                    # "AccessRate": '',
                    # #唯一登陆
                    # "EnableLoginLimit": '',
                    # #主机组
                    # "HGroupSet": '',
                    #账号详情
                    "detail_data":[]
                }
                debug(str(detail_item))
		detail_data.append(detail_item)
                debug(str(len(detail_data)))
		debug(str(host_index_value))
		host_id_arr.append(host_index_value)
		debug(str(len(host_id_arr)))
            debug(str(host_id_arr))
	    host_index=host_id_arr.index(host_index_value)
            debug(str(host_index))
	    # case 0: item.Status = '未执行'; break;
            # case 1: item.Status = '正在执行'; break;
            # case 2: item.Status = '执行成功'; break;
            # case 3: item.Status = '连接失败'; break;
            # case 4: item.Status = '登录失败'; break;
            if i['Status']==0:
                i['Status']='未执行'
            elif i['Status']==1:
                i['Status']='正在执行'
            elif i['Status']==2:
                i['Status']='执行成功'
            elif i['Status']==3:
                i['Status']='连接失败'
            elif i['Status']==4:
                i['Status']='登录失败'
            detail_acc_data={
                "ProtocolName":i['ProtocolName'],
                "Port":str(i['Port']),
                "AccountName":i['AccountName'],
                "Status":i['Status']
            }
	    debug(str(detail_acc_data))
            debug(str(detail_data[host_index]))
	    debug(str(detail_data[host_index]['detail_data']))
	    detail_data[host_index]['detail_data'].append(detail_acc_data)
	    debug(str(detail_data[host_index]['detail_data']))
	    debug(str(detail_data))
    	    debug('----------------------------if end')
    debug('------------------------------for end')
    debug(str(detail_data))
    detail_data=json.dumps(detail_data)
    debug(str(detail_data))
    return "{\"Result\":true,\"info\":%s}" % str(detail_data)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@host_test.route('/get_host_dir',methods=['POST','GET'])
def get_host_dir():
    reload(sys)
    sys.setdefaultencoding('utf-8')
####  检验会话  ####
    session = request.form.get('a0')
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
####  检验结束  ####
    userCode = "E\'" + str( request.form.get('userCode')) + "\'"
    hgroupId = str( request.form.get('hgroupId'))
    try:
        with pyodbc.connect( StrSqlConn('BH_CONFIG')) as conn, conn.cursor() as curs:
            sqlStr = "select public.\"PGetHostDirectory\"(%s,%s,0,0,null,null)" % (userCode.decode("utf-8"),hgroupId)
            curs.execute(sqlStr)
            results = curs.fetchall()[0][0]
            return '{"Result":true,"info":%s}' % results
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
