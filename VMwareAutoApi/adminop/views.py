#coding=utf8
from django.shortcuts import render, redirect, HttpResponse
from VMwareAPI.models import *
from django.contrib.auth.models import User
from VMwareAPI.views import logincheck, authcheck

# Create your views here.

@logincheck
@authcheck
def adminop(request):
    rightlist = Rightlist.objects.all()
    modellist = {"rightlist": rightlist, "username": request.user}
    return render(request, 'adminop/adminop.html', modellist)

@logincheck
def userlist(request):
    userlist = User.objects.all()
    modellist = {"userlist": userlist, "username": request.user}
    return render(request, 'adminop/userlist.html', modellist)

@logincheck
def modelist(request):
    modellist = ModelList.objects.all()
    modellists = {"modellist": modellist, "username": request.user}
    return render(request, 'adminop/modelist.html', modellists)

