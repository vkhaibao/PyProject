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
from htmlencode import check_role
from htmlencode import parse_sess

from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 

env = Environment(loader = FileSystemLoader('templates'))
app = Flask(__name__)
alias_show = Blueprint('alias_show',__name__)

SIZE_PAGE = 20
ERRNUM_MODULE = 35000
ERRNUM_MODULE_top = 36000
def debug(c):
	return 0
        path = "/var/tmp/debugalias.txt"
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

#1创建 2编辑 3列表
@alias_show.route('/alias_show_',methods=['GET','POST'])
def alias_show_():
    tasktype = request.form.get("tasktype")
    aliasId = request.form.get("a")
    paging = request.form.get("b")
    search_typeall = request.form.get("c")
    se = request.form.get("a0")
    if se ==None or se<0:
        se =request.args.get("a0")
    e = request.form.get("e")
    if tasktype < 0:
        tasktype = "3"
    if search_typeall<0:
        search_typeall=''
    if e<0:
        e=':'
    if paging<0:
        paging='1'
    if tasktype == "1" or tasktype == "2":
        t = "alias_add.html"
    elif tasktype == "3":
        t = "alias_list.html"
        aliasId="0"
    return render_template(t,tasktype=tasktype,a=aliasId,b=paging,c=search_typeall,e=e,se=se)

@alias_show.route('/save_alias',methods=['GET','POST'])
def save_alias():
    ###session 检查
    reload(sys)
    sys.setdefaultencoding('utf-8')
    sess = request.form.get('a0')
    alias_json=request.form.get('a1')
    md5_str = request.form.get('m1')
	
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
	md5_json = StrMD5(alias_json);##python中的json的MD5
	if(parse_sess(md5_str,sess,md5_json) == False): # md5_json 是python里面json数据的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
    alias_json=json.loads(str(alias_json))
    alias_json['UserCode']=system_user
    try:
        with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
            sql="select public.\"PSaveHostAccountAliasName\"(E'%s');"%(str(json.dumps(alias_json)))
            debug(str(sql))
            curs.execute(sql)
            results = curs.fetchall()[0][0]
            results_json=json.loads(results)
            if alias_json['HostAccountAliasNameId']=='0':
                oper='创建别名：%s'%alias_json['HostAccountAliasName']
            else:
                oper='编辑别名：%s'%alias_json['HostAccountAliasName']
            if not results_json['Result']:
                if not system_log(system_user,oper,results_json['ErrMsg'],'访问工具>别名管理'):
                    return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
            else:
			    # return results 
                if not system_log(system_user,oper,'成功','访问工具>别名管理'):
                    return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
        conn.commit()
        return results 
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@alias_show.route('/del_alias',methods=['GET','POST'])
def del_alias():
    ###session 检查
    reload(sys)
    sys.setdefaultencoding('utf-8')
    sess = request.form.get('a0')
    delect_str=request.form.get('a1')
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
    delect_id_arr=delect_str.split(',')
    try:
        with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
            all_arr=[]
            succ_num=0
            fail_num=0
            succ_arr=[]
            fail_arr=[]
            for delect_id in delect_id_arr:
                if delect_id==None or delect_id=='':
                    continue
                # PDeleteHostAccountAliasName(id)
                id_arr=delect_id.split('\t')
                delect_id=id_arr[0]
                all_arr.append(id_arr[1])
                sql = "select public.\"PDeleteHostAccountAliasName\"(%s);" % (delect_id)
                curs.execute(sql)
                result = curs.fetchall()[0][0]
                result_json=json.loads(result)
                debug(str(sql))
                if not result_json['Result']:
                    
                    fail_arr.append(id_arr[1])
                    fail_num+=1
                else:
                    succ_arr.append(id_arr[1])
                    succ_num+=1
            conn.commit()
            oper='删除别名：%s'%('、'.join(all_arr))
            if (succ_num+fail_num)==1:
                if succ_num==1:
                    mesg='成功'
                else:
                    mesg=result_json['ErrMsg']
            else:
                if fail_num==0:
                    mesg='成功'
                elif succ_num!=0:
                    mesg='成功：%s，失败：%s'%('、'.join(succ_arr),'、'.join(fail_arr))
                else:
                    mesg='失败：%s'%('、'.join(fail_arr))
            if not system_log(system_user,oper,mesg,'访问工具>别名管理'):
                return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
            return "{\"Result\":true,\"success_num\":%s,\"fail_num\":%s,\"ErrMsg\":\"%s\"}"%(succ_num,fail_num,mesg) 
            return "{\"Result\":true,\"info\":\"删除成功\"}"
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@alias_show.route('/get_alias_Host',methods=['GET','POST'])
def get_alias_Host():
    ###session 检查
    reload(sys)
    sys.setdefaultencoding('utf-8')
    sess = request.form.get('a0')
    hostid=request.form.get('a1')
    nohostservice=request.form.get('a2')
    if hostid<0 or hostid==None:
        hostid='null'
    if nohostservice<0 or nohostservice==None:
        nohostservice='null'
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
            sql="select public.\"PGetHost\"(%s,%s,E'%s');"%(hostid,nohostservice,system_user)
            curs.execute(sql)
            results = curs.fetchall()[0][0]
            return "{\"Result\":true,\"info\":%s}" % results
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

