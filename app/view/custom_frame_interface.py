from PyQt5.QtCore import Qt, QEasingCurve,pyqtSignal
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, TabBar, CheckBox, ComboBox,
                            TabCloseButtonDisplayMode, BodyLabel, SpinBox, BreadcrumbBar,LineEdit,SwitchButton,PrimaryPushButton,PlainTextEdit)
from PyQt5.QtGui import QFont
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from ..plugins.frame_csg import FramePos
from ..plugins import frame_fun,frame_csg
class ParamFrameInterface(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pnlayout = QHBoxLayout()  # 使用水平布局
        self.pnlabel = QLabel('测量点')
        self.pnlabel.setFont(QFont("Courier New", 12))
        self.pnInput = LineEdit()
        self.pnInput.setMaximumWidth(200)
        self.pnlayout.addWidget(self.pnlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.pnlayout.addWidget(self.pnInput, 1, Qt.AlignLeft)

        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemlabel = QLabel('数据标识')
        self.itemlabel.setFont(QFont("Courier New", 12))
        self.itemInput = LineEdit()
        self.itemInput.setMaximumWidth(200)
        self.itemlayout.addWidget(self.itemlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.itemlayout.addWidget(self.itemInput, 1, Qt.AlignLeft)

        self.datalayout = QHBoxLayout()  # 使用水平布局
        self.datalabel = QLabel('数据内容')
        self.datalabel.setFont(QFont("Courier New", 12))
        self.dataInput = LineEdit()
        self.dataInput.setFixedWidth(200)
        self.datalayout.addWidget(self.datalabel, 0,Qt.AlignLeft)
        self.datalayout.addWidget(self.dataInput, 1, Qt.AlignLeft)

        self.switchButton = SwitchButton(self.tr('设置'))
        self.switchButton.setChecked(True)
        self.switchButton.setText(self.tr('设置'))
        self.switchButton.checkedChanged.connect(self.onSwitchCheckedChanged)

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.button.clicked.connect(self.create_frame)

        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.pnlayout)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.itemlayout)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addLayout(self.datalayout)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.switchButton)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.button)

        self.qvlayout.setContentsMargins(0,0,0,0)
        self.qvlayout.setSpacing(2)
    
    def onSwitchCheckedChanged(self, isChecked):
        if isChecked:
            self.switchButton.setText(self.tr('设置'))
        else:
            self.switchButton.setText(self.tr('读取'))

    def create_frame(self, frame):
        if self.switchButton.isChecked():
            afn = 0x04
        else:
            afn = 0x0A
        item_dic = {}
        frame_len = 0
        frame = [0x00] * FramePos.POS_DATA.value
        input_text = self.pnInput.text()
        if input_text:                                       
              point_array =  frame_fun.parse_meterpoint_input(input_text)
        else:
            self.pnInput.setStyleSheet("border: 2px solid red;")
            raise ValueError("需要输入测量点")

        item = self.itemInput.text()
        if item is not None and item != '':
            item = int(item, 16)
        data = self.dataInput.text()
        if data is not None and data!= '':
            if self.switchButton.isChecked():
                item_dic[item] = data
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


    

class FrameInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.songInterface = ParamFrameInterface(self)
        self.albumInterface = ParamFrameInterface(self)
        self.artistInterface = ParamFrameInterface(self)

        self.framearea = PlainTextEdit(self)
        # add items to pivot
        self.addSubInterface(self.songInterface, 'paramInterface', self.tr('参数类'))
        self.addSubInterface(self.albumInterface, 'curdataInterface', self.tr('当前数据类'))
        self.addSubInterface(self.artistInterface, 'histotyInterface', self.tr('历史数据类'))

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget, 0, Qt.AlignLeft | Qt.AlignTop)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.addWidget(self.framearea,1)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.songInterface)
        self.pivot.setCurrentItem(self.songInterface.objectName())
        self.songInterface.frame_finfish.connect(self.display_frame)

        qrouter.setDefaultRouteKey(self.stackedWidget, self.songInterface.objectName())

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

    def display_frame(self, frame, length):
        text = frame_fun.get_data_str_with_space(frame)
        self.framearea.setPlainText(text)

class CustomFrameInterface(FrameInterface):

    Nav = SegmentedWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout.removeWidget(self.pivot)
        self.vBoxLayout.insertWidget(0, self.pivot)

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