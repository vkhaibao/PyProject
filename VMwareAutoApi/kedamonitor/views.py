#coding=utf8
from VMwareAPI.models import *
from django.contrib.sessions.models import Session
from django.shortcuts import render
from django.shortcuts import render, redirect, HttpResponse
from VMwareAPI.views import logincheck, authcheck
from kedamonitor.kedaopmanage import kedaopm
# Create your views here.

@logincheck
def index(request):
    url = "http://10.2.2.33:8086/fault/AlarmView.do?viewId=ActiveAlarms"
    username = "admin"
    password = "admin"
    alertinfo = kedaopm.getalertinfo(url, username, password)
    opalerts = {"alertinfo": alertinfo, "username": request.user}
    return render(request, 'kedamontemp/index.html', opalerts)

@logincheck
def accountm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'kedamontemp/accountm.html', vmdict)

@logincheck
def orgm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'kedamontemp/orgm.html', vmdict)

@logincheck
def plicm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'kedamontemp/plicm.html', vmdict)