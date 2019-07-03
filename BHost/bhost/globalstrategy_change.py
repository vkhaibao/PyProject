#!/usr/bin/env python
# encoding: utf-8

import json
import time
import sys
import os
import pyodbc
import base64
import MySQLdb
from comm import StrMD5
from comm import StrSqlConn
from comm import SessionLogin
from comm import SessionCheck

from htmlencode import parse_sess
from htmlencode import check_role
from comm import LogSet
from logbase import common
from index import PGetPermissions
from generating_log import system_log
from flask import Flask,Blueprint,request,session,render_template # 
from jinja2 import Environment,FileSystemLoader
globalstrategy_change = Blueprint('globalstrategy_change',__name__)

ERRNUM_MODULE_globalstrategy = 1000
reload(sys)
sys.setdefaultencoding('utf-8')
def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()
	
@globalstrategy_change.route('/globalstrategy_show',methods=['GET','POST'])
def globalstrategy_show():
	se = request.form.get('a0')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(se,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	_power=PGetPermissions(userCode)
	_power_json = json.loads(str(_power));
	manage_power_id = []
	for one in _power_json:
		if one['Mode'] == 2:
			manage_power_id.append(one['SubMenuId'])
	return render_template('globalstrategy_change.html',se=se,manage_power_id=manage_power_id)

@globalstrategy_change.route('/get_personnel',methods=['GET','POST'])
def get_personnel():
	session = request.form.get('a0')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetUser\"(null,0);")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@globalstrategy_change.route('/get_eventalarminfo',methods=['GET','POST'])
