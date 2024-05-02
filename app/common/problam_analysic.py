from qfluentwidgets import ExpandSettingCard,FluentIconBase,PrimaryPushButton,SmoothScrollDelegate,LineEdit,ToolButton,InfoBar,InfoBarIcon,InfoBarPosition
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtWidgets import QFileDialog,QHBoxLayout,QApplication,QVBoxLayout,QTreeWidget,QTreeWidgetItem,QTableWidget,QTableWidgetItem
from PyQt5.QtCore import Qt, QPropertyAnimation,QSize,QThread,QDate,QTime,QCoreApplication
from PyQt5.QtGui import QIcon, QFontMetricsF
from typing import Union
from .style_sheet import StyleSheet
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from pathlib import Path
import yaml,yaml_include
import time,sys,os
import importlib.util
from ..components.state_tools import DateTimePicker
import inspect
from datetime import datetime
from ..components.state_tools import CustomStateTool
from app.common.config import log_config
import sqlite3

class AnalysizeThread(QThread):
    result_change = pyqtSignal(dict)
    step_change = pyqtSignal(str)
    def __init__(self, conf_data, param_list, parent=None):
        super().__init__(parent)
        self.is_running = True
        self.param_list = param_list
        self.conf_data = conf_data
        self.result_info = self.conf_data.get("result", [])
        print(self.param_list)

    def run(self):
        # 读取配置文件
        jobs = self.conf_data.get("job",[])
        # 遍历每个步骤
        for step in jobs:
            # 获取步骤名称
            print(step)
            steps = step.get("steps",{})
            step_name = steps.get("name", "")
            self.step_change.emit(step_name)
            # 获取步骤详细信息
            step_details = steps.get("items", [])
            for detail in step_details:
                # 执行命令
                name = detail.get("name", "")
                run = detail.get("run", "")
                script = detail.get("script", "")
                function = detail.get("function", "")
                arg = detail.get("arg", "")
                return_value = detail.get("return", "")
                print(name, run, script, function, arg, return_value)

                if run != '':
                    # 如果步骤中指定了要执行的命令，则直接执行该命令
                    result = self.run_command(run)
                
                elif script and function:
                    if arg != '':
                        if isinstance(arg,dict):
                            param = []
                            # 如果步骤中指定了参数，则将参数赋值给指定的变量
                            for key, value in arg.items():
                                print(key, value)
                                if value.startswith("$"):
                                    value = value.replace("$", "")
                                param.append(self.param_list[value])
                        elif isinstance(arg,list):
                            param = []
                            for i in range(len(arg)):
                                pa = arg[i].replace("$", "")
                                param.append(self.param_list[pa])
                        else:
                            pa = arg.replace("$", "")
                            param = self.param_list[pa]
                    else:
                        param = None

                    # 如果步骤中指定了脚本文件和函数名，则执行对应的函数
                    result = self.execute_script_function(script, function, param, self.result_change)
                    print(result, return_value)
                    if return_value != '':
                        return_value = return_value.replace("$", "")
                        # 如果步骤中指定了返回值，则将函数执行结果赋值给指定的变量
                        print(return_value)
                        func_result = result.get("result", "")
                        self.param_list[return_value] = func_result

                    print(f"Result of {function}: {result}")
                else:
                    err_code = "No script or function specified for this step"
                    {"state":False, "result":err_code,"other":""}
                # 更新结果
                uiinfo = result.get("uiinfo", "")
                print(uiinfo)
                self.result_change.emit(uiinfo)

        # 执行完毕后，停止线程
        self.is_running = False
        self.finished.emit()
        return
    def import_scripts_from_directory(directory):
        # 确保路径存在且是文件夹
        if not os.path.exists(directory) or not os.path.isdir(directory):
            print(f"Error: '{directory}' is not a valid directory.")
            return []

        # 遍历目录中的所有文件
        script_modules = []
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            # 检查文件是否为 Python 脚本文件
            if filename.endswith('.py') and os.path.isfile(filepath):
                # 尝试导入脚本文件
                try:
                    spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
                    script_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(script_module)
                    script_modules.append(script_module)
                    print(f"Imported script module from '{filepath}'")
                except Exception as e:
                    print(f"Error importing script module from '{filepath}': {e}")

        return script_modules

    def run_command(self, command):
        import subprocess
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return {"state":True, "result":result.stdout.strip(),"uiinfo":{"执行步骤":command, "执行结果":"成功", "失败原因":"无", "时间":f"{datetime.now()}"}}
        except subprocess.CalledProcessError as e:
            print(f"Error executing command '{command}': {e}")
            return {"state":False, "result":e.returncode,"uiinfo":{"执行步骤":command, "执行结果":"失败", "失败原因":e.returncode, "时间":f"{datetime.now()}"}}


    def execute_script_function(self, script_path, function_name, args, singal=None):
        try:
            # 导入脚本文件
            current_directory = os.path.dirname(__file__)
            parent_directory = os.path.dirname(current_directory)
            parent_directory = os.path.dirname(parent_directory)
            os.chdir(parent_directory)
            spec = importlib.util.spec_from_file_location("script_module", script_path)
            script_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(script_module)

            # 检查函数是否存在
            if hasattr(script_module, function_name):
                script_function = getattr(script_module, function_name)
                # 获取函数的签名
                sig = inspect.signature(script_function)
                # 获取函数参数的数量
                num_params = len(sig.parameters)
                
                # 执行函数
                if num_params == 0:
                    try:
                        result = script_function()
                        return result
                    except Exception as e:
                        return {"state":False, "result":{e},"uiinfo":{"执行步骤":function_name, "执行结果":"失败", "失败原因":f"{e}", "时间":f"{datetime.now()}"}}
                elif num_params == 1:
                    try:
                        result = script_function(args)
                        return result
                    except Exception as e:
                        log_config.log_error(f"Error executing script function '{function_name}': {e}")
                        return {"state":False, "result":{e},"uiinfo":{"执行步骤":function_name, "执行结果":"失败", "失败原因":f"{e}", "时间":f"{datetime.now()}"}}
                elif num_params == 2:
                    try:
                        result = script_function(args, singal)
                        return result
                    except Exception as e:
                        log_config.log_error(f"Error executing script function '{function_name}': {e}")
                        return {"state":False, "result":{e},"uiinfo":{"执行步骤":function_name, "执行结果":"失败", "失败原因":f"{e}", "时间":f"{datetime.now()}"}}
                else:
                    # 处理其他情况，例如参数数量超过 2 个的情况
                    pass
            else:
                err = f"Function '{function_name}' not found in script file '{script_path}'"
                log_config.log_error(err)
                return {"state":False, "result":err,"uiinfo":{"执行步骤":function_name, "执行结果":"失败", "失败原因":err, "时间":f"{datetime.now()}"}}
        except Exception as e:
            err = f"Error executing script function '{function_name}': {e}"
            log_config.log_error(err)
            return {"state":False, "result":err,"uiinfo":{"执行步骤":function_name, "执行结果":"失败", "失败原因":err, "时间":f"{datetime.now()}"}}
        
    def stop(self):
        self.is_running = False
        self.wait()
        self.terminate()
        



