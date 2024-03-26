import sys
import os
import json
from PyQt5.QtWidgets import QFileDialog,QSizePolicy, QSplitter, QTreeWidgetItem, QVBoxLayout, QWidget, QTreeWidget, QLabel, QTextEdit,QHBoxLayout,QFrame
from PyQt5.QtCore import Qt, QTextCodec,QSize,pyqtSignal
from PyQt5.QtGui import QTextOption,QColor
from qfluentwidgets import InfoBadge,PrimaryPushButton,CheckBox,TextEdit,TextWrap,ScrollArea,SmoothScrollDelegate
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from ..common.signal_bus import signalBus
from ..common.config import cfg


class InterfaceInfoWidget(ScrollArea):
    resizeRequested = pyqtSignal(QSize)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.layout = QVBoxLayout(self)
        self.cur_item = None
        self.scroll_area = SmoothScrollDelegate(self)
        nameqhlayout = QHBoxLayout()
        self.name_label = QLabel("消息名称:")
        self.name_content = QLabel()
        nameqhlayout.addWidget(self.name_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        nameqhlayout.addWidget(self.name_content, 1, Qt.AlignLeft)
        nameqhlayout.setContentsMargins(0,5,10,0)
        nameqhlayout.setStretch(1, 1)

        descriplaout = QHBoxLayout()
        self.description_label = QLabel("消息描述:")
        self.description_content = QLabel()
        descriplaout.addWidget(self.description_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        descriplaout.addWidget(self.description_content, 1, Qt.AlignLeft)
        descriplaout.setStretch(1, 1)
        descriplaout.setContentsMargins(0,5,10,0)
        # self.description_content.setStyleSheet("background-color: blue;")
        self.description_content.setWordWrap(True)

        inputqvlayout = QVBoxLayout()
        self.input_label = QLabel("消息请求:")
        self.input_editor = TextEdit()
        inputqvlayout.addWidget(self.input_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        inputqvlayout.addWidget(self.input_editor, 1, Qt.AlignLeft)
        inputqvlayout.setContentsMargins(0,5,10,0)
        inputqvlayout.setStretch(1, 1)

        outputqvlayout = QVBoxLayout()
        self.output_label = QLabel("消息响应:")
        self.output_editor = TextEdit()
        outputqvlayout.addWidget(self.output_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        outputqvlayout.addWidget(self.output_editor, 1, Qt.AlignLeft)
        outputqvlayout.setStretch(1, 1)
        outputqvlayout.setContentsMargins(0,5,10,0)

        self.layout.addLayout(nameqhlayout)
        self.layout.addLayout(descriplaout)
        self.layout.addLayout(inputqvlayout)
        self.layout.addLayout(outputqvlayout)

        self.layout.setContentsMargins(0, 0, 20, 0)

        # 在 InterfaceInfoWidget 的 __init__ 方法的最后添加
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.input_editor.textChanged.connect(self.on_input_editor_text_changed)
        # 在适当的位置检查其他控件的大小策略，并设置为 Expanding
        self.name_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.description_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.input_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.output_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.init_size()
    def init_size(self):
        self.description_content.setFixedWidth(int(self.width())- 100)
        self.name_content.setFixedWidth(int(self.width())- 100)
        self.output_editor.setFixedWidth(int(self.width()))
        self.input_editor.setFixedWidth(int(self.width()))
    def connect_to_parent_splitter(self, splitter:QSplitter):
        splitter.splitterMoved.connect(self.init_size)

    def update_interface_info(self, item):
        self.name_content.setText(item.data(1, Qt.UserRole))
        self.description_content.setText(item.data(2, Qt.UserRole))
        self.cur_item = item
        self.input_editor.setPlainText(item.data(3, Qt.UserRole))
        self.output_editor.setPlainText(item.data(4, Qt.UserRole))
    def on_input_editor_text_changed(self):
        text = self.input_editor.toPlainText()
        if self.cur_item and text != '':
            self.cur_item.setData(3, Qt.UserRole, text)
    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.init_size()
        
class MessageConfig(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.config_file_path = None
        # 添加打开文件夹按钮和显示文件夹路径的标签
        self.open_folder_button = PrimaryPushButton("打开文件夹", self)
        self.folder_path_label = QLabel("配置文件：", self)
        
        # 连接按钮的点击信号到槽函数
        self.open_folder_button.clicked.connect(self.open_folder_dialog)
        self.open_folder_button.setFixedWidth(100)
        # 添加布局管理器，水平排列按钮和标签
        button_label_layout = QHBoxLayout()
        button_label_layout.addWidget(self.folder_path_label)
        button_label_layout.addWidget(self.open_folder_button)
        button_label_layout.setContentsMargins(0, 0, 0, 5)

        # 创建拆分器和左侧树形控件
        self.splitter = QSplitter(self)
        self.left_tree = QTreeWidget()
        self.scrollDelegate = SmoothScrollDelegate(self.left_tree)
        # 右侧的 InterfaceInfoWidget，这里使用 QTextEdit 模拟
        self.right_widget = InterfaceInfoWidget()
        self.right_widget.connect_to_parent_splitter(self.splitter)
        # 将左侧树形控件和右侧的 QTextEdit 添加到拆分器中
        self.splitter.addWidget(self.left_tree)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setOrientation(1)

        self.send_button = PrimaryPushButton("发送消息", self)
        self.send_label = QLabel("发送结果：暂不支持😟", self)
        
        # 连接按钮的点击信号到槽函数
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setFixedWidth(100)
        # 添加布局管理器，水平排列按钮和标签
        send_layout = QHBoxLayout()
        send_layout.addWidget(self.send_label)
        send_layout.addWidget(self.send_button)
        send_layout.setContentsMargins(0, 5, 0, 5)

        # 创建垂直布局管理器，包括按钮和标签的水平布局和拆分器
        self.central_layout = QVBoxLayout(self)
        self.central_layout.addLayout(button_label_layout)
        self.central_layout.addWidget(self.splitter)
        self.central_layout.addLayout(send_layout)
        self.central_layout.setContentsMargins(10, 5, 0, 0)

        # 设置左侧树形控件的隐藏表头
        self.left_tree.header().hide()

        self.init_widget()
        # 设置样式表
        StyleSheet.CUSTOM_INTERFACE.apply(self)
        # signalBus.windowschange.connect(self.update_size)
        
        # 设置固定大小 
    # def resizeEvent(self, e):
    #     super().resizeEvent(e)
    #     # self.toolBar.resize(self.width(), self.toolBar.height())
    #     self.update_size(self.size())
    # def update_size(self, size:QSize):
    #     if size.height() > self.size().height():
    #         self.setFixedHeight(size.height())
    def init_widget(self):
        initial_pos = 50
        self.splitter.setSizes([initial_pos, self.splitter.width() - initial_pos])
        self.config_file_path = cfg.get(cfg.messageFolder)
        self.folder_path_label.setText(f"当前文件夹路径：{self.config_file_path}")
        self.load_config_files_from_folder(self.config_file_path)
 
    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            # 更新文件夹路径标签
            self.config_file_path = folder_path
            cfg.set(cfg.messageFolder, folder_path)
            self.folder_path_label.setText(f"当前文件夹路径：{folder_path}")
            # 加载文件夹中的 dbc 文件
            self.load_config_files_from_folder(folder_path)

    def load_config_files_from_folder(self, folder_path):
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"The specified folder path does not exist: {folder_path}")
        self.left_tree.clear()
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                self.load_config_file(file_path)

    def load_config_file(self, filename):
        # 设置文本编码为UTF-8
        QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))

        with open(filename, "r", encoding="utf-8") as file:
            interface_data = json.load(file)

        # Extract filename without extension
        app_name = interface_data.get("name", "")

        self.left_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.left_tree.setSelectionBehavior(QTreeWidget.SelectItems)

        rootlayout = QHBoxLayout()
        rootwidget = QWidget()
        rootwidget.setLayout(rootlayout)
        rootlabel = QLabel(app_name)
        root_item = QTreeWidgetItem(self.left_tree.invisibleRootItem())
        root_checkbox = CheckBox()
        root_checkbox.setChecked(True)  # 初始状态为选中
        rootlayout.addWidget(root_checkbox)
        rootlayout.addWidget(rootlabel)
        root_checkbox.stateChanged.connect(self.on_checkbox_state_changed)
        rootwidget.setFixedWidth(rootlayout.sizeHint().width())
        self.left_tree.setItemWidget(root_item, 0, rootwidget)
        root_item.setData(0, Qt.UserRole, root_checkbox)
        for interface in interface_data.get("interface", []):
            curitem = QTreeWidgetItem(root_item)

            # 创建一个 QVBoxLayout 用于垂直排列 "name"、"type"、复选框和状态标识的控件
            layout = QHBoxLayout()

            # 创建一个 QHBoxLayout 用于水平排列 "name"、"type"、复选框
            horizontal_layout = QHBoxLayout()

            checkbox = CheckBox()
            checkbox.setChecked(True)  # 初始状态为选中
            checkbox.stateChanged.connect(self.on_checkbox_state_changed)
            horizontal_layout.addWidget(checkbox)
            curitem.setData(0, Qt.UserRole, checkbox)
            horizontal_layout.addSpacing(2)
            name_label = QLabel(interface.get("name", ""))
            name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            horizontal_layout.addWidget(name_label)
            
            typetag = InfoBadge.success(interface.get("type", "Unknown Type"))
            typetag.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            horizontal_layout.addWidget(typetag)

            # 设置水平布局的外边距
            horizontal_layout.setContentsMargins(10, 0, 10, 0)

            # 添加水平布局到垂直布局
            layout.addLayout(horizontal_layout)

            # 添加用于表示消息状态的标签
            status_label = QLabel()  # 初始状态为"Pending"
            status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            layout.addWidget(status_label, 0, Qt.AlignRight)

            # 设置垂直布局的外边距
            layout.setContentsMargins(0, 0, 0, 10)

            widget_container = QWidget()
            widget_container.setLayout(layout)
            self.left_tree.setItemWidget(curitem, 0, widget_container)

            input_text = json.dumps(interface.get("input", ""), indent=2, ensure_ascii=False)
            output_text = json.dumps(interface.get("output", ""), indent=2, ensure_ascii=False)
            # curitem.setData(1, Qt.DisplayRole, json.dumps(interface, indent=2, ensure_ascii=False))
            name = interface.get("name", "")
            description = interface.get("description", "")
            curitem.setData(1, Qt.UserRole, name)
            curitem.setData(2, Qt.UserRole, description)
            curitem.setData(3, Qt.UserRole, input_text)
            curitem.setData(4, Qt.UserRole, output_text)

        self.left_tree.expandAll()
        self.left_tree.clicked.connect(self.on_tree_item_clicked)

    def on_tree_item_clicked(self, index):
        item = self.left_tree.itemFromIndex(index)
        if item is not None:
            self.right_widget.update_interface_info(item)    
    def on_checkbox_state_changed(self, state):
        sender_checkbox = self.sender()
        if sender_checkbox:
            item = self.find_item_by_checkbox(sender_checkbox)
            if item:
                for i in range(item.childCount()):
                    child_item = item.child(i)
                    checkbox = child_item.data(0, Qt.UserRole)
                    if checkbox:
                        status = True if state == Qt.Checked else False
                        checkbox.setChecked(status)
    def send_message(self):
        print("send_message")
        item_array  = self.find_item_with_checkbox_state(True)
        for item in item_array:
            print(item.data(1, Qt.UserRole))
            print(item.data(2, Qt.UserRole))
            print(item.data(3, Qt.UserRole))
            print(item.data(4, Qt.UserRole))

    def find_item_with_checkbox_state(self, checkbox_state):
        item_array = []
        for i in range(self.left_tree.topLevelItemCount()):
            item = self.left_tree.topLevelItem(i)
            box = item.data(0, Qt.UserRole)
            if box.isChecked() == checkbox_state:
                    # Add all children to the array
                array = self.get_all_children(item)
                item_array.extend(array)
            else:
                array = self.find_child_with_checkbox_state(item, checkbox_state)
                item_array.extend(array)
        return item_array

    def find_child_with_checkbox_state(self, parent_item, checkbox_state):
        child_item_array = []
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            box = child_item.data(0, Qt.UserRole)
            if box.isChecked() == checkbox_state:
                child_item_array.append(child_item)
                # 递归检查子节点的子节点
            array = self.find_child_with_checkbox_state(child_item, checkbox_state)
            if array:
                child_item_array.extend(array)
        return child_item_array

    def get_all_children(self, parent_item):
        child_item_array = []
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            child_item_array.append(child_item)
            # Recursively add all children of each child
            array = self.get_all_children(child_item)
            if array:
                child_item_array.extend(array)
        return child_item_array
    def find_item_by_checkbox(self, checkbox):
        for i in range(self.left_tree.topLevelItemCount()):
            item = self.left_tree.topLevelItem(i)
            box = item.data(0, Qt.UserRole)
            if box == checkbox:
                return item
            else:
                self.has_child_with_checkbox(item, checkbox)
        return None
    def has_child_with_checkbox(self, parent_item, checkbox):
        for i in range(parent_item.childCount()):
            child_item = parent_item.child(i)
            box = child_item.data(0, Qt.UserRole)
            if box == checkbox:
                return True
            # 递归检查子节点的子节点
            if self.has_child_with_checkbox(child_item, checkbox):
                return True
        return False

class AppMessageInterface(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="APP消息接口",
            parent=parent
        )
        self.setObjectName('AppMessageInterface')
        self.qhlayout = QHBoxLayout(self)
        self.customframe = MessageConfig()
        self.qhlayout.addWidget(self.customframe)