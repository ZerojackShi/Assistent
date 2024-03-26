from token import STAR
from PyQt5.QtGui import QResizeEvent, QTextCharFormat,QColor,QTextCursor
from PyQt5.QtCore import Qt,pyqtSignal,QSize,QObject,QEvent
# coding:utf-8
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout,QButtonGroup,QLabel,QSplitter
from qfluentwidgets import ComboBox, isDarkTheme, FluentIcon,InfoBarIcon,PlainTextEdit,TransparentToolButton,InfoBarPosition,RadioButton,TextEdit
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (Pivot, qrouter, PrimaryPushButton, TabBar, CheckBox, ComboBox,
                            TabCloseButtonDisplayMode, BodyLabel, SpinBox, BreadcrumbBar)
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
from ..common.config import cfg, HELP_URL, REPO_URL, EXAMPLE_URL, FEEDBACK_URL,log_config
from ..common.style_sheet import StyleSheet
from ..plugins import frame_csg,protocol
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.signal_bus import signalBus
from ..common.commodule import commmbus
from ..components.custom_infoBay import CustomInfoBar
from ..plugins.signalCommunication import SEND_ERR
import datetime,re, binascii,socket
from ..common.trie import format_hex_string
from ..common.commodule import CommType
from ..plugins.frame_csg import is_csg_frame,get_dir_prm,send_ack_frame,get_csg_adress
from ..plugins.frame_fun import FrameFun as frame_fun
from ..plugins.signalCommunication import SerialPortThread,MQTTClientThread,TcpClient,ClientWorker,MqttMessageDetails
import os, json, ast
from PyQt5.QtNetwork import QTcpSocket
from typing import Type
import paho.mqtt.client as mqtt
DIR_UP = 1
DIR_DOWN = 2
DIR_UNKNOW = 3

