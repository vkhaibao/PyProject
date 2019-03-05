# -*- coding: utf8 -*-

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import atexit
import sys
import time
import ssl
from urllib.parse import quote

class VCenter:
    def __init__(self, username, password):
        self.pyVmomi = __import__("pyVmomi")
        self.vcenter_server = '10.2.2.9'
        self.vcenter_username = username
        self.vcenter_password = password
        self.port = 443
        # self.isDHCP=False,
        # self.vm_ip='10.7.42.91',
        # self.subnet= '255.255.255.0',
        # self.gateway= '10.7.42.40',
        # self.dns= ['company.com', 'company.com'],
        # self.domain= 'esx10g.company.com'

    def add_nic(vm, network):
        spec = vim.vm.ConfigSpec()

        # add Switch here
        dev_changes = []
        switch_spec = vim.vm.device.VirtualDeviceSpec()
        switch_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        switch_spec.device = vim.vm.device.VirtualVmxnet3()

        switch_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        switch_spec.device.backing.useAutoDetect = False
        switch_spec.device.backing.deviceName = network.name
        switch_spec.device.backing.network = network
        switch_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        switch_spec.device.connectable.startConnected = True
        switch_spec.device.connectable.connected = True

        dev_changes.append(switch_spec)

        spec.deviceChange = dev_changes
        output = vm.ReconfigVM_Task(spec=spec)
        time.sleep(2)
        print(output.info)

    def connect_to_vcenter(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_NONE
        self.service_instance = SmartConnect(
            host=self.vcenter_server,
            user=self.vcenter_username,
            pwd=self.vcenter_password,
            port=self.port,
            sslContext=context)
        self.content = self.service_instance.RetrieveContent()
        # atexit.register(Disconnect, self.service_instance)

    def disconnect_vcenter(self):

        atexit.register(Disconnect, self.service_instance)

    def wait_for_task(self, task, actionName='job', hideResult=False):
        while task.info.state == (self.pyVmomi.vim.TaskInfo.State.running or self.pyVmomi.vim.TaskInfo.State.queued):
            time.sleep(2)
        if task.info.state == self.pyVmomi.vim.TaskInfo.State.success:
            if task.info.result is not None and not hideResult:
                out = '%s completed successfully, result: %s' % (actionName, task.info.result)
                print(out)
            else:
                out = '%s completed successfully.' % actionName
                print(out)
        elif task.info.state == self.pyVmomi.vim.TaskInfo.State.error:
            out = 'Error - %s did not complete successfully: %s' % (actionName, task.info.error)
            raise ValueError(out)
        return task.info.result

    def answer_vm_question(self, vm):
        choices = vm.runtime.question.choice.choiceInfo
        default_option = None
        choice = ""
        if vm.runtime.question.choice.defaultIndex is not None:
            ii = vm.runtime.question.choice.defaultIndex
            default_option = choices[ii]
            choice = None
        while choice not in [o.key for o in choices]:
            print("VM power on is paused by this question:\n\n")
            for option in choices:
                print("\t %s: %s " % (option.key, option.label))
            if default_option is not None:
                print("default (%s): %s\n" % (default_option.label, default_option.key))
            choice = raw_input("\nchoice number: ").strip()
            print("...")
        return choice

    def poweroff(self, si, vm):
        task = vm.PowerOff()
        actionName = 'job'
        while task.info.state not in [self.pyVmomi.vim.TaskInfo.State.success or self.pyVmomi.vim.TaskInfo.State.error]:
            time.sleep(2)
        if task.info.state == self.pyVmomi.vim.TaskInfo.State.success:
            out = '%s completed successfully.' % actionName
            print(out)
        elif task.info.state == self.pyVmomi.vim.TaskInfo.State.error:
            out = 'Error - %s did not complete successfully: %s' % (actionName, task.info.error)
            raise ValueError(out)
        return

    def poweron(self, si, vm):
        task = vm.PowerOn()
        actionName = 'job'
        answers = {}
        while task.info.state not in [self.pyVmomi.vim.TaskInfo.State.success or self.pyVmomi.vim.TaskInfo.State.error]:
            if vm.runtime.question is not None:
                question_id = vm.runtime.question.id
                if question_id not in answers.keys():
                    answers[question_id] = self.answer_vm_question(vm)
                    vm.AnswerVM(question_id, answers[question_id])
            time.sleep(2)
        if task.info.state == self.pyVmomi.vim.TaskInfo.State.success:
            out = '%s completed successfully.' % actionName
            print(out)
        elif task.info.state == self.pyVmomi.vim.TaskInfo.State.error:
            out = 'Error - %s did not complete successfully: %s' % (actionName, task.info.error)
            raise ValueError(out)
        return

    def set_dvs_mtu(self, dvs, mtu):
        dvs_config_spec = self.pyVmomi.vim.VmwareDistributedVirtualSwitch.ConfigSpec()
        dvs_config_spec.configVersion = dvs.config.configVersion
        dvs_config_spec.maxMtu = int(mtu)
        task = dvs.ReconfigureDvs_Task(dvs_config_spec)
        self.wait_for_task(task)
        print("Successfully reconfigured DVS %s with mtu %s" % (dvs.name, mtu))
        return dvs

    def get_dvs_portgroup(self, vimtype, portgroup_name, dvs_name):
        obj = None
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == portgroup_name:
                if c.config.distributedVirtualSwitch.name == dvs_name:
                    obj = c
                    break
        return obj

    def list_obj(self, vimtype):
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        return container.view

    def get_obj(self, vimtype, name):
        obj = None
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj

    def get_folder(self, folder_name=''):
        """获取文件夹"""
        folder_list = []
        if folder_name == '':
            listOBJ = self.list_obj([vim.Folder])
        else:
            listOBJ = self.get_obj([vim.Folder], folder_name)
        for each in listOBJ:
            folder_list.append(each)
        return folder_list

    def get_vcenters(self):
        """获取所有数据中心"""
        listOBJ = self.list_obj([vim.Datacenter])
        vcenters_list = []
        for each in listOBJ:
            vcenters_list.append(each)
        return listOBJ

    def get_vcenters_alarm(self):
        """获取所有数据中心报警"""
        listOBJ = self.list_obj([vim.Datacenter])
        vcenters_alarm_dict = {}
        for i in listOBJ[0].triggeredAlarmState:
            vcenters_alarm_dict[i.entity.name] = i.alarm.info.name.decode()
        return vcenters_alarm_dict

    def get_datastore(self, datastore_name=''):
        """获取存储"""
        datastore_list = []
        if datastore_name == '':
            listOBJ = self.list_obj([vim.Datastore])
        else:
            listOBJ = self.get_obj([vim.Datastore], datastore_name)
        for each in listOBJ:
            datastore_list.append(each.name)
        return listOBJ

    def get_clusters(self, clusters_name=''):
        """获取所有的集群"""
        clusters_list = []
        if clusters_name == '':
            listOBJ = self.list_obj([vim.ClusterComputeResource])
        else:
            listOBJ = self.get_obj([vim.ClusterComputeResource], clusters_name)
        for each in listOBJ:
            clusters_list.append(each.name)
        return listOBJ

    def get_resource_pool(self, resource_pool_name=''):
        """获取所有的资源池"""
        resource_pool_list = []
        if resource_pool_name == '':
            listOBJ = self.list_obj([vim.ResourcePool])
        else:
            listOBJ = self.get_obj([vim.ResourcePool], resource_pool_name)
        for each in listOBJ:
            resource_pool_list.append(each.name)
        return resource_pool_list

    def get_hosts(self):
        """获取所有的宿主机"""
        listOBJ = self.list_obj([vim.HostSystem])
        return listOBJ

    def get_pnic(self):
        """获取所有的上行口"""
        listOBJ = self.list_obj([vim.HostSystem])
        index = 0
        for each in listOBJ:
            tuplePNic = sys._getframe().f_code.co_name, index, each.config.network.pnic
            for eachpnic in tuplePNic[2]:
                index = index + 1
                print(sys._getframe().f_code.co_name, index, each, eachpnic.device)

    def get_vswitchs(self):
        """获取所有的交换机（包括标准交换机和分布式交换机)"""
        listOBJ = self.list_obj([vim.HostSystem])
        index = 0
        for each in listOBJ:
            tupleVswitch = sys._getframe().f_code.co_name, index, each.config.network.vswitch
            for eachsw in tupleVswitch[2]:
                index = index + 1
                print(sys._getframe().f_code.co_name, index, eachsw.name)

    def get_portgroups(self):
        """获取所有的交换机端口组（包括标准交换机和分布式交换机)"""
        listOBJ = self.list_obj([vim.Network])
        index = 0
        for each in listOBJ:
            index = index + 1
            print(sys._getframe().f_code.co_name, index, each)

    def get_vns(self):
        """获取所有的虚拟网络（包括标准交换机端口组和分布式交换机端口组)"""
        listOBJ = self.list_obj([vim.Network])
        index = 0
        for each in listOBJ:
            index = index + 1
            print(sys._getframe().f_code.co_name, index, each)

    def get_dvswitchs(self):
        """获取所有的分布式交换机"""
        listOBJ = self.list_obj([vim.DistributedVirtualSwitch])
        index = 0
        for each in listOBJ:
            index = index + 1
            print(sys._getframe().f_code.co_name, index, each)

    def get_dvportgroups(self):
        """获取所有的分布式交换机端口组"""
        listOBJ = self.list_obj([vim.DistributedVirtualSwitch])
        index = 0
        for each in listOBJ:
            for eachportgroup in each.portgroup:
                index = index + 1
                print(sys._getframe().f_code.co_name, index, eachportgroup)

    def get_vnic(self):
        """获取所有的虚拟网卡"""
        listOBJ = self.list_obj([vim.VirtualMachine])
        index = 0
        for each in listOBJ:
            index = index + 1
            vmdeviceList = each.config.hardware.device
            for eachdevice in vmdeviceList:
                index = index + 1
                if isinstance(eachdevice, vim.vm.device.VirtualEthernetCard):
                    if isinstance(eachdevice.backing,
                                  vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                        print(sys._getframe().f_code.co_name, \
                              index, \
                              eachdevice.deviceInfo.label, \
                              eachdevice.macAddress, \
                              eachdevice.deviceInfo.summary, \
                              eachdevice.backing.port.portgroupKey)
                    else:
                        print(sys._getframe().f_code.co_name, \
                              index, \
                              eachdevice.deviceInfo.label, \
                              eachdevice.macAddress, \
                              eachdevice.backing.deviceName, \
                              eachdevice.backing.network)

    def get_allvms(self):
        """获取所有的虚机"""
        listOBJ = self.list_obj([vim.VirtualMachine])
        index = 0
        vmlist = list()
        for each in listOBJ:
            index = index + 1
            # print(index, each.name, each.summary.config.template)
            vmlist.append([index, each.name, each.summary.config.template])
        return listOBJ

    def print_vm_info(self, virtual_machine, depth=1):
        """打印虚机信息"""
        maxdepth = 10
        if hasattr(virtual_machine, 'childEntity'):
            if depth > maxdepth:
                return
            vmList = virtual_machine.childEntity
            for c in vmList:
                self.print_vm_info(c, depth + 1)
            return
        summary = virtual_machine.summary
        template = summary.config.template
        if template is False:
            print("Name       : ", summary.config.name)
            print("Path       : ", summary.config.vmPathName)
            print("Guest      : ", summary.config.guestFullName)
            annotation = summary.config.annotation
            #if annotation:
                #print("Annotation : ", annotation)
            print("State      : ", summary.runtime.powerState)
            if summary.guest is not None:
                ip_address = summary.guest.ipAddress
                if ip_address:
                    print("IP         : ", ip_address)
            if summary.runtime.question is not None:
                print("Question  : ", summary.runtime.question.text)
            print("")

    def get_acquireTicket(self, virtual_machine):
        """获取主机Console授权"""
        acquireTickets_dict = {}
        listOBJ = self.get_obj([vim.VirtualMachine], virtual_machine)
        try:
            acquireTickets = listOBJ.AcquireTicket("webmks")
        except Exception as err:
            print('acquireTickets_err:', err)
        acquireTickets_dict['ticket'] = acquireTickets.ticket
        acquireTickets_dict['host'] = acquireTickets.host
        acquireTickets_dict['port'] = acquireTickets.port

        return acquireTickets_dict

    def get_hosts_exsi_version(self, virtual_machine):
        """获得主机Esxi版本"""
        try:
            hosts_name = self.get_obj([vim.VirtualMachine], virtual_machine).summary.runtime.host
            for i in self.list_obj([vim.HostSystem]):
                if i == hosts_name:
                    hosts_ip = i.name
            listOBJ = self.get_obj([vim.HostSystem], hosts_ip)
            try:
                exsi_version = listOBJ.summary.config.product.fullName
            except Exception as err:
                print(err)
                exsi_version = ''
        except Exception as err:
            print(err)
            exsi_version = ''
        return exsi_version

    def get_vm_status(self, virtual_machine, depth=1):
        for i in self.get_allvms():
            if i.config.template is False and i.summary.config.name == virtual_machine:
                vmstatus = i.guest.guestState
                print(vmstatus)

        return vmstatus

# conn = VCenter("sunhaibao@kedacom.com", "shbmyy0615..")
# conn.connect_to_vcenter()
# conn.get_vm_status("KMS")