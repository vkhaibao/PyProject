# coding=utf8
class my_mid():


    def __init__(self, request):
        """初始化：无需任何参数,服务器响应第一个请求的时候调用一次，用于确定是否启用当前中间件"""
        print('--------------init')

    def process_request(self, request):
        """处理请求前：在每个请求上，request对象产生之后，url匹配之前调用 返回HttpResponse对象"""
        print('--------------request')

    def process_view(self, request, view_func, *view_args, **view_kwargs):
        """处理视图前：在每个请求上，url匹配之后，视图函数调用之前调用 返回HttpResponse对象"""
        print('--------------view')

    def process_response(self, request, response):
        """处理响应后：视图函数调用之后，所有响应返回浏览器之前被调用，在每个请求上调用 返回一个HttpResponse对象"""
        print('--------------response')
        return response