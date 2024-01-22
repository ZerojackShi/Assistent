# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme,Pivot,qrouter,IndicatorPosition,FluentIconBase,
                            qconfig,LineEdit,ComboBox,PrimaryPushButton,SwitchButton,ConfigItem, SettingCard,PlainTextEdit,IconWidget)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths,QRegExp
from PyQt5.QtGui import QDesktopServices,QIcon,QPainter,QColor,QRegExpValidator,QFont
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog,QPushButton
from typing import Union
from ..common.config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
import serial.tools.list_ports
from ..plugins.signalCommunication import CommunicationModule
from ..common.commodule import CommType,commmbus
from ..components.state_tools import CustomStateToolTip
from ..common.icon import Icon
import serial
from PyQt5.QtCore import QObject

class CustomVBoxLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 默认对齐方式为左对齐
        self.setAlignment(Qt.AlignLeft)

    def setAlignment(self, alignment):
        self.alignment = alignment

    def addItem(self, item):
        super().addItem(item)
        item.setAlignment(self.alignment)

class Tcpconfig(QWidget):
    def __init__(self, type, label1, label2, parent=None):
        super().__init__(parent=parent)
        self.type = type
        self.setFixedSize(300, 100)
        ip_validator = QRegExpValidator(QRegExp(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"))
        self.iplayout = QHBoxLayout()  # 使用水平布局
        self.iplabel = QLabel(label1)
        self.iplabel.setFont(QFont("Courier New", 12))
        self.iplabel.setAlignment(Qt.AlignLeft)
        self.ipNumberInput = LineEdit()
        self.ipNumberInput.setAlignment(Qt.AlignRight)
        self.ipNumberInput.setMaximumWidth(200)
        self.ipNumberInput.setValidator(ip_validator)
        self.iplayout.addWidget(self.iplabel, 1)
        self.iplayout.addWidget(self.ipNumberInput)

        self.portlayout = QHBoxLayout()  # 使用水平布局
        self.portlabel = QLabel()
        self.portlabel.setText(label2)
        self.portlabel.setFont(QFont("Courier New", 12))
        self.portlabel.setAlignment(Qt.AlignLeft)
        self.portNumberInput = LineEdit()
        self.portNumberInput.setMaximumWidth(200)
        self.portNumberInput.setAlignment(Qt.AlignRight)
        self.portlayout.addWidget(self.portlabel, 1)
        self.portlayout.addWidget(self.portNumberInput)

        self.qvlayout = CustomVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.iplayout)
        self.qvlayout.addLayout(self.portlayout)

        self.qvlayout.setContentsMargins(0,0,0,0)
        self.qvlayout.setSpacing(2)
        self.init_widget()

    def init_widget(self):
        if self.type == CommType.TCP_CLIENT:
            ip = cfg.get(cfg.tcpClientIP)
            port = cfg.get(cfg.tcpClientPort)
        else:
            ip = cfg.get(cfg.tcpServerIP)
            port = cfg.get(cfg.tcpServerPort)
        self.ipNumberInput.setText(ip)
        self.portNumberInput.setText(str(port))

    def setAlignment(self, a0: Union[Qt.Alignment, Qt.AlignmentFlag]):
        self.qvlayout.setAlignment(a0)

    def get_tcp_connect_param(self):
        port = self.portNumberInput.text()
        ipaddr = self.ipNumberInput.text()    
        return ipaddr,int(port)
    
    def set_edit_enable(self, enable=True):
        self.ipNumberInput.setEnabled(enable)
        self.portNumberInput.setEnabled(enable)
    
class SerialConfig(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setFixedSize(300, 200)
        self.serialPortlayout = QHBoxLayout()  # 使用水平布局
        self.serialPortlabel = QLabel('串口号')
        self.serialPortlabel.setAlignment(Qt.AlignLeft)

        self.serialcomboBox = ComboBox()
        self.serialPortlayout.addWidget(self.serialPortlabel)
        self.serialPortlayout.addWidget(self.serialcomboBox)

        self.Budratelayout = QHBoxLayout()  # 使用水平布局
        self.Budratelabel = QLabel('波特率')
        self.Budratelabel.setAlignment(Qt.AlignLeft)
        self.BudrateComBox = ComboBox()
        self.Budratelayout.addWidget(self.Budratelabel)
        self.Budratelayout.addWidget(self.BudrateComBox)

        self.Checklayout = QHBoxLayout()  # 使用水平布局
        self.Checklabel = QLabel('校验位')
        self.Checklabel.setAlignment(Qt.AlignLeft)
        self.CheckComBox = ComboBox()
        self.Checklayout.addWidget(self.Checklabel)
        self.Checklayout.addWidget(self.CheckComBox)

        self.DataBitlayout = QHBoxLayout()  # 使用水平布局
        self.DataBitlabel = QLabel('数据位')
        self.DataBitlabel.setAlignment(Qt.AlignLeft)
        self.DataBitComBox = ComboBox()
        self.DataBitlayout.addWidget(self.DataBitlabel)
        self.DataBitlayout.addWidget(self.DataBitComBox)

        self.StopBitlayout = QHBoxLayout()  # 使用水平布局
        self.StopBitlabel = QLabel('停止位')
        self.StopBitlabel.setAlignment(Qt.AlignLeft)
        self.StopBitComBox = ComboBox()
        self.StopBitlayout.addWidget(self.StopBitlabel)
        self.StopBitlayout.addWidget(self.StopBitComBox)


        self.qvlayout = CustomVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.serialPortlayout)
        self.qvlayout.addLayout(self.Budratelayout)
        self.qvlayout.addLayout(self.Checklayout)
        self.qvlayout.addLayout(self.DataBitlayout)
        self.qvlayout.addLayout(self.StopBitlayout)

        self._init_Widgets()

    def _init_Widgets(self):
        self.populate_serial_ports()
        self.Budrate = ['2400', '4800', '9600', '115200']
        self.BudrateComBox.addItems(self.Budrate)
        self.check = ['奇校验','偶校验','无校验']
        self.CheckComBox.addItems(self.check)
        self.databit=['5','6', '7','8']
        self.DataBitComBox.addItems(self.databit)
        self.stopbit = ['1','1.5','2']
        self.StopBitComBox.addItems(self.stopbit)

        # 读取串口配置
        baud_rate = cfg.get(cfg.serial_BaudRate)
        parity = cfg.get(cfg.serial_parity)
        data_bits = cfg.get(cfg.serial_databit)
        stop_bits = cfg.get(cfg.serial_stopbit)
        if baud_rate:
            self.BudrateComBox.setCurrentText(f'{baud_rate}')
        else:
            self.BudrateComBox.setCurrentIndex(2)
        
        if parity:
            self.CheckComBox.setCurrentText(parity)
        else:
            self.CheckComBox.setCurrentText(1)

        if data_bits:
            self.DataBitComBox.setCurrentText(f"{data_bits}")
        else:
            self.DataBitComBox.setCurrentIndex(3)
        
        if stop_bits:
            self.StopBitComBox.setCurrentText(f"{stop_bits}")
        else:
            self.StopBitComBox.setCurrentIndex(3)

        self.qvlayout.setContentsMargins(0,0,0,0)
        self.qvlayout.setSpacing(2)

    def setAlignment(self, a0: Union[Qt.Alignment, Qt.AlignmentFlag]):
        self.qvlayout.setAlignment(a0)

    def populate_serial_ports(self):
        serial_ports = [port.device for port in serial.tools.list_ports.comports()]
        self.serialcomboBox.addItems(serial_ports)

    def get_serial_connect_param(self):
        comname = self.serialcomboBox.currentText()
        budrate =  int(self.Budrate[self.BudrateComBox.currentIndex()])
        check = self.get_serial_check()
        databit = self.get_serial_datait()
        stopbit = self.get_serial_stopbit()
        return comname,budrate,check,databit,stopbit
    
    def get_serial_check(self):
        if self.CheckComBox.currentIndex() == 0:
            check = serial.PARITY_ODD
        elif self.CheckComBox.currentIndex() == 1:
            check = serial.PARITY_EVEN
        elif self.CheckComBox.currentIndex() == 2:
            check = serial.PARITY_NONE
        else:
            check = serial.PARITY_NONE
        return check
    
    def get_serial_datait(self):
        if self.DataBitComBox.currentIndex() == 0:
            databit = serial.FIVEBITS
        elif self.DataBitComBox.currentIndex() == 1:
            databit = serial.SIXBITS
        elif self.DataBitComBox.currentIndex == 2:
            databit = serial.SEVENBITS
        elif self.DataBitComBox.currentIndex() == 3:
            databit = serial.EIGHTBITS
        else:
            databit = serial.EIGHTBITS
        return databit
    
    def get_serial_stopbit(self):
        if self.StopBitComBox.currentIndex() == 0:
            stopbit = serial.STOPBITS_ONE
        elif self.StopBitComBox.currentIndex() == 1:
            stopbit = serial.STOPBITS_ONE_POINT_FIVE
        elif self.StopBitComBox.currentIndex() == 2:
            stopbit = serial.STOPBITS_TWO
        else:
            stopbit = serial.STOPBITS_ONE
        return stopbit
    
    def set_edit_enable(self, enable=True):
        self.serialcomboBox.setEnabled(enable)
        self.BudrateComBox.setEnabled(enable)
        self.CheckComBox.setEnabled(enable)
        self.DataBitComBox.setEnabled(enable)
        self.StopBitComBox.setEnabled(enable)

class MqttConfig(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.type = type
        self.setFixedSize(300, 100)
        ip_validator = QRegExpValidator(QRegExp(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"))
        self.iplayout = QHBoxLayout()  # 使用水平布局
        self.iplabel = QLabel("主机IP")
        self.iplabel.setFont(QFont("Courier New", 12))
        self.iplabel.setAlignment(Qt.AlignLeft)
        self.ipNumberInput = LineEdit()
        self.ipNumberInput.setAlignment(Qt.AlignRight)
        self.ipNumberInput.setMaximumWidth(200)
        self.ipNumberInput.setValidator(ip_validator)
        self.iplayout.addWidget(self.iplabel, 1)
        self.iplayout.addWidget(self.ipNumberInput)

        self.portlayout = QHBoxLayout()  # 使用水平布局
        self.portlabel = QLabel()
        self.portlabel.setText("端口")
        self.portlabel.setFont(QFont("Courier New", 12))
        self.portlabel.setAlignment(Qt.AlignLeft)
        self.portNumberInput = LineEdit()
        self.portNumberInput.setMaximumWidth(200)
        self.portNumberInput.setAlignment(Qt.AlignRight)
        self.portlayout.addWidget(self.portlabel, 1)
        self.portlayout.addWidget(self.portNumberInput)

        self.qvlayout = CustomVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.iplayout)
        self.qvlayout.addLayout(self.portlayout)

        self.qvlayout.setContentsMargins(0,0,0,0)
        self.qvlayout.setSpacing(2)
        self.init_widget()

    def init_widget(self):
        if self.type == CommType.TCP_CLIENT:
            ip = cfg.get(cfg.tcpClientIP)
            port = cfg.get(cfg.tcpClientPort)
        else:
            ip = cfg.get(cfg.tcpServerIP)
            port = cfg.get(cfg.tcpServerPort)
        self.ipNumberInput.setText(ip)
        self.portNumberInput.setText(str(port))

    def setAlignment(self, a0: Union[Qt.Alignment, Qt.AlignmentFlag]):
        self.qvlayout.setAlignment(a0)

    def get_tcp_connect_param(self):
        port = self.portNumberInput.text()
        ipaddr = self.ipNumberInput.text()    
        return ipaddr,int(port)
    
    def set_edit_enable(self, enable=True):
        self.ipNumberInput.setEnabled(enable)
        self.portNumberInput.setEnabled(enable)

class ConnectConfig(QWidget):
    """ Pivot interface """

    Nav = Pivot
    sizeChanged = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.connectType = CommType.TCP_CLIENT
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        self.setFixedSize(300, 140)
        text = "<font>端&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;口</font>"
        self.tcpclientInterface = Tcpconfig(CommType.TCP_CLIENT, '远程地址',text,self)
        self.tcpserverInterface = Tcpconfig(CommType.TCP_SERVICE, '本地地址',text, self)
        self.serialInterface = SerialConfig(self)
        # self.mqttInterface = MqttConfig(self)
        # add items to pivot
        self.addSubInterface(self.tcpclientInterface, 'tcpclientInterface', self.tr('TCP客户端'))
        self.addSubInterface(self.tcpserverInterface, 'tcpserverInterface', self.tr('TCP服务器'))
        self.addSubInterface(self.serialInterface, 'serialInterface', self.tr('串口'))
        # self.addSubInterface(self.mqttInterface, 'mqttInterface', self.tr('MQTT'))

        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.tcpclientInterface)
        self.pivot.setCurrentItem(self.tcpclientInterface.objectName())

        qrouter.setDefaultRouteKey(self.stackedWidget, self.tcpclientInterface.objectName())

    def addSubInterface(self, widget: QLabel, objectName, text):
        widget.setObjectName(objectName)
        widget.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.setFixedSize(widget.width(), widget.height() + 40)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
        if index == 0:
            self.connectType = CommType.TCP_CLIENT
        elif index == 1:
            self.connectType = CommType.TCP_SERVICE
        elif index == 2:
            self.connectType = CommType.SERIAL

    def resizeEvent(self, event):
        # 大小变化事件处理
        new_size = event.size()
        # 在这里执行你想要的操作
        # 发射自定义信号以通知大小变化
        self.sizeChanged.emit()

    def get_connect_type(self)->CommType:
        return self.connectType
    
    def get_serial_connect_param(self):
        return self.serialInterface.get_serial_connect_param()
    
    def get_tcp_connect_param(self):
        if self.connectType == CommType.TCP_CLIENT:
            return self.tcpclientInterface.get_tcp_connect_param()
        elif self.connectType == CommType.TCP_SERVICE:
            return self.tcpserverInterface.get_tcp_connect_param()
    def set_edit_enable(self, type, enable=True):
        if self.connectType == CommType.TCP_CLIENT:
            self.tcpclientInterface.set_edit_enable(enable)
        elif self.connectType == CommType.TCP_SERVICE:
            self.tcpserverInterface.set_edit_enable(enable)    
        else:
            self.serialInterface.set_edit_enable(enable)
    
class ConnectCard(QFrame):
    """ Connnect card """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, parent=None):
        super().__init__(parent=parent)
        self.stateTooltip = None
        self.connectStatus = False
        self.setObjectName('setting_card')
        self.hBoxLayout = QHBoxLayout(self)
        self.Conconfig = ConnectConfig()
        self.connectButon = PrimaryPushButton('连接', self)
        self.connectButon.setFixedWidth(95)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.Conconfig,0, Qt.AlignLeft)
        self.hBoxLayout.addStretch(1)  # 伸缩空间，将后续的控件推到右边
        self.hBoxLayout.addWidget(self.connectButon, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.setFixedHeight(self.Conconfig.height() + 15)
        StyleSheet.SET_CARD.apply(self)
        self.Conconfig.sizeChanged.connect(self.update_size)
        self.connectButon.clicked.connect(self.connectProcess)
        self.commnectModule = None
        self.connecttype = None
    def update_size(self):
        self.setFixedHeight(self.Conconfig.height() + 15)
    
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

    def connectProcess(self):
        if self.connectStatus and self.commnectModule is not None:
            self.commnectModule.connection_result.connect(self.get_connect_result)
            self.commnectModule.tcpSocketChange.connect(self.tcp_socket_change_process)
            self.commnectModule.close()
            self.Conconfig.set_edit_enable(self.connecttype, True)
        else:
            self.connectButon.setEnabled(False)
            self.onStateButtonClicked()
            self.connecttype = self.Conconfig.get_connect_type()
            if self.connecttype == CommType.SERIAL:
                params = self.Conconfig.get_serial_connect_param()
                if None not in params:
                    comname, budrate, check, data, stop = params
                    self.update_connect_param(params)
                    # 所有参数都不为空
                    # 执行你的代码
                    self.commnectModule = CommunicationModule(
                    self.connecttype, 
                    serial_port=comname, 
                    baudrate=budrate,
                    databit=data,
                    checktype=check,
                    stopbit=stop
                    )
            elif self.connecttype == CommType.TCP_CLIENT:
                params = self.Conconfig.get_tcp_connect_param()
                if '' not in params:
                    ipaddr, port = params
                    self.update_connect_param(params)
                    # 所有参数都不为空
                    # 执行你的代码
                    self.commnectModule = CommunicationModule(
                    self.connecttype, 
                    tcp_ip = ipaddr,
                    tcp_port = port
                    )

            elif self.connecttype == CommType.TCP_SERVICE:
                params = self.Conconfig.get_tcp_connect_param()
                if '' not in params:
                    ipaddr, port = params
                    self.update_connect_param(params)
                    # 所有参数都不为空
                    # 执行你的代码
                    self.commnectModule = CommunicationModule(
                    self.connecttype, 
                    tcp_ip = ipaddr,
                    tcp_port = port
                    )

            if self.commnectModule:
                self.commnectModule.connection_result.connect(self.get_connect_result)
                self.commnectModule.tcpSocketChange.connect(self.tcp_socket_change_process)
                self.commnectModule.connect()
            else:
                self.connectStatus = False
                self.onStateButtonClicked()
                self.connectButon.setEnabled(True)
                self.connectButon.setText('连接')

    def get_connect_result(self, status):
        self.connectStatus = status
        self.onStateButtonClicked()
        commmbus.connecttype = self.connecttype
        commmbus.link_port = self.commnectModule
        if self.connecttype == CommType.SERIAL:
            commmbus.channel = self.commnectModule.serial
        elif self.connecttype == CommType.TCP_CLIENT:
            commmbus.channel = self.commnectModule.tcp_socket
        elif self.connecttype == CommType.TCP_SERVICE:
            commmbus.channel = self.commnectModule.clientSocket
        commmbus.link_status = status
        if status:
            self.Conconfig.set_edit_enable(self.connecttype, False)
            self.connectButon.setEnabled(True)
        else:
            self.connectButon.setEnabled(True)
            self.Conconfig.set_edit_enable(self.connecttype, True)

    def tcp_socket_change_process(self,socket_list):
        commmbus.tcpSocket = socket_list
        signalBus.tcpSocketChange.emit(socket_list)
        
    def onStateButtonClicked(self):
        text = self.connectButon.text()
        if self.stateTooltip:
            if text == '连接':
                # self.stateTooltip.setTitle('连接结果')
                if self.connectStatus:
                    self.stateTooltip.seticon(FIF.COMPLETED)
                    self.stateTooltip.setTitle(
                        self.tr('连接成功') + ' 😆')
                    self.stateTooltip.setState(True)
                    self.connectButon.setText('断开')
                else:
                    self.stateTooltip.seticon(Icon.ERROR)
                    self.stateTooltip.setTitle(
                        self.tr('连接失败') + ' 😒')
                    self.stateTooltip.setState(True)
                    self.connectButon.setText('连接')
            else:
                # self.stateTooltip.setTitle('断开结果')
                if self.connectStatus:
                    self.stateTooltip.seticon(Icon.ERROR)
                    self.stateTooltip.setTitle(
                        self.tr('断开失败') + ' 😒')
                    self.stateTooltip.setState(True)
                    self.connectButon.setText('断开')
                else:
                    self.stateTooltip.seticon(FIF.COMPLETED)
                    self.stateTooltip.setTitle(
                        self.tr('已断开') + ' 😆')
                    self.stateTooltip.setState(True)
                    self.connectButon.setText('连接')

            self.stateTooltip = None
        else:
            if text == '连接':
                self.stateTooltip = CustomStateToolTip(
                    FIF.SYNC, self.tr('正在连接...'), self.window())
                self.stateTooltip.move(self.stateTooltip.getSuitablePos())
                self.stateTooltip.show()
            else:
                self.stateTooltip = CustomStateToolTip(
                    FIF.SYNC, self.tr('正在断开...'), self.window())
                self.stateTooltip.move(self.stateTooltip.getSuitablePos())
                self.stateTooltip.show()

    def update_connect_param(self, params):
        # 设置串口配置
        if self.connecttype == CommType.SERIAL:
            comname, budrate, check, data, stop = params
            cfg.set(cfg.serial_BaudRate, budrate)
            if check == serial.PARITY_ODD:
                check = "奇校验"
            elif check == serial.PARITY_EVEN:
                check = "偶校验"
            else:
                check = "无校验"
            cfg.set(cfg.serial_parity,check)
            cfg.set(cfg.serial_databit,data)
            cfg.set(cfg.serial_stopbit,stop)
        elif self.connecttype == CommType.TCP_CLIENT:
            ip, port = params
            cfg.set(cfg.tcpClientIP, ip)
            cfg.set(cfg.tcpClientPort, port)
        else:
            ip, port = params
            cfg.set(cfg.tcpServerIP, ip)
            cfg.set(cfg.tcpServerPort, port)


class MultireportCard(QWidget):
    checkedChanged = pyqtSignal(bool)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, ReportconfigItem: ConfigItem = None,
                 adressconfigItem: ConfigItem = None, parent=None):
        super().__init__(parent=parent)
        self.stateTooltip = None
        self.connectStatus = False
        self.reportconfig = ReportconfigItem
        self.adressConfig = adressconfigItem
        self.setObjectName('MultireportCard')

        self.switchButton = SwitchButton(
            self.tr('关'), self, IndicatorPosition.RIGHT)
        
        self.hBoxlayout = QHBoxLayout()
        self.PlainTextEdit = PlainTextEdit()
        self.button = PrimaryPushButton(self.tr('设置地址'))
        self.hBoxlayout.addWidget(self.PlainTextEdit, 0, Qt.AlignLeft)
        self.hBoxlayout.addSpacing(5)
        self.hBoxlayout.addWidget(self.button,0, Qt.AlignRight)
        self.PlainTextEdit.setFixedSize(200, 100)

        self.button.clicked.connect(self.__onTextChanged)
        self.switchButton.checkedChanged.connect(self.__onCheckedChanged)
        if ReportconfigItem:
            self.setValue(qconfig.get(ReportconfigItem))
            ReportconfigItem.valueChanged.connect(self.setValue)

        if adressconfigItem:
            self.setadressValue(qconfig.get(adressconfigItem))
            adressconfigItem.valueChanged.connect(self.setadressValue)

        # add switch button to layout
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.switchButton, 0, Qt.AlignRight)
        self.vBoxLayout.addLayout(self.hBoxlayout)

        StyleSheet.SET_CARD.apply(self)
        
        # Set size policies for better control
        self.PlainTextEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Adjust the layout to ensure no overlap
        self.hBoxlayout.setContentsMargins(10, 0, 10, 0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 10)

        self.setFixedSize(self.hBoxlayout.sizeHint().width(), self.vBoxLayout.sizeHint().height())
                          
    def __onCheckedChanged(self, isChecked: bool):
        """ switch button checked state changed slot """
        self.setValue(isChecked)
        self.checkedChanged.emit(isChecked)
    def __onTextChanged(self):
        """ text edit text changed slot """
        ayyay=[]
        text = self.PlainTextEdit.toPlainText()
        if not text:
            return
        parts = text.split(",")
        for part in parts:
            while len(part) < 12:
                part = "0" + part
            if part not in ayyay:
                ayyay.append(part)
        self.setadressValue(ayyay)
    def setValue(self, isChecked: bool):
        if self.reportconfig:
            qconfig.set(self.reportconfig, isChecked)

        self.switchButton.setChecked(isChecked)
        self.switchButton.setText(
            self.tr('开') if isChecked else self.tr('关'))
    def setadressValue(self, adress: list):
        if self.adressConfig:
            qconfig.set(self.adressConfig, adress)
        str = ",".join(adress)
        self.PlainTextEdit.setPlainText(str)
    def setChecked(self, isChecked: bool):
        self.setValue(isChecked)

    def isChecked(self):
        return self.switchButton.isChecked()
    
