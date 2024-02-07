from PyQt5.QtCore import Qt, QEasingCurve,pyqtSignal,QSize
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, TabBar, CheckBox, ComboBox,
                            TabCloseButtonDisplayMode, BodyLabel, SpinBox, BreadcrumbBar,InfoBarPosition,InfoBar,PrimaryPushButton,PlainTextEdit)
from PyQt5.QtGui import QFont
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from ..plugins.frame_csg import FramePos
from ..plugins import frame_fun,protocol
from .analysic_interface import CustomTreeWidgetItem,CustomTreeWidget
from ..common.config import cfg
from ..common.signal_bus import signalBus

class ParamTaskParam(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.item_position = {}

        self.taskParamlayout = QHBoxLayout()  # 使用水平布局
        self.taskParamlabel = QLabel('任务内容')
        self.taskParamInput = PlainTextEdit()
        self.taskParamButton = PrimaryPushButton(self.tr('确定'))
        self.taskParamlayout.addWidget(self.taskParamlabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.taskParamlayout.addWidget(self.taskParamInput, 1)
        self.taskParamlayout.addWidget(self.taskParamButton, 2, Qt.AlignRight)

        self.tree_widget = CustomTreeWidget()
        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.taskParamlayout)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.tree_widget, 8)
        self.qvlayout.setContentsMargins(0, 0, 0, 0)
        # 设置大小策略和伸展因子
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.taskParamInput.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.taskParamButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.taskParamlayout.setStretch(0, 0)
        self.taskParamlayout.setStretch(1, 1)
        self.taskParamlayout.setStretch(2, 0)

        self.tree_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.qvlayout.setStretch(0, 0)
        self.qvlayout.setStretch(1, 8)  # 设置伸展因子为 8

        self.taskParamButton.clicked.connect(self.taskParamButtonClicked)
        signalBus.windowschange.connect(self.update_size)

    def update_size(self, size: QSize):
        self.setFixedSize(size)
        self.tree_widget.header().resizeSection(0,int(size.width() * 0.35))
        self.tree_widget.header().resizeSection(1,int(size.width() * 0.25))   
    def taskParamButtonClicked(self):
        data = self.taskParamInput.toPlainText()
        alalysic_result = []
        self.tree_widget.clear()
        self.tree_widget.last_item = None
        if data == '':
            InfoBar.warning(
            title=self.tr('告警'),
            content=self.tr("数据内容不能为空"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
            return
        cleaned_string = data.replace(' ', '').replace('\n', '')
        data_content = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
        protocol.frame_fun.globregion = cfg.get(cfg.Region)
        frame_fun.globalprotocol = "CSG13"
        print(data_content)
        template_element = frame_fun.get_template_element("BASETASK", frame_fun.globalprotocol,frame_fun.globregion)
        show_data = protocol.parse_splitByLength_data(template_element, data_content, 0, 0)
        frame_fun.prase_data_with_config(show_data, False, alalysic_result)
        self.tree_widget.create_tree(None, alalysic_result, self.item_position)
        self.tree_widget.expandAll()


class FrameInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.songInterface = ParamTaskParam(self)
        # add items to pivot
        self.addSubInterface(self.songInterface, 'paramInterface', self.tr('任务参数'))

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget, 0, Qt.AlignLeft | Qt.AlignTop)

        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.songInterface)
        self.pivot.setCurrentItem(self.songInterface.objectName())

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

class CustomDataBaseInterface(FrameInterface):

    Nav = SegmentedWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout.removeWidget(self.pivot)
        self.vBoxLayout.insertWidget(0, self.pivot)

class DataBaseInterface(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="数据库数据",
            parent=parent
        )
        self.setObjectName('CustomDataBaseInterface')

        self.customframe = CustomDataBaseInterface(self)
        self.vBoxLayout.addWidget(self.customframe)
