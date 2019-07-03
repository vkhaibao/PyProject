#!/usr/bin/python
#-coding: UTF-8-

import os
import sys
import pyodbc
import time
import json
import MySQLdb
import urllib
import hashlib
from comm import StrSqlConn

from comm import StrMD5
from comm import SessionCheck
import traceback
import base64
MAX_SIZE =0x800000
from flask import request,Blueprint,render_template,send_from_directory # 

tran = Blueprint('tran',__name__)

reload(sys)
sys.setdefaultencoding('utf-8')
list_path = ['/usr/storage/.system/upload','/usr/storage/.system/replay','/usr/storage/.system/software','/usr/storage/.system/update','/usr/storage/.system/config/backup','/usr/storage/.system/dwload','/usr/storage/.system/passwd','/usr/storage/.system/backup','/usr/storage/.system/transf']
def PrintError(c):
	return 0;
	path = "/var/tmp/error_tran.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write('\n')
		fp.close()
def parseHeader(headers):
	
	if headers.find('Filename')< 0:
		return -1,'','','','',0,0;
	Filename = headers.split('Filename')[1].split()[1];
	
	if headers.find('Session')< 0:
		return -1,'','','','',0,0;
	Session = headers.split('Session')[1].split()[1];
	
	if headers.find('Path')< 0:
		return -1,'','','','',0,0;
	Path = headers.split('Path')[1].split()[1];
	
	if headers.find('Method')< 0:
		Method = '';
	else:
		Method = headers.split('Method')[1].split()[1];
	
	if headers.find('Offset')< 0:
		Offset = '0';
	else:
		Offset = headers.split('Offset')[1].split()[1];
	
	if headers.find('Content-Length')< 0:
		Content_Length = 0;
	else:
		Content_Length = int(headers.split('Content-Length')[1].split()[1]);
	
	if headers.find('Sesstimet')< 0:
                sesstimet = '';
        else:
                sesstimet = headers.split('Sesstimet')[1].split()[1];	
	return 	0,Filename, Session, Path, Method, Offset, Content_Length,sesstimet;
def check_path(path):
	for one in list_path:
		if path.find(one) >=0:
			return True
	return False
###下载
@tran.route("/bhTranDownload", methods=['GET', 'POST'])
def bhTranDownload():
	headers  = str(request.headers) ;
	##解析头文件
	#
	try:
		ret,Filename,Session,Path,Method,Offset,Content_Length,sesstimet = parseHeader(headers);
		if ret < 0:
			return' -1';
	except Exception,e:
		return '-1';
	PrintError(str(Filename) +','+str(Session)+','+str(Path)+','+str(Method)+','+str(Offset) +','+str(Content_Length)+','+sesstimet);	
	Path = base64.b64decode(Path);
	Filename = base64.b64decode(Filename);
	
	if check_path(Path) == False and Filename !='cf_tnsora':
		return '-1',403;
	
	if Path.find("/software") >=0 or Method =='GetSize' or Filename =='cf_tnsora': ###系统自动升级 没有session
		pass
	else:
		#j_data =  json.loads(data)
		client_ip = request.remote_addr;
		(error,userCode,mac) = SessionCheck(Session,client_ip);
		
		if error < 0:
			PrintError('bhTranDownload：系统繁忙');
			return '-1',403;
		elif error > 0:
			if error == 2:
				PrintError('bhTranDownload：非法访问');
				return '-1',403;
			else:
				PrintError('bhTranDownload：系统超时');
				return '-1',403;
	
	
	if Filename == 'launch.exe.tmp':
		Filename = "launch.exe"	
	FilePath = Path + '/' + Filename;
	##判断文件是否存在
	if os.path.exists(FilePath) == False:
		return '-1';
	
	if Method == "": ## 下载
		##每次读取文件的 8k  8 * 1024
		try:
			with open(FilePath, 'rb') as fp:
				fp.seek(int(Offset));
				data = fp.read(MAX_SIZE);
			return data;
		except Exception,e:
			return '-1';
		
	else: ##获取文件大小
		try:
			if Method =='GetSize':
				file_size = os.path.getsize(FilePath);
				return str(file_size);
			else:
				return '0';
		except Exception,e:
			return '-1';

