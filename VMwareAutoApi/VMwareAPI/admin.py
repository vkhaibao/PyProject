from django.contrib import admin
from VMwareAPI.models import *
# Register your models here.


@admin.register(VMDatacenter)
class VMDatacenterAdmin(admin.ModelAdmin):
    list_display = ['id', 'datacentername']

@admin.register(VMCluster)
class VMClusterAdmin(admin.ModelAdmin):
    list_display = ['id', 'clustername', 'datacentername_id']

@admin.register(VMVirtual)
class VMVirtualAdmin(admin.ModelAdmin):
    list_display = ['id', 'vmname', 'vmstatus', 'istemplate', 'clustername_id', 'datacentername_id']

@admin.register(VMHost)
class VMHostAdmin(admin.ModelAdmin):
    list_display = ['id', 'hostname', 'clustername_id', 'datacentername_id']

@admin.register(DataStore)
class DataStoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'datasotrename', 'hostname_id', 'freespace']