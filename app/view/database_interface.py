from PyQt5.QtCore import Qt, QEasingCurve,pyqtSignal,QSize
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, TextEdit, CheckBox, ComboBox,
                            TabCloseButtonDisplayMode, BodyLabel, SpinBox, BreadcrumbBar,InfoBarPosition,InfoBar,PrimaryPushButton,PlainTextEdit)
from PyQt5.QtGui import QFont, QResizeEvent
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from ..plugins.frame_csg import FramePos
from ..plugins import protocol
from ..plugins.frame_fun import FrameFun as frame_fun
from .analysic_interface import CustomTreeWidgetItem,CustomTreeWidget
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..plugins.MeterTask import MeterTask

class ReadTask(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.item_position = {}

        self.taskParamlayout = QHBoxLayout()  # 使用水平布局
        self.taskParamlabel = QLabel('任务内容')
        self.taskParamInput = PlainTextEdit()
        self.taskParamButton = PrimaryPushButton(self.tr('确定'))
        self.taskParamlayout.addWidget(self.taskParamlabel)
        self.taskParamlayout.addSpacing(5)
        self.taskParamlayout.addWidget(self.taskParamInput)
        self.taskParamlayout.addSpacing(5)
        self.taskParamlayout.addWidget(self.taskParamButton)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.taskParamInput.setSizePolicy(size_policy)

        self.tree_widget = CustomTreeWidget()
        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.taskParamlayout)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.tree_widget, 8)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tree_widget.setSizePolicy(size_policy)
        self.qvlayout.setContentsMargins(0, 0, 0, 0)

        self.taskParamButton.clicked.connect(self.taskParamButtonClicked)
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
        item_str = frame_fun.to_hex_string_with_space(data_content)
        self.taskParamInput.setPlainText(item_str.upper())
        protocol.frame_fun.globregion = cfg.get(cfg.Region)
        meter_task = MeterTask()
        meter_task.analysic_meter_task(data_content, alalysic_result, 0)
        self.tree_widget.create_tree(None, alalysic_result, self.item_position)
        self.tree_widget.expandAll()

class CustomItem(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.item_position = {}

        self.itemlabel = QLabel('数据标识')
        self.itemInput = TextEdit()
        self.itemlayout = QHBoxLayout()
        # self.itemlabel.setAlignment(Qt.AlignLeft)
        self.itemInput.setAlignment(Qt.AlignLeft)
        self.itemlayout.addWidget(self.itemlabel)
        self.itemlayout.addSpacing(5)
        self.itemlayout.addWidget(self.itemInput, 1 ,Qt.AlignLeft)
        self.itemInput.setFixedSize(200,35)

        self.contentlabel = QLabel('数据内容')
        self.contentInput = PlainTextEdit()
        self.contentlayout = QHBoxLayout()  # 使用水平布局
        self.contentlayout.addWidget(self.contentlabel)
        self.contentlayout.addSpacing(5)
        self.contentlayout.addWidget(self.contentInput)

        self.Button = PrimaryPushButton(self.tr('解析'))
        self.Button.setFixedWidth(100)

        self.infolayout = QVBoxLayout()
        self.infolayout.addLayout(self.itemlayout)
        self.infolayout.addSpacing(5)
        self.infolayout.addLayout(self.contentlayout)
        self.infolayout.addSpacing(5)
        self.infolayout.addWidget(self.Button,1 ,Qt.AlignCenter)

        self.tree_widget = CustomTreeWidget()
        self.qvlayout = QVBoxLayout(self)  # 使用垂直布局
        self.qvlayout.addLayout(self.infolayout)
        self.qvlayout.addSpacing(5)
        self.qvlayout.addWidget(self.tree_widget, 8)
        # size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.tree_widget.setSizePolicy(size_policy)
        self.qvlayout.setContentsMargins(0, 0, 0, 0)

        self.Button.clicked.connect(self.taskParamButtonClicked)
    def taskParamButtonClicked(self):
        try:
            item = self.itemInput.toPlainText()
            data = self.contentInput.toPlainText()
            alalysic_result = []
            self.tree_widget.clear()
            self.tree_widget.last_item = None
            if item == '':
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识不能为空"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
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
            template_element = frame_fun.get_config_xml(item, frame_fun.globalprotocol,frame_fun.globregion)
            if template_element is None:
                InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("数据标识不存在"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
                return
            show_data = protocol.parse_data_item(template_element, data_content, 0, 0)
            frame_fun.prase_data_with_config(show_data, False, alalysic_result)
            sub_result = []
            reverse_item = item.replace(' ', '').replace('\n', '')
            item_list = [int(reverse_item[i:i + 2], 16) for i in range(0, len(reverse_item), 2)]
            item_str = frame_fun.to_hex_string_reverse_with_space(item_list)
            name = template_element.find('name').text
            dis_data_identifier = "数据标识编码：" + f"[{reverse_item.upper()}]" + "-" + name
            result_str = f"数据标识[{reverse_item.upper()}]数据内容：" + frame_fun.get_data_str_reverser(data_content)
            frame_fun.add_data(sub_result, f"数据标识编码DI",item_str,dis_data_identifier,[])
            frame_fun.add_data(sub_result, f"数据标识内容",frame_fun.get_data_str_with_space(data_content),result_str,[],alalysic_result)
            self.tree_widget.create_tree(None, sub_result, self.item_position)
            self.tree_widget.expandAll()
        except Exception as e:
            print(e)
            InfoBar.error(
                title=self.tr('错误'),
                content=self.tr("解析失败"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
class FrameInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        # self.taskterface = ReadTask()
        self.itemterface = CustomItem()
        # add items to pivot

        self.addSubInterface(self.itemterface, 'itemterface', self.tr('数据解析'))
        # self.addSubInterface(self.taskterface, 'taskterface', self.tr('任务配置'))

        self.vBoxLayout.addWidget(self.pivot, 1)
        self.vBoxLayout.addWidget(self.stackedWidget, 9)
        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.itemterface)
        self.pivot.setCurrentItem(self.itemterface.objectName())

        qrouter.setDefaultRouteKey(self.stackedWidget, self.itemterface.objectName())


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
        self.qhlayout = QHBoxLayout(self)
        self.customframe = CustomDataBaseInterface()
        self.qhlayout.addWidget(self.customframe)