class SendReceive(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="收发页面",
            parent=parent
        )
        self.setObjectName('SendandReceive')
        self.send_type = 'HEX'
        self.tcpClientSocket = []
        self.vBoxLayout = QVBoxLayout(self)
        self.sendandreceive = PlainTextEdit()
    
        self.hBoxLayout = QHBoxLayout()
        self.customSend = PlainTextEdit()
        self.sendButton = TransparentToolButton(FluentIcon.SEND)

        self.leftlayout = QVBoxLayout()
        self.radioWidget = QWidget()
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.radioLayout.setContentsMargins(2, 0, 0, 0)
        self.radioLayout.setSpacing(15)
        self.radioButton1 = RadioButton(self.tr('HEX'), self.radioWidget)
        self.radioButton2 = RadioButton(self.tr('ASCII'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self.radioWidget)
        self.buttonGroup.addButton(self.radioButton1)
        self.buttonGroup.addButton(self.radioButton2)
        self.radioLayout.addWidget(self.radioButton1)
        self.radioLayout.addWidget(self.radioButton2)
        self.radioButton1.click()

        self.clientlayout = QHBoxLayout()
        self.socketLabel = QLabel("客户端:")
        self.tcpClientSocketCombox = ComboBox()
        self.clientlayout.addWidget(self.socketLabel)
        self.clientlayout.addWidget(self.tcpClientSocketCombox)

        self.leftlayout.addWidget(self.radioWidget)
        self.leftlayout.setSpacing(5)
        #self.leftlayout.addLayout(self.clientlayout)
        self.leftlayout.addWidget(self.sendButton)


        self.hBoxLayout.addWidget(self.customSend, 1)
        self.hBoxLayout.addLayout(self.leftlayout)

        self.vBoxLayout.addWidget(self.sendandreceive, 6)
        self.vBoxLayout.addLayout(self.hBoxLayout)  # 这里添加下面部分的布局

        self.setLayout(self.vBoxLayout)
        self.sendButton.clicked.connect(self.send_text)
        self.buttonGroup.buttonClicked.connect(self.send_type_change)
        StyleSheet.HOME_INTERFACE.apply(self)
        # signalBus.messagereceive.connect(self.display_receive_message)
        signalBus.tcpSocketChange.connect(self.init_widget)
        signalBus.sendmessage.connect(self.send_custom_frame)
        self.init_widget()
    
    def init_widget(self, tcpSocket=None):
        if commmbus.connecttype == CommType.TCP_SERVICE:
            if self.clientlayout:
                self.clientlayout.setParent(None)  # 移除现有布局
            self.leftlayout.addWidget(self.radioWidget)
            self.leftlayout.setSpacing(5)
            self.leftlayout.addLayout(self.clientlayout)
            self.leftlayout.addWidget(self.sendButton)
            self.tcpClientSocketCombox.clear()
            if len(tcpSocket):
                self.tcpClientSocketCombox.addItem("所有客户端")
                for insocket in tcpSocket:
                    if isinstance(insocket, socket.socket):
                        try:
                            client_address = insocket.getpeername()
                            client_ip, client_port = client_address
                            text = f"{client_ip}:{client_port}"
                            self.tcpClientSocketCombox.addItem(text)
                        except OSError as e:
                            continue

        else:
            if self.clientlayout:
                self.clientlayout.setParent(None)
            self.leftlayout.addWidget(self.radioWidget)
            self.leftlayout.setSpacing(5)
            self.leftlayout.addWidget(self.sendButton)

    def get_tcp_server_send_client(self):
        if self.tcpClientSocketCombox.currentIndex() == 0:
            return commmbus.tcpSocket
        else:
            currenttext = self.tcpClientSocketCombox.currentText()
            for socket in commmbus.tcpSocket:
                client_address = socket.getpeername()
                client_ip, client_port = client_address
                text = f"{client_ip}:{client_port}"
                if currenttext == text:
                    return socket
                
    def send_type_change(self, button):
        if button == self.radioButton1:
            self.send_type = 'HEX'
            # 在这里处理HEX按钮被点击的操作
        elif button == self.radioButton2:
            self.send_type = 'ASCII'
            
        if commmbus.link_port:
            commmbus.link_port.set_message_send_type(self.send_type)

    def send_text(self):
        text = self.customSend.toPlainText()
        self.send_custom_frame(text)
    def send_custom_frame(self, text):
        try:
            if text != '':
                err_str = ''
                if commmbus.link_port and commmbus.link_status:
                    if commmbus.connecttype == CommType.TCP_SERVICE:
                        sockets = self.get_tcp_server_send_client()
                    else:
                        sockets = commmbus.channel
                    commmbus.link_port.set_message_send_type(self.send_type)
                    send_result = commmbus.link_port.send_messages(text, sockets)

                if commmbus.link_port is None or commmbus.link_status == False:
                    err_str = '请检查是否连接！'
                else:
                    if send_result == SEND_ERR.ERR_LINK:
                        err_str = '请检查是否连接！'
                    elif send_result == SEND_ERR.ERR_TYPE:
                        err_str = '发送区类型错误！'
                    elif send_result == SEND_ERR.ERR_SEND:
                        err_str = '发送失败！'
                    elif send_result == SEND_ERR.SUCCESS:
                        last_position = self.sendandreceive.verticalScrollBar().value() + self.sendandreceive.viewport().height()
                        current_time = datetime.datetime.now()
                        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        sent_message_format = QTextCharFormat()
                        sent_message_format.setForeground(QColor("green"))
                        cursor = self.sendandreceive.textCursor()
                        cursor.movePosition(QTextCursor.End)
                        cursor.setCharFormat(sent_message_format)
                        if self.send_type == 'HEX':
                            text = format_hex_string(text)

                        if sockets:
                            if commmbus.connecttype != CommType.SERIAL:
                                if isinstance(sockets, list):
                                    link = "AllTcpSession"
                                else:
                                    client_address = sockets.getpeername()
                                    client_ip, client_port = client_address
                                    link = f"{client_ip}:{client_port}"
                            else:
                                link = sockets
                        if self.sendandreceive.toPlainText() == '':
                            cursor.insertText(f'[{current_time_str}]' + f"[{link}]" + "  发送  " + text)
                        else:
                            cursor.insertText('\n' + f'[{current_time_str}]' + f"[{link}]" + "  发送  " + text)
                        self.sendandreceive.verticalScrollBar().setValue(last_position)

                if err_str != '':
                    infoBar = CustomInfoBar(
                    icon=InfoBarIcon.ERROR,
                    title=self.tr('失败'),
                    content=err_str,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    duration=-1,
                    position=InfoBarPosition.TOP,
                    parent=self
                    )
                    infoBar.show()
        except Exception as e:
            # 处理特定异常（如果需要）
            log_config.log_error(f"捕获到一个异常: {e}", exc_info=True)

    def display_receive_message(self, text, socket):
        try:
            frame = self.get_hex_frame(text)
            if frame:
                if cfg.get(cfg.Multireport) == True:
                    adresslist = cfg.get(cfg.MultireportAdress)
                    adress = get_csg_adress(frame)
                    if adress not in adresslist:
                        self.report_replay(text, socket)
                        print("接收地址{}不在列表中".format(adress))
                        return
            last_position = self.sendandreceive.verticalScrollBar().value() + self.sendandreceive.viewport().height()
            current_time = datetime.datetime.now()
            current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            sent_message_format = QTextCharFormat()
            sent_message_format.setForeground(QColor("red"))
            cursor = self.sendandreceive.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.setCharFormat(sent_message_format)
            if commmbus.connecttype == CommType.TCP_SERVICE:
                if socket is None:
                    link = "AllTcpSession"
                else:
                    client_address = socket.getpeername()
                    client_ip, client_port = client_address
                    link = f"{client_ip}:{client_port}"
            elif commmbus.connecttype == CommType.TCP_CLIENT:
                client_address = socket.getpeername()
                client_ip, client_port = client_address
                link = f"{client_ip}:{client_port}"
            else:
                link = socket
            if self.sendandreceive.toPlainText() == '':
                cursor.insertText(f'[{current_time_str}]' + f"[{link}]" +"  接收  " + text)
            else:
                cursor.insertText('\n' + f'[{current_time_str}]' + f'[{link}]' + "  接收  " + text)
            self.sendandreceive.verticalScrollBar().setValue(last_position)
            self.tcpClientSocket.append(socket)

            self.report_replay(text, socket)
        except Exception as e:
            # 处理特定异常（如果需要）
            log_config.log_error(f"捕获到一个异常: {e}", exc_info=True)
    def get_hex_frame(self, text):
        try:
            hex_str = text.replace(' ', '')
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
            return frame
        except ValueError:
            return None
            
    def report_replay(self, text, sockets):
        try:
            frame = self.get_hex_frame(text)
            if frame:
                if is_csg_frame(frame):
                    control_data = frame[6]
                    dir, prm,acd,fcv  = get_dir_prm(control_data)
                    if dir and prm:
                        control_code = control_data & 0x0f
                        if control_code != 9 and cfg.get(cfg.ReportReplay) == False:
                            return
                        replay_frame = send_ack_frame(frame, control_code)
                        raplay = get_data_str_with_space(replay_frame)
                        commmbus.link_port.send_messages(raplay, sockets)
                        
                        if cfg.get(cfg.Multireport) == True:
                            adresslist = cfg.get(cfg.MultireportAdress)
                            adress = get_csg_adress(frame)
                            if adress not in adresslist:
                                print("发送地址{}不在列表中".format(adress))
                                return
                        last_position = self.sendandreceive.verticalScrollBar().value() + self.sendandreceive.viewport().height()
                        current_time = datetime.datetime.now()
                        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        sent_message_format = QTextCharFormat()
                        sent_message_format.setForeground(QColor("green"))
                        cursor = self.sendandreceive.textCursor()
                        cursor.movePosition(QTextCursor.End)
                        cursor.setCharFormat(sent_message_format)
                        if self.send_type == 'HEX':
                            text = format_hex_string(text)

                        if sockets:
                            if commmbus.connecttype == CommType.TCP_SERVICE:
                                if isinstance(sockets, list):
                                    link = "AllTcpSession"
                                else:
                                    client_address = sockets.getpeername()
                                    client_ip, client_port = client_address
                                    link = f"{client_ip}:{client_port}"
                            else:
                                link = sockets
                        if self.sendandreceive.toPlainText() == '':
                            cursor.insertText(f'[{current_time_str}]' + f"[{link}]" + "  发送  " + raplay)
                        else:
                            cursor.insertText('\n' + f'[{current_time_str}]' + f"[{link}]" + "  发送  " + raplay)
                        self.sendandreceive.verticalScrollBar().setValue(last_position)
        except Exception as e:
            # 处理特定异常（如果需要）
            log_config.log_error(f"捕获到一个异常: {e}", exc_info=True)

class BaseSendRecive(QWidget):
    """ Base send and receive interface """
    def __init__(self, title, message_type, parent=None):
        super().__init__(parent=parent)
        self.title = title
        self.message_type = message_type
        self.sendandreceive = TextEdit(self)
        self.sendandreceive.setReadOnly(True)
        self.sendandreceive.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.qvlayout = QVBoxLayout(self)
        self.qvlayout.addWidget(self.sendandreceive)
        self.qvlayout.setContentsMargins(0, 0, 0, 0)
    
    def set_title(self, title):
        self.title = title
    def set_last_message(self, message):
        self.sendandreceive.setHtml(message)
    def set_message_type(self, message_type):
        self.message_type = message_type
    def set_info_to_log(self, message):
        self.add_message(DIR_UNKNOW, message, "INFO")
    def add_message(self, diraction, message, custom=None):
        if diraction == DIR_DOWN:
            bkg = QColor("green")
            dir_name = "发送"
        elif diraction == DIR_UP:
            bkg = QColor("red")
            dir_name = "接收"
        else:
            bkg = QColor("blue")
            dir_name = custom

        last_position = self.sendandreceive.verticalScrollBar().value() + self.sendandreceive.viewport().height()
        current_time = datetime.datetime.now()
        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]
        sent_message_format = QTextCharFormat()
        sent_message_format.setForeground(bkg)
        
        cursor = self.sendandreceive.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.setCharFormat(sent_message_format)

        if not self.sendandreceive.toPlainText().endswith('\n'):
            cursor.insertText('\n')

        cursor.insertText(f'[{current_time_str}]' + f'[{self.title}]' + f' {dir_name} ' + message)
        
        self.sendandreceive.verticalScrollBar().setValue(last_position)
        title_without_colon = self.title.replace(":", "_")
        file_name = f"{title_without_colon}.log"
        self.write_log(diraction, message, file_name, custom)


    
    def write_log(self, diraction, message, file_name, custom=""):

        path = cfg.get(cfg.logFolder)
        flodername = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3]

        file_path = os.path.join(path, flodername, file_name)
        link_type = self.title
          # 判断日志目录是否存在,不存在创建
        if not os.path.exists(os.path.dirname(file_path)): 
            os.makedirs(os.path.dirname(file_path))
        
        if diraction == DIR_DOWN:
            dir_name = ">>> 发送:"
        elif diraction == DIR_UP:
            dir_name = "<<< 接收:"
        else:
            dir_name = custom

        try:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(f"{current_time} [{link_type}] {dir_name} {message}\n")
        except FileNotFoundError:
            # 如果文件不存在，创建新文件并以二进制方式写入内容
            with open(file_path, 'w') as file:
                file.write(f"{current_time} [{link_type}] {dir_name} {message}\n")
    
    def get_last_text(self):
        cursor = self.sendandreceive.textCursor()
        cursor.select(QTextCursor.Document)
        selected_text = cursor.selection().toHtml()
        return selected_text

