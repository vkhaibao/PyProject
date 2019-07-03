#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from flask import Flask,Blueprint,request,render_template # 
b_user_manage = Blueprint('b_user_manage',__name__)

@b_user_manage.route('/user_manage',methods=['GET', 'POST'])
def user_manage():
	tasktype = request.form.get('tasktype') # 0->用户列表 1->角色列表 
	if tasktype < 0:
		tasktype = "0"
	if tasktype == '0':
		t = "user_list.html"
	else:
		t = "role_list.html"	
	return render_template(t)
	












