import psutil
import subprocess
import time, os, zipfile,shutil,configparser,sys
from app.common.config import cfg
from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen,InfoBar)
from PyQt5.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect,QApplication, QMainWindow)
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtGui import QIcon, QDesktopServices
CONFIG_DIR = 'app/config'
def is_process_running(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            return True
    return False

def close_process(process_name):
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            try:
                psutil.Process(process.info['pid']).terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")
def copy_assistent_folder_to_current_folder(upgrade_folder="upgrade", assistent_folder="Assistent"):
    # 构建 Assistent 文件夹的路径
    assistent_folder_path = os.path.join(upgrade_folder, assistent_folder)

    # 检查 Assistent 文件夹是否存在
    if not os.path.exists(assistent_folder_path):
        print(f"Error: {assistent_folder_path} does not exist.")
        return

    # 复制 Assistent 文件夹及其内容到当前文件夹
    shutil.copytree(assistent_folder_path, os.path.join(os.getcwd(), assistent_folder))
def update_app():
    if not os.path.exists("./update.zip"):
        return
    try:
        if backup_folder(f"./{CONFIG_DIR}", f"./{CONFIG_DIR}.bak"):
            copy_assistent_folder_to_current_folder()
            restore_folder(f"./{CONFIG_DIR}.bak", f"./{CONFIG_DIR}")
    except Exception as e:
        print(e)

def backup_folder(source_folder, backup_folder):
    try:
        if os.path.exists(backup_folder):
            shutil.rmtree(backup_folder)
        shutil.copytree(source_folder, backup_folder)
        print(f"备份成功：{source_folder} -> {backup_folder}")
        return True
    except Exception as e:
        print(f"备份失败：{e}")
        return False
def restore_folder(backup_folder, target_folder):
    try:
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        shutil.copytree(backup_folder, target_folder)
        shutil.rmtree(backup_folder)
        print(f"恢复成功：{backup_folder} -> {target_folder}")
        return True
    except Exception as e:
        print(f"恢复失败：{e}")
        return False
def read_config():
    # 定义保存文件的路径
    config_file_path = "config.ini"

    try:
        # 创建配置对象
        config = configparser.ConfigParser()

        # 尝试读取现有配置文件
        config.read(config_file_path)

        # 获取 node_id
        node_id = config.get('Config', 'NodeID')
        cfg.set(cfg.node_id, node_id, True)
        os.remove(config_file_path)
        print(f"Node ID read from {config_file_path}: {node_id}")
        return node_id
    except Exception as e:
        print(f"Error reading configuration: {e}")
        return None

def clear_upgrade_():
    if os.path.exists("./upgrade"):
        shutil.rmtree("./upgrade")

class UpdateWindow(QMainWindow):
    def __init__(self, parent=None):
        super(UpdateWindow, self).__init__(parent)
        self.old_version_exe = "Assistent.exe"
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("软件更新")
        self.setFixedSize(500, 300)
        self.setWindowIcon(QIcon(os.path.join(sys._MEIPASS, 'app/assets/icon/logo.png')))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.label = QLabel("开始更新...", central_widget)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(10, 10, 200, 30)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        central_widget.setLayout(layout)

    def update_label_text(self, text):
        self.label.setText(text)

    def close_old_version(self):
        if is_process_running(self.old_version_exe):
            print("Closing old version...")
            self.update_label_text("正在关闭旧版本...")
            close_process(self.old_version_exe)

    def update_app_and_start_new_version(self):
        print("Performing update...")
        self.update_label_text("正在更新...")
        update_app()
        read_config()
        clear_upgrade_()
        print("Starting new version...")
        self.update_label_text("正在启动新版本...")
        QTimer.singleShot(2000, self.start_new_version)
        QTimer.singleShot(3000, self.close)  # 3秒后关闭窗口
    def start_new_version(self):
        if os.path.exists(self.old_version_exe):
            subprocess.Popen([self.old_version_exe])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    update_window = UpdateWindow()
    update_window.close_old_version()
    QTimer.singleShot(2000, update_window.update_app_and_start_new_version)

    update_window.show()
    sys.exit(app.exec_())