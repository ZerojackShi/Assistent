from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QTextEdit, QWidget,QHBoxLayout,QFrame,QGraphicsDropShadowEffect,QGraphicsOpacityEffect
from PyQt5.QtCore import Qt,QPropertyAnimation,QEasingCurve,QEvent
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPalette, QPixmap,QResizeEvent
from qfluentwidgets import StyleSheetBase, Theme, isDarkTheme, qconfig,PrimaryPushButton,ComboBox
from ..common.signal_bus import signalBus
from ..common.channel_info import channel_info

class MaskDialogBase(QDialog):
    """ Dialog box base class with a mask """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._hBoxLayout = QHBoxLayout(self)
        self.windowMask = QWidget(self)

        # dialog box in the center of mask, all widgets take it as parent
        self.widget = QFrame(self, objectName='centerWidget')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, parent.width(), parent.height())

        c = 0 if isDarkTheme() else 255
        self.windowMask.resize(self.size())
        self.windowMask.setStyleSheet(f'background:rgba({c}, {c}, {c}, 0.6)')
        self._hBoxLayout.addWidget(self.widget)
        self.setShadowEffect()

        self.window().installEventFilter(self)

    def setShadowEffect(self, blurRadius=60, offset=(0, 10), color=QColor(0, 0, 0, 100)):
        """ add shadow to dialog """
        shadowEffect = QGraphicsDropShadowEffect(self.widget)
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setOffset(*offset)
        shadowEffect.setColor(color)
        self.widget.setGraphicsEffect(None)
        self.widget.setGraphicsEffect(shadowEffect)

    def setMaskColor(self, color: QColor):
        """ set the color of mask """
        self.windowMask.setStyleSheet(f"""
            background: rgba({color.red()}, {color.blue()}, {color.green()}, {color.alpha()})
        """)

    def showEvent(self, e):
        """ fade in """
        opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacityEffect)
        opacityAni = QPropertyAnimation(opacityEffect, b'opacity', self)
        opacityAni.setStartValue(0)
        opacityAni.setEndValue(1)
        opacityAni.setDuration(200)
        opacityAni.setEasingCurve(QEasingCurve.InSine)
        opacityAni.finished.connect(opacityEffect.deleteLater)
        opacityAni.start()
        super().showEvent(e)

    def closeEvent(self, e):
        """ fade out """
        self.widget.setGraphicsEffect(None)
        opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacityEffect)
        opacityAni = QPropertyAnimation(opacityEffect, b'opacity', self)
        opacityAni.setStartValue(1)
        opacityAni.setEndValue(0)
        opacityAni.setDuration(100)
        opacityAni.setEasingCurve(QEasingCurve.OutCubic)
        opacityAni.finished.connect(self.deleteLater)
        opacityAni.start()
        e.ignore()

    def resizeEvent(self, e):
        self.windowMask.resize(self.size())

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Resize:
                re = QResizeEvent(e)
                self.resize(re.size())

        return super().eventFilter(obj, e)

class Comwidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setObjectName("Comwidget")
        self.resize(400, 300)
        self._hBoxLayout = QHBoxLayout(self)
        
        self.read_button = PrimaryPushButton(self.tr('读取'))
        self.setbutton = PrimaryPushButton(self.tr("设置"))
        self.channelcomboBox = ComboBox()
        self.channelcomboBox.setPlaceholderText(self.tr("请选择通道"))

        self._hBoxLayout.addWidget(self.read_button)
        self._hBoxLayout.addWidget(self.setbutton)
        self._hBoxLayout.addWidget(self.channelcomboBox)
        self.channel_info = None
        self.init_ui()

    def init_ui(self):
        channel = channel_info.get_all_channel_info()
        for key, value in channel.items():
            self.channelcomboBox.addItem(value[2])
        
        channel_info.channelInfoChanel.connect(self.add_combobox)
        self.channelcomboBox.currentIndexChanged.connect(self.set_cur_channel)
        
    def add_combobox(self, channel_info):
        for key, value in channel_info.items():
            channel_name = value[2]  # 获取 channel_name
            print(channel_name)
            if self.channelcomboBox.findText(channel_name) == -1:
                self.channelcomboBox.addItem(channel_name)

    def set_cur_channel(self):
        channel_name = self.channelcomboBox.currentText()
        all_channel = channel_info.get_all_channel_info()
        channel = None
        for key, value in all_channel.items():
            if value[2] == channel_name:
                channel = value
                break
        if channel:
            self.channel_info = channel
        

    def get_channel(self):
        channel_name = self.channelcomboBox.currentText()
        all_channel = channel_info.get_all_channel_info()
        channel = None
        for key, value in all_channel.items():
            if value[2] == channel_name:
                channel = value
                break
        self.channel_info = channel
        return self.channel_info
    
    def send_message(self, channel, type, message):
        channel_info.send_message(channel, type, message)
