#coding=utf8
from VMwareAPI.models import *
from django.shortcuts import render, redirect, HttpResponse
from VMwareAPI.views import logincheck, authcheck
from time import sleep
from .tasks import getinfo
# Create your views here.

@logincheck
def index(request):
    userinfo = {"username": request.user}
    return render(request, 'kedamontemp/index.html', userinfo)

@logincheck
def getalerts(request):
    alertinfo = getinfo.delay()
    opalerts = {"opalerts": alertinfo.get(), "username": request.user}
    return render(request, 'kedamontemp/getalerts.html', opalerts)


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