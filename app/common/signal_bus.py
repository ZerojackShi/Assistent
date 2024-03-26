# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal,QSize
from enum import Enum
from ..common.commodule import CommType
class SignalBus(QObject):
    """ Signal bus """

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    windowschange = pyqtSignal(QSize)
    sendmessage = pyqtSignal(str)
    messagereceive = pyqtSignal(bytes, object)
    tcpSocketChange = pyqtSignal(list)
    infopopup = pyqtSignal(bool, str, str)
    upgrade = pyqtSignal()
    channel_connected = pyqtSignal(CommType, object)
    channel_disconnected = pyqtSignal(CommType, object)     
    
signalBus = SignalBus()
