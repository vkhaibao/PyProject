# coding=utf8
from pymysql import *

def insert_mul_data(conn):
    cursor = conn.cursor()
    # 插入10万次数据
    for i in range(100000):
        cursor.execute("insert into test_index values('ha-%d')" % i)
    # 提交数据
    conn.commit()

def main():
    try:
        conn = connect(host='10.2.2.6', port=3306, user='root', password='123456', database='jing_dong', charset='utf8')
        if conn:
            return conn
            print("数据库连接成功 %s" % conn.server_status)
    except Exception as ret:
        print("连接失败，原因为%s" % ret)


if __name__ == '__main__':
    main()
