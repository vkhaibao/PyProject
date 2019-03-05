from django.shortcuts import render
from booktest.models import BookInfo
# Create your views here.
#from django.http import HttpResponse
#from django.template import loader, RequestContext
"""
def index(request):
    """
#    1.找到模板
#    2.定义上下文
#    3.渲染模板
"""
    # 定义模板
    template = loader.get_template("booktest/index.html")
    # 定义上下文
    context = {'title': '图书列表', 'list': range(10)}
    # 渲染模板
    return HttpResponse(template.render(context))
"""
"""
视图调用模板简写
"""
def index(request):
    booklist = BookInfo.objects.all()
    return render(request, 'booktest/index.html', {'booklist': booklist})


def detail(request, bid):
    book = BookInfo.objects.get(id=int(bid))
    heros =book.heroinfo_set.all()
    return render(request, 'booktest/detail.html', {'book': book, 'heros': heros})