#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from flask import Flask,Blueprint,request,render_template # 
b_proto_manage = Blueprint('b_proto_manage',__name__)

@b_proto_manage.route('/proto_manage',methods=['GET', 'POST'])
def proto_manage():
	tasktype = request.form.get('tasktype') # 0->添加 1->编辑 
	if tasktype < 0:
		tasktype = "0"
	t = ""	
	if tasktype == '0':
		t = "proto_add.html"
	elif tasktype == '1':
		t = "proto_edit.html"
		
	return render_template(t)
	
@b_proto_manage.route('/proto_list',methods=['GET', 'POST'])
def proto_list():
	t = "proto_list.html"	
	return render_template(t)