###上传
@tran.route("/bhTranUpload", methods=['GET', 'POST'])
def bhTranUpload():
	headers  = str(request.headers);
	PrintError(headers)
	##解析头文件
	#
	try:
		ret,Filename,Session,Path,Method,Offset,Content_Length,sesstimet = parseHeader(headers);
		if ret < 0:
			return '-1';
	except Exception,e:
		return '-1';
	PrintError(str(Filename) +','+str(Session)+','+str(Path)+','+str(Method)+','+str(Offset) +','+str(Content_Length)+','+sesstimet);	
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(Session,client_ip);
	
	if error < 0:
		PrintError('bhTranUpload：系统繁忙');
		return '-1',403
	elif error > 0:
		if error == 2:
			PrintError('bhTranUpload：非法访问');
			return '-1',403
		else:
			PrintError('bhTranUpload：系统超时');
			return '-1',403

	Path = base64.b64decode(Path);
	if check_path(Path) == False:
		return '-1',403;
	Filename = base64.b64decode(Filename)
	FileNameSwp = Filename +'.swp';
	FilePath = Path +'/'+Filename;
	FilePathSwp = Path +'/'+FileNameSwp;
	if Method =='SaveFile':
		try:
			with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:#新建任务
				sql = "insert into private.\"USBKeyResult\"(\"UserCode\",\"Type\",\"Status\",\"SessTime\",\"CertInfo\") values('','sysupdate',3,'%s','%s');" %(sesstimet,Filename.decode('utf-8'))
				PrintError(sql)
				curs.execute(sql)
		except pyodbc.Error,e:
			PrintError('bhTranUpload:%s'%str(e));
			return '-1'
		PrintError('bhTranUpload:SaveFile');
		return '0'
	else:
		pass
	
	
	#content_length = int(headers['content_length']);
	#Content-Length = 8192;
	##判断文件目录是否存在
	if os.path.exists(Path) == False:
		return '-1';
	if(int(Offset) == 0):
		with open(FilePathSwp, 'w') as fp:
			pass
		if os.path.exists(FilePath):
			os.system('rm -f ' + FilePath);
			print "sucess del file"
	#写文件
	try:
		if( int(Offset) == -1): ##文件传输完毕
			os.rename(FilePathSwp,FilePath);
			return '0';
			
		data = request.data;	
		#data = request.json; ####获取 文件信息 
		#	return -1;
		with open(FilePathSwp, 'rb+') as fp:
			fp.seek(int(Offset));
			fp.write(data);		
		return '0';
	except Exception,e:
		return '-1';
def GetFileMd5(filename):
	filename_list = filename.split(',')
	i = 0
	file_list = []
	while i < len(filename_list):
		path = '/usr/storage/.system/software/%s' % filename_list[i]
		if not os.path.exists(path):
			file_list.append('')
		else:
			myhash = hashlib.md5()
			f = file(path,'rb')
			while True:
				b = f.read(8096)
				if not b :
					break
				myhash.update(b)
			f.close()
			file_list.append(myhash.hexdigest())
		i = i + 1
	return ','.join(file_list)
	
### 获取 控件jar MD5值	
@tran.route("/GetMd5", methods=['GET', 'POST'])
def GetMd5():
	
	headers = str(request.headers);
	PrintError(str(headers));
	if str(headers).find('Filename') < 0:
		Filename = request.args.get('Filename');
	else:
		Filename = headers.split('Filename')[1].split()[1];
	
	return GetFileMd5(Filename)
	#path = '/usr/storage/.system/software/' + Filename
	#PrintError(str(path));
	#if os.path.exists(path) == True:
	#	return GetFileMd5(path);
	#else:
	#	return ''
	
	
'''
if not sys.stdin.isatty():
		PrintError('yes');
		PrintError(str(sys.stdin.read()));
		for line in sys.stdin:
				PrintError(str(line));
else:
		PrintError('no');
'''			
			
			
