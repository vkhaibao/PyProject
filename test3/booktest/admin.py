# coding=utf8
from django.contrib import admin
from booktest.models import *
# Register your models here.


class AreaStackedInline(admin.StackedInline):
    model = AreaInfo
    extra = 2


class AreaTabularInline(admin.TabularInline):
    model = AreaInfo
    extra = 2


@admin.register(AreaInfo)
class AreaAdmin(admin.ModelAdmin):
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = True
    list_display = ['id', 'atitle', 'title', 'parent']
    list_filter = ['atitle']
    search_fields = ['atitle']
    # fields = ['aParent', 'atitle']
    fieldsets = (
        ('基本', {'fields': ['atitle']}),
        ('高级', {'fields': ['aParent']})
    )
    inlines = [AreaStackedInline]
    inlines = [AreaTabularInline]


admin.site.register(PicTest)
# admin.site.register(AreaInfo, AreaAdmin)