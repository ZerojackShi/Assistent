import frame_fun

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

def Analysis_645_fram_by_afn(frame, result_list):
    afn = frame[8]
    Alalysis_head_frame(frame, result_list)

    if afn == 0x11:#下行读取报文
        Alalysis_read_frame(frame, result_list)
    elif afn in (0x91,0xB1):#读取回复正常
        analyze_read_response_frame(frame, result_list)
    elif afn in (0xD1, 0xD2,0xD4,0xD6,0xD7,0xD9,0xDA,0xDB):#异常应答
        analyze_read_err_frame(frame, result_list)
    elif afn == 0x12:#读取后续帧下行报文
        Alalysis_read_subsequent_frame(frame, result_list)
    elif afn in (0x92,0xB2):#读取后续帧回复报文
        analyze_read_subsequent_response_frame(frame, result_list)
    elif afn == 0x14:#写数据
        Alalysis_write_frame(frame, result_list)
    elif afn == 0x93:#d读通信地址正常应答
        Alalysis_read_adress_frame(frame, result_list)
    elif afn == 0x15:#写数据
        Alalysis_write_adress_frame(frame, result_list)
    elif afn == 0x08:
        Alalysis_brodcast_time_frame(frame, result_list)
    elif afn == 0x16:#冻结命令
        Alalysis_write_frozen_time_frame(frame, result_list)
    elif afn in (0x17,0x97):#更改通信速率
        Alalysis_write_buradet_frame(frame, result_list)
    elif afn == 0x18:#更改密码
        Alalysis_write_password_frame(frame, result_list)
    elif afn == 0x98:#修改密码应答
        Alalysis_write_password_response_frame(frame, result_list)
    elif afn == 0x19:#最大需量清零
        Alalysis_maximum_demand_reset_frame(frame, result_list)
    elif afn == 0x1A:#电表清零
        Alalysis_meter_reset_frame(frame, result_list)
    elif afn == 0x1B:#事件清零
        Alalysis_event_reset_frame(frame, result_list)
    else:
        Alalysis_invalid_frame(frame, result_list)
    Alalysis_end_frame(frame, result_list)


def Alalysis_head_frame(frame, result_list):
    # 解析报文
    data_length = frame[9]  # 数据长度
    control_code = frame[8]  # 控制码
    address = frame[1:7]  # 地址域
    address_with_spaces = frame_fun.get_data_str_with_space(address)
    address_str = frame_fun.get_data_str_reverser(address)

    frame_fun.add_data(result_list, "帧起始符", f"{frame[0]:02X}", "电表规约：标识一帧信息的开始",[0,1])
    frame_fun.add_data(result_list, "地址域", address_with_spaces,"电表通信地址：" + address_str,[1,7])

    frame_fun.add_data(result_list, "帧起始符", f"{frame[7]:02X}", "电表规约：标识一帧信息的开始",[7,8])

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
    frame_fun.add_data(afn_data, "D7传送反向", f"{binary_array[0]}", D7_str,[8,9])
    frame_fun.add_data(afn_data, "D7传送反向", f"{binary_array[1]}", D6_str,[8,9])
    frame_fun.add_data(afn_data, "D7传送反向", f"{binary_array[2]}", D5_str,[8,9])
    frame_fun.add_data(afn_data, "D0~D4功能码", hexadecimal[2:], func_code_str,[8,9])

    afn_str = "主站请求：" if binary_array[0] == 0 else "电表返回："
    frame_fun.add_data(result_list, "控制码", f"{control_code:02X}", afn_str+func_code_str, [8,9],afn_data)
    frame_fun.add_data(result_list, "数据长度", f"{data_length:02X}",f"长度={data_length}, 总长度={data_length + 12}(总长度=长度+12)",[9,10])


def Alalysis_end_frame(frame, result_list):
    cs = frame_fun.caculate_cs(frame[:-2])
    cs_str = "电表规约报文校验码正确" if cs == frame[-2] else f"电表规约校验码错误，应为：{cs:02X}"
    frame_fun.add_data(result_list, "校验码", f"{frame[-2]:02X}", cs_str,[-2,-1])
    frame_fun.add_data(result_list, "结束符", f"{frame[-1]:02X}", "电表规约报文结束符",[-1,0])

