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
import shutil

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
from logbase import task_client
from logbase import defines
from index import PGetPermissions

from flask import Flask,Blueprint,request,session,render_template,send_from_directory# 
from jinja2 import Environment,FileSystemLoader
from generating_log import system_log
from htmlencode import check_role
from htmlencode import parse_sess


module = "系统管理>配置管理"
Backup_File_Path='/usr/storage/.system/config/backup/'
UPLOAD_FOLDER = '/usr/storage/.system/update'

config_manage = Blueprint('config_manage',__name__)
env = Environment(loader = FileSystemLoader('templates'))

def debug(c):
	return 0
        path = "/var/tmp/debugbhconfig.txt"
        fp = open(path,"a+")
        if fp :
			fp.write(c)
			fp.write('\n')
			fp.close()
#HTMLEncode 
def HTMLEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('&',"&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace('\'',"&apos;")
	return newStr
	
#error encode
def ErrorEncode(str):
	newStr = ""
	if str == "":
		return ""
	newStr = str.replace('\\',"\\\\").replace('"',"'").replace('\n',"\\n")
	return newStr

@config_manage.route('/config_show',methods=['GET', 'POST'])
def config_show():
		tasktype = request.form.get("tasktype")
		# page = request.form.get("c")
		# search	= request.form.get("d")
		# id = 0
		# if page < 0 or page == None:
		# 	page = "1"
		# if search < 0 or search == None:
		# 	search = ""
		sess =request.form.get('a0')
		if sess<0 or sess=='':
			sess=request.args.get('a0')
			
		if tasktype < 0 or tasktype == None:
			tasktype = "1"
		if tasktype == "1":
			t = "config_backup.html"
		elif tasktype == "2":
			t = "config_recover.html"
		elif tasktype == "3":
			t = "backup_strategy.html"
			
		client_ip = request.remote_addr
		(error,us,mac) = SessionCheck(sess,client_ip)
		error_msg=''
		if error < 0:
			error_msg = "系统繁忙(%d)" %(sys._getframe().f_lineno)
		elif error > 0:
			if error == 2:
				error_msg = "非法访问"
			else:
				error_msg = "系统超时" 
		_power=PGetPermissions(us)
		_power_json = json.loads(str(_power));
		_power_mode = 2;
		for one in _power_json:
			if one['SystemMenuId'] == 6:
				_power_mode = one['Mode']
				
		return render_template(t,tasktype = tasktype,_power_mode=_power_mode,se=sess)

#获取配置备份任务
@config_manage.route('/get_backup_list', methods=['GET', 'POST'])
def get_backup_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num = request.form.get('a1')
	paging = request.form.get('a2')
	tasktype = request.form.get('a3')

	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	if tasktype < 0 or tasktype == "":
		tasktype = "null"
	elif not tasktype.isdigit():
		return '',403
	paging = int(paging)
	if paging < 0:
		paging = 1
	num = int(num)
	if num < 0:
		num = 10
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))

	sql = "select public.\"PGetConfigBackupTask\"(%s,%d,%d);" %(tasktype,num,(paging-1)*num)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"配置备份任务列表获取异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1])) 
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

@config_manage.route('/get_backup_list1', methods=['GET', 'POST'])
def get_backup_list1():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	tasktype = request.form.get('a3')

	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	if tasktype < 0 or tasktype == "":
		tasktype = "null"
	elif not  tasktype.isdigit():
		return '',403
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))

	sql = "select public.\"PGetConfigBackupTask\"(%s,null,null);" %(tasktype)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"配置备份任务列表获取异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1])) 
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results	

