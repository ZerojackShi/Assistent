# coding:utf-8
import os
import sys
from mur.user import *
from PyQt5.QtCore import Qt, QTranslator
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator
# 将项目的根目录添加到模块搜索路径中
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.common.config import cfg,custom_read_user_code
from app.view.main_window import MainWindow
from app.view.active_window import ActiveWindow
# enable dpi scale
if cfg.get(cfg.dpiScale) == "Auto":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
else:
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

# create application
app = QApplication(sys.argv)
app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
# internationalization
locale = cfg.get(cfg.language).value
translator = FluentTranslator(locale)
galleryTranslator = QTranslator()
galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")

app.installTranslator(translator)
app.installTranslator(galleryTranslator)


def handle_activation_status(status):
    if status:
        w = MainWindow()
        w.show()
    else:
        app.exit(1)

# create main window
# my_crypt = Crypt()
# u_user_code = custom_read_user_code()
# if u_user_code == "":
#     u_machine_code = gen_machine_code(my_crypt)
#     activewindow = ActiveWindow(u_machine_code)
#     activewindow.activestatus.connect(handle_activation_status)
#     activewindow.show()
#     app.exec_()
# else:
#     rst = verify_authorization(u_user_code, my_crypt)
w = MainWindow()
w.show()
app.exec_()