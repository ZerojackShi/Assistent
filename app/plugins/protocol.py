from ..plugins import frame_fun
import re
def caculate_unknown_length(data_subitem_elem, data_segment, length_maap):
    relues = data_subitem_elem.find('lengthrule').text
    operator_mapping = {
    '+': '+',
    '-': '-',
    '*': '*',
    '/': '/'
    }
    sub_length = 0;
    if relues is not None:
        # 使用正则表达式进行拆分
        components = re.split(r'\s*([*])\s*', relues)

        # Filter out any empty strings
        components = [c for c in components if c.strip()]
        number_part = components[0]
        operator_part = components[1]
        text_part = components[2]
        operator = operator_mapping.get(operator_part)
        vaule = length_maap[text_part]
        vaule_data = data_segment[vaule[0] - vaule[1] : vaule[0]]
        value_element = vaule[2]
        result = parse_data_item(value_element, vaule_data, 0, False)
        sub_value = frame_fun.get_sublength_caculate_base(result,text_part)
        # 使用正则表达式提取前面的数字
        match = re.match(r"(\d+)", sub_value)

        if match:
            extracted_number = int(match.group(1))
            print(f"提取到的数字为: {extracted_number}")
        else:
            extracted_number = int(sub_value, 10)
            print("未找到数字")
        try:
            decimal_number = int(number_part, 10)
            sub_value = extracted_number
        except ValueError:
            print("无法转换为整数:", number_part)
        if operator == '+':
            sub_length = decimal_number + sub_value
        elif operator == '-':
            sub_length = decimal_number - sub_value
        elif operator == '*':
            sub_length = decimal_number * sub_value
        elif operator == '/':
            sub_length = decimal_number / sub_value
        else:
            sub_length = 0
    return sub_length

def caculate_item_length(sub_element, data_segment, all_length_items=None):
    def execute_calculation(element, data, items=None):
        length = 0
        length_maap = {}
        if items is None:
            all_items = element.findall('splitByLength')
        else:
            all_items = items
        template_element = element.find('type')

        if len(all_items) == 0:
            if template_element is not None:
                data_type = template_element.text.upper()
                if data_type not in ("BCD", "BIN", "ASCII"):
                    template = frame_fun.get_template_element(data_type, frame_fun.globalprotocol, frame_fun.globregion)
                    if template is not None:
                        # 递归调用子函数
                        template_items = template.findall('splitByLength')
                        return execute_calculation(template, data, template_items)
        else:
            for data_subitem_elem in all_items:
                subitem_name = data_subitem_elem.find('name').text
                sub_length_content = data_subitem_elem.find('length').text
                if sub_length_content == "unknown":
                    subitem_length = caculate_unknown_length(data_subitem_elem, data, length_maap)
                else:
                    subitem_length = int(sub_length_content)
                length += subitem_length
                length_maap[subitem_name] = [length, subitem_length, data_subitem_elem]
        return length

    # 初始调用
    length = execute_calculation(sub_element, data_segment, all_length_items)

    return length



def parse_bitwise_data(splitbit_elem, data_segment,index,need_delete):
    # 解析使用splitbit拆分的数据段
    result = {}

    for bit_elem in splitbit_elem.findall('.//bit'):
        bit_id_attr = bit_elem.get('id')
        bit_name_elem = bit_elem.find('name')

        if '-' in bit_id_attr:
            # If the bit ID is a range (e.g., "6-15")
            start_bit, end_bit = map(int, bit_id_attr.split('-'))
        else:
            start_bit = int(bit_id_attr)
            end_bit = start_bit

        bit_value = frame_fun.extract_bits(start_bit, end_bit,frame_fun.hex_array_to_int(data_segment,need_delete))

        bit_value_elem = bit_elem.find('value[@key="' + bit_value + '"]')
        if bit_name_elem is not None:
            # If <name> tag is present, use its text as bit_name
            bit_name = bit_name_elem.text
        else:
            # If <name> tag is not present, use an empty string
            bit_name = ""

        if bit_value_elem is not None:
            bit_value_name = bit_value_elem.text
        else:
            # If <value> tag is not present, use an empty string
            if bit_elem.find('value[@key="other"]') is not None:
                bit_value_name = bit_elem.find('value[@key="other"]').text
            else:
                bit_value_name = ""
        bit_id_attr = "bit"+bit_id_attr
        result[bit_id_attr] = [bit_name, bit_value, bit_value_name,[index, index + len(data_segment)]]
    return result
def prase_type_item(data_item_elem, data_segment, index, need_delete, singal_length):
    from ..plugins.frame_csg import FrameCsg
    sub_type = data_item_elem.find('type').text.upper()
    sub_length = len(data_segment)
    result = {}
    pos = 0
    i = 0
    ret = False

    if need_delete:
        new_data = frame_fun.frame_delete_33H(data_segment)
    else:
        new_data = data_segment
    ret = prase_simple_type_data(data_item_elem, data_segment,index, need_delete)
    if ret is not False:
        subitem_value = ret
    elif sub_type in ("PN"):
        if sub_length % singal_length == 0:
            while pos < sub_length:
                da = new_data[pos:pos + singal_length]
                subitem_name = f"第{i + 1}组信息点"
                subitem_value = frame_fun.prase_DA_data(da)
                subitem_value = [subitem_name, da, subitem_value, [index + pos,index + pos +singal_length]]
                result[i] = subitem_value
                i += 1
                pos += singal_length
        else:
            subitem_value = ["PN", data_segment, frame_fun.get_data_str_reverser(new_data), [index + pos,index + pos +sub_length]]
            result[i] = subitem_value
    elif sub_type in ("ITEM"):
        if sub_length % singal_length == 0:
            while pos < sub_length:
                item = new_data[pos:pos + singal_length]
                subitem_name = f"第{i + 1}组数据标识"
                data_item = frame_fun.get_data_str_reverser(item)
                subitem_value_element = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
                if subitem_value_element:
                    subitem_element_name = subitem_value_element.find('name').text
                    subitem_value = f"[{data_item}]-{subitem_element_name}"
                else:
                     subitem_value = f"[{data_item}]"
                subitem_value = [subitem_name, item, subitem_value, [index + pos,index + pos +singal_length]]
                result[i] = subitem_value
                i += 1
                pos += singal_length
        else:
            subitem_value = ["PN", data_segment, frame_fun.get_data_str_reverser(new_data), [index + pos,index + pos +sub_length]]
            result[i] = subitem_value
    elif sub_type in ("FRAME645"):
        subitem_value = []
        Analysis_645_fram_by_afn(data_segment, subitem_value,index)
        sub_length = len(data_segment)
        return subitem_value
    elif sub_type in ("CSG13"):
        subitem_value = []
        csg = FrameCsg()
        csg.Analysis_csg_frame_by_afn(data_segment, subitem_value,index)
        sub_length = len(data_segment)
        return subitem_value
        #result[i] = ["645报文",data_segment,frame_fun.get_data_str_reverser(data_segment),subitem_value,[index + pos,index + pos +sub_length]]
    elif sub_type in ("IPWITHPORT"):
        port = data_segment[0:2]
        port_str = frame_fun.prase_port(port)
        ip_str = frame_fun.prase_ip_str(data_segment[2:6])
        subitem_value = ["IP地址", data_segment[2:6], ip_str, [index + 2,index + 8]]
        result[i] = subitem_value
        i+=1
        subitem_value = ["端口号", port, port_str, [index,index + 2]]
        result[i] = subitem_value
        i+=1
    else:
        template = frame_fun.get_template_element(sub_type,frame_fun.globalprotocol, frame_fun.globregion)
        if template:
            if sub_length % singal_length == 0:
                while pos < sub_length:
                    splitname_elem = template.find('name')
                    if splitname_elem is not None:
                        name = splitname_elem.text
                        subitem_name = f"第{i + 1}组{name}"
                    else:
                        splitname_elem = data_item_elem.find('name')
                        subitem_name = f"第{i + 1}组{splitname_elem.text}" if splitname_elem is not None else f"第{i + 1}组内容"
                    data_seg = new_data[pos:pos + singal_length]
                    subitem_value = parse_splitByLength_data(template,data_seg,index + pos,need_delete)
                    subitem_value = [subitem_name, data_seg, subitem_value, [index + pos,index + pos +singal_length]]
                    result[i] = subitem_value
                    i += 1
                    pos += singal_length

        else:
            result = prase_singal_item(data_item_elem,data_segment,index,need_delete)
    return result