# 还原备份文件
@config_manage.route('/recover_config', methods=['GET', 'POST'])
def recover_config():
	# #debug('recover_config')
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	filedate = request.form.get('a1')
	fname = 'bhost_'+filedate
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	# 还原数据库
	jsondata={
        "LogRecoveryTaskId": 0,    
        "FileName": fname+".config",
        "Status": 3,
		"Ignore":None        
	}
	data = str(json.dumps(jsondata))
	sql = "select public.\"PSaveConfigRecoveryTask\"(E'%s');" %((data).decode("utf-8"))
	# #debug(sql)
	##debug(sql)
	oper ="配置恢复：（文件名：%s）" %(fname+".config")
	backup_file_path='/usr/storage/.system/config/backup/'+fname+".config"
	# #debug(backup_file_path)
	version = ''
	version_back=''
	if os.path.exists(UPLOAD_FOLDER):
		list_file = os.listdir(UPLOAD_FOLDER)
		file_arr = []
		if not list_file:
			version = ""
		else:
			for file in list_file:
				if os.path.isdir(UPLOAD_FOLDER + "/" + file) and len(file)>8:
					if file[0:3] == "bh-" :
						file_arr.append(file)
			# #debug(str(file_arr))
			if not file_arr :
				version = ""
			else :
				filedate = file_arr[0][-10:]
				
				if len(file_arr) > 1:
					t1 = os.path.getmtime(UPLOAD_FOLDER +'/' + file_arr[0])
					for files in file_arr:
						t2 = os.path.getmtime(UPLOAD_FOLDER +'/' + files)
						if t2>=t1:
							version = files
							t1 = t2
				else:
					version = file_arr[0]
	# #debug(version)
	with open(backup_file_path,'r') as fo:
		file_data=fo.read()
		file_data_arr=file_data.split('|version:')
		if len(file_data_arr)>1:
			version_back=file_data.split('|version:')[1]
	# #debug(version_back)
	# #debug(version)
	if version_back=='':
		pass
		# return "{\"Result\":false,\"ErrMsg\":\"当前版本过低\"}"
	elif version=='':
		return "{\"Result\":false,\"ErrMsg\":\"获取版本号异常(%d)\"}" %(sys._getframe().f_lineno)
	else:
		version_arr=version.split('-');
		for i in version_arr:
			if i[0]=='v':
				i_arr= i[1:].split('.')
				version=int(i_arr[0])*1000000+int(i_arr[1])*1000+int(i_arr[2])
		version_back_arr=version_back.split('-');
		for i in version_back_arr:
			if i[0]=='v':
				i_arr= i[1:].split('.')
				version_back=int(i_arr[0])*1000000+int(i_arr[1])*1000+int(i_arr[2])
		if version<version_back:
			return "{\"Result\":false,\"ErrMsg\":\"当前版本过低\"}"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		msg = "数据库连接异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		msg = "数据库连接异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		msg = "配置恢复保存异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"配置恢复保存异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]
	if(result == True):
		conn.commit()
		
		msg = "成功"
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		try:
			sql = "select c.\"SubmitTime\" from private.\"ConfigRecoveryTask\" c where c.\"ConfigRecoveryTaskId\" = %d" % (long(ret["ConfigRecoveryTaskId"]))
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
		subtime = curs.fetchall()[0][0]
		curs.close()
		conn.close()
		filedate = str(subtime)
		recover_file_path='/usr/storage/.system/config/recover/'+fname+".config"+filedate.replace(' ','').replace(':','').replace('-','').replace('T','').replace('/','')
		shutil.copyfile(backup_file_path,recover_file_path)
	else:
		curs.close()
		conn.close()
		msg = ret['ErrMsg']
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return results
	'''
	task_content = '[global]\nclass = taskbackup\ntype = recover_db\nfilename=%s\nConfigRecoveryTaskId=%s\n' % (str(fname),ret['ConfigRecoveryTaskId'])
	##debug('1')
	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
		##debug('recover error...')
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	else:
	'''
	return "{\"Result\":true,\"info\":\"\"}"

#保存备注信息
@config_manage.route('/save_remarks_text',methods=['GET','POST'])
def save_remarks_text():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
		
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	remarks_text = request.form.get('a1')
	taskid = request.form.get('a2')
	oper ="配置备份"
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = 'update private."ConfigBackupTask" set "RemarksText"=\'%s\' where "ConfigBackupTaskId"=%s;' %((remarks_text).decode("utf-8"),taskid)
			curs.execute(sql)
			conn.commit()
			sql = "select c.\"SubmitTime\" from private.\"ConfigBackupTask\" c where c.\"ConfigBackupTaskId\" = %d" % (long(taskid))
			curs.execute(sql)
			subtime = str(curs.fetchall()[0][0])
			msg = "成功"
			if remarks_text=='':
				oper ="备份任务（备份信息：无）"
			else:
				oper ="备份任务：%s（备份信息：%s）"%(subtime,remarks_text)
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	return "{\"Result\":true}"
	

