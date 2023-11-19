from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen)
from ..common.config import cfg, HELP_URL, REPO_URL, EXAMPLE_URL, FEEDBACK_URL
from ..common.style_sheet import StyleSheet
from ..plugins import frame_csg,protocol
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
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
from .receive_send_interface import SendReceive
from ..common import resource

class ParamInterface(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="报文解析",
            parent=parent
        )
        self.setObjectName('frameanalysic')

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
        self.sendreceive = SendReceive(self)

        # enable acrylic effect
        # self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()
        self.splashScreen.finish()

    def connectSignalToSlot(self):
        # signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSampleCard.connect(self.switchToSample)
        # signalBus.supportSignal.connect(self.onSupport)
        # signalBus.windowschange.connect(self.analysicView.analysicView.update_tree_widget)

    def initNavigation(self):
        # add navigation items
        t = Translator()
        # self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))
        # self.addSubInterface(self.iconInterface, Icon.EMOJI_TAB_SYMBOLS, t.icons)
        # self.navigationInterface.addSeparator()

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
        # self.addSubInterface(self.viewInterface, Icon.GRID, t.view, pos)
        self.addSubInterface(self.analysicView, Icon.FRAME_ALALYSIC, t.frameanalysic,pos)
        self.addSubInterface(self.sendreceive, FIF.SEND, t.sendreceive, pos)


        # add custom widget to bottom
        # self.navigationInterface.addWidget(
        #     routeKey='avatar',
        #     widget=NavigationAvatarWidget('zhiyiYo', ':/gallery/images/shoko.png'),
        #     onClick=self.onSupport,
        #     position=NavigationItemPosition.BOTTOM
        # )
        self.addSubInterface(
            self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)

    def switchToSample(self, routeKey, index):
        """ switch to sample """
        interfaces = self.findChildren(GalleryInterface)
        for w in interfaces:
            if w.objectName() == routeKey:
                self.stackedWidget.setCurrentWidget(w, False)
                w.scrollToCard(index)