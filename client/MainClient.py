# coding=utf-8

import configparser
import json
import logging.config
import random
import socket
import sys
import threading

import wx

stop = False
chat = []

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

logger.info('加载配置中')
try:
    config = configparser.ConfigParser()
    config.read('udpclient.ini', encoding='utf-8')

    HOST = config['socket']['host']
    PORT = config.getint('socket', 'port')

    font_name = config['font']['name']
    font_size = config.getint('font', 'size')
except Exception as e:
    logger.error('读取配置失败，请检查配置信息')
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
                data, _ = s.recvfrom(10240)
                decoded_data = data.decode()
                logger.debug('收到消息：' + decoded_data)
                if decoded_data == 'bye':
                    break

                self.frame.update_chat(decoded_data)
            except Exception as e:
                logger.warning('客户端发生错误')
                logger.warning('错误信息：{0}'.format(e))

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
            msg_dict = {'user_name': self.user_name,
                        'time': '', 'msg': self.msg}
            msg_json = json.dumps(msg_dict)
            s.sendto(msg_json.encode(), server_address)
            logger.debug('发送消息：' + msg_json)
        except Exception as e:
            logger.warning('客户端发生错误')
            logger.warning('错误信息：{0}'.format(e))


class ChatFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='UDP聊天室 ver1.0', size=(1000, 700))
        self.Center()
        self.SetMinClientSize((300, 300))
        self.SetFont(wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                             faceName=font_name))
        self.SetIcon(wx.Icon('udpclient.ico', wx.BITMAP_TYPE_ICO))

        self.Bind(wx.EVT_CLOSE, self.on_close)

        panel = wx.Panel(parent=self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 聊天显示框
        self.chat_tc = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.chat_tc, 6, wx.EXPAND | wx.CENTER | (wx.ALL ^ wx.BOTTOM), 10)

        # 下面的边框
        sb = wx.StaticBox(panel)
        hsbox = wx.StaticBoxSizer(sb, wx.HORIZONTAL)

        # 昵称输入框
        self.name_tc = wx.TextCtrl(panel)
        self.name_tc.SetValue('用户{0:0>4d}'.format(random.randint(1, 9999)))
        hsbox.Add(self.name_tc, 1, wx.EXPAND | wx.CENTER | (wx.ALL ^ wx.RIGHT), 5)

        # 消息输入框
        self.input_tc = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.input_tc.SetFocus()
        hsbox.Add(self.input_tc, 8, wx.EXPAND | wx.CENTER | wx.ALL, 5)
        self.input_tc.Bind(wx.EVT_KEY_UP, self.on_key_up)

        # 发送按钮
        self.send_btn = wx.Button(panel, label='发送')
        self.Bind(wx.EVT_BUTTON, self.on_send_btn_click, self.send_btn)
        hsbox.Add(self.send_btn, 1, wx.EXPAND | wx.CENTER | wx.ALL, 5)

        vbox.Add(hsbox, 1, wx.EXPAND | wx.CENTER | wx.ALL, 5)

        panel.SetSizer(vbox)

    def on_send_btn_click(self, event):
        user_name = self.name_tc.GetValue()
        msg = self.input_tc.GetValue()
        # 恢复消息输入框
        self.input_tc.SetValue('')
        self.input_tc.SetFocus()
        if user_name and msg:
            SendThread('Send-Thread', user_name, msg).start()

    def on_close(self, event):
        global stop

        if self.chat_tc.GetValue():
            logger.info('保存聊天中...')
            with open('chat_client.txt', 'a+', encoding='utf-8') as f:
                f.write(self.chat_tc.GetValue())

        logger.info('结束程序中...')
        s.sendto(b'bye', server_address)
        stop = True
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
        # 判断是否发送消息
        if (not wx.GetKeyState(wx.WXK_CONTROL)) and event.GetUnicodeKey() == wx.WXK_RETURN:
            # 去除最后一行多余的换行
            if self.input_tc.GetValue().endswith('\n'):
                self.input_tc.SetValue(self.input_tc.GetValue()[:-1])
            self.on_send_btn_click(None)


class App(wx.App):
    def OnInit(self):
        frame = ChatFrame()

        logger.info('连接服务器中...')
        try:
            s.sendto(b'test', server_address)
            s.settimeout(5)
            d, _ = s.recvfrom(10240)
            # print(d.decode())
            if d.decode() == 'test':
                logger.info('连接服务器成功')
                s.settimeout(None)
            else:
                frame.fail_to_connect()
                return True
        except Exception as e:
            frame.fail_to_connect(e)
            return True

        frame.Show()

        t_receive = ReceiveThread('Receive-Thread', frame)
        t_receive.start()

        return True


if __name__ == '__main__':
    app = App()
    app.MainLoop()
