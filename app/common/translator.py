# coding: utf-8
from PyQt5.QtCore import QObject


class Translator(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.text = self.tr('Text')
        self.view = self.tr('View')
        self.menus = self.tr('Menus & toolbars')
        self.icons = self.tr('Icons')
        self.layout = self.tr('Layout')
        self.dialogs = self.tr('Dialogs & flyouts')
        self.scroll = self.tr('Scrolling')
        self.material = self.tr('Material')
        self.dateTime = self.tr('Date & time')
        self.navigation = self.tr('Navigation')
        self.basicInput = self.tr('Basic input')
        self.statusInfo = self.tr('Status & info')
        self.frameanalysic = self.tr('报文解析')
        self.sendreceive = self.tr('发送和接收')
        self.param      = self.tr('参数设置')
        self.customframe      = self.tr('自定义报文')
        self.dataBaseView      = self.tr('数据库解析')
        self.appmessage        = self.tr('APP消息接口')
        self.problam = self.tr('问题分析')
        self.framefile = self.tr('文件解析')