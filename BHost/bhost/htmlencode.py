#!/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import MySQLdb
from comm import StrSqlConn
import pyodbc
from comm import StrMD5
def debug(c):
	return 0
	path = "/var/tmp/debugmd5.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()

#HTMLEncode 
def HtmlEncode(oldStr):
	newStr = "";
	if oldStr == "":
		return "";
	newStr = oldStr.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr;

#ErrorEncode 
def ErrorEncode(oldStr):
	newStr = "";
	if oldStr == "":
		return "";
	newStr = oldStr.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

#账号
def checkaccount(account):
        p = re.compile(u'^[\w\.\-\u4E00-\u9FA5]+$')
        if p.match(account.decode('utf-8')):
                return True
        else:
                return False

def ToHtmlEncode(oldStr):
	newStr = ""
	if oldStr == "":
		return "";
	newStr = oldStr.replace("\\", "\\\\").replace("'","\\'").replace('"','\\"').replace("/", "\\/").replace("\n", "\\n")
	return newStr;
	
def parse_sess(md5_str,session,src_md5): ### md5_str ajax传过来的md5值 src_md5 是python里面json数据的md5值
	tmp =  src_md5[:16].lower()+str(session) +src_md5[16:].lower()
	
	if(md5_str != StrMD5(tmp).lower()):
		return False
	return True

def check_role(userCode,module):
	module_list = module.split(',');
	if module_list[0].isdigit() == True:
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				debug('2222')
				sql = "select \"SubMenuId\" from public.\"SystemSubMenu\"  where \"SubMenuId\" in(select  \"SubMenuId\" from public.\"RolePermissions\" where \"RoleId\" in (select \"RoleId\" from public.\"UserRole\" where \"UserId\" in (select \"UserId\" from public.\"User\" where \"UserCode\"=E'%s')) and \"Mode\" =2);" %(MySQLdb.escape_string(userCode).decode("utf-8"))
				debug(sql)
				curs.execute(sql)
				data = curs.fetchall()
				debug(str(data))
				for d in data:
					if str(d[0]) in module_list:
						return True
				return False	
		except pyodbc.Error,e:
			debug(str(e))
			return False
	else:
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
				curs = conn.cursor()
				sql = "select \"SubMenuName\" from public.\"SystemSubMenu\"  where \"SubMenuId\" in(select  \"SubMenuId\" from public.\"RolePermissions\" where \"RoleId\" in (select \"RoleId\" from public.\"UserRole\" where \"UserId\" in (select \"UserId\" from public.\"User\" where \"UserCode\"=E'%s')) and \"Mode\" =2);" %(MySQLdb.escape_string(userCode).decode("utf-8"))
				debug(sql)
				curs.execute(sql)
				data = curs.fetchall()
				debug(str(data))
				for d in data:
					if d[0].encode('utf-8') in module_list:
						return True
				return False	
		except pyodbc.Error,e:
			debug(str(e))
			return False
	
#协议
def checkproto(account):
	p = re.compile(u'^[\w_\-\u4E00-\u9FA5]+$')
	if p.match(account.decode('utf-8')):
		return True
	else:
		return False
#主机账号
def checkhostaccount(account):
	p = re.compile(u'^[\w_\-@\\\.\u4E00-\u9FA5]+$')
	if p.match(account.decode('utf-8')):
		return True
	else:
		return False
	
#{1,2,43,5}ttype
def checkarr_1(a_str):
	p = re.compile(u'^[\d,{}]+$')
	if p.match(a_str.decode('utf-8')):
                return True
        else:
                return False
#服务
def checkserver(account):
	p = re.compile(u'^[a-zA-Z\d_\-]+$')
	if p.match(account.decode('utf-8')):
		return True
	else:
		return False				
def checkserver1(account):
	p = re.compile(u'^[a-zA-Z\d_\-\(\)\u4E00-\u9FA5\\\://.|]+$')
	if p.match(account.decode('utf-8')):
		return True
	else:
		return False				
			