#保存配置备份任务
@config_manage.route('/save_backup', methods=['GET', 'POST'])
def save_backup():
	##debug('\t\t\t\tsave_backup')
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	jsondata = request.form.get('jsondata')	
	data = str(jsondata)
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	sql = "select public.\"PSaveConfigBackupTask\"(E'%s');" %((data).decode("utf-8"))
	##debug(sql)
	oper ="配置备份"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		msg = '数据库连接异常(%d):%s' %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		msg = '数据库连接异常(%d):%s' %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		msg = '系统用户创建异常(%d):%s' %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"系统用户创建异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	results = curs.fetchall()[0][0].encode('utf-8')
	##debug('results:'+results)
	ret = json.loads(results)
	##debug("ret:"+str(ret))
	result = ret["Result"]
	
	if(result == True):
		##debug('if...')
		backupId = ret["ConfigBackupTaskId"]
		##debug('id:'+str(backupId))
		conn.commit()
		# curs.close()
		# conn.close()
		msg = "成功"
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		# 获得新增的backupID
		##debug('select start...')
		##debug('backupid:'+str(backupId))
		'''
		try:
			sql = "select c.\"SubmitTime\" from private.\"ConfigBackupTask\" c where c.\"ConfigBackupTaskId\" = %d" % (long(backupId))
			curs.execute(sql)
			##debug(sql)
		except pyodbc.Error,e:
			##debug('select error:'+e.args[1])
			curs.close()
			conn.close()
		subtime = curs.fetchall()[0][0]
		##debug('subtime:'+str(subtime))
		filedate = str(subtime)
		'''
		curs.close()
		conn.close()
		##debug('filedate:'+filedate)
		# 备份文件
		##debug('backup start..')
		'''
		task_content = '[global]\nclass = taskbackup\ntype = backup_db\nfiledate = %s\nclient_ip=%s\nbackupId=%s\n' % (str(filedate),client_ip,backupId)
		##debug(task_content)
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		'''
		##debug('over...')
		return results
	else:
		curs.close()
		conn.close()
		msg = ret['ErrMsg']
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return results

#删除配置备份任务
@config_manage.route('/del_backup', methods=['GET', 'POST'])
def del_backup():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit() 
		
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
		
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	oper = '删除配置备份：（'
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	for id in ids:
		id = int(id)
		
		sql = "select \"SubmitTime\" from private.\"ConfigBackupTask\" where \"ConfigBackupTaskId\" = %d " %(id)
		curs.execute(sql)
		SubmitTime = curs.fetchall()[0][0]
		filename='bhost_'+str(SubmitTime).replace(" ", "").replace("-", "").replace(":", "").replace("T", "")+'.config'
		##debug(filename)
		oper +="备份时间："+ str(SubmitTime)+"，"
		
		sql = "select public.\"PDeleteConfigBackupTask\"(%d);" %(id)
		# ##debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			oper =oper[:-3] +"）"
			msg = "配置备份删除异常(%d):%s"%(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"配置备份删除异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		result = curs.fetchall()[0][0].encode('utf-8')
		'''
		try:
			curs.execute('DELETE FROM private.config_backfile WHERE filename = \'%s\';'%(filename))
			##debug('DELETE FROM private.config_backfile WHERE filename = \'%s\';'%(filename))
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			oper =oper[:-3] +"）"
			msg = "配置备份删除异常(%d):%s"%(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"配置备份删除异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		'''
		if "false" in result:
			curs.close()
			conn.close()
			oper =oper[:-3]+"）"
			msg = json.loads(result)['ErrMsg']
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result
		task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=%s\n' % (Backup_File_Path+str(filename))
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	conn.commit()
	curs.close()
	conn.close()
	oper =oper[:-3]+"）"
	msg = "成功"
	if not system_log(system_user,oper,msg,module):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	
	return result

#取配置恢复任务列表
@config_manage.route('/get_recover_list', methods=['GET', 'POST'])
def get_recover_list():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	num = request.form.get('a1')
	paging = request.form.get('a2')

	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	paging = int(paging)
	if paging < 0:
		paging = 1
	num = int(num)
	if num < 0:
		num = 10
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))

	sql = "select public.\"PGetConfigRecoveryTask\"(%d,%d);" %(num,(paging-1)*num)
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"配置备份任务列表获取异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1])) 
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

@config_manage.route('/get_recover_list1', methods=['GET', 'POST'])
def get_recover_list1():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')

	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()

		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))

	sql = "select public.\"PGetConfigRecoveryTask\"(null,null);"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"配置备份任务列表获取异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1])) 
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

