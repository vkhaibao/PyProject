# coding=utf8
from django.shortcuts import render, redirect
from booktest.models import *
from datetime import date
import urllib
# Create your views here.

# 查看所有图书并显示
# def index(request):
#    booklist = BookInfo.objects.all()
#    return render(request, 'booktest/index.html', context={'booklist': booklist})


# 创建新图书
def create(request):
    book = BookInfo()
    book.btitle = "流星蝴蝶剑"
    book.bpub_data = date(2018, 10, 10)
    book.save()
    return redirect('/')


# 逻辑删除指定编号的图书
def delete(request, id):
    del_book = BookInfo.objects.get(id=int(id))
    del_book.delete()
    return redirect('/')


def area(request):
    if request.method == 'GET':
        atitle = request.GET.get('atitle')
        area = AreaInfo.objects.get(atitle=atitle)
        return render(request, 'booktest/area.html', context={'area': area})

def index(request):
    area = AreaInfo.objects.get(atitle="宿迁市")
    return render(request, 'booktest/index.html', context={'area': area})