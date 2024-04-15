# coding:utf-8
import shutil
import os
import sys
import yaml,yaml_include
from enum import Enum
from lxml import etree as ET
from pathlib import Path
from PyQt5.QtCore import QLocale,QObject,pyqtSignal
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, ConfigValidator,__version__)
import logging
from datetime import datetime
class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

class ConfigGroupItem(QObject):
    configChanged = pyqtSignal()

    def __init__(self, group, name):
        super().__init__()
        self.config_items = {}
        self.group = group
        self.name = name

    def add_config_item(self, config_item):
        self.config_items[config_item.key] = config_item
        config_item.valueChanged.connect(self.config_item_changed)

    def config_item_changed(self):
        self.configChanged.emit()

    def reset_to_defaults(self):
        for config_item in self.config_items.values():
            config_item.value = config_item.defaultValue
        self.configChanged.emit()

    def get_config_item(self, key):
        return self.config_items.get(key)

    def serialize(self):
        serialized = {}
        for key, config_item in self.config_items.items():
            serialized[key] = config_item.serialize()
        return serialized

    def deserialize_from(self, serialized):
        for key, value in serialized.items():
            config_item = self.get_config_item(key)
            if config_item:
                config_item.deserializeFrom(value)

    def __str__(self):
        return f'{self.__class__.__name__}[group={self.group}, name={self.name}, config_items={len(self.config_items)}]'
    
class StringValidator(ConfigValidator):
    def __init__(self, regex_pattern=None):
        self.regex_pattern = regex_pattern

    def validate(self, value):
        if self.regex_pattern:
            import re
            return bool(re.match(self.regex_pattern, value))
        else:
            return True

    def correct(self, value):
        # 对于字符串，通常不需要纠正
        return value
     
class Config(QConfig):
    """ Config of application """

    # folders
    musicFolders = ConfigItem(
        "Folders", "LocalMusic", [], FolderListValidator())
    logFolder = ConfigItem(
        "Folders", "Log", "app/log", FolderValidator())
    messageFolder = ConfigItem(
        "Folders", "AppInterface", "app/config/appinterface", FolderValidator())
    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # Material
    blurRadius  = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

    # 在串口配置项中添加具体的串口参数
    serial_BaudRate = ConfigItem("Serial", "BaudRate", 9600, OptionsValidator([2400, 4800, 9600, 115200]), restart=False)
    serial_parity = ConfigItem("Serial", "Parity", "偶校验", OptionsValidator(["无校验", "偶校验", "奇校验"]), restart=False)
    serial_databit = ConfigItem("Serial", "DataBits", 8, OptionsValidator([5, 6, 7, 8]), restart=False)
    serial_stopbit = ConfigItem("Serial", "StopBits", 1, OptionsValidator([1, 1.5, 2]), restart=False)


    tcpClientIP = ConfigItem("TcpClient", "IP", "127.0.0.1", StringValidator(regex_pattern=r'^(\d{1,3}\.){3}\d{1,3}$'))
    tcpClientPort = ConfigItem("TcpClient", "Port", 1002)

    tcpServerIP = ConfigItem("TcpServer", "IP", "127.0.0.1", StringValidator(regex_pattern=r'^(\d{1,3}\.){3}\d{1,3}$'))
    tcpServerPort = ConfigItem("TcpServer", "Port", 1002)

    mqttip = ConfigItem("Mqtt", "IP", "127.0.0.1", StringValidator(regex_pattern=r'^(\d{1,3}\.){3}\d{1,3}$'))
    mqttport = ConfigItem("Mqtt", "Port", 1883)
    mqttuser = ConfigItem("Mqtt", "user", "None", validator=None)
    mqttpasswd = ConfigItem("Mqtt", "passwd", "None", validator=None)
    
    ReportReplay = ConfigItem("BasicSeting", "ReportReplay", True, BoolValidator())

    Region = OptionsConfigItem("BasicSeting", "region", "南网", OptionsValidator(["南网","云南","广东","深圳","广西","贵州","海南","topo"]), restart=False)

    Multireport = ConfigItem("BasicSeting", "Multireport", False, BoolValidator())
    MultireportAdress = ConfigItem("BasicSeting", "MultireportAdress", [], validator=None)
    node_id = ConfigItem("Version", "node_id", "None", validator=None)

