# encoding: utf-8
import os
from ctypes import *
import psycopg2
def decrypt_pwd(passwork,pwd_rc4_value='0'*512):
    if os.path.exists('/usr/lib64/logproxy.so') == False:
        return (-1,"系统繁忙")
    lib = cdll.LoadLibrary("/usr/lib64/logproxy.so")
    pwd_rc4 = c_char_p()# 定义一个指针
    pwd_rc4.value = pwd_rc4_value.encode('ascii') # 初始化 指针
    lib.decrypt_pwd.argtypes = [c_char_p,c_char_p]; #定义函数参数
    lib.decrypt_pwd.restype = None #定义函数返回值
    ret = lib.decrypt_pwd(passwork.encode('ascii'),pwd_rc4);#执行函数
    return pwd_rc4.value.decode()

def connpsqp(dbserver):
    conn = psycopg2.connect(database='BH_CONFIG',user='paver',password='Pav5nA$',host=dbserver,port='5432')
    serverdict = dict()
    serverlist = list()
    if conn:
        #print("Connect Success")
        cur = conn.cursor()
        cur.execute('SELECT h."HostName" hname,\
                    hs."HostServiceName" hsname,\
                    hs."Port" hport,\
                    acu."AccountName" haccount,\
                    pa."Password" hpassword\
                    FROM "Host" h\
                    INNER JOIN "HostService" hs ON h."HostId" = hs."HostId"\
                    INNER JOIN "PasswordAuthService" pas ON hs."HostServiceId" = pas."HostServiceId"\
                    INNER JOIN "PasswordAuthAccount" paa on pas."PasswordAuthId" = paa."PasswordAuthId"\
                    INNER JOIN "PasswordAuth" pa on paa."PasswordAuthId" = pa."PasswordAuthId"\
                    INNER JOIN "Account" acu    on paa."AccountId" =acu."AccountId"')
        rows = cur.fetchall()
        for row in rows:
            serverdict['hname']=row[0]
            serverdict['hsname']=row[1]
            serverdict['hport']=row[2]
            serverdict['haccount']=row[3]
            serverdict['hpassword']=row[4]
            serverlist.append(serverdict.copy())
    conn.close
    return  serverlist

def decrypt():
    serverlist = connpsqp('10.64.8.209')
    for server in serverlist:
        if server['hpassword'] != '' and server['hpassword'] is not None:
            password = decrypt_pwd(server['hpassword'])
            server['hpassword'] = password
    return serverlist

print(decrypt())