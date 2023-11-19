# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """ Signal bus """

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    windowschange = pyqtSignal()
    sendmessage = pyqtSignal(str)
    messagereceive = pyqtSignal(str, object)
    tcpSocketChange = pyqtSignal(list)


signalBus = SignalBus()
