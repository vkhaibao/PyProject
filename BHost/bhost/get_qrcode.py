#!/usr/bin/env python
# encoding: utf-8

import os
import cgi
import cgitb
import re
import pyodbc
import MySQLdb
import json
import time
import base64

from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck
from comm import LogSet
from logbase import common
import sys
sys.path.append("/usr/bin")
import random
import hmac, base64, struct, hashlib, time
import qrcode
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader 
get_qrcode = Blueprint('get_qrcode',__name__)

ERRNUM_MODULE_get_qrcode = 1000
size=1

def debug(c):
	return 0
	path = "/var/tmp/debugzdppp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)
		fp.write("\n")
		fp.close()

#ErrorEncode 
def ErrorEncode(str):
	newStr = "";
	if str == "":
		return "";
	newStr = str.replace('\\',"\\\\").replace('"','\'').replace('\n','\\n')
	return newStr;

#get secret
def random_secretKey():
	chars = r"234567ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	return ''.join(
	random.choice(chars)
	for i in xrange(16)
	)

#set URL
def set_URL(secret,url,account):
	url = url.replace('account',account)
	return url+secret


#get qrcode,size value 1-40:little-lagre
def create_qrcode(data,size):
	qr = qrcode.QRCode(
		version=size,
		error_correction=qrcode.constants.ERROR_CORRECT_L,
		box_size=5,
		border=4,
	)
	qr.add_data(data)
	img = qr.make_image()
	img.save("/var/www/manage/html/images/totp_code.png")
	#img.show()
#get passwd
def get_hotp_token(secret,intervals_no):
	key = base64.b32decode(secret, True)
	msg = struct.pack(">Q", intervals_no)
	h = hmac.new(key, msg, hashlib.sha1).digest()
	o = ord(h[19])&15
	h = (struct.unpack(">I",h[o:o+4])[0] & 0x7fffffff)%1000000
	return h

def get_totp_token(secret):
	intervals_no=int(time.time())//30
	valid_codes = []
	debug("intervals:%d" % intervals_no)
	for offset in [-1, 0, 1]:
		debug("%d" % get_hotp_token(secret, intervals_no+offset))
		valid_codes.append(get_hotp_token(secret, intervals_no+offset))
	count=0
	debug("begin")
	while count<3:
		l=str(valid_codes[count])
		if len(l)<6:
			s = 6-len(l)
			if s == 6:
				valid_codes[count] = "000000"
			if s == 5:
				valid_codes[count] = "00000"+l
			if s == 4:
				valid_codes[count] = "0000"+l
			if s == 3:
				valid_codes[count] = "000"+l
			if s == 2:
				valid_codes[count] = "00"+l
			if s == 1:
				valid_codes[count] = "0"+l
		count=count+1
	debug("12313zzz")
	debug(str(valid_codes))
	return valid_codes
#test
@get_qrcode.route('/get_qrcode_img',methods=['GET', 'POST'])
def get_qrcode_img():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	user_account = request.form.get('z1')
	url = "otpauth://totp/account?secret="	
	secret =random_secretKey()
	data = set_URL(secret,url,user_account)
	#valid_codes =get_totp_token(secret)
	create_qrcode(data,size)
	return '{\"Result\":true,\"secret\":\"'+secret+'\","img":"/manage/images/totp_code.png"}'
	#return "/manage/images/testzdp.png"
	
@get_qrcode.route('/test_qrcode',methods=['GET', 'POST'])
def test_qrcode():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	totp_v = request.form.get('z1')
	secret = request.form.get('z2')
	valid_codes = get_totp_token(secret)
	if int(totp_v) in valid_codes:
		return "true"
	else:
		return "false"

@get_qrcode.route('/clear_secretkey',methods=['GET', 'POST'])
def clear_secretkey():
	reload(sys)
	sys.setdefaultencoding('utf-8')
	session = request.form.get('a0')
	userid = request.form.get('z1')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn,conn.cursor() as curs:
			sql = "update public.\"User\" set \"SecretKey\"=\'\' where \"UserId\"=%s" % userid
			debug("sql:%s" % sql)
			curs.execute(sql)
			return "{\"Result\":true}"
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)