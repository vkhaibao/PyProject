#coding=utf8
from django.shortcuts import render, redirect, HttpResponse
from VMwareAPI.models import *
from VMwareAPI.connvcenter import *
from VMwareAPI.webconsole import *
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from pyVmomi import vim, vmodl
from VMwareAPI.vmtools.clone_vm import *
import json
import datetime
# Create your views here.


def updatevm_db(request):
    """更新数据库"""
    conn.connect_to_vcenter()
    g_vcenter = conn
    listvmobj = g_vcenter.get_allvms()
    listhostobj = g_vcenter.get_hosts()
    listdcobj = g_vcenter.get_vcenters()
    listcrsobj = g_vcenter.get_clusters()
    liststoreobj = g_vcenter.get_datastore()

    datastorename = DataStore.objects.values("datasotrename")

    if len(datastorename) == 0:
        for each in liststoreobj:
            for i in each.host:
                datahostname = i.key.name
                hostnameid = VMHost.objects.filter(hostname=datahostname).values("id")
                filterstore = DataStore.objects.filter(datasotrename=each.name)
                dataspace = each.summary.freeSpace/1024/1024/1024
                freespace = float("%.2f" %dataspace)
                postdata = DataStore(datasotrename=each.name, freespace=freespace, hostname_id=hostnameid[0]["id"])
                postdata.save()
    else:
        for each in liststoreobj:
            for i in each.host:
                datahostname = i.key.name
                hostnameid = VMHost.objects.filter(hostname=datahostname).values("id")
                filterstore = DataStore.objects.filter(datasotrename=each.name)
                if len(filterstore) == 0:
                    dataspace = each.summary.freeSpace / 1024 / 1024 / 1024
                    freespace = float("%.2f" % dataspace)
                    postdata = DataStore(datasotrename=each.name, freespace=freespace, hostname_id=hostnameid[0]["id"])
                    postdata.save()
        liststore = list()
        for each02 in liststoreobj:
            liststore.append(each02.name)

        for each01 in datastorename:
            datastorename01 = each01['datasotrename']
            if datastorename01 not in liststore:
                DataStore.objects.filter(datasotrename=datastorename01).delete()

    hostname = VMHost.objects.values('hostname')

    def datacenternameid(foreach):
        if foreach.parent.name == "正式环境" or foreach.parent.name == "测试环境":
            datacentername = foreach.parent.name
            return datacentername
        return datacenternameid(foreach=foreach.parent)

    if len(hostname) == 0:
        for each in listhostobj:
            foreach = each
            datacentername = datacenternameid(foreach)
            if datacentername == "正式环境":
                postdata = VMHost(hostname=each.name, clustername_id='', datacentername_id=1)
                postdata.save()
            elif datacentername == "测试环境":
                postdata = VMHost(hostname=each.name, clustername_id='', datacentername_id=2)
                postdata.save()
    else:
        for each in listhostobj:
            filterhost = VMHost.objects.filter(hostname=each.name)
            if len(filterhost) == 0:
                foreach = each
                datacentername = datacenternameid(foreach)
                if datacentername == "正式环境":
                    postdata = VMHost(hostname=each.name, clustername_id='', datacentername_id=1)
                    postdata.save()
                elif datacentername == "测试环境":
                    postdata = VMHost(hostname=each.name, clustername_id='', datacentername_id=2)
                    postdata.save()

        listhost = list()
        for each02 in listhostobj:
            listhost.append(each02.name)

        for each01 in hostname:
            hostname01 = each01['hostname']
            if hostname01 not in listhost:
                VMHost.objects.filter(hostname=hostname01).delete()

    dcname = VMDatacenter.objects.values('datacentername')

    crsname = VMCluster.objects.values('datacentername')
    if len(crsname) == 0:
        for each in listcrsobj:
            postdata = VMCluster(clustername=each.name, datacentername_id='')
            postdata.save()
    else:
        for each in listcrsobj:
            filtercrs = VMCluster.objects.filter(clustername=each.name)
            if len(filtercrs) == 0:
                postdata = VMCluster(clustername=each.name, datacentername_id='')
                postdata.save()

    vm = VMVirtual.objects.values('vmname')
    if len(vm) == 0:
        for each in listvmobj:
            if each.summary.config.template is False:
                istemp = 0
                postdata = VMVirtual(vmname=each.name,
                                     istemplate=istemp,
                                     clustername_id='',
                                     datacentername_id='1',
                                     vmstatus=each.runtime.powerState)
                postdata.save()
            else:
                istemp = 1
                postdata = VMVirtual(vmname=each.name,
                                     istemplate=istemp,
                                     clustername_id='',
                                     datacentername_id='1',
                                     vmstatus=each.runtime.powerState)
                postdata.save()
    else:
        for each in listvmobj:
            filtervm = VMVirtual.objects.filter(vmname=each.name)
            if len(filtervm) == 0:
                if each.summary.config.template is False:
                    istemp = 0
                    postdata = VMVirtual(vmname=each.name,
                                         istemplate=istemp,
                                         clustername_id='',
                                         datacentername_id='1',
                                         vmstatus=each.runtime.powerState)
                    postdata.save()
                else:
                    istemp = 1
                    postdata = VMVirtual(vmname=each.name,
                                         istemplate=istemp,
                                         clustername_id='',
                                         datacentername_id='1',
                                         vmstatus=each.runtime.powerState)
                    postdata.save

        listvm = list()
        for each02 in listvmobj:
            listvm.append(each02.name)

        for each01 in vm:
            vm01 = each01['vmname']
            if vm01 not in listvm:
                VMVirtual.objects.filter(vmname=vm01).delete()

    return HttpResponse("更新成功")


