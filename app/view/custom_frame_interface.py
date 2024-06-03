from PyQt5.QtCore import Qt, QEasingCurve,pyqtSignal,pyqtSlot,QSize,QDate,QTime,QDateTime,QTimer,QEvent,QRectF,QCoreApplication,QMetaObject,Q_ARG,QByteArray
from PyQt5.QtWidgets import (QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QButtonGroup,
                             QAbstractItemView, QTableWidgetItem,QHeaderView,QToolTip,QSplitter,QApplication,QSplitterHandle,
                             QAction,QStyledItemDelegate,QGridLayout,QSizePolicy,QFormLayout,QMenu)
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, InfoBar, InfoBarPosition, ComboBox,
                            RadioButton, ToolButton, ToolTip,LineEdit,SwitchButton,PrimaryPushButton,PlainTextEdit,
                            RoundMenu,TableWidget,CheckBox,ToolTipFilter,ScrollArea,menu, Action)
from PyQt5.QtGui import QFont, QResizeEvent,QPainter,QCursor,QBrush
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from ..plugins.frame_csg import FramePos
from ..plugins import frame_csg
from ..plugins.frame_fun import FrameFun as frame_fun
from ..common.signal_bus import signalBus
from ..components.state_tools import DateTimePicker
from .view_interface import Frame
from qfluentwidgets import FluentIcon as FIF
from ..components.Splitter import Splitter
from ..components.messageBox import Comwidget    
from ..plugins.protocol_channel import WorkerThread,AsyncCommunicator
import string