def Alalysis_read_frame(frame, result_list):
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
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier), data_identifier_str,[10,14])
    if read_type == 1:
        block_num = frame[14] - 0x33
        frame_fun.add_data(data_list, "负荷记录块数", f"{frame[14]:02X}",f"负荷记录块数={block_num}",[14,15])
    elif read_type == 6:
        block_num = frame[14] - 0x33
        frame_fun.add_data(data_list, "负荷记录块数", f"{frame[14]:02X}",f"负荷记录块数={block_num}",[14,15])
        frame_fun.add_data(data_list, "给定时间", frame_fun.get_data_str_with_space(frame[15:-2]),frame_fun.parse_time_data(frame[15:-2],"YYMMDDhhmm",True),[15,-2])
    elif read_type > 0:
        frame_fun.add_data(data_list, "液晶查看命令"," ".join(f"{b:02X}" for b in frame[14:-2]),"",[14,-2])

    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)


def analyze_read_response_frame(frame, result_list):
    # 解析报文
    data_list = []
    data_identifier = frame[10:14]  # 数据标识
    data_content = frame[14:-2]  # 数据内容

    # 转换数据标识和数据内容为字符串形式
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
            time_str = frame_fun.parse_time_data(time,"YYMMDDhhmm",True)
            frame_fun.add_data(sub_result, "数据起始时间",frame_fun.get_data_str_with_space(time),time_str,[14,19])
            all_length -= 5
            data_content = data_content[5:]
        pos = 0
        while pos < all_length:
            alalysic_result = frame_fun.parse_data(data_identifier_str,"DLT/645-2007", frame_fun.globregion,data_content[pos:pos+sublength], 19 + pos)
            frame_fun.prase_data_with_config(alalysic_result, True,sub_result)
            pos += sublength
        dis_data_identifier = "数据标识编码：" + f"[{data_identifier_str}]" + "-" + data_item_elem.find('name').text
        frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier),dis_data_identifier,[10,14])
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}", [14,-2],sub_result)
    else:
        dis_data_identifier = "数据标识编码：" + f"[{data_identifier_str}]"
        frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier),dis_data_identifier,[10,14])
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}",[14,-2])

    frame_fun.add_data(result_list, "数据域", "","数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)

def analyze_read_err_frame(frame, result_list):
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
    
    frame_fun.add_data(result_list, "错误信息字",f"{err_code:02X}","错误类型: " + err_str,[10,-2])


def Alalysis_read_subsequent_frame(frame, result_list):
    data_identifier = frame[10:14]  # 数据标识
    data_length = frame[9]  # 数据长度
    seq = frame[-3]

    data_identifier_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)

    data_list = []
    data_item = frame_fun.get_config_xml(data_identifier_str, "DLT/645-2007", frame_fun.globregion)
    if data_item is not None:
        data_identifier_str = "数据标识编码：" + f"[{data_identifier_str}]" + "-" + data_item.find('name').text
    else:
        data_identifier_str = "数据标识编码：" + f"[{data_identifier_str}]"
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier), data_identifier_str,[10,14])
   
    frame_fun.add_data(data_list, "帧序号",f"{seq:02X}", "请求帧序号:"+f"{(seq-0x33)&0xff}",[-3,-2])

    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)