# 是否指定备份文件存在
@config_manage.route('/down_backupfile_exist', methods=['GET', 'POST'])
def down_backupfile_exist():
	#debug('down_backupfile_exist')
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	##debug('session'+str(session))
	filedate = request.form.get('filename')
	fname = 'bhost_'+str(filedate)
	##debug('fname:'+str(fname))
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"info\":\"系统超时\"}"
		sys.exit()
	downfile_path = '/usr/storage/.system/config/backup/' + fname + '.config' 
	#debug(downfile_path)
	if os.path.exists(downfile_path):
		return "{\"Result\":true,\"info\":1}"
	else:
		return "{\"Result\":true,\"info\":0}"

#下载指定备份文件下发任务down_backupfile_workflow
@config_manage.route('/down_backupfile_workflow', methods=['GET', 'POST'])
def down_backupfile_workflow():
	##debug('in down_backupfile....')
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	##debug('reload...')
	sys.setdefaultencoding('utf-8')
	##debug('sys...')
	session = request.form.get('a0')
	##debug('session'+str(session))
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"info\":\"系统超时\"}"
		sys.exit()
	filedate = request.form.get('filename')
	fname = 'bhost_'+str(filedate)
	return "{\"Result\":true,\"info\":\"\"}"

# 下载指定备份文件
@config_manage.route('/down_backupfile', methods=['GET', 'POST'])
def down_backupfile():
	##debug('in down_backupfile....')
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	##debug('reload...')
	sys.setdefaultencoding('utf-8')
	##debug('sys...')
	session = request.form.get('a0')
	use_BH = request.form.get('a99')
	##debug('session'+str(session))
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"info\":\"系统超时\"}"
		sys.exit()
	filedate = request.form.get('filename')
	fname = 'bhost_'+str(filedate)
	downfile_path = '/usr/storage/.system/config/backup/' + fname + '.config' 
	msg='成功'
	oper='下载配置文件：%s.config'%fname	
	filename = fname + '.config'
	while (True):
		if os.path.exists(downfile_path):
			if not system_log(system_user,oper,msg,module):
                        	return "{\"Result\":false,\"info\":\"生成日志失败\"}"
			if use_BH=='0':
				return send_from_directory('/usr/storage/.system/config/backup/',filename,as_attachment=True)
			else:
				return '{"Result":true,"Path":"/usr/storage/.system/config/backup/","Filename":"%s"}'%filename
		else:
			time.sleep(1)
	return 0

# 下载指定备份文件删除
@config_manage.route('/down_backupfile_delete', methods=['GET', 'POST'])
def down_backupfile_delete():
	##debug('in down_backupfile....')
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	##debug('reload...')
	sys.setdefaultencoding('utf-8')
	##debug('sys...')
	session = request.form.get('a0')
	##debug('session'+str(session))
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)\"}" %(sys._getframe().f_lineno)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问\"}"
		else:
			return "{\"Result\":false,\"info\":\"系统超时\"}"
		sys.exit()
	'''
	filedate = request.form.get('filename')
	fname = 'bhost_'+str(filedate)
	##debug('fname:'+str(fname))
	downfile_path = '/usr/storage/.system/config/backup/' + fname + '.config' 
	##debug(downfile_path)
	if os.path.exists(downfile_path): # 如果文件存在
		##debug('os.path.exists(downfile_path)')
		#删除文件，可使用以下两种方法。
		os.remove(downfile_path) # 则删除
		#os.unlink(my_file)
	else:
		##debug('no such file:%s'%downfile_path)
		pass
	'''
	return "{\"Result\":true,\"info\":\"\"}"

