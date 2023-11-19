# coding:utf-8
import sys
from enum import Enum
from lxml import etree as ET
from pathlib import Path
from PyQt5.QtCore import QLocale,QObject,pyqtSignal
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, ConfigValidator,__version__)

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

    ReportReplay = ConfigItem("BasicSeting", "ReportReplay", True, BoolValidator())

    Region = OptionsConfigItem("BasicSeting", "region", "南网", OptionsValidator(["南网","云南","广东","深圳","广西","贵州","海南"]), restart=False)

    Multireport = ConfigItem("BasicSeting", "Multireport", True, BoolValidator())
    MultireportAdress = ConfigItem("BasicSeting", "MultireportAdress", [], validator=None)

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
    
    def get_item(self, item_id, protocol, region):
        def is_vaild_data_item(data_item, target_protocol, tagrget_region):
            attri_protocol = data_item.get('protocol')
            if attri_protocol is not None:
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
        def find_target_dataitem(root, target_id, target_protocol, region):
            target_node = root.findall(".//*[@id='{}']".format(target_id,target_protocol,region))
            if target_node is None:
                print("No node found with id {} protocol {} and region {}".format(target_id))
                return None
            #当前标签无法找到
            for node in target_node:
                if is_vaild_data_item(node, target_protocol, region):
                    return node
                else:
                    parent = node.getparent()
                    while parent is not None:
                        if is_vaild_data_item(parent, target_protocol, region):
                            return node
                        parent = parent.getparent()
            print("No parent found with protocol {} and region {}".format(target_protocol,region))
            return None
        if self.config is None:
            return None
        root = self.config.getroot()
        target = find_target_dataitem(root, item_id, protocol, region)
        if target is None:
            region = "南网"
            target = find_target_dataitem(root, item_id, protocol, region)
        return target


YEAR = 2023
AUTHOR = "zhiyiYo"
VERSION = __version__
HELP_URL = "https://qfluentwidgets.com"
REPO_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets"
EXAMPLE_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/master/examples"
FEEDBACK_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues"
RELEASE_URL = "https://github.com/zhiyiYo/PyQt-Fluent-Widgets/releases/latest"
SUPPORT_URL = "https://afdian.net/a/zhiyiYo"


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)


config_645 = QframeConfig()
config_645.load('app/config/DLT645.xml')

config_csg13 = QframeConfig()
config_csg13.load('app/config/CSG13.xml')