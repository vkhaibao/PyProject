#!/usr/bin/env python
# Copyright (c) 2015 Christian Gerbrandt <derchris@derchris.eu>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python port of William Lam's generateHTML5VMConsole.pl
Also ported SHA fingerprint fetching to Python OpenSSL library
"""

import OpenSSL
import ssl
from VMwareAPI.connvcenter import *
from pyVmomi import vim
import time
ssl._create_default_https_context = ssl._create_unverified_context

def get_vm(content, name):
    try:
        name = name
    except TypeError:
        pass

    vm = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True)

    for c in container.view:
        if c.name == name:
            vm = c
            break
    return vm


def getconsoleurl(name):
    """
    Simple command-line program to generate a URL
    to open HTML5 Console in Web browser
    """

    conn.connect_to_vcenter()

    content = conn.content
    vm = get_vm(content, name)
    vm_moid = vm._moId

    vcenter_data = content.setting
    vcenter_settings = vcenter_data.setting
    console_port = '9443'

    for item in vcenter_settings:
        key = getattr(item, 'key')
        if key == 'VirtualCenter.FQDN':
            vcenter_fqdn = getattr(item, 'value')

    session_manager = content.sessionManager
    session = session_manager.AcquireCloneTicket()

    vc_cert = ssl.get_server_certificate(("10.2.2.9", int(9443)))
    vc_pem = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, vc_cert)
    vc_fingerprint = vc_pem.digest('sha1')

    # print("Open the following URL in your browser to access the " "Remote Console.\n"
    #      "You have 60 seconds to open the URL, or the session"
    #      "will be terminated.")
    acquireTickets_dict = dict()
    acquireTickets_dict["vmid"] = str(vm_moid)
    acquireTickets_dict["vmname"] = name
    acquireTickets_dict["host"] = vcenter_fqdn
    acquireTickets_dict["session"] = session
    acquireTickets_dict["fingerprint"] = vc_fingerprint.decode("utf8")
    webconsoleurl = "https://10.2.2.9:9443" + "/vsphere-client/webconsole.html?vmId=" \
                    + str(vm_moid) + "&vmName=" + name + "&serverGuid=047b5cf4-787d-4828-a118-eeff1f5169e0&locale=zh_CN&" + "&host=" + vcenter_fqdn\
                    + "&sessionTicket=" + session + "&thumbprint=" + vc_fingerprint.decode("utf8")
    # print("Waiting for 60 seconds, then exit")
    return acquireTickets_dict