def parse_item(data_item_elem, data_segment,index, need_delete):
    # 解析splitByLength数据段
    splitlength = {}
    sub_data_segment = data_segment

    if data_item_elem.findall('item') is not None:
        all_item = data_item_elem.findall('item')
    else:
        all_item = None
    
    pos = 0
    i = 0
    for item_elem in all_item:
        item_id = item_elem.text
        item = frame_fun.get_config_xml(item_id, frame_fun.globalprotocol, frame_fun.globregion)
        if item is not None:
            item_length_ele = item.find('length')
            item_name_ele = item.find('name')
            if item_name_ele is not None:
                name = item_name_ele.text
                reultname = f"{item_id}:{name}"
            else:
                reultname = f"{item_id}"
            if item_length_ele is not None:
                item_length = int(item_length_ele.text)
            item_data = sub_data_segment[:item_length]
            result = parse_data_item(item, item_data, index + pos, need_delete)

        subitem_value = [reultname, item_data, result, [index + pos,index + pos +item_length]]
        splitlength[i] = subitem_value
        pos += item_length
        i += 1
        sub_data_segment = sub_data_segment[item_length:]
    return splitlength
def parse_splitByLength_data(data_item_elem, data_segment,index, need_delete):
    # 解析splitByLength数据段
    result = {}
    i = 0
    pos = 0
    splitbit_elem = data_item_elem.find('splitbit')
    splitname_elem = data_item_elem.find('name')
    if splitbit_elem is not None:
        parsed_bitwise_data = parse_bitwise_data(splitbit_elem, data_segment,index, need_delete)
        result_data = {splitbit_name, data_segment, parsed_bitwise_data, [index, index + len(data_segment)]}
        result.append(result_data)
    if splitname_elem is not None:
        splitbit_name = splitname_elem.text

    splitlength = {}
    sub_data_segment = data_segment

    if data_item_elem.findall('splitByLength') is not None:
        all_split_length_item = data_item_elem.findall('splitByLength')
    else:
        all_split_length_item = None
    
    pos = 0
    singal_length=None
    for data_subitem_elem in all_split_length_item:
        subitem_name_elem = data_subitem_elem.find('name')
        if subitem_name_elem is not None:
            subitem_name = data_subitem_elem.find('name').text
        else:
            subitem_name = ""
        sub_length_ele = data_subitem_elem.find('length')
        if sub_length_ele is not None:
            sub_length_content = sub_length_ele.text
            if sub_length_content in ("unknown"):
                singal_length, subitem_length = frame_fun.get_subitem_length(data_subitem_elem, splitlength, i - 1)
            else:
                subitem_length = int(sub_length_content)
                singal_length = subitem_length
        else:
            sub_item_ele = data_subitem_elem.find('item')
            if sub_item_ele is not None:
                subitem_length = frame_fun.caculate_item_box_length(data_subitem_elem)

        subitem_content = sub_data_segment[:subitem_length]
        if subitem_length > len(subitem_content):
            break
        if data_subitem_elem.find('unit') is not None and data_subitem_elem.find('value') is not None:
            subitem_value = prase_value_item(data_subitem_elem, subitem_content, index + pos,  need_delete)
            subitem_value = f"{subitem_value}"
        elif data_subitem_elem.find('unit') is not None:
            # 解析有单位的数据
            subitem_unit = data_subitem_elem.find('unit').text
            subitem_decimal = data_subitem_elem.find('decimal')
            subitem_type = data_subitem_elem.find('type')
            data_type = ""
            if subitem_type is not None:
                data_type = subitem_type.text
            if subitem_decimal is not None:
                decimal = int(data_subitem_elem.find('decimal').text)
            else:
                decimal = 0
            is_sign = data_subitem_elem.find('sign')
            sign = False
            if is_sign is not None:
                sign = True if is_sign.text=="yes" else False
            if data_type in ("BCD","Bcd","bcd"):
                subitem_value = frame_fun.bcd_to_decimal(subitem_content,decimal,need_delete,sign)
            elif data_type in ("BIN","Bin","bin"):
                subitem_value = frame_fun.bin_to_decimal(subitem_content,decimal,need_delete,sign)
            else:
                subitem_value = frame_fun.bcd_to_decimal(subitem_content,decimal,need_delete,sign)
            if subitem_value != "无效数据":
                subitem_value = f"{subitem_value}" + subitem_unit
        elif data_subitem_elem.find('time') is not None:
            # 解析时间数据
            subitem_time_format = data_subitem_elem.find('time').text
            subitem_type = data_subitem_elem.find('type')
            data_type = ""
            if subitem_type is not None:
                data_type = subitem_type.text
            time_data = subitem_content[:6][::-1]
            if data_type in ("BIN","Bin","bin"):
                time_data = frame_fun.binary_to_bcd(subitem_content[:6][::-1])
            subitem_value = frame_fun.parse_time_data(time_data,subitem_time_format,need_delete)
        elif data_subitem_elem.find('splitbit') is not None:
            splitbit_elem = data_subitem_elem.find('splitbit')
            subitem_value = parse_bitwise_data(splitbit_elem, subitem_content,index + pos,need_delete)
            # subitem_value = [subitem_name, subitem_content, subitem_value]
        elif data_subitem_elem.find('splitByLength') is not None:
            subitem_value = parse_splitByLength_data(data_subitem_elem, subitem_content,index + pos, need_delete)
        elif data_subitem_elem.find('value') is not None:
            subitem_value = prase_value_item(data_subitem_elem, subitem_content, index + pos,  need_delete)
        elif data_subitem_elem.find('type') is not None:
            subitem_value = prase_type_item(data_subitem_elem, subitem_content, index + pos,  need_delete, singal_length)
        elif data_subitem_elem.find('item') is not None:
            subitem_value = parse_item(data_subitem_elem, subitem_content, index + pos,  need_delete)
        else:
            subitem_value = prase_singal_item(data_subitem_elem,subitem_content,index + pos,need_delete)
        subitem_value = [subitem_name, subitem_content, subitem_value, [index + pos,index + pos +subitem_length]]
        splitlength[i] = subitem_value
        pos += subitem_length
        i += 1
        sub_data_segment = sub_data_segment[subitem_length:]
    # result[splitbit_name] = [splitbit_name, data_segment, splitlength]
    return splitlength