class BaseSend(QWidget):
    type_changed = pyqtSignal(str)
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.send_type = "HEX"
        self.qhlayout = QHBoxLayout(self)
        self.customSend = PlainTextEdit(self)
        self.customSend.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.leftlayout = QVBoxLayout()
        self.radioWidget = QWidget()
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.radioLayout.setContentsMargins(2, 0, 0, 0)
        self.radioLayout.setSpacing(15)
        self.radioButton1 = RadioButton(self.tr('HEX'), self.radioWidget)
        self.radioButton2 = RadioButton(self.tr('ASCII'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self.radioWidget)
        self.buttonGroup.addButton(self.radioButton1)
        self.buttonGroup.addButton(self.radioButton2)
        self.radioLayout.addWidget(self.radioButton1)
        self.radioLayout.addWidget(self.radioButton2)
        self.radioButton1.click()

        self.sendButton = TransparentToolButton(FluentIcon.SEND)
        self.leftlayout.addWidget(self.radioWidget)
        self.leftlayout.setSpacing(5)
        self.leftlayout.addWidget(self.sendButton)

        self.qhlayout.addWidget(self.customSend)
        self.qhlayout.addSpacing(10)
        self.qhlayout.addLayout(self.leftlayout)
        self.qhlayout.setContentsMargins(0, 0, 0, 0)
        self.buttonGroup.buttonClicked.connect(self.send_type_change)
    def send_type_change(self, button):
        if button == self.radioButton1:
            self.send_type = 'HEX'
            # 在这里处理HEX按钮被点击的操作
        elif button == self.radioButton2:
            self.send_type = 'ASCII'
        self.type_changed.emit(self.send_type)
    
    def get_type(self):
        return self.send_type
    
    def get_last_send_text(self):
        return self.customSend.toPlainText()
    
    def set_last_send_text(self, text):
        self.customSend.setPlainText(text)

class BaseSendReceive(QWidget):  # Replace QWidget with the actual base class if different
    def __init__(self, parent=None):
        super().__init__(parent=parent)

class NormalSendReceive(BaseSendReceive):
    def __init__(self, title, chennel, parent=None):
        super().__init__(parent=parent)
        self.title = title
        self.chennel = chennel
        # self.setFixedSize(self.parent().size())
        self.basesend = BaseSend(self)
        self.message_type = self.basesend.get_type()
        self.sendandreceive = BaseSendRecive(self.title, self.message_type, self)
        self.qvlayout = QVBoxLayout(self)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sendandreceive.setSizePolicy(size_policy)
        self.basesend.setSizePolicy(size_policy)
        self.qvlayout.addWidget(self.sendandreceive, 7)
        self.qvlayout.addSpacing(10)
        self.qvlayout.addWidget(self.basesend, 3)
        self.qvlayout.setContentsMargins(0, 0, 0, 0)
        self.qvlayout.setStretch(0, 7)  # sendandreceive
        self.qvlayout.setStretch(1, 3)  # basesend
        self.slot_init()

    def slot_init(self):
        self.basesend.sendButton.clicked.connect(self.send_message)
        self.basesend.type_changed.connect(self.set_message_type)
        if isinstance(self.chennel, SerialPortThread):
            self.chennel.data_received.connect(self.receive_message_process)
        if isinstance(self.chennel, TcpClient):
            self.chennel.data_received.connect(self.receive_message_process)
        if isinstance(self.chennel, ClientWorker):
            self.chennel.receive_data.connect(self.client_receive_message_process)
    def set_title(self, title):
        self.title = title
        self.sendandreceive.set_title(self.title)
    
    def set_last_message(self, message):
        self.sendandreceive.set_last_message(message)
    def set_message_type(self, message_type):
        self.sendandreceive.set_message_type(message_type)
        self.message_type = message_type

    def set_last_send_text(self, message):
        self.basesend.set_last_send_text(message)
    def get_last_send_text(self):
        return self.basesend.get_last_send_text()
    
    def get_last_log_text(self):
        return self.sendandreceive.get_last_text()
    
    def set_info_to_log(self, text):
        self.sendandreceive.set_info_to_log(text)
    def is_valid_hex_string(self, input_string):
        try:
            bytes.fromhex(input_string)
            return True
        except ValueError:
            return False
    def get_modify_text(self, input_text:str):
        if self.message_type == 'ASCII':
            return input_text
        formatted_frame = ''
        hex_str = input_text.replace(' ', '').replace('\n', '')
        for i in range(0, len(hex_str), 2):
            formatted_frame += hex_str[i:i + 2] + ' '
        return formatted_frame.upper()
    def get_message_by_type(self):
        try:
            text = self.basesend.customSend.toPlainText()
            formatted_frame = self.get_modify_text(text)
            if self.message_type == 'HEX':
                if self.is_valid_hex_string(text):
                    send_data = bytes.fromhex(text)
                    return send_data,formatted_frame
            elif self.message_type == 'ASCII':
                if isinstance(text, bytes):
                    send_data = text,text
                elif isinstance(text, str):
                    hex_message = binascii.hexlify(text.encode('ascii')).decode('ascii')
                    if self.is_valid_hex_string(hex_message):
                        send_data = bytes.fromhex(hex_message)
                        return send_data,text
                    
            return None,None
        except Exception as e:
            print(e)
            return None,None
    def get_receive_text(self, data:bytes):
        print(data)
        mesg_list = []
        if data:
            if self.message_type == 'HEX':
                # 如果数据是十六进制格式，将其转换为字符串
                try:
                    mesg_list.append(binascii.hexlify(data).decode('utf-8'))
                except UnicodeDecodeError as e:
                    # 如果解码失败，你可以选择其他解码方式
                    mesg_list.append(data.hex())
            else:
                try:
                    mesg_list = self.get_format_data(data)
                except Exception as e:
                    mesg_list.append(str(data))
            return mesg_list
        else:
            return None
    def get_normal_text(self, data: bytes):
        parts = []
        # parts = data.split(b'"""')
        # start_index = 0
        # start_index = data.find(b'/sys')
        # if start_index == -1:
        #     start_index = 0  # 如果找不到，则返回空字符串

        # data = data[start_index:]
        # while True:
        #     # 找到下一个 """ 的位置
        #     start_quote_index = data.find(b'"""', start_index)
        #     if start_quote_index == -1:
        #         break  # 如果找不到，则结束循环

        #     # 从当前 """ 的位置开始找到 /sys 部分的位置
        #     sys_index = data.find(b'/sys', start_quote_index)
        #     if sys_index == -1:
        #         break  # 如果找不到 /sys，则结束循环

        #     # 添加找到的部分到列表中
        #     parts.append(data[start_quote_index:sys_index])

        #     # 更新下一次搜索的起始位置
        #     start_index = sys_index

        # return parts
        # 找到第一个数字字符的位置
        start_index = data.find(b'/sys')
        if start_index == -1:
            start_index = 0  # 如果找不到，则返回空字符串

        # 返回从 /sys 后面到字符串末尾的内容
        parts.append(data[start_index:])
        return parts

    def get_format_data(self, receive_data:bytes):
        try:
            datalist = self.get_normal_text(receive_data)
        except Exception as e:
            datalist = receive_data
        print(data)
        list = []
        for data in datalist:
            try:   
                json_data = json.loads(data)
                # 将JSON格式化为可读形式
                message = json.dumps(json_data, indent=4)
            except Exception as e:
                try:
                # 如果数据是ASCII文本格式，可以直接使用
                    message = data.decode('utf-8')
                except Exception as e:
                    try:
                        message = data.decode('gbk')
                    except Exception as e:
                        try:
                            # 将16进制字符串转换为整数
                            ascii_value = int(data, 16)

                            # 将ASCII码值转换为字符
                            message = chr(ascii_value)
                        except Exception as e:
                            message = str(data)
            list.append(message)
        return list
    def receive_message_process(self, data:bytes):
        message = self.get_receive_text(data)
        if message is not None:
            for mesg in message:
                message = self.get_modify_text(mesg)
                self.sendandreceive.add_message(DIR_UP, message)
    def client_receive_message_process(self, socket:QTcpSocket, data:bytes):
        message = self.get_receive_text(data)
        if message is not None:
            for mesg in message:
                format_message = self.get_modify_text(mesg)
                self.sendandreceive.add_message(DIR_UP, format_message)
                self.check_is_need_replay(mesg)
        
    def check_is_need_replay(self, data:bytes):
        try:
            frame = self.get_hex_frame(data)
            if frame:
                if is_csg_frame(frame):
                    control_data = frame[6]
                    adress = get_csg_adress(frame)
                    dir, prm, acd, fcv  = get_dir_prm(control_data)
                    if dir and prm:
                        control_code = control_data & 0x0f
                        if control_code != 9 and cfg.get(cfg.ReportReplay) == False:
                            return
                        replay_frame = send_ack_frame(frame, control_code)
                        self.chennel.data_sended.emit(bytes(replay_frame))
                        frame_format = frame_fun.get_data_str_with_space(replay_frame)
                        self.sendandreceive.add_message(DIR_DOWN, frame_format)
                        
                        if cfg.get(cfg.Multireport) == True:
                            adresslist = cfg.get(cfg.MultireportAdress)
                            if adress not in adresslist:
                                print("发送地址{}不在列表中".format(adress))
                                return
        except Exception as e:
            print(e)

    def get_hex_frame(self, text):
        try:
            hex_str = text.replace(' ', '')
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
            return frame
        except ValueError:
            return None
    def send_message(self):
        channel = self.chennel
        message, formatted_frame = self.get_message_by_type()
        if message is None:
            return
        if isinstance(channel, SerialPortThread):
            channel.data_sended.emit(message)
            self.sendandreceive.add_message(DIR_DOWN, formatted_frame)
        if isinstance(channel, TcpClient):
            channel.data_sended.emit(message)
            self.sendandreceive.add_message(DIR_DOWN, formatted_frame)
        if isinstance(channel, ClientWorker):
            channel.data_sended.emit(message)
            self.sendandreceive.add_message(DIR_DOWN, formatted_frame)
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        return super().resizeEvent(a0)
    
class MqttSend(QWidget):
    subtopic_changed = pyqtSignal(str)
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.qhlayout = QHBoxLayout(self)

        self.topiclabel = QLabel('主题')
        self.topic = PlainTextEdit()
        self.topiclayout = QHBoxLayout()
        self.topiclayout.addWidget(self.topiclabel)
        self.topiclayout.addWidget(self.topic)
        self.topic.setFixedHeight(50)

        self.payloadlabel = QLabel('负载')
        self.payload = PlainTextEdit()
        self.payloadlayout = QHBoxLayout()
        self.payloadlayout.addWidget(self.payloadlabel)
        self.payloadlayout.addWidget(self.payload)
        self.payload.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.messagelayout = QVBoxLayout()
        self.messagelayout.addLayout(self.topiclayout)
        self.messagelayout.addLayout(self.payloadlayout)

        self.leftlayout = QVBoxLayout()
        self.radioWidget = QWidget()
        self.radioLayout = QVBoxLayout(self.radioWidget)
        self.radioLayout.setContentsMargins(2, 0, 0, 0)
        self.radioLayout.setSpacing(15)
        self.subtopic = PlainTextEdit(self.radioWidget)
        self.radioWidget.setFixedSize(400, 300)
        self.subbutton = PrimaryPushButton('订阅')
        self.radioLayout.addWidget(self.subtopic)
        self.radioLayout.addWidget(self.subbutton)

        self.sendButton = TransparentToolButton(FluentIcon.SEND)
        self.leftlayout.addWidget(self.radioWidget)
        self.leftlayout.setSpacing(5)
        self.leftlayout.addWidget(self.sendButton)

        self.qhlayout.addLayout(self.messagelayout)
        self.qhlayout.addSpacing(10)
        self.qhlayout.addLayout(self.leftlayout)
        self.qhlayout.setContentsMargins(0, 0, 0, 0)

        self.subbutton.clicked.connect(self.sub_topic)
    
    def get_last_send_text(self):
        return self.topic.toPlainText(), self.payload.toPlainText(),self.subtopic.toPlainText()
    
    def set_last_send_text(self, topic, payload):
        self.topic.setPlainText(topic)
        self.payload.setPlainText(payload)

    def get_last_subtopic(self):
        return self.subtopic.toPlainText()
    def set_last_subtopic(self, topic):
        self.subtopic.setPlainText(topic)
    def sub_topic(self):
        topic = self.subtopic.toPlainText()
        if topic:
            self.subtopic_changed.emit(topic)
    
    def get_sub_topic(self):
        return self.subtopic.toPlainText()

class MqttSendReceive(BaseSendReceive):
    def __init__(self, title, chennel: MQTTClientThread, parent=None):
        super().__init__(parent=parent)
        self.title = title
        self.chennel = chennel

        # Upper Part (BaseSendRecive)
        self.subtopic = [self.chennel.get_def_topic()]
        self.sendandreceive = BaseSendRecive(self.title, self.subtopic, self)
        self.sendandreceive.setContentsMargins(0, 0, 0, 5)
        # Lower Part (MqttSend)
        self.basesend = MqttSend(self)
        self.basesend.setContentsMargins(0, 5, 0, 0)

        # Main Widget
        self.qvlayout = QVBoxLayout(self)
        self.qvlayout.setContentsMargins(0, 0, 0, 0)

        # Splitter
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        # Upper Part (sendandreceive)
        size_policy_upper = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sendandreceive.setSizePolicy(size_policy_upper)
        splitter.addWidget(self.sendandreceive)


        # Lower Part (basesend)
        size_policy_lower = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.basesend.setSizePolicy(size_policy_lower)
        splitter.addWidget(self.basesend)

        # Add the splitter to the main layout
        self.qvlayout.addWidget(splitter)

        self.slot_init()
    def slot_init(self):
        self.basesend.sendButton.clicked.connect(self.send_message)
        self.basesend.subtopic_changed.connect(self.subtopic_changed)
        self.chennel.message_received.connect(self.receive_message_process)
        
    def set_title(self, title):
        self.title = title
        self.sendandreceive.set_title(self.title)
    
    def set_last_message(self, message):
        self.sendandreceive.set_last_message(message)
    def subtopic_changed(self, topic):
        topics = topic.replace(" ", "").split(',')
        # 订阅新的主题
        for new_topic in topics:
            if new_topic not in self.subtopic:
                self.subtopic.append(new_topic)
                self.chennel.subscribe(new_topic)

        # 取消订阅不再包含在topics中的主题
        for current_topic in self.subtopic.copy():
            if current_topic not in topics:
                self.subtopic.remove(current_topic)
                self.chennel.unsubscribe(current_topic)

    def set_last_send_text(self, message):
        topic, payload, subtopic = message
        self.basesend.set_last_send_text(topic, payload)
        self.basesend.set_last_subtopic(subtopic)
    def get_last_send_text(self):
        return self.basesend.get_last_send_text()
    
    def get_last_log_text(self):
        return self.sendandreceive.get_last_text()
    
    def get_last_subtopic(self):
        return self.basesend.get_last_subtopic()
    
    def set_last_subtopic(self, subtopic):
        self.basesend.set_last_subtopic(subtopic)
    def set_info_to_log(self, text):
        self.sendandreceive.set_info_to_log(text)
    def receive_message_process(self, message:MqttMessageDetails):
        try:
            formatted_message = json.dumps(
                {
                    'topic': message.topic,
                    'payload': ast.literal_eval(message.payload),
                },
                indent=4
            )
            self.sendandreceive.add_message(DIR_UP, formatted_message)
        except Exception as e:
            try:
                payload=message.payload.rstrip('\u0000')
                formatted_message = json.dumps(
                    {
                        'topic': message.topic,
                        'payload': ast.literal_eval(payload),
                    },
                    indent=4
                )
                self.sendandreceive.add_message(DIR_UP, formatted_message)
            except Exception as e:
                try:
                    formatted_message = json.dumps(
                        {
                            'topic': message.topic,
                            'payload': message.payload,
                        },
                        indent=4
                    )
                    self.sendandreceive.add_message(DIR_UP, formatted_message)
                except Exception as e:
                    print(e)
    def send_message(self):
        channel = self.chennel
        topic = self.basesend.topic.toPlainText()
        payload = self.basesend.payload.toPlainText()
        channel.publish_message(topic, payload)
    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        return super().resizeEvent(a0)
    
class TabInterface(QWidget):
    """ Tab interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabCount = 0
        self.widget_dict = {}
        self.tabBar = TabBar(self)
        self.stackedWidget = QStackedWidget(self)
        self.tabView = QWidget(self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout(self.tabView)
        self.label = QLabel("请前往设置页面连接...")
        self.vBoxLayout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignCenter)
        self.__initWidget()

    def __initWidget(self):
        self.initLayout()
        self.tabBar.setAddButtonVisible(False)
        self.tabBar.setMovable(True)
        self.tabBar.setScrollable(True)
        self.tabBar.setTabShadowEnabled(True)
        self.tabBar.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)

        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.connectSignalToSlot()

    def connectSignalToSlot(self):
        # self.tabBar.tabAddRequested.connect(self.addTab)
        self.tabBar.tabCloseRequested.connect(self.removeTab)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        signalBus.channel_connected.connect(self.onChannelConnected)
        signalBus.channel_disconnected.connect(self.onChannelDisconnected)

    def initLayout(self):
        self.tabBar.setTabMaximumWidth(200)
        self.hBoxLayout.addWidget(self.tabView)


        self.vBoxLayout.addWidget(self.tabBar)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

    def addSubInterface(self, widget: Type[BaseSendReceive], objectName, text, icon):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.tabBar.addTab(
            routeKey=objectName,
            text=text,
            icon=icon,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
        self.widget_dict[text] = widget
    
    def insertSubInterface(self, index, widget: Type[BaseSendReceive], objectName, text, icon):
        widget.setObjectName(objectName)
        self.stackedWidget.insertWidget(index, widget)
        self.tabBar.insertTab(
            index,
            routeKey=objectName,
            text=text,
            icon=icon,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )
        self.update_widget_dict(widget, text)
    def update_widget_dict(self, widget, text):
        if text in self.widget_dict:
            self.widget_dict[text] = widget

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        if not widget:
            return

        self.tabBar.setCurrentTab(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
    
    def removeTabByIdex(self, index):
        item = self.tabBar.tabItem(index)
        widget = self.findChild(BaseSendReceive, item.routeKey())

        self.stackedWidget.removeWidget(widget)
        self.tabBar.removeTab(index)
        widget.deleteLater()
    def removeTab(self, index):
        item = self.tabBar.tabItem(index)
        widget = self.findChild(BaseSendReceive, item.routeKey())
        self.stackedWidget.removeWidget(widget)
        self.tabBar.removeTab(index)
        widget.deleteLater()
        self.disconnect_channel(widget.chennel)
        self.widget_dict.pop(item.text())

    def onChannelConnected(self, type, channel):
        """连接成功后，将channel添加到tab栏上"""
        if self.label is not None:
            self.vBoxLayout.removeWidget(self.label)
            self.label.deleteLater()
            self.label = None
        text = self.get_title_name(channel)
        if text in self.widget_dict:
            index, last_text, last_send = self.removeTabByName(text)
        else:
            index = None
        if type != CommType.MQTT:
            widget = NormalSendReceive(text, channel, self)
        else:
            widget = MqttSendReceive(text, channel, self)
        if type == CommType.SERIAL:
            if index is None:
                self.addSubInterface(widget, text, text, ":/gallery/images/serial_connect.png")
                self.tabCount += 1
            else:
                self.insertSubInterface(index, widget, text, text, ":/gallery/images/serial_connect.png")
                widget.set_last_message(last_text)
                widget.set_last_send_text(last_send)
        elif type == CommType.TCP_CLIENT:
            if index is None:
                self.addSubInterface(widget, text, text, ':/gallery/images/tcp_connect.png')
                self.tabCount += 1
            else:
                self.insertSubInterface(index, widget, text, text, ':/gallery/images/tcp_connect.png')
                widget.set_last_message(last_text)
                widget.set_last_send_text(last_send)
        elif type == CommType.TCP_SERVICE:
            if index is None:
                self.addSubInterface(widget, text, text, ':/gallery/images/tcp_connect.png')
                self.tabCount += 1
            else:
                self.insertSubInterface(index, widget, text, text, ':/gallery/images/tcp_connect.png')
                widget.set_last_message(last_text)
                widget.set_last_send_text(last_send)
        elif type == CommType.MQTT:
            if index is None:
                self.addSubInterface(widget, text, text, ':/gallery/images/mqtt_connect.png')
                self.tabCount += 1
            else:
                self.insertSubInterface(index, widget, text, text, ':/gallery/images/mqtt_connect.png')
                widget.set_last_message(last_text)
                widget.set_last_send_text(last_send)
        
        widget.set_info_to_log("online")

    def disconnect_channel(self, channel):
        if isinstance(channel, SerialPortThread):
            channel.stopsingal.emit()
        elif isinstance(channel, TcpClient):
            channel.stopsingal.emit()
        elif isinstance(channel, ClientWorker):
            channel.stopsingal.emit() 
        elif isinstance(channel, MQTTClientThread):
            channel.stopsingal.emit()       
    def get_title_name(self, channel):
        if isinstance(channel, SerialPortThread):
            text = channel.port_name + ':' + str(channel.baud_rate)
        elif isinstance(channel, TcpClient):
            text = channel.host + ':' + str(channel.port)
        elif isinstance(channel, ClientWorker):
            text = channel.socket.peerAddress().toString() + ':' + str(channel.socket.peerPort())
        elif isinstance(channel, MQTTClientThread):
            text = channel.broker_address + ':' + str(channel.broker_port)
        else:
            text = "Unknown"
        return text
    def onChannelDisconnected(self, type, channel):
        text = self.get_title_name(channel)
        widget = self.getWidgetByText(text)
        index = self.getWidgetIndex(widget)
        if index is None:
            return
        widget.set_info_to_log("offine")
        if type == CommType.SERIAL:
            self.tabBar.setTabIcon(index, ':/gallery/images/serial_disconnect.png')
        elif type == CommType.TCP_CLIENT:
            self.tabBar.setTabIcon(index, ':/gallery/images/tcp_disconnect.png')
        elif type == CommType.TCP_SERVICE:
            self.tabBar.setTabIcon(index, ':/gallery/images/tcp_disconnect.png')
        elif type == CommType.MQTT:
            self.tabBar.setTabIcon(index, ':/gallery/images/mqtt_disconnect.png')

    def getWidgetByText(self, text):
        return self.widget_dict.get(text, None)

    def getWidgetIndex(self, widget):
        index = self.stackedWidget.indexOf(widget)
        return index if index != -1 else None
    def removeTabByName(self, name):
        """ Remove a widget based on the provided text """
        widget = self.getWidgetByText(name)
        if widget:
            last_text = widget.get_last_log_text()
            last_send = widget.get_last_send_text()
            index = self.getWidgetIndex(widget)
            self.removeTabByIdex(index)
            return index, last_text, last_send
        else:
            return None, None, None
    
class ReceiveSendInterface(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="收发页面",
            parent=parent
        )
        self.setObjectName('SendandReceive')
        self.analysicView = TabInterface()
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.analysicView)
        self.vBoxLayout.setContentsMargins(0, 0, 2, 2)

