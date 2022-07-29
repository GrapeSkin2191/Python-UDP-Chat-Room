# coding=utf-8

import configparser
import datetime
import json
import logging.config
import socket
import sys
import threading

stop = False

try:
    logging.config.fileConfig('udpserver.ini')
    logger = logging.getLogger('udpserver_logger')
except Exception as e:
    bf = logging.Formatter('%(asctime)s-%(levelname)s-%(message)s')

    consoleHandler = logging.StreamHandler(sys.stdout, )
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(bf)

    fileHandler = logging.FileHandler('udpserver.log', 'w+', 'utf-8')
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(bf)

    logging.root.setLevel(logging.INFO)
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    logging.root.addHandler(consoleHandler)

    logger = logging.getLogger('udpserver_logger')
    logger.setLevel(logging.INFO)
    for handler in logger.handlers:
        logger.removeHandler(handler)
    logger.addHandler(fileHandler)

    logger.warning('读取日志配置失败，已使用默认配置')
    logger.warning('错误信息：{0}'.format(e))

logger.info('服务端启动...')

logger.info('加载socket配置中')
try:
    config = configparser.ConfigParser()
    config.read('udpserver.ini', encoding='utf-8')
    HOST = config['socket']['Host']
    PORT = config.getint('socket', 'Port')
except Exception as e:
    logger.error('读取socket配置失败，请检查配置信息')
    logger.error('错误信息：{0}'.format(e))
    sys.exit(0)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((socket.gethostbyname(HOST), PORT))


def chat_thread():
    global s, logger

    data = []
    client_addresses = []
    while not stop:
        this_addr = None
        try:
            data.clear()

            # 接受来自客户端的消息
            received_msg, address = s.recvfrom(10240)

            # 如果ip地址是新的，就加入列表
            if client_addresses.count(address) == 0:
                client_addresses.append(address)

                # 打印ip地址列表
                logging.debug(client_addresses)

            decoded_msg = received_msg.decode()

            # 接收到客户端的测试消息
            if decoded_msg == 'test':
                s.sendto(received_msg, address)
            # 客户端退出
            elif decoded_msg == 'bye':
                logger.info('{0}离开了'.format(address))
                client_addresses.remove(address)
                s.sendto(received_msg, address)
            else:
                msg_dict = json.loads(decoded_msg)
                msg_dict['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                decoded_msg = json.dumps(msg_dict)
                received_msg = decoded_msg.encode()
                data.append(received_msg)
                msg = '[{0}]{1}: {2}'.format(msg_dict['time'], msg_dict['user_name'], msg_dict['msg'])
                logger.info(msg)

            # 把接收到的消息转发给客户端
            for d in data:
                for addr in client_addresses:
                    this_addr = addr
                    s.sendto(d, addr)
        except ConnectionResetError:
            if client_addresses.count(this_addr) != 0:
                client_addresses.remove(this_addr)
        except Exception as e:
            logger.warning('服务端发生错误')
            logger.warning('错误信息：{0}'.format(e))


if __name__ == '__main__':
    chat_thr = threading.Thread(target=chat_thread, name='Chat-Thread')
    chat_thr.start()

    input('随时输入回车以结束程序\n')
    logger.info('结束程序中')
    stop = True
    s.close()
