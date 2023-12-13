from token import STAR
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QVBoxLayout

# coding:utf-8
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, isDarkTheme, FluentIcon,LineEdit,PlainTextEdit,SmoothScrollDelegate
from ..common.config import cfg, log_config
from ..common.style_sheet import StyleSheet
from ..plugins import protocol
from ..plugins.frame_csg import FrameCsg
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
import sys
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

def create_tree(parent_item, data, item_positions):
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
           create_tree(item, child_items,item_positions)

class CustomTreeWidget(QtWidgets.QTreeWidget):
    custom_signal = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem)  # Define a custom signal
    def __init__(self):
        super().__init__()
        self.last_item = None
        self.last_column = 0
        self.scrollDelegate = SmoothScrollDelegate(self)
        self.setObjectName('custom_tree')
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
        StyleSheet.CUSTOM_TREE.apply(self)

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

class Alalysic(QWidget):
    """ Icon card view """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.input_text = PlainTextEdit(self)
        self.input_text.setPlaceholderText(self.tr('请输入报文...'))
        self.tree_widget = CustomTreeWidget()

        self.vBoxLayout = QVBoxLayout(self)

        self.item_position = {}
        self.frame_len  = 0
        self.tools_window = None
        self.current_screen_number = 0xFF

        self.__initWidget()

    def __initWidget(self):

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.addWidget(self.input_text, 3)
        self.vBoxLayout.addWidget(self.tree_widget, 7)
        
        self.tree_widget.header().resizeSection(0,int(720 * 0.35))
        self.tree_widget.header().resizeSection(1,int(720 * 0.25))   

        self.highlight_format = QtGui.QTextCharFormat()
        self.highlight_format.setBackground(QtGui.QColor(51, 134, 255))  # 蓝色背景
        self.highlight_format.setForeground(QtGui.QColor(255, 255, 255))  # 白色字体

        StyleSheet.HOME_INTERFACE.apply(self)
        self.reconnect_text_changed()
        self.tree_widget.custom_signal.connect(self.highlight_text)

    def update_tree_widget(self):
        w, h = self.width(), self.height()
        self.tree_widget.header().resizeSection(0,int(w * 0.35))
        self.tree_widget.header().resizeSection(1,int(w * 0.25))   

    def highlight_text(self, item):
        self.disconnect_text_changed()
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
        self.reconnect_text_changed()

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
    def disconnect_text_changed(self):
        # 断开连接
        self.input_text.textChanged.disconnect(self.display_tree)
        # 将连接状态设置为 False
        self.is_connected = False

    def reconnect_text_changed(self):
        # 重新连接
        self.input_text.textChanged.connect(self.display_tree)
        # 将连接状态设置为 True
        self.is_connected = True

    def display_tree(self):
        self.tree_widget.clear()
        input_text = self.input_text.toPlainText()
        protocol.frame_fun.globregion = cfg.get(cfg.Region)
        print(protocol.frame_fun.globregion)
        # Process the input text and generate the tree data
        show_data = []
        framedis = FrameCsg()
        # Add tree data using add data function
        try:
            frame = bytearray.fromhex(input_text)
            self.frame_len = len(frame)
            self.tree_widget.last_item = None
            formatted_frame = ''
            hex_str = input_text.replace(' ', '')
            for i in range(0, len(hex_str), 2):
                formatted_frame += hex_str[i:i + 2] + ' '
            self.disconnect_text_changed()
            self.input_text.setPlainText(formatted_frame)
            cursor = self.input_text.textCursor()

            # Clear any previous selections
            cursor.clearSelection()
            # print(self.input_text.toPlainText())
            # 将字符串拆分为每两个字符
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]

            if protocol.is_dlt645_frame(frame):
                protocol.frame_fun.globalprotocol = "DLT/645-2007"
                protocol.Analysis_645_fram_by_afn(frame, show_data,0)
            elif framedis.is_csg_frame(frame):
                protocol.frame_fun.globalprotocol = "CSG13"
                framedis.Analysis_csg_frame_by_afn(frame,show_data,0)
            create_tree(self.tree_widget.invisibleRootItem(), show_data, self.item_position)

            self.tree_widget.expandAll()
            self.reconnect_text_changed()
        except Exception as e:
            # 处理特定异常（如果需要）
            print(f"捕获到一个异常: {e}")
            log_config.log_error(f"报文：{input_text} \n 捕获到一个异常: {e}", exc_info=True)
            if isinstance(e, ValueError):
                # frame_fun.CustomMessageBox("告警",'输入的字符中包含非十六进制字符！')
                if self.is_connected:
                    self.disconnect_text_changed()
                # 保存当前文本内容
                temp_text = self.input_text.toPlainText()
                # 清除输入框内容
                self.input_text.clear()
                # 将保存的文本内容设置回输入框
                self.input_text.setPlainText(temp_text)
                self.reconnect_text_changed()
            else:
                # 获取异常信息
                exc_type, exc_value, exc_traceback = sys.exc_info()
                # 打印原始回溯信息
                import traceback
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                self.reconnect_text_changed()


        


class ViewAnalysic(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="报文解析",
            parent=parent
        )
        self.setObjectName('frameanalysic')

        self.analysicView = Alalysic(self)
        self.vBoxLayout.addWidget(self.analysicView)