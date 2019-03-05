# *-* coding:utf8 *-*
from socket import *
# 1. 创建套接字
udp_socket = socket(AF_INET, SOCK_DGRAM)
local_addr = ("", 6666)
udp_socket.bind(local_addr)
# 等待接收方发送数据
recv_data = udp_socket.recvfrom(1024)
# 显示接收到数据
print(recv_data[0].decode('utf8'))
print(recv_data[1])
udp_socket.close()