class CheckableHeader(QFrame):
    checkBoxClicked = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(CheckableHeader, self).__init__(parent)
        self.checkBox = CheckBox(self)
        self.checkBox.setTristate(False)
        self.checkBox.stateChanged.connect(self.onStateChanged)

        layout = QHBoxLayout(self)
        layout.addWidget(self.checkBox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setStyleSheet("QHeaderView { border: none; }")

    def onStateChanged(self, state):
        self.checkBoxClicked.emit(state == Qt.Checked)

class CusTableWidget(TableWidget):
    def resizeEvent(self, event):
        super(CusTableWidget, self).resizeEvent(event)
        self.resizeColumns()

    def resizeColumns(self):
        table_width = self.viewport().width()
        self.setColumnWidth(0, 30)
        self.setColumnWidth(1, 80)
        remaining_width = table_width - 110
        if remaining_width > 0:
            self.setColumnWidth(2, remaining_width)
        else:
            self.setColumnWidth(2, 0)

class BaseTaskTable(QFrame):
    cell_clicked = pyqtSignal(str, str)
    itemChange = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_list = {}
        self.checkboxes = []
        self.qvlayout = QVBoxLayout(self)
        self.table = CusTableWidget(self)
        self.qvlayout.addWidget(self.table)

        self.table.verticalHeader().hide()
        self.table.setColumnCount(3)
        self.table.setRowCount(0)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        # self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.horizontalHeader().resizeSection(0, 30)
        self.table.horizontalHeader().resizeSection(1, 80)

        self.table.setMouseTracking(True)
        self.table.viewport().installEventFilter(self)
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.showCopyTooltip)
        self.hovered_row = -1

        # 移除表头
        self.table.horizontalHeader().hide()

        self.addHeaderRow()

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def addHeaderRow(self):
        self.table.insertRow(0)

        checkable_header = CheckableHeader(self)
        checkable_header.checkBoxClicked.connect(self.handleHeaderClick)
        self.table.setCellWidget(0, 0, checkable_header)

        header_task_number = QTableWidgetItem("任务号")
        header_task_number.setFlags(header_task_number.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
        header_task_number.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 1, header_task_number)

        header_task_param = QTableWidgetItem("任务参数")
        header_task_param.setTextAlignment(Qt.AlignCenter)
        header_task_param.setFlags(header_task_param.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
        self.table.setItem(0, 2, header_task_param)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 80)
        self.table.cellClicked.connect(self.handleCellClick)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.table.itemChanged.connect(self.item_change)

    def add_table(self, task_list):
        task_id = task_list[0]
        task_id = int(task_id)
        if task_id != 0xFF and (task_id in self.task_list):
            row = self.task_list[task_id]
        else:
            rows = self.table.rowCount()
            if 0 == rows:
                self.table.insertRow(rows)
                row = rows
                checkbox = CheckBox()
                self.table.setCellWidget(row, 0, checkbox)
                self.checkboxes.append(checkbox)
            else:
                for row in range(rows):
                    item = self.table.item(row, 1)
                    if item is None or item.text() == "":
                        if task_id != 0xFF:
                            break
                        else:
                            row = rows
                            self.table.insertRow(row)
                            checkbox = CheckBox()
                            self.table.setCellWidget(row, 0, checkbox)
                            self.checkboxes.append(checkbox)
                            break
                    elif row == rows - 1:
                        self.table.insertRow(rows)
                        row += 1
                        checkbox = CheckBox()
                        self.table.setCellWidget(row, 0, checkbox)
                        self.checkboxes.append(checkbox)

        for i, task in enumerate(task_list):
            item = QTableWidgetItem(str(task))
            if i == 0:
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, i + 1, item)
            self.table.setRowHeight(row, 40)
            if (i == 0) and task != 0xFF:
                task = int(task)
                self.task_list[task] = row
        v_scroll_bar = self.table.verticalScrollBar()
        v_scroll_bar.setValue(v_scroll_bar.maximum())
        self.qvlayout.update()
    
    def show_context_menu(self, position):
        menu = RoundMenu(self)
        self.export_action = Action("清除所有", self)
        self.export_action.triggered.connect(self.clear_all_row)
        self.copy_action = Action("清除选中", self)
        self.copy_action.triggered.connect(self.clear_selected_row)
        menu.addAction(self.export_action)
        menu.addAction(self.copy_action)
        menu.exec_(self.table.viewport().mapToGlobal(position))

    def clear_selected_row(self):
        selected_rows = []
        for row in range(1, self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget and widget.checkState() == Qt.Checked:
                selected_rows.append(row)

        # 反向删除选中的行
        for row in reversed(selected_rows):
            self.table.removeRow(row)
            self.update_task_list(row)

    def update_task_list(self, selected_row):
        for key, value in list(self.task_list.items()):
            if value == selected_row:
                del self.task_list[key]
                break
        # 更新剩余行的 task_list 映射
        for key, value in self.task_list.items():
            if value > selected_row:
                self.task_list[key] = value - 1

    def clear_all_row(self):
        self.table.setRowCount(1)
        self.task_list.clear()
        

    def get_task_parm(self):
        task_param = {}
        for row in range(1, self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                if widget.checkState() == Qt.Checked:
                    content1 = self.table.item(row, 1)
                    content2 = self.table.item(row, 2)
                    if content1:
                        task_id = int(content1.text(), 10)
                        task_param[task_id] = ""
                    if content2:
                        task_param[task_id] = content2.text()
        return task_param
    
    def get_exit_task_parm(self):
        task_param = {}
        for row in range(1, self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                content1 = self.table.item(row, 1)
                content2 = self.table.item(row, 2)
                if content1:
                    task_id = int(content1.text(), 10)
                    task_param[task_id] = ""
                elif content2:
                    task_param[task_id] = content2.text()
        return task_param

    def handleHeaderClick(self, checked):
        for row in range(1, self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                widget.setChecked(checked)

    def handleCellClick(self, row, column):
        if row >= 1:
            content1 = self.table.item(row, 1)
            content2 = self.table.item(row, 2)
            if content1 and content2:
                content1 = content1.text()
                content2 = content2.text()
            print(content1, content2)
            self.cell_clicked.emit(content1, content2)

    def item_change(self, item):
        row = item.row()
        column = item.column()
        text = item.text()
        if column == 1:  # Check if the changed item is in the second column
            if text != '' and text.isdigit():
                task_id = int(text, 10)
                if task_id <= 0 or task_id >= 255:
                    InfoBar.error(
                        title=self.tr('失败'),
                        content=self.tr("任务号非法!"),
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    item.setText("")
                    return
                result, orgin_task_id = self.is_row_in_task_list(row)
                if task_id in self.task_list and self.task_list[task_id] != row:
                    #相同任务号，但是不同列
                    InfoBar.error(
                        title=self.tr('失败'),
                        content=self.tr("不允许添加相同任务号!"),
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                    item.setText("")
                    return
                self.task_list[task_id] = row
                if result and orgin_task_id != task_id:
                    if orgin_task_id is not None:
                        self.task_list.pop(orgin_task_id)

                    content2 = self.table.item(row, 2)
                    if content2:
                        self.table.itemChanged.disconnect(self.item_change)
                        self.reset_task_frame(task_id, content2.text())
                        self.table.itemChanged.connect(self.item_change)
            


    def is_row_in_task_list(self, row):
        for task_id in self.task_list:
            if row == self.task_list[task_id]:
                return True, task_id
        return False, None
    
    def reset_task_frame(self, task_id, content):
        self.itemChange.emit(task_id, content)

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseMove:
            index = self.table.indexAt(event.pos())
            if index.isValid():
                row = index.row()
                column = index.column()
                if row != self.hovered_row or column != self.hovered_column:
                    self.hovered_row = row
                    self.hovered_column = column
                    self.hover_timer.start(1000)  # Start the timer for 1 second
            else:
                self.hover_timer.stop()
                self.hovered_row = -1
                self.hovered_column = -1
        elif event.type() == QEvent.Leave:
            self.hover_timer.stop()
            self.hovered_row = -1
            self.hovered_column = -1
        return super().eventFilter(source, event)

    def showCopyTooltip(self):
        if self.hovered_row >= 1 and self.hovered_column > 1:
            widget = self.table.item(self.hovered_row, self.hovered_column)
            if widget is None:
                return 
            cell_content = widget.text()  # Get content of the hovered cell
            if len(cell_content) <= 0:
                return
            pos = self.table.viewport().mapToGlobal(self.table.visualRect(self.table.model().index(self.hovered_row, self.hovered_column)).center())
            menu = RoundMenu(self)
            self.copy_action = QAction("复制", self)
            self.copy_action.triggered.connect(lambda: self.copyToClipboard(cell_content))
            # self.copy_action.installEventFilter(ToolTipFilter(self.copy_action))
            menu.addAction(self.copy_action)
            menu.exec_(pos)

    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        InfoBar.success(
            title=self.tr('成功'),
            content=self.tr("已复制到剪贴板!"),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.window()
        )

class CustomframeResult(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.sendthread = None

        self.qvlayout = QVBoxLayout(self)

        self.chanel_box = Comwidget()
        self.framearea = PlainTextEdit()
        self.framearea.setPlaceholderText("报文生成区...")

        self.receivearea = PlainTextEdit()
        self.receivearea.setPlaceholderText("报文接收区...")

        self.qvlayout.addWidget(self.chanel_box)
        self.qvlayout.addWidget(self.framearea)
        self.qvlayout.addWidget(self.receivearea)
        self.chanel_box.read_button.clicked.connect(self.read_click)
        # self.chanel_box.setbutton.clicked.connect(self.set_click)

        self.chanel_box.read_button.setText(self.tr("发送"))
        self.chanel_box._hBoxLayout.removeWidget(self.chanel_box.setbutton)
        self.chanel_box.setbutton.deleteLater()
        self.chanel_box.setbutton.setParent(None)

    def set_frame(self, frame):
        self.framearea.setPlainText(frame)
    def clear_frame(self):
        self.framearea.clear()

    def set_readbutton_state(self, state):
        self.chanel_box.read_button.setProperty('is_act', True if state == False else False)
        if state == False:
            self.chanel_box.read_button.setText(self.tr("终止"))
        else:
            self.chanel_box.read_button.setText(self.tr("发送"))

    def set_setbutton_state(self, state):
        self.chanel_box.read_button.setEnabled(state)
        self.chanel_box.setbutton.setProperty('is_act', True if state == False else False)
        if state == False:
            self.chanel_box.setbutton.setText(self.tr("终止"))
        else:
            self.chanel_box.setbutton.setText(self.tr("设置"))

    def read_click(self):
        is_reconnectable = self.chanel_box.read_button.property('is_act')
        if is_reconnectable:
            if self.sendthread is not None:
                self.sendthread.stop()
                self.sendthread.exit()
                if self.sendthread.isRunning():
                    print("close failed")
            self.set_readbutton_state(True)
            return
        data = self.framearea.toPlainText()
        if len(data) <= 0:
            return
        channel_info = self.chanel_box.get_channel()
        if channel_info is None:
            return
        frame = bytearray()
        if self.sendthread is not None:
            self.sendthread.stop()
            self.sendthread.exit()
            if self.sendthread.isRunning():
                print("close failed")
                return
        data = self.framearea.toPlainText()
        if len(data) <= 0:
            return
        frame = frame_fun.get_frame_list_from_str(data).copy()    
        self.set_readbutton_state(False)
        self.sendthread = WorkerThread(channel_info[1], 15, self.data_replay)
        send_list = []
        send_list.append(frame)

        self.sendthread.set_send_data(send_list)
        self.sendthread.finished.connect(self.finish_handle)
        self.sendthread.start()

    def data_replay(self, index, data):
        # 将回调函数移到主线程执行
        QMetaObject.invokeMethod(self, "_data_replay_impl", Qt.QueuedConnection, Q_ARG(int, index), Q_ARG(list, data))

    @pyqtSlot(int, list)
    def _data_replay_impl(self, index, data):
        try:
            frame = frame_fun.get_data_str_with_space(data)
            print("data_replay", frame)
            self.receivearea.clear()
            self.receivearea.setPlainText(frame)
            QApplication.processEvents()
        except Exception as e:
            print(e)

    def finish_handle(self):
        self.set_readbutton_state(True)

    def set_click(self):
        is_reconnectable = self.chanel_box.setbutton.property('is_act')
        if is_reconnectable:
            if self.sendthread is not None:
                self.sendthread.stop()
                self.sendthread.exit()
                if self.sendthread.isRunning():
                    print("close failed")
            self.set_setbutton_state(True)
            return
        
        task_id_list = self.tasktable.get_task_parm()
        if task_id_list is None:
            return

        channel_info = self.chanel_box.get_channel()
        if channel_info is None:
            return
        
        self.set_setbutton_state(False)
        self.sendthread = WorkerThread(channel_info[1], 15)

        send_list = []
        for taskid, data in task_id_list.items():
            frame = frame_fun.get_frame_list_from_str(data).copy()
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            adress = frame[FramePos.POS_RTUA.value:FramePos.POS_RTUA.value + 6]
            frame_csg.init_frame(0x4a, 0x04, adress, 0x10, seq, frame)
            len = frame_csg.get_meter_task_len(frame[FramePos.POS_ITEM.value + 4:])
            len += (FramePos.POS_ITEM_DATA.value - FramePos.POS_CTRL.value)
            send_frame = frame[:FramePos.POS_CTRL.value + len].copy()
            len += frame_csg.set_frame_finish(send_frame[FramePos.POS_CTRL.value:], send_frame)
            frame_csg.set_frame_len(len, send_frame)
            send_list.append(frame)
        
        self.sendthread.set_send_data(send_list)
        self.sendthread.finished.connect(self.setfinish_handle)
        self.sendthread.start()

    def setfinish_handle(self):
        self.set_setbutton_state(True)

class CheckboxGrid(QWidget):
    def __init__(self, list, parent=None):
        super().__init__(parent)
        self.setObjectName("checkboxGrid")
        self.list = list
        self.total_checkboxes = len(self.list)
        self.selected_indexes = set()
        self.init_ui()

    def init_ui(self):
        self.qvlayout = QVBoxLayout(self)

        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Main container with border
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")

        # Inner container for checkboxes
        self.container = QWidget()
        self.container.setObjectName("container")
        self.grid_layout = QGridLayout(self.container)

        # Create checkboxes including "Select All"
        self.select_all_checkbox = CheckBox("全选")
        self.select_all_checkbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)

        self.checkboxes = [self.select_all_checkbox] + [CheckBox(f"{self.list[i]}") for i in range(self.total_checkboxes)]
        for index, checkbox in enumerate(self.checkboxes):
            checkbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            if index > 0:  # Skip the "Select All" checkbox for individual stateChanged connections
                checkbox.stateChanged.connect(self.on_checkbox_state_changed)

        self.update_grid()
        self.container.setLayout(self.grid_layout)

        # Add inner container to main container
        layout = QVBoxLayout(self.main_container)
        layout.addWidget(self.container)
        self.main_container.setLayout(layout)

        self.scroll_area.setWidget(self.container)

        self.qvlayout.addWidget(self.scroll_area)
        self.setLayout(self.qvlayout)

        StyleSheet.GRIDBOX.apply(self)
    def resizeEvent(self, event):
        super().resizeEvent(event)

    def update_grid(self):
        width = self.scroll_area.viewport().width()
        # column_count = max(1, width // 100)  # Assuming each checkbox needs 100px width
        column_count = 3
        self.grid_layout.setSpacing(10)
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                widget.setParent(None)

        
        self.grid_layout.update()
        QCoreApplication.processEvents()
        for index, checkbox in enumerate(self.checkboxes):
            row = index // column_count
            col = index % column_count
            self.grid_layout.addWidget(checkbox, row, col, Qt.AlignTop)
        
        self.grid_layout.update()
        QCoreApplication.processEvents()

    def toggle_select_all(self, state):
        is_checked = state == Qt.Checked
        for checkbox in self.checkboxes:
            if checkbox == self.select_all_checkbox:
                continue
            if is_checked:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)

        if is_checked:
            self.selected_indexes = set(range(1, len(self.checkboxes)))
        else:
            self.selected_indexes.clear()

        print("Selected indexes:", self.selected_indexes)

    def get_selected_indexes(self):
        return self.selected_indexes.copy()

    def on_checkbox_state_changed(self, state):
        checkbox = self.sender()
        index = self.checkboxes.index(checkbox)

        if state == Qt.Checked:
            self.selected_indexes.add(index)
        else:
            self.selected_indexes.discard(index)

        # Update "Select All" checkbox state if necessary
        self.select_all_checkbox.stateChanged.disconnect(self.toggle_select_all)
        if len(self.selected_indexes) == len(self.checkboxes) - 1:
            self.select_all_checkbox.setCheckState(Qt.Checked)
        elif len(self.selected_indexes) == 0:
            self.select_all_checkbox.setCheckState(Qt.Unchecked)
        else:
            self.select_all_checkbox.setCheckState(Qt.PartiallyChecked)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)

class ParamFrame(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("paramframe")

        self.pnlabel = QLabel('测量点')
        self.pnlabel.setAlignment(Qt.AlignVCenter)
        self.pnInput = PlainTextEdit()
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")

        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setPlaceholderText("使用英文','拆分,如E0000130,E0000131")
        self.itemInput.textChanged.connect(self.update_ui)

        self.datalabel = QLabel('数据内容')
        self.dataInput = PlainTextEdit()

        self.switchButton = SwitchButton(self.tr('设置'))
        self.switchButton.setChecked(True)
        self.switchButton.setText(self.tr('设置'))
        self.switchButton.checkedChanged.connect(self.onSwitchCheckedChanged)

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.button.clicked.connect(self.create_frame)
        # Use QFormLayout to align labels and inputs
        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.pnlabel, self.pnInput)
        self.form_layout.addRow(self.itemlabel, self.itemInput)
        self.form_layout.addRow(self.datalabel, self.dataInput)
        self.form_layout.addWidget(self.switchButton)
        self.form_layout.addWidget(self.button)

        self.setLayout(self.form_layout)
        
        self.datalayout_index = 2
    def update_ui(self):
        text = self.itemInput.toPlainText()
        if len(text) > 0 and all(c in string.hexdigits for c in text) and (int(text, 16) in (0xE0000150, 0xE0000151, 0xE0000152)):
            item_list = self.get_item_data_list(text)
            self.mask_widget = CheckboxGrid(item_list)
            self.replace_layout(self.datalabel, self.dataInput, self.mask_widget)
        else:
            current_widget = self.form_layout.itemAt(self.datalayout_index, QFormLayout.FieldRole)
            if current_widget and isinstance(current_widget.widget(), CheckboxGrid):
                self.dataInput = PlainTextEdit()
                self.replace_layout(self.datalabel, current_widget.widget(), self.dataInput)

    def replace_layout(self, label, old_widget, new_widget):
        # 移除旧的控件
        self.form_layout.removeRow(self.datalayout_index)

        # 重新创建 datalabel
        self.datalabel = QLabel('数据内容')

        # 重新添加 datalabel 和新控件
        self.form_layout.insertRow(self.datalayout_index, self.datalabel, new_widget)
        self.form_layout.update()
        QCoreApplication.processEvents()

    def get_item_data_list(self, text):
        name_list = []
        item = frame_fun.get_config_xml(text, "CSG13", "南网")
        if item is not None:
            allitem = item.findall('.//bit')
            if allitem is not None:
                for bit_elem in allitem:
                    bit_id_attr = bit_elem.get('id')
                    bit_name_elem = bit_elem.find('name')
                    if bit_name_elem is not None:
                        name_list.append(bit_name_elem.text)
        return name_list.copy()

    def get_size(self):
        return self.qvlayout.sizeHint() + QSize(0, 50)
    
    def onSwitchCheckedChanged(self, isChecked):
        if isChecked:
            self.switchButton.setText(self.tr('设置'))
        else:
            self.switchButton.setText(self.tr('读取'))

    def get_item_mask_data(self):
        mask_data = self.mask_widget.get_selected_indexes()
        data = [0] * 32
        for mask in mask_data:
            frame_fun.set_bit_value(data, mask - 1)
        return data.copy()
    
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
        if item in (0xE0000150, 0xE0000151,0xE0000152):
            if self.switchButton.isChecked():
                data = self.get_item_mask_data()
                item_dic[item] = frame_fun.get_data_str_order(data)
            else:
                data = None
                item_dic[item] = data 
        else:
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
        seq = frame_csg.get_frame_seq(0, 1, 1, False)
        frame_csg.init_frame(0x4a, afn, adress, msa, seq, frame)
        frame_len += FramePos.POS_DATA.value
        frame_len += frame_csg.get_frame(point_array, item_dic, frame)
        frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
        frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)
        self.frame_finfish.emit(frame, frame_len)


class ParamFrameInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.qhlayout = QHBoxLayout(self)  # 使用水平布局

        self.framearea = ParamFrame()
        self.result = CustomframeResult()
        self.framearea.frame_finfish.connect(self.display_frame)
        self.qhlayout.addWidget(self.framearea, 6, alignment=Qt.AlignTop)
        self.qhlayout.addWidget(self.result, 4)

        StyleSheet.CUSTOM_INTERFACE.apply(self)
    
    def display_frame(self, frame, length):
        self.result.clear_frame()
        text = frame_fun.get_data_str_with_space(frame)
        self.result.set_frame(text)

class ReadCurFrame(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")

        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()
        self.itemInput.setPlaceholderText("使用英文','拆分,0201FF00,0202FF00")

        self.button = PrimaryPushButton(self.tr('生成报文'))
        self.button.clicked.connect(self.create_frame)

        self.form_layout = QFormLayout(self)
        self.form_layout.addRow(self.pnlabel, self.pnInput)
        self.form_layout.addRow(self.itemlabel, self.itemInput)
        self.form_layout.addRow(self.button)
        self.setLayout(self.form_layout)

    def create_frame(self, frame):
        try:
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
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, afn, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value
            frame_len += frame_csg.add_point_and_item_to_frame(point_array, item_array, frame)
            frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
            frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

            self.frame_finfish.emit(frame, frame_len)
        except Exception as e:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("生成报文失败!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return


class ReadCurInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.qhlayout = QHBoxLayout(self)  # 使用水平布局

        self.framearea = ReadCurFrame()
        self.result = CustomframeResult()
        self.framearea.frame_finfish.connect(self.display_frame)
        self.qhlayout.addWidget(self.framearea, 5, alignment=Qt.AlignTop)
        self.qhlayout.addWidget(self.result, 5)

        StyleSheet.CUSTOM_INTERFACE.apply(self)
    
    def display_frame(self, frame, length):
        self.result.clear_frame()
        text = frame_fun.get_data_str_with_space(frame)
        self.result.set_frame(text)

class ReadHistoryFrame(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()

        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()

        self.starttimelabel = QLabel('开始时间')
        self.starttimeInput = DateTimePicker()

        self.endtimelabel = QLabel('结束时间')
        self.endtimeInput = DateTimePicker()

        self.datakindlabel = QLabel('数据密度')
        self.datakindInput = ComboBox()

        self.button = PrimaryPushButton(self.tr('生成报文'))

        self.form_layout = QFormLayout(self)
        self.form_layout.addRow(self.pnlabel, self.pnInput)
        self.form_layout.addRow(self.itemlabel, self.itemInput)
        self.form_layout.addRow(self.starttimelabel, self.starttimeInput)
        self.form_layout.addRow(self.endtimelabel, self.endtimeInput)
        self.form_layout.addRow(self.datakindlabel, self.datakindInput)
        self.form_layout.addRow(self.button)
        self.setLayout(self.form_layout)

        self.init_widget()

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
        try:
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
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, afn, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value
            frame_len += frame_csg.add_point_and_item_and_time_to_frame(point_array, item_array, start_time_array[:6], end_time_array[:6],datakind,frame)
            frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
            frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

            self.frame_finfish.emit(frame, frame_len)
        except Exception as e:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("生成报文失败!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
class ReadHistoryInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.qhlayout = QHBoxLayout(self)  # 使用水平布局

        self.framearea = ReadHistoryFrame()
        self.result = CustomframeResult()
        self.framearea.frame_finfish.connect(self.display_frame)
        self.qhlayout.addWidget(self.framearea, 5, alignment=Qt.AlignTop)
        self.qhlayout.addWidget(self.result, 5)

        StyleSheet.CUSTOM_INTERFACE.apply(self)
    
    def display_frame(self, frame, length):
        self.result.clear_frame()
        text = frame_fun.get_data_str_with_space(frame)
        self.result.set_frame(text)

class ReadEventAlarmFrame(QWidget):
    frame_finfish = pyqtSignal(list, int)
    def __init__(self, type, parent=None):
        super().__init__(parent=parent)

        self.type = type #1 告警类型 2事件类型
        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()

        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()

        self.starttimelabel = QLabel('开始时间')
        self.starttimeInput = DateTimePicker()

        self.endtimelabel = QLabel('结束时间')
        self.endtimeInput = DateTimePicker()

        self.readtypelabel = QLabel('读取类型')
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

        self.button = PrimaryPushButton(self.tr('生成报文'))

        self.form_layout = QFormLayout(self)
        self.form_layout.addRow(self.pnlabel, self.pnInput)
        self.form_layout.addRow(self.itemlabel, self.itemInput)
        self.form_layout.addRow(self.starttimelabel, self.starttimeInput)
        self.form_layout.addRow(self.endtimelabel, self.endtimeInput)
        self.form_layout.addRow(self.readtypelabel, self.radioWidget)
        self.form_layout.addRow(self.button)
        self.setLayout(self.form_layout)

        self.init_widget()

    def init_widget(self):
        # self.setFixedHeight(300)
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")
        self.itemInput.setPlaceholderText("使用英文','拆分,如E2000001,E2000002")
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
        try:
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
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, afn, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value
            frame_len += frame_csg.add_point_and_item_and_time_to_frame(point_array, item_array, start_time_array[:6], end_time_array[:6],None,frame)
            frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
            frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)

            self.frame_finfish.emit(frame, frame_len)
        except Exception as e:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("生成报文失败!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

class ReadEventAlarmInterface(QWidget):
    def __init__(self, type, parent=None):
        super().__init__(parent=parent)

        self.qhlayout = QHBoxLayout(self)  # 使用水平布局

        self.framearea = ReadEventAlarmFrame(type=type, parent=None)
        self.result = CustomframeResult()
        self.framearea.frame_finfish.connect(self.display_frame)
        self.qhlayout.addWidget(self.framearea, 5, alignment=Qt.AlignTop)
        self.qhlayout.addWidget(self.result, 5)

        StyleSheet.CUSTOM_INTERFACE.apply(self)
    
    def display_frame(self, frame, length):
        self.result.clear_frame()
        text = frame_fun.get_data_str_with_space(frame)
        self.result.set_frame(text)

class MeterTaskFrame(QWidget):
    frame_finfish = pyqtSignal(int, list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.tasklabel = QLabel('表端任务号')
        self.taskNumberInput = LineEdit()

        self.validreadtypelabel = QLabel('有效性标志')
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

        self.reportbasetimelabel = QLabel('上报基准时间')
        self.reportbasetimeInput = DateTimePicker()

        self.reportunitreadtypelabel = QLabel('定时上报周期单位')
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

        self.reportcyclelabel = QLabel('定时上报周期')
        # self.reportcyclelabel.setAlignment(Qt.AlignLeft)
        self.reportcycleInput = LineEdit()

        self.tasktypereadtypelabel = QLabel('数据结构方式')
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


        self.readtimelabel = QLabel('采样基准时间')
        self.readtimeInput = DateTimePicker()

        self.meterunitreadtypelabel = QLabel('表端定时采样周期基本单位')
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


        self.metercyclelabel = QLabel('表端定时采样周期')
        self.metercyclelabel.setAlignment(Qt.AlignLeft)
        self.metercycleInput = LineEdit()

        self.datafreqlabel = QLabel('数据抽取倍率')
        self.datafreqlabel.setAlignment(Qt.AlignLeft)
        self.datafreqInput = LineEdit()

        self.ertureadtimelabel = QLabel('终端查询基准时间')
        self.ertureadtimeInput = DateTimePicker()

        self.ertureadunitreadtypelabel = QLabel('终端定时查询周期单位')
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


        self.ertureadcyclelabel = QLabel('终端定时查询周期')
        self.ertureadcyclelabel.setAlignment(Qt.AlignLeft)
        self.ertureadcycleInput = LineEdit()

        self.taskexeccountlabel = QLabel('执行次数')
        self.taskexeccountlabel.setAlignment(Qt.AlignLeft)
        self.taskexeccountInput = LineEdit()

        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()

        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()

        self.button = PrimaryPushButton(self.tr('生成报文'))

        self.form_layout = QFormLayout(self)
        self.form_layout.addRow(self.tasklabel, self.taskNumberInput)
        self.form_layout.addRow(self.validreadtypelabel, self.validradioWidget)
        self.form_layout.addRow(self.reportbasetimelabel, self.reportbasetimeInput)
        self.form_layout.addRow(self.reportunitreadtypelabel, self.reportunitradioWidget)
        self.form_layout.addRow(self.reportcyclelabel, self.reportcycleInput)
        self.form_layout.addRow(self.tasktypereadtypelabel,self.tasktyperadioWidget)
        self.form_layout.addRow(self.readtimelabel, self.readtimeInput)
        self.form_layout.addRow(self.meterunitreadtypelabel, self.meterunitradioWidget)
        self.form_layout.addRow(self.metercyclelabel, self.metercycleInput)
        self.form_layout.addRow(self.datafreqlabel, self.datafreqInput)
        self.form_layout.addRow(self.ertureadtimelabel, self.ertureadtimeInput)
        self.form_layout.addRow(self.ertureadunitreadtypelabel, self.ertureadunitradioWidget)
        self.form_layout.addRow(self.ertureadcyclelabel, self.ertureadcycleInput)
        self.form_layout.addRow(self.taskexeccountlabel,self.taskexeccountInput)
        self.form_layout.addRow(self.pnlabel, self.pnInput)
        self.form_layout.addRow(self.itemlabel, self.itemInput)

        self.form_layout.addRow(self.button)
        self.setLayout(self.form_layout)

        self.init_widget()
    def init_widget(self):
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")
        self.itemInput.setPlaceholderText("使用英文','拆分,如061201FF,061202FF")
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        self.reportbasetimeInput.setDateTime(current_date, current_time)
        self.readtimeInput.setDateTime(current_date, current_time)
        self.ertureadtimeInput.setDateTime(current_date, current_time)
        self.button.clicked.connect(self.create_frame)

    def create_frame(self, frame):
        try:
            afn = 0x04
            frame_len = 0
            frame = [0x00] * FramePos.POS_DATA.value

            adress = [0xff] * 6  # Fix the initialization of adress
            msa = 0x10
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, afn, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value

            frame.extend([0x00,0x00])
            frame_len += 2

            input_text = self.taskNumberInput.text()
            if input_text: 
                try:          
                    task_id = int(input_text, 10)                            
                    task_item = 0xE0001500 + task_id
                    if task_id <= 0 or task_id >= 255:
                        raise ValueError("任务号错误")
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

            self.frame_finfish.emit(task_id, frame, frame_len)
        except Exception as e:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("生成报文失败!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
    def set_task(self, task_id:str, task_param:str):
        if task_id is None or task_param is None:
            return False
        if 0 != len(task_id):
            self.taskNumberInput.setText(task_id)
        else:
            return False
        
        if 0 == len(task_param):
            return False
        try:
            self.taskNumberInput.setText(task_id)

            param = frame_fun.get_frame_list_from_str(task_param)
            valid_param = param[FramePos.POS_DATA.value:]
            da = frame_fun.hex_array_to_int(valid_param[2:6], False)
            task_id = da - 0xE0001500
            self.taskNumberInput.setText(str(task_id))
            valid_flag = valid_param[6]
            if valid_flag == 0x1:
                self.validradioButton2.click()
            else:
                self.validradioButton1.click()
            
            report_time = valid_param[7:12]
            centry = (QDate.currentDate().year() // 100) * 100
            
            date = QDate(frame_fun.bcd2int(report_time[-1]) + centry, frame_fun.bcd2int(report_time[-2]), frame_fun.bcd2int(report_time[-3]))
            time = QTime(frame_fun.bcd2int(report_time[1]), frame_fun.bcd2int(report_time[0]), 0, 0)
            self.reportbasetimeInput.setDateTime(date, time)

            report_unit = valid_param[12]
            if 0x0 == report_unit:
                self.reportunitradioButton1.click()
            elif 0x1 == report_unit:
                self.reportunitradioButton2.click()
            elif 0x2 == report_unit:
                self.reportunitradioButton3.click()
            elif 0x3 == report_unit:
                self.reportunitradioButton4.click()
            else:
                InfoBar.warning(
                    title=self.tr('告警'),
                    content=self.tr("报文上报周期非法!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False
            
            cycle = frame_fun.bcd2int(valid_param[13])
            self.reportcycleInput.setText(str(cycle))

            data_type = valid_param[14]
            if data_type == 0x00:
                self.tasktyperadioButton1.click()
            else:
                self.tasktyperadioButton2.click()


            get_time = valid_param[15:20]
            date = QDate(frame_fun.bcd2int(get_time[-1]) + centry, frame_fun.bcd2int(get_time[-2]), frame_fun.bcd2int(get_time[-3]))
            time = QTime(frame_fun.bcd2int(get_time[1]), frame_fun.bcd2int(get_time[0]), 0, 0)
            self.readtimeInput.setDateTime(date, time)

            get_unit = valid_param[20]
            if 0x0 == get_unit:
                self.meterunitradioButton1.click()
            elif 0x1 == get_unit:
                self.meterunitradioButton2.click()
            elif 0x2 == get_unit:
                self.meterunitradioButton3.click()
            elif 0x3 == get_unit:
                self.meterunitradioButton4.click()
            else:
                InfoBar.warning(
                    title=self.tr('告警'),
                    content=self.tr("定时采样周期基本单位非法!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False

            cycle = frame_fun.bcd2int(valid_param[21])
            self.metercycleInput.setText(str(cycle))

            data_cylce = valid_param[22]
            data_cylce = frame_fun.bcd2int(data_cylce)
            self.datafreqInput.setText(str(data_cylce))


            get_time = valid_param[23:28]
            date = QDate(frame_fun.bcd2int(get_time[-1]) + centry, frame_fun.bcd2int(get_time[-2]), frame_fun.bcd2int(get_time[-3]))
            time = QTime(frame_fun.bcd2int(get_time[1]), frame_fun.bcd2int(get_time[0]), 0, 0)
            self.ertureadtimeInput.setDateTime(date, time)

            get_unit = valid_param[28]
            if 0x0 == get_unit:
                self.ertureadunitradioButton1.click()
            elif 0x1 == get_unit:
                self.ertureadunitradioButton2.click()
            elif 0x2 == get_unit:
                self.ertureadunitradioButton3.click()
            elif 0x3 == get_unit:
                self.ertureadunitradioButton4.click()
            else:
                InfoBar.warning(
                    title=self.tr('告警'),
                    content=self.tr("定时采样周期基本单位非法!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False
            
            cycle = frame_fun.bcd2int(valid_param[29])
            self.ertureadcycleInput.setText(str(cycle))

            exec_count = valid_param[30:32]
            exec_count = frame_fun.hex_array_to_int(exec_count, False)
            self.taskexeccountInput.setText(str(exec_count))

            point_count = valid_param[32]
            point_array = valid_param[33:33+point_count*2]
            
            point_str = []
            for i in range(point_count):
                total_measurement_points, measurement_points_array = frame_fun.calculate_measurement_points(point_array[i*2:i*2+2])
                for point_id in measurement_points_array:
                    if point_id == 0xFFFF:
                        point_str.append("FFFF")
                    else:
                        point_str.append(str(point_id))
                
            point_str = ",".join(point_str)

            self.pnInput.setPlainText(point_str)

            item_count = valid_param[33+point_count*2]
            item_array = valid_param[34+point_count*2:34+point_count*2+item_count*4]

            items = []
            for i in range(item_count):
                item_id = item_array[i*4:i*4+4]
                items.append(frame_fun.get_data_str_reverser(item_id))
            item_str = ",".join(items)

            self.itemInput.setPlainText(item_str)
            return True
        except Exception as e:
            print({e}) 
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("报文格式错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

    def reset_task(self, task_id:str, task_param:str):
        if self.set_task(task_id, task_param):
            self.taskNumberInput.setText(task_id)
            frame = []
            self.create_frame(frame)

class MeterTaskInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.sendthread = None
        self.frame_id_map = {}

        # 主布局：水平布局
        self.qhlayout = QHBoxLayout(self)

        # 创建拆分器
        splitter = Splitter(Qt.Horizontal)

        # 左侧区域布局
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.chanel_box = Comwidget()
        self.tasktable = BaseTaskTable()
        left_layout.addWidget(self.chanel_box)
        left_layout.addWidget(self.tasktable)
        self.chanel_box.read_button.clicked.connect(self.read_click)
        self.chanel_box.setbutton.clicked.connect(self.set_click)

        self.addbutton = ToolButton()
        self.addbutton.setFixedSize(40, 40)
        self.addbutton.setIcon(FIF.ADD)
        self.addbutton.clicked.connect(self.add_task)        
        left_layout.addWidget(self.addbutton, 0, Qt.AlignRight)

        # 中间区域布局
        middle_layout = QVBoxLayout()
        self.framearea = MeterTaskFrame()
        self.framearea.frame_finfish.connect(self.display_frame)
        self.framearea.setContentsMargins(10, 0, 5, 0)
        middle_layout.addWidget(self.framearea)

        # 右侧区域布局
        right_layout = QVBoxLayout()
        self.result = CustomframeResult()
        right_layout.addWidget(self.result)

        # 将左侧、中间和右侧部分添加到拆分器中
        splitter.addWidget(left_widget)
        splitter.addWidget(self.framearea)
        # splitter.addWidget(self.result)

        # 设置拆分器大小策略
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        # splitter.setStretchFactor(2, 1)  # 右侧部分可伸缩

        # 将拆分器添加到主布局中
        self.qhlayout.addWidget(splitter)

        StyleSheet.CUSTOM_INTERFACE.apply(self)       

        self.tasktable.cell_clicked.connect(self.display_widget_frame)
        self.tasktable.itemChange.connect(self.recreat_frame)

    def set_readbutton_state(self, state):
        self.chanel_box.setbutton.setEnabled(state)
        self.chanel_box.read_button.setProperty('is_act', True if state == False else False)
        if state == False:
            self.chanel_box.read_button.setText(self.tr("终止"))
        else:
            self.chanel_box.read_button.setText(self.tr("读取"))

    def set_setbutton_state(self, state):
        self.chanel_box.read_button.setEnabled(state)
        self.chanel_box.setbutton.setProperty('is_act', True if state == False else False)
        if state == False:
            self.chanel_box.setbutton.setText(self.tr("终止"))
        else:
            self.chanel_box.setbutton.setText(self.tr("设置"))

    def read_click(self):
        is_reconnectable = self.chanel_box.read_button.property('is_act')
        if is_reconnectable:
            if self.sendthread is not None:
                self.sendthread.stop()
                self.sendthread.exit()
                if self.sendthread.isRunning():
                    print("close failed")
            self.set_readbutton_state(True)
            return
        task_id_list = self.tasktable.get_task_parm()
        if task_id_list is None:
            return
        channel_info = self.chanel_box.get_channel()
        if channel_info is None:
            return
        frame = bytearray()
        self.frame_id_map.clear()
        if self.sendthread is not None:
            self.sendthread.stop()
            self.sendthread.exit()
            if self.sendthread.isRunning():
                print("close failed")
                return
            
        self.set_readbutton_state(False)
        self.sendthread = WorkerThread(channel_info[1], 10, self.data_replay)
        send_list = []
        for taskid, data in task_id_list.items():
            frame = [0x00] * FramePos.POS_DATA.value
            adress = [0xff] * 6  # Fix the initialization of adress
            msa = 0x10
            frame_len = 0
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, 0x0A, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value
            frame_len += frame_csg.add_point_to_frame(0, frame)
            frame_len += frame_fun.item_to_di(0xE0001500 + taskid, frame)
            frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
            frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)
            send_list.append(frame)
            index = len(send_list) - 1
            self.frame_id_map[index] = taskid

        self.sendthread.set_send_data(send_list)
        self.sendthread.finished.connect(self.finish_handle)
        self.sendthread.start()

    def data_replay(self, index, data):
        # 将回调函数移到主线程执行
        QMetaObject.invokeMethod(self, "_data_replay_impl", Qt.QueuedConnection, Q_ARG(int, index), Q_ARG(list, data))

    @pyqtSlot(int, list)
    def _data_replay_impl(self, index, data):
        task_id = self.frame_id_map[index]
        frame = frame_fun.get_data_str_order(data)
        print("data_replay", task_id, frame)
        self.tasktable.add_table([task_id, frame])
        self.qhlayout.update()
        QApplication.processEvents()

    def finish_handle(self):
        self.set_readbutton_state(True)

    def set_click(self):
        is_reconnectable = self.chanel_box.setbutton.property('is_act')
        if is_reconnectable:
            if self.sendthread is not None:
                self.sendthread.stop()
                self.sendthread.exit()
                if self.sendthread.isRunning():
                    print("close failed")
            self.set_setbutton_state(True)
            return
        
        task_id_list = self.tasktable.get_task_parm()
        if task_id_list is None:
            return

        channel_info = self.chanel_box.get_channel()
        if channel_info is None:
            return
        
        self.set_setbutton_state(False)
        self.sendthread = WorkerThread(channel_info[1], 15)

        send_list = []
        for taskid, data in task_id_list.items():
            frame = frame_fun.get_frame_list_from_str(data).copy()
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            adress = frame[FramePos.POS_RTUA.value:FramePos.POS_RTUA.value + 6]
            frame_csg.init_frame(0x4a, 0x04, adress, 0x10, seq, frame)
            len = frame_csg.get_meter_task_len(frame[FramePos.POS_ITEM.value + 4:])
            len += (FramePos.POS_ITEM_DATA.value - FramePos.POS_CTRL.value)
            send_frame = frame[:FramePos.POS_CTRL.value + len].copy()
            len += frame_csg.set_frame_finish(send_frame[FramePos.POS_CTRL.value:], send_frame)
            frame_csg.set_frame_len(len, send_frame)
            send_list.append(send_frame)
        
        self.sendthread.set_send_data(send_list)
        self.sendthread.finished.connect(self.setfinish_handle)
        self.sendthread.start()

    def setfinish_handle(self):
        self.set_setbutton_state(True)
        
    def display_frame(self, task_id, frame, length):
        self.tasktable.add_table([task_id, frame_fun.get_data_str_order(frame)])

    def recreat_frame(self, task_id, frame):
        print("reset", task_id, frame)
        self.framearea.reset_task(str(task_id), frame)

    def find_missing_key(self, task_id_list):
        keys = sorted(task_id_list.keys())
        last_key = keys[-1]  # 获取字典中最后一个元素的键
        if last_key >= 254:
            # 从第一个元素开始找
            for i in range(1, 255):
                if i not in task_id_list:
                    return i
        else:
            # 从最后一个元素的下一个键开始找
            for i in range(last_key + 1, 255):
                if i not in task_id_list:
                    return i
        return None  # 没有找到符合条件的键
    
    def add_task(self):
        try:
            task_id_list = self.tasktable.get_exit_task_parm()
            if task_id_list is None or len(task_id_list) == 0:
                new_task = 1
            else:
                new_task = self.find_missing_key(task_id_list)

            if new_task is None:
                InfoBar.error(
                    title=self.tr('错误'),
                    content=self.tr("添加任务失败!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return  
            self.tasktable.add_table([new_task, ""])
        except Exception as e:
            print(e)
            return

    def display_widget_frame(self, task_id:str, param:str):
        self.framearea.set_task(task_id, param)

class NoramlTaskFrame(QWidget):
    frame_finfish = pyqtSignal(int, list, int)
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("NormalTaskFrame")

        self.tasklabel = QLabel('普通任务号')
        self.tasklabel.setAlignment(Qt.AlignLeft)
        self.taskNumberInput = LineEdit()

        self.validreadtypelabel = QLabel('有效性标志')
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

        self.reportbasetimelabel = QLabel('上报基准时间')
        self.reportbasetimeInput = DateTimePicker()

        self.reportunitreadtypelabel = QLabel('定时上报周期单位')
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

        self.reportcyclelabel = QLabel('定时上报周期')
        self.reportcyclelabel.setAlignment(Qt.AlignLeft)
        self.reportcycleInput = LineEdit()

        self.tasktypereadtypelabel = QLabel('数据结构方式')
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

        self.readtimelabel = QLabel('采样基准时间')
        self.readtimeInput = DateTimePicker()


        self.meterunitreadtypelabel = QLabel('定时采样周期基本单位')
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

        self.metercyclelabel = QLabel('定时采样周期')
        self.metercyclelabel.setAlignment(Qt.AlignLeft)
        self.metercycleInput = LineEdit()

        self.datafreqlabel = QLabel('数据抽取倍率')
        self.datafreqlabel.setAlignment(Qt.AlignLeft)
        self.datafreqInput = LineEdit()

        self.taskexeccountlabel = QLabel('执行次数')
        self.taskexeccountlabel.setAlignment(Qt.AlignLeft)
        self.taskexeccountInput = LineEdit()

        self.pnlabel = QLabel('测量点')
        self.pnInput = PlainTextEdit()

        self.itemlabel = QLabel('数据标识')
        self.itemInput = PlainTextEdit()

        self.button = PrimaryPushButton(self.tr('生成报文'))

        self.form_layout = QFormLayout(self)
        self.form_layout.addRow(self.tasklabel, self.taskNumberInput)
        self.form_layout.addRow(self.validreadtypelabel, self.validradioWidget)
        self.form_layout.addRow(self.reportbasetimelabel, self.reportbasetimeInput)
        self.form_layout.addRow(self.reportunitreadtypelabel, self.reportunitradioWidget)
        self.form_layout.addRow(self.reportcyclelabel, self.reportcycleInput)
        self.form_layout.addRow(self.tasktypereadtypelabel,self.tasktyperadioWidget)
        self.form_layout.addRow(self.readtimelabel, self.readtimeInput)
        self.form_layout.addRow(self.meterunitreadtypelabel, self.meterunitradioWidget)
        self.form_layout.addRow(self.metercyclelabel, self.metercycleInput)
        self.form_layout.addRow(self.datafreqlabel, self.datafreqInput)
        self.form_layout.addRow(self.taskexeccountlabel,self.taskexeccountInput)
        self.form_layout.addRow(self.pnlabel, self.pnInput)
        self.form_layout.addRow(self.itemlabel, self.itemInput)

        self.form_layout.addRow(self.button)
        self.setLayout(self.form_layout)

        self.init_widget()
    def init_widget(self):
        self.pnInput.setPlaceholderText("使用英文','或'-'拆分,如1,3,5-6")
        self.itemInput.setPlaceholderText("使用英文','拆分,如05060100,05060101")
        current_date = QDate.currentDate()
        current_time = QTime.currentTime()
        self.reportbasetimeInput.setDateTime(current_date, current_time)
        self.readtimeInput.setDateTime(current_date, current_time)
        self.button.clicked.connect(self.create_frame)

    def create_frame(self, frame):
        try:
            afn = 0x04
            frame_len = 0
            frame = [0x00] * FramePos.POS_DATA.value

            adress = [0xff] * 6  # Fix the initialization of adress
            msa = 0x10
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, afn, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value

            frame.extend([0x00,0x00])
            frame_len += 2

            input_text = self.taskNumberInput.text()
            if input_text: 
                try:      
                    task_id = int(input_text, 10)                                
                    if task_id <= 0 or task_id >= 255:
                        raise ValueError("任务号错误")
                    task_item = 0xE0000300 + task_id
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
                    content=self.tr("定时采样周期错误!"),
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
                content=self.tr("请输入定时采样周期周期!"),
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

            self.frame_finfish.emit(task_id, frame, frame_len)
        except Exception as e:
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("生成报文失败!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
    def set_task(self, task_id:str, task_param:str):
        if task_id is None or task_param is None:
            return False
        if 0 != len(task_id):
            self.taskNumberInput.setText(task_id)
        else:
            return False
        
        if 0 == len(task_param):
            return False
        try:
            self.taskNumberInput.setText(task_id)

            param = frame_fun.get_frame_list_from_str(task_param)
            valid_param = param[FramePos.POS_DATA.value:]
            da = frame_fun.hex_array_to_int(valid_param[2:6], False)
            task_id = da - 0xE0000300
            self.taskNumberInput.setText(str(task_id))
            valid_flag = valid_param[6]
            if valid_flag == 0x1:
                self.validradioButton2.click()
            else:
                self.validradioButton1.click()
            
            report_time = valid_param[7:12]
            centry = (QDate.currentDate().year() // 100) * 100
            date = QDate(frame_fun.bcd2int(report_time[-1]) + centry, frame_fun.bcd2int(report_time[-2]), frame_fun.bcd2int(report_time[-3]))
            time = QTime(frame_fun.bcd2int(report_time[1]), frame_fun.bcd2int(report_time[0]), 0, 0)
            self.reportbasetimeInput.setDateTime(date, time)

            report_unit = valid_param[12]
            if 0x0 == report_unit:
                self.reportunitradioButton1.click()
            elif 0x1 == report_unit:
                self.reportunitradioButton2.click()
            elif 0x2 == report_unit:
                self.reportunitradioButton3.click()
            elif 0x3 == report_unit:
                self.reportunitradioButton4.click()
            else:
                InfoBar.warning(
                    title=self.tr('告警'),
                    content=self.tr("报文上报周期非法!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False
            
            cycle = frame_fun.bcd2int(valid_param[13])
            self.reportcycleInput.setText(str(cycle))

            data_type = valid_param[14]
            if data_type == 0x00:
                self.tasktyperadioButton1.click()
            else:
                self.tasktyperadioButton2.click()


            get_time = valid_param[15:20]
            date = QDate(frame_fun.bcd2int(get_time[-1]) + centry, frame_fun.bcd2int(get_time[-2]), frame_fun.bcd2int(get_time[-3]))
            time = QTime(frame_fun.bcd2int(get_time[1]), frame_fun.bcd2int(get_time[0]), 0, 0)
            self.readtimeInput.setDateTime(date, time)

            get_unit = valid_param[20]
            if 0x0 == get_unit:
                self.meterunitradioButton1.click()
            elif 0x1 == get_unit:
                self.meterunitradioButton2.click()
            elif 0x2 == get_unit:
                self.meterunitradioButton3.click()
            elif 0x3 == get_unit:
                self.meterunitradioButton4.click()
            else:
                InfoBar.warning(
                    title=self.tr('告警'),
                    content=self.tr("定时采样周期基本单位非法!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False

            cycle = frame_fun.bcd2int(valid_param[21])
            self.metercycleInput.setText(str(cycle))

            data_cylce = valid_param[22]
            data_cylce = frame_fun.bcd2int(data_cylce)
            self.datafreqInput.setText(str(data_cylce))

            exec_count = valid_param[23:25]
            exec_count = frame_fun.hex_array_to_int(exec_count, False)
            self.taskexeccountInput.setText(str(exec_count))

            point_count = valid_param[25]
            point_array = valid_param[26:26+point_count*2]
            
            point_str = []
            for i in range(point_count):
                total_measurement_points, measurement_points_array = frame_fun.calculate_measurement_points(point_array[i*2:i*2+2])
                for point_id in measurement_points_array:
                    if point_id == 0xFFFF:
                        point_str.append("FFFF")
                    else:
                        point_str.append(str(point_id))
                
            point_str = ",".join(point_str)

            self.pnInput.setPlainText(point_str)

            item_count = valid_param[26+point_count*2]
            item_array = valid_param[27+point_count*2:27+point_count*2+item_count*4]

            items = []
            for i in range(item_count):
                item_id = item_array[i*4:i*4+4]
                items.append(frame_fun.get_data_str_reverser(item_id))
            item_str = ",".join(items)

            self.itemInput.setPlainText(item_str)
            return True
        except Exception as e:
            print({e}) 
            InfoBar.warning(
                title=self.tr('告警'),
                content=self.tr("报文格式错误!"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False

    def reset_task(self, task_id:str, task_param:str):
        if self.set_task(task_id, task_param):
            self.taskNumberInput.setText(task_id)
            frame = []
            self.create_frame(frame)

class NoramlTaskInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.sendthread = None
        self.frame_id_map = {}

        # 主布局：水平布局
        self.qhlayout = QHBoxLayout(self)

        # 创建拆分器
        splitter = Splitter(Qt.Horizontal)

        # 左侧区域布局
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.chanel_box = Comwidget()
        self.tasktable = BaseTaskTable()
        left_layout.addWidget(self.chanel_box)
        left_layout.addWidget(self.tasktable)
        self.chanel_box.read_button.clicked.connect(self.read_click)
        self.chanel_box.setbutton.clicked.connect(self.set_click)
        self.addbutton = ToolButton()
        self.addbutton.setFixedSize(40, 40)
        self.addbutton.setIcon(FIF.ADD)
        self.addbutton.clicked.connect(self.add_task)        
        left_layout.addWidget(self.addbutton, 0, Qt.AlignRight)

        # 中间区域布局
        middle_layout = QVBoxLayout()
        self.framearea = NoramlTaskFrame()
        self.framearea.frame_finfish.connect(self.display_frame)
        self.framearea.setContentsMargins(10, 0, 5, 0)
        middle_layout.addWidget(self.framearea)

        # 右侧区域布局
        right_layout = QVBoxLayout()
        self.result = CustomframeResult()
        right_layout.addWidget(self.result)

        # 将左侧、中间和右侧部分添加到拆分器中
        splitter.addWidget(left_widget)
        splitter.addWidget(self.framearea)
        # splitter.addWidget(self.result)

        # 设置拆分器大小策略
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        # splitter.setStretchFactor(2, 1)  # 右侧部分可伸缩

        # 将拆分器添加到主布局中
        self.qhlayout.addWidget(splitter)

        StyleSheet.CUSTOM_INTERFACE.apply(self)       

        self.tasktable.cell_clicked.connect(self.display_widget_frame)
        self.tasktable.itemChange.connect(self.recreat_frame)

    def set_readbutton_state(self, state):
        self.chanel_box.setbutton.setEnabled(state)
        self.chanel_box.read_button.setProperty('is_act', True if state == False else False)
        if state == False:
            self.chanel_box.read_button.setText(self.tr("终止"))
        else:
            self.chanel_box.read_button.setText(self.tr("读取"))

    def set_setbutton_state(self, state):
        self.chanel_box.read_button.setEnabled(state)
        self.chanel_box.setbutton.setProperty('is_act', True if state == False else False)
        if state == False:
            self.chanel_box.setbutton.setText(self.tr("终止"))
        else:
            self.chanel_box.setbutton.setText(self.tr("设置"))

    def read_click(self):
        is_reconnectable = self.chanel_box.read_button.property('is_act')
        if is_reconnectable:
            if self.sendthread is not None:
                self.sendthread.stop()
                self.sendthread.exit()
                if self.sendthread.isRunning():
                    print("close failed")
            self.set_readbutton_state(True)
            return
        task_id_list = self.tasktable.get_task_parm()
        if task_id_list is None:
            return
        channel_info = self.chanel_box.get_channel()
        if channel_info is None:
            return
        frame = bytearray()
        self.frame_id_map.clear()
        if self.sendthread is not None:
            self.sendthread.stop()
            self.sendthread.exit()
            if self.sendthread.isRunning():
                print("close failed")
                return
            
        self.set_readbutton_state(False)
        self.sendthread = WorkerThread(channel_info[1], 15, self.data_replay)
        send_list = []
        for taskid, data in task_id_list.items():
            frame = [0x00] * FramePos.POS_DATA.value
            adress = [0xff] * 6  # Fix the initialization of adress
            msa = 0x10
            frame_len = 0
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            frame_csg.init_frame(0x4a, 0x0A, adress, msa, seq, frame)
            frame_len += FramePos.POS_DATA.value
            frame_len += frame_csg.add_point_to_frame(0, frame)
            frame_len += frame_fun.item_to_di(0xE0000300 + taskid, frame)
            frame_len += frame_csg.set_frame_finish(frame[FramePos.POS_CTRL.value:frame_len], frame)
            frame_csg.set_frame_len(frame_len - FramePos.POS_CTRL.value, frame)
            send_list.append(frame)
            index = len(send_list) - 1
            self.frame_id_map[index] = taskid

        self.sendthread.set_send_data(send_list)
        self.sendthread.finished.connect(self.finish_handle)
        self.sendthread.start()

    def data_replay(self, index, data):
        # 将回调函数移到主线程执行
        QMetaObject.invokeMethod(self, "_data_replay_impl", Qt.QueuedConnection, Q_ARG(int, index), Q_ARG(list, data))

    @pyqtSlot(int, list)
    def _data_replay_impl(self, index, data):
        task_id = self.frame_id_map[index]
        frame = frame_fun.get_data_str_order(data)
        print("data_replay", task_id, frame)
        self.tasktable.add_table([task_id, frame])
        self.qhlayout.update()
        QApplication.processEvents()

    def finish_handle(self):
        self.set_readbutton_state(True)

    def set_click(self):
        is_reconnectable = self.chanel_box.setbutton.property('is_act')
        if is_reconnectable:
            if self.sendthread is not None:
                self.sendthread.stop()
                self.sendthread.exit()
                if self.sendthread.isRunning():
                    print("close failed")
            self.set_setbutton_state(True)
            return
        
        task_id_list = self.tasktable.get_task_parm()
        if task_id_list is None:
            return

        channel_info = self.chanel_box.get_channel()
        if channel_info is None:
            return
        
        self.set_setbutton_state(False)
        self.sendthread = WorkerThread(channel_info[1], 15)

        send_list = []
        for taskid, data in task_id_list.items():
            frame = frame_fun.get_frame_list_from_str(data).copy()
            seq = frame_csg.get_frame_seq(0, 1, 1, False)
            adress = frame[FramePos.POS_RTUA.value:FramePos.POS_RTUA.value + 6]
            frame_csg.init_frame(0x4a, 0x04, adress, 0x10, seq, frame)
            len = frame_csg.get_meter_task_len(frame[FramePos.POS_ITEM.value + 4:])
            len += (FramePos.POS_ITEM_DATA.value - FramePos.POS_CTRL.value)
            send_frame = frame[:FramePos.POS_CTRL.value + len].copy()
            len += frame_csg.set_frame_finish(send_frame[FramePos.POS_CTRL.value:], send_frame)
            frame_csg.set_frame_len(len, send_frame)
            send_list.append(frame)
        
        self.sendthread.set_send_data(send_list)
        self.sendthread.finished.connect(self.setfinish_handle)
        self.sendthread.start()

    def setfinish_handle(self):
        self.set_setbutton_state(True)


    @pyqtSlot(int, list, int)
    def display_frame(self, task_id, frame, length):
        # self.result.clear_frame()
        text = frame_fun.get_data_str_with_space(frame)
        # self.result.set_frame(text)
        print("type", type(task_id))
        self.tasktable.add_table([task_id, frame_fun.get_data_str_order(frame)])

    def recreat_frame(self, task_id, frame):
        print("reset", task_id, frame)
        self.framearea.reset_task(str(task_id), frame)
    
    @pyqtSlot()
    def add_task(self):
        try:
            task_id_list = self.tasktable.get_exit_task_parm()
            if task_id_list is None or len(task_id_list) == 0:
                new_task = 1
            else:
                new_task = self.find_missing_key(task_id_list)

            if new_task is None:
                InfoBar.error(
                    title=self.tr('错误'),
                    content=self.tr("添加任务失败!"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return  

            self.tasktable.add_table([new_task, ""])
        except Exception as e:
            print(e)
            return

    def find_missing_key(self, task_id_list):
        keys = sorted(task_id_list.keys())
        last_key = keys[-1]  # 获取字典中最后一个元素的键
        if last_key >= 254:
            # 从第一个元素开始找
            for i in range(1, 255):
                if i not in task_id_list:
                    return i
        else:
            # 从最后一个元素的下一个键开始找
            for i in range(last_key + 1, 255):
                if i not in task_id_list:
                    return i
        return None  # 没有找到符合条件的键
    
    def display_widget_frame(self, task_id:str, param:str):
        self.framearea.set_task(task_id, param)
        # self.result.clear_frame()
        # self.result.set_frame(param)


class CusFrameInterface(QWidget):
    """ Pivot interface """

    Nav = Pivot

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.pivot = self.Nav(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.paramInterface = ParamFrameInterface(self)
        self.curdataInterface = ReadCurInterface(self)
        self.historyDataInterface = ReadHistoryInterface(self)
        self.readAlarmInterface = ReadEventAlarmInterface(type=1, parent=self)
        self.metertaskinterface = MeterTaskInterface(self)
        self.normaltaskinterface = NoramlTaskInterface(self)

        # add items to pivot
        self.addSubInterface(self.paramInterface, 'paramInterface', self.tr('参数类'))
        self.addSubInterface(self.curdataInterface, 'curdataInterface', self.tr('当前数据类'))
        self.addSubInterface(self.historyDataInterface, 'histotyInterface', self.tr('历史数据类'))
        self.addSubInterface(self.readAlarmInterface, 'readAlarmInterface', self.tr('事件告警类'))
        self.addSubInterface(self.normaltaskinterface, 'normaltaskinterface', self.tr('普通任务类'))
        self.addSubInterface(self.metertaskinterface, 'metertaskinterface', self.tr('表端任务类'))

        self.vBoxLayout.addWidget(self.pivot, 1)
        self.vBoxLayout.addWidget(self.stackedWidget, 9)
        StyleSheet.NAVIGATION_VIEW_INTERFACE.apply(self)

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.paramInterface)
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

class CustomFrameInterface(CusFrameInterface):

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
        self.qhlayout = QHBoxLayout(self)
        self.customframe = CustomFrameInterface()
        self.qhlayout.addWidget(self.customframe)
