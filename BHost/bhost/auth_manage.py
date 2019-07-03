#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from flask import Flask,Blueprint,request,render_template # 
b_auth_manage = Blueprint('b_auth_manage',__name__)

def debug(c):
	return 0
	path = "/var/tmp/debugzdp.txt"
	fp = open(path,"a+")
	if fp :
		fp.write(c)		
		fp.write("\n")
		fp.close()

@b_auth_manage.route('/auth_manage',methods=['GET', 'POST'])
def auth_manage():
	tasktype = request.form.get('tasktype') # 0->用户列表 1->角色列表 
	if tasktype < 0:
		tasktype = "0"		
	if tasktype == '0':
		t = "access_list.html"
	elif tasktype == '1':
		t = "worktask_list.html"
	else:
		t = "command_list.html"	
	return render_template(t)
	
"""
@b_auth_manage.route('/add_access_auth',methods=['GET', 'POST'])
def add_access_auth():
	now = request.form.get('z1')
	edit = request.form.get('z2')
	type = request.form.get('z3')
	keyword = request.form.get('z4')
	manage_filter_flag = request.form.get('z5')
	debug(now)
	t = "add_access_auth.html"
	if edit != "None":
		return render_template(t,edit=edit,now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag)
	else:
		return render_template(t,edit='"None"',now=now,tasktype=type,keyword=keyword,manage_filter_flag=manage_filter_flag)	
"""
@b_auth_manage.route('/add_role',methods=['GET', 'POST'])
def add_role():
	t = "add_role.html"	
	return render_template(t)








