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

class Problam_Interface(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="问题分析",
            parent=parent
        )
        self.index = 0
        self.file_path = []
        self.setObjectName('Problam_Interface')
        self.addbutton = ToolButton()
        self.addbutton.setFixedSize(40, 40)
        self.addbutton.setIcon(FIF.ADD)
        self.addbutton.clicked.connect(self.add_card)        
        self.vBoxLayout.addWidget(self.addbutton, 0, Qt.AlignRight)

        save_path = cfg.get(cfg.problam_conf)
        for path in save_path:
            path = path.strip("'")
            self.add_analysize_card(path, False)

    def add_card(self, path):
        file_dialog = QFileDialog()
        folder_path, _ = file_dialog.getOpenFileName(self, "选择配置文件")
        if folder_path :
            save_path = cfg.get(cfg.problam_conf).copy()
            if folder_path in save_path:
                infoBar = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('错误'),
                content="该文件配置文件已添加",
                orient=Qt.Vertical,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
                infoBar.show()
                return
            
            if self.add_analysize_card(folder_path, True):
                save_path.append(f"{folder_path}")
                cfg.set(cfg.problam_conf, save_path)
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
        try:
            index = self.vBoxLayout.indexOf(self.addbutton)
            analysiz_card = ProblemAnalysic(
                FIF.QUESTION,
                "",
                "",
                parent=self
            )
            analysiz_card.set_conf_path(conf_path)
            analysiz_card.deleteconf.connect(self.delete_card)
            self.vBoxLayout.insertWidget(index, analysiz_card)
            if is_new:
                infoBar = InfoBar(
                    icon=InfoBarIcon.SUCCESS,
                    title=self.tr('成功'),
                    content="配置文件添加成功",
                    orient=Qt.Vertical,
                    isClosable=True,
                    duration=2000,
                    position=InfoBarPosition.TOP_RIGHT,
                    parent=self
                )
                infoBar.show()
            return True
        except Exception as e:
            infoBar = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('错误'),
                content=f"配置文件{conf_path}解析失败",
                orient=Qt.Vertical,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            infoBar.show()
            return False

    def delete_card(self, widget: ProblemAnalysic):
        try:
            path = widget.file_path
            save_path = cfg.get(cfg.problam_conf).copy()
            save_path.remove(path)
            cfg.set(cfg.problam_conf, save_path)
            widget.deleteLater()
            self.vBoxLayout.removeWidget(widget)
            self.vBoxLayout.update()
            QCoreApplication.processEvents()
            infoBar = InfoBar(
                icon=InfoBarIcon.SUCCESS,
                title=self.tr('成功'),
                content=self.tr('配置移除成功'),
                orient=Qt.Vertical,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            infoBar.show()
        except Exception as e:
            InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('失败'),
                content=self.tr('配置移除失败'),
                orient=Qt.Vertical,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            return

    def resizeEvent(self, e):
        return super().resizeEvent(e)
