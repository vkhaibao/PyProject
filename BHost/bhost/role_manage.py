#!/usr/bin/env python
# encoding: utf-8

import os
import sys
from flask import Flask,Blueprint,request,render_template # 
b_role_manage = Blueprint('b_role_manage',__name__)

@b_role_manage.route('/role_manage',methods=['GET', 'POST'])
def role_manage():
	t = "role_list.html"	
	return render_template(t)
	