def prase_simple_type_data(data_item_elem, data_segment,index, need_delete):
    subitem_decimal = data_item_elem.find('decimal')
    is_sign = data_item_elem.find('sign')
    decimal = 0
    if subitem_decimal is not None:
        decimal = int(subitem_decimal.text)
    sign = False
    if is_sign is not None:
        sign = True if is_sign.text=="yes" else False
    subitem_type = data_item_elem.find('type')
    data_type = ""
    if subitem_type is not None:
        data_type = subitem_type.text
    if data_type in ("BCD","Bcd","bcd"):
         subitem_value = frame_fun.bcd_to_decimal(data_segment,decimal,need_delete,sign)
    elif data_type in ("BIN","Bin","bin"):
         subitem_value = frame_fun.bin_to_decimal(data_segment,decimal,need_delete,sign)
    elif data_type in ("ASCII","ascii"):
         subitem_value = frame_fun.ascii_to_str(data_segment)
    elif data_type == "PORT":
        subitem_value = frame_fun.prase_port(data_segment)
    elif data_type == "IP":
        subitem_value = frame_fun.prase_ip_str(data_segment)
    else:
        subitem_value = False
    return subitem_value

def prase_singal_item(data_item_elem, data_segment,index, need_delete):
    subitem_name = data_item_elem.find('name').text
    splitbit_elem = data_item_elem.find('splitbit')
    if data_item_elem.find('unit') is not None:
        # 解析有单位的数据
        subitem_unit = data_item_elem.find('unit').text
        subitem_value = prase_simple_type_data(data_item_elem, data_segment,index, need_delete)
        if subitem_value is not False:
            subitem_value = f"{subitem_value}" + subitem_unit
        else:
            subitem_value = "无效数据"
            
    elif data_item_elem.find('time') is not None:
        # 解析时间数据
        subitem_time_format = data_item_elem.find('time').text
        subitem_type = data_item_elem.find('type')
        data_type = ""
        if subitem_type is not None:
            data_type = subitem_type.text
        time_data = data_segment[:6][::-1]
        if data_type in ("BIN","Bin","bin"):
            time_data = frame_fun.binary_to_bcd(data_segment[:6][::-1])
        subitem_value = frame_fun.parse_time_data(time_data, subitem_time_format,need_delete)

    elif splitbit_elem is not None:
        subitem_value = parse_bitwise_data(splitbit_elem, data_segment,index, need_delete)
    else:
        # 简单数据，直接转为十进制数
        subitem_decimal = data_item_elem.find('decimal')
        is_sign = data_item_elem.find('sign')
        decimal = 0
        if subitem_decimal is not None:
            decimal = int(subitem_decimal.text)
        sign = False
        if is_sign is not None:
            sign = True if is_sign.text=="yes" else False
        ret = prase_simple_type_data(data_item_elem, data_segment,index, need_delete)
        if ret == True:
            subitem_value = ret
        else:
            subitem_value = frame_fun.bcd_to_decimal(data_segment,decimal,need_delete,sign)

    return subitem_value

def prase_value_item(data_item_elem, data_segment, index, need_delete):
    parsevalue = prase_singal_item(data_item_elem,data_segment,index, need_delete)
    match = re.match(r'(\d+)', parsevalue)

    if match:
        # 如果匹配成功，返回匹配的部分
        value = match.group(1)
    else:
        value = f"{parsevalue}"
    value_elem = data_item_elem.find('value[@key="' + value + '"]')
    if value_elem is not None:
        # If <name> tag is present, use its text as bit_name
        value_name = value_elem.text
    else:
        # If <name> tag is not present, use an empty string
        if data_item_elem.find('value[@key="other"]') is not None:
            value_name = data_item_elem.find('value[@key="other"]').text
        else:
            value_name = parsevalue
    return value_name

