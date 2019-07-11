#coding=utf8
"""VMwareAutoApi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from itomap import views
import django_cas_ng.views
app_name = 'itomap'
urlpatterns = [
    path('', views.index, name='root'),
    path('index', views.index, name='index'),

    path('login', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'),
    path('logout', django_cas_ng.views.LogoutView.as_view(), name='cas_ng_logout'),
    path('callback', django_cas_ng.views.CallbackView.as_view(), name='cas_ng_proxy_callback'),

    path('accountm', views.accountm, name='accountm'),
    path('orgm', views.orgm, name='orgm'),
    path('plicm', views.plicm, name='plicm')
]
