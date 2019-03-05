from django.contrib import admin
from booktest.models import *
# Register your models here.
class GoodsInfoAdmin(admin.ModelAdmin):
    list_display = ['id']


admin.site.register(GoodsInfo, GoodsInfoAdmin)