def parse_data_item(data_item_elem, data_segment, index, need_delete):
    # 解析单个dataItem数据段
    result = {}
    if len(data_segment) == 0:
        return result

    # 获取dataItem标签的id属性值
    data_item_id = data_item_elem.get('id')
    data_item_name = data_item_elem.find('name').text

    # 递归解析子dataItem标签
    sub_data_item = data_item_elem.find('dataItem')
    if sub_data_item is not None:
        sub_data_segment = data_segment
        pos = 0
        for sub_data_item_elem in data_item_elem.findall('dataItem'):
            sub_data_item_id = sub_data_item_elem.get('id')
            sub_item_name = sub_data_item_elem.find('name').text
            sub_data_item_length = int(sub_data_item_elem.find('length').text)
            sub_data_segment = data_segment[pos:pos + sub_data_item_length]
            if sub_data_item_length > len(sub_data_segment):
                break
            if 'splitByLength' in sub_data_item_elem.tag:
                sub_data_segment = sub_data_segment[:int(sub_data_item_elem.find('length').text)]
            parsed_sub_data = parse_data_item(sub_data_item_elem,sub_data_segment,index + pos,need_delete)
            result_data = [sub_item_name, sub_data_segment, parsed_sub_data, [index + pos, index + pos + sub_data_item_length]]
            result[sub_data_item_id] = parsed_sub_data
            pos += sub_data_item_length
    elif data_item_elem.find('unit') is not None and data_item_elem.find('value') is not None:
        subitem_value = prase_value_item(data_item_elem, data_segment, index,  need_delete)
        singal_result = f"{subitem_value}"
        result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
    elif data_item_elem.find('unit') is not None:
        singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
        #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
        result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
        #result = singal_result
    elif data_item_elem.find('value') is not None:
        singal_result = prase_value_item(data_item_elem, data_segment, index,  need_delete)
        result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
    elif data_item_elem.find('time') is not None:
       # 解析时间数据
       subitem_time_format = data_item_elem.find('time').text
       subitem_type = data_item_elem.find('type')
       data_type = ""
       if subitem_type is not None:
           data_type = subitem_type.text
       time_data = data_segment[:6][::-1]
       if data_type in ("BIN","Bin","bin"):
           time_data = frame_fun.binary_to_bcd(time_data)
       singal_result = frame_fun.parse_time_data(time_data,subitem_time_format,need_delete)
       result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
        # 判断是否包含splitbit标签
    elif data_item_elem.find('splitbit') is not None:
        # 包含splitbit标签，则先解析splitbit数据
        splitbit_elem = data_item_elem.find('splitbit')
        parsed_bitwise_data = parse_bitwise_data(splitbit_elem, data_segment,index, need_delete)
        result = {data_item_id: [data_item_name, data_segment, parsed_bitwise_data,[index, index + len(data_segment)]]}
        # result.update(parsed_bitwise_data)

    # 解析splitByLength数据
    elif data_item_elem.find('splitByLength') is not None:
        splitLength_elem = data_item_elem.find('splitByLength')
        parsed_splitByLength_data = parse_splitByLength_data(data_item_elem, data_segment,index, need_delete)
        result = parsed_splitByLength_data
    elif data_item_elem.find('itembox') is not None:
        result = parse_item(data_item_elem, data_segment, index + pos,  need_delete)
        # result.update(parsed_splitByLength_data)
    elif data_item_elem.find('indelength') is not None:
        length = len(data_segment)
        length_vaue = f"{length}"
        length_elem = data_item_elem.find('indelength[@len="' + length_vaue + '"]')
        if length_elem is not None:
            result = parse_data_item(length_elem, data_segment, index, need_delete)
    elif data_item_elem.find('type') is not None:
        data_type = data_item_elem.find('type').text.upper()
        if data_type not in ("BCD","BIN","ASCII"):
            template = frame_fun.get_template_element(data_type,frame_fun.globalprotocol, frame_fun.globregion)
            if template is not None:
                result = parse_splitByLength_data(template, data_segment, index,  need_delete)
            elif data_type == "IPWITHPORT":
                i = 0
                port = data_segment[0:2]
                port_str = frame_fun.prase_port(port)
                ip_str = frame_fun.prase_ip_str(data_segment[2:6])
                subitem_value = ["IP地址", data_segment[2:6], ip_str, [index + 2,index + 8]]
                result[i] = subitem_value
                i+=1
                subitem_value = ["端口号", port, port_str, [index,index + 2]]
                result[i] = subitem_value
                i+=1
            else:
                if data_item_id:
                    key = data_item_id
                else:
                    key = data_item_name
                singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
                #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
                result[key] = [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]
        else:
            if data_item_id:
                key = data_item_id
            else:
                key = data_item_name
            singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
            #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
            result[key] = [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]
    else:
        if data_item_id:
            key = data_item_id
        else:
            key = data_item_name
        singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
        #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
        result[key] = [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]
    return result
    #return {data_item_id: [data_item_name, data_segment, result,[index, index + len(data_segment)]]}
def get_sub_length(data,sub_item_ele, target_name):
    length = 0
    sub_length = 0
    all_item = sub_item_ele.findall('splitByLength')
    for item in all_item:
        if item.find('name') is not None:
            if item.find('name').text == target_name:
                sub_length = int(item.find('length').text,10)
                value = prase_singal_item(item,data[:sub_length],0,False)
                length = int(value,10)
    return sub_length,length

def get_relay_type(relaytype):
    if relaytype == 0x00:
        return "普通中继"
    elif relaytype == 0x01:
        return "转发主站对电能表的拉闸命令"
    elif relaytype == 0x02:
        return "转发主站对电能表的允许合闸命令"
    elif relaytype == 0x03:
        return "转发主站对电能表的保电投入命令"
    elif relaytype == 0x04:
        return "转发主站对电能表的保电解除命令"
    else:
        return "未知"
    
