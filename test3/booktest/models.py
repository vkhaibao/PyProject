# coding=utf8
from django.db import models

# Create your models here.
from django.db import models
class AreaInfo(models.Model):

    atitle = models.CharField('城市', max_length=30)
    aParent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.atitle

    def title(self):
        return self.atitle

    def parent(self):
        if self.aParent is None:
            return ''
        return self.aParent.atitle

    title.admin_order_field = 'atitle'
    title.short_description = '区域名称'
    parent.admin_order_fiedl = 'atitle'
    parent.short_description = '上级区域名称'

    class Meta:
        db_table = 'AreaInfo'


class PicTest(models.Model):
    pic = models.ImageField(upload_to='booktest/')