class QframeConfig(QObject):
    """ Config of app """

    appRestartSig = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.file = Path("config/CSG13.xml")
        self._cfg = self
        self.config = None

    def get(self, item):
        """ get the value of config item """
        return item.value

    def load(self, file=None, config=None):
        """ load config

        Parameters
        ----------
        file: str or Path
            the path of json config file

        config: Config
            config object to be initialized
        """
        if isinstance(config, QConfig):
            self._cfg = config

        if isinstance(file, (str, Path)):
            self._cfg.file = Path(file)
            if self._cfg.file.exists() == False:
                self._cfg.file.parent.mkdir(parents=True, exist_ok=True)
                source_path = Path(f"_internal/{file}")
                try:
                    source_path.replace(self._cfg.file)
                except:
                    self._cfg.file = source_path
        try:
            with open(self._cfg.file, encoding="utf-8") as f:
                self.config = ET.parse(f)
        except:
            self.config = None
    def get_template_item(self, template, protocol, region):
        if self.config is None:
            return None
        root = self.config.getroot()
        def find_template_element(root, target_id, target_protocol, region):
            template_attributes = {
                "id": target_id,
                "protocol": target_protocol,
                "region": region
            }

            # Find the <template> element with the specified attributes
            template_element = None
            for template in root.findall(".//template"):
                if all(template.get(attr) == value for attr, value in template_attributes.items()):
                    template_element = template
                    break

            return template_element
        protocol = protocol.lower()
        target = find_template_element(root, template, protocol, region)
        if target is None:
            protocol = protocol.upper()
            target = find_template_element(root, template, protocol, region)
            if target is None:
                region = "南网"
                protocol = protocol.lower()
                target = find_template_element(root, template, protocol, region)
                if target is None:
                    protocol = protocol.upper()
                    target = find_template_element(root, template, protocol, region)
        return target
    
    def get_item(self, item_id, protocol, region, dir=None):
        def is_vaild_data_item(data_item, target_protocol, tagrget_region, dir=None):
            attri_protocol = data_item.get('protocol')
            if attri_protocol is not None:
                attri_dir = data_item.get('dir')
                if attri_dir is not None and dir is not None:
                    if int(attri_dir) != dir:
                        return False
                protocols = [protocol.upper() for protocol in attri_protocol.split(',')]
                # 判断目标protocol是否在列表中
                target_protocol = target_protocol.upper()
                if target_protocol in protocols:
                    attri_region = data_item.get('region')
                    if attri_region is not None:
                        regions = attri_region.split(',')
                        if tagrget_region in regions:
                            return True
            return False
        def find_target_dataitem(root, target_id, target_protocol, region, dir=None):
            target_node = root.findall(".//*[@id='{}']".format(target_id,target_protocol,region))
            if target_node is None:
                print("No node found with id {} protocol {} and region {}".format(target_id,target_protocol,region))
                return None
            #当前标签无法找到
            print("found with id {} protocol {} and region {}".format(target_id,target_protocol,region))
            for node in target_node:
                if is_vaild_data_item(node, target_protocol, region, dir):
                    return node
                else:
                    parent = node.getparent()
                    while parent is not None:
                        if is_vaild_data_item(parent, target_protocol, region, dir):
                            return node
                        parent = parent.getparent()
            print("No parent found with protocol {} and region {}".format(target_protocol,region))
            return None
        if self.config is None:
            return None
        root = self.config.getroot()
        protocol = protocol.lower()
        target = find_target_dataitem(root, item_id, protocol, region, dir)
        if target is None:
            protocol = protocol.upper()
            target = find_target_dataitem(root, item_id, protocol, region, dir)
            if target is None:
                region = "南网"
                protocol = protocol.lower()
                target = find_target_dataitem(root, item_id, protocol, region, dir)
                if target is None:
                    protocol = protocol.upper()
                    target = find_target_dataitem(root, item_id, protocol, region, dir)
        return target
    
class LogConfig:
    def __init__(self, log_dir='app/log', log_level=logging.INFO):
        # 获取当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')

        # 创建日期命名的日志文件夹
        log_folder = os.path.join(log_dir, current_date)
        os.makedirs(log_folder, exist_ok=True)

        # 设置日志器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # 创建文件处理器并设置格式
        log_path = os.path.join(log_folder, 'sys_log.log')
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 创建控制台处理器并设置格式
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log_info(self, message, exc_info=True):
        self.logger.info(message,exc_info=exc_info)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message,exc_info=True):
        self.logger.error(message,exc_info=exc_info)

    def log_critical(self, message,exc_info=True):
        self.logger.critical(message,exc_info=exc_info)


class OadFinder:
    def __init__(self, file_path):
        self.data = None
        self.file_path = Path(file_path)
        if self.file_path.exists() == False:
            folder_path = Path('app/config/task_plan')
            source_path = Path("_internal/app/config/task_plan")
            shutil.copytree(source_path, folder_path)

        # 添加自定义构造器以支持 !include 标签
        folder_path = Path('app/config/task_plan')
        yaml.add_constructor("!inc", yaml_include.Constructor(base_dir=folder_path))

        # 检查文件是否存在并加载YAML数据
        if not Path(self.file_path).exists():
            print(f"File not found: {file_path}")
            return

        with open(self.file_path, 'r', encoding="utf-8") as file:
            self.data = yaml.full_load(file)

    def find_oad_info(self, master_oad_id, virtual_oad_id):
        if self.data is None:
            return None
        
        try:
            for oad_list in self.data.get("Oad_List", []):
                if oad_list.get('master_oad') == master_oad_id:
                    voad_list = oad_list.get('file')
                    if isinstance(voad_list, dict):
                        for key, value in voad_list.items():
                            if isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict) and 'V_oad' in item and item['V_oad'] == virtual_oad_id:
                                        return item
        except Exception as e:
            log_config.log_error(f"find_oad_info error: {e} {master_oad_id} {virtual_oad_id}")
        
        return None

YEAR = 2023
AUTHOR = "ZeroJack"
REPO_OWNER = "ZerojackShi"
REPO_NAME = "Assistent"
APP_NAME = "Assistent"
VERSION = "1.0.0"
HELP_URL = "https://gitee.com/zerokit/assistent"
REPO_URL = "https://gitee.com/zerokit/assistent"
EXAMPLE_URL = "https://gitee.com/zerokit/assistent"
FEEDBACK_URL = "https://gitee.com/zerokit/assistent/issues"
RELEASE_URL = "https://gitee.com/zerokit/assistent/releases"
SUPPORT_URL = "https://gitee.com/zerokit/assistent"
CONFIG_DIR = 'app/config'
Authorization = "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"
UPDATE_FILE = './upgrade.zip'
UPDATE_DIR = 'upgrade'
APP_EXEC = "Assistent.exe"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)


config_645 = QframeConfig()
config_645.load('app/config/DLT645.xml')

config_csg13 = QframeConfig()
config_csg13.load('app/config/CSG13.xml')

log_config = LogConfig()

# 使用示例
oad_finder = OadFinder(f'{CONFIG_DIR}/task_plan/oad_list.yml')