class PraseFrameData():
    def parse_data_item(self,data_item_elem, data_segment, index, need_delete):
        # 解析单个dataItem数据段
        result = {}
        if len(data_segment) == 0:
            return result

        # 获取dataItem标签的id属性值
        data_item_id = data_item_elem.get('id')
        data_item_name = data_item_elem.find('name').text

        # 递归解析子dataItem标签
        sub_data_item = data_item_elem.find('dataItem')
        if sub_data_item is not None:
            sub_data_segment = data_segment
            pos = 0
            for sub_data_item_elem in data_item_elem.findall('dataItem'):
                sub_data_item_id = sub_data_item_elem.get('id')
                sub_item_name = sub_data_item_elem.find('name').text
                sub_data_item_length = int(sub_data_item_elem.find('length').text)
                sub_data_segment = data_segment[pos:pos + sub_data_item_length]
                if sub_data_item_length > len(sub_data_segment):
                    break
                if 'splitByLength' in sub_data_item_elem.tag:
                    sub_data_segment = sub_data_segment[:int(sub_data_item_elem.find('length').text)]
                parsed_sub_data = parse_data_item(sub_data_item_elem,sub_data_segment,index + pos,need_delete)
                result_data = [sub_item_name, sub_data_segment, parsed_sub_data, [index + pos, index + pos + sub_data_item_length]]
                result[sub_data_item_id] = parsed_sub_data
                pos += sub_data_item_length
        elif data_item_elem.find('unit') is not None and data_item_elem.find('value') is not None:
            subitem_value = prase_value_item(data_item_elem, data_segment, index,  need_delete)
            singal_result = f"{subitem_value}"
            result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
        elif data_item_elem.find('unit') is not None:
            singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
            #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
            result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
            #result = singal_result
        elif data_item_elem.find('value') is not None:
            singal_result = prase_value_item(data_item_elem, data_segment, index,  need_delete)
            result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
        elif data_item_elem.find('time') is not None:
            # 解析时间数据
            subitem_time_format = data_item_elem.find('time').text
            subitem_type = data_item_elem.find('type')
            data_type = ""
            if subitem_type is not None:
                data_type = subitem_type.text
            time_data = data_segment[:6][::-1]
            if data_type in ("BIN","Bin","bin"):
                time_data = frame_fun.binary_to_bcd(time_data)
            singal_result = frame_fun.parse_time_data(time_data,subitem_time_format,need_delete)
            result = {data_item_id: [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]}
                # 判断是否包含splitbit标签
        elif data_item_elem.find('splitbit') is not None:
            # 包含splitbit标签，则先解析splitbit数据
            splitbit_elem = data_item_elem.find('splitbit')
            parsed_bitwise_data = parse_bitwise_data(splitbit_elem, data_segment,index, need_delete)
            result = {data_item_id: [data_item_name, data_segment, parsed_bitwise_data,[index, index + len(data_segment)]]}
            # result.update(parsed_bitwise_data)

        # 解析splitByLength数据
        elif data_item_elem.find('splitByLength') is not None:
            splitLength_elem = data_item_elem.find('splitByLength')
            parsed_splitByLength_data = parse_splitByLength_data(data_item_elem, data_segment,index, need_delete)
            result = parsed_splitByLength_data
        elif data_item_elem.find('itembox') is not None:
            result = parse_item(data_item_elem, data_segment, index + pos,  need_delete)
            # result.update(parsed_splitByLength_data)
        elif data_item_elem.find('indelength') is not None:
            length = len(data_segment)
            length_vaue = f"{length}"
            length_elem = data_item_elem.find('indelength[@len="' + length_vaue + '"]')
            if length_elem is not None:
                result = parse_data_item(length_elem, data_segment, index, need_delete)
        elif data_item_elem.find('type') is not None:
            data_type = data_item_elem.find('type').text.upper()
            if data_type not in ("BCD","BIN","ASCII"):
                template = frame_fun.get_template_element(data_type,frame_fun.globalprotocol, frame_fun.globregion)
                if template is not None:
                    result = parse_splitByLength_data(template, data_segment, index,  need_delete)
                elif data_type == "IPWITHPORT":
                    i = 0
                    port = data_segment[0:2]
                    port_str = frame_fun.prase_port(port)
                    ip_str = frame_fun.prase_ip_str(data_segment[2:6])
                    subitem_value = ["IP地址", data_segment[2:6], ip_str, [index + 2,index + 8]]
                    result[i] = subitem_value
                    i+=1
                    subitem_value = ["端口号", port, port_str, [index,index + 2]]
                    result[i] = subitem_value
                    i+=1
                else:
                    if data_item_id:
                        key = data_item_id
                    else:
                        key = data_item_name
                    singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
                    #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
                    result[key] = [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]
            else:
                if data_item_id:
                    key = data_item_id
                else:
                    key = data_item_name
                singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
                #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
                result[key] = [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]
        else:
            if data_item_id:
                key = data_item_id
            else:
                key = data_item_name
            singal_result = prase_singal_item(data_item_elem, data_segment, index, need_delete)
            #result = [data_item_name,data_segment, singal_result, [index, index+len(data_segment)]]
            result[key] = [data_item_name, data_segment, singal_result,[index, index + len(data_segment)]]
        return result
    def parse_data(self,data_item_id, protocol, region, data_segment, index):
        # 根据xml配置解析数据
        parsed_data = {}
        data_item_elem = frame_fun.get_config_xml(data_item_id, protocol, region)
        need_delete = True if protocol == "DLT/645-2007" else False
        if data_item_elem is not None:
            parsed_data = parse_data_item(data_item_elem, data_segment, index, need_delete)
        return parsed_data
    def caculate_item_length(self,sub_element, data_segment, all_length_items=None):
        def execute_calculation(element, data, items=None):
            length = 0
            length_maap = {}
            if items is None:
                all_items = element.findall('splitByLength')
            else:
                all_items = items
            template_element = element.find('type')

            if len(all_items) == 0:
                if template_element is not None:
                    data_type = template_element.text.upper()
                    if data_type not in ("BCD", "BIN", "ASCII"):
                        template = frame_fun.get_template_element(data_type, frame_fun.globalprotocol, frame_fun.globregion)
                        if template is not None:
                            # 递归调用子函数
                            template_items = template.findall('splitByLength')
                            return execute_calculation(template, data, template_items)
            else:
                for data_subitem_elem in all_items:
                    subitem_name = data_subitem_elem.find('name').text
                    sub_length_content = data_subitem_elem.find('length').text
                    if sub_length_content == "unknown":
                        subitem_length = caculate_unknown_length(data_subitem_elem, data, length_maap)
                    else:
                        subitem_length = int(sub_length_content)
                    length += subitem_length
                    length_maap[subitem_name] = [length, subitem_length, data_subitem_elem]
            return length

        # 初始调用
        length = execute_calculation(sub_element, data_segment, all_length_items)

        return length
def is_dlt645_frame(data):
    # 判断报文长度是否符合最小要求
    if len(data) < 12:
        return False

    # 判断起始符和结束符
    if data[0] != 0x68 or data[-1] != 0x16 or data[7] != 0x68:
        return False

    # 判断数据长度是否合法
    data_length = data[9]
    if len(data) != data_length + 12:
        return False

    #计算校验位
    return True

def Analysis_645_fram_by_afn(frame, result_list, indx):
    afn = frame[8]
    Alalysis_head_frame(frame, result_list,indx)

    if afn == 0x11:#下行读取报文
        Alalysis_read_frame(frame, result_list,indx)
    elif afn in (0x91,0xB1):#读取回复正常
        analyze_read_response_frame(frame, result_list,indx)
    elif afn in (0xD1, 0xD2,0xD4,0xD6,0xD7,0xD9,0xDA,0xDB):#异常应答
        analyze_read_err_frame(frame, result_list,indx)
    elif afn == 0x12:#读取后续帧下行报文
        Alalysis_read_subsequent_frame(frame, result_list,indx)
    elif afn in (0x92,0xB2):#读取后续帧回复报文
        analyze_read_subsequent_response_frame(frame, result_list,indx)
    elif afn == 0x14:#写数据
        Alalysis_write_frame(frame, result_list,indx)
    elif afn == 0x93:#d读通信地址正常应答
        Alalysis_read_adress_frame(frame, result_list,indx)
    elif afn == 0x15:#写数据
        Alalysis_write_adress_frame(frame, result_list,indx)
    elif afn == 0x08:
        Alalysis_brodcast_time_frame(frame, result_list,indx)
    elif afn == 0x16:#冻结命令
        Alalysis_write_frozen_time_frame(frame, result_list,indx)
    elif afn in (0x17,0x97):#更改通信速率
        Alalysis_write_buradet_frame(frame, result_list,indx)
    elif afn == 0x18:#更改密码
        Alalysis_write_password_frame(frame, result_list,indx)
    elif afn == 0x98:#修改密码应答
        Alalysis_write_password_response_frame(frame, result_list,indx)
    elif afn == 0x19:#最大需量清零
        Alalysis_maximum_demand_reset_frame(frame, result_list,indx)
    elif afn == 0x1A:#电表清零
        Alalysis_meter_reset_frame(frame, result_list,indx)
    elif afn == 0x1B:#事件清零
        Alalysis_event_reset_frame(frame, result_list,indx)
    else:
        Alalysis_invalid_frame(frame, result_list,indx)
    Alalysis_end_frame(frame, result_list,indx)


