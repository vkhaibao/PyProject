# coding=utf8
from django.shortcuts import render, redirect, HttpResponse
from booktest.models import *
from PIL import Image, ImageDraw, ImageFont
from django.utils.six import BytesIO
# Create your views here.

def index(request):
    return render(request, 'bootest/index.html')

def temp_var(request):
    book = BookInfo.objects.all()
    return render(request, 'bootest/temp_var.html', {'list': book})

def temp_tag(request):
    book = BookInfo.objects.all()
    return render(request, 'bootest/temp_tag.html', {'list': book})

def temp_filter(request):
    book = BookInfo.objects.all()
    return render(request, 'bootest/temp_filter.html', {'list': book})

def temp_inherit(request):
    context = {'title': '模板继承', 'list': BookInfo.objects.all()}
    return render(request, 'bootest/temp_inherit.html', context)

def html_escape(request):
    context = {'content': '<b>hello world</b>'}
    return render(request, 'bootest/html_escape.html', context)


def login(request):
    return render(request, 'bootest/login.html')

def login_check(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    # 校验
    if username == 'smart' and password == '123':
        request.session['username'] = username
        request.session['islogin'] = True
        return redirect('/post/')
    else:
        return redirect('/login/')

def post(request):
    return render(request, 'bootest/post.html')

def post_action(request):
    if request.session['islogin']:
        username = request.session['username']
        return HttpResponse('用户' + username + '发送了一个帖子')
    else:
        return HttpResponse('发帖失败')

def verify_code(request):
    import random
    # 定义颜色，以及高度和宽度
    bgcolor = (random.randrange(20, 100), random.randrange(20, 200), 255)
    width = 100
    height = 25
    # 创建画面对象
    im = Image.new('RGB', (width, height), bgcolor)
    # 创建画笔对象
    draw = ImageDraw.Draw(im)
    # 调用画笔的point()函数绘制噪点
    for i in range(100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill=fill)
    # 定义验证码的备选值
    strcode = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    # 随机选取4个值作为验证码
    rand_str = ''
    for i in range(0, 4):
        rand_str += strcode[random.randrange(0, len(strcode))]
    # 构造字体对象
    font = ImageFont.truetype("CENTURY.TTF", 20)
    fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
    # 绘制4个字
    draw.text((5, 1), rand_str[0], font=font, fill=fontcolor)
    draw.text((25, 1), rand_str[1], font=font, fill=fontcolor)
    draw.text((50, 1), rand_str[2], font=font, fill=fontcolor)
    draw.text((75, 1), rand_str[3], font=font, fill=fontcolor)
    # 释放画笔
    del draw
    # 存入session，用于做进一步验证
    request.session['verifycode'] = rand_str
    # 内存文件操作
    buf = BytesIO()
    # 将图片保存在内存中，文件类型为png
    im.save(buf, 'png')
    # 将内存中的图片数据返回给客户端，MIME类型为图片png
    return HttpResponse(buf.getvalue(), 'image/png')

def verify_show(request):
    return render(request, 'bootest/verify_show.html')

def verify_yz(request):
    yzm = request.POST.get('yzm')
    verify_code = request.session['verifycode']
    response = HttpResponse('验证失败')
    if yzm == verify_code:
        response = HttpResponse('验证成功')
    return response

def fan1(request):
    return render(request, 'bootest/fan1.html')

def fan2(request, num):
    return HttpResponse('fan2')

def fan3(request, a, b):
    return HttpResponse(int(a)+int(b))

def fan4(request, id, age):
    return HttpResponse(int(id) + int(age))


