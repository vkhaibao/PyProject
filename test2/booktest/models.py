from django.db import models

# Create your models here.
# 定义图书模型类BookInfo

class BookInfoManager(models.Manager):

    def all(self):
        # 默认查询未删除的图书信息
        # 调用父类的成员语法为：super().方法名
        return super().all().filter(isDelete=False)

    # 创建模型类，接收参数为属性赋值
    def create_book(self, title, pub_date):
        # 创建模型类对象self.model可以获得模型类
        book = self.model()
        book.btitle = title
        book.bpub_date = pub_date
        book.bread = 0
        book.bcommet = 0
        book.isDelete = False
        # 将数据插入进数据表
        book.save()
        return book

class BookInfo(models.Model):
    books = BookInfoManager()
    # 图书名称
    btitle = models.CharField(max_length=20)
    # 发布日期
    bpub_data = models.DateField()
    # 阅读量
    bread = models.IntegerField(default=0)
    # 评论量
    bcomment = models.IntegerField(default=0)
    # 逻辑删除
    isDelete = models.BooleanField(default=False)

    class Meta:
        db_table = "BookInfo"

# 定义英雄模型类HeroInfo
class HeroInfo(models.Model):
    # 英雄姓名
    hname = models.CharField(max_length=10)
    # 英雄性别
    hgender = models.BooleanField(default=False)
    # 逻辑删除
    isDelete = models.BooleanField(default=False)
    # 英雄描述信息
    hcommment = models.CharField(max_length=200)
    # 英雄与图书表的关系为一对多，所以属性定义在英雄模型类中
    hbook = models.ForeignKey('BookInfo', on_delete=models.CASCADE)

    class Meta:
        db_table = 'HeroInfo'


class AreaInfo(models.Model):
    atitle = models.CharField(max_length=30)
    aParent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'AreaInfo'