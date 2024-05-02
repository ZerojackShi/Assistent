# coding:utf-8
from PyQt5.QtCore import QPropertyAnimation, Qt, QTimer, pyqtSignal, QPoint, QRectF,QDate, QTime,pyqtProperty,QDateTime
from PyQt5.QtGui import QPainter,QPen,QColor
from PyQt5.QtWidgets import QLabel, QWidget, QToolButton, QGraphicsOpacityEffect,QHBoxLayout
from qfluentwidgets import  isDarkTheme,Theme,CalendarPicker,TimePicker
from qfluentwidgets import FluentIcon as FIF
from ..common.style_sheet import StyleSheet
from datetime import datetime
from ..common.config import cfg
class CustomStateCloseButton(QToolButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.isPressed = False
        self.isEnter = False

    def enterEvent(self, e):
        self.isEnter = True
        self.update()

    def leaveEvent(self, e):
        self.isEnter = False
        self.isPressed = False
        self.update()

    def mousePressEvent(self, e):
        self.isPressed = True
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.isPressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        if self.isPressed:
            painter.setOpacity(0.6)
        elif self.isEnter:
            painter.setOpacity(0.8)

        theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT
        FIF.CLOSE.render(painter, self.rect(), theme)


class CustomStateToolTip(QWidget):
    """ State tooltip """

    closedSignal = pyqtSignal()

    def __init__(self, icon, title, parent=None):
        """
        Parameters
        ----------
        title: str
            title of tooltip

        content: str
            content of tooltip

        parant:
            parent window
        """
        super().__init__(parent)
        self.title = title
        # self.content = content
        self.icon = icon
        self.titleLabel = QLabel(self.title, self)
        # self.contentLabel = QLabel(self.content, self)
        self.rotateTimer = QTimer(self)

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.animation = QPropertyAnimation(self.opacityEffect, b"opacity")
        self.closeButton = CustomStateCloseButton(self)

        self.isDone = False
        self.rotateAngle = 0
        self.deltaAngle = 20
        self.setObjectName("state_tool_tip")
        self.__initWidget()

    def __initWidget(self):
        """ initialize widgets """
        self.setAttribute(Qt.WA_StyledBackground)
        self.setGraphicsEffect(self.opacityEffect)
        self.opacityEffect.setOpacity(1)
        self.rotateTimer.setInterval(50)
        # self.contentLabel.setMinimumWidth(200)

        # connect signal to slot
        self.closeButton.clicked.connect(self.__onCloseButtonClicked)
        self.rotateTimer.timeout.connect(self.__rotateTimerFlowSlot)

        self.__setQss()
        self.__initLayout()

        self.rotateTimer.start()

    def __initLayout(self):
        """ initialize layout """
        self.setFixedSize(self.titleLabel.width() + 56, 37)
        self.titleLabel.move(32, 9)
        # self.contentLabel.move(12, 27)
        # self.closeButton.move(self.width() - 24, 19)
        self.closeButton.move(self.width(), 19)


    def __setQss(self):
        """ set style sheet """
        self.titleLabel.setObjectName("titleLabel")
        # self.contentLabel.setObjectName("contentLabel")

        StyleSheet.STATE_TOOL_TIP.apply(self)

        self.titleLabel.adjustSize()
        # self.contentLabel.adjustSize()

    def setTitle(self, title: str):
        """ set the title of tooltip """
        self.title = title
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()
        self.__initLayout()

    def setContent(self, content: str):
        """ set the content of tooltip """
        self.content = content
        # self.contentLabel.setText(content)

        # adjustSize() will mask spinner get stuck
        # self.contentLabel.adjustSize()

    def setState(self, isDone=False):
        """ set the state of tooltip """
        self.isDone = isDone
        self.update()
        if isDone:
            QTimer.singleShot(1000, self.__fadeOut)

    def setComPlate(self):
        self.rotateTimer.stop()
        self.rotateAngle = 0
        self.deltaAngle = 20
        self.update()

    def seticon(self, icon):
        self.icon = icon

    def __onCloseButtonClicked(self):
        """ close button clicked slot """
        self.closedSignal.emit()
        self.hide()

    def __fadeOut(self):
        """ fade out """
        self.rotateTimer.stop()
        self.animation.setDuration(200)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()

    def __rotateTimerFlowSlot(self):
        """ rotate timer time out slot """
        self.rotateAngle = (self.rotateAngle + self.deltaAngle) % 360
        self.update()

    def getSuitablePos(self):
        """ get suitable position in main window """
        for i in range(10):
            dy = i*(self.height() + 16)
            pos = QPoint(self.parent().width() - self.width() - 24, 50+dy)
            widget = self.parent().childAt(pos + QPoint(2, 2))
            if isinstance(widget, CustomStateToolTip):
                pos += QPoint(0, self.height() + 16)
            else:
                break

        return pos

    def paintEvent(self, e):
        """ paint state tooltip """
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        theme = Theme.DARK if not isDarkTheme() else Theme.LIGHT

        if not self.isDone:
            painter.translate(19, 18)
            painter.rotate(self.rotateAngle)
            self.icon.render(painter, QRectF(-8, -8, 16, 16), theme)
        else:
            self.icon.render(painter, QRectF(11, 10, 16, 16), theme)


class CustomStateTool(QWidget):
    """ State tooltip """

    closedSignal = pyqtSignal()

    def __init__(self, icon, height, parent=None):
        """
        Parameters
        ----------
        title: str
            title of tooltip

        content: str
            content of tooltip

        parant:
            parent window
        """
        super().__init__(parent)

        self.high = int(height / 2) * 2
        # self.content = content
        self.icon = icon
        # self.contentLabel = QLabel(self.content, self)
        self.rotateTimer = QTimer(self)

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.animation = QPropertyAnimation(self.opacityEffect, b"opacity")
        self.closeButton = CustomStateCloseButton(self)

        self.isDone = False
        self.rotateAngle = 0
        self.deltaAngle = 20
        self.setObjectName("state_tool_tip")
        self.__initWidget()

    def __initWidget(self):
        """ initialize widgets """
        self.setAttribute(Qt.WA_StyledBackground)
        self.setGraphicsEffect(self.opacityEffect)
        self.opacityEffect.setOpacity(1)
        self.rotateTimer.setInterval(50)
        # self.contentLabel.setMinimumWidth(200)

        # connect signal to slot
        self.closeButton.clicked.connect(self.__onCloseButtonClicked)
        self.rotateTimer.timeout.connect(self.__rotateTimerFlowSlot)

        self.__setQss()
        self.__initLayout()

        self.rotateTimer.start()

    def __initLayout(self):
        """ initialize layout """
        self.setFixedSize(self.high + 4, self.high + 4)
        self.closeButton.move(self.width(), 19)
        cfg.themeChanged.connect(self.__setQss)
        cfg.themeColorChanged.connect(self.__setQss)


    def __setQss(self):
        """ set style sheet """
        # self.contentLabel.setObjectName("contentLabel")

        # StyleSheet.STATE_TOOL_TIP.apply(self)
        color = cfg.get(cfg.themeColor)
        print(color.name())
        self.setStyleSheet("CustomStateTool {\
            background-color:" + str(color.name()) + ";\
            border: none;\
            border-radius:" + str((self.high + 4)/2) + "px;\
        }")
        # self.contentLabel.adjustSize()

    def setState(self, isDone=False):
        """ set the state of tooltip """
        self.isDone = isDone
        self.update()
        if isDone:
            QTimer.singleShot(1000, self.__fadeOut)

    def setComPlate(self):
        self.rotateTimer.stop()
        self.rotateAngle = 0
        self.deltaAngle = 20
        self.update()

    def seticon(self, icon):
        self.icon = icon

    def __onCloseButtonClicked(self):
        """ close button clicked slot """
        self.closedSignal.emit()
        self.hide()

    def __fadeOut(self):
        """ fade out """
        self.rotateTimer.stop()
        self.animation.setDuration(200)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()

    def __rotateTimerFlowSlot(self):
        """ rotate timer time out slot """
        self.rotateAngle = (self.rotateAngle + self.deltaAngle) % 360
        self.update()

    def getSuitablePos(self):
        """ get suitable position in main window """
        for i in range(10):
            dy = i*(self.height() + self.high)
            pos = QPoint(self.parent().width() - self.width() - self.high * 2, 50+dy)
            widget = self.parent().childAt(pos + QPoint(2, 2))
            if isinstance(widget, CustomStateToolTip):
                pos += QPoint(self.high, self.height() + self.high)
            else:
                break

        return pos

    def paintEvent(self, e):
        """ paint state tooltip """
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        theme = Theme.DARK if isDarkTheme() else Theme.LIGHT
        if not self.isDone:
            painter.translate(self.width()/2, self.width()/2)
            painter.rotate(self.rotateAngle)
            self.icon.render(painter, QRectF(-(self.high/2), -(self.high/2), self.high,self.high), theme)
        else:
            self.icon.render(painter, QRectF(self.high - 5, self.high-6, self.high, self.high), theme)


class DateTimePicker(QWidget):
    dateTimeChanged = pyqtSignal(QDate, QTime)

    def __init__(self, parent=None, showSeconds=False):
        super().__init__(parent)

        self.calendar_picker = CalendarPicker(self)
        self.time_picker = TimePicker(self, showSeconds)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.calendar_picker)
        self.layout.addWidget(self.time_picker)

        # Connect signals from individual pickers to the combined signal
        self.calendar_picker.dateChanged.connect(self._onDateTimeChanged)
        self.time_picker.timeChanged.connect(self._onDateTimeChanged)

    def getDateTime(self):
        return self.calendar_picker.getDate(), self.time_picker.getTime()
    
    def getDateTimeStamp(self):
        date_obj = self.calendar_picker.getDate()
        time_obj = self.time_picker.getTime()
        # 将日期和时间对象合并为一个datetime对象
        # 将 QDate 和 QTime 对象转换为 QDateTime 对象
        datetime_obj = QDateTime(date_obj, time_obj, Qt.UTC)

        # 将 QDateTime 对象转换为 datetime 对象
        python_datetime = datetime_obj.toPyDateTime()

        # 将 datetime 对象转换为时间戳（秒）
        timestamp = python_datetime.timestamp()
        return timestamp

    def setDateTime(self, date: QDate, time: QTime):
        self.calendar_picker.setDate(date)
        self.time_picker.setTime(time)

    dateTime = pyqtProperty(tuple, getDateTime, setDateTime)

    def _onDateTimeChanged(self):
        date = self.calendar_picker.getDate()
        time = self.time_picker.getTime()
        self.dateTimeChanged.emit(date, time)