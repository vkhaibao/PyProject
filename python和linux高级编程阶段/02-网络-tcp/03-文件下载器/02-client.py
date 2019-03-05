# *-* coding:utf8 *-*
from socket import *


def main():
    # 创建socket
    tcp_client = socket(AF_INET, SOCK_STREAM)
    # 目的信息
    server_ip = input("输入服务器地址：")
    server_port = int(input("输入服务器端口："))
    # 链接服务器
    tcp_client.connect((server_ip, server_port))
    # 输入需要下载的文件名：
    file_name = input("输入需要下载的文件名")
    # 发送数据
    tcp_client.send(file_name.encode("utf-8"))
    # 接收数据，最大接收字节1KB
    recv_data = tcp_client.recv(1024)
    # print('接收到的数据为:', recv_data.decode('utf-8'))
    # 如果接收到数据再创建文件，否则不创建
    if recv_data:
        with open("接收" + file_name, "wb") as f:
            f.write(recv_data)
            print("%s 已经下载" % file_name)
    # 关闭链接
    tcp_client.close()


if __name__ == "__main__":
    main()
