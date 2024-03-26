# coding: utf-8
from enum import Enum
from PyQt5.QtCore import QObject
class CommType(Enum):
    TCP_CLIENT = 0,
    TCP_SERVICE = 1,
    SERIAL = 2,
    MQTT = 3,

class SendAndReceive(QObject):
    connecttype = []
    link_port = None
    link_status = None
    tcpSocket = []
    channel = []

commmbus = SendAndReceive()