def Alalysis_head_frame(frame, result_list,indx):
    # 解析报文
    data_length = frame[9]  # 数据长度
    control_code = frame[8]  # 控制码
    address = frame[1:7]  # 地址域
    address_with_spaces = frame_fun.get_data_str_with_space(address)
    address_str = frame_fun.get_data_str_reverser(address)

    frame_fun.add_data(result_list, "帧起始符", f"{frame[0]:02X}", "电表规约：标识一帧信息的开始",[indx + 0,indx + 1])
    frame_fun.add_data(result_list, "地址域", address_with_spaces,"电表通信地址：" + address_str,[indx+1,indx+7])

    frame_fun.add_data(result_list, "帧起始符", f"{frame[7]:02X}", "电表规约：标识一帧信息的开始",[indx+7,indx+8])

    afn_data = []
    binary_array = []
    frame_fun.get_bit_array(control_code, binary_array)
    func_code = "".join(str(bit) for bit in binary_array[-5:])
    if func_code == "00000":
        func_code_str = "保留"
    elif func_code == "01000":
        func_code_str = "广播校时"
    elif func_code == "10001":
        func_code_str = "读数据"
    elif func_code == "10010":
        func_code_str = "读后续数据"
    elif func_code == "10011":
        func_code_str = "读通信地址"
    elif func_code == "10100":
        func_code_str = "写数据"
    elif func_code == "10101":
        func_code_str = "写通信地址"
    elif func_code == "10110":
        func_code_str = "冻结命令"
    elif func_code == "10111":
        func_code_str = "更改通信速率"
    elif func_code == "11000":
        func_code_str = "修改密码"
    elif func_code == "11001":
        func_code_str = "最大需量清零"
    elif func_code == "11010":
        func_code_str = "电表清零"
    elif func_code == "11011":
        func_code_str = "事件清零"
    else:
        func_code_str = "未知"

    binary_decimal = int(func_code, 2)
    hexadecimal = hex(binary_decimal)

    D7_str = "主站发出的命令帧" if binary_array[0] == 0 else "从站发出的应答帧"
    D6_str = "从站正常应答" if binary_array[1] == 0 else "从站异常应答"
    D5_str = "无后续数据帧" if binary_array[2] == 0 else "有后续数据帧"
    frame_fun.add_data(afn_data, "D7传送反向", f"{binary_array[0]}", D7_str,[indx+8,indx+9])
    frame_fun.add_data(afn_data, "D7传送反向", f"{binary_array[1]}", D6_str,[indx+8,indx+9])
    frame_fun.add_data(afn_data, "D7传送反向", f"{binary_array[2]}", D5_str,[indx+8,indx+9])
    frame_fun.add_data(afn_data, "D0~D4功能码", hexadecimal[2:], func_code_str,[indx+8,indx+9])

    afn_str = "主站请求：" if binary_array[0] == 0 else "电表返回："
    frame_fun.add_data(result_list, "控制码", f"{control_code:02X}", afn_str+func_code_str, [indx+8,indx+9],afn_data)
    frame_fun.add_data(result_list, "数据长度", f"{data_length:02X}",f"长度={data_length}, 总长度={data_length + 12}(总长度=长度+12)",[indx+9,indx+10])


def Alalysis_end_frame(frame, result_list,indx):
    length = len(frame)
    cs = frame_fun.caculate_cs(frame[:-2])
    cs_str = "电表规约报文校验码正确" if cs == frame[-2] else f"电表规约校验码错误，应为：{cs:02X}"
    frame_fun.add_data(result_list, "校验码", f"{frame[-2]:02X}", cs_str,[indx + length -2,indx + length-1])
    frame_fun.add_data(result_list, "结束符", f"{frame[-1]:02X}", "电表规约报文结束符",[indx + length-1,indx + length])

def Alalysis_read_frame(frame, result_list,indx):
    length = len(frame)
    data_identifier = frame[10:14]  # 数据标识
    data_length = frame[9]  # 数据长度
    read_type = data_length - 4

    data_identifier_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)

    data_list = []
    data_item = frame_fun.get_config_xml(data_identifier_str, "DLT/645-2007", frame_fun.globregion)
    if data_item is not None:
        data_identifier_str = "数据标识编码：" + f"[{data_identifier_str}]" + "-" + data_item.find('name').text
    else:
        data_identifier_str = "数据标识编码：" + f"[{data_identifier_str}]"
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier), data_identifier_str,[indx + 10,indx + 14])
    if read_type == 1:
        block_num = frame[14] - 0x33
        frame_fun.add_data(data_list, "负荷记录块数", f"{frame[14]:02X}",f"负荷记录块数={block_num}",[indx +14,indx+15])
    elif read_type == 6:
        block_num = frame[14] - 0x33
        frame_fun.add_data(data_list, "负荷记录块数", f"{frame[14]:02X}",f"负荷记录块数={block_num}",[indx+14,indx+15])
        frame_fun.add_data(data_list, "给定时间", frame_fun.get_data_str_with_space(frame[15:-2]),frame_fun.parse_time_data(frame[15:-2],"mmhhDDMMYY",True),[indx+15,length + indx-2])
    elif read_type > 0:
        frame_fun.add_data(data_list, "液晶查看命令"," ".join(f"{b:02X}" for b in frame[14:-2]),"",[indx + 14,length + indx-2])

    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,length + indx-2],data_list)