def analyze_read_subsequent_response_frame(frame, result_list):
    # 解析报文
    data_list = []
    data_identifier = frame[10:14]  # 数据标识
    data_content = frame[14:-2]  # 数据内容
    seq = frame[-3]

    # 转换数据标识和数据内容为字符串形式
    data_identifier_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)
    data_item_elem = frame_fun.get_config_xml(data_identifier_str, "DLT/645-2007", frame_fun.globregion)
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier),"数据标识编码：" + data_identifier_str,[10,14])
    if data_item_elem is not None:
        sub_result = []
        alalysic_result = frame_fun.parse_data(data_identifier_str,"DLT/645-2007", frame_fun.globregion,data_content, 14)
        frame_fun.prase_data_with_config(alalysic_result, True,sub_result)
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}", [14,-2], sub_result)
    else:
        frame_fun.add_data(data_list, "数据标识内容",frame_fun.get_data_str_with_space(data_content),f"数据标识[{data_identifier_str}]内容数据{frame_fun.get_data_str_delete_33h_reverse(data_content)}",[14,-2])
    frame_fun.add_data(data_list, "帧序号",f"{seq:02X}", "请求帧序号:"+f"{(seq-0x33)&0xff}",[-3,-2])
    frame_fun.add_data(result_list, "数据域", "","数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)


def Alalysis_write_frame(frame, result_list):
    data_identifier = frame[10:14]  # 数据标识
    data_length = frame[9]  # 数据长度
    password = frame[14:18]
    operator = frame[18:22]

    write_data = frame[22:-3]

    item_str = frame_fun.get_data_str_delete_33h_reverse(data_identifier)

    data_list = []
    data_item = frame_fun.get_config_xml(item_str, "DLT/645-2007", frame_fun.globregion)
    if data_item is not None:
        data_identifier_str = "数据标识编码：" + f"[{item_str}]" + "-" + data_item.find('name').text
    else:
        data_identifier_str = "数据标识编码：" + f"[{item_str}]"
    frame_fun.add_data(data_list, "数据标识编码",frame_fun.get_data_str_with_space(data_identifier), data_identifier_str,[10,14])
    frame_fun.add_data(data_list, "密码权限",f"{password[0]:02x}", "权限："+f"{(password[0]-0x33)&0xff:02x}",[14,15])
    frame_fun.add_data(data_list, "密码",frame_fun.get_data_str_with_space(password[1:]), "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[15,18])
    frame_fun.add_data(data_list, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[18,22])

    if data_item is not None:
        write_result = []
        alalysic_result = frame_fun.parse_data(item_str,"DLT/645-2007", frame_fun.globregion,write_data, 22)
        frame_fun.prase_data_with_config(alalysic_result, True,write_result)
        frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(write_data), "写数据内容："+frame_fun.get_data_str_delete_33h_reverse(write_data),[22,-3],write_result)
    else:
        frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(write_data), "写数据内容："+frame_fun.get_data_str_delete_33h_reverse(write_data),[22,-3])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)

def analyze_write_replay_frame(frame, result_list):
    err_code = frame[-3]
    if err_code != 0:
        err_str = "写数据错误"
    else:
        err_str = "正常应答"
    
    frame_fun.add_data(result_list, "写数据应答",f"{err_code:02X}", err_str,[-3,-2])

def Alalysis_read_adress_frame(frame, result_list):
    adress = frame[10:16]
    data_list = []
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(adress), "通信地址："+frame_fun.get_data_str_delete_33h_reverse(adress),[10,16])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,16],data_list)


def Alalysis_write_adress_frame(frame, result_list):
    adress = frame[10:16]
    data_list = []
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(adress), "写通信地址："+frame_fun.get_data_str_delete_33h_reverse(adress),[10,16])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,16],data_list)


def Alalysis_brodcast_time_frame(frame, result_list):
    time = frame[10:16]
    data_list = []
    form_time = time[:6][::-1]
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(time), "校时时间："+ frame_fun.parse_time_data(form_time, "ssmmhhDDMMYY",True),[10,16])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,16],data_list)

def Alalysis_write_frozen_time_frame(frame, result_list):
    time = frame[10:14]
    form_time = frame_fun.frame_delete_33H(time)
    form_time = form_time[:4][::-1]
    data_list = []

    frozen_type = frame_fun.parse_freeze_time(form_time)
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(time), "冻结命令："+frame_fun.get_data_str_delete_33h_reverse(time) + " " * 3 + "表示冻结时间为：" +frozen_type,[10,-2])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)


def Alalysis_write_buradet_frame(frame, result_list):
    CommunicationRate = frame[10]
    data_list = []
    binary_array = []
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

    frame_fun.add_data(data_list, "数据内容",f"{(CommunicationRate - 0x33)&0xff:02X}", "通信速率特征字："+f"{(CommunicationRate - 0x33)&0xff:02X}" + " " * 3 + "通信速率：" +rate,[10,11])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)


