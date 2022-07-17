# coding=utf-8

import configparser
import datetime
import json
import logging.config
import random
import socket
import sys
import threading
import time

import wx

try:
    logging.config.fileConfig('udpclient.ini')
    logger = logging.getLogger('udpclient_logger')
except Exception as e:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s-%(message)s',
                        filename='udpclient.log', filemode='w+', encoding='utf-8')
    logger = logging.getLogger('udpclient_logger')

    logger.warning('读取日志配置失败，已使用默认配置')
    logger.warning('错误信息：{0}'.format(e))

logger.info('客户端启动...')

stop = False

logger.info('加载socket配置中')
config = configparser.ConfigParser()
config.read('udpclient.ini', encoding='utf-8')
try:
    HOST = config['socket']['Host']
    PORT = config.getint('socket', 'Port')
except Exception as e:
    logger.error('读取socket配置失败，请检查配置信息')
    logger.error('错误信息：{0}'.format(e))
    sys.exit(0)
server_address = (socket.gethostbyname(HOST), PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


class ReceiveThread(threading.Thread):
    def __init__(self, name, frame):
        super().__init__(name=name)
        self.frame = frame

    def run(self):
        global s, stop

        while not stop:
            try:
                # FIXME 不知道为什么报错
                data, _ = s.recvfrom(10240)
                decoded_data = data.decode()
                logger.debug('收到消息：' + decoded_data)
                if decoded_data == 'bye':
                    break
                # print('receive: ' + decoded_data)

                self.frame.update_chat(decoded_data)
            # except OSError:
            #     pass
            except Exception as e:
                logger.error('客户端发生错误')
                logger.error('错误信息：{0}'.format(e))

        s.close()
        sys.exit(0)


class SendThread(threading.Thread):
    def __init__(self, t_name, user_name, msg):
        super().__init__(name=t_name)
        self.user_name = user_name
        self.msg = msg

    def run(self):
        global s

        try:
            # input_str = input('send: ')
            msg_dict = {'user_name': self.user_name,
                        'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'msg': self.msg}
            msg_json = json.dumps(msg_dict)
            s.sendto(msg_json.encode(), server_address)
            logger.debug('发送消息：' + msg_json)

            # if input_str == 'bye':
            #     stop = True
        except Exception as e:
            logger.error('客户端发生错误')
            logger.error('错误信息：{0}'.format(e))


class ChatFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='UDP聊天室 ver1.0', size=(700, 550))
        self.Center()
        self.SetMinClientSize((300, 300))
        self.SetIcon(wx.Icon('udpclient.ico', wx.BITMAP_TYPE_ICO))

        self.Bind(wx.EVT_CLOSE, self.on_close)

        panel = wx.Panel(parent=self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.chat_tc = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.chat_tc, 7, wx.EXPAND | wx.CENTER | (wx.ALL ^ wx.BOTTOM), 10)

        sb = wx.StaticBox(panel)
        hsbox = wx.StaticBoxSizer(sb, wx.HORIZONTAL)

        self.name_tc = wx.TextCtrl(panel)
        self.name_tc.SetValue('用户{0:0>4d}'.format(random.randint(1, 9999)))
        hsbox.Add(self.name_tc, 1, wx.EXPAND | wx.CENTER | (wx.ALL ^ wx.RIGHT), 5)

        self.input_tc = wx.TextCtrl(panel)
        self.input_tc.SetFocus()
        hsbox.Add(self.input_tc, 8, wx.EXPAND | wx.CENTER | wx.ALL, 5)
        self.input_tc.Bind(wx.EVT_KEY_UP, self.on_key_up)

        self.send_btn = wx.Button(panel, label='发送')
        self.Bind(wx.EVT_BUTTON, self.on_send_btn_click, self.send_btn)
        hsbox.Add(self.send_btn, 1, wx.EXPAND | wx.CENTER | wx.ALL, 5)

        vbox.Add(hsbox, 1, wx.EXPAND | wx.CENTER | wx.ALL, 5)

        panel.SetSizer(vbox)

    def on_send_btn_click(self, event):
        user_name = self.name_tc.GetValue()
        msg = self.input_tc.GetValue()
        self.input_tc.SetValue('')
        if user_name and msg:
            SendThread('Send-Thread', user_name, msg).start()

    def on_close(self, event):
        global stop

        logger.info('结束程序中...')
        stop = True
        s.sendto(b'bye', server_address)
        # self.Close()
        self.Destroy()

    def update_chat(self, new_msg):
        msg_dict = json.loads(new_msg)
        self.chat_tc.SetValue(self.chat_tc.GetValue() +
                              '[{0}]{1}: {2}\n'.format(msg_dict['time'], msg_dict['user_name'], msg_dict['msg']))

    def fail_to_connect(self, e=None):
        logger.error('连接服务器失败')
        if e:
            logger.error('错误信息：{0}'.format(e))
        dlg = wx.MessageDialog(self, '连接服务器失败', '错误', wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        self.on_close(None)

    def on_key_up(self, event):
        if event.GetUnicodeKey() == wx.WXK_RETURN:
            self.on_send_btn_click(None)


class App(wx.App):
    def OnInit(self):
        frame = ChatFrame()

        logger.info('连接服务器中...')
        try:
            s.sendto(b'test', server_address)
            d, _ = s.recvfrom(10240)
            # print(d.decode())
            for _ in range(10):
                if d.decode() != 'test':
                    time.sleep(0.25)
                    s.sendto(b'test', server_address)
                else:
                    logger.info('连接服务器成功')
                    break
            # 失败10次
            else:
                frame.fail_to_connect()
                return True
        except Exception as e:
            frame.fail_to_connect(e)

        frame.Show()

        t_receive = ReceiveThread('Receive-Thread', frame)
        t_receive.start()

        return True


if __name__ == '__main__':
    app = App()
    app.MainLoop()