class FileChooserWidget(QWidget):
    file_path_change = pyqtSignal(str)
    def __init__(self, info:str, file_type=1, parent=None):
        super().__init__()
        self.file_type = file_type
        self.file_info = info
        self.floder_path = ""
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout()
        self.browse_button = QPushButton('点击选择文件')
        self.browse_button.clicked.connect(self.openFileDialog)

        self.layout.addWidget(self.browse_button)
        self.setLayout(self.layout)

    def openFileDialog(self):
        file_dialog = QFileDialog()
        if self.file_type:
            folder_path = file_dialog.getExistingDirectory(self, self.file_info)
        else:
            folder_path, _ = file_dialog.getOpenFileName(self, self.file_info)
        if folder_path :
            self.browse_button.setText(folder_path )
            self.file_path_change.emit(folder_path )
            self.floder_path = folder_path
    def get_file_path(self):
        return self.floder_path
    
    def setEnabled(self, state:bool):
        self.browse_button.setEnabled(state)



class ProblemAnalysic(ExpandSettingCard):
    deleteconf = pyqtSignal(ExpandSettingCard)
    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, texts=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.setExpand(False)
        # self.card.setTitle("数据缺失问题分析")
        self.data = None
        self.params = {}
        self.parent_item = None
        self.last_status = None
        self.param_list = {}
        self.exec_info = []
        self.file_path = None
        self.card.removeEventFilter(self.card)
        self._adjustViewSize()  



    def set_exec_info(self, exec_info:list):
        self.exec_info = exec_info.copy()
        self.button = PrimaryPushButton("开始分析")
        self.button.clicked.connect(self.try_to_analyse)
        self.button.setProperty('is_start', True)
        # 将树形控件和按钮添加到布局
        self.button.setFixedSize(80,30)
        self.viewLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.tree = QTreeWidget(self.view)
        StyleSheet.CUSTOM_TREE.apply(self.tree)
        self.smothscroller = SmoothScrollDelegate(self.tree)
        self.tree.setFixedHeight(400)

        self.tree.setColumnCount(len(exec_info))
        self.tree.setHeaderLabels(exec_info)

        self.update_tree_size()

        self.viewLayout.addWidget(self.tree)
        self._adjustViewSize() 

    def update_tree_size(self):
        if len(self.exec_info):
            w = int((self.tree.width() - 20) / len(self.exec_info))
            for i, value in enumerate(self.exec_info):
                self.tree.header().resizeSection(i, w)


    def set_conf_path(self, conf_path:str):
        self.file_path = conf_path
        self.path_label = QLabel(f'配置文件: {conf_path}')
        self.card.addWidget(self.path_label)
        self.syncutton = ToolButton()
        self.syncutton.setFixedSize(20, 20)
        self.syncutton.setIcon(FIF.SYNC)
        self.syncutton.setStyleSheet("background: transparent; border-radius: 0px")
        self.card.addWidget(self.syncutton)
        self.syncutton.clicked.connect(self.sync_conf)


        self.deletebutton = ToolButton()
        self.deletebutton.setIcon(FIF.DELETE)
        self.deletebutton.setStyleSheet("background: transparent; border-radius: 0px")
        self.card.addWidget(self.deletebutton)
        self.deletebutton.clicked.connect(self.delete_conf)

        self.set_base_info()

    def delete_conf(self):
        self.deleteconf.emit(self)

    def sync_conf(self):
        # self.setExpand(False)
        self.clearLayout()
        self.view.repaint()
        self.viewLayout.update()
        QCoreApplication.processEvents()
        self._adjustViewSize() 
        self.set_base_info()
        QCoreApplication.processEvents()
        self.view.repaint()
        self.viewLayout.update()
        self._adjustViewSize() 

    def clearLayout(self):
        while self.viewLayout.count():
            item = self.viewLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                self.viewLayout.removeWidget(widget)
            else:
                subLayout = item.layout()
                if subLayout is not None:
                    while subLayout.count():
                        subItem = subLayout.takeAt(0)
                        subWidget = subItem.widget()
                        if subWidget:
                            subWidget.deleteLater()
                            subLayout.removeWidget(subWidget)
                    subLayout.setParent(None)


    def load_conf(self, conf_path:str):
        # 加载配置文件
        file_path = Path(conf_path)
        if file_path.exists() == False:
            folder_path = Path('app/config/task_plan')
            source_path = Path("_internal/app/config/task_plan")
            # shutil.copytree(source_path, folder_path)

        # 添加自定义构造器以支持 !include 标签
        # folder_path = Path('app/config/task_plan')
        # yaml.add_constructor("!inc", yaml_include.Constructor(base_dir=folder_path))

        # 检查文件是否存在并加载YAML数据
        if not Path(file_path).exists():
            print(f"File not found: {self.file_path}")
            return

        with open(file_path, 'r', encoding="utf-8") as file:
            self.data = yaml.full_load(file)

    def set_base_info(self):
        self.load_conf(self.file_path)
        name = self.data.get("name", "")
        content = self.data.get("content", "")
        result_info = self.data.get("result", [])
        inputs= self.data.get("input", [])

        self.card.setTitle(name)
        self.card.setContent(content)
        # self.setWindowTitle(name)
        for item in inputs:
            name = item.get('name', '')
            ui_type = item.get('ui_type', '')
            param = item.get('param', '')
            type = item.get('type', '')
            layout = QHBoxLayout()
            label = QLabel(name)
            layout.addWidget(label)

            if ui_type == 'path':
                input_widget = FileChooserWidget(name)
            elif ui_type == 'text':
                input_widget = LineEdit()
            elif ui_type == 'datetime':
                current_date = QDate.currentDate()
                current_time = QTime.currentTime()
                input_widget = DateTimePicker()
                input_widget.setDateTime(current_date, current_time)
            else:
                input_widget = None
            
            if input_widget is None:
                raise Exception(f"不支持的输入类型: {ui_type}")
            input_widget.setObjectName(name)
            param = param.replace("$", "")
            param_map = {"widget": input_widget, "name": name, "type": type}
            self.params[param] = param_map
            layout.addWidget(input_widget)
            self.viewLayout.addLayout(layout)

        self.set_exec_info(result_info)
        self._adjustViewSize() 

    def try_to_analyse(self):
        is_start = self.button.property('is_start')
        if is_start:
            self.button.setText('停止分析')
            self.button.setProperty('is_start', False)
            self.set_input_state(False)
            self.analyse()
        else:
            self.button.setText('开始分析')
            self.button.setProperty('is_start', True)
            self.set_input_state(True)
            self.stop_analyse()

    def analyse(self):
        self.tree.clear()
        self.param_list.clear()
        if self.base_param_get():
            self.analysize_thread = AnalysizeThread(self.data, self.param_list)
            self.analysize_thread.result_change.connect(self.add_info_list)
            self.analysize_thread.finished.connect(self.thread_finished)
            self.analysize_thread.step_change.connect(self.change_parent_item)
            self.analysize_thread.start()
        else:
            self.button.setText('开始分析')
            self.set_input_state(True)
            self.button.setProperty('is_start', True)

    def stop_analyse(self):
        self.analysize_thread.stop()
        self.parent_item = None

    def thread_finished(self):
        self.button.setText('开始分析')
        self.button.setProperty('is_start', True)
        self.set_input_state(True)
        if self.last_status is not None:
            self.last_status.setComPlate()
            self.last_status.seticon(FIF.COMPLETED)
            # self.last_status.setContent(self.tr("执行结束"))
        
        self.parent_item = None
        self.last_status = None

    def get_value_by_type(self, value:str, type):
        if type == 'int':
            return int(value, 16)
        elif type == 'float':
            return float(value)
        elif type == 'timestamp':
            return int(value)
        elif type == 'str':
            return value
        

    def base_param_get(self):
        for key, value in self.params.items():
            widget = value.get('widget', None)
            type = value.get('type', None)
            name = widget.objectName()
            if isinstance(widget, FileChooserWidget):
                param_value = widget.get_file_path()
            elif isinstance(widget, LineEdit):
                param_value = widget.text()
            elif isinstance(widget, DateTimePicker):
                param_value = widget.getDateTimeStamp() 
            if param_value == '' or param_value is None:
                content = f'{name}内容不能为空'
                self.param_list[key] = None
                infoBar = InfoBar(
                icon=InfoBarIcon.ERROR,
                title=self.tr('错误'),
                content=content,
                orient=Qt.Vertical,
                isClosable=True,
                duration=2000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
                infoBar.show()
                return False
            self.param_list[key] = self.get_value_by_type(param_value, type)
        
        return True


    def set_input_state(self, status):
        for key, value in self.params.items():
            widget = value.get('widget', None)
            if isinstance(widget, FileChooserWidget):
                widget.setEnabled(status)
            elif isinstance(widget, LineEdit):
                widget.setEnabled(status)
            elif isinstance(widget, DateTimePicker):
                widget.setEnabled(status)

    def add_info_list(self, texts:dict):
        item = QTreeWidgetItem(self.parent_item if self.parent_item else self.tree)
        count = self.tree.columnCount()
        for i, info in enumerate(self.exec_info):
            for key, value in texts.items():
                if key == info:
                    item.setText(i, str(value))

        self.parent_item.setExpanded(True)
        self._adjustViewSize()
        self.tree.verticalScrollBar().setValue(self.tree.verticalScrollBar().maximum())

    def change_parent_item(self, current_name):
        # if self.parent_item is not None:
            # self.parent_item.setText(1, "执行结束")
        if self.last_status is not None:
            self.last_status.setComPlate()
            self.last_status.seticon(FIF.COMPLETED)
            # self.last_status.setTitle(self.tr("执行结束"))


        self.parent_item = QTreeWidgetItem(self.tree)
        # 创建一个垂直布局
        last_status = CustomStateTool(FIF.SYNC, 12, self.tree)
        layout = QVBoxLayout()
        layout.addWidget(last_status)

        # 创建一个小部件来容纳垂直布局
        widget = QWidget()
        widget.setLayout(layout)

        # 在树中设置部件，第一个参数为行，第二个参数为列，第三个参数为部件
        self.tree.setItemWidget(self.parent_item, 1, widget)

        # 在垂直布局中居中对齐部件
        layout.setAlignment(Qt.AlignLeft)
        layout.setContentsMargins(1,2,1,2)

        self.last_status = last_status
        # last_status.setFixedHeight(20)
        last_status.show()
        self.parent_item.setText(0, current_name)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.update_tree_size()