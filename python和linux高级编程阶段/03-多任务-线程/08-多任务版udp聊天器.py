import socket
import threading


def send_msg(udp_socket, dest_ip, dest_port):
    while True:
        send_data = input("请输入发送内容：")
        udp_socket.sendto(send_data.encode('gbk'), (dest_ip, dest_port))


def recv_msg(udp_socket):
    while True:
        recv_msg = udp_socket.recvfrom(1024)
        recv_ip = recv_msg[1]
        recv_msg = recv_msg[0].decode("gbk")
        print(">>>%s:%s" % (str(recv_ip), recv_msg),end="\n")


def main():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("", 7789))
    t = threading.Thread(target=recv_msg, args=(udp_socket,))
    t.start()
    #
    dest_ip = input("请输入IP地址：")
    dest_port = int(input("请输入端口："))
    send_msg(udp_socket, dest_ip, dest_port)


if __name__ == "__main__":
    main()
