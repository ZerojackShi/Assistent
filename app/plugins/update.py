from PyQt5.QtCore import QThread, pyqtSignal,Qt
from ..common.config import cfg, APP_EXEC, FEEDBACK_URL, AUTHOR, VERSION, YEAR, isWin11,REPO_OWNER,REPO_NAME,Authorization,APP_NAME,UPDATE_FILE,UPDATE_DIR
from qfluentwidgets import InfoBar,MessageBox,TextEdit,PrimaryPushButton
import requests,os,re,zipfile,shutil,subprocess
import time,configparser,difflib
from PyQt5.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                             QToolButton, QGraphicsOpacityEffect,QApplication, QMainWindow,QPushButton,QSpacerItem,QSizePolicy)
from PyQt5.QtGui import QIcon
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
import ctypes,sys
import ctypes
from ctypes import wintypes,c_ulong

def get_github_tags(repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
    headers = {'Authorization': f'token {Authorization}','User-Agent': f"{APP_NAME}"}
    response = requests.get(url, headers=headers)
    response = requests.get(url)
    tags = response.json()
    return tags
def check_for_updates(local_version, local_node_id, github_tags):
    for tag in github_tags:
        tag_name = tag["tag_name"]
        node_id = tag["node_id"]
        version_pattern = re.compile(r'^(V|v)\d+\.\d+\.\d+$')
        if bool(version_pattern.match(tag_name)) == False:
            continue

        tag_name = tag_name.lstrip("V").lstrip("v")
        if tag_name == local_version:
            print(f"已经是最新版本 {local_version}")
            if local_node_id == node_id:
                # Your code here
                print(f"已经下载过最新版本 {node_id}")
                return None
            else:
                print(f"发现新版本 {tag_name}")
                return tag
        # 检查是否有新版本可用
        if tag_name > local_version:
            print(f"发现新版本 {tag_name}")
            return tag
    print("没有找到匹配的版本标签")
    return None

class UpdateThread(QThread):
    update_signal = pyqtSignal(bool, str, str)
    process_info = pyqtSignal(float,float, float)
    update_info = pyqtSignal(str, str)
    update_enable = pyqtSignal(bool)
    """检查更新的线程"""
    def __init__(self, parent=None):
        super(UpdateThread, self).__init__(parent)
        self.node_id = None
        self.description = None
        self.update_enable.connect(self.update)

    def run(self):
        # 在这里执行检查更新的操作
        tags = get_github_tags(REPO_OWNER, REPO_NAME)
        local_node = cfg.get(cfg.node_id)
        tag = check_for_updates(VERSION, local_node, tags)
        if tag:
            self.update_signal.emit(True, self.tr('发现新版本'),self.tr('正在下载更新...'))
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                if self.get_update_from_github(tag):
                    node_id = tag["node_id"]
                    description = tag["body"]
                    self.update_signal.emit(True, self.tr('下载成功'), self.tr('正在安装更新...'))
                    self.update_app(node_id, description) 
                    return
                elif attempt < max_attempts:
                    print(f"Retrying download (attempt {attempt + 1}/{max_attempts})...")
                    # self.add_firewall_rule()
                    time.sleep(2)  # 等待一段时间后重试
                else:
                    print(f"Failed after {max_attempts} attempts. Exiting.")
                    self.update_signal.emit(False, self.tr('下载失败'),self.tr('请检查网络连接'))
                    return
        else:
            self.update_signal.emit(False, self.tr('没有发现新版本'),self.tr('已经是最新版本'))
        return
    def stop(self):
        self.quit()
    def get_download_url(self, tag):
        tag_name = tag["tag_name"]
        tag_name = tag_name.lstrip("V").lstrip("v")
        print(tag_name)
        for asset in tag["assets"]:
            print(asset)
            if asset["name"] == f"{REPO_NAME}_{tag_name}.zip":
                return asset["browser_download_url"]
        return None
    def get_update_from_github(self, tag):
        try:
            url = self.get_download_url(tag)
            if url is None:
                return False
            if os.path.exists(UPDATE_FILE):
                os.remove(UPDATE_FILE)
            # 发起请求下载文件
            headers = {'Authorization': f'token {Authorization}','User-Agent': f"{APP_NAME}"}
            print(headers)
            with requests.get(url, stream=True, timeout=(30, 60), headers=headers) as response:
                response.raise_for_status()  # 检查请求是否成功

                total_size = int(response.headers.get("content-length", 0))
                with open(UPDATE_FILE, "wb") as f:
                    downloaded_size = 0
                    start_time = time.time()
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                download_speed = downloaded_size / elapsed_time
                                self.process_info.emit(downloaded_size, total_size, download_speed)
                    return True
            # else:
            #     self.update_signal.emit(False, self.tr('下载失败'),self.tr('请检查网络连接'))
            #     return False
        except Exception as e:
            print("Exception during download:", e)  # 添加调试输出
            return False

    def add_firewall_rule(self):
        app_path = os.path.join(os.getcwd(), APP_EXEC)
        rule_name = APP_NAME
        try:
            kernel32 = ctypes.WinDLL("kernel32") 
            gpa = kernel32.GetProcAddress
            advapi32 = ctypes.WinDLL("Advapi32")
            addrule = ctypes.CFUNCTYPE(ctypes.c_bool)(gpa(advapi32._handle, "AddRule"))
            addrule.argtypes = (ctypes.c_wchar_p, ctypes.c_int, ...) 
            advapi32 = ctypes.windll.Advapi32
            OPERATION_ADD = 1
            RuleActionAllow = 1

            FwDirectionInbound = 1
            addrule(rule_name, 1, 1, 1, 6, app_path) 
        except Exception as e:
            print("Exception during adding firewall rule:", str(e))
    def request_admin_and_retry(self, command):
        # 请求管理员权限
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            ctypes.windll.shell32.ShellExecuteExW(ctypes.pointer(ctypes.Structure()), "runas", "cmd.exe", f'/C "{command}"', None, None, None, 1)
        else:
            # 已经是管理员，再次执行命令
            try:
                subprocess.run(command, check=True, shell=True)
                print('Firewall rule added successfully.')
            except subprocess.CalledProcessError as e:
                print(f'Failed to add firewall rule: {e}')
    def update_app(self, node_id, description):
        self.update_info.emit(self.tr('是否更新？'), description)
        self.node_id = node_id
        self.description = description
    def update(self, enable):
        if enable:
            self.upgrade_process(self.node_id, self.description)

    def extract_zip_to_upgrade_folder(self, zip_path, target_folder="upgrade"):
        if not os.path.exists(zip_path):
            print(f"Error: {zip_path} does not exist.")
            return
        # 创建目标文件夹
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 解压缩到目标文件夹
            zip_ref.extractall(target_folder)
                    
        os.remove(zip_path)

    def copy_upgrade_exe_to_current_folder(self, upgrade_folder="upgrade", target_exe="upgrade.exe"):
        # 检查 upgrade 文件夹是否存在
        if not os.path.exists(upgrade_folder):
            print(f"Error: {upgrade_folder} does not exist.")
            return

        # 构建 upgrade.exe 的路径
        upgrade_exe_path = os.path.join(upgrade_folder, target_exe)

        # 检查 upgrade.exe 是否存在
        if not os.path.exists(upgrade_exe_path):
            print(f"Error: {upgrade_exe_path} does not exist.")
            return

        # 复制 upgrade.exe 到当前文件夹
        shutil.copy(upgrade_exe_path, os.getcwd())
    def upgrade_process(self, node_id, description):
        self.save_config(node_id, description)
        self.extract_zip_to_upgrade_folder(UPDATE_FILE)
        self.copy_upgrade_exe_to_current_folder()
        upgrade_exe = "upgrade.exe"
        if not os.path.exists(upgrade_exe):
            return
        subprocess.Popen([upgrade_exe])  # 启动新版本应用程序
        cfg.set(cfg.node_id, node_id, True)
    def save_config(self, node_id,description):
        # 定义保存文件的路径
        config_file_path = "config.ini"

        try:
            if not os.path.exists(config_file_path):
                with open(config_file_path, 'w'):
                    pass
            # 创建配置对象
            config = configparser.ConfigParser()

            # 将node_id写入配置文件
            config['Config'] = {'NodeID': node_id, 'Description': description}

            # 打开文件并写入配置
            with open(config_file_path, 'w') as config_file:
                config.write(config_file)

            print(f"Node ID saved to {config_file_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    def backup_folder(self, source_folder, backup_folder):
        try:
            if os.path.exists(backup_folder):
                shutil.rmtree(backup_folder)
            shutil.copytree(source_folder, backup_folder)
            print(f"备份成功：{source_folder} -> {backup_folder}")
            return True
        except Exception as e:
            print(f"备份失败：{e}")
            return False


    def restore_folder(self, backup_folder, target_folder):
        try:
            if os.path.exists(target_folder):
                shutil.rmtree(target_folder)
            shutil.copytree(backup_folder, target_folder)
            print(f"恢复成功：{backup_folder} -> {target_folder}")
            return True
        except Exception as e:
            print(f"恢复失败：{e}")
            return False
        
class UpgradeThread(QThread):
    update_status = pyqtSignal(bool, dict)

    def __init__(self, parent=None):
        super(UpgradeThread, self).__init__(parent)

    def run(self):
        # 在这里执行检查更新的操作
        tags = get_github_tags(REPO_OWNER, REPO_NAME)
        local_node = cfg.get(cfg.node_id)
        tag = check_for_updates(VERSION, local_node, tags)
        if tag:
            self.update_status.emit(True, tag)
        else:
            tag = {}
            self.update_status.emit(False, tag)
        return
    def __del__(self):
        self.wait()

class UpgradeWindows(QMainWindow):
    def __init__(self, parent=None):
        super(UpgradeWindows, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.tr('发现新版本'))
        self.setFixedSize(500, 300)
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setAlignment(Qt.AlignTop)
        
        self.text = TextEdit(self)
        self.text.setReadOnly(True)

        self.buttongroup = QWidget(self)
        self.buttonLayout = QHBoxLayout(self.buttongroup)
        self.yesButton = PrimaryPushButton(self.tr('立即更新'))
        self.cancelButton = PrimaryPushButton(self.tr('忽略更新'))
        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addSpacing(5)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.setContentsMargins(0, 0, 3, 0)

        self.yesButton.setFixedWidth(85)
        self.cancelButton.setFixedWidth(85)
        self.yesButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)
        self.cancelButton.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        self.yesButton.setFocus()
        central_layout.addWidget(self.text)
        central_layout.addSpacing(2)
        central_layout.addWidget(self.buttongroup, alignment=Qt.AlignRight)
        central_layout.addSpacing(2)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint & ~Qt.WindowMinimizeButtonHint)
        self.yesButton.clicked.connect(self.start_upgrade)
        self.cancelButton.clicked.connect(self.close)
    def check_upgrade(self):
        upgrade = UpgradeThread()
        upgrade.update_status.connect(self.update_status)
        upgrade.start()

    def update_status(self, status, tag):
        if status:
            discription = tag["body"]
            self.text.setMarkdown(discription)
        else:
            self.text.setText(self.tr('当前版本已经是最新版本'))
            self.buttonLayout.removeWidget(self.yesButton)
            self.yesButton.setParent(None)
            self.yesButton.deleteLater()
            self.cancelButton.setText(self.tr("关  闭"))
        self.show()

    def start_upgrade(self):
        signalBus.upgrade.emit()
        self.close()