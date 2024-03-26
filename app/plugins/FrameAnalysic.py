from dis import Positions
from token import STAR
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QToolBar,QComboBox,QApplication,QHBoxLayout,QVBoxLayout,QButtonGroup,QLabel,QPushButton,QRadioButton,QLabel,QVBoxLayout,QLineEdit,QDateTimeEdit,QTextEdit,QGridLayout,QMenu
import config
import os
from PyQt5.QtGui import QIcon
import protocol
import frame_csg, subsocket
from ..plugins.frame_fun import FrameFun as frame_fun
from ..plugins.frame_fun import CustomMessageBox
from screeninfo import get_monitors
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator

try:
  import win32con
except ImportError:
  win32con = None

class CustomTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent, text_list):
        self.data = text_list  # Store the associated data
        super(CustomTreeWidgetItem, self).__init__(parent, text_list)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)

class CustomDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(CustomDelegate, self).__init__(parent)
        self.hovered_item = None

    def paint(self, painter, option, index):
    
        # 移除选中状态
        option.state &= ~QtWidgets .QStyle.State_Selected
    
        super().paint(painter, option, index)


class CustomTreeWidget(QtWidgets.QTreeWidget):
    custom_signal = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem)  # Define a custom signal
    def __init__(self):
        super().__init__()
        self.last_item = None
        self.last_column = 0
        self.setColumnCount(3)
        self.setHeaderLabels(["帧域","数据","说明"])
        self.setMouseTracking(False)
        self.setSelectionMode(QtWidgets .QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets .QAbstractItemView.SelectItems)
        self.delegate=CustomDelegate(parent=self)
        self.setItemDelegate(self.delegate)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.header().setSectionResizeMode(2,QtWidgets.QHeaderView.Stretch)
        self.itemClicked.connect(self.onItemClicked)

    def onItemClicked(self, item):

        column = self.currentColumn()
        self.old_color = item.background(column)
        self.old_brush = item.foreground(column)

        for i in range(self.columnCount()):
            if i != column:
                backbrush = QtGui.QBrush(QtGui.QColor(51, 134, 255)) 
            else:
                backbrush = QtGui.QBrush(QtGui.QColor(225, 0, 65)) 

            forcebrush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
            item.setBackground(i,backbrush)
            item.setForeground(i,forcebrush)
            if self.last_item != None:
                self.last_item.setBackground(i,self.old_color)
                self.last_item.setForeground(i,self.old_brush)

        self.last_item = item
        self.last_column = column
        self.custom_signal.emit(item)

    def mousePressEvent(self, event):
    # 在这里处理CustomTreeWidget的鼠标事件
        super().mousePressEvent(event)  
    def create_tree(self,parent_item, data, item_positions):
        if parent_item is None:
            parent_item = self.invisibleRootItem()
        for item_data in data:
            frame = item_data.get("帧域", "")
            data_value = item_data.get("数据", "")
            description = item_data.get("说明", "")
            position = item_data.get("位置")
            column_texts = [frame, data_value, description]

            item = CustomTreeWidgetItem(parent_item, column_texts)
            item_positions[id(item)] = position
            parent_item.addChild(item)
            child_items = item_data.get("子项", [])
            if child_items:
                self.create_tree(item, child_items,item_positions)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.item_position = {}
        self.frame_len  = 0
        self.tools_window = None
        self.current_screen_number = 0xFF
        self.setWindowTitle("报文解析")
        self.update_windows_size()
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.input_text = QtWidgets.QPlainTextEdit(self)
        self.input_text.setPlaceholderText("请输入报文..")
        height = int(self.height() * 0.25)
        self.input_text.setFixedHeight(height)
        layout.addWidget(self.input_text)
        self.tree_widget = CustomTreeWidget()
        self.tree_widget.header().resizeSection(0,int(self.width() * 0.35))
        self.tree_widget.header().resizeSection(1,int(self.width() * 0.25))
        layout.addWidget(self.tree_widget)
        self.input_text.textChanged.connect(self.display_tree)
        self.tree_widget.custom_signal.connect(self.highlight_text)
        self.create_menu_bar()

        self.highlight_format = QtGui.QTextCharFormat()
        self.highlight_format.setBackground(QtGui.QColor(51, 134, 255))  # 蓝色背景
        self.highlight_format.setForeground(QtGui.QColor(255, 255, 255))  # 白色字体

        self.install_event_filters()

    def highlight_text(self, item):
        self.input_text.textChanged.disconnect(self.display_tree)
        # Find the target_data in the input_text and highlight it
        cursor = self.input_text.textCursor()

        # Clear any previous selections
        cursor.clearSelection()
        cursor = self.input_text.cursorForPosition(QtCore.QPoint(0, 0))
        cursor.clearSelection()
        self.input_text.setTextCursor(cursor)
        # Remove previous highlights
        cursor.select(QtGui.QTextCursor.Document) 
        cursor.setCharFormat(QtGui.QTextCharFormat())
        cursor.clearSelection()
        positions = self.item_position.get(id(item))
        self.input_text.setTextCursor(self.input_text.textCursor())
        if positions:
            start = positions[0]
            if start < 0:
                start = self.frame_len - abs(start)
            end = positions[1]
            if end <= 0:
                end = self.frame_len - abs(end)

            length = end - start
            
            length = length * 2 + (length - 1)

            length = int(length)
            if start > 0:
                 start = start * 2 + start

            start = int(start)
            cursor.setPosition(start)
            cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, length)
            cursor.setCharFormat(self.highlight_format)
        self.input_text.setTextCursor(self.input_text.textCursor())
        self.input_text.textChanged.connect(self.display_tree)

    def moveEvent(self, event):
        # 当窗口位置发生变化时，更新显示器信息
        if not self.isMaximized() and not self.isMinimized():
            self.update_windows_size()
        super().moveEvent(event)

    def update_windows_size(self):
        # 获取主窗口所在的显示器索引
        screen_number = QApplication.desktop().screenNumber(self)

        if self.current_screen_number != screen_number:
            # 获取显示器信息
            self.current_screen_number = screen_number
            screen = QApplication.desktop().screen(screen_number)
            self.resize(int(screen.size().width() * 0.8), int(screen.size().height() * 0.6))

    def display_tree(self):
        self.tree_widget.clear()
        input_text = self.input_text.toPlainText()
        # Process the input text and generate the tree data
        show_data = []
        # Add tree data using add data function
        try:
            frame = bytearray.fromhex(input_text)
            self.frame_len = len(frame)
            self.tree_widget.last_item = None
            formatted_frame = ''
            hex_str = input_text.replace(' ', '')
            for i in range(0, len(hex_str), 2):
                formatted_frame += hex_str[i:i + 2] + ' '
            self.input_text.textChanged.disconnect(self.display_tree)
            self.input_text.setPlainText(formatted_frame)
            cursor = self.input_text.textCursor()

            # Clear any previous selections
            cursor.clearSelection()
            # 将字符串拆分为每两个字符
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]

            if protocol.is_dlt645_frame(frame):
                protocol.FRAME_645.Analysis_645_fram_by_afn(frame, show_data,0)
            elif frame_csg.is_csg_frame(frame):
                frame_csg.Analysis_csg_frame_by_afn(frame,show_data)
                print("is csg frame")
            self.tree_widget.create_tree(None, show_data, self.item_position)

            self.tree_widget.expandAll()
            self.input_text.textChanged.connect(self.display_tree)
        except ValueError:
            CustomMessageBox("告警",'输入的字符中包含非十六进制字符！')
            self.input_text.textChanged.disconnect(self.display_tree)
                # 保存当前文本内容
            temp_text = self.input_text.toPlainText()
            # 清除输入框内容
            self.input_text.clear()
            # 将保存的文本内容设置回输入框
            self.input_text.setPlainText(temp_text)
            self.input_text.textChanged.connect(self.display_tree)


    def install_event_filters(self):
        def recursive_install(parent):
            for child in parent.findChildren(QtCore.QObject):
              child.installEventFilter(self)
              recursive_install(child)
        recursive_install(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                 if self.tools_window is not None:
                    self.tools_window.toggle_transparency()
        return super().eventFilter(obj, event)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu=menu_bar.addMenu("文件")
        exit_action=QtWidgets.QAction("退出",self)
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        file_menu.addAction(exit_action)

        edit_menu=menu_bar.addMenu("配置")
        clear_action=QtWidgets.QAction("清空输入",self)
        clear_action.triggered.connect(self.clear_input)
        config_action=QtWidgets.QAction("连接配置",self)
        config_action.triggered.connect(self.connect_tools)
        edit_menu.addAction(clear_action)
        edit_menu.addAction(config_action)


        tool_menu=menu_bar.addMenu("报文生成")
        csg13frame=QtWidgets.QAction("南网13",self)
        csg13frame.triggered.connect(self.frame_tools)
        meter_task=QtWidgets.QAction("表端任务方案配置",self)
        meter_task.triggered.connect(self.meter_task_config)
        ctrl_frame=QtWidgets.QAction("负荷控制",self)
        ctrl_frame.triggered.connect(self.multi_ctrl_tools)
        phase_frame=QtWidgets.QAction("相位识别参数",self)
        phase_frame.triggered.connect(self.phase_tools)
        tool_menu.addAction(csg13frame)
        tool_menu.addAction(meter_task)
        tool_menu.addAction(ctrl_frame)
        tool_menu.addAction(phase_frame)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir,":/gallery/images/seting.png")
        config_action=QtWidgets.QAction(QtGui.QIcon(icon_path),"配置数据项",self)
        config_action.triggered.connect(self.open_config_dialog)
        edit_menu.addAction(config_action)

        main_menu = menu_bar.addMenu("解析配置")
        
        sub_menu = QMenu("省份", self) 
        self.csgaction = QtWidgets.QAction("南网", self)
        self.yunaction = QtWidgets.QAction("云南", self)
        self.gudaction = QtWidgets.QAction("广东", self)
        self.shzaction = QtWidgets.QAction("深圳", self)
        self.guxaction = QtWidgets.QAction("广西", self)
        self.guzaction = QtWidgets.QAction("贵州", self)
        self.hanaction = QtWidgets.QAction("海南", self)

        sub_menu.addAction(self.csgaction)
        sub_menu.addAction(self.yunaction)
        sub_menu.addAction(self.gudaction)
        sub_menu.addAction(self.shzaction)
        sub_menu.addAction(self.guxaction)
        sub_menu.addAction(self.guzaction)
        sub_menu.addAction(self.hanaction)
        
        main_menu.addMenu(sub_menu)
        
        self.csgaction.triggered.connect(self.onItemClicked)
        self.yunaction.triggered.connect(self.onItemClicked)
        self.gudaction.triggered.connect(self.onItemClicked)
        self.shzaction.triggered.connect(self.onItemClicked)
        self.guxaction.triggered.connect(self.onItemClicked)
        self.guzaction.triggered.connect(self.onItemClicked)
        self.hanaction.triggered.connect(self.onItemClicked)

        self.csgaction.setCheckable(True)
        self.yunaction.setCheckable(True)
        self.gudaction.setCheckable(True)
        self.shzaction.setCheckable(True)
        self.guxaction.setCheckable(True)
        self.guzaction.setCheckable(True)
        self.hanaction.setCheckable(True)
        self.lastsender = self.csgaction
        frame_fun.globregion = "南网"
        self.csgaction.setChecked(True)
    def onItemClicked(self):
        sender = self.sender()
        if sender == self.csgaction:
            frame_fun.globregion = "南网"
            self.csgaction.setChecked(True)
        elif sender == self.yunaction:
            frame_fun.globregion = "云南"
            self.yunaction.setChecked(True)
        elif sender == self.gudaction: 
            frame_fun.globregion = "广东"
            self.gudaction.setChecked(True)
        elif sender == self.shzaction:
            frame_fun.globregion = "深圳"
            self.shzaction.setChecked(True)
        elif sender == self.guxaction:
            frame_fun.globregion = "广西"
            self.guxaction.setChecked(True)
        elif sender == self.guzaction: 
            frame_fun.globregion = "贵州"
            self.guzaction.setChecked(True)
        elif sender == self.hanaction:
            frame_fun.globregion = "海南"
            self.hanaction.setChecked(True)

        if sender != self.lastsender:
            self.lastsender.setChecked(False)
            self.lastsender = sender

    def clear_input(self):
        self.input_text.clear()
        self.tree_widget.clear()
    def open_config_dialog(self):
        config_window = ConfigMainWindow(self)
        config_window.show()

    def frame_tools(self):
        self.tools_window = FrameToolsWindow(self)
        self.tools_window.show()
    def meter_task_config(self):
        self.task_config = TASKWindow(self)
        self.task_config.show()
    def multi_ctrl_tools(self):
        self.ctrl_tools = CtrlWindow(self)
        self.ctrl_tools.show()
    def phase_tools(self):
        self.phase_windows = PhaseWindow(self)
        self.phase_windows.show()
    def connect_tools(self):
        self.connConfig = ConfigWindow(self)
        self.connConfig.show()

