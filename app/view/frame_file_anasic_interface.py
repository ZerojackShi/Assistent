from ..common.problam_analysic import ProblemAnalysic
from ..common.translator import Translator
from ..common.style_sheet import StyleSheet
from .gallery_interface import GalleryInterface
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout,QFileDialog,QPushButton
from qfluentwidgets import PrimaryPushButton,PushButton,ToolButton,InfoBar,InfoBarPosition,InfoBarIcon
from ..common.icon import Icon
from ..common.config import cfg
from ..common.problam_analysic import FileChooserWidget
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtCore import Qt,QCoreApplication

class FrameFileInterface(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="文件解析",
            parent=parent
        )
        self.index = 0
        self.file_path = []
        self.setObjectName('FrameFileInterface')
        self.addbutton = ToolButton()
        self.addbutton.setFixedSize(40, 40)
        self.addbutton.setIcon(FIF.ADD)
        self.addbutton.clicked.connect(self.add_card)        
        self.vBoxLayout.addWidget(self.addbutton, 0, Qt.AlignRight)

    def add_card(self, path):
        file_dialog = QFileDialog()
        folder_path, _ = file_dialog.getOpenFileName(self, "选择报文文件")
        if folder_path :          
            if self.add_analysize_card(folder_path, True):
                pass
        else:
            infoBar = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('错误'),
                content="请选择配置文件",
                orient=Qt.Vertical,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )

    def add_analysize_card(self, conf_path, is_new):
        pass

    def resizeEvent(self, e):
        return super().resizeEvent(e)
