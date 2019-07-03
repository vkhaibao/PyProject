#!/usr/bin/python
#-coding: UTF-8-

import platform
import sys
import os
import time
import thread
import logging
import socket
import cgi
import cgitb
import re
import pyodbc
import pyodbc
import MySQLdb
import json
import taskcommon
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import task_client

HostScanTaskId=''
conn=None
curs=None
# dict_={}
# dict_1={}
#ErrorEncode 
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr

def system_os():
	 os = platform.system() 
	 if os == "Windows": 
	 	return "n"
	 else: 
	 	return "c"

def system_port(ip, port,pass_num,num_all):
	
	# global dict_
	# global dict_1
	try:
		sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sk.settimeout(2)
		sk.connect((ip, port))
		sk.close()
		print '\tport %s pass'%port
		return "{'HostIP':'%s','Port':%s}"%(ip,port)
	except socket.error:
		return False
	

def system_connect(ipstr, ports,pass_num,num_all):
	# global dict_
	global HostScanTaskId
	global conn
	global curs
	dict_={}
	print ipstr
	cmd = ["ping", "-{op}".format(op=system_os()), "1", ipstr] 
	p = os.popen(" ".join(cmd)); 
	result = p.readlines()
	print str(result)
	p.close()
	flag = False
	for line in list(result):
		if not line: 
			continue
		if str(line).upper().find("TTL") >=0: 
		 	flag = True
		 	break
	dict_['HostScanTaskId']=int(HostScanTaskId)
	dict_['Status']=1
	dict_['Progress']=(pass_num*100)/num_all
	if flag:
	 	print "%s ok" %ipstr
		dict_['Result']=[]
		for port in ports:
			if not port:
				continue
			result_port=system_port(ipstr, int(port),pass_num,num_all)
			if result_port!=False:
				dict_['Result'].append(eval(result_port))
	sql='select public."PSaveHostScanTask"(\'%s\');'%(str(dict_).replace('\'','"'))
	# try:
	# 	print 'sql1start'
	# 	sql='select public."PSaveHostScanTask"(E\'%s\');'%(str(dict_).replace('\'','"'))
	# 	print sql
	# 	curs.execute(sql)
	# 	conn.commit()
	# 	print 'sql1end'
	# except pyodbc.Error,e:
	# 	print "sql error1"
	# 	print "%s :%s"%(str(e),pass_num)
	# 	curs.close()
	# 	conn.close()
	# 	exit(0)

def ip2num(ip):#ip to int num
    lp = [int(x) for x in ip.split('.')]
    return lp[0] << 24 | lp[1] << 16 | lp[2] << 8 | lp[3]

def num2ip(num):# int num to ip
    ip = ['', '', '', '']
    ip[3] = (num & 0xff)
    ip[2] = (num & 0xff00) >> 8
    ip[1] = (num & 0xff0000) >> 16
    ip[0] = (num & 0xff000000) >> 24
    return '%s.%s.%s.%s' % (ip[0], ip[1], ip[2], ip[3])

def system_scan(prefix,ports):
	global conn
	global curs
	# global dict_
	global HostScanTaskId
	
	dict_={}
	dict_['HostScanTaskId']=int(HostScanTaskId)
	print 'start'
	prefix=prefix.split(',')
	if ports=='':
		ports = [21, 22, 23, 80,90,177,1433,1521,2389,3306,3389,4899,5000,5631,5900,50000]
	else:
		ports=ports.split(',')
		print str(ports)
		ports=list(set(ports))
		print str(ports)
	num_all=0
	for i in prefix:
		if not i:
			continue
		prefix_array=i.split('-')
		num1=ip2num(prefix_array[0])
		num2=ip2num(prefix_array[1])
		print num1
		print num2
		num_all+=(num2-num1+1)
	print num_all
	pass_num=1
	for j in prefix:
		if not j:
			continue
		prefix_array=j.split('-')
		num1=ip2num(prefix_array[0])
		num2=ip2num(prefix_array[1])
		while num1<=num2:
			ip=num2ip(num1)
			print '%s:%s'%(pass_num,num_all)
			thread.start_new_thread(system_connect, (ip, ports,pass_num,num_all))#ip ports
			time.sleep(0.3)
			num1+=1
			pass_num+=1	
			print 'while end'
	print '-----------'
	dict_['Status']=2
	dict_['Progress']=100
	sql='select public."PSaveHostScanTask"(\'%s\');'%(str(dict_).replace('\'','"'))
	# try:
	# 	print 'sql3start'
	# 	sql='select public."PSaveHostScanTask"(E\'%s\');'%(str(dict_).replace('\'','"'))
	# 	print sql
	# 	curs.execute(sql)
	# 	conn.commit()
	# 	print 'sql3end'
	# except pyodbc.Error,e:
	# 	print "sql error3"
	# 	print "%s :%s"%(str(e),pass_num)
	# 	curs.close()
	# 	conn.close()
	# 	exit(0)
	print 'end'

try:
	method = sys.argv[1]
	prefix = sys.argv[2]
	ports = sys.argv[3]
	HostScanTaskId = sys.argv[4]
	print 'system_scan'
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		print str(e)
		exit(0)
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		print str(e)
		exit(0)
	system_scan(prefix,ports)
# 打开文件失败时
except IOError:
    print "Bind port failed!"

# 调用系统命令失败
except OSError:
    print "Command failed!"

except KeyError:
    print "No such item!"

# 使用Ctrl+c退出时
except KeyboardInterrupt:
    print "User quitted!"

except pyodbc.Error,e:
	print "sql error"
	print str(e)

finally:
	curs.close()
	conn.close()
	exit(0)
	

