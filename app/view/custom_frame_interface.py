from PyQt5.QtCore import Qt, QEasingCurve,pyqtSignal,QSize,QDate,QTime,QDateTime
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QButtonGroup
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, InfoBar, InfoBarPosition, ComboBox,
                            RadioButton, SpinBox, BreadcrumbBar,LineEdit,SwitchButton,PrimaryPushButton,PlainTextEdit)
from PyQt5.QtGui import QFont
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from ..plugins.frame_csg import FramePos
from ..plugins import frame_fun,frame_csg
from ..common.signal_bus import signalBus
from ..components.state_tools import DateTimePicker

class ParamFrameInterface(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pnlayout = QHBoxLayout()  # 使用水平布局
        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()
        self.pnInput.setFixedSize(400, 50)
        self.pnlayout.addWidget(self.pnlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.pnlayout.addWidget(self.pnInput, 1, Qt.AlignRight)
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")

        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setFixedSize(400, 100)
        self.itemlayout.addWidget(self.itemlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.itemlayout.addWidget(self.itemInput, 1, Qt.AlignRight)
        self.itemInput.setPlaceholderText("使用英文','拆分,如05060100,05060101")

        self.datalayout = QHBoxLayout()  # 使用水平布局
        self.datalabel = QLabel('数据内容')
        self.dataInput = PlainTextEdit()
        self.dataInput.setFixedSize(400, 100)
        self.datalayout.addWidget(self.datalabel, 0,Qt.AlignLeft)
        self.datalayout.addWidget(self.dataInput, 1, Qt.AlignRight)

        self.switchButton = SwitchButton(self.tr('设置'))
        self.switchButton.setChecked(True)
        self.switchButton.setText(self.tr('设置'))
        self.switchButton.checkedChanged.connect(self.onSwitchCheckedChanged)

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.button.clicked.connect(self.create_frame)
        self.framearea = PlainTextEdit()
        self.framearea.setPlaceholderText("报文生成区...")
        self.framearea.setFixedHeight(200)

        self.sendbutton = PrimaryPushButton(self.tr('发送报文'))
        self.sendbutton.clicked.connect(self.sendframe)

        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.pnlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.itemlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.datalayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.switchButton, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.button)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.framearea, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.sendbutton)

        self.qvlayout.setContentsMargins(0,0,0,5)
        self.qvlayout.setSpacing(2)

        StyleSheet.CUSTOM_INTERFACE.apply(self)
    def get_size(self):
        return self.qvlayout.sizeHint() + QSize(0, 50)
    
    def onSwitchCheckedChanged(self, isChecked):
        if isChecked:
            self.switchButton.setText(self.tr('设置'))
        else:
            self.switchButton.setText(self.tr('读取'))
    def sendframe(self):
        text = self.framearea.toPlainText()
        signalBus.sendmessage.emit(text)
    def create_frame(self, frame):
        if self.switchButton.isChecked():
            afn = 0x04
        else:
            afn = 0x0A
        item_dic = {}
        frame_len = 0
        frame = [0x00] * FramePos.POS_DATA.value
        input_text = self.pnInput.toPlainText()
        if input_text:                                       
            try:                                    
                point_array =  frame_fun.parse_meterpoint_input(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("测量点错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("请输入测量点!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        item = self.itemInput.toPlainText()
        if item is not None and item != '':
            try:
                item = int(item, 16)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("请输入数据标识!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        data = self.dataInput.toPlainText()
        if self.switchButton.isChecked():
            if data is not None and data != '':
                item_dic[item] = data
            else:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("请输入数据内容!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            data = None
            item_dic[item] = data
            
        adress = [0xff] * 6  # Fix the initialization of adress
        msa = 0x10
        frame_csg.init_frame(0x4a, afn, adress, msa, 0x60, frame)
        frame_len += FramePos.POS_DATA.value
        frame_len += frame_csg.get_frame(point_array, item_dic, frame)
        frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
        frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

        self.frame_finfish.emit(frame, frame_len)
        self.display_frame(frame, frame_len)

    def display_frame(self, frame, length):
        self.framearea.clear()
        text = frame_fun.get_data_str_with_space(frame)
        self.framearea.setPlainText(text)


class ReadCurInterface(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pnlayout = QHBoxLayout()  # 使用水平布局
        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()
        self.pnInput.setFixedSize(400, 50)
        self.pnlayout.addWidget(self.pnlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.pnlayout.addWidget(self.pnInput, 1, Qt.AlignRight)
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")

        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setFixedSize(400, 100)
        self.itemlayout.addWidget(self.itemlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.itemlayout.addWidget(self.itemInput, 1, Qt.AlignRight)
        self.itemInput.setPlaceholderText("使用英文','拆分,如05060100,05060101")

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.button.clicked.connect(self.create_frame)
        self.framearea = PlainTextEdit()
        self.framearea.setPlaceholderText("报文生成区...")
        self.framearea.setFixedHeight(200)
        self.sendbutton = PrimaryPushButton(self.tr('发送报文'))
        self.sendbutton.clicked.connect(self.sendframe)

        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.pnlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.itemlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.button, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.framearea, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.sendbutton, 1)

        self.qvlayout.setContentsMargins(0,0,0,5)
        StyleSheet.CUSTOM_INTERFACE.apply(self)

    def get_size(self):
        return self.qvlayout.sizeHint() + QSize(0, 50)
    def sendframe(self):
        text = self.framearea.toPlainText()
        signalBus.sendmessage.emit(text)
    def create_frame(self, frame):
        afn = 0x0c
        frame_len = 0
        frame = [0x00] * FramePos.POS_DATA.value
        input_text = self.pnInput.toPlainText()
        if input_text:   
            try:                                    
                point_array =  frame_fun.parse_meterpoint_input(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("测量点错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
            
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入测量点!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return

        item_array = []
        input_text = self.itemInput.toPlainText()
        if input_text:
            try:
                item_array = frame_fun.prase_item_by_input_text(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入数据标识!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
            
        adress = [0xff] * 6  # Fix the initialization of adress
        msa = 0x10
        frame_csg.init_frame(0x4a, afn, adress, msa, 0x60, frame)
        frame_len += FramePos.POS_DATA.value
        frame_len += frame_csg.add_point_and_item_to_frame(point_array, item_array, frame)
        frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
        frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

        self.frame_finfish.emit(frame, frame_len)
        self.display_frame(frame, frame_len)

    def display_frame(self, frame, length):
        self.framearea.clear()
        text = frame_fun.get_data_str_with_space(frame)
        self.framearea.setPlainText(text)
   
class ReadHistoryInterface(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pnlayout = QHBoxLayout()  # 使用水平布局
        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()
        self.pnInput.setFixedSize(400, 50)
        self.pnlayout.addWidget(self.pnlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.pnlayout.addWidget(self.pnInput, 1, Qt.AlignRight)

        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setFixedSize(400, 100)
        self.itemlayout.addWidget(self.itemlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.itemlayout.addWidget(self.itemInput, 1, Qt.AlignRight)

        self.starttimelayout = QHBoxLayout()  # 使用水平布局
        self.starttimelabel = QLabel('开始时间')
        self.starttimeInput = DateTimePicker()
        self.starttimelayout.addWidget(self.starttimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.starttimelayout.addWidget(self.starttimeInput, 1, Qt.AlignLeft)

        self.endtimelayout = QHBoxLayout()  # 使用水平布局
        self.endtimelabel = QLabel('结束时间')
        self.endtimeInput = DateTimePicker()
        self.endtimelayout.addWidget(self.endtimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.endtimelayout.addWidget(self.endtimeInput, 1, Qt.AlignLeft)

        self.datakindlayout = QHBoxLayout()  # 使用水平布局
        self.datakindlabel = QLabel('数据密度')
        self.datakindInput = ComboBox()
        self.datakindlayout.addWidget(self.datakindlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.datakindlayout.addWidget(self.datakindInput, 1, Qt.AlignLeft)

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.framearea = PlainTextEdit()
        self.framearea.setPlaceholderText("报文生成区...")
        self.framearea.setFixedHeight(200)

        self.sendbutton = PrimaryPushButton(self.tr('发送报文'))
        self.sendbutton.clicked.connect(self.sendframe)

        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.pnlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.itemlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.starttimelayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.endtimelayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.datakindlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.button, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.framearea, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.sendbutton, 1)

        self.qvlayout.setContentsMargins(0,0,0,5)

        self.init_widget()
        StyleSheet.CUSTOM_INTERFACE.apply(self)

    def get_size(self):
        return self.qvlayout.sizeHint() + QSize(0, 50)
    def sendframe(self):
        text = self.framearea.toPlainText()
        signalBus.sendmessage.emit(text)
    def init_widget(self):
        # self.setFixedHeight(300)
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")
        self.itemInput.setPlaceholderText("使用英文','拆分,如05060100,05060101")
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        self.starttimeInput.setDateTime(current_date, current_time)

        data_kind = ["1分钟","5分钟","15分钟","30分钟","60分钟","1日","1月"]
        self.datakindInput.addItems(data_kind)
        self.datakindInput.setCurrentIndex(0)

        current_datetime = QDateTime()
        current_datetime.setDate(current_date)
        current_datetime.setTime(current_time)
        new_datetime = frame_fun.add_time_interval(current_datetime, self.datakindInput.currentIndex(), 1)

        self.endtimeInput.setDateTime(new_datetime.date(), new_datetime.time())
        self.button.clicked.connect(self.create_frame)
    def create_frame(self, frame):
        afn = 0x0d
        frame_len = 0
        frame = [0x00] * FramePos.POS_DATA.value
        input_text = self.pnInput.toPlainText()
        if input_text: 
            try:                                      
                point_array =  frame_fun.parse_meterpoint_input(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("测量点错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入测量点!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return

        item_array = []
        input_text = self.itemInput.toPlainText()
        if input_text:
            try:
                item_array = frame_fun.prase_item_by_input_text(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入数据标识!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        start_date, start_time = self.starttimeInput.getDateTime() 
        start_time_array = frame_fun.get_time_bcd_array(start_date, start_time)
        end_date, end_time = self.endtimeInput.getDateTime() 
        end_time_array = frame_fun.get_time_bcd_array(end_date, end_time)
        adress = [0xff] * 6  # Fix the initialization of adress
        msa = 0x10
        datakind = self.datakindInput.currentIndex() + 1
        frame_csg.init_frame(0x4a, afn, adress, msa, 0x60, frame)
        frame_len += FramePos.POS_DATA.value
        frame_len += frame_csg.add_point_and_item_and_time_to_frame(point_array, item_array, start_time_array[:6], end_time_array[:6],datakind,frame)
        frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
        frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

        self.frame_finfish.emit(frame, frame_len)
        self.display_frame(frame, frame_len)

    def display_frame(self, frame, length):
        self.framearea.clear()
        text = frame_fun.get_data_str_with_space(frame)
        self.framearea.setPlainText(text)

class ReadEventAlarmInterface(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, type, parent=None):
        super().__init__(parent=parent)
        self.type = type #1 告警类型 2事件类型
        self.pnlayout = QHBoxLayout()  # 使用水平布局
        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()
        self.pnInput.setFixedSize(400, 50)
        self.pnlayout.addWidget(self.pnlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.pnlayout.addWidget(self.pnInput, 1, Qt.AlignRight)

        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setFixedSize(400, 100)
        self.itemlayout.addWidget(self.itemlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.itemlayout.addWidget(self.itemInput, 1, Qt.AlignRight)

        self.starttimelayout = QHBoxLayout()  # 使用水平布局
        self.starttimelabel = QLabel('开始时间')
        self.starttimeInput = DateTimePicker()
        self.starttimelayout.addWidget(self.starttimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.starttimelayout.addWidget(self.starttimeInput, 1, Qt.AlignLeft)

        self.endtimelayout = QHBoxLayout()  # 使用水平布局
        self.endtimelabel = QLabel('结束时间')
        self.endtimeInput = DateTimePicker()
        self.endtimelayout.addWidget(self.endtimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.endtimelayout.addWidget(self.endtimeInput, 1, Qt.AlignLeft)

        self.radioWidget = QWidget()
        self.radioLayout = QHBoxLayout(self.radioWidget)
        self.radioLayout.setContentsMargins(2, 0, 0, 0)
        self.radioLayout.setSpacing(15)
        self.radioButton1 = RadioButton(self.tr('告警读取'), self.radioWidget)
        self.radioButton2 = RadioButton(self.tr('事件读取'), self.radioWidget)
        self.buttonGroup = QButtonGroup(self.radioWidget)
        self.buttonGroup.addButton(self.radioButton1, 1)
        self.buttonGroup.addButton(self.radioButton2, 2)
        self.radioLayout.addWidget(self.radioButton1)
        self.radioLayout.addWidget(self.radioButton2)
        self.radioButton1.click()
        self.readtypelayout = QHBoxLayout()  # 使用水平布局
        self.readtypelabel = QLabel('读取类型')
        self.readtypelayout.addWidget(self.readtypelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.readtypelayout.addWidget(self.radioWidget, 1, Qt.AlignLeft)

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.framearea = PlainTextEdit()
        self.framearea.setPlaceholderText("报文生成区...")
        self.framearea.setFixedHeight(200)

        self.sendbutton = PrimaryPushButton(self.tr('发送报文'))
        self.sendbutton.clicked.connect(self.sendframe)

        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.pnlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.itemlayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.starttimelayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.endtimelayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.readtypelayout, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.button, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.framearea, 1)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.sendbutton, 1)

        self.qvlayout.setContentsMargins(0,0,0,5)
        self.init_widget()
        StyleSheet.CUSTOM_INTERFACE.apply(self)

    def get_size(self):
        return self.qvlayout.sizeHint() + QSize(0, 50)

    def sendframe(self):
        text = self.framearea.toPlainText()
        signalBus.sendmessage.emit(text)
    def init_widget(self):
        # self.setFixedHeight(300)
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")
        self.itemInput.setPlaceholderText("使用英文','拆分,如05060100,05060101")
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        self.starttimeInput.setDateTime(current_date, current_time)

        current_datetime = QDateTime()
        current_datetime.setDate(current_date)
        current_datetime.setTime(current_time)
        new_datetime = frame_fun.add_time_interval(current_datetime, 3, 1)

        self.endtimeInput.setDateTime(new_datetime.date(), new_datetime.time())
        self.button.clicked.connect(self.create_frame)
     
    def create_frame(self, frame):
        selected_button = self.buttonGroup.checkedButton()
        selected_index = self.buttonGroup.id(selected_button)
        if selected_index == 1:
            afn = 0x13
        else:
            afn = 0x0e
        frame_len = 0
        frame = [0x00] * FramePos.POS_DATA.value
        input_text = self.pnInput.toPlainText()
        if input_text: 
            try:                                      
                point_array =  frame_fun.parse_meterpoint_input(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("测量点错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入测量点!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return

        item_array = []
        input_text = self.itemInput.toPlainText()
        if input_text:
            try:
                item_array = frame_fun.prase_item_by_input_text(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入数据标识!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        start_date, start_time = self.starttimeInput.getDateTime() 
        start_time_array = frame_fun.get_time_bcd_array(start_date, start_time)
        end_date, end_time = self.endtimeInput.getDateTime() 
        end_time_array = frame_fun.get_time_bcd_array(end_date, end_time)
        adress = [0xff] * 6  # Fix the initialization of adress
        msa = 0x10
        frame_csg.init_frame(0x4a, afn, adress, msa, 0x60, frame)
        frame_len += FramePos.POS_DATA.value
        frame_len += frame_csg.add_point_and_item_and_time_to_frame(point_array, item_array, start_time_array[:6], end_time_array[:6],None,frame)
        frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
        frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

        self.frame_finfish.emit(frame, frame_len)
        self.display_frame(frame, frame_len)

    def display_frame(self, frame, length):
        self.framearea.clear()
        text = frame_fun.get_data_str_with_space(frame)
        self.framearea.setPlainText(text)

class MeterTaskInterface(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.tasklayout = QHBoxLayout()  # 使用水平布局
        self.tasklabel = QLabel('表端任务号')
        self.tasklabel.setAlignment(Qt.AlignLeft)
        self.taskNumberInput = LineEdit()
        self.tasklayout.addWidget(self.tasklabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.tasklayout.addWidget(self.taskNumberInput, 1, Qt.AlignRight)

        self.validradioWidget = QWidget()
        self.validradioLayout = QHBoxLayout(self.validradioWidget)
        self.validradioLayout.setContentsMargins(2, 0, 0, 0)
        self.validradioLayout.setSpacing(15)
        self.validradioButton1 = RadioButton(self.tr('无效'), self.validradioWidget)
        self.validradioButton2 = RadioButton(self.tr('有效'), self.validradioWidget)
        self.validbuttonGroup = QButtonGroup(self.validradioWidget)
        self.validbuttonGroup.addButton(self.validradioButton1, 1)
        self.validbuttonGroup.addButton(self.validradioButton2, 2)
        self.validradioLayout.addWidget(self.validradioButton1)
        self.validradioLayout.addWidget(self.validradioButton2)
        self.validradioButton1.click()
        self.validreadtypelayout = QHBoxLayout()  # 使用水平布局
        self.validreadtypelabel = QLabel('有效性标志')
        self.validreadtypelayout.addWidget(self.validreadtypelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.validreadtypelayout.addWidget(self.validradioWidget, 1, Qt.AlignRight)

        self.reportbasetimelayout = QHBoxLayout()  # 使用水平布局
        self.reportbasetimelabel = QLabel('上报基准时间')
        self.reportbasetimeInput = DateTimePicker()
        self.reportbasetimelayout.addWidget(self.reportbasetimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.reportbasetimelayout.addWidget(self.reportbasetimeInput, 1, Qt.AlignRight)


        self.reportunitradioWidget = QWidget()
        self.reportunitradioLayout = QHBoxLayout(self.reportunitradioWidget)
        self.reportunitradioLayout.setContentsMargins(2, 0, 0, 0)
        self.reportunitradioLayout.setSpacing(15)
        self.reportunitradioButton1 = RadioButton(self.tr('分'), self.reportunitradioWidget)
        self.reportunitradioButton2 = RadioButton(self.tr('时'), self.reportunitradioWidget)
        self.reportunitradioButton3 = RadioButton(self.tr('日'), self.reportunitradioWidget)
        self.reportunitradioButton4 = RadioButton(self.tr('月'), self.reportunitradioWidget)
        self.reportunitbuttonGroup = QButtonGroup(self.reportunitradioWidget)
        self.reportunitbuttonGroup.addButton(self.reportunitradioButton1, 1)
        self.reportunitbuttonGroup.addButton(self.reportunitradioButton2, 2)
        self.reportunitbuttonGroup.addButton(self.reportunitradioButton3, 3)
        self.reportunitbuttonGroup.addButton(self.reportunitradioButton4, 4)
        self.reportunitradioLayout.addWidget(self.reportunitradioButton1)
        self.reportunitradioLayout.addWidget(self.reportunitradioButton2)
        self.reportunitradioLayout.addWidget(self.reportunitradioButton3)
        self.reportunitradioLayout.addWidget(self.reportunitradioButton4)
        self.reportunitradioButton1.click()
        self.reportunitreadtypelayout = QHBoxLayout()  # 使用水平布局
        self.reportunitreadtypelabel = QLabel('定时上报周期单位')
        self.reportunitreadtypelayout.addWidget(self.reportunitreadtypelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.reportunitreadtypelayout.addWidget(self.reportunitradioWidget, 1, Qt.AlignRight)

        self.reportcycleinput = QHBoxLayout()  # 使用水平布局
        self.reportcyclelabel = QLabel('定时上报周期')
        self.reportcyclelabel.setAlignment(Qt.AlignLeft)
        self.reportcycleInput = LineEdit()
        self.reportcycleinput.addWidget(self.reportcyclelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.reportcycleinput.addWidget(self.reportcycleInput, 1, Qt.AlignRight)

        self.tasktyperadioWidget = QWidget()
        self.tasktyperadioLayout = QHBoxLayout(self.tasktyperadioWidget)
        self.tasktyperadioLayout.setContentsMargins(2, 0, 0, 0)
        self.tasktyperadioLayout.setSpacing(15)
        self.tasktyperadioButton1 = RadioButton(self.tr('自描述格式组织数据'), self.tasktyperadioWidget)
        self.tasktyperadioButton2 = RadioButton(self.tr('任务定义的数据格式组织数据'), self.tasktyperadioWidget)
        self.tasktypebuttonGroup = QButtonGroup(self.tasktyperadioWidget)
        self.tasktypebuttonGroup.addButton(self.tasktyperadioButton1, 1)
        self.tasktypebuttonGroup.addButton(self.tasktyperadioButton2, 2)
        self.tasktyperadioLayout.addWidget(self.tasktyperadioButton1)
        self.tasktyperadioLayout.addWidget(self.tasktyperadioButton2)
        self.tasktyperadioButton1.click()
        self.tasktypereadtypelayout = QHBoxLayout()  # 使用水平布局
        self.tasktypereadtypelabel = QLabel('数据结构方式')
        self.tasktypereadtypelayout.addWidget(self.tasktypereadtypelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.tasktypereadtypelayout.addWidget(self.tasktyperadioWidget, 1, Qt.AlignRight)

        self.readtimelayout = QHBoxLayout()  # 使用水平布局
        self.readtimelabel = QLabel('采样基准时间')
        self.readtimeInput = DateTimePicker()
        self.readtimelayout.addWidget(self.readtimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.readtimelayout.addWidget(self.readtimeInput, 1, Qt.AlignRight)

        self.meterunitradioWidget = QWidget()
        self.meterunitradioLayout = QHBoxLayout(self.meterunitradioWidget)
        self.meterunitradioLayout.setContentsMargins(2, 0, 0, 0)
        self.meterunitradioLayout.setSpacing(15)
        self.meterunitradioButton1 = RadioButton(self.tr('分'), self.meterunitradioWidget)
        self.meterunitradioButton2 = RadioButton(self.tr('时'), self.meterunitradioWidget)
        self.meterunitradioButton3 = RadioButton(self.tr('日'), self.meterunitradioWidget)
        self.meterunitradioButton4 = RadioButton(self.tr('月'), self.meterunitradioWidget)
        self.meterunitbuttonGroup = QButtonGroup(self.meterunitradioWidget)
        self.meterunitbuttonGroup.addButton(self.meterunitradioButton1, 1)
        self.meterunitbuttonGroup.addButton(self.meterunitradioButton2, 2)
        self.meterunitbuttonGroup.addButton(self.meterunitradioButton3, 3)
        self.meterunitbuttonGroup.addButton(self.meterunitradioButton4, 4)
        self.meterunitradioLayout.addWidget(self.meterunitradioButton1)
        self.meterunitradioLayout.addWidget(self.meterunitradioButton2)
        self.meterunitradioLayout.addWidget(self.meterunitradioButton3)
        self.meterunitradioLayout.addWidget(self.meterunitradioButton4)
        self.meterunitradioButton1.click()
        self.meterunitreadtypelayout = QHBoxLayout()  # 使用水平布局
        self.meterunitreadtypelabel = QLabel('表端定时采样周期基本单位')
        self.meterunitreadtypelayout.addWidget(self.meterunitreadtypelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.meterunitreadtypelayout.addWidget(self.meterunitradioWidget, 1, Qt.AlignRight)


        self.metercyclelayout = QHBoxLayout()  # 使用水平布局
        self.metercyclelabel = QLabel('表端定时采样周期')
        self.metercyclelabel.setAlignment(Qt.AlignLeft)
        self.metercycleInput = LineEdit()
        self.metercyclelayout.addWidget(self.metercyclelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.metercyclelayout.addWidget(self.metercycleInput, 1, Qt.AlignRight)

        self.datafreqlayout = QHBoxLayout()  # 使用水平布局
        self.datafreqlabel = QLabel('数据抽取倍率')
        self.datafreqlabel.setAlignment(Qt.AlignLeft)
        self.datafreqInput = LineEdit()
        self.datafreqlayout.addWidget(self.datafreqlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.datafreqlayout.addWidget(self.datafreqInput, 1, Qt.AlignRight)

        self.ertureadtimelayout = QHBoxLayout()  # 使用水平布局
        self.ertureadtimelabel = QLabel('终端查询基准时间')
        self.ertureadtimeInput = DateTimePicker()
        self.ertureadtimelayout.addWidget(self.ertureadtimelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.ertureadtimelayout.addWidget(self.ertureadtimeInput, 1, Qt.AlignRight)

        self.ertureadunitradioWidget = QWidget()
        self.ertureadunitradioLayout = QHBoxLayout(self.ertureadunitradioWidget)
        self.ertureadunitradioLayout.setContentsMargins(2, 0, 0, 0)
        self.ertureadunitradioLayout.setSpacing(15)
        self.ertureadunitradioButton1 = RadioButton(self.tr('分'), self.ertureadunitradioWidget)
        self.ertureadunitradioButton2 = RadioButton(self.tr('时'), self.ertureadunitradioWidget)
        self.ertureadunitradioButton3 = RadioButton(self.tr('日'), self.ertureadunitradioWidget)
        self.ertureadunitradioButton4 = RadioButton(self.tr('月'), self.ertureadunitradioWidget)
        self.ertureadunitbuttonGroup = QButtonGroup(self.ertureadunitradioWidget)
        self.ertureadunitbuttonGroup.addButton(self.ertureadunitradioButton1, 1)
        self.ertureadunitbuttonGroup.addButton(self.ertureadunitradioButton2, 2)
        self.ertureadunitbuttonGroup.addButton(self.ertureadunitradioButton3, 3)
        self.ertureadunitbuttonGroup.addButton(self.ertureadunitradioButton4, 4)
        self.ertureadunitradioLayout.addWidget(self.ertureadunitradioButton1)
        self.ertureadunitradioLayout.addWidget(self.ertureadunitradioButton2)
        self.ertureadunitradioLayout.addWidget(self.ertureadunitradioButton3)
        self.ertureadunitradioLayout.addWidget(self.ertureadunitradioButton4)
        self.ertureadunitradioButton1.click()
        self.ertureadunitreadtypelayout = QHBoxLayout()  # 使用水平布局
        self.ertureadunitreadtypelabel = QLabel('终端定时查询周期单位')
        self.ertureadunitreadtypelayout.addWidget(self.ertureadunitreadtypelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.ertureadunitreadtypelayout.addWidget(self.ertureadunitradioWidget, 1, Qt.AlignRight)

        self.ertureadcyclelayout = QHBoxLayout()  # 使用水平布局
        self.ertureadcyclelabel = QLabel('终端定时查询周期')
        self.ertureadcyclelabel.setAlignment(Qt.AlignLeft)
        self.ertureadcycleInput = LineEdit()
        self.ertureadcyclelayout.addWidget(self.ertureadcyclelabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.ertureadcyclelayout.addWidget(self.ertureadcycleInput, 1, Qt.AlignRight)

        self.taskexeccountlayout = QHBoxLayout()  # 使用水平布局
        self.taskexeccountlabel = QLabel('执行次数')
        self.taskexeccountlabel.setAlignment(Qt.AlignLeft)
        self.taskexeccountInput = LineEdit()
        self.taskexeccountlayout.addWidget(self.taskexeccountlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.taskexeccountlayout.addWidget(self.taskexeccountInput, 1, Qt.AlignRight)

        self.pnlayout = QHBoxLayout()  # 使用水平布局
        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()
        self.pnInput.setFixedSize(400, 50)
        self.pnlayout.addWidget(self.pnlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.pnlayout.addWidget(self.pnInput, 1, Qt.AlignRight)

        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setFixedSize(400, 100)
        self.itemlayout.addWidget(self.itemlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.itemlayout.addWidget(self.itemInput, 1, Qt.AlignRight)

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.framearea = PlainTextEdit(self)
        self.framearea.setPlaceholderText("报文生成区...")
        self.framearea.setFixedHeight(200)
        self.sendbutton = PrimaryPushButton(self.tr('发送报文'))
        self.sendbutton.clicked.connect(self.sendframe)

        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.tasklayout)
        self.qvlayout.addLayout(self.validreadtypelayout)
        self.qvlayout.addLayout(self.reportbasetimelayout)
        self.qvlayout.addLayout(self.reportunitreadtypelayout)
        self.qvlayout.addLayout(self.reportcycleinput)
        self.qvlayout.addLayout(self.tasktypereadtypelayout)
        self.qvlayout.addLayout(self.readtimelayout)
        self.qvlayout.addLayout(self.meterunitreadtypelayout)
        self.qvlayout.addLayout(self.metercyclelayout)
        self.qvlayout.addLayout(self.datafreqlayout)
        self.qvlayout.addLayout(self.ertureadtimelayout)
        self.qvlayout.addLayout(self.ertureadunitreadtypelayout)
        self.qvlayout.addLayout(self.ertureadcyclelayout)
        self.qvlayout.addLayout(self.taskexeccountlayout)
        self.qvlayout.addLayout(self.pnlayout)
        self.qvlayout.addLayout(self.itemlayout)
        self.qvlayout.addWidget(self.button)
        self.qvlayout.addWidget(self.framearea)
        self.qvlayout.addWidget(self.sendbutton)
        self.qvlayout.setContentsMargins(0,0,0,5)

        self.init_widget()
    def init_widget(self):
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")
        self.itemInput.setPlaceholderText("使用英文','拆分,如05060100,05060101")
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        self.reportbasetimeInput.setDateTime(current_date, current_time)
        self.readtimeInput.setDateTime(current_date, current_time)
        self.ertureadtimeInput.setDateTime(current_date, current_time)
        self.button.clicked.connect(self.create_frame)
        StyleSheet.CUSTOM_INTERFACE.apply(self)

    def sendframe(self):
        text = self.framearea.toPlainText()
        signalBus.sendmessage.emit(text)
    def get_size(self):
        return self.qvlayout.sizeHint() + QSize(0, 50)
    def create_frame(self, frame):
        afn = 0x04
        frame_len = 0
        frame = [0x00] * FramePos.POS_DATA.value

        adress = [0xff] * 6  # Fix the initialization of adress
        msa = 0x10
        frame_csg.init_frame(0x4a, afn, adress, msa, 0x60, frame)
        frame_len += FramePos.POS_DATA.value

        frame.extend([0x00,0x00])
        frame_len += 2

        input_text = self.taskNumberInput.text()
        if input_text: 
            try:                                      
                task_item = 0xE0001500 + int(input_text, 10)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("任务号错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入任务号!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        frame_len += frame_fun.item_to_di(task_item, frame)

        #有效性标志
        selected_button = self.validbuttonGroup.checkedButton()
        selected_index = self.validbuttonGroup.id(selected_button)
        frame.append(selected_index - 1)
        frame_len += 1
        #上报基准时间
        time_date, time_time = self.reportbasetimeInput.getDateTime()
        time_array = frame_fun.get_time_bcd_array(time_date, time_time)
        frame.extend(time_array[1:6][::-1])
        frame_len += 5
        
        #定时上报周期单位
        selected_button = self.reportunitbuttonGroup.checkedButton()
        selected_index = self.reportunitbuttonGroup.id(selected_button)
        frame.append(selected_index - 1)
        frame_len += 1

        #定时上报周期
        data = self.reportcycleInput.text()
        if data is not None and data != "":
            try:
                cycle = int(data, 10)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("定时上报周期错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入定时上报周期!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
            
        frame.append(cycle)
        frame_len += 1

        #数据结构方式
        selected_button = self.tasktypebuttonGroup.checkedButton()
        selected_index = self.tasktypebuttonGroup.id(selected_button)
        frame.append(selected_index - 1)
        frame_len += 1

        #采样基准时间
        time_date, time_time = self.readtimeInput.getDateTime()
        time_array = frame_fun.get_time_bcd_array(time_date, time_time)
        frame.extend(time_array[1:6][::-1])
        frame_len += 5

        #采样周期单位
        selected_button = self.meterunitbuttonGroup.checkedButton()
        selected_index = self.meterunitbuttonGroup.id(selected_button)
        frame.append(selected_index - 1)
        frame_len += 1

        #采样周期
        data = self.metercycleInput.text()
        if data is not None and data != "":
            try:
                cycle = int(data, 10)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("表端定时采样周期错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入表端定时采样周期周期!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        
        frame.append(cycle)
        frame_len += 1

        #数据抽取倍率
        data = self.datafreqInput.text()
        if data is not None and data != "":
            try:
                cycle = int(data, 10)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据抽取倍率错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入数据抽取倍率!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        
        frame.append(cycle)
        frame_len += 1

        #终端查询基准时间
        time_date, time_time = self.ertureadtimeInput.getDateTime()
        time_array = frame_fun.get_time_bcd_array(time_date, time_time)
        frame.extend(time_array[1:6][::-1])
        frame_len += 5

        #终端定时查询周期单位
        selected_button = self.ertureadunitbuttonGroup.checkedButton()
        selected_index = self.ertureadunitbuttonGroup.id(selected_button)
        frame.append(selected_index - 1)
        frame_len += 1

        #终端定时查询周期
        data = self.ertureadcycleInput.text()
        if data is not None and data != "":
            try:
                cycle = int(data, 10)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("终端定时查询周期错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入终端定时查询周期!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        
        frame.append(cycle)
        frame_len += 1

        #执行次数
        data = self.taskexeccountInput.text()
        if data is not None and data != "":
            try:
                cycle = int(data, 10)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("执行次数错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入执行次数!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        
        cycle_array = frame_fun.int16_to_bcd(cycle)
        frame.extend(cycle_array)
        frame_len += 2

        #测量点组
        input_text = self.pnInput.toPlainText()
        if input_text: 
            try:                                      
                point_array =  frame_fun.parse_meterpoint_input(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("测量点错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入测量点!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        
        pn_frame = []
        count, pos = frame_csg.add_point_array_to_frame(pn_frame, point_array)
        frame.append(count)
        frame.extend(pn_frame)
        frame_len += pos + 1

        #数据标识组
        item_array = []
        input_text = self.itemInput.toPlainText()
        if input_text:
            try:
                item_array = frame_fun.prase_item_by_input_text(input_text)
            except Exception as e:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
        else:
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("请输入数据标识!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
    
        frame.append(len(item_array))
        frame_len += 1
        frame_len += frame_csg.add_item_array_to_frame(frame, item_array)

        frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
        frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

        self.frame_finfish.emit(frame, frame_len)
        self.display_frame(frame, frame_len)

    def display_frame(self, frame, length):
        self.framearea.clear()
        text = frame_fun.get_data_str_with_space(frame)
        self.framearea.setPlainText(text)

class FrameInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.curwidget = None
        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.paramInterface = ParamFrameInterface(self)
        self.curdataInterface = ReadCurInterface(self)
        self.historyDataInterface = ReadHistoryInterface(self)
        self.readAlarmInterface = ReadEventAlarmInterface(type=1, parent=self)
        self.metertaskinterface = MeterTaskInterface(self)

        # add items to pivot
        self.addSubInterface(self.paramInterface, 'paramInterface', self.tr('参数类'))
        self.addSubInterface(self.curdataInterface, 'curdataInterface', self.tr('当前数据类'))
        self.addSubInterface(self.historyDataInterface, 'histotyInterface', self.tr('历史数据类'))
        self.addSubInterface(self.readAlarmInterface, 'readAlarmInterface', self.tr('读取报警类'))
        self.addSubInterface(self.metertaskinterface, 'metertaskinterface', self.tr('表端任务类'))
        
        # self.button = PrimaryPushButton(self.tr('生成报文'))
        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget, 0, Qt.AlignLeft | Qt.AlignTop)
        # self.vBoxLayout.addStretch(1)
        self.vBoxLayout.setSpacing(5)
        # self.vBoxLayout.addWidget(self.button)  
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.paramInterface)
        self.onCurrentIndexChanged(0)
        self.pivot.setCurrentItem(self.paramInterface.objectName())
        qrouter.setDefaultRouteKey(self.stackedWidget, self.paramInterface.objectName())

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        qrouter.push(self.stackedWidget, widget.objectName())
        self.setFixedHeight(widget.get_size().height() + self.vBoxLayout.spacing())

class CustomFrameInterface(FrameInterface):

    Nav = SegmentedWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout.removeWidget(self.pivot)
        self.vBoxLayout.insertWidget(0,self.pivot)

class CustomFrame(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="自定义报文",
            parent=parent
        )
        self.setObjectName('custominterface')

        self.customframe = CustomFrameInterface(self)
        self.vBoxLayout.addWidget(self.customframe)