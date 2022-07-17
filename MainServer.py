# coding=utf-8

import json
import socket
import threading

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', 14514))
print('Server started...')


def chat_thread():
    global s

    data = []
    client_addresses = []
    while True:
        this_addr = None
        try:
            data.clear()

            # 接受来自客户端的消息
            received_msg, address = s.recvfrom(10240)
            data.append(received_msg)

            # 如果ip地址是新的，就加入列表
            if client_addresses.count(address) == 0:
                client_addresses.append(address)

                # 打印ip地址列表
                # print(client_addresses)

            decoded_msg = received_msg.decode()
            # 接收到客户端的测试消息
            if decoded_msg == 'test':
                data.remove(received_msg)
                s.sendto(received_msg, address)
            elif decoded_msg == 'bye':
                client_addresses.remove(address)
                data.remove(received_msg)
                s.sendto(received_msg, address)

            # if received_msg:
            #     print(received_msg.decode())

            # 把接收到的消息转发给客户端
            for d in data:
                for addr in client_addresses:
                    this_addr = addr
                    s.sendto(d, addr)
        except ConnectionResetError:
            if client_addresses.count(this_addr) != 0:
                client_addresses.remove(this_addr)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    chat_thr = threading.Thread(target=chat_thread, name='Chat-Thread')
    chat_thr.start()
