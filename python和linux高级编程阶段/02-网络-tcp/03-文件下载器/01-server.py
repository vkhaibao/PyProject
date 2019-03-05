# *-* coding:utf8 *-*
from socket import *
import sys


def getfile(filename):
    """
    获取文件内容
    :param filename:
    """
    try:
        with open(filename, 'rb') as f:
            content = f.read()
        return content
    except:
        print("没有下载的文件 %s" % filename)
        pass
    pass


def main():
    if len(sys.argv) != 2:
        print("请按照如下方式运行：python3 xxx.py 7890")
        return
    else:
        # 运行方式为python3 xxx.py 7890
        port = int(sys.argv[1])
        pass
    # 创建socket
    tcp_srv = socket(AF_INET, SOCK_STREAM)
    local_addr = ("", port)
    tcp_srv.bind(local_addr)
    # 开启端口监听
    tcp_srv.listen(120)
    while True:
        # 等待客户端建立连接
        client_soc, client_addr = tcp_srv.accept()
        # 接收客户端数据
        recv_data = client_soc.recv(1024)
        file_name = recv_data.decode("utf-8")
        print("对方请求下载的文件名为:%s" % file_name)
        # 输出文本内容
        file_content = getfile(file_name)
        # 发送文件的数据给客户端
        if file_content:
            client_soc.send(file_content)
        # 断开客户端连接
        client_soc.close()
    # 关闭监听
    tcp_srv.close()


if __name__ == "__main__":
    main()