def analyze_read_response_frame(frame, result_list,indx):
    # 解析报文
    data_list = []
    data_identifier = frame[10:14]  # 数据标识
    data_content = frame[14:-2]  # 数据内容
    length = len(frame)
    # 转换数据标识和数据内容为字符串形式
    prase_data = PraseFrameData()
    data_identifier_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)
    data_item_elem = frame_fun.get_config_xml(data_identifier_str, "DLT/645-2007", frame_fun.globregion)
    if data_item_elem is not None:
        sub_result = []
        sublength_ele = data_item_elem.find('length')
        all_length = len(data_content)
        if sublength_ele is not None:
            sublength = int(sublength_ele.text)
        else:
            sublength = len(data_content)
        if len(data_content) % sublength != 0 and len(data_content) > sublength:
            time = data_content[:5]
            time_str = frame_fun.parse_time_data(time,"mmhhDDMMYY",True)
            frame_fun.add_data(sub_result, "数据起始时间",frame_fun.get_data_str_with_space(time),time_str,[indx+14,indx +19])
            all_length -= 5
            data_content = data_content[5:]
            indx += 5
        pos = 0
        while pos < all_length:
            alalysic_result = prase_data.parse_data(data_identifier_str,"DLT/645-2007", frame_fun.globregion,data_content[pos:pos+sublength], 14 + pos +indx)
            frame_fun.prase_data_with_config(alalysic_result, True,sub_result)
            pos += sublength
        dis_data_identifier = "数据标识编码：" + f"[{data_identifier_str}]" + "-" + data_item_elem.find('name').text
        frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier),dis_data_identifier,[indx+10,indx+14])
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}", [indx+14,indx+length-2],sub_result)
    else:
        dis_data_identifier = "数据标识编码：" + f"[{data_identifier_str}]"
        frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier),dis_data_identifier,[indx+10,indx+14])
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}",[indx+14,indx+length-2])

    frame_fun.add_data(result_list, "数据域", "","数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)

def analyze_read_err_frame(frame, result_list,indx):
    length = len(frame)
    err_code = frame[10]
    binary_array = []
    frame_fun.get_bit_array((err_code - 0X33)&0XFF, binary_array)
    reversed_array = binary_array[:8][::-1]
    if reversed_array[1] == 1:
        err_str = "无请求数据"
    elif reversed_array[2] == 1:
        err_str = "密码错误/未授权"
    elif reversed_array[3] == 1:
        err_str = "通信速率不能更改"
    elif reversed_array[4] == 1:
        err_str = "年时区数超"
    elif reversed_array[5] == 1:
        err_str = "时段数超"
    elif reversed_array[6] == 1:
        err_str = "费率数超"
    elif (err_code - 0X33)&0XFF != 0:
        err_str  = "其他错误"
    
    frame_fun.add_data(result_list, "错误信息字",f"{err_code:02X}","错误类型: " + err_str,[indx+10,indx+length-2])


def Alalysis_read_subsequent_frame(frame, result_list,indx):
    data_identifier = frame[10:14]  # 数据标识
    data_length = frame[9]  # 数据长度
    seq = frame[-3]
    length = len(frame)
    data_identifier_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)

    data_list = []
    data_item = frame_fun.get_config_xml(data_identifier_str, "DLT/645-2007", frame_fun.globregion)
    if data_item is not None:
        data_identifier_str = "数据标识编码：" + f"[{data_identifier_str}]" + "-" + data_item.find('name').text
    else:
        data_identifier_str = "数据标识编码：" + f"[{data_identifier_str}]"
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier), data_identifier_str,[indx+10,indx+14])
   
    frame_fun.add_data(data_list, "帧序号",f"{seq:02X}", "请求帧序号:"+f"{(seq-0x33)&0xff}",[indx+length-3,indx+length-2])

    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)


def analyze_read_subsequent_response_frame(frame, result_list,indx):
    # 解析报文
    data_list = []
    data_identifier = frame[10:14]  # 数据标识
    data_content = frame[14:-2]  # 数据内容
    seq = frame[-3]
    length = len(frame)
    prase_data = PraseFrameData()
    # 转换数据标识和数据内容为字符串形式
    data_identifier_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)
    data_item_elem = frame_fun.get_config_xml(data_identifier_str, "DLT/645-2007", frame_fun.globregion)
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier),"数据标识编码：" + data_identifier_str,[indx+10,indx+14])
    if data_item_elem is not None:
        sub_result = []
        alalysic_result = prase_data.parse_data(data_identifier_str,"DLT/645-2007", frame_fun.globregion,data_content, indx+14)
        print(alalysic_result)
        frame_fun.prase_data_with_config(alalysic_result, True,sub_result)
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}", [indx+14,indx+length-2], sub_result)
    else:
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}",[indx+14,indx+length-2])
    frame_fun.add_data(data_list, "帧序号",f"{seq:02X}", "请求帧序号:"+f"{(seq-0x33)&0xff}",[indx+length-3,indx+length-2])
    frame_fun.add_data(result_list, "数据域", "","数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)


def Alalysis_write_frame(frame, result_list,indx):
    data_identifier = frame[10:14]  # 数据标识
    data_length = frame[9]  # 数据长度
    password = frame[14:18]
    operator = frame[18:22]
    length = len(frame)
    write_data = frame[22:-2]

    item_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)

    data_list = []
    prase_data = PraseFrameData()
    data_item = frame_fun.get_config_xml(item_str, "DLT/645-2007", frame_fun.globregion)
    if data_item is not None:
        data_identifier_str = "数据标识编码：" + f"[{item_str}]" + "-" + data_item.find('name').text
    else:
        data_identifier_str = "数据标识编码：" + f"[{item_str}]"
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier), data_identifier_str,[indx+10,indx+14])
    frame_fun.add_data(data_list, "密码权限",f"{password[0]:02x}", "权限："+f"{(password[0]-0x33)&0xff:02x}",[indx+14,indx+15])
    frame_fun.add_data(data_list, "密码",frame_fun.get_data_str_with_space(password[1:]), "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[indx+15,indx+18])
    frame_fun.add_data(data_list, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[indx+18,indx+22])

    if data_item is not None:
        write_result = []
        alalysic_result = prase_data.parse_data(item_str,"DLT/645-2007", frame_fun.globregion,write_data, 22 + indx)
        frame_fun.prase_data_with_config(alalysic_result, True,write_result)
        frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(write_data), "写数据内容："+frame_fun.get_data_str_delete_33h_reverse(write_data),[indx+22,indx+len(write_data) + 22],write_result)
    else:
        frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(write_data), "写数据内容："+frame_fun.get_data_str_delete_33h_reverse(write_data),[indx+22,indx+len(write_data) +22])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+len(write_data) + 22],data_list)

def analyze_write_replay_frame(frame, result_list,indx):
    err_code = frame[-3]
    if err_code != 0:
        err_str = "写数据错误"
    else:
        err_str = "正常应答"
    length = len(frame)
    frame_fun.add_data(result_list, "写数据应答",f"{err_code:02X}", err_str,[indx+length-3,indx+length-2])

