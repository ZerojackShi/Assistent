# coding: utf-8
from PyQt5.QtCore import QUrl, QSize, QEvent
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen,InfoBar)
from qfluentwidgets import FluentIcon as FIF

from .gallery_interface import GalleryInterface
from .home_interface import HomeInterface
from .basic_input_interface import BasicInputInterface
from .date_time_interface import DateTimeInterface
from .dialog_interface import DialogInterface
from .layout_interface import LayoutInterface
from .icon_interface import IconInterface
from .material_interface import MaterialInterface
from .menu_interface import MenuInterface
from .navigation_view_interface import NavigationViewInterface
from .scroll_interface import ScrollInterface
from .status_info_interface import StatusInfoInterface
from .setting_interface import SettingInterface
from .text_interface import TextInterface
from .view_interface import ViewInterface
from .analysic_interface import ViewAnalysic
from ..common.config import SUPPORT_URL, cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from .receive_send_interface import SendReceive,ReceiveSendInterface
from ..common import resource
from .problam_interface import Problam_Interface
from .custom_frame_interface import CustomFrame
from .database_interface import DataBaseInterface
from .app_message_interface import AppMessageInterface
from ..plugins.update import UpgradeWindows
from PyQt5.QtCore import QThread

class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.analysicView = ViewAnalysic(self)
        self.iconInterface = IconInterface(self)
        self.basicInputInterface = BasicInputInterface(self)
        self.dateTimeInterface = DateTimeInterface(self)
        self.dialogInterface = DialogInterface(self)
        self.layoutInterface = LayoutInterface(self)
        self.menuInterface = MenuInterface(self)
        self.materialInterface = MaterialInterface(self)
        self.navigationViewInterface = NavigationViewInterface(self)
        self.scrollInterface = ScrollInterface(self)
        self.statusInfoInterface = StatusInfoInterface(self)
        self.settingInterface = SettingInterface(self)
        self.textInterface = TextInterface(self)
        self.viewInterface = ViewInterface(self)
        # self.sendreceive = SendReceive(self)
        self.sendreceive = ReceiveSendInterface(self)
        self.customFrame = CustomFrame(self)
        self.dataBaseView = DataBaseInterface(self)
        self.appmessage = AppMessageInterface(self)
        self.problam = Problam_Interface(self)
        self.test = StatusInfoInterface(self)
        # self.param_interface = ParamInterface(self)
        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()
        self.splashScreen.finish()
        # self.check_upgrade()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSampleCard.connect(self.switchToSample)
        signalBus.supportSignal.connect(self.onSupport)
        signalBus.infopopup.connect(self.onInfoPopup)
    def initNavigation(self):
        # add navigation items
        t = Translator()
        # self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))
        # self.addSubInterface(self.iconInterface, Icon.EMOJI_TAB_SYMBOLS, t.icons)
        self.navigationInterface.addSeparator()

        pos = NavigationItemPosition.SCROLL
        # self.addSubInterface(self.basicInputInterface, FIF.CHECKBOX,t.basicInput, pos)
        # self.addSubInterface(self.dateTimeInterface, FIF.DATE_TIME, t.dateTime, pos)
        # self.addSubInterface(self.dialogInterface, FIF.MESSAGE, t.dialogs, pos)
        # self.addSubInterface(self.layoutInterface, FIF.LAYOUT, t.layout, pos)
        # self.addSubInterface(self.materialInterface, FIF.PALETTE, t.material, pos)
        # self.addSubInterface(self.menuInterface, Icon.MENU, t.menus, pos)
        # self.addSubInterface(self.navigationViewInterface, FIF.MENU, t.navigation, pos)
        # self.addSubInterface(self.scrollInterface, FIF.SCROLL, t.scroll, pos)
        # self.addSubInterface(self.statusInfoInterface, FIF.CHAT, t.statusInfo, pos)
        # self.addSubInterface(self.textInterface, Icon.TEXT, t.text, pos)
        self.addSubInterface(self.analysicView, Icon.FRAME_ALALYSIC, t.frameanalysic,pos)
        self.addSubInterface(self.sendreceive, FIF.SEND, t.sendreceive, pos)
        self.addSubInterface(self.customFrame, FIF.SCROLL, t.customframe, pos)
        self.addSubInterface(self.dataBaseView, FIF.ZOOM, t.dataBaseView, pos)
        self.addSubInterface(self.appmessage, FIF.MESSAGE, t.appmessage, pos)
        self.addSubInterface(self.problam, FIF.CHAT, t.problam, pos)
        # self.addSubInterface(self.param_interface, FIF.SCROLL, t.param, pos) 

        # add custom widget to bottom
        # self.navigationInterface.addWidget(
        #     routeKey='avatar',
        #     widget=NavigationAvatarWidget('zhiyiYo', ':/gallery/images/shoko.png'),
        #     onClick=self.onSupport,
        #     position=NavigationItemPosition.BOTTOM
        # )
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(960, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))
        self.setWindowTitle('Assistent')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def onSupport(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')
        if w.exec():
            QDesktopServices.openUrl(QUrl(SUPPORT_URL))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.splashScreen.resize(self.size())

    def switchToSample(self, routeKey, index):
        """ switch to sample """
        interfaces = self.findChildren(GalleryInterface)
        for w in interfaces:
            if w.objectName() == routeKey:
                self.stackedWidget.setCurrentWidget(w, False)
                w.scrollToCard(index)
    def onInfoPopup(self, result, msg, status):
        if result:
            InfoBar.success(
                msg,
                status,
                duration=1500,
                parent=self
            )
        else:
            InfoBar.warning(
                msg,
                status,
                duration=1500,
                parent=self
            )
    def check_upgrade(self):
        check = cfg.get(cfg.checkUpdateAtStartUp)
        if check:
            self.upgrade = UpgradeWindows()
            self.upgrade.check_upgrade()