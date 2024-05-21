from ast import Return
from ..plugins import config
import os, json
from lxml import etree as ET
from PyQt5.QtWidgets import QMessageBox,QDialogButtonBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt,pyqtSlot,QDateTime,QDate,QTime
import re
from ..common.config import config_645, config_csg13,log_config
from qfluentwidgets import InfoBarIcon
import traceback,sys

class CustomMessageBox(QMessageBox):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        icon = InfoBarIcon.WARNING.icon()
        self.setWindowIcon(icon)
        self.setText("解析失败！")
        self.setInformativeText(message)
        self.finished.connect(self.handle_close)
        # 添加确认按钮
        self.addButton(QMessageBox.Ok)
        self.exec_()

    @pyqtSlot(int)
    def handle_close(self, result):
        if result == QMessageBox.Ok:
            print("User clicked OK")
        else:
            print("User clicked Cancel or closed the dialog")

class FrameFun:
    @staticmethod
    def get_hex_frame(text):
        try:
            hex_str = text.replace(' ', '')
            # 去除换行符和空格
            cleaned_string = hex_str.replace(' ', '').replace('\n', '')
            # 将每两个字符转换为一个十六进制数
            frame = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
            return frame
        except ValueError:
            return None
    @staticmethod
    def add_data(data_list, frame, data, description, location,child_items=None):
        new_data = {"帧域": frame, "数据": data, "说明": description,"位置":location}
        if child_items is not None:
            new_data["子项"] = child_items
        data_list.append(new_data)

    @staticmethod
    def get_bit_array(hexadecimal, bit_array):

        for i in range(7, -1, -1):
            bit = (hexadecimal >> i) & 1
            bit_array.append(bit)
        bit_array = bit_array[::-1]

    @staticmethod
    def decimal_to_bcd_byte(decimal_num):
        # 确保输入数字在0-99的范围内，因为BCD表示只能表示两位数
        if decimal_num < 0 or decimal_num > 99:
            raise ValueError("Decimal number must be between 0 and 99")

        # 将十进制数字的十位和个位分别提取出来，并转换为BCD形式的二进制
        tens_digit = decimal_num // 10
        ones_digit = decimal_num % 10
        bcd_byte = (tens_digit << 4) | ones_digit

        return bcd_byte
    
    @staticmethod
    def is_array_all_ffs(arr):
        return all(element == 0xff for element in arr)
    
    @staticmethod
    def bcd_to_decimal(bcd_array, decimal_places, need_delete,sign):
        # 将BCD数组转换为整数
        int_value = 0
        is_sign = False
        trans_array = bcd_array.copy()
        new_array = trans_array.copy()
        if FrameFun.is_array_all_ffs(bcd_array):
            return "无效数据"

        if need_delete:
            new_array = FrameFun.frame_delete_33H(trans_array)

        if sign:
            if new_array[len(new_array) - 1] &0x80:
                is_sign = True
                new_array[len(new_array) - 1] &=0x7F

        for digit in reversed(new_array):
            int_value = int_value * 100 + (digit >> 4) * 10 + (digit & 0x0F)

        # 格式化整数值为带小数位的字符串
        decimal_string = "{:.{}f}".format(int_value / (10**decimal_places),decimal_places)

        # 在字符串中添加小数点
        decimal_string = decimal_string[:-decimal_places] + decimal_string[-decimal_places:]

        # 在字符串中添加前导零
        if decimal_places != 0:
            decimal_string = decimal_string.zfill(len(bcd_array) * 2 + 1)
        else:
            decimal_string = decimal_string.zfill(len(bcd_array) * 2)
        if is_sign:
            return "-"+decimal_string
        return decimal_string
    @staticmethod
    def bin_to_decimal(bcd_array, decimal_places, need_delete,sign, judge_ff):
        # 将BCD数组转换为整数
        int_value = 0
        is_sign = False
        trans_array = bcd_array.copy()
        new_array = trans_array.copy()

        if judge_ff:
            if FrameFun.is_array_all_ffs(bcd_array):
                return "无效数据"

        if need_delete:
            new_array = FrameFun.frame_delete_33H(trans_array)

        if sign:
            if new_array[len(new_array) - 1] &0x80:
                is_sign = True
                new_array[len(new_array) - 1] &=0x7F

        int_value = FrameFun.bintodecimal(new_array)

        # 格式化整数值为带小数位的字符串
        decimal_string = "{:.{}f}".format(int_value / (10**decimal_places),decimal_places)

        # 在字符串中添加小数点
        decimal_string = decimal_string[:-decimal_places] + decimal_string[-decimal_places:]

        # 在字符串中添加前导零
        if decimal_places != 0:
            decimal_string = decimal_string.zfill(len(bcd_array) * 2 + 1)
        else:
            decimal_string = decimal_string.zfill(len(bcd_array) * 2)
        if is_sign:
            return "-"+decimal_string
        return decimal_string
    
    @staticmethod
    def bintodecimal(bindata):
        # 将数组元素拼接成字符串
        hex_string = ''.join(format(x, '02x') for x in reversed(bindata))

        # 将字符串转换为 10 进制
        decimal_value = int(hex_string, 16)
        return decimal_value
    
    @staticmethod
    def bcdArray_to_decimalArray(data_array):
        dec_array = []
        for bcd_digit in data_array:
            high_nibble = (bcd_digit >> 4) & 0x0F
            low_nibble = bcd_digit & 0x0F
            dec_value = high_nibble * 10 + low_nibble
            dec_array.append(dec_value)
        return dec_array
    @staticmethod
    def find_node_by_data_item(data, data_item):
        if isinstance(data, dict):
            if '数据项' in data and data['数据项'] == data_item:
                return data
            for key, value in data.items():
                result = FrameFun.find_node_by_data_item(value, data_item)
                if result is not None:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = FrameFun.find_node_by_data_item(item, data_item)
                if result is not None:
                    return result
        return None
    @staticmethod
    def caculate_cs(data):
        cs = 0
        for value in data:
            cs += value
        return (cs & 0xff)

    @staticmethod
    def frame_delete_33H(frame):
        new_frame = []
        for i in range(len(frame)):
            value = (frame[i] - 0x33) & 0xff
            new_frame.append(value)
        return new_frame

    @staticmethod
    def frame_add_33H(frame):
        new_frame = []
        for i in range(len(frame)):
            value = (frame[i] + 0x33) & 0xff
            new_frame.append(value)
        return new_frame

    @staticmethod
    def get_data_str_delete_33h_reverse(data):
        data_str = "".join([f"{b:02X}" for b in reversed(FrameFun.frame_delete_33H(data))])
        return data_str

    @staticmethod
    def get_data_item_str_delete_33h_order(data):
        data_str = "".join([f"{b:02X}" for b in FrameFun.frame_delete_33H(data)])
        return data_str

    @staticmethod
    def get_data_str_with_space(data):
        data_str = ' '.join(['{:02X}'.format(byte) for byte in data])
        return data_str
    
    @staticmethod
    def get_data_str_reverser_with_space(data):
        data_str = " ".join([f"{b:02X}" for b in reversed(data)])
        return data_str

    @staticmethod
    def get_data_str_reverser(data):
        data_str = "".join([f"{b:02X}" for b in reversed(data)])
        return data_str

    @staticmethod   
    def get_data_str_order(data):
        data_str = "".join([f"{b:02X}" for b in data])
        return data_str
    @staticmethod
    def get_data_normal(data, need_delete):
        if need_delete:
            return FrameFun.get_data_str_delete_33h_reverse(data)
        else:
            return FrameFun.get_data_str_reverser(data)
        
    @staticmethod
    def get_frame_list_from_str(input_text):
        hex_str = input_text.replace(' ', '').replace('\n', '')
        # 将每两个字符转换为一个十六进制数
        frame = [int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)]
        return frame
    @staticmethod
    def extract_bits(start_bit, end_bit, value):
        # Mask to extract the desired bits
        mask = ((1 << (end_bit - start_bit + 1)) - 1) << start_bit
        # Shift and mask the value to get the extracted bits
        extracted_bits = (value & mask) >> start_bit
        # Convert the extracted bits to binary representation
        binary_value = bin(extracted_bits)[2:].zfill(end_bit - start_bit + 1)
        return binary_value
    @staticmethod
    def is_array_all_zeros(arr):
        return all(element == 0 for element in arr)
    @staticmethod
    def bcd_to_int(bcd_array,need_delete):
        # Convert BCD array to integer
        int_value = 0
        for digit in reversed(bcd_array):
            if need_delete:
                digit = (digit - 0x33)&0xFF
            int_value = int_value * 100 + (digit >> 4) * 10 + (digit & 0x0F)
        return int_value
    @staticmethod
    def bcd2int(bcd):
        int_value = 0
        int_value = int_value * 100 + (bcd >> 4) * 10 + (bcd & 0x0F)
        return int_value
    @staticmethod
    def hex_array_to_int(hex_array,need_delete):
        if need_delete:
            hex_array = FrameFun.frame_delete_33H(hex_array)
        hex_string = ''.join(format(x, '02x') for x in reversed(hex_array))
        return int(hex_string, 16)
    @staticmethod
    def parse_freeze_time(data_array):
        if len(data_array) == 4:
            if data_array[0] == 0x99:
                if data_array[1] == 0x99:
                    if data_array[2] == 0x99:
                        if data_array[3] == 0x99:
                            return "瞬时冻结"
                        else:
                            return f"每时{data_array[3]:02X}分"
                    else:
                        return f"每日{data_array[2]:02X}时{data_array[3]:02X}分"
                else:
                    return f"每月{data_array[1]:02X}日{data_array[2]:02X}时{data_array[3]:02X}分"
            else:
                return "未知冻结类型"
        else:
            return "数据长度不正确"
    @staticmethod
    def is_only_one_bit_set(byte):
        # 判断是否为2的幂，使用位运算
        return byte & (byte - 1) == 0
    @staticmethod   
    def is_all_elements_equal(arr, value):
        return all(element == value for element in arr)
    @staticmethod
    def ascii_to_str(ascii_array):
        ascii_string = ''.join(chr(item) for item in ascii_array)
        return ascii_string
    @staticmethod
    def binary_to_bcd(binary_array):
        bcd_array = []
        for binary_number in binary_array:
            # 将十进制数转换为BCD码
            bcd = ((binary_number // 10) << 4) + (binary_number % 10)
            
            # 将BCD码添加到新数组中
            bcd_array.append(bcd)
        
        return bcd_array
    
    @staticmethod
    def int16_to_bcd(int16):
        bcd_array = []
        bcd_array.append(int16 & 0x00ff)
        bcd_array.append(int16 >> 8)
        return bcd_array
    @staticmethod
    def binary2bcd(binary):
        # 将十进制数转换为BCD码
        bcd = ((binary // 10) << 4) + (binary % 10)
        return bcd
    @staticmethod
    def get_frame_fe_count(frame):
        fe_count = 0
        for i in range(len(frame)):
            if frame[i] == 0xFE:
                fe_count += 1
            if frame[i+1] != 0xFE or frame[i] != 0xFE:
                break
        return fe_count
    @staticmethod
    def get_sublength_caculate_base(splitlength,target_subitem_name):
        #for subitem, value in splitlength.items():
        #    if value[0] == target_subitem_name:
        #        break
        matching_subitems = [(idx, value) for idx, (subitem, value) in enumerate(splitlength.items()) if value[0] == target_subitem_name]

        # 如果有多个匹配项，matching_subitems 将包含它们
        for idx, subitem in matching_subitems:
            subitem_name, subitem_content, subitem_value, subitem_indices = subitem
            return subitem_value, idx, subitem
        
    @staticmethod
    def get_subitem_length(data_subitem_elem, splitlength, key, data_segment):
        """获取子项的长度"""
        relues = data_subitem_elem.find('lengthrule')
        operator_mapping = {
        '+': '+',
        '-': '-',
        '*': '*',
        '/': '/'
        }
        pattern = r'^RANGE\(([^)]+)\)$'
        
        # 获取长度规则
        if relues is not None:
            relues = relues.text
            # 使用 re.match 函数进行匹配
            match = re.match(pattern, relues)
            # 如果匹配成功，返回 True，否则返回 False
            if bool(match):
                # 获取匹配到的字符串
                match_string = match.group(1)
                vaule, index, subitem = FrameFun.get_sublength_caculate_base(splitlength, match_string)
                # 使用正则表达式提取前面的数字
                match = re.match(r"(\d+)", vaule)
                if index > 0:
                    before_item = splitlength[index-1]
                    pos = before_item[3][0]
                else:
                    pos = 0

                cur_pos = subitem[3][0]
                target_data = subitem[1][0]
                if cur_pos > pos:
                    sub_length = cur_pos - pos
                sub_length += 1
                for i, data in enumerate(data_segment[sub_length:]):
                    if data == target_data:
                        return i,i
            # 使用正则表达式进行拆分
            components = re.split(r'\s*([*])\s*', relues)

            # Filter out any empty strings
            components = [c for c in components if c.strip()]
            number_part = components[0]
            operator_part = components[1]
            text_part = components[2]
            operator = operator_mapping.get(operator_part)
            if text_part.isdigit():
                vaule = int(text_part)
            else:
                vaule, index, subitem = FrameFun.get_sublength_caculate_base(splitlength, text_part)
                # 使用正则表达式提取前面的数字
                match = re.match(r"(\d+)", vaule)
                if match:
                    extracted_number = int(match.group(1))
                    print(f"提取到的数字为: {extracted_number}")
                else:
                    extracted_number = int(vaule, 10)
                    print("未找到数字")
                
                vaule = extracted_number
            try:
                decimal_number = int(number_part, 10)
            except ValueError:
                print("无法转换为整数:", number_part)

            if operator == '+':
                sub_length = decimal_number + vaule
            elif operator == '-':
                sub_length = decimal_number - vaule
            elif operator == '*':
                sub_length = decimal_number * vaule
            elif operator == '/':
                sub_length = decimal_number / vaule
            else:
                sub_length = 0
        else:
            from .protocol import PraseFrameData
            prase_data = PraseFrameData()
            sub_type = data_subitem_elem.find('type').text
            template = FrameFun.get_template_element(sub_type, FrameFun.globalprotocol, FrameFun.globregion)
            sub_length = prase_data.caculate_item_length(template, data_segment)
            decimal_number = sub_length
        return decimal_number, sub_length
    @staticmethod
    def calculate_measurement_points(DA):
        da1 = DA[0]
        da2 = DA[1]
        def find_set_bits(value):
            set_bits = []
            for i in range(8):
                if (value >> i) & 1:
                    set_bits.append(i)
            return set_bits
        
        if da1 == 0xFF and da2 == 0xFF:
            total_measurement_points = 1
            measurement_points_array = [0xFFFF]
        elif da1 == 0x00 and da2 == 0x00:
            total_measurement_points = 1
            measurement_points_array = [0]
        else:
            set_bits_da1 = find_set_bits(da1)
            info_point_group = da2
            info_point_start = (info_point_group - 1) * 8
            
            measurement_points = [info_point_start + bit + 1 for bit in set_bits_da1]
            total_measurement_points = len(measurement_points)
            measurement_points_array = [mp for mp in measurement_points]
        
        return total_measurement_points, measurement_points_array
    @staticmethod
    def prase_DA_data(DA):
        point_str = ""
        total_measurement_points, measurement_points_array = FrameFun.calculate_measurement_points(DA)
        if measurement_points_array[0] == 0 and total_measurement_points == 1:
            point_str = "Pn=测量点：0(终端)"
        elif measurement_points_array[0] == 0xffff and total_measurement_points == 1:
            point_str = "Pn=测量点：FFFF(除了终端信息点以外的所有测量点)"
        else:
            formatted_string = ', '.join(map(str, measurement_points_array))
            point_str = "Pn=第" + formatted_string + "测量点"
        return point_str
    
    @staticmethod
    def caculate_item_box_length(item_ele):
        pos = 0
        i = 0
        if item_ele.findall('item') is not None:
            all_item = item_ele.findall('item')
        else:
            all_item = None
        for item_elem in all_item:
            item_id = item_elem.text
            item = FrameFun.get_config_xml(item_id, FrameFun.globalprotocol, FrameFun.globregion)
            if item is not None:
                item_length_ele = item.find('length')
                if item_length_ele is not None:
                    item_length = int(item_length_ele.text)
                else:
                    item_length = 0
                pos += item_length
                i += 1
        return pos
    @staticmethod
    def is_vaild_data_item(data_item, target_protocol, tagrget_region):
        attri_protocol = data_item.get('protocol')
        if attri_protocol is not None:
            protocols = attri_protocol.split(',')
            # 判断目标protocol是否在列表中
            if target_protocol in protocols:
                attri_region = data_item.get('region')
                if attri_region is not None:
                    regions = attri_region.split(',')
                    if tagrget_region in regions:
                        return True
        return False

    @staticmethod
    def find_target_dataitem(root, target_id, target_protocol, region):
        target_node = root.findall(".//*[@id='{}']".format(target_id,target_protocol,region))

        if target_node is None:
            print("No node found with id {} protocol {} and region {}".format(target_id))
            return None
        #当前标签无法找到
        for node in target_node:
            if FrameFun.is_vaild_data_item(node, target_protocol, region):
                return node
            else:
                parent = node.getparent()
                while parent is not None:
                    if FrameFun.is_vaild_data_item(parent, target_protocol, region):
                        return node
                    parent = parent.getparent()
        print("No parent found with protocol {} and region {}".format(target_protocol,region))
        return None

    globregion = None
    globalprotocol = None
    @staticmethod
    def get_config_xml(data_item_id:str, protocol:str, region:str, dir=None):
        find_protocol = protocol.upper()
        # data_item_id = data_item_id.upper()
        if "DLT/645" in find_protocol:
            if find_protocol != "DLT/645-2007":
                find_protocol = "DLT/645-2007"
            itemconfig = config_645.get_item(data_item_id, find_protocol, region)
            if itemconfig is not None:
                return itemconfig
            else:
                if data_item_id.isupper():
                    return config_645.get_item(data_item_id.lower(), find_protocol, region, dir)
                if itemconfig is not None:
                    return config_645.get_item(data_item_id.upper(), find_protocol, region, dir)
        elif "CSG13" in find_protocol:
            itemconfig = config_csg13.get_item(data_item_id, find_protocol, region, dir)
            if itemconfig is not None:
                return itemconfig
            else:
                if data_item_id.isupper():
                    return config_csg13.get_item(data_item_id.lower(), find_protocol, region, dir)
                else:
                    return config_csg13.get_item(data_item_id.upper(), find_protocol, region, dir)
        else:
            return None
    @staticmethod
    def get_template_element(template:str, protocol:str, region:str):
        find_protocol = protocol.upper()
        template = template.upper()
        if "DLT/645" in protocol:
            itemconfig = config_645.get_item(template, find_protocol, region)
            if itemconfig is not None:
                return itemconfig
            else:
                if template.isupper():
                    return config_645.get_item(template.lower(), find_protocol, region)
                else:
                    return config_645.get_item(template.upper(), find_protocol, region)
        elif "CSG13" in find_protocol:
            itemconfig = config_csg13.get_item(template, find_protocol, region)
            if itemconfig is not None:
                return itemconfig
            else:
                if template.isupper():
                    return config_csg13.get_item(template.lower(), find_protocol, region)
                else:
                    return config_csg13.get_item(template.upper(), find_protocol, region)
        else:
            return None
            


    @staticmethod
    def parse_time_data(data_array, format_str, need_delete):
        # 定义格式字符串中的对应关系
        correct = "CCYYMMDDWWhhmmss"
        format_mapping = {
            'CC': '{:02X}',
            'YY': '{:02X}年',
            'MM': '{:02X}月',
            'DD': '{:02X}日',
            'hh': '{:02X}时',
            'mm': '{:02X}分',
            'ss': '{:02X}秒',
            'WW': '星期:',
        }
        new_array = data_array.copy()
        # 初始化格式化后的结果
        formatted_data = ""
        if need_delete:
            new_array = FrameFun.frame_delete_33H(data_array)

        # 将数组元素根据格式字符串逐个格式化
        pos = 0
        weekday_mapping = {0: '天', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六'}
        while pos < len(correct):
            corr = correct[pos:pos+2]
            index = 0
            flag = False
            while index < len(format_str):
                fmt = format_str[index:index+2]
                if fmt == corr:
                    flag = True
                    break
                index += 2
            if flag:
                if fmt in format_mapping:
                    index = int(index / 2)                    
                    formatted_data += format_mapping[fmt].format(new_array[index])
                    if fmt == 'WW':
                        index = int(index / 2)
                        # 使用星期映射字典将数字转换为星期字符串
                        weekday = new_array[index]
                        formatted_data += weekday_mapping.get(weekday, '未知')
            pos += 2

        return formatted_data
    @staticmethod
    def prase_ip_str(ipdata):
        if len(ipdata) < 4:
            return ""
        return f"{ipdata[3]}.{ipdata[2]}.{ipdata[1]}.{ipdata[0]}"
    @staticmethod
    def prase_port(port_data):
        if len(port_data) < 2:
            return ""
        return FrameFun.bintodecimal(port_data)
    @staticmethod
    def str_reverse_with_space(str:str):
        # 将字符串按每两个字符分割成一个列表，并反转
        split_str = [str[i:i+2] for i in range(0, len(str), 2)][::-1]

        # 将列表中的每个元素转换为大写形式
        upper_str = [x.upper() for x in split_str]

        # 将列表中的元素连接起来，每个元素之间用空格分隔
        output_str = ' '.join(upper_str)
        return output_str   
    
    @staticmethod   
    def str_order_with_space(str:str):
        # 将字符串按每两个字符分割成一个列表，并反转
        split_str = [str[i:i+2] for i in range(0, len(str), 2)]

        # 将列表中的每个元素转换为大写形式
        upper_str = [x.upper() for x in split_str]

        # 将列表中的元素连接起来，每个元素之间用空格分隔
        output_str = ' '.join(upper_str)
        return output_str   
    @staticmethod
    def to_hex_string_reverse(value):
        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            return hex(value)[2:].upper()
        elif isinstance(value, list):
            return FrameFun.get_data_str_reverser(value)
        else:
            raise ValueError("Unsupported data type. Expected int or list of ints.")
    @staticmethod    
    def to_hex_string_reverse_with_space(value):
        if isinstance(value, str):
            return FrameFun.str_reverse_with_space(value)
        elif isinstance(value, int):
            return hex(value)[2:].upper()
        elif isinstance(value, list):
            return FrameFun.get_data_str_reverser_with_space(value)
        else:
            raise ValueError("Unsupported data type. Expected int or list of ints.")
        
    @staticmethod
    def to_hex_string_delete_33h_reverse(value):
        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            hex_str = hex(value)[2:].upper()
            return hex_str.zfill(2)  # 在前面补零，直到达到指定长度
        elif isinstance(value, list):
            return FrameFun.get_data_str_delete_33h_reverse(value)
        else:
            raise ValueError("Unsupported data type. Expected int or list of ints.")
    @staticmethod
    def to_hex_string_with_space(value):
        if isinstance(value, str):
            return value
        elif isinstance(value, int):
            hex_str = hex(value)[2:].upper()
            return hex_str.zfill(2)  # 在前面补零，直到达到指定长度
        elif isinstance(value, list):
            return FrameFun.get_data_str_with_space(value)
        else:
            raise ValueError("Unsupported data type. Expected int or list of ints.")
    @staticmethod
    def is_numeric_and_4_bytes(variable):
        # 判断变量是否为数字类型
        if not isinstance(variable, (int, float)):
            return False

        # 将数字类型转换为字符串
        str_representation = str(variable)

        # 检查字符串的字节长度是否为4
        if len(str_representation.encode()) != 4:
            return False

        return True
    @staticmethod
    def starts_with_bit(input_var):
        # 判断变量是否为字符串
        if not isinstance(input_var, str):
            return False

        # 将前三个字符转换为小写，然后检查是否为 "bit"
        if input_var[:3].lower() == "bit":
            return True

        return False
    @staticmethod
    def prase_data_with_config(alalysic_result, need_delete,data_list=None,indent=0):
        if data_list is None:
            data_list = []

        for item_id, item_data in alalysic_result.items():
            if isinstance(item_data, list):
                name = item_data[0]
                origial_data = FrameFun.to_hex_string_with_space(item_data[1])
                if need_delete:
                    data_str = FrameFun.to_hex_string_delete_33h_reverse(item_data[1])
                else:
                    data_str = FrameFun.to_hex_string_reverse(item_data[1])
                sub_data_items = item_data[2]
                data_index = item_data[3]
                dispriction = data_str if isinstance(sub_data_items, dict) else sub_data_items
                result_dispriction = ""
                if FrameFun.is_numeric_and_4_bytes(item_id):
                    result_dispriction = f"{item_id}：[{name}]"
                elif FrameFun.starts_with_bit(item_id):
                    result_dispriction = f"[{name}]"
                else:
                    result_dispriction = f"[{name}]"
                    item_id = name
                if dispriction != '':
                    result_dispriction = result_dispriction + f"：{dispriction}"

                if isinstance(sub_data_items, dict):
                    sub_result = []
                    FrameFun.prase_data_with_config(sub_data_items, need_delete,sub_result, indent + 1)
                    FrameFun.add_data(data_list, f"{item_id}", origial_data, result_dispriction, data_index,sub_result)
                else:
                    if isinstance(sub_data_items, list):
                        FrameFun.add_data(data_list, f"{item_id}", origial_data, f"{item_id}内容", data_index,sub_data_items)
                    else:
                        FrameFun.add_data(data_list, f"{item_id}", origial_data, result_dispriction, data_index)

            elif isinstance(item_data, dict):
                sub_result = []
                FrameFun.prase_data_with_config(item_data, need_delete,sub_result, indent + 1)
                data_list.extend(sub_result)
            #else:
            #    name = item_data[0]
            #    origial_data = to_hex_string_with_space(item_data[1])
            #    if need_delete:
            #        data_str = to_hex_string_delete_33h_reverse(item_data[1])
            #    else:
            #        data_str = to_hex_string_reverse(item_data[1])
            #    sub_data_items = item_data[2]
            #    data_index = item_data[3]
            #    print(f"{'    ' * indent}{item_id}: {name}, Bits: [{data_str}], {sub_data_items}, {data_index}")
            #    dispriction = data_str if isinstance(sub_data_items, dict) else sub_data_items
            #    result_dispriction = ""
            #    if is_numeric_and_4_bytes(item_id):
            #        result_dispriction = f"{item_id}：[{name}]"
            #    elif starts_with_bit(item_id):
            #        result_dispriction = f"[{name}]"
            #    else:
            #        result_dispriction = f"[{name}]"
            #        item_id = name
            #    if dispriction != '':
            #        result_dispriction = result_dispriction + f"：{dispriction}"

            #    if isinstance(sub_data_items, dict):
            #        sub_result = []
            #        prase_data_with_config(sub_data_items, need_delete,sub_result, indent + 1)
            #        add_data(data_list, f"{item_id}", origial_data, result_dispriction, data_index,sub_result)
            #    else:
            #        add_data(data_list, f"{item_id}", origial_data, result_dispriction, data_index)

        return data_list
    @staticmethod
    def warn_infto_message(info):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir,":/gallery/images/warn.ico")
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(icon_path))
        msgBox.setText("解析失败！")
        msgBox.setInformativeText(info)
        msgBox.setWindowTitle("告警")
        # 添加确认框按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel) 

        # 从按钮框中取出按钮添加到消息框
        ok_button = buttons.button(QDialogButtonBox.Ok)  
        cancel_button = buttons.button(QDialogButtonBox.Cancel)

        msgBox.addButton(ok_button, QMessageBox.ActionRole)
        #msgBox.addButton(cancel_button, QMessageBox.ActionRole)
        ok_button.clicked.connect(QDialogButtonBox.accepted)
        # 显示消息框并获取选择结果  
        ret = msgBox.exec_() 
        return ret
    @staticmethod
    def parse_meterpoint_input(input_text):
        # 使用正则表达式从输入文本中提取整数和范围
        integers = set()
        ranges = set()
        pattern = r'(\d+)-(\d+)|(\d+)'
        matches = re.finditer(pattern, input_text)
        sorted_result = []
        if input_text.upper() == "FFFF":
            sorted_result.append(0xFFFF)
        else:
            parts = input_text.split(',')
            for part in parts:
                if part.upper() == "FFFF":
                    integers.add(0xFFFF)
                    continue
                matches = re.finditer(pattern, part)
                for match in matches:
                    start, end, single = match.groups()
                    if start and end:
                        # 处理范围表示，将范围内的整数添加到集合中
                        start, end = int(start), int(end)
                        ranges.update(range(start, end + 1))
                    elif single:
                        # 处理单个整数，将其添加到集合中
                        single = int(single)
                        integers.add(single)
                
            # 合并整数和范围
            integers.update(ranges)
        
            # 将结果按升序排序并返回
            sorted_result = sorted(integers)
        return sorted_result
    @staticmethod
    def prase_item_by_input_text(input_text):
        # Split the input by commas or spaces, and remove any leading/trailing whitespace
        hex_values = [x.strip() for x in input_text.replace(',', ' ').split()]

        # Convert the hexadecimal strings to integers
        item_array = [int(x, 16) for x in hex_values]
        return item_array
    @staticmethod
    def item_to_di(item, frame):
        for _ in range(4):
            byte = item & 0xFF  # 获取最低8位的数据
            frame.append(byte)  # 将字节添加到字节数组
            item >>= 8  # 将整数右移8位以处理下一个字节
        return 4
    @staticmethod
    def prase_item_input(input_text, frame):
        # Split the input by commas or spaces, and remove any leading/trailing whitespace
        hex_values = [x.strip() for x in input_text.replace(',', ' ').split()]

        # Convert the hexadecimal strings to integers
        item_array = [int(x, 16) for x in hex_values]
        frame.append(len(item_array))
        for item in item_array:
            FrameFun.item_to_di(item, frame)
    @staticmethod
    def prase_text_to_frame(text:str, frame:list):
        cleaned_string = text.replace(' ', '').replace('\n', '')
                # 将每两个字符转换为一个十六进制数
        hex_array  = [int(cleaned_string[i:i + 2], 16) for i in range(0, len(cleaned_string), 2)]
        frame.extend(hex_array)
        return int(len(cleaned_string) / 2)
    @staticmethod
    def add_time_interval(current_datetime:QDateTime, index, interval):
        interval_map = {
            0: "1分钟",
            1: "5分钟",
            2: "15分钟",
            3: "30分钟",
            4: "60分钟",
            5: "1日",
            6: "1月",
        }

        interval_kind = interval_map.get(index, "1分钟")
        interval_value = int(interval_kind.split("分钟")[0])

        if "分钟" in interval_kind:
            new_datetime = current_datetime.addSecs(interval_value * 60 * interval)
        elif "日" in interval_kind:
            new_datetime = current_datetime.addDays(interval_value * interval)
        elif "月" in interval_kind:
            new_datetime = current_datetime.addMonths(interval_value * interval)
        else:
            # 默认为分钟
            new_datetime = current_datetime.addSecs(interval_value * 60 * interval)

        return new_datetime
    @staticmethod
    def get_time_bcd_array(date:QDate, time:QTime):
        year = date.year()
        bcd_array = [FrameFun.binary2bcd(year//100),FrameFun.binary2bcd(year % 100),FrameFun.binary2bcd(date.month()),FrameFun.binary2bcd(date.day()),FrameFun.binary2bcd(time.hour()),
                    FrameFun.binary2bcd(time.minute()),FrameFun.binary2bcd(time.second())]
        return bcd_array
    
    @staticmethod
    def cosem_bin2_int32u(bin):
        val = 0
        for byte in bin:
            val <<= 8
            val += byte
        return val