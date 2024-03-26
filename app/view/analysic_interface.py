from token import STAR
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QVBoxLayout,QHBoxLayout
from PyQt5.QtGui import QImage,QPainter,QRegion,QPixmap,QFont
# coding:utf-8
from PyQt5.QtWidgets import QWidget, QVBoxLayout,QSizePolicy
from qfluentwidgets import ScrollArea, isDarkTheme, FluentIcon,LineEdit,PlainTextEdit,SmoothScrollDelegate,RoundMenu,Action,InfoBar,InfoBarPosition
from ..common.config import cfg, log_config
from ..common.style_sheet import StyleSheet
from ..plugins import protocol
from ..plugins.frame_csg import FrameCsg
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.signal_bus import signalBus
import sys,os,time
from PyQt5.QtSvg import QSvgGenerator
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
        self.total_height = 0
        self.datalist = None
        self.item_position = None
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

    def resizeEvent(self, event):
        self.update_tree_widget(self.size())
    def update_tree_widget(self, size: QtCore.QSize):
        w, h = size.width(), size.height()
        self.header().resizeSection(0,int(w * 0.35))
        self.header().resizeSection(1,int(w * 0.25))  

    def create_tree(self, parent_item, data, item_positions):
        if data is None or item_positions is None:
            return
        if parent_item is None:
            parent_item = self.invisibleRootItem()
            self.total_height = 0
            self.datalist =  data
            self.item_position = item_positions
        font_metrics = self.fontMetrics()
        singal_height = max(font_metrics.height(), 18)  # 避免出现高度为零的情况
        for item_data in data:
            frame = item_data.get("帧域", "")
            data_value = item_data.get("数据", "")
            description = item_data.get("说明", "")
            position = item_data.get("位置")
            column_texts = [frame, data_value, description]

            item = CustomTreeWidgetItem(parent_item, column_texts)
            item_positions[id(item)] = position
            parent_item.addChild(item)
            self.total_height += singal_height
            child_items = item_data.get("子项", [])
            if child_items:
                self.create_tree(item, child_items,item_positions)
    def contextMenuEvent(self, event):
        menu = RoundMenu(self)
        export_action = Action("导出为图片", self)
        export_action.triggered.connect(lambda: self.export(1))
        copy_action = Action("复制到剪贴板", self)
        copy_action.triggered.connect(lambda: self.export(2))
        menu.addAction(export_action)
        menu.addAction(copy_action)
        menu.exec_(event.globalPos())
    
    def export(self, type):
        try:
            if type == 1:
                # 弹出文件对话框以获取保存路径
                filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self, "保存图片", "", "PNG Image (*.png);;JPEG Image (*.jpg)"
                )
                # 如果有选择保存路径，保存图像
                if not filename:
                    InfoBar.warning(
                    title=self.tr('告警'),
                    content=self.tr("未选择保存路径!"),
                    orient=QtCore.Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                    return
            tree_widget = CustomTreeWidget()
            viewport_size = self.viewport().size()

            w, h = viewport_size.width(), self.total_height
            tree_widget.header().resizeSection(0,int(w * 0.35))
            tree_widget.header().resizeSection(1,int(w * 0.25))  

            head_height = tree_widget.header().height()

            treeheight = h + head_height + 20
            # 直接使用当前实例的数据和位置信息
            tree_widget.create_tree(None, self.datalist, self.item_position)
            tree_widget.expandAll()
            # 设置临时实例的大小
            tree_widget.setFixedSize(w, treeheight)
            StyleSheet.EXPORT.apply(tree_widget)
            # 显示并确保布局已完成
            QtWidgets.QApplication.processEvents()

            # 创建一个图像，包含所有可见区域
            image = QPixmap(w + 20, treeheight)
            coclor = QtCore.Qt.black if isDarkTheme() else QtCore.Qt.white
            image.fill(coclor)

            # 创建一个绘图设备
            painter = QPainter(image)

            # 在同一个绘图设备上进行绘制
            tree_widget.render(painter, targetOffset=QtCore.QPoint(10, 10))

            painter.end()


            if type == 1 and filename is not None:
                image.save(filename)
                InfoBar.success(
                    title=self.tr('成功'),
                    content=self.tr("已保存!"),
                    orient=QtCore.Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            elif type == 2:    
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setPixmap(image)
                InfoBar.success(
                title=self.tr('成功'),
                content=self.tr("已复制到剪贴板!"),
                orient=QtCore.Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            # 销毁临时实例
            tree_widget.deleteLater()
        except Exception as e:
            log_config.log_error(f"捕获到一个异常: {e}", exc_info=True)
            return



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
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_text.setSizePolicy(size_policy)
        self.tree_widget.setSizePolicy(size_policy)
        self.tree_widget.header().resizeSection(0,int(720 * 0.35))
        self.tree_widget.header().resizeSection(1,int(720 * 0.25))   

        self.highlight_format = QtGui.QTextCharFormat()
        self.highlight_format.setBackground(QtGui.QColor(51, 134, 255))  # 蓝色背景
        self.highlight_format.setForeground(QtGui.QColor(255, 255, 255))  # 白色字体

        StyleSheet.HOME_INTERFACE.apply(self)
        self.reconnect_text_changed()
        self.tree_widget.custom_signal.connect(self.highlight_text)

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
            hex_str = input_text.replace(' ', '').replace('\n', '')
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
            # 将每两个字符转换为一个十六进制数
            frame = [int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)]

            if protocol.is_dlt645_frame(frame):
                protocol.frame_fun.globalprotocol = "DLT/645-2007"
                protocol.FRAME_645.Analysis_645_fram_by_afn(frame, show_data,0)
            elif framedis.is_csg_frame(frame):
                protocol.frame_fun.globalprotocol = "CSG13"
                framedis.Analysis_csg_frame_by_afn(frame,show_data,0)
            self.tree_widget.create_tree(None, show_data, self.item_position)
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
        self.qhlayout = QHBoxLayout(self)
        self.analysicView = Alalysic()
        self.qhlayout.addWidget(self.analysicView)