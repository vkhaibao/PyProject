# coding=utf8
from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from booktest import tasks
from booktest.models import GoodsInfo
import time

# Create your views here.
def index(request):
    return render(request, 'booktest/index.html')

def editor(request):
    return render(request, 'booktest/editor.html')

def save_ed(request):
    text = request.POST.get('gcontent')
    text1 = {'gcontent': text}
    GoodsInfo.objects.create(**text1)
    return HttpResponse('%s保存成功' % text1['gcontent'])

def show(request):
    goods = GoodsInfo.objects.all()
    context = {'g': goods}
    return render(request, 'booktest/show.html', context)

def send(request):
    msg = request.POST.get('main_body')
    subject = request.POST.get('subject')
    mail_list = request.POST.get('mail_list')
    mail_list = mail_list.split(',')
    #msg = '<a href="http://www.itcast.cn/subject/pythonzly/index.shtml" target="_blank">点击激活</a>'
    try:
        send_mail(subject,
            '',
            settings.EMAIL_FROM,
            mail_list,
            html_message=msg
        )
        return HttpResponse("发送成功")
    except Exception as ret:
        return HttpResponse("发送失败原因如下: %s" % str(ret))

def send_mails(request):
    return render(request, 'booktest/send_mail.html')

def sayhello(request):
    #print('hello...')
    #time.sleep(2)
    #print('world...')
    tasks.sayhello.delay()
    return HttpResponse("hello world")