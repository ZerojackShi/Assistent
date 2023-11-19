from token import STAR
from PyQt5.QtGui import QTextCharFormat,QColor,QTextCursor
from PyQt5.QtCore import Qt
# coding:utf-8
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout,QButtonGroup,QLabel
from qfluentwidgets import ComboBox, isDarkTheme, FluentIcon,InfoBarIcon,PlainTextEdit,TransparentToolButton,InfoBarPosition,RadioButton
from qfluentwidgets import FluentIcon as FIF
from ..common.config import cfg, HELP_URL, REPO_URL, EXAMPLE_URL, FEEDBACK_URL
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
from ..plugins.frame_fun import get_data_str_order,get_data_str_with_space
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
        signalBus.messagereceive.connect(self.display_receive_message)
        signalBus.tcpSocketChange.connect(self.init_widget)
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

    def display_receive_message(self, text, socket):
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
        else:
            link = socket
        if self.sendandreceive.toPlainText() == '':
            cursor.insertText(f'[{current_time_str}]' + f"[{link}]" +"  接收  " + text)
        else:
            cursor.insertText('\n' + f'[{current_time_str}]' + f'[{link}]' + "  接收  " + text)
        self.sendandreceive.verticalScrollBar().setValue(last_position)
        self.tcpClientSocket.append(socket)

        self.report_replay(text, socket)
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
