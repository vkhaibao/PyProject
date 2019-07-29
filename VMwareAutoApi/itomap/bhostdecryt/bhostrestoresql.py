# coding=utf8
import os
import time
import datetime

#定义服务器，用户名、密码、数据库名称（多个库分行放置）和备份的路径
DB_HOST="10.64.8.209"
DB_NAME="BH_CONFIG"
DB_USER="paver"
DB_PASSWORD="Pav5nA$"
DB_BACKUP_PATH="/tmp/"

DATETIME=time.strftime('%Y%m%d-%H')
BACKFILENAME=DB_NAME + "-" + DATETIME+".sql"


#定义自动备份函数
def run_backup_restore():
    #print("/tmp/%s" % BACKFILENAME)
    if not os.path.exists("/tmp/%s" % BACKFILENAME):
        print("=====备份不存在，开始备份=====")
        try:
            while True:
                backcmd = 'pg_dump "host=%s user=%s password=%s dbname=%s" > /tmp/%s' % (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, BACKFILENAME)
                print(backcmd)
                backup = os.system(backcmd)
                if backup == 0:
                    print("===========备份成功===========")          
                    print("===========还原数据===========")
                    delschemacmd = 'psql --command "drop schema private,"public" CASCADE;" "host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=BH_CONFIG01"'
                    os.system(delschemacmd)

                    creschemacmd = 'psql --command "create schema "public" AUTHORIZATION mysql" "host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=BH_CONFIG01"'
                    os.system(creschemacmd)

                    restorecmd = 'psql "host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=BH_CONFIG01" < /tmp/%s' % BACKFILENAME
                    os.system(restorecmd)
                    print("还原成功")
                    while True:
                        killscmd = "psql --command \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=\'BH_CONFIG\' AND pid<>pg_backend_pid();\" \"host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=postgres\""
                        os.system(killscmd)

                        rename01 = "psql --command \"ALTER DATABASE \\\"BH_CONFIG\\\" RENAME TO \\\"BH_CONFIG02\\\"\" \"host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=postgres\""
                        result = os.system(rename01)
                        print(result)
                        if result == 0:
                            print("老数据库重命名成功BH_CONFIG02")
                            break
                        else:
                            continue
                    print("===============2================")
                    killscmd02 = "psql --command \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=\'BH_CONFIG01\' AND pid<>pg_backend_pid();\" \"host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=postgres\""
                    
                    rename02 = "psql --command \"ALTER DATABASE \\\"BH_CONFIG01\\\" RENAME TO \\\"BH_CONFIG\\\"\" \"host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=postgres\""
                    os.system(rename02)
                    print("新数据库重命名成功BH_CONFIG")
                     
                    rename03 = "psql --command \"ALTER DATABASE \\\"BH_CONFIG02\\\" RENAME TO \\\"BH_CONFIG01\\\"\" \"host=10.5.0.46 port=5432 user=paver password=Pav5nA$ dbname=postgres\""
                    os.system(rename03)
                    print("老数据库重命名为BH_CONFIG01")
                    
                    os.system("rm -fr /tmp/*.sql")
                    print("清理备份文件成功")
                    break
                elif backup == 256:
                    print("=====密码错误,请验证密码======")
                    break
                else:
                    print("======备份失败,重新备份=======")
                    break
        except Exception as err:
            backup = 1
            print(err)
    return backup
print(run_backup_restore())