@alias_show.route('/get_alias_list',methods=['GET','POST'])
def get_alias_list():
    ###session 检查
    reload(sys)
    sys.setdefaultencoding('utf-8')
    sess = request.form.get('a0')
    num = request.form.get('a4')
    paging = request.form.get('a3')
    search_typeall = request.form.get('a2')
    HostAccountAliasNameId = request.form.get('a1')
    if HostAccountAliasNameId<0 or HostAccountAliasNameId=="" or HostAccountAliasNameId=="0":
        HostAccountAliasNameId="null"
    if sess < 0:
        sess = ""
    if search_typeall<0:
        search_typeall="{}"
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
    search_typeall=json.loads(search_typeall)
    search_typeall['searchstring']=search_typeall['searchstring'].split('\n')
    search_typeall['AccountName']=search_typeall['AccountName'].split('\n')
    search_typeall['HostName']=search_typeall['HostName'].split('\n')
    search_typeall['HostAccountAliasName']=search_typeall['HostAccountAliasName'].split('\n')
    for i in search_typeall['searchstring']:
        i=MySQLdb.escape_string(i).decode("utf-8")
    for i in search_typeall['AccountName']:
        i=MySQLdb.escape_string(i).decode("utf-8")
    for i in search_typeall['HostName']:
        i=MySQLdb.escape_string(i).decode("utf-8")
    for i in search_typeall['HostAccountAliasName']:
        i=MySQLdb.escape_string(i).decode("utf-8")
    search_typeall['searchstring']='\n'.join(search_typeall['searchstring'])
    search_typeall['AccountName']='\n'.join(search_typeall['AccountName'])
    search_typeall['HostName']='\n'.join(search_typeall['HostName'])
    search_typeall['HostAccountAliasName']='\n'.join(search_typeall['HostAccountAliasName'])
    search_typeall=json.dumps(search_typeall)
    search_typeall=search_typeall.replace("\\","\\\\")
    search_typeall=search_typeall.replace(".","\\\\\\\\.")
    search_typeall=search_typeall.replace("?","\\\\\\\\?")
    search_typeall=search_typeall.replace("+","\\\\\\\\+")
    search_typeall=search_typeall.replace("(","\\\\\\\\(")
    search_typeall=search_typeall.replace("*","\\\\\\\\*")
    search_typeall=search_typeall.replace("[","\\\\\\\\[")
    try:
        with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
            sql="select public.\"PGetHostAccountAliasName\"(E'%s',%s,%s,E'%s');"%(system_user,num,paging,search_typeall)
            debug(str(sql))
            curs.execute(sql)
            results = curs.fetchall()[0][0]
            return "{\"Result\":true,\"info\":%s}" % results
    except pyodbc.Error,e:
        return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
    return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)

