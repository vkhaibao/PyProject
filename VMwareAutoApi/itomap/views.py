#coding=utf8
from VMwareAPI.models import *
from django.contrib.sessions.models import Session
from django.shortcuts import render
from django.shortcuts import render, redirect, HttpResponse
from VMwareAPI.views import logincheck, authcheck
# Create your views here.
from itomap.bhostdecryt.comm_function import *

@logincheck
@authcheck
def index(request):
    listobj = decrypt()
    vmdict = {"vmlist": listobj, "username": request.user}
    if listobj:
        return render(request, 'itomaptemp/index.html', vmdict)
    else:
        return HttpResponse("failed")

@logincheck
def accountm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'itomaptemp/accountm.html', vmdict)

@logincheck
def orgm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'itomaptemp/orgm.html', vmdict)

@logincheck
def plicm(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'itomaptemp/plicm.html', vmdict)