#保存配置恢复任务
@config_manage.route('/save_recover', methods=['GET', 'POST'])
def save_recover():
	##debug('in save_recover....')
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 40000
	reload(sys)
	##debug('reload...')
	sys.setdefaultencoding('utf-8')
	##debug('sys...')
	session = request.form.get('a0')
	use_BH = request.form.get('a99')
	##debug('geta0....')
	if use_BH=='0':
		filedata = request.files['path1']
		fname=filedata.filename
	else:
		path = request.form.get('path')
		fname = request.form.get('fname')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	jsondata = request.form.get('jsondata')
	data = str(jsondata)
	
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	
	sql = "select public.\"PSaveConfigRecoveryTask\"('%s');" %((data).decode("utf-8"))
	##debug(sql)
	FileName = json.loads(jsondata)['FileName']
	oper ="配置恢复：（文件名：%s）"%FileName
	upload_path = '/usr/storage/.system/config/recover/' + fname
	try:
		if use_BH=='0':
			filedata.save(upload_path)
		else:
			shutil.move(path,upload_path)
	except Exception,e:
		##debug('save error:'+str(e))
		pass
	version = ''
	version_back=''
	if os.path.exists(UPLOAD_FOLDER):
		list_file = os.listdir(UPLOAD_FOLDER)
		file_arr = []
		if not list_file:
			version = ""
		else:
			for file in list_file:
				if os.path.isdir(UPLOAD_FOLDER + "/" + file) and len(file)>8:
					if file[0:3] == "bh-" :
						file_arr.append(file)
			#debug(str(file_arr))
			if not file_arr :
				version = ""
			else :
				filedate = file_arr[0][-10:]
				
				if len(file_arr) > 1:
					t1 = os.path.getmtime(UPLOAD_FOLDER +'/' + file_arr[0])
					for files in file_arr:
						t2 = os.path.getmtime(UPLOAD_FOLDER +'/' + files)
						if t2>=t1:
							version = files
							t1 = t2
				else:
					version = file_arr[0]
	#debug(version)
	with open(upload_path,'r') as fo:
		file_data=fo.read()
		file_data_arr=file_data.split('|version:')
		if len(file_data_arr)>1:
			version_back=file_data.split('|version:')[1]
	#debug(version_back)
	#debug(version)
	if version_back=='':
		pass
		# return "{\"Result\":false,\"ErrMsg\":\"当前版本过低\"}"
	elif version=='':
		task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=%s\n' % (upload_path)
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		return "{\"Result\":false,\"ErrMsg\":\"获取版本号异常(%d)\"}" %(sys._getframe().f_lineno)
	else:
		version_arr=version.split('-');
		for i in version_arr:
			if i[0]=='v':
				i_arr= i[1:].split('.')
				version=int(i_arr[0])*1000000+int(i_arr[1])*1000+int(i_arr[2])
		version_back_arr=version_back.split('-');
		for i in version_back_arr:
			if i[0]=='v':
				i_arr= i[1:].split('.')
				version_back=int(i_arr[0])*1000000+int(i_arr[1])*1000+int(i_arr[2])
		if version<version_back:
			task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=%s\n' % (upload_path)
			if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
				return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
			return "{\"Result\":false,\"ErrMsg\":\"当前版本过低\"}"
	
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		msg = "数据库连接异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		msg = "数据库连接异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		msg = "配置恢复保存异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return "{\"Result\":false,\"ErrMsg\":\"配置恢复保存异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]
	if(result == True):
		conn.commit()
		try:
			sql="select c.\"SubmitTime\" from private.\"ConfigRecoveryTask\" c where c.\"ConfigRecoveryTaskId\" = %d" % (long(ret["ConfigRecoveryTaskId"]))
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			msg = "配置恢复保存异常(%d):%s" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"配置恢复保存异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		subtime = curs.fetchall()[0][0]
		curs.close()
		conn.close()
		# 保存上传的文件
		upload_pathll = '/usr/storage/.system/config/recover/' + fname+str(subtime).replace('/','').replace('-','').replace(':','').replace(' ','').replace('T','')
		try:
			shutil.move(upload_path,upload_pathll)
		except Exception,e:
			##debug('save error:'+str(e))
			pass
		task_content = '[global]\nclass = taskglobal\ntype = del_file\nfname=%s\n' % (upload_path)
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		##debug('save over..')
		msg = "成功"
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		'''
		# 执行还原数据库命令
		task_content = '[global]\nclass = taskbackup\ntype = uploadrecover\nuploadpath = %s\nConfigRecoveryTaskId=%s\n' % (str(upload_path),ret['ConfigRecoveryTaskId'])
		##debug('1')
		if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
			return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
		'''
		##debug('over...')
		return results
	else:
		curs.close()
		conn.close()
		msg = ret['ErrMsg']
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return results

#删除配置恢复任务
@config_manage.route('/del_recover', methods=['GET', 'POST'])
def del_recover():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	id_str = request.form.get('a1')
	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit() 
	if check_role(system_user,'系统管理') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	if id_str < 0:
		id_str = ""
	ids = id_str.split(',')
	oper ="删除配置恢复：（"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	for id in ids:
		id = int(id)
		
		sql = "select \"SubmitTime\" from private.\"ConfigRecoveryTask\" where \"ConfigRecoveryTaskId\" = %d " %(id)
		curs.execute(sql)
		SubmitTime = curs.fetchall()[0][0]
		oper +="恢复时间："+ str(SubmitTime)+"，"
		
		
		sql = "select public.\"PDeleteConfigRecoveryTask\"(%d);" %(id)
		# ##debug(sql)
		try:
			curs.execute(sql)
		except pyodbc.Error,e:
			curs.close()
			conn.close()
			oper =oper[:-3]+"）"
			msg = "配置恢复删除异常(%d):%s"%(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return "{\"Result\":false,\"ErrMsg\":\"配置恢复删除异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
		result = curs.fetchall()[0][0].encode('utf-8')
		if "false" in result:
			curs.close()
			conn.close()
			oper =oper[:-3]+"）"
			msg = json.loads(result)['ErrMsg']
			if not system_log(system_user,oper,msg,module):
				return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
			return result
	conn.commit()
	curs.close()
	conn.close()
	oper =oper[:-3]+"）"
	msg = "成功"
	if not system_log(system_user,oper,msg,module):
		return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
	return result

#取配置自动备份策略
@config_manage.route('/get_backup_strategy', methods=['GET', 'POST'])
def get_backup_strategy():
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')

	if session < 0:
		session = ""
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))

	sql = "select public.\"PGetConfigBackupStrategy\"();"
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"配置自动备份策略信息获取异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1])) 
	results = curs.fetchall()[0][0].encode('utf-8')
	curs.close()
	conn.close()
	return "{\"Result\":true,\"info\":%s}" %results