def logincheck(func):
    def login(request, *args, **kwargs):
        if 'sessionid' in request.COOKIES and Session.objects.filter(session_key=request.COOKIES['sessionid']):
            return func(request, *args, **kwargs)
        else:
            return redirect('/login')
    return login


def authcheck(func):
    def login(request, *args, **kwargs):
        rightlist = Rightlist.objects.all()
        modellist = ModelList.objects.all()
        for userinfo in rightlist:
            loginuser = str(request.user)
            authdict = {"username": request.user}
            if userinfo.username == loginuser:
                for model in modellist:
                    if model.modelname == 'OA自助运维':
                        return func(request, *args, **kwargs)
            continue
        return render(request, "altervm/authcheck.html", authdict)
    return login


@logincheck
@authcheck
def index(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'index/index.html', vmdict)

def logout(request):
    return redirect('/logout')

@logincheck
def vmtemp(request):
    listobj = VMVirtual.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'index/template.html', vmdict)

@logincheck
def showhost(request):
    listobj = VMHost.objects.all()
    vmdict = {"vmlist": listobj, "username": request.user}
    return render(request, 'index/host.html', vmdict)

@logincheck
def vmdetail(request, id):
    conn.connect_to_vcenter()
    vmname = VMVirtual.objects.filter(id=id).values("vmname")
    for i in conn.get_allvms():
        if i.summary.config.name == vmname[0]["vmname"]:
            vmname01 = i.summary.config.name
            vmcpu = i.config.hardware.numCoresPerSocket
            vmmemory = i.config.hardware.memoryMB/1024
            vmguest = i.summary.config.guestFullName
            vmip = i.summary.guest.ipAddress
            vmstatus = i.guest.guestState
            vmdisk = i.config.hardware.device
            vmdisklist = list()
            for eachvmdisk in vmdisk:
                if isinstance(eachvmdisk, vim.vm.device.VirtualDisk):
                    vmdisklist.append(eachvmdisk.backing.fileName)

            vmdict = {"vmname": vmname01,
                      "vmcpu": vmcpu,
                      "vmmemory": vmmemory,
                      "vmdisk": vmdisklist,
                      "vmguest": vmguest,
                      "vmip": vmip,
                      "vmstatus": vmstatus,
                      "vmdisknum": len(vmdisklist)
                      }
            return render(request, 'index/vmdetail.html', vmdict)


@logincheck
def webconsole(request, id):
    conn.connect_to_vcenter()
    vmname = VMVirtual.objects.filter(id=id).values("vmname")
    for i in conn.get_allvms():
        if i.summary.config.name == vmname[0]["vmname"]:
            vmname = i.summary.config.name
            webconsoleurl = conn.get_acquireTicket(vmname)
            # print(webconsoleurl)
            # return redirect(webconsoleurl)
            return render(request, 'index/webconsoleapi.html', webconsoleurl)

@logincheck
def vmshudown(request, id):
    conn.connect_to_vcenter()
    content = conn.content
    vmname = VMVirtual.objects.filter(id=id).values("vmname")
    vmname = get_obj(content, [vim.VirtualMachine], vmname[0]["vmname"])
    if vmname.runtime.powerState == "poweredOn":
        vmname.PowerOff()
        powerState = vmname.runtime.powerState
    else:
        powerState = vmname.runtime.powerState
    return HttpResponse(powerState)

