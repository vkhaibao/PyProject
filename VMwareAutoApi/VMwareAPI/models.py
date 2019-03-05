from django.db import models

# Create your models here.

class DataStore(models.Model):
    datasotrename = models.CharField(max_length=500)
    freespace = models.FloatField(null=True)
    hostname = models.ForeignKey('VMHost', on_delete=models.CASCADE)

    class Meta:
        db_table = 'DataStore'

class VMHost(models.Model):
    hostname = models.CharField(max_length=250)
    clustername = models.ForeignKey('VMCluster', on_delete=models.CASCADE)
    datacentername = models.ForeignKey('VMDatacenter', on_delete=models.CASCADE)

    class Meta:
        db_table = 'VMHost'


class VMCluster(models.Model):
    clustername = models.CharField(max_length=250)
    datacentername = models.ForeignKey('VMDatacenter', on_delete=models.CASCADE)

    class Meta:
        db_table = 'VMCluster'


class VMVirtual(models.Model):
    vmname = models.CharField(max_length=500)
    vmstatus = models.CharField(max_length=500, null=True)
    istemplate = models.BooleanField(default=True)
    hostname = models.ForeignKey('VMHost', null=True, on_delete=models.CASCADE)
    clustername = models.ForeignKey('VMCluster', null=True, on_delete=models.CASCADE)
    datacentername = models.ForeignKey('VMDatacenter', on_delete=models.CASCADE)

    class Meta:
        db_table = 'VMVirtual'


"""        
class VMFloder(models.Model):

    class Meta:
        db_table = 'VMFloder'

class VMResouce(models.Model):

    class Meta:
        db_table = 'VMResouce'
"""


class VMDatacenter(models.Model):
    datacentername = models.CharField(max_length=250)
    class Meta:
        db_table = 'VMDatacenter'