def Alalysis_write_password_frame(frame, result_list):
    item = frame[10:14]
    origial_password = frame[14:18]
    new_password = frame[18:22]
    sub_result = []
    data_list = []
    frame_fun.add_data(sub_result, "数据标识编码",frame_fun.get_data_str_with_space(item), "数据标识"+f"[{frame_fun.get_data_str_delete_33h_reverse(item)}]",[10,14])
    frame_fun.add_data(sub_result, "原密码及权限",frame_fun.get_data_str_with_space(origial_password), "原密码权限："+f"{(origial_password[0]-0x33)&0xff:02X}"+" "*5 + "原密码："+frame_fun.get_data_str_delete_33h_reverse(origial_password[1:]),[14,18])
    frame_fun.add_data(sub_result, "新密码及权限",frame_fun.get_data_str_with_space(new_password), "新密码权限："+f"{(new_password[0]-0x33)&0xff:02X}"+" "*5+ "新密码："+frame_fun.get_data_str_delete_33h_reverse(new_password[1:]),[18,22])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "密码设置",[14,22],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)

def Alalysis_write_password_response_frame(frame, result_list):
    new_password = frame[10:14]
    sub_result = []
    data_list = []
    frame_fun.add_data(sub_result, "新密码及权限",frame_fun.get_data_str_with_space(new_password), "新密码权限："+f"{(new_password[0]-0x33)&0xff:02X}"+" "*5+ "新密码："+frame_fun.get_data_str_delete_33h_reverse(new_password[1:]),[10,14])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "密码设置",[10,14],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)

def Alalysis_maximum_demand_reset_frame(frame, result_list):
    password = frame[10:14]
    operator = frame[14:18]
    sub_result = []
    data_list = []
    frame_fun.add_data(sub_result, "密码权限",frame_fun.get_data_str_with_space(password), "权限："+f"{(password[0]-0x33)&0xff:02X}"+" "*5+ "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[10,14])
    frame_fun.add_data(sub_result, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[14,18])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "最大需量清零",[10,-2],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)

def Alalysis_meter_reset_frame(frame,result_list):
    password = frame[10:14]
    operator = frame[14:18]
    sub_result = []
    data_list = []
    frame_fun.add_data(sub_result, "密码权限",frame_fun.get_data_str_with_space(password), "权限："+f"{(password[0]-0x33)&0xff:02X}"+" "*5+ "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[10,14])
    frame_fun.add_data(sub_result, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[14,18])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "电表清零",[10,18],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,18],data_list)

def Alalysis_event_reset_frame(frame, result_list):
    password = frame[10:14]
    operator = frame[14:18]
    item = frame[18:22]
    sub_result = []
    data_list = []
    if frame_fun.is_all_elements_equal(item, 0x32):
        event_type="事件总清零"
    else:
        event_type="分项事件清零"

    frame_fun.add_data(sub_result, "密码权限",frame_fun.get_data_str_with_space(password), "权限："+f"{(password[0]-0x33)&0xff:02X}"+" "*5+ "密码："+frame_fun.get_data_str_delete_33h_reverse(password[1:]),[10,14])
    frame_fun.add_data(sub_result, "操作者代码",frame_fun.get_data_str_with_space(operator), "操作者代码："+frame_fun.get_data_str_delete_33h_reverse(operator),[14,18])
    frame_fun.add_data(sub_result, "事件清零类型",frame_fun.get_data_str_with_space(item), "事件清零："+f"[{frame_fun.get_data_str_delete_33h_reverse(item)}]" +" - " +event_type,[18,22])
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "事件清零",[10,22],sub_result)
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)

def Alalysis_invalid_frame(frame, result_list):
    data_list = []
    frame_fun.add_data(data_list, "数据内容",frame_fun.get_data_str_with_space(frame[10:-2]), "数据域数据："+frame_fun.get_data_str_delete_33h_reverse(frame[10:-2]),[10,-2])
    frame_fun.add_data(result_list, "数据域", "", "数据域传输时按字节进行加33H处理，接收后应按字节减33H处理", [10,-2],data_list)