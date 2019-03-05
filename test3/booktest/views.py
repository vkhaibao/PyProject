# coding=utf8
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from booktest.models import PicTest
from booktest.models import AreaInfo
from django.core.paginator import Paginator
# Create your views here.
def index(request):
    return render(request, 'booktest/index.html')

def static_test(request):
    return render(request, 'booktest/static_test.html')

def index2(request):
    str = '<h1>Hello Word</h1>'
    return HttpResponse(str)

def index3(request):
    # 加载模板
    #t1 = loader.get_template('booktest/index3.html')

    # 构造上下文
    #context = {'h1': 'Hello'}
    # html = t1.render(context)

    # 使用上下文渲染模板，生成字符串后返回响应对象
    # return HttpResponse(html)
    return render(request, 'booktest/index3.html', {'h1': 'Hello'})

def show_arg(request, id):
    return HttpResponse('show_arg %s' %id)


def method_show(request):
    return HttpResponse(request.method)


def show_reqarg(request):

    if request.method == 'GET':
        a = request.GET.get('a')
        b = request.GET.get('b')
        c = request.GET.get('c')
        return render(request, 'booktest/show_getarg.html', context={'a': a, 'b': b, 'c': c})
    else:
        name = request.POST.get('uname')
        gender = request.POST.get('gender')
        hobbys = request.POST.getlist('hobby')
        return render(request, 'booktest/show_postarg.html', context={'name':name, 'gender':gender, 'hobbys':hobbys})


def json1(request):
    return render(request, 'booktest/json1.html')

def json2(request):
    return JsonResponse({'h1': 'hello', 'h2': 'world'})

def red1(request):
    # return HttpResponseRedirect('/')
    return redirect('/')

def cookie_set(request):
    cookie = ('cookie_key', 'cookie_value')
    response = HttpResponse('<h1>设置Cookie，请查看响应报文头</h1>')
    response.set_cookie(cookie[0], cookie[1])
    return response


def cookie_get(request):
    response = HttpResponse('<h1>获取Cookie</h1>')
    for cookie_key in request.COOKIES:
        response.write('<p>' + cookie_key + ": " + request.COOKIES[cookie_key] + '</p>')
    return response


def session_set(request):
    request.session['hi'] = '海宝'
    request.session.set_expiry(None)
    # h1 = request.session.get('hi')
    # request.session.flush()
    return HttpResponse('写Cookie')


def pic_upload(request):
    return render(request, 'booktest/pic_upload.html')

def pic_handle(request):
    f = request.FILES.get('pic')
    fname = '%s/booktest/%s' % (settings.MEDIA_ROOT, f.name)
    with open(fname, 'wb') as pic:
        for c in f.chunks():
            pic.write(c)
    picname = "booktest/" + f.name
    dic = {"pic": picname}
    PicTest.objects.create(**dic)
    return HttpResponse("%s上传成功" % f.name)


def pic_show(request):
    pic = PicTest.objects.all()
    context = {'list': pic}
    return render(request, 'booktest/pic_show.html', context)

def page_test(request, pIndex):
    # 查询所有的地区信息
    list1 = AreaInfo.objects.filter(aParent__isnull=True)
    # 将地区信息按一页10条进行分页
    p = Paginator(list1, 10)
    # 如果当前没有传递页码信息，则认为是第一页，这样写是为了请求第一页时可以不写页码
    if pIndex == '':
        pIndex = '1'

    # 通过url匹配的参数都是字符串类型，转换成int类型
    pIndex = int(pIndex)
    # 获取第pIndex页的数据
    list2 = p.page(pIndex)
    # 获取所有的页码信息
    plist = p.page_range
    # 将当前页码、当前页的数据、页码信息传递到模板中
    return render(request, 'booktest/page_test.html', {'list': list2, 'plist': plist, 'pIndex': pIndex})

def area1(request):
    return render(request, 'booktest/area1.html')


def area2(request):
    list = AreaInfo.objects.filter(aParent__isnull=True)
    list2 = []
    for item in list:
        list2.append([item.id, item.atitle])
    return JsonResponse({'data': list2})

def area3(request, pid):
    list = AreaInfo.objects.filter(aParent_id=pid)
    list2 = []
    for item in list:
        list2.append([item.id, item.atitle])
    return JsonResponse({'data': list2})