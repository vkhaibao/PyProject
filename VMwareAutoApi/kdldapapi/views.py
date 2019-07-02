#coding=utf8
from VMwareAPI.models import *
from django.contrib.sessions.models import Session
from django.shortcuts import render
from django.shortcuts import render, redirect, HttpResponse
from VMwareAPI.views import logincheck
# Create your views here.

@logincheck
def index(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'ldaptemp/index.html', vmdict)

@logincheck
def accountm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'ldaptemp/accountm.html', vmdict)

@logincheck
def orgm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'ldaptemp/orgm.html', vmdict)

@logincheck
def plicm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'ldaptemp/plicm.html', vmdict)
