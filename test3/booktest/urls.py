# coding=utf8
from booktest import views
from django.conf.urls import include, url
"""
方式一：位置参数
直接使用小括号，通过位置参数传递给视图

urlpatterns =[
    url(r'^$', views.index),
    url(r'^delete(\d+)/$', views.show_arg),
]
"""
"""
方式二：关键字参数
在正则表达式部分为组命名
"""
urlpatterns = [
    url(r'^$', views.index),
    url(r'^static_test/$', views.static_test),
    url(r'^delete/a=(?P<id>\d+)$', views.show_arg),
    url(r'^method_show/$', views.method_show),
    url(r'^show_reqarg/$', views.show_reqarg),
    url(r'^index2/$', views.index2),
    url(r'^index3/$', views.index3),
    url(r'^json1/$', views.json1),
    url(r'^json2/$', views.json2),
    url(r'^red1/$', views.red1),
    url(r'^cookie_set/$', views.cookie_set),
    url(r'^cookie_get/$', views.cookie_get),
    url(r'^session_set/$', views.session_set),
    url(r'^pic_upload/$', views.pic_upload),
    url(r'^pic_handle/$', views.pic_handle),
    url(r'^pic_show/$', views.pic_show),
    url(r'^page(?P<pIndex>[0-9]*)/$', views.page_test),
    url(r'^area1/$', views.area1),
    url(r'^area2/$', views.area2),
    url(r'^area3_(\d+)/$', views.area3),
]

