#coding=utf8

"""
 4 @Author: wjx
 5 @Description: AD域
 6 @Date: 2018-12-23 21:23:57
 7 @LastEditTime: 2019-03-28 23:46:56
"""
from ldap3 import Server, Connection, ALL, NTLM
from kdldapapi.ldaptool.definds import *

class Adoper:
    """
    AD域操作
    """
    def __init__(self, domain, ip, ucenter, user, password):
        """
        :param domain:域名,格式为xxx.xxx.xxx
        :param ip:服务器地址,格式为域名xxx.xxx.xxx
        :param user:管理账户
        :param password:密码
        :param basedn:
        """
        self.domain = domain
        self.ip = ip
        self.ucenter = ucenter
        self.user = user
        self.password = password
        self.server = Server(self.ip, get_info=ALL)
        self.conn = Connection(self.server,
                               user=self.domain+'\\'+self.user,
                               password=self.password,
                               auto_bind=True,
                               authentication=NTLM)

    def searchuser(self, orgunit):
        """
        :param orgunit: 组织单元名,格式为aaa.bbb 即bbb组织下的aaa组织，不包含域地址
        :return:
        """
        att_list = ['displayName', 'userPrincipalName', 'userAccountControl', 'sAMAccountName', 'pwdLastSet', 'department']
        org_base = ','.join(['OU=' + ou for ou in orgunit.split('/')][::-1]) + ',' + self.ucenter
        res = self.conn.search(search_base=org_base,
                               search_scope=1,
                               search_filter='(objectclass=user)',  # 查询数据的类型
                               attributes=att_list)  # 查询数据的哪些属性
        if res:
            for user in self.conn.entries:
                yield user['userPrincipalName'], user['displayName'], user['sAMAccountName']
        else:
            # print('查询失败: ', self.conn.result['description'])
            return None

    def searchgroup(self, orgunit):
        """
        :param orgunit: 组织单元名,格式为aaa.bbb 即bbb组织下的aaa组织，不包含域地址
        :return:
        """
        att_list = ['cn', 'name', 'sAMAccountName', 'canonicalName']
        org_base = ','.join(['OU=' + ou for ou in orgunit.split('/')][::-1]) + ',' + self.ucenter
        res = self.conn.search(search_base=org_base,
                               search_scope=1,
                               search_filter='(objectclass=group)',  # 查询数据的类型
                               attributes=att_list)  # 查询数据的哪些属性
        if res:
            for group in self.conn.entries:
                groupname = group['name']
                groupou = group['canonicalName']
                yield groupname, str(groupou).replace('kedacom.com/UCenter', '')
        else:
            # print('查询失败: ', self.conn.result['description'])
            return None

    def searchou(self, orgunit):
        """
        :param orgunit: 组织单元名,格式为aaa.bbb 即bbb组织下的aaa组织，不包含域地址
        :return:
        """
        att_list = ['canonicalName', 'name', 'ou']
        org_base = ','.join(['OU=' + ou for ou in orgunit.split('/')][::-1]) + ',' + self.ucenter
        res = self.conn.search(search_base=org_base,
                               search_scope=1,
                               search_filter='(objectclass=organizationalUnit)',  # 查询数据的类型
                               attributes=att_list)  # 查询数据的哪些属性
        if res:
            for ou in self.conn.entries:
                ounamelong = ou['canonicalName']
                oushort = ou['name']
                yield str(ounamelong).replace('kedacom.com/UCenter/', '')
        else:
            # print('查询失败: ', self.conn.result['description'])
            return None


if __name__ == '__main__':
    cmo = Adoper(DOMAIN, SERVER, UCENTERDC, USER, PASSWORD)
    deptment = list()
    for ou in cmo.searchou('科达科技'):
        deptment.append(ou)
    for i in deptment:
        print(i)
        for j in cmo.searchou(i):
            print(j)