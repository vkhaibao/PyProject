# *-* coding:utf8 *-*
import socket


def send_msg(udp_socket):

    msg = input("\n输入需要发送的消息：")
    dest_ip = input("\n输入接收方的IP：")
    dest_port = int(input("\n输入目的端口："))
    udp_socket.sendto(msg.encode('utf-8'), (dest_ip, dest_port))


def recv_msg(udp_socket):
    """

    :param udp_socket:
    """
    recv_msg = udp_socket.recvfrom(1024)
    recv_ip = recv_msg[1]
    recv_msg = recv_msg[0].decode("utf-8")
    # 3. 显示接收到的数据
    print(">>>%s:%s" % (str(recv_ip), recv_msg))


def main():
    # 1. 创建套接字
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 2. 绑定本地信息
    udp_socket.bind(("", 7890))
    while True:
        # 3. 选择功能
        print("="*30)
        print("1:发送消息")
        print("2:接收消息")
        print("="*30)
        op_num = input("请输入要操作的功能序号:")

        # 4. 根据选择调用相应的函数
        if op_num == "1":
            send_msg(udp_socket)
        elif op_num == "2":
            recv_msg(udp_socket)
        else:
            print("输入有误，请重新输入...")


if __name__ == "__main__":
    main()