class MultiReportSetingCard(QFrame):
    """ Connnect card """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, ReportconfigItem: ConfigItem = None,
                 adressconfigItem: ConfigItem = None, parent=None):
        super().__init__(parent=parent)

        self.setObjectName('setting_card')
        self.iconLabel = IconWidget(icon, self)
        self.titleLabel = QLabel(title, self)
        self.hBoxLayout = QHBoxLayout()
        self.vBoxLayout = QVBoxLayout()
        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(7, 0, 0, 0)
        self.hBoxLayout.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)

        self.hBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignLeft)
        self.hBoxLayout.addSpacing(16)

        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignLeft)

        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addStretch(1)

        self.iconLabel.setFixedSize(16, 16)

        self.lhBoxLayout = QHBoxLayout(self)
        self.multireport = MultireportCard(icon, title, ReportconfigItem, adressconfigItem)

        self.lhBoxLayout.addLayout(self.hBoxLayout)
        self.lhBoxLayout.addWidget(self.multireport,0, Qt.AlignRight)
        self.setFixedHeight(self.multireport.height() + 15)
        StyleSheet.SET_CARD.apply(self)
    
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)   

class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.connectPCGroup = SettingCardGroup(
            self.tr("连接设置"), self.scrollWidget)
            
        self.connectCard = ConnectCard(
            FIF.DOWNLOAD,
            self.tr("配置"),
            self.connectPCGroup
        )
        
        # music folders
        self.basicsetgroup = SettingCardGroup(
            self.tr("基础设置"), self.scrollWidget)
        
        self.logFolderCard = PushSettingCard(
            self.tr('选择文件夹'),
            FIF.DOWNLOAD,
            self.tr("日志文件夹"),
            cfg.get(cfg.logFolder),
            self.basicsetgroup
        )
        self.replayenableCard = SwitchSettingCard(
            Icon.REPLAY,
            self.tr('主动上报回复'),
            None,
            cfg.ReportReplay,
            self.basicsetgroup
        )
        self.regiongroup = ComboBoxSettingCard(
            cfg.Region,
            Icon.REGION,
            self.tr('省份'),
            None,
            texts=["南网","云南","广东","深圳","广西","贵州","海南","topo"],
            parent=self.basicsetgroup
        )
        self.multireport = MultiReportSetingCard(
            Icon.REGION,
            self.tr('多主站上报'),
            cfg.Multireport,
            cfg.MultireportAdress,
            parent=self.basicsetgroup
        )
        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('Personalization'), self.scrollWidget)
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.personalGroup
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for UI'),
            texts=['简体中文', '繁體中文', 'English', self.tr('Use system setting')],
            parent=self.personalGroup
        )

        # material
        self.materialGroup = SettingCardGroup(
            self.tr('Material'), self.scrollWidget)
        self.blurRadiusCard = RangeSettingCard(
            cfg.blurRadius,
            FIF.ALBUM,
            self.tr('Acrylic blur radius'),
            self.tr('The greater the radius, the more blurred the image'),
            self.materialGroup
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup(
            self.tr("Software update"), self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('Check for updates when the application starts'),
            self.tr('The new version will be more stable and have more features'),
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup
        )

        # application
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('Open help page'),
            FIF.HELP,
            self.tr('Help'),
            self.tr(
                'Discover new features and learn useful tips about PyQt-Fluent-Widgets'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve PyQt-Fluent-Widgets by providing feedback'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " " + VERSION,
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.connectPCGroup.addSettingCard(self.connectCard)
        self.basicsetgroup.addSettingCard(self.logFolderCard)
        self.basicsetgroup.addSettingCard(self.replayenableCard)
        self.basicsetgroup.addSettingCard(self.regiongroup)
        self.basicsetgroup.addSettingCard(self.multireport)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.materialGroup.addSettingCard(self.blurRadiusCard)

        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.connectPCGroup)
        self.expandLayout.addWidget(self.basicsetgroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.materialGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.logFolder) == folder:
            return

        cfg.set(cfg.logFolder, folder)
        self.logFolderCard.setContent(folder)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # music in the pc
        self.logFolderCard.clicked.connect(
            self.__onDownloadFolderCardClicked)

        # personalization
        self.themeCard.optionChanged.connect(lambda ci: setTheme(cfg.get(ci)))
        self.themeColorCard.colorChanged.connect(setThemeColor)
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # about
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