@logincheck
def createvm(request):
    """
    :param request:
    :return:
    """
    templatename = VMVirtual.objects.filter(istemplate=1)
    deployvm = dict()
    databasename = VMDatacenter.objects.get(id=1)
    databasename.vmhost_set.all()
    deployvm["template"] = templatename
    deployvm["datacenter"] = VMDatacenter.objects.all()
    deployvm["datastore"] = DataStore.objects.all()
    deployvm["esxihost"] = VMHost.objects.all()
    return render(request, 'altervm/createvm.html', deployvm)


@logincheck
def showdata(request):
    if request.POST:
        datacenter_name = request.POST['datacenter_name']
        datacenter = VMDatacenter.objects.get(datacentername=datacenter_name)
        hostname = datacenter.vmhost_set.all().values("hostname")
        listhostname = list()
        for i in hostname:
            listhostname.append(i["hostname"])

        return HttpResponse(json.dumps(listhostname))
    else:
        return HttpResponse("没有数据,请检查")

@logincheck
def showstore(request):
    if request.POST:
        esxi_name = request.POST['esxi_name']
        esxi = VMHost.objects.get(hostname=esxi_name)
        storename = esxi.datastore_set.all().values("datasotrename")
        liststorename = list()
        for i in storename:
            liststorename.append(i["datasotrename"])
        return HttpResponse(json.dumps(liststorename))
    else:
        return HttpResponse("没有数据,请检查")

@logincheck
def postnewvm(request):
    if request.POST:
        new_vmname = request.POST["newvmname"]
        temlpate = request.POST["tep_name"]
        datacenter = request.POST["datacenter_name"]
        esxi = request.POST["esxi_name"]
        datastore = request.POST["datastore_name"]
        conn.connect_to_vcenter()
        content = conn.content
        temlpate = get_obj(content, [vim.VirtualMachine], temlpate)
        clone_vm(content,
                 temlpate,
                 new_vmname,
                 datacenter,
                 datastore,
                 esxi)
        testint = ["30"]
        testint = json.dumps(testint)
        return HttpResponse(testint)
    else:
        testint = ["20"]
        testint = json.dumps(testint)
        return HttpResponse(testint)

@logincheck
def progressint(request):
    conn.connect_to_vcenter()
    content = conn.content
    progressint = list()
    if request.POST:
        tep_name = request.POST["tep_name"]
        datenow = request.POST["datenow"]
        datenow = datetime.datetime.strptime(datenow, "%Y-%m-%d %H:%M:%S")
        startt = datenow+datetime.timedelta(minutes=3)
        endt = datenow+datetime.timedelta(minutes=-3)
        temlpate = get_obj(content, [vim.VirtualMachine], tep_name)
        newvm_tasks = temlpate.recentTask
        if len(newvm_tasks) != 0:
            for i in newvm_tasks:
                taskstarttime = i.info.startTime+datetime.timedelta(hours=8)
                taskstarttime = taskstarttime.strftime("%Y-%m-%d %H:%M:%S")
                taskstarttime = datetime.datetime.strptime(taskstarttime, "%Y-%m-%d %H:%M:%S")
                if i.info.descriptionId == "VirtualMachine.clone" \
                        and i.info.state == "running" \
                        and i.info.entityName == tep_name \
                        and endt < taskstarttime < startt:
                    progressint.append({"prog": i.info.progress, "status": i.info.state})
                elif i.info.descriptionId == "VirtualMachine.clone" \
                        and i.info.state == "success" \
                        and i.info.entityName == tep_name \
                        and endt < taskstarttime < startt:
                    progressint.append({"prog": i.info.progress, "status": i.info.state})
            return HttpResponse(json.dumps(progressint))
        else:
            progressint = list()
            progressint.append({"prog": 50, "status": "任务错误"})
            return HttpResponse(json.dumps(progressint))
    else:
        progressint = list()
        progressint.append({"prog": 50, "status": "任务错误"})
        return HttpResponse(json.dumps(progressint))

@logincheck
def alltasks(request):
    conn.connect_to_vcenter()
    alltasks = {"alltaks": conn.get_task()}
    return render(request, "index/alltasks.html", alltasks)

@logincheck
def adminop(request):
    rightlist = Rightlist.objects.all()
    modellist = {"rightlist": rightlist, "username": request.user}
    return render(request, 'adminop/adminop.html', modellist)

@logincheck
def userlist(request):
    userlist = User.objects.all()
    modellist = {"userlist": userlist, "username": request.user}
    return render(request, 'adminop/userlist.html', modellist)

@logincheck
def modelist(request):
    modellist = ModelList.objects.all()
    modellists = {"modellist": modellist, "username": request.user}
    return render(request, 'adminop/modelist.html', modellists)