def get_eventalarminfo():
	id = request.form.get('z1')
	session = request.form.get('a0')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if id == "-1":
				curs.execute("select public.\"PGetEventAlarmInfo\"(null,null,null,null,null);")
			else:
				debug("select public.\"PGetEventAlarmInfo\"(%d,null,null,null,null);" %(int(id)))
				curs.execute("select public.\"PGetEventAlarmInfo\"(%d,null,null,null,null);" %(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@globalstrategy_change.route('/save_globalstrategy',methods=['GET','POST'])
def save_globalstrategy():
	g_data  = request.form.get('z1')
	pwd_data  = request.form.get('z2')
	session = request.form.get('a0')
	md5_str = request.form.get('m1')
	md5_str1 = request.form.get('m2')
	client_ip = request.remote_addr
	(error,userCode,mac) = SessionCheck(session,client_ip);
	if error < 0:
		return "{\"Result\":false,\"info\":\"系统繁忙(%d)\"}" %(sys._getframe().f_lineno)
	elif error > 0:
		if error == 2:
			return "{\"Result\":false,\"info\":\"非法访问(%d)\"}" %(sys._getframe().f_lineno)
		else:
			return "{\"Result\":false,\"info\":\"系统超时(%d)\"}" %(sys._getframe().f_lineno)
	if md5_str < 0 or md5_str =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json = StrMD5(g_data);##python中的json的MD5
		if(parse_sess(md5_str,session,md5_json) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if md5_str1 < 0 or md5_str1 =='':#md5_str ajax传过来的md5值
		return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"
	else:
		md5_json1 = StrMD5(pwd_data);##python中的json的MD5
		if(parse_sess(md5_str1,session,md5_json1) == False): # md5_json 是python里面json数据的md5值
			return "{\"Result\":false,\"ErrMsg\":\"拒绝访问\"}"

	if check_role(userCode,'全局策略') == False:
		return "{\"Result\":false,\"ErrMsg\":\"无权限访问(%d)\"}" % (sys._getframe().f_lineno)
	try:
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetGlobalStrategy\"();")
			
			old_strategy = json.loads(curs.fetchall()[0][0].encode('utf-8'))
			debug("old_strategy:%s" % str(old_strategy))
			new_strategy = json.loads(g_data)
			debug("new_strategy:%s" % g_data)
			
			curs.execute("select public.\"PSaveGlobalStrategy\"(E\'%s\');"%(MySQLdb.escape_string(g_data).decode('utf-8')))
			results = curs.fetchall()[0][0].encode('utf-8')
			g_re = json.loads(results)
			if g_re['Result'] == True:
				sql = "select public.\"PGetPwdStrategy\"();"
				curs.execute(sql)
				old_pwdstrategy = json.loads(curs.fetchall()[0][0].encode('utf-8'))
				debug("old_pwdstrategy:%s" % str(old_pwdstrategy))
				new_pwdstrategy = json.loads(pwd_data)
				debug("new_pwdstrategy:%s" % str(pwd_data))
				
				sql="select public.\"PSavePwdStrategy\"(E'%s')" %(MySQLdb.escape_string(pwd_data).decode("utf-8"))
				curs.execute(sql)
				results = curs.fetchall()[0][0].encode('utf-8')
				pwd_re = json.loads(results)
				
				t_f_dict = {"True":"启用","False":"禁用"}
				remind_dict = {"0":"提示","1":"保存","2":"不保存"}
				alarm_dict = {"0":"不告警","1":"异常登录告警","2":"登录告警","3":"全部告警"}
				if pwd_re['Result'] == False:
					system_log(userCode,'保存全局策略','失败：'+g_re['ErrMsg'],'运维管理>全局策略')
					conn.rollback()
				else:
					show_msg_list = []
					#安全策略
					if old_pwdstrategy['PwdMinLen'] != new_pwdstrategy['PwdMinLen']:
						PwdMinLen = "密码最小长度：" + str(new_pwdstrategy['PwdMinLen'])
						show_msg_list.append(PwdMinLen)
					debug("111111111111111111111111111111")
					if old_pwdstrategy['IfPwdUseExpire'] != new_pwdstrategy['IfPwdUseExpire']:
						IfPwdUseExpire = "密码使用期限：" + t_f_dict[str(new_pwdstrategy['IfPwdUseExpire'])]
						if new_pwdstrategy['IfPwdUseExpire']:
							if new_pwdstrategy['PwdUseExpireNotify'] == 0:
								IfPwdUseExpire = "%s（%d天，不提醒）" % (IfPwdUseExpire,new_pwdstrategy['PwdUseExpire'])
							else:
								IfPwdUseExpire = "%s（%d天，过期前%d天将自动提醒）" % (IfPwdUseExpire,new_pwdstrategy['PwdUseExpire'],new_pwdstrategy['PwdUseExpireNotify'])
						show_msg_list.append(IfPwdUseExpire)
					else:
						PwdUseExpire_list = []
						if old_pwdstrategy['PwdUseExpire'] != new_pwdstrategy['PwdUseExpire']:
							PwdUseExpire = "%d天" % new_pwdstrategy['PwdUseExpire']
							PwdUseExpire_list.append(PwdUseExpire)
							
						if old_pwdstrategy['PwdUseExpireNotify'] != new_pwdstrategy['PwdUseExpireNotify']:
							if new_pwdstrategy['PwdUseExpireNotify'] == 0:
								PwdUseExpireNotify = "过期不提醒"
							else:
								PwdUseExpireNotify = "过期前%d天将自动提醒" % new_pwdstrategy['PwdUseExpireNotify']
							PwdUseExpire_list.append(PwdUseExpireNotify)
						
						if len(PwdUseExpire_list) > 0:
							IfPwdUseExpire = "密码使用期限（%s）" % ('，'.join(PwdUseExpire_list))
							show_msg_list.append(IfPwdUseExpire)
					debug("222222222222222222222222222222")
					if old_pwdstrategy['IfPwdComplex'] != new_pwdstrategy['IfPwdComplex']:
						IfPwdComplex = "密码复杂度要求：" + t_f_dict[str(new_pwdstrategy['IfPwdComplex'])]
						pwd_list = []
						if new_pwdstrategy['IfPwdIncUpperApha']:
							pwd_list.append("大写字母")
						if new_pwdstrategy['IfPwdIncLowerApha']:
							pwd_list.append("小写字母")
						if new_pwdstrategy['IfPwdIncNumber']:
							pwd_list.append("数字")
						if new_pwdstrategy['IfPwdIncSpecialChar']:
							pwd_list.append("特殊字符")
						if len(pwd_list) > 0:
							IfPwdComplex = IfPwdComplex + '（' + '、'.join(pwd_list) + '）'
						show_msg_list.append(IfPwdComplex)
					else:
						pwd_list = []
						if old_pwdstrategy['IfPwdIncUpperApha'] != new_pwdstrategy['IfPwdIncUpperApha']:
							if new_pwdstrategy['IfPwdIncUpperApha']:
								pwd_list.append("增加大写字母")
							else:
								pwd_list.append("取消大写字母")
						
						if old_pwdstrategy['IfPwdIncLowerApha'] != new_pwdstrategy['IfPwdIncLowerApha']:
							if new_pwdstrategy['IfPwdIncLowerApha']:
								pwd_list.append("增加小写字母")
							else:
								pwd_list.append("取消小写字母")
						
						if old_pwdstrategy['IfPwdIncNumber'] != new_pwdstrategy['IfPwdIncNumber']:
							if new_pwdstrategy['IfPwdIncNumber']:
								pwd_list.append("增加数字")
							else:
								pwd_list.append("取消数字")
						if old_pwdstrategy['IfPwdIncSpecialChar'] != new_pwdstrategy['IfPwdIncSpecialChar']:
							if new_pwdstrategy['IfPwdIncSpecialChar']:
								pwd_list.append("增加特殊字符")
							else:
								pwd_list.append("取消特殊字符")
						
						if len(pwd_list) > 0:
							show_msg = "密码复杂度要求（%s）" % ('、'.join(pwd_list))
							show_msg_list.append(show_msg)
					debug("333333333333333333333333333333")	
					if old_pwdstrategy['IfPwdUnRepeat'] != new_pwdstrategy['IfPwdUnRepeat']:
						IfPwdUnRepeat = "密码安全策略：" + t_f_dict[str(new_pwdstrategy['IfPwdUnRepeat'])]
						if new_pwdstrategy['IfPwdUnRepeat']:
							IfPwdUnRepeat = "%s（不能与前%d次密码重复）" % (IfPwdUnRepeat,new_pwdstrategy['PwdUnRepeat'])
						show_msg_list.append(IfPwdUnRepeat)
					else:
						if old_pwdstrategy['PwdUnRepeat'] != new_pwdstrategy['PwdUnRepeat']:
							show_msg = "密码安全策略（不能与前%d次密码重复）" % new_pwdstrategy['PwdUnRepeat']
							show_msg_list.append(show_msg)
					
					debug("666666666666666666666666666666")
					if old_pwdstrategy['IfPwdErrorLock'] != new_pwdstrategy['IfPwdErrorLock']:
						IfPwdErrorLock = "账户锁定策略：" + t_f_dict[str(new_pwdstrategy['IfPwdErrorLock'])]
						if new_pwdstrategy['IfPwdErrorLock']:
							PwdErrorLockExpire = "%d分钟内" % new_pwdstrategy['PwdErrorLockExpire']
							PwdErrorLockNumber = "连续输错%d次即锁定账户" % new_pwdstrategy['PwdErrorLockNumber']
							IfPwdErrorLock = IfPwdErrorLock + '（' + PwdErrorLockExpire + PwdErrorLockNumber + '）'
						show_msg_list.append(IfPwdErrorLock)
					else:
						if old_pwdstrategy['PwdErrorLockExpire'] != new_pwdstrategy['PwdErrorLockExpire']:
							PwdErrorLockExpire = "%d分钟内" % new_pwdstrategy['PwdErrorLockExpire']
						else:
							PwdErrorLockExpire = ""

						if old_pwdstrategy['PwdErrorLockNumber'] != new_pwdstrategy['PwdErrorLockNumber']:
							PwdErrorLockNumber = "连续输错%d次即锁定账户" % new_pwdstrategy['PwdErrorLockNumber']
						else:
							PwdErrorLockNumber = ""
						
						if PwdErrorLockExpire + PwdErrorLockNumber != "":
							IfPwdErrorLock = "账户锁定策略（" + PwdErrorLockExpire + PwdErrorLockNumber + "）"
							show_msg_list.append(IfPwdErrorLock)
					debug("777777777777777777777777777777")
					if old_pwdstrategy['IfAccountAutoUnLock'] != new_pwdstrategy['IfAccountAutoUnLock']:
						IfAccountAutoUnLock = "账户自动解锁：" + t_f_dict[str(new_pwdstrategy['IfAccountAutoUnLock'])]
						if new_pwdstrategy['IfAccountAutoUnLock']:
							AccountAutoUnLock = "%d分钟后自动解锁" % new_pwdstrategy['AccountAutoUnLock']
							IfAccountAutoUnLock = "%s（%s）" % (IfAccountAutoUnLock,AccountAutoUnLock)
						show_msg_list.append(IfAccountAutoUnLock)
					else:
						if old_pwdstrategy['AccountAutoUnLock'] != new_pwdstrategy['AccountAutoUnLock']:
							AccountAutoUnLock = "%d分钟后自动解锁" % new_pwdstrategy['AccountAutoUnLock']
							show_msg_list.append(AccountAutoUnLock)
					debug("888888888888888888888888888888")
					if old_pwdstrategy['IfNeedCode'] != new_pwdstrategy['IfNeedCode']:					
						IfNeedCode = "登录验证码：" + t_f_dict[str(new_pwdstrategy['IfNeedCode'])]
						show_msg_list.append(IfNeedCode)
					debug("111111111111111111111111111111")
					#运维策略
					if old_strategy['LoginUniqueIP'] != new_strategy['LoginUniqueIP']:
						LoginUniqueIP = "登录限制：" + t_f_dict[str(new_strategy['LoginUniqueIP'])]
						show_msg_list.append(LoginUniqueIP)
					debug("111111111111111111111111111112")	
					if old_strategy['ConnectTimeOut'] != new_strategy['ConnectTimeOut']:
						if new_strategy['ConnectTimeOut'] != 0:
							ConnectTimeOut = "超时设置：启用，超时时间：" + str(new_strategy['ConnectTimeOut'])
						else:
							ConnectTimeOut = "超时设置：禁用"
						show_msg_list.append(ConnectTimeOut)
					debug("111111111111111111111111111113")
					if old_strategy['MapPort'] != new_strategy['MapPort']:
						MapPort = "映射端口：" + str(new_strategy['MapPort'])
						show_msg_list.append(MapPort)
					debug("111111111111111111111111111114")
					if old_strategy['IsTunnel'] != new_strategy['IsTunnel']:
						IsTunnel = "运维访问通道：" + t_f_dict[str(new_strategy['IsTunnel'])]
						show_msg_list.append(IsTunnel)
					debug("111111111111111111111111111115")
					if old_strategy['FileRecordOpened'] != new_strategy['FileRecordOpened']:
						FileRecordOpened = "文件传输记录：" + t_f_dict[str(new_strategy['FileRecordOpened'])]
						if new_strategy['FileRecordOpened']:
							FileRecordOpened = FileRecordOpened + "，磁盘限额：" + str(new_strategy['FileRecordDiskLimit'])
						show_msg_list.append(FileRecordOpened)
					else:
						if str(old_strategy['FileRecordDiskLimit']) != str(new_strategy['FileRecordDiskLimit']) and new_strategy['FileRecordDiskLimit'] != None:
							FileRecordDiskLimit = "文件记录（磁盘限额：%s）" % str(new_strategy['FileRecordDiskLimit'])
							show_msg_list.append(FileRecordDiskLimit)
					debug("111111111111111111111111111116")
					if old_strategy['IfHiddenHostIP'] != new_strategy['IfHiddenHostIP']:
						IfHiddenHostIP = "隐藏主机IP：" + t_f_dict[str(new_strategy['IfHiddenHostIP'])]
						show_msg_list.append(IfHiddenHostIP)
					debug("111111111111111111111111111117")	
					if old_strategy['IsRemindSaveUser'] != new_strategy['IsRemindSaveUser']:
						IsRemindSaveUser = "账号密码保存：" + remind_dict[str(new_strategy['IsRemindSaveUser'])]
						show_msg_list.append(IsRemindSaveUser)
					debug("111111111111111111111111111118")
					if old_strategy['AccControlOpened'] != new_strategy['AccControlOpened']:
						AccControlOpened = "应用发布访问控制：" + t_f_dict[str(new_strategy['AccControlOpened'])]
						show_msg_list.append(AccControlOpened)
					debug("111111111111111111111111111119")
					if old_strategy['SyslogOpened'] != new_strategy['SyslogOpened']:
						SyslogOpened = "SYSLOG发送：" + t_f_dict[str(new_strategy['SyslogOpened'])]
						show_msg_list.append(SyslogOpened)
					debug("1111111111111111111111111111111")	
					if old_strategy['EnableApprove'] != new_strategy['EnableApprove']:
						EnableApprove = "登录审批：" + t_f_dict[str(new_strategy['EnableApprove'])]
						if new_strategy['EnableApprove']:
							EnableApprove = "%s（%s）" % (EnableApprove, new_strategy['ApproveStrategyName'])
						show_msg_list.append(EnableApprove)
					else:
						if old_strategy['ApproveStrategyName'] != new_strategy['ApproveStrategyName'] and new_strategy['ApproveStrategyName'] != None:
							ApproveStrategyName = "登录审批（%s）" % new_strategy['ApproveStrategyName']
							show_msg_list.append(ApproveStrategyName)
					debug("1111111111111111111111111111112")
					if old_strategy['IfGiveAccessInfo'] != new_strategy['IfGiveAccessInfo']:
						IfGiveAccessInfo = "访问备注：" + t_f_dict[str(new_strategy['IfGiveAccessInfo'])]
						show_msg_list.append(IfGiveAccessInfo)
					debug("1111111111111111111111111111113")
					if old_strategy['IfForceAidance'] != new_strategy['IfForceAidance']:
						IfForceAidance = "协同登录：" + t_f_dict[str(new_strategy['IfForceAidance'])]
						show_msg_list.append(IfForceAidance)
					debug("111111111111111111111111111114")
					if str(old_strategy['EnableAlarm']) != str(new_strategy['EnableAlarm']):
						EnableAlarm = "登录告警：" + alarm_dict[str(new_strategy['EnableAlarm'])]
						if new_strategy['EventAlarmInfoName']:
							EnableAlarm = "%s（%s）" % (EnableAlarm, new_strategy['EventAlarmInfoName'])
						show_msg_list.append(EnableAlarm)
					else:
						if old_strategy['EventAlarmInfoName'] != new_strategy['EventAlarmInfoName'] and new_strategy['EventAlarmInfoName'] != None:
							EventAlarmInfoName = "登录告警（%s）" % new_strategy['EventAlarmInfoName']
							show_msg_list.append(EventAlarmInfoName)
					if old_strategy['AccIPSet']==None and new_strategy['AccIPSet']==None:
						pass
					elif new_strategy['AccIPSet']==None:
						show_msg_list.append('指定应用发布（禁用）')
					elif (old_strategy['AccIPSet']==None) or (len(old_strategy['AccIPSet'])!=len(new_strategy['AccIPSet'])):
						acc_arr=[]
						for acc_item in new_strategy['AccIPSet']:
							if acc_item['AccIP']=='':
								acc_arr.append('内置：%s'%acc_item['AccIPId'])
							else:
								acc_arr.append('外置：%s'%acc_item['AccIP'])
						if len(acc_arr)>0:
							show_msg_list.append('指定应用发布（%s）'%('，'.join(acc_arr)))
					# elif len(old_strategy['AccIPSet'])!=len(new_strategy['AccIPSet']):
					else:
						acc_arr=[]
						pass_all_value=True
						for acc_item in new_strategy['AccIPSet']:
							pass_value=False
							for acc_old in old_strategy['AccIPSet']:
								if acc_item['AccIPId']==acc_old['AccIPId']:
									pass_value=True
									break
							if pass_value==True:
								continue
							else:
								pass_all_value=False
						if pass_all_value==True:
							pass
						else:
							acc_arr=[]	
							for acc_item in new_strategy['AccIPSet']:
								if acc_item['AccIP']=='':
									acc_arr.append('内置：%s'%acc_item['AccIPId'])
								else:
									acc_arr.append('外置：%s'%acc_item['AccIP'])
							if len(acc_arr)>0:
								show_msg_list.append('指定应用发布（%s）'%('，'.join(acc_arr)))
					debug("111111111111111111111111111115")
					if len(show_msg_list) > 0:
						show_msg = "修改全局策略（%s）" % ("，".join(show_msg_list))
						system_log(userCode,show_msg,"成功",'运维管理>全局策略')
			else:
				system_log(userCode,'保存全局策略','失败：'+g_re['ErrMsg'],'运维管理>全局策略')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@globalstrategy_change.route('/get_globalstrategy',methods=['GET','POST'])
def get_globalstrategy():
	session = request.form.get('a0')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			curs.execute("select public.\"PGetGlobalStrategy\"();")
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

@globalstrategy_change.route('/get_approve_personnel',methods=['GET','POST'])
def get_approve_personnel():
	id = request.form.get('z1')
	session = request.form.get('a0')
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
		with pyodbc.connect(StrSqlConn('BH_CONFIG')) as conn:
			curs = conn.cursor()
			if id == "-1":
				curs.execute("select public.\"PGetApproveStrategy\"(null,null,null,null);")
			else:
				debug("select public.\"PGetApproveStrategy\"(%d,null,null,null);" %(int(id)))
				curs.execute("select public.\"PGetApproveStrategy\"(%d,null,null,null);" %(int(id)))
			results = curs.fetchall()[0][0].encode('utf-8')
			return results	
	except pyodbc.Error,e:
		return "{\"Result\":false,\"ErrMsg\":\"系统异常: %s(%d)\"}" % (ErrorEncode(e.args[1]),sys._getframe().f_lineno)

