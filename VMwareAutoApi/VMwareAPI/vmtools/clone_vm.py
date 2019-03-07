#coding=utf8
"""
Written by Dann Bohn
Github: https://github.com/whereismyjetpack
Email: dannbohn@gmail.com
Clone a VM from template example
"""
from pyVmomi import vim
from VMwareAPI.connvcenter import *

def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print("there was an error")
            task_done = True


def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    return obj


def clone_vm(
        content,
        template,
        vm_name,
        datacenter_name,
        datastore_name,
        esxi_name,
        vm_folder=None,
        resource_pool=None):
    """
    Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
    cluster_name, resource_pool, and power_on are all optional.
    """

    # if none git the first one
    datacenter = get_obj(content, [vim.Datacenter], datacenter_name)
    host = get_obj(content, [vim.HostSystem], esxi_name)
    power_on = True

    if vm_folder:
        destfolder = get_obj(content, [vim.Folder], vm_folder)
    else:
        destfolder = datacenter.vmFolder

    if datastore_name:
        datastore = get_obj(content, [vim.Datastore], datastore_name)
    else:
        datastore = get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one

    vmconf = vim.vm.ConfigSpec()
    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = host.parent.resourcePool
    relospec.host = host

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on

    print("cloning VM...")
    # task = \
    template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    # wait_for_task(task)


def main():
    conn.connect_to_vcenter()

    content = conn.content
    template = None
    template = get_obj(content, [vim.VirtualMachine], "Docker-CentOS")
    print(template)
    host = get_obj(content, [vim.HostSystem], "10.1.7.5")
    print(host)
    datacenter = get_obj(content, [vim.Datacenter], "测试环境")
    print(datacenter)

"""
    if template:
        clone_vm(
            content, template, args.vm_name, si,
            args.datacenter_name, args.vm_folder,
            args.datastore_name, args.cluster_name,
            args.resource_pool, args.power_on, args.datastorecluster_name)
        if args.opaque_network:
            vm = get_obj(content, [vim.VirtualMachine], args.vm_name)
            add_nic(si, vm, args.opaque_network)
    else:
        print("template not found")
"""

# start this thing
if __name__ == "__main__":
    main()