def Alalysis_read_adress_frame(frame, result_list,indx):
    adress = frame[10:16]
    data_list = []
    length = len(frame)
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(adress), "通信地址："+frame_fun.get_data_str_delete_33h_reverse(adress),[indx+10,indx+16])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+16],data_list)


def Alalysis_write_adress_frame(frame, result_list,indx):
    adress = frame[10:16]
    data_list = []
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(adress), "写通信地址："+frame_fun.get_data_str_delete_33h_reverse(adress),[indx+10,indx+16])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+16],data_list)


def Alalysis_brodcast_time_frame(frame, result_list,indx):
    time = frame[10:16]
    data_list = []
    form_time = time[:6][::-1]
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(time), "校时时间："+ frame_fun.parse_time_data(form_time, "YYMMDDhhmmss",True),[indx+10,indx+16])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+16],data_list)

def Alalysis_write_frozen_time_frame(frame, result_list,indx):
    time = frame[10:14]
    form_time = frame_fun.frame_delete_33H(time)
    form_time = form_time[:4][::-1]
    data_list = []
    length = len(frame)
    frozen_type = frame_fun.parse_freeze_time(form_time)
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(time), "冻结命令："+frame_fun.get_data_str_delete_33h_reverse(time) + " " * 3 + "表示冻结时间为：" +frozen_type,[indx+10,indx+length-2])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)


def Alalysis_write_buradet_frame(frame, result_list,indx):
    CommunicationRate = frame[10]
    data_list = []
    binary_array = []
    length = len(frame)
    frame_fun.get_bit_array((CommunicationRate - 0X33)&0XFF, binary_array)
    reversed_array = binary_array[:8][::-1]
    if frame_fun.is_only_one_bit_set((CommunicationRate - 0X33)&0XFF) == False:
        rate = "特征字错误(多个bit位为1)"
    elif reversed_array[0] == 1 or reversed_array[7] == 1:
        rate = "保留"
    elif reversed_array[1] == 1:
        rate = "600bps"
    elif reversed_array[2] == 1:
        rate = "1200bps"
    elif reversed_array[3] == 1:
        rate = "2400bps"
    elif reversed_array[4] == 1:
        rate = "4800bps"
    elif reversed_array[5] == 1:
        rate = "9600bps"
    elif reversed_array[6] == 1:
        rate = "19200bps"

    frame_fun.add_data(data_list, "数据内容",f"{(CommunicationRate - 0x33)&0xff:02X}", "通信速率特征字："+f"{(CommunicationRate - 0x33)&0xff:02X}" + " " * 3 + "通信速率：" +rate,[indx+10,indx+11])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)


def Alalysis_write_password_frame(frame, result_list,indx):
    item = frame[10:14]
    origial_password = frame[14:18]
    new_password = frame[18:22]
    sub_result = []
    data_list = []
    length = len(frame)
    frame_fun.add_data(sub_result, "数据标识编码",frame_fun.get_data_str_with_space(item), "数据标识"+f"[{frame_fun.get_data_str_delete_33h_reverse(item)}]",[indx+10,indx+14])
    frame_fun.add_data(sub_result, "原密码及权限",frame_fun.get_data_str_with_space(origial_password), "原密码权限："+f"{(origial_password[0]-0x33)&0xff:02X}"+" "*5 + "原密码："+frame_fun.get_data_str_delete_33h_reverse(origial_password[1:]),[indx+14,indx+18])
    frame_fun.add_data(sub_result, "新密码及权限",frame_fun.get_data_str_with_space(new_password), "新密码权限："+f"{(new_password[0]-0x33)&0xff:02X}"+" "*5+ "新密码："+frame_fun.get_data_str_delete_33h_reverse(new_password[1:]),[indx+18,indx+22])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "密码设置",[indx+14,indx+22],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)

def Alalysis_write_password_response_frame(frame, result_list,indx):
    new_password = frame[10:14]
    sub_result = []
    data_list = []
    length = len(frame)
    frame_fun.add_data(sub_result, "新密码及权限",frame_fun.get_data_str_with_space(new_password), "新密码权限："+f"{(new_password[0]-0x33)&0xff:02X}"+" "*5+ "新密码："+frame_fun.get_data_str_delete_33h_reverse(new_password[1:]),[indx+10,indx+14])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "密码设置",[indx+10,indx+14],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)

def Alalysis_maximum_demand_reset_frame(frame, result_list,indx):
    password = frame[10:14]
    operator = frame[14:18]
    sub_result = []
    data_list = []
    length = len(frame)
    frame_fun.add_data(sub_result, "密码权限",frame_fun.get_data_str_with_space(password), "权限："+f"{(password[0]-0x33)&0xff:02X}"+" "*5+ "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[indx+10,indx+14])
    frame_fun.add_data(sub_result, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[indx+14,indx+18])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "最大需量清零",[indx+10,indx+length-2],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)

def Alalysis_meter_reset_frame(frame,result_list,indx):
    password = frame[10:14]
    operator = frame[14:18]
    sub_result = []
    data_list = []
    length = len(frame)
    frame_fun.add_data(sub_result, "密码权限",frame_fun.get_data_str_with_space(password), "权限："+f"{(password[0]-0x33)&0xff:02X}"+" "*5+ "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[indx+10,indx+14])
    frame_fun.add_data(sub_result, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[indx+14,indx+18])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "电表清零",[indx+10,indx+18],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+18],data_list)

def Alalysis_event_reset_frame(frame, result_list,indx):
    password = frame[10:14]
    operator = frame[14:18]
    item = frame[18:22]
    sub_result = []
    data_list = []
    length = len(frame)
    if frame_fun.is_all_elements_equal(item, 0x32):
        event_type="事件总清零"
    else:
        event_type="分项事件清零"

    frame_fun.add_data(sub_result, "密码权限",frame_fun.get_data_str_with_space(password), "权限："+f"{(password[0]-0x33)&0xff:02X}"+" "*5+ "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[indx+10,indx+14])
    frame_fun.add_data(sub_result, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[indx+14,indx+18])
    frame_fun.add_data(sub_result, "事件清零类型",frame_fun.get_data_str_with_space(item), "事件清零："+f"[{frame_fun.get_data_str_delete_33h_reverse(item)}]" +" - " +event_type,[indx+18,indx+22])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "事件清零",[indx+10,indx+22],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)

def Alalysis_invalid_frame(frame, result_list,indx):
    data_list = []
    length = len(frame)
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "数据域数据："+frame_fun.get_data_str_delete_33h_reverse(frame[10:-2]),[indx+10,indx+length-2])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [indx+10,indx+length-2],data_list)