#保存配置恢复任务
@config_manage.route('/save_backup_strategy', methods=['GET', 'POST'])
def save_backup_strategy():
	global ERRNUM_MODULE 
	ERRNUM_MODULE = 40000
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	client_ip = request.remote_addr
	(error,system_user,mac) = SessionCheck(session,client_ip)
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统异常(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)：%d\"}" %(sys._getframe().f_lineno,error)
		sys.exit()
	jsondata = request.form.get('jsondata')
	data = str(jsondata)
	md5_str = request.form.get('m1')		
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
			
	sql = "select public.\"PSaveConfigBackupStrategy\"(E'%s');" %((data).decode("utf-8"))
	##debug(sql)
	oper ="保存自动备份策略"
	try:
		conn = pyodbc.connect(StrSqlConn('BH_CONFIG'))
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	try:
		curs = conn.cursor()
	except pyodbc.Error,e:
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"数据库连接异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	
	try:
		curs.execute(sql)
	except pyodbc.Error,e:
		curs.close()
		conn.close()
		return "{\"Result\":false,\"ErrMsg\":\"自动备份策略保存异常(%d):%s\"}" %(sys._getframe().f_lineno,ErrorEncode(e.args[1]))
	results = curs.fetchall()[0][0].encode('utf-8')
	ret = json.loads(results)
	result = ret["Result"]
	if(result == True):
		conn.commit()
		curs.close()
		conn.close()
		msg = "成功"
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return results
	else:
		curs.close()
		conn.close()
		msg = ret['ErrMsg']
		if not system_log(system_user,oper,msg,module):
			return "{\"Result\":false,\"ErrMsg\":\"生成日志失败\"}"
		return results
		
# 返回要下载的指定备份文件的大小
@config_manage.route('/down_backupfile_size', methods=['GET', 'POST'])
def down_backupfile_size():
	##debug('in down_backupfile_size....')
	global ERRNUM_MODULE
	ERRNUM_MODULE = 40000
	reload(sys)
	##debug('reload...')
	sys.setdefaultencoding('utf-8')
	##debug('sys...')
	session = request.form.get('a0')
	##debug('session'+str(session))
	filedate = request.form.get('filename')
	fname = 'bhost_'+str(filedate)
	##debug('fname:'+str(fname))
	downfile_path = '/var/www/manage/bhost/downbackupfile/' + fname + '.config' 
	'''task_content = '[global]\nclass = down_backupfile\ntype = downbackupfile\nfilename=%s\n' % (str(fname))
	##debug('1')
	if False == task_client.task_send(defines.MASTER_SERVER_ID,task_content):
		##debug('createfile error...')
		return "{\"Result\":false,\"ErrMsg\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	##debug('over...')'''
	filename = fname + '.config'
	while (True):
		if os.path.exists(downfile_path):
			##debug('exists...')
			#等待文件生成完毕
			while (True):
				size = os.path.getsize(downfile_path)
				time.sleep(0.1)
				if size == os.path.getsize(downfile_path):
					return 0
	return 0
