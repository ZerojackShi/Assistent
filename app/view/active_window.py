import psutil
import subprocess
import time, os, zipfile,shutil,configparser,sys
from app.common.config import cfg
from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,TextEdit, PrimaryPushButton,
                            SplashScreen,InfoBar)
from PyQt5.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect,QApplication, QMainWindow)
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QIcon, QDesktopServices
# from mur.user import *
from PyQt5.QtCore import Qt, QTextCodec,QSize,pyqtSignal
class ActiveWindow(QMainWindow):
    activestatus = pyqtSignal(bool)
    def __init__(self, user_code, parent=None):
        super(ActiveWindow, self).__init__(parent)
        self.user_code = user_code
        self.rst = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("软件激活")
        self.setFixedSize(500, 300)
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.slayout = QVBoxLayout(central_widget)

        user_codeqhlayout = QHBoxLayout()
        self.user_codelabel = QLabel("机器码：")
        self.user_codeinput = TextEdit()
        self.user_codeinput.setText(self.user_code)
        user_codeqhlayout.addWidget(self.user_codelabel)
        user_codeqhlayout.addWidget(self.user_codeinput)

        self.slayout.addLayout(user_codeqhlayout)

        mechineqhlayout = QHBoxLayout()
        self.mechinelabel = QLabel("激活码：")
        self.mechineinput = TextEdit()
        mechineqhlayout.addWidget(self.mechinelabel)
        mechineqhlayout.addWidget(self.mechineinput)
        self.slayout.addLayout(mechineqhlayout)

        regisqhlayout = QHBoxLayout()
        self.regislabel = QLabel("注册码：")
        self.regisinput = TextEdit()
        regisqhlayout.addWidget(self.regislabel)
        regisqhlayout.addWidget(self.regisinput)
        self.slayout.addLayout(regisqhlayout)




        self.activebutton = PrimaryPushButton(self.tr("激活"))
        self.activebutton.clicked.connect(self.active)
        self.slayout.addWidget(self.activebutton)

        central_widget.setLayout(self.slayout)


    def active(self):
        my_crypt = Crypt()
        u_user_code = self.mechineinput.toPlainText()
        save(u_user_code, USER_CODE_PATH)
        u_regis_code = self.regisinput.toPlainText()
        save(u_regis_code, REGISTER_CODE_PATH)
        self.rst = verify_authorization(u_user_code, my_crypt)
        if self.rst == True :
            self.activelabel = QLabel("激活成功")
            self.slayout.addWidget(self.activelabel)
        else:
            self.activelabel = QLabel("激活失败")
            self.slayout.addWidget(self.activelabel)

    def closeEvent(self, event):
        print("closeEvent", self.rst)
        self.activestatus.emit(self.rst)
        super().closeEvent(event)