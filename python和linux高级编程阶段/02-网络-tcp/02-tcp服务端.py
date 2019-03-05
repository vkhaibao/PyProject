# *-* coding:utf8 *-*
import socket
"""
socket创建一个套接字
bind绑定ip和port
listen使套接字变为可以被动链接
accept等待客户端的链接
recv/send接收发送数据
"""
tcp_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
local_addr = ("", 7789)
tcp_srv.bind(local_addr)
tcp_srv.listen(120)  # 参数为拒绝接收新的链接之前允许接受的链接数
client_socket, clientAddr = tcp_srv.accept()
print(client_socket, end="\n")
print(clientAddr)
recv_data = client_socket.recv(1024)
print('接收到的数据为:', recv_data.decode('gbk'))
client_socket.send("thank you !".encode('gbk'))
print(client_socket.close())