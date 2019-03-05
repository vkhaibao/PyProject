# coding=utf8
from pymysql import *

# 增删改
def insert_data(conn):
    # 创建Connection连接
    # 获得Cursor对象
    cs1 = conn.cursor()
    # 执行insert语句，并返回受影响的行数：添加一条数据
    # 增加
    count = cs1.execute('insert into goods_cates(name) values("硬盘")')
    # 打印受影响的行数
    print(count)

    count = cs1.execute('insert into goods_cates(name) values("光盘")')
    print(count)

    # # 更新
    # count = cs1.execute('update goods_cates set name="机械硬盘" where name="硬盘"')
    # # 删除
    # count = cs1.execute('delete from goods_cates where id=6')

    # 提交之前的操作，如果之前已经之执行过多次的execute，那么就都进行提交
    conn.commit()

    # 关闭Cursor对象
    cs1.close()
    # 关闭Connection对象
    conn.close()

# 查询一行数据
def select_data(conn):

    # 获得Cursor对象
    cs1 = conn.cursor()
    # 执行select语句，并返回受影响的行数：查询一条数据
    count = cs1.execute('select id,name from goods where id=4')
    # 打印受影响的行数
    print("查询到%d条数据:" % count)

    for i in range(count):
        # 获取查询的结果
        result = cs1.fetchone()
        # 打印查询的结果
        print(result)
        # 获取查询的结果

    # 关闭Cursor对象
    cs1.close()
    conn.close()

# 查询多行数据
def select_mul_data(conn):
    cs1 = conn.cursor()
    count = cs1.execute('select id,name from goods where id>=4')
    print("查询到%d条数据" % count)
    for i in range(count):
        result = cs1.fetchone()
        print(result)
    cs1.close()
    conn.close()

# 参数化：
def select_parms(conn, find_name):
    cs1 = conn.cursor()
    # # 非安全的方式
    # # 输入 " or 1=1 or "   (双引号也要输入)
    # sql = 'select * from goods where name="%s"' % find_name
    # print("""sql===>%s<====""" % sql)
    # # 执行select语句，并返回受影响的行数：查询所有数据
    # count = cs1.execute(sql)

    # 安全的方式
    # 构造参数列表
    params = [find_name]
    # 执行select语句，并返回受影响的行数：查询所有数据
    count = cs1.execute('select * from goods where name=%s', params)
    # 注意：
    # 如果要是有多个参数，需要进行参数化
    # 那么params = [数值1, 数值2....]，此时sql语句中有多个%s即可
    print(count)
    result = cs1.fetchall()
    # 打印查询的结果
    print(result)
    # 关闭Cursor对象
    cs1.close()
    # 关闭Connection对象
    conn.close()


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

select_data(main())
select_mul_data(main())
select_parms(main(), ["x240 超极本"])