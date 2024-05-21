from PyQt5.QtCore import Qt, QEasingCurve,pyqtSignal,QSize,QDate,QTime,QDateTime,QTimer,QEvent,QRectF
from PyQt5.QtWidgets import (QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QButtonGroup,
                             QAbstractItemView, QTableWidgetItem,QHeaderView,QToolTip,QSplitter,QApplication,QSplitterHandle,
                             QAction,QStyledItemDelegate)
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, InfoBar, InfoBarPosition, ComboBox,
                            RadioButton, ToolButton, ToolTip,LineEdit,SwitchButton,PrimaryPushButton,PlainTextEdit,
                            RoundMenu,TableWidget,CheckBox,ToolTipFilter)
from PyQt5.QtGui import QFont, QResizeEvent,QPainter,QCursor,QBrush

class SplitterHandle(QSplitterHandle):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(SplitterHandle, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        super(SplitterHandle, self).mousePressEvent(event)
        if event.pos().y() <= 24:
            self.clicked.emit()

    def mouseMoveEvent(self, event):
        if event.pos().y() <= 24:
            self.unsetCursor()
            event.accept()
        else:
            self.setCursor(Qt.SplitHCursor if self.orientation()
                                              == Qt.Horizontal else Qt.SplitVCursor)
            super(SplitterHandle, self).mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制红色的圆角矩形
        rect = QRectF(0, (self.height() - 40) // 2, self.width(), 40)
        painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(Qt.gray))
        painter.drawRoundedRect(rect, 5, 5)


class Splitter(QSplitter):

    def onClicked(self):
        print('clicked')

    def createHandle(self):
        if self.count() == 1:
            handle = SplitterHandle(self.orientation(), self)
            handle.clicked.connect(self.onClicked)
            return handle
        return super(Splitter, self).createHandle()
