# *-* coding:utf8 *-*
import socket
# 创建socket
tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 目的信息
dest_ip = input("\n请输入目的地址：")
dest_port = int(input("\n输入端口："))
try:
    tcp_client.connect((dest_ip, dest_port))
    send_data = input("\n输入发送数据：")
    tcp_client.send(send_data.encode('gbk'))
    recv_data = tcp_client.recv(1024)
    print("接收到的数据为:", recv_data.decode('gbk'))
    tcp_client.close()
except OverflowError:
    print("内存溢出")
except Exception as result:
    print("发现错误：%s" % result)
    pass