class CustomToolBar(QToolBar):
    def __init__(self,parent=None):
        super().__init__(parent)
    
    def contextMenuEvent(self,event):
        pass

class ConfigMainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)

        self.setWindowTitle("配置数据")
        tree_widget = config.ConfigCustomTreeWidget(self)
        self.setCentralWidget(tree_widget)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir,":/gallery/images/.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))
        self.resize(830,300)
        #Create toolbar
        toolbar = CustomToolBar(self)
        self.addToolBar(toolbar)
        # Create Load button
        save_icon_path = os.path.join(current_dir,":/gallery/images/上传.png")
        save_button = QtWidgets.QAction(QtGui.QIcon(save_icon_path),"保存",self)
        save_button.triggered.connect(tree_widget.save_config)
        toolbar.addAction(save_button)
        # Create Load button
        load_icon_path = os.path.join(current_dir,":/gallery/images/下载.png")
        load_button = QtWidgets.QAction(QtGui.QIcon(load_icon_path),"读取",self)
        load_button.triggered.connect(tree_widget.read_config)
        toolbar.addAction(load_button)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        # Create Protocol dropdown selector
        protocol_label=QtWidgets.QLabel("协议：",self)
        toolbar.addWidget(protocol_label)
        protocol_selector = QtWidgets.QComboBox(self)
        protocal=['DLT/645-2007','DLT/645-1997','南网13','模块协议']
        protocol_selector.addItems(protocal)
        toolbar.addWidget(protocol_selector)
        protocol_selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)


        # Create spacer item
        spacer = QtWidgets.QWidget(self)
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Preferred)
        spacer.setFixedWidth(10)#Adjust the width to your desired spacing
        toolbar.addWidget(spacer)
        # Create Province dropdown selector
        province_label=QtWidgets.QLabel("省份：",self)
        toolbar.addWidget(province_label)
        province_selector = QtWidgets.QComboBox(self)
        regoin=['南网','云南','广东','深圳','广西','贵州','海南']
        province_selector.addItems(regoin)
        toolbar.addWidget(province_selector)
        province_selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

class FrameToolsWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, flags=QtCore.Qt.Window)

        self.setWindowTitle("报文工具")
        self.resize(830, 300)
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        splitter = QtWidgets.QSplitter(self.central_widget)

        self.input_text = QtWidgets.QPlainTextEdit(splitter)
        self.input_text.setPlaceholderText("请输入报文..")
        self.input_text.setMinimumWidth(200)

        # 添加转换按钮
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, ":/gallery/images/transe.png")
        self.convert_button = QtWidgets.QPushButton()
        self.convert_button.setIcon(QtGui.QIcon(icon_path))
        self.convert_button.clicked.connect(self.convert_text)
        splitter.addWidget(self.convert_button)

        self.result_text = QtWidgets.QPlainTextEdit(splitter)
        self.result_text.setPlaceholderText("生成报文..")
        self.result_text.setMinimumWidth(200)

        layout = QtWidgets.QVBoxLayout(self.central_widget)
        layout.addWidget(splitter)

        self.install_event_filters()

    def install_event_filters(self):
        self.installEventFilter(self)
        def recursive_install(parent):
            for child in parent.findChildren(QtCore.QObject):
              child.installEventFilter(self)
              recursive_install(child)
        recursive_install(self)

    #def nativeEvent(self, eventType, message):
    #    ret = super().nativeEvent(eventType, message)
    #    if eventType == 'windows_generic_MSG':
    #        msg = ctypes.wintypes.MSG.from_address(message.__int__())
    #        if msg.message == win32con.WM_NCLBUTTONDOWN:
    #            # 处理标题栏点击事件
    #            self.setWindowOpacity(1.0)
    #            return True
    #    return ret == None


    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.setWindowOpacity(1.0)
        return super().eventFilter(obj, event)

    def toggle_transparency(self):
        self.setWindowOpacity(0.2)  # 设置透明度为0.8或其他值

    def convert_text(self):
        #self.tree_widget.clear()
        input_text = self.input_text.toPlainText()
        try:
            frame = bytearray.fromhex(input_text)
            formatted_frame = ''
            hex_str = input_text.replace(' ', '')
            for i in range(0, len(hex_str), 2):
                formatted_frame += hex_str[i:i + 2] + ' '

            # Clear any previous selections
            print(self.input_text.toPlainText())
            # 将字符串拆分为每两个字符
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
            if len(frame) < 6:
                raise ValueError("输入的帧长度太短，至少应该有 6 个字节")
            length = len(frame[6:-2])
            frame[1] = length & 0X00ff
            frame[2] = length >> 8
            frame[3] = length & 0X00ff
            frame[4] = length >> 8

            caculate_cs = frame_fun.caculate_cs(frame[6:-2])
            frame[-2] = caculate_cs
            frame[-1] = 0x16

            print(frame)
            self.result_text.clear()
            self.result_text.setPlainText(frame_fun.to_hex_string_with_space(frame))

        except ValueError:
            print("输入的字符中包含非十六进制字符。")

class TASKWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, flags=QtCore.Qt.Window)

        self.setWindowTitle("任务配置")
        self.resize(830, 300)
        self.qvlayout = QVBoxLayout()

        self.taskinput = QHBoxLayout()  # 使用水平布局
        self.tasklabel = QLabel('表端任务号：')
        self.tasklabel.setAlignment(QtCore.Qt.AlignLeft)
        self.taskNumberInput = QLineEdit()
        self.taskinput.addWidget(self.tasklabel)
        self.taskinput.addWidget(self.taskNumberInput)
        self.taskNumberInput.textChanged.connect(self.update_color)

        self.taskStatusLayout = QHBoxLayout()  # 使用水平布局
        self.task_statusLabel = QLabel('有效性标志：')
        self.task_statusLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.taskStatusButtGroup = QButtonGroup()
        # 创建单选按钮
        self.taskInvalidButton = QRadioButton('无效')
        self.taskEffectButton = QRadioButton('有效')

        # 添加单选按钮到按钮组
        self.taskStatusButtGroup.addButton(self.taskInvalidButton, 1)
        self.taskStatusButtGroup.addButton(self.taskEffectButton, 2)

        # 设置默认选中状态
        self.taskInvalidButton.setChecked(True)

        # 添加控件到水平布局
        self.taskStatusLayout.addWidget(self.task_statusLabel)
        self.taskStatusLayout.addWidget(self.taskInvalidButton)
        self.taskStatusLayout.addWidget(self.taskEffectButton)

        self.reportTImelayout = QHBoxLayout() 
        self.reportTImebaseLabel = QLabel('上报基准时间：')
        self.reportTImebaseLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.time_input = QDateTimeEdit()
        self.reportTImelayout.addWidget(self.reportTImebaseLabel)
        self.reportTImelayout.addWidget(self.time_input)

        self.reportunitlayout = QHBoxLayout()  # 使用水平布局
        self.reportunitlabel = QLabel('定时上报周期单位：')
        self.reportunitbutton = QButtonGroup()
        # 创建单选按钮
        self.reportunit_Minutes = QRadioButton('分')
        self.reportunit_Hour = QRadioButton('时')
        self.reportunit_day = QRadioButton('日')
        self.reportunit_Mouth = QRadioButton('月')

        # 添加单选按钮到按钮组
        self.reportunitbutton.addButton(self.reportunit_Minutes, 1)
        self.reportunitbutton.addButton(self.reportunit_Hour, 2)
        self.reportunitbutton.addButton(self.reportunit_day, 3)
        self.reportunitbutton.addButton(self.reportunit_Mouth, 4)

        # 设置默认选中状态
        self.reportunit_Minutes.setChecked(True)

        # 添加控件到水平布局
        self.reportunitlayout.addWidget(self.reportunitlabel)
        self.reportunitlayout.addWidget(self.reportunit_Minutes)
        self.reportunitlayout.addWidget(self.reportunit_Hour)
        self.reportunitlayout.addWidget(self.reportunit_day)
        self.reportunitlayout.addWidget(self.reportunit_Mouth)


        self.reportcyclelayout = QHBoxLayout()  # 使用水平布局
        self.reportcycleLabel = QLabel('定时上报周期：')
        self.reportcycleinput = QLineEdit()
        self.reportcyclelayout.addWidget(self.reportcycleLabel)
        self.reportcyclelayout.addWidget(self.reportcycleinput)
        self.reportcycleinput.textChanged.connect(self.update_color)


        self.tasktypelayout = QHBoxLayout()  # 使用水平布局
        self.tasktypelabel = QLabel('数据结构方式：')
        self.tasktypebutt = QButtonGroup()
        self.tasktypenormal = QRadioButton('自描述格式组织数据')
        self.tasktypecustom = QRadioButton('任务定义的数据格式组织数据')
        self.tasktypebutt.addButton(self.tasktypenormal, 1)
        self.tasktypebutt.addButton(self.tasktypecustom, 2)
        self.tasktypenormal.setChecked(True)
        self.tasktypelayout.addWidget(self.tasktypelabel)
        self.tasktypelayout.addWidget(self.tasktypenormal)
        self.tasktypelayout.addWidget(self.tasktypecustom)


        self.readTImelayout = QHBoxLayout() 
        self.readTImebaseLabel = QLabel('采样基准时间')
        self.readtime_input = QDateTimeEdit()
        self.readTImelayout.addWidget(self.readTImebaseLabel)
        self.readTImelayout.addWidget(self.readtime_input)

        self.meterunitlayout = QHBoxLayout()  # 使用水平布局
        self.meterunitlabel = QLabel('表端定时采样周期基本单位：')
        self.meterunitbutton = QButtonGroup()
        # 创建单选按钮
        self.meterunit_Minutes = QRadioButton('分')
        self.meterunit_Hour = QRadioButton('时')
        self.meterunit_day = QRadioButton('日')
        self.meterunit_Mouth = QRadioButton('月')

        # 添加单选按钮到按钮组
        self.meterunitbutton.addButton(self.meterunit_Minutes, 1)
        self.meterunitbutton.addButton(self.meterunit_Hour, 2)
        self.meterunitbutton.addButton(self.meterunit_day, 3)
        self.meterunitbutton.addButton(self.meterunit_Mouth, 4)

        # 设置默认选中状态
        self.meterunit_Minutes.setChecked(True)

        # 添加控件到水平布局
        self.meterunitlayout.addWidget(self.meterunitlabel)
        self.meterunitlayout.addWidget(self.meterunit_Minutes)
        self.meterunitlayout.addWidget(self.meterunit_Hour)
        self.meterunitlayout.addWidget(self.meterunit_day)
        self.meterunitlayout.addWidget(self.meterunit_Mouth)


        self.metercyclelayout = QHBoxLayout()  # 使用水平布局
        self.metercycleLabel = QLabel('表端定时采样周期：')
        self.metercycleinput = QLineEdit()
        self.metercyclelayout.addWidget(self.metercycleLabel)
        self.metercyclelayout.addWidget(self.metercycleinput)
        self.metercycleinput.textChanged.connect(self.update_color)


        self.datafreqLayout = QHBoxLayout()  # 使用水平布局
        self.datafreqLabel = QLabel('数据抽取倍率：')
        self.datafreqinput = QLineEdit()
        self.datafreqLayout.addWidget(self.datafreqLabel)
        self.datafreqLayout.addWidget(self.datafreqinput)
        self.datafreqinput.textChanged.connect(self.update_color)
    
        self.ertureadmelayout = QHBoxLayout() 
        self.ertureadmebaseLabel = QLabel('终端查询基准时间：')
        self.ertureadme_input = QDateTimeEdit()
        self.ertureadmelayout.addWidget(self.ertureadmebaseLabel)
        self.ertureadmelayout.addWidget(self.ertureadme_input)

        self.ertureadunitlayout = QHBoxLayout()  # 使用水平布局
        self.ertureadunitlabel = QLabel('终端定时查询周期单位：')
        self.ertureadunitbutton = QButtonGroup()
        # 创建单选按钮
        self.ertureadunit_Minutes = QRadioButton('分')
        self.ertureadunit_Hour = QRadioButton('时')
        self.ertureadunit_day = QRadioButton('日')
        self.ertureadunit_Mouth = QRadioButton('月')

        # 添加单选按钮到按钮组
        self.ertureadunitbutton.addButton(self.ertureadunit_Minutes, 1)
        self.ertureadunitbutton.addButton(self.ertureadunit_Hour, 2)
        self.ertureadunitbutton.addButton(self.ertureadunit_day, 3)
        self.ertureadunitbutton.addButton(self.ertureadunit_Mouth, 4)

        # 设置默认选中状态
        self.ertureadunit_Minutes.setChecked(True)

        # 添加控件到水平布局
        self.ertureadunitlayout.addWidget(self.ertureadunitlabel)
        self.ertureadunitlayout.addWidget(self.ertureadunit_Minutes)
        self.ertureadunitlayout.addWidget(self.ertureadunit_Hour)
        self.ertureadunitlayout.addWidget(self.ertureadunit_day)
        self.ertureadunitlayout.addWidget(self.ertureadunit_Mouth)


        self.ertureadcyclelayout = QHBoxLayout()  # 使用水平布局
        self.ertureadcycleLabel = QLabel('终端定时查询周期：')
        self.ertureadcycleinput = QLineEdit()
        self.ertureadcyclelayout.addWidget(self.ertureadcycleLabel)
        self.ertureadcyclelayout.addWidget(self.ertureadcycleinput)
        self.ertureadcycleinput.textChanged.connect(self.update_color)


        self.taskexeccountlayout = QHBoxLayout()  # 使用水平布局
        self.taskexeccountLabel = QLabel('执行次数：')
        self.taskexeccountinput = QLineEdit()
        self.taskexeccountlayout.addWidget(self.taskexeccountLabel)
        self.taskexeccountlayout.addWidget(self.taskexeccountinput)
        self.taskexeccountinput.textChanged.connect(self.update_color)


        self.meterpointlayout = QHBoxLayout()  # 使用水平布局
        self.meterpointLabel = QLabel('测量点：')
        self.meterpointinput = QLineEdit()
        self.meterpointlayout.addWidget(self.meterpointLabel)
        self.meterpointlayout.addWidget(self.meterpointinput)
        self.meterpointinput.textChanged.connect(self.update_color)


        self.itemlayout = QHBoxLayout()  # 使用水平布局
        self.itemLabel = QLabel('数据标识:')
        self.iteminput = QTextEdit()
        self.itemlayout.addWidget(self.itemLabel)
        self.itemlayout.addWidget(self.iteminput)
        self.iteminput.textChanged.connect(self.update_color)


        self.qvlayout.addLayout(self.taskinput)
        self.qvlayout.addLayout(self.taskStatusLayout)
        self.qvlayout.addLayout(self.reportTImelayout)
        self.qvlayout.addLayout(self.reportunitlayout)
        self.qvlayout.addLayout(self.reportcyclelayout)
        self.qvlayout.addLayout(self.tasktypelayout)
        self.qvlayout.addLayout(self.readTImelayout)
        self.qvlayout.addLayout(self.meterunitlayout)
        self.qvlayout.addLayout(self.metercyclelayout)
        self.qvlayout.addLayout(self.datafreqLayout)
        self.qvlayout.addLayout(self.ertureadmelayout)
        self.qvlayout.addLayout(self.ertureadunitlayout)
        self.qvlayout.addLayout(self.ertureadcyclelayout)
        self.qvlayout.addLayout(self.taskexeccountlayout)
        self.qvlayout.addLayout(self.meterpointlayout)
        self.qvlayout.addLayout(self.itemlayout)

        # 创建一个分割器
        splitter = QtWidgets.QSplitter(self)

        # 左边部分，使用 QVBoxLayout
        left_widget = QtWidgets.QWidget(self)
        left_layout = QVBoxLayout()
        left_layout.addLayout(self.qvlayout)  # 将 self.qvlayout 添加到左边
        left_widget.setLayout(left_layout)

        # 右边部分，使用 QVBoxLayout
        right_widget = QtWidgets.QWidget(self)
        right_layout = QHBoxLayout()

        # 添加一个转换按钮
        convert_button = QtWidgets.QPushButton("转换")
        convert_button.clicked.connect(self.convert_text)  # 连接转换按钮的槽函数
        right_layout.addWidget(convert_button)

        
        # 添加一个文本框
        self.text_edit = QtWidgets.QTextEdit()
        right_layout.addWidget(self.text_edit)


        right_widget.setLayout(right_layout)

        # 将左右部分添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割器的大小策略，让左右部分可以自由调整大小
        sidth = int(self.width() / 2)
        splitter.setSizes([sidth, sidth])

        # 将分割器设置为中央部件
        self.setCentralWidget(splitter)


        self.install_event_filters()

    def install_event_filters(self):
        self.installEventFilter(self)
        def recursive_install(parent):
            for child in parent.findChildren(QtCore.QObject):
              child.installEventFilter(self)
              recursive_install(child)
        recursive_install(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.setWindowOpacity(1.0)
        return super().eventFilter(obj, event)

    def toggle_transparency(self):
        self.setWindowOpacity(0.2)  # 设置透明度为0.8或其他值

    def update_color(self):
        # Get the sender widget that triggered the signal
        text_input = self.sender()

        if text_input:
            # Get the text from the sender widget
            try:
                input_text = text_input.text()
            except:
                input_text = text_input.toPlainText()

            # Rest of your code to check and update the border color goes here
            if input_text:
                current_border_color = text_input.styleSheet()
                if "border: 2px solid red;" in current_border_color:
                    text_input.setStyleSheet("")
            else:
                text_input.setStyleSheet("border: 2px solid red;")



    def convert_text(self):
        frame = bytearray()
        frame = [0x68,0x00, 0x00, 0x00, 0x00, 0x68,0x4a,0xff, 0xff, 0xff, 0xff, 0xff,0xff, 0x0a, 0x04,  0x62, 0x00, 0x00]
        try:
            input_text = self.taskNumberInput.text()
            if input_text:
                task_item = 0xE0001500 + int(input_text, 10)
            else:
                self.taskNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入任务号")
    
            frame_fun.item_to_di(task_item, frame)
            selected_button = self.taskStatusButtGroup.checkedButton()
            selected_index = self.taskStatusButtGroup.id(selected_button)
            frame.append(selected_index - 1)
            time = self.time_input.dateTime()
            time = self.get_time(time)
            for data in reversed(time):
                 frame.append(data)
            selected_button = self.reportunitbutton.checkedButton()
            if selected_button is not None:
                selected_index = self.reportunitbutton.id(selected_button)
                frame.append(selected_index - 1)

            input_text = self.reportcycleinput.text()
            if input_text:
                 frame.append(int(input_text, 10))
            else:
                self.reportcycleinput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入上报周期")
        
            selected_button = self.tasktypebutt.checkedButton()
            selected_index = self.tasktypebutt.id(selected_button)
            frame.append(selected_index - 1)
        
            time = self.get_time(self.readtime_input.dateTime())
            for data in reversed(time):
                 frame.append(data)
        
            selected_button = self.meterunitbutton.checkedButton()
            selected_index = self.meterunitbutton.id(selected_button)
            frame.append(selected_index - 1)

            input_text = self.metercycleinput.text()
            if input_text:
                 frame.append(int(input_text, 10))
            else:
                self.metercycleinput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入采集周期")

            input_text = self.datafreqinput.text()
            if input_text:
                 frame.append(int(input_text, 10))
            else:
                self.datafreqinput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入数据抽取倍率")

            time = self.get_time(self.ertureadme_input.dateTime())
            for data in reversed(time):
                frame.append(data)

            selected_button = self.ertureadunitbutton.checkedButton()
            selected_index = self.ertureadunitbutton.id(selected_button)
            frame.append(selected_index - 1)

            input_text = self.ertureadcycleinput.text()
            if input_text:
                 frame.append(int(input_text, 10))
            else:
                self.ertureadcycleinput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入读取周期")

            input_text = self.taskexeccountinput.text()
            if input_text:
                 count = int(input_text, 10)
            else:
                self.taskexeccountinput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入执行次数")
            
            frame.append(count & 0x00ff)
            frame.append(count >> 8)

            input_text = self.meterpointinput.text()
            if input_text:
                  measurement_points_array =  frame_fun.parse_meterpoint_input(input_text)
            else:
                self.meterpointinput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入测量点")
            if measurement_points_array[0] == 0xFF and measurement_points_array[1] == 0xff:
                frame.append(0x01)
                frame.append(0xff)
                frame.append(0xff)
            else:
                frame.append(len(measurement_points_array))
                for meter_point in measurement_points_array:
                    da1, da2 = frame_csg.toDA(meter_point)
                    frame.append(da1)
                    frame.append(da2)

            input_text = self.iteminput.toPlainText()
            if input_text:
                 frame_fun.prase_item_input(input_text, frame)
            else:
                self.iteminput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入数据标识")

            caculate_cs = frame_fun.caculate_cs(frame[6:])
            frame.append(caculate_cs)
            frame.append(0x16)

            length = len(frame[6:-2])
            frame[1] = length & 0X00ff
            frame[2] = length >> 8
            frame[3] = length & 0X00ff
            frame[4] = length >> 8

            self.text_edit.clear()
            self.text_edit.setPlainText(frame_fun.to_hex_string_with_space(frame))
        except ValueError:
            print("输入的字符中包含非十六进制字符。")

    def get_time(self,selected_datetime):
        date = selected_datetime.date()
        time = selected_datetime.time()

        # 提取年、月、日、小时和分钟
        year = date.year() - 2000  # 获取年份后减去2000，得到两位的年份
        month = date.month()
        day = date.day()
        hour = time.hour()
        minute = time.minute()

        # 将年、月、日、小时和分钟转换为BCD码
        bcd_year = ((year // 10) << 4) | (year % 10)
        bcd_month = ((month // 10) << 4) | (month % 10)
        bcd_day = ((day // 10) << 4) | (day % 10)
        bcd_hour = ((hour // 10) << 4) | (hour % 10)
        bcd_minute = ((minute // 10) << 4) | (minute % 10)

        # 创建一个包含BCD码的字节串
        bcd_datetime = bytes([bcd_year, bcd_month, bcd_day, bcd_hour, bcd_minute])
        return bcd_datetime
class CtrlWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, flags=QtCore.Qt.Window)

        self.setWindowTitle("负荷控制")
        self.resize(830, 300)
        self.qvlayout = QVBoxLayout()

        self.ctrllayout = QHBoxLayout()  # 使用水平布局
        self.ctrllabel = QLabel('开关编号：')
        self.ctrllabel.setAlignment(QtCore.Qt.AlignLeft)
        self.ctrlNumberInput = QLineEdit()
        self.ctrllayout.addWidget(self.ctrllabel)
        self.ctrllayout.addWidget(self.ctrlNumberInput)
        self.ctrlNumberInput.textChanged.connect(self.update_color)

        self.branchlayout = QHBoxLayout()  # 使用水平布局
        self.branchlabel = QLabel('分支编号：')
        self.branchlabel.setAlignment(QtCore.Qt.AlignLeft)
        self.branchNumberInput = QLineEdit()
        self.branchlayout.addWidget(self.branchlabel)
        self.branchlayout.addWidget(self.branchNumberInput)
        self.branchNumberInput.textChanged.connect(self.update_color)

        self.circulayout = QHBoxLayout()  # 使用水平布局
        self.circulabel = QLabel('回路编号：')
        self.circulabel.setAlignment(QtCore.Qt.AlignLeft)
        self.circuNumberInput = QLineEdit()
        self.circulayout.addWidget(self.circulabel)
        self.circulayout.addWidget(self.circuNumberInput)
        self.circuNumberInput.textChanged.connect(self.update_color)

        self.ctrlStatusLayout = QHBoxLayout()  # 使用水平布局
        self.ctrl_statusLabel = QLabel('开关状态：')
        self.ctrl_statusLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.ctrlStatusButtGroup = QButtonGroup()
        # 创建trlc按钮
        self.ctrlInvalidButton = QRadioButton('合')
        self.ctrlEffectButton = QRadioButton('分')

        # 添加单选按钮到按钮组
        self.ctrlStatusButtGroup.addButton(self.ctrlInvalidButton, 1)
        self.ctrlStatusButtGroup.addButton(self.ctrlEffectButton, 2)

        # 设置默认选中状态
        self.ctrlInvalidButton.setChecked(True)

        # 添加控件到水平布局
        self.ctrlStatusLayout.addWidget(self.ctrl_statusLabel)
        self.ctrlStatusLayout.addWidget(self.ctrlInvalidButton)
        self.ctrlStatusLayout.addWidget(self.ctrlEffectButton)

        self.qvlayout.addLayout(self.ctrllayout)
        self.qvlayout.addLayout(self.branchlayout)
        self.qvlayout.addLayout(self.circulayout)
        self.qvlayout.addLayout(self.ctrlStatusLayout)

        # 创建一个分割器
        splitter = QtWidgets.QSplitter(self)

        # 左边部分，使用 QVBoxLayout
        left_widget = QtWidgets.QWidget(self)
        left_layout = QVBoxLayout()
        left_layout.addLayout(self.qvlayout)  # 将 self.qvlayout 添加到左边
        left_widget.setLayout(left_layout)

        # 右边部分，使用 QVBoxLayout
        right_widget = QtWidgets.QWidget(self)
        right_layout = QHBoxLayout()

        # 添加一个转换按钮
        convert_button = QtWidgets.QPushButton("转换")
        convert_button.clicked.connect(self.convert_text)  # 连接转换按钮的槽函数
        right_layout.addWidget(convert_button)

        
        # 添加一个文本框
        self.text_edit = QtWidgets.QTextEdit()
        right_layout.addWidget(self.text_edit)


        right_widget.setLayout(right_layout)

        # 将左右部分添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割器的大小策略，让左右部分可以自由调整大小
        sidth = int(self.width() / 2)
        splitter.setSizes([sidth, sidth])

        # 将分割器设置为中央部件
        self.setCentralWidget(splitter)


        self.install_event_filters()

    def install_event_filters(self):
        self.installEventFilter(self)
        def recursive_install(parent):
            for child in parent.findChildren(QtCore.QObject):
              child.installEventFilter(self)
              recursive_install(child)
        recursive_install(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.setWindowOpacity(1.0)
        return super().eventFilter(obj, event)

    def toggle_transparency(self):
        self.setWindowOpacity(0.2)  # 设置透明度为0.8或其他值

    def update_color(self):
        # Get the sender widget that triggered the signal
        text_input = self.sender()

        if text_input:
            # Get the text from the sender widget
            try:
                input_text = text_input.text()
            except:
                input_text = text_input.toPlainText()

            # Rest of your code to check and update the border color goes here
            if input_text:
                current_border_color = text_input.styleSheet()
                if "border: 2px solid red;" in current_border_color:
                    text_input.setStyleSheet("")
            else:
                text_input.setStyleSheet("border: 2px solid red;")



    def convert_text(self):
        frame = bytearray()
        frame = [0x68,0x00, 0x00, 0x00, 0x00, 0x68,0x4a,0xff, 0xff, 0xff, 0xff, 0xff,0xff, 0x0a, 0x04,  0x62, 0x00, 0x00]
        try:
            input_text = self.ctrlNumberInput.text()
            if input_text:
                task_item = 0xE0000E50 + int(input_text, 10)
            else:
                self.ctrlNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入开关编号")
    
            frame_fun.item_to_di(task_item, frame)

            input_text = self.branchNumberInput.text()
            if input_text:
                 frame.append(frame_fun.binary2bcd(int(input_text, 10)))
            else:
                self.branchNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入分支编号")

            input_text = self.circuNumberInput.text()
            if input_text:
                 frame.append(frame_fun.binary2bcd(int(input_text, 10)))
            else:
                self.circuNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入回路编号")

            selected_button = self.ctrlStatusButtGroup.checkedButton()
            selected_index = self.ctrlStatusButtGroup.id(selected_button)
            frame.append(selected_index - 1)

            frame.extend([0x00 for i in range(16)])
            caculate_cs = frame_fun.caculate_cs(frame[6:])
            frame.append(caculate_cs)
            frame.append(0x16)

            length = len(frame[6:-2])
            frame[1] = length & 0X00ff
            frame[2] = length >> 8
            frame[3] = length & 0X00ff
            frame[4] = length >> 8

            subsocket.send_to_tcp_data(frame, 1)
            self.text_edit.clear()
            self.text_edit.setPlainText(frame_fun.to_hex_string_with_space(frame))
        except ValueError:
            print("输入的字符中包含非十六进制字符。")

class PhaseWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, flags=QtCore.Qt.Window)

        self.setWindowTitle("相位识别周期参数")
        self.resize(830, 300)
        self.qvlayout = QVBoxLayout()
        
        self.protocolLayout = QGridLayout()  # 使用水平布局
        self.protocolLabel = QLabel('协议类型：')
        self.protocolButtGroup = QButtonGroup()
        # 创建trlc按钮
        self.protocolInvalidButton = QRadioButton('老协议')
        self.protocolEffectButton = QRadioButton('广东V2.1协议')

        # 添加单选按钮到按钮组
        self.protocolButtGroup.addButton(self.protocolInvalidButton, 1)
        self.protocolButtGroup.addButton(self.protocolEffectButton, 2)
        self.protocolButtGroup.buttonClicked.connect(self.protocol_change)

        # 设置默认选中状态
        self.protocolEffectButton.setChecked(True)

        # 添加控件到水平布局
        self.protocolLayout.addWidget(self.protocolLabel,0,0)
        self.protocolLayout.addWidget(self.protocolInvalidButton,0,1)
                                           
        self.protocolLayout.addWidget(self.protocolEffectButton,0,2)


        self.ctrlStatusLayout = QGridLayout()  # 使用水平布局
        self.ctrl_statusLabel = QLabel('是否开启：')
        self.ctrlStatusButtGroup = QButtonGroup()
        # 创建trlc按钮
        self.ctrlInvalidButton = QRadioButton('关闭')
        self.ctrlEffectButton = QRadioButton('开启')

        # 添加单选按钮到按钮组
        self.ctrlStatusButtGroup.addButton(self.ctrlInvalidButton, 1)
        self.ctrlStatusButtGroup.addButton(self.ctrlEffectButton, 2)

        # 设置默认选中状态
        self.ctrlInvalidButton.setChecked(True)

        # 添加控件到水平布局
        self.ctrlStatusLayout.addWidget(self.ctrl_statusLabel,0,0)
        self.ctrlStatusLayout.addWidget(self.ctrlInvalidButton,0,1)

        self.ctrlStatusLayout.addWidget(self.ctrlEffectButton,0,2)


        self.execLayout = QGridLayout()  # 使用水平布局
        self.execLabel = QLabel('执行周期：')

        self.execButtGroup = QButtonGroup()
        # 创建trlc按钮
        self.execInvalidButton = QRadioButton('单次执行')
        self.execEffectButton = QRadioButton('每日执行')

        # 添加单选按钮到按钮组
        self.execButtGroup.addButton(self.execInvalidButton, 1)
        self.execButtGroup.addButton(self.execEffectButton, 2)

        # 设置默认选中状态
        self.execEffectButton.setChecked(True)

        # 添加控件到水平布局
        self.execLayout.addWidget(self.execLabel,0,0)
        self.execLayout.addWidget(self.execInvalidButton, 0, 1)
        self.execLayout.addWidget(self.execEffectButton,0, 2)


        self.oldExeclayout = QGridLayout()  # 使用水平布局
        self.oldExeclabel = QLabel('执行时长：')
        self.oldExeclayout.addWidget(self.oldExeclabel,0,0)
             
        self.oldExecNumberInput = QLineEdit()
        self.oldExeclayout.addWidget(self.oldExecNumberInput,0,1)
        self.oldExecunitlabel = QLabel('时')
        self.oldExeclayout.addWidget(self.oldExecunitlabel,0,2)
        self.oldExecNumberInput.textChanged.connect(self.update_color)


        self.startlayout = QGridLayout()

        self.startlabel = QLabel('起始时间:')
        self.startlayout.addWidget(self.startlabel, 0, 0)

        self.hourlabel = QLabel('时')  
        self.hourNumberInput = QLineEdit()
        self.startlayout.addWidget(self.hourNumberInput, 0, 1)
        self.startlayout.addWidget(self.hourlabel, 0, 2)

        self.minutelabel = QLabel('分')
        self.minuteNumberInput = QLineEdit()  
        self.startlayout.addWidget(self.minuteNumberInput, 0, 3)
        self.startlayout.addWidget(self.minutelabel, 0, 4)

        self.keeptimelayout = QGridLayout()  # 使用水平布局
        self.keeptimelabel = QLabel('执行时长：')
        self.keeptimelayout.addWidget(self.keeptimelabel,0,0)

        self.keeptimeNumberInput = QLineEdit()
        self.keeptimelayout.addWidget(self.keeptimeNumberInput,0,1)
        self.keeptimeunitlabel = QLabel('时')
        self.keeptimelayout.addWidget(self.keeptimeunitlabel,0,2)
        self.keeptimeNumberInput.textChanged.connect(self.update_color)

        self.qvlayout.addLayout(self.protocolLayout)
        self.qvlayout.addLayout(self.ctrlStatusLayout)
        self.qvlayout.addLayout(self.execLayout)
        self.qvlayout.addLayout(self.startlayout)
        self.qvlayout.addLayout(self.keeptimelayout)

        # 创建一个分割器
        splitter = QtWidgets.QSplitter(self)

        # 左边部分，使用 QVBoxLayout
        left_widget = QtWidgets.QWidget(self)
        left_layout = QVBoxLayout()
        left_layout.addLayout(self.qvlayout)  # 将 self.qvlayout 添加到左边
        left_widget.setLayout(left_layout)

        # 右边部分，使用 QVBoxLayout
        right_widget = QtWidgets.QWidget(self)
        right_layout = QHBoxLayout()

        # 添加一个转换按钮
        convert_button = QtWidgets.QPushButton("转换")
        convert_button.clicked.connect(self.convert_text)  # 连接转换按钮的槽函数
        right_layout.addWidget(convert_button)

        
        # 添加一个文本框
        self.text_edit = QtWidgets.QTextEdit()
        right_layout.addWidget(self.text_edit)


        right_widget.setLayout(right_layout)

        # 将左右部分添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割器的大小策略，让左右部分可以自由调整大小
        sidth = int(self.width() / 2)
        splitter.setSizes([sidth, sidth])

        # 将分割器设置为中央部件
        self.setCentralWidget(splitter)


        self.install_event_filters()

    def install_event_filters(self):
        self.installEventFilter(self)
        def recursive_install(parent):
            for child in parent.findChildren(QtCore.QObject):
              child.installEventFilter(self)
              recursive_install(child)
        recursive_install(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.setWindowOpacity(1.0)
        return super().eventFilter(obj, event)

    def toggle_transparency(self):
        self.setWindowOpacity(0.2)  # 设置透明度为0.8或其他值

    def update_color(self):
        # Get the sender widget that triggered the signal
        text_input = self.sender()

        if text_input:
            # Get the text from the sender widget
            try:
                input_text = text_input.text()
            except:
                input_text = text_input.toPlainText()

            # Rest of your code to check and update the border color goes here
            if input_text:
                current_border_color = text_input.styleSheet()
                if "border: 2px solid red;" in current_border_color:
                    text_input.setStyleSheet("")
            else:
                text_input.setStyleSheet("border: 2px solid red;")

    def protocol_change(self):
        selected_button = self.protocolButtGroup.checkedButton()
        if selected_button == self.protocolInvalidButton:
            self.execInvalidButton.setText("每日执行")
            self.execEffectButton.setText("每月执行")
        else:
            self.execInvalidButton.setText("单次执行")
            self.execEffectButton.setText("每日执行")

    def convert_text(self):
        frame = bytearray()
        frame = [0x68,0x00, 0x00, 0x00, 0x00, 0x68,0x4a,0xff, 0xff, 0xff, 0xff, 0xff,0xff, 0x0a, 0x04,  0x62, 0x00, 0x00,0x01,0x12,0x00,0xE0]
        try:
            selected_button = self.ctrlStatusButtGroup.checkedButton()
            selected_index = self.ctrlStatusButtGroup.id(selected_button)
            frame.append(selected_index - 1)


            input_text = self.minuteNumberInput.text()
            if input_text:
                hexstr = frame_fun.decimal_to_bcd_byte(int(input_text, 10))
                frame.append(hexstr)
            else:
                self.minuteNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入分钟")
    
            input_text = self.hourNumberInput.text()
            if input_text:
                 frame.append(int(frame_fun.decimal_to_bcd_byte(int(input_text, 10))))
            else:
                self.hourNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入时间")

            selected_button = self.execButtGroup.checkedButton()
            selected_index = self.execButtGroup.id(selected_button)
            frame.append(selected_index - 1)

            input_text = self.keeptimeNumberInput.text()
            if input_text:
                 frame.append(int(frame_fun.decimal_to_bcd_byte(int(input_text, 10))))
            else:
                self.keeptimeNumberInput.setStyleSheet("border: 2px solid red;")
                raise ValueError("需要输入执行时长")

            frame.extend([0x00 for i in range(16)])
            caculate_cs = frame_fun.caculate_cs(frame[6:])
            frame.append(caculate_cs)
            frame.append(0x16)

            length = len(frame[6:-2])
            frame[1] = length & 0X00ff
            frame[2] = length >> 8
            frame[3] = length & 0X00ff
            frame[4] = length >> 8

            self.text_edit.clear()
            self.text_edit.setPlainText(frame_fun.to_hex_string_with_space(frame))
        except ValueError:
            print("输入的字符中包含非十六进制字符。")  

class ConfigWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, flags=QtCore.Qt.Window)

        self.setWindowTitle("连接配置")
        self.resize(830, 300)
        ip_validator = QRegExpValidator(QRegExp(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"))
        self.iplayout = QHBoxLayout()  # 使用水平布局
        self.iplabel = QLabel('远程IP：')
        self.iplabel.setAlignment(QtCore.Qt.AlignLeft)
        self.ipNumberInput = QLineEdit()
        self.ipNumberInput.setValidator(ip_validator)
        self.iplayout.addWidget(self.iplabel)
        self.iplayout.addWidget(self.ipNumberInput)
        self.ipNumberInput.textChanged.connect(self.update_color)

        self.portlayout = QHBoxLayout()  # 使用水平布局
        self.portlabel = QLabel('端口：')
        self.portlabel.setAlignment(QtCore.Qt.AlignLeft)
        self.portNumberInput = QLineEdit()
        self.portlayout.addWidget(self.portlabel)
        self.portlayout.addWidget(self.portNumberInput)
        self.portNumberInput.textChanged.connect(self.update_color)

        # 添加一个转换按钮
        self.convert_button = QtWidgets.QPushButton("连接")
        self.convert_button.clicked.connect(self.connnet_button)  # 连接转换按钮的槽函数


        self.sendlayout = QHBoxLayout()  # 使用水平布局
        self.sendlabel = QLabel('发送区：')
        self.sendlabel.setAlignment(QtCore.Qt.AlignLeft)
        self.sendinput = QtWidgets.QPlainTextEdit()
        self.sendlayout.addWidget(self.sendlabel)
        self.sendlayout.addWidget(self.sendinput)
        self.sendinput.textChanged.connect(self.update_color)

        # 添加一个转换按钮
        self.send_button = QtWidgets.QPushButton("发送")
        self.send_button.clicked.connect(self.send_func)  # 连接转换按钮的槽函数
        
        qvlayout = QVBoxLayout()  # 使用垂直布局
        qvlayout.addLayout(self.iplayout)
        qvlayout.addLayout(self.portlayout)
        qvlayout.addWidget(self.convert_button)
        qvlayout.addLayout(self.sendlayout)
        qvlayout.addWidget(self.send_button)

        # 设置主窗口的中央部件为垂直布局
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(qvlayout)
        self.setCentralWidget(central_widget)

        self.install_event_filters()

    def install_event_filters(self):
        self.installEventFilter(self)
        def recursive_install(parent):
            for child in parent.findChildren(QtCore.QObject):
              child.installEventFilter(self)
              recursive_install(child)
        recursive_install(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.LeftButton:
                self.setWindowOpacity(1.0)
        return super().eventFilter(obj, event)

    def toggle_transparency(self):
        self.setWindowOpacity(0.2)  # 设置透明度为0.8或其他值

    def update_color(self):
        # Get the sender widget that triggered the signal
        text_input = self.sender()

        if text_input:
            # Get the text from the sender widget
            try:
                input_text = text_input.text()
            except:
                input_text = text_input.toPlainText()

            # Rest of your code to check and update the border color goes here
            if input_text:
                current_border_color = text_input.styleSheet()
                if "border: 2px solid red;" in current_border_color:
                    text_input.setStyleSheet("")
            else:
                text_input.setStyleSheet("border: 2px solid red;")

    def connnet_button(self):
        ipadress = self.ipNumberInput.text()
        port = self.portNumberInput.text()
        if ipadress is None:
            self.ipNumberInput.setStyleSheet("border: 2px solid red;")
            raise ValueError("需要输入IP")
        if port is None:
            self.portNumberInput.setStyleSheet("border: 2px solid red;")
            raise ValueError("需要输入端口")
        if subsocket.get_new_tcp_client_session(ipadress, int(port)):
            self.convert_button.setCheckable(False)

    def send_func(self):
        input_text = self.sendinput.toPlainText()
        # Process the input text and generate the tree data
        show_data = []
        # Add tree data using add data function
        try:
            frame = bytearray.fromhex(input_text)
            formatted_frame = ''
            hex_str = input_text.replace(' ', '')
            for i in range(0, len(hex_str), 2):
                formatted_frame += hex_str[i:i + 2] + ' '

            # 将字符串拆分为每两个字符
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
            subsocket.send_to_tcp_data(frame, 1)
        except ValueError:
            print("发送失败")

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path=os.path.join(current_dir,":/gallery/images/ico.ico")
    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))
    window.show()
    app.exec_()