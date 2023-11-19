from PyQt5 import QtWidgets, QtCore
import json
import os
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QTableWidget,
    QMessageBox,
)
class ConfigCustomTreeWidget(QtWidgets.QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(11)

        self.ConfigContex = ["数据项", "数据项名称", "数据长度", "单位", "小数位"]
        self.text_input_mapping = {}  # 存储文本和输入框的映射关系

        self.header().setHidden(True)
        self.add_tree_item(self, self.ConfigContex, None)  # Add tree item using top-level item as parent

        # 设置列宽度调整模式为自动调整
        header = self.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def add_tree_item(self, parent, item_list, node_data):
        child_item = QtWidgets.QTreeWidgetItem(parent)
        child_key = id(child_item)
        parent_key = id(parent)
        # mapping = {'id': child_key, 'children': [], 'mapping': {}}

        for i, text in enumerate(item_list):
            child_item.setText(i * 2, text)

            edit = QtWidgets.QLineEdit()
            edit.textChanged.connect(lambda text, column=i, item=child_item:
                                     self.adjust_column_width(item, column))
            if i >= 2 and i < 5:
                edit.setFixedWidth(30 + 10)
            else:
                edit.setFixedWidth(100 + 10)

            self.setItemWidget(child_item, i * 2 + 1, edit)
            # mapping['mapping'][i] = {'text': text, 'widget': edit}

            # if node_data is not None:
            #     if text in node_data:
            #         value = node_data[text]
            #         if i < 5:
            #             edit.setText(value)
            #         else:
            #             edit.setCurrentText(value)

        # self.update_mapping(parent, child_item, mapping)  # 更新映射关系

        # if node_data is not None:
        #     if "children" in node_data:
        #         for child_data in node_data["children"]:
        #             self.add_tree_item(child_item, self.ConfigContex,
        #                                child_data)

        self.expandItem(child_item)
        self.adjust_column_widths()  # 调整列宽度
        return child_item

    def showContextMenu(self, pos):
        selected_item = self.currentItem()
        if selected_item is None:
            return

        menu = QtWidgets.QMenu(self)

        add_parent_action = QtWidgets.QAction("添加主节点", self)
        add_parent_action.triggered.connect(self.add_main_node)
        menu.addAction(add_parent_action)

        add_child_action = QtWidgets.QAction("添加子节点", self)
        add_child_action.triggered.connect(self.add_child_node)
        menu.addAction(add_child_action)

        add_parent_action = QtWidgets.QAction("添加长度拆分节点", self)
        add_parent_action.triggered.connect(self.add_langth_crack_node)
        menu.addAction(add_parent_action)

        add_child_action = QtWidgets.QAction("添加位拆分节点", self)
        add_child_action.triggered.connect(self.add_bit_crack_node)
        menu.addAction(add_child_action)

        delete_action = QtWidgets.QAction("删除节点", self)
        delete_action.triggered.connect(self.delete_selected_item)
        menu.addAction(delete_action)

        global_pos = self.viewport().mapToGlobal(pos)
        menu.exec_(global_pos)

    def add_main_node(self):
        selected_item = self.currentItem()
        if selected_item is not None:
            parent = selected_item.parent() or self
            self.add_tree_item(parent, self.ConfigContex, None)

    def add_child_node(self):
        selected_item = self.currentItem()
        if selected_item is not None:
            select_key = id(selected_item.parent())
            self.add_tree_item(selected_item, self.ConfigContex, None)

    def add_langth_crack_node(self):
        selected_item = self.currentItem()
        if selected_item is not None:
            data_list = [
                "数据项名称",
                "长度",
                "编码",
            ]
            self.add_tree_item(selected_item, data_list, None)

    def add_bit_crack_node(self):
        selected_item = self.currentItem()
        if selected_item is not None:
            data_list = [
                "数据项名称",
                "bit"
            ]
            self.add_tree_item(selected_item, data_list, None)

    def delete_selected_item(self):
        selected_item = self.currentItem()
        if selected_item is not None:
            parent_item = selected_item.parent()
            parent_key = id(parent_item) if parent_item else None
            current_key = id(selected_item)
            root_node = self.get_root_node(selected_item)
            root_key = id(root_node)

            if root_key in self.text_input_mapping:
                root_mapping = self.text_input_mapping[root_key]
                parent_mapping = self.find_mapping(root_mapping, parent_key) if parent_key else root_mapping
                if parent_mapping:
                    children_mappings = parent_mapping['children']
                    self.remove_mapping_recursively(parent_mapping, current_key)
                    parent_mapping['mapping'].pop(current_key, None)
                    self.text_input_mapping[root_key] = root_mapping

            if parent_item is not None:
                parent_item.removeChild(selected_item)

    def get_root_node(self, node_item):
        parent = node_item.parent()
        if parent is None:
            return node_item  # This is the root node
        else:
            return self.get_root_node(parent)

    def get_mapping(self, current_item):
        if current_item is None:
            return self.text_input_mapping

        root_item = self.get_root_node(current_item)
        parent_key = id(root_item)
        if parent_key in self.text_input_mapping:
            return self.find_mapping(self.text_input_mapping.get(parent_key),
                                     id(current_item))
        return None

    def find_mapping(self, mapping, key):
        if mapping['id'] == key:
            return mapping
        for child_mapping in mapping['children']:
            found_mapping = self.find_mapping(child_mapping, key)
            if found_mapping:
                return found_mapping
        return None


    def update_mapping(self, parent_item, current_item, mapping):
        root_node = self.get_root_node(parent_item)
        root_key = id(root_node)

        if root_key not in self.text_input_mapping:
            # Root node mapping doesn't exist, create a new one
            root_mapping = mapping
            root_key = id(current_item)
            self.text_input_mapping[root_key] = root_mapping
        else:
            root_mapping = self.text_input_mapping[root_key]
            parent_key = id(parent_item)
            parent_mapping = self.find_mapping(root_mapping, parent_key)
            if parent_mapping:
                parent_mapping['children'].append(mapping)
            else:
                root_mapping['children'].append(mapping)

            self.text_input_mapping[root_key] = root_mapping


    def collect_child_edit_from_mapping(self, mapping, text, edit_list):
        for _, value in mapping['mapping'].items():
            if value['text'] == text:
                edit_list.append(value['widget'])

        for child_mapping in mapping['children']:
            self.collect_child_edit_from_mapping(child_mapping, text, edit_list)

    def find_edits_with_text(self,mapping, text):
        edits = []
        for key, value in mapping.items():
            self.collect_child_edit_from_mapping(value, text, edits)
        return edits


    def remove_mapping_recursively(self, mapping, key):
        if mapping['id'] == key:
            return True

        children_mappings = mapping['children']
        for child_mapping in children_mappings:
            if self.remove_mapping_recursively(child_mapping, key):
                children_mappings.remove(child_mapping)
                return True

        return False

    def adjust_column_widths(self):
        column_count = self.columnCount()
        for column in range(column_count):
            self.resizeColumnToContents(column)

    def adjust_column_width(self, item, column):
        default_with = [100, 100, 30, 30, 30, 30]
        self.resizeColumnToContents(column)
        max_width = 0
        # item = self.currentItem()
        text = item.text(column * 2)
        mapping_edit = self.find_edits_with_text(self.text_input_mapping, text)
        for edit in mapping_edit:
            if isinstance(edit, QtWidgets.QLineEdit):
                width = edit.fontMetrics().width(edit.text())
                max_width = max(max_width, width)
        if max_width < default_with[column]:
            max_width = default_with[column]

        for edit in mapping_edit:
            edit.setFixedWidth(max_width + 10)  # Add some extra width

        self.setColumnWidth(column * 2 + 1, max_width + 10)  # 加上一些额外的宽度
        self.adjust_column_widths()


    # def handle_combobox_selection(self, index):
    #     selected_item = self.currentItem()
    #     if selected_item is not None:
    #         item_widget = self.itemWidget(selected_item, 11)
    #         if item_widget is not None and index == 1:  # Index 1 corresponds to the "是" option
    #             self.add_tree_item(selected_item, self.ConfigContex, None)

    def find_node_by_value(self, data, data_item):
        if isinstance(data, dict):
            if '数据项' in data and data['数据项'] == data_item:
                return data
            for key, value in data.items():
                result = self.find_node_by_value(value, data_item)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self.find_node_by_value(item, data_item)
                if result is not None:
                    return result
        return None

    def find_root_node_by_value(self, data, value):
        for key, root_node in data.items():
            result = self.find_node_by_value(root_node, value)
            if result is not None:
                return root_node
        return None

    def find_top_level_root_nodes(self,data, node):
        root_nodes = []
        parent_node = node
        while parent_node is not None:
            root_nodes.append(parent_node)
            parent_key = next(iter(parent_node))
            parent_node = data.get(parent_key)
        return root_nodes

    def read_config(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, ":/gallery/images/config.json")
        with open(file_path, "r", encoding='utf-8') as file:
            try:
                json_data = json.load(file)
            except json.decoder.JSONDecodeError:
                json_data = {}
        current_item = self.currentItem()
        root_node = self.get_root_node(current_item)
        key = id(root_node)
        value = self.text_input_mapping[key]['mapping'][0]['widget'].text()
        matching_nodes = self.find_root_node_by_value(json_data, value)
        if matching_nodes is None:
            QMessageBox.warning(self, '错误：', '未找到数据标识！',
                                QMessageBox.Ok)
        else:
            self.update_tree_widget(matching_nodes)

    def update_tree_widget(self, root_nodes):
        # 清空原有的树形列表内容
        self.text_input_mapping = {}
        self.clear()
        # 遍历每个根节点并添加到树形列表中
        self.add_tree_item(self, self.ConfigContex, root_nodes)

    def save_config(self):
        config_data = self.get_tree_data()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, ":/gallery/images/config.json")

        if os.path.isfile(file_path):
            # 读取现有的配置数据
            with open(file_path, "r", encoding='utf-8') as file:
                try:
                    existing_data = json.load(file)
                except json.decoder.JSONDecodeError:
                    existing_data = {}

            # 更新或添加新配置数据
            existing_data.update(config_data)
            config_data = existing_data

        with open(file_path, "w", encoding='utf-8') as file:
            json.dump(config_data, file, indent=4, ensure_ascii=False)

        print("配置已保存：")
        print(json.dumps(config_data, indent=4, ensure_ascii=False))

    def get_node_data(self, item):
        node_data = {}
        for column in range(self.columnCount()):
            if column % 2 != 0:  # 奇数列
                text = item.text(column)
                widget = self.itemWidget(item, column + 1)
                if widget is not None and isinstance(widget, QtWidgets.QLineEdit):
                    data = widget.text()
                    node_data[text] = data
        return node_data

    def traverse_tree(self, parent_item):
        node_data = self.get_node_data(parent_item)
        child_data = []
        child_count = parent_item.childCount()
        for i in range(child_count):
            child_item = parent_item.child(i)
            child_data.append(self.traverse_tree(child_item))
        return {"node_data": node_data, "child_data": child_data}

    def traverse_mapping(self, mapping):
        mapping_result = {}
        for mapp_key, mapp_value in mapping['mapping'].items():
            edit = mapp_value['widget']
            text = edit.text()
            mapping_result[mapp_value['text']] = text
        if mapping['children']:
            children_result = []
            for child_mapping in mapping['children']:
                child_result = self.traverse_mapping(child_mapping)
                children_result.append(child_result)
            mapping_result['children'] = children_result
        return mapping_result

    def get_tree_data(self):
        result = {}

        for key, value in self.text_input_mapping.items():
            key_value = value['mapping'][0]
            key = key_value['widget'].text()
            mapping_result = self.traverse_mapping(value)
            result[key] = mapping_result

        return result
