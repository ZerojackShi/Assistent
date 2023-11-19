# coding: utf-8
from enum import Enum
from PyQt5.QtCore import QObject
class CommType(Enum):
    TCP_CLIENT = 0,
    TCP_SERVICE = 1,
    SERIAL = 2,

class SendAndReceive(QObject):
    connecttype = None
    link_port = None
    link_status = None
    tcpSocket = []
    channel = None

commmbus = SendAndReceive()