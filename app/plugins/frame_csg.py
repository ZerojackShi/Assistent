from asyncio.windows_events import ERROR_CONNECTION_ABORTED
from xml.dom.expatbuilder import FragmentBuilder
from ..plugins.frame_fun import FrameFun as frame_fun
from ..plugins.frame_fun import CustomMessageBox
from ..plugins.protocol import PraseFrameData, FRAME_645
from PyQt5.QtWidgets import QMessageBox
import re
from datetime import datetime, timedelta
from enum import Enum
ITEM_ACK_NAK=0xE0000000
MASK_FIR = 0x40
MASK_FIN = 0x20

class FramePos(Enum):
    POS_START0  = 0
    POS_DATALEN = 1           #数据长度
    POS_START1  = 5
    POS_CTRL    = 6           #控制码
    POS_RTUA    = 7           #集中器逻辑地址
    POS_UID     = 10           #终端地址        2字节
    POS_MSA     = 13          #主站地址
    POS_AFN     = 14          #应用层功能码
    POS_SEQ     = 15          #命令序号
    POS_DATA    = 16          #用户数据域起始
    POS_ITEM    = 18          #数据项起始


ACK = 0x00        #全部确认
NAK = 0x01        #全部否认

def init_frame(ctrl, afn, adress, msa, seq, frame):
    frame[FramePos.POS_START0.value] = 0x68
    frame[FramePos.POS_START1.value] = 0x68
    frame[FramePos.POS_CTRL.value] = ctrl
    frame[FramePos.POS_RTUA.value:FramePos.POS_RTUA.value + 6] = adress
    frame[FramePos.POS_MSA.value] = msa
    frame[FramePos.POS_AFN.value] = afn
    frame[FramePos.POS_SEQ.value] = seq
def get_frame(point_arrray:list, itemData:dict, frame:list=None):
    if frame is None:
        frame = bytearray()
    frame_len = 0
    def push_item_data_into_frame(itemData:dict, frame):
        pos = 0
        for item, data in itemData.items():
            pos += frame_fun.item_to_di(item, frame)
            if data is not None:
                pos += frame_fun.prase_text_to_frame(data, frame)
        return pos
    if point_arrray[0] == 0xFF and point_arrray[1] == 0xff:
        frame.extend([0xFF, 0XFF])
        frame_len += 2
        frame_len += push_item_data_into_frame(itemData, frame)

    else:
        for meter_point in point_arrray:
            da1, da2 = toDA(meter_point)
            frame.extend([da1, da2])
            frame_len += 2
            frame_len += push_item_data_into_frame(itemData, frame)

    return frame_len
def add_point_to_frame(point, frame:list):
    if point == 0xFFFF:
        frame.extend([0xFF, 0XFF])
    else:
        da1, da2 = toDA(point)
        frame.extend([da1, da2])
    return 2

def add_point_and_item_to_frame(point_arrray:list, item_array:list, frame:list=None):
    if frame is None:
        frame = bytearray()
    frame_len = 0
    def push_item_into_frame(meter_point, itemData:dict, frame):
        pos = 0
        for item in item_array:
            if meter_point == 0XFFFF:
                frame.extend([0xFF, 0XFF])
                pos += 2
            else:
                da1, da2 = toDA(meter_point)
                frame.extend([da1, da2])
                pos += 2
            pos += frame_fun.item_to_di(item, frame)
        return pos
    if point_arrray[0] == 0xFF and point_arrray[1] == 0xff:
        meter_point = 0xFFFF
        frame_len += push_item_into_frame(meter_point, item_array, frame)

    else:
        for meter_point in point_arrray:
            frame_len += push_item_into_frame(meter_point, item_array, frame)

    return frame_len

def add_point_and_item_and_time_to_frame(point_arrray:list, item_array:list, start_time:list, endtime:list, datakind:int=None, frame:list=None):
    frame_len = 0
    def push_item_into_frame(meter_point, itemData:dict, frame):
        pos = 0
        for item in item_array:
            if meter_point == 0XFFFF:
                frame.extend([0xFF, 0XFF])
                pos += 2
            else:
                da1, da2 = toDA(meter_point)
                frame.extend([da1, da2])
                pos += 2
            pos += frame_fun.item_to_di(item, frame)
            frame.extend(start_time)
            frame.extend(endtime)
            if datakind is not None:
                frame.extend([datakind])
                pos += 1
            pos += 12
            
        return pos
    if point_arrray[0] == 0xFF and point_arrray[1] == 0xff:
        meter_point = 0xFFFF
        frame_len += push_item_into_frame(meter_point, item_array, frame)

    else:
        for meter_point in point_arrray:
            frame_len += push_item_into_frame(meter_point, item_array, frame)

    return frame_len

def add_point_array_to_frame(frame, point_array):
    pos = 0
    count = 0
    if point_array[0] == 0xFFFF:
        frame.append(0xff)
        frame.append(0xff)
        count = 1
        pos += 2
    else:
        count = len(point_array)
        for meter_point in point_array:
            if meter_point == 0xFFFF:
                frame.append(0xff)
                frame.append(0xff)
                pos += 2
            else:
                da1, da2 = toDA(meter_point)
                frame.append(da1)
                frame.append(da2)
                pos += 2

    return count, pos
def add_pw_to_frame(frame:list):
    frame.extend([0x00] * 16)
    return 16

def add_item_array_to_frame(frame, item_array):
    pos = 0
    for item in item_array:
        pos += frame_fun.item_to_di(item, frame)
    return pos

def set_frame_finish(data, frame:list):
    frame_len = 0
    if frame[FramePos.POS_AFN.value] == 0x04:
        pw = [0x00] * 16
        frame.extend(pw)
        data.extend(pw)
        frame_len = 16
    caculate_cs = frame_fun.caculate_cs(data)
    frame.extend([caculate_cs, 0x16])
    return frame_len

def set_frame_len(length, frame):
    frame[FramePos.POS_DATALEN.value] = length & 0X00ff
    frame[FramePos.POS_DATALEN.value + 1] = length >> 8
    frame[FramePos.POS_DATALEN.value + 2] = length & 0X00ff
    frame[FramePos.POS_DATALEN.value + 3] = length >> 8
def is_csg_frame(frame):
    if len(frame) < 24:
        return False
    if frame[0] != 0x68 or frame[5] != 0x68:
        return False
    if frame[1] != frame[3] or frame[2] != frame[4]:
        print("frame err")
        return False
    frame_length = ((frame[2] << 8) | frame[1])
    if frame_length + 8 != len(frame):
        print("length err")
        return False
    if frame[-1] != 0x16:
        return False
    return True

def is_contoine_custom_head(frame):
    if frame[0] != 0x66 and frame[47] != 0x66:
        return False
    if frame[3] != frame[-3] and frame[4] != frame[-2]:
        return False
    return True

class FrameCsg():
    def is_contoine_custom_head(self, frame):
        if frame[0] != 0x66 and frame[47] != 0x66:
            return False
        if frame[3] != frame[-3] and frame[4] != frame[-2]:
            return False
        return True
        
    def is_csg_frame(self,data):
        frame = data.copy()
        if len(frame) < 24:
            return False
        
        if len(frame) > 84:
            if self.is_contoine_custom_head(frame[:84]):
                frame = frame[84:]

        if frame[0] != 0x68 or frame[5] != 0x68:
            return False
        if frame[1] != frame[3] or frame[2] != frame[4]:
            print("frame err")
            return False
        frame_length = ((frame[2] << 8) | frame[1])
        if frame_length + 8 != len(frame):
            print("length err")
            return False
        if frame[-1] != 0x16:
            return False
        return True
    def Analysis_csg_frame_by_afn(self,frame,result_list,index):
        
        if len(frame) > 84:
            if self.is_contoine_custom_head(frame[:84]):
                Analysic_csg_custom_head_frame(frame,result_list,index)
                frame = frame[84:]
                index += 84

        afn = frame[14]
        dir, prm = Analysic_csg_head_frame(frame,result_list,index)

        if afn == 0x00:
            Analysic_csg_ack_frame(frame, dir, prm, result_list,index)
        elif afn == 0x02:
            Analysic_csg_link_frame(frame, dir, prm, result_list,index)
        elif afn == 0x04:
            Analysic_csg_write_frame(frame, dir, prm,result_list,index)
        elif afn == 0x06:
            Analysic_csg_security_frame(frame, dir, prm,result_list,index)
        elif afn == 0x0C:
            Analysic_csg_read_cur_frame(frame, dir, prm,result_list,index)
        elif afn == 0x0D:
            Analysic_csg_read_history_frame(frame, dir, prm,result_list,index)
        elif afn == 0x0A:
            Analysic_csg_read_param_frame(frame, dir, prm,result_list,index)
        elif afn ==0x10:
            Analysic_csg_relay_frame(frame, dir, prm,result_list,index)
        elif afn == 0x12:
            Analysic_csg_read_task_frame(frame, dir, prm,result_list,index)
        elif afn == 0x13:
            Analysic_csg_read_alarm_frame(frame, dir, prm,result_list,index)
        elif afn == 0x0e:
            Analysic_csg_read_event_frame(frame, dir, prm,result_list,index)
        elif afn == 0x23:
            Analysic_csg_topo_frame(frame, dir, prm,result_list,index)
        Analysic_csg_end_frame(frame,result_list,index)


def Analysic_csg_head_frame(frame,result_list,start_pos):
    length_data = frame[1:5]
    control_data = frame[6]
    length = length_data[1] << 8 | length_data[0]
    adress_data = frame[7:14]
    frame_fun.add_data(result_list, "起始符", f"{frame[0]:02X}", "起始符",[start_pos + 0,start_pos + 1])
    frame_fun.add_data(result_list,"长度", frame_fun.get_data_str_with_space(length_data), f"长度={length}，总长度={length + 8}(总长度=长度+8)",[start_pos + 1,start_pos + 5])
    frame_fun.add_data(result_list,"起始符", f"{frame[5]:02X}", "起始符",[start_pos + 5,start_pos + 6])
    contro_result, result_str,dir, prm = get_control_code_str(control_data,start_pos)
    frame_fun.add_data(result_list,"控制域", f"{frame[6]:02X}", result_str,[start_pos + 6,start_pos + 7],contro_result)
    adress_result, ertu_adress = get_adress_result(adress_data, start_pos + 7)
    frame_fun.add_data(result_list,"地址域",frame_fun.get_data_str_with_space(adress_data), "终端逻辑地址" + ertu_adress,[start_pos + 7,start_pos + 14],adress_result)
    return dir, prm

def get_csg_adress(frame):
    adress_data = frame[7:14]
    adress_result, ertu_adress = get_adress_result(adress_data, 7)
    return ertu_adress

def get_frame_info(frame):
    control_data = frame[6]
    adress_data = frame[7:14]
    A3 = adress_data[6]
    seq = A3 & 0xf0
    afn = frame[14]
    contro_result, result_str,dir, prm = get_control_code_str(control_data,0)
    adress_result, ertu_adress = get_adress_result(adress_data, 7)

    return dir, prm, seq, afn, ertu_adress

def Analysic_csg_end_frame(frame, result_list, start_pos):
    cs = frame[-2]
    caculate_cs = frame_fun.caculate_cs(frame[6:-2])
    cs_str = "校验正确" if cs == caculate_cs else f"校验码错误，应为：{caculate_cs:02X}"
    frame_fun.add_data(result_list, "校验码CS", f"{cs:02X}", cs_str, [start_pos + len(frame)-2,start_pos + len(frame)-1])
    frame_fun.add_data(result_list, "结束符", f"{frame[-1]:02X}","结束符",[start_pos + len(frame)-1,start_pos + len(frame)])

def send_ack_frame(frame, control_code):
    replay_frame = []
    replay_frame = frame.copy()
    # item = frame[POS_DATA + 2: POS_DATA + 6]
    replay_frame = replay_frame[:25]
    replay_frame.extend([0] * (25 - len(replay_frame)))
    tpv_area = frame[-7:-2]

    if control_code == 9:
        replay_frame[FramePos.POS_CTRL.value] = 0x0B
    else:
        replay_frame[FramePos.POS_CTRL.value] = 0x08

    replay_frame[FramePos.POS_MSA.value] = 0x0A
    replay_frame[FramePos.POS_AFN.value] = 0x00
    
    if replay_frame[FramePos.POS_SEQ.value] & 0x80:
        tpv = True
    else:
        tpv = False
    replay_frame[FramePos.POS_SEQ.value] &= 0x7F
    replay_frame[FramePos.POS_SEQ.value] |= MASK_FIR | MASK_FIN
    replay_frame[FramePos.POS_DATA.value] = frame[FramePos.POS_DATA.value]
    replay_frame[FramePos.POS_DATA.value + 1] = frame[FramePos.POS_DATA.value + 1]
    replay_frame[FramePos.POS_DATA.value + 2] = (ITEM_ACK_NAK) & 0xFF
    replay_frame[FramePos.POS_DATA.value + 3] = (ITEM_ACK_NAK >> 8) & 0xFF
    replay_frame[FramePos.POS_DATA.value + 4] = (ITEM_ACK_NAK >> 16) & 0xFF
    replay_frame[FramePos.POS_DATA.value + 5] = (ITEM_ACK_NAK >> 24) & 0xFF
    replay_frame[FramePos.POS_DATA.value + 6] = ACK
    pos = FramePos.POS_DATA.value + 7 
    if tpv:
        replay_frame[FramePos.POS_SEQ.value] |= 0x80
        replay_frame.extend(tpv_area)
        pos += 5
    pos -= FramePos.POS_CTRL.value
    replay_frame[FramePos.POS_DATALEN.value] = pos
    replay_frame[FramePos.POS_DATALEN.value + 1] = pos >> 8
    replay_frame[FramePos.POS_DATALEN.value + 2] = pos
    replay_frame[FramePos.POS_DATALEN.value + 3] = pos >> 8

    caculate_cs = frame_fun.caculate_cs(replay_frame[6:-2])
    replay_frame[-2] = caculate_cs
    replay_frame[-1] = 0x16

    return replay_frame

def get_dir_prm(control):
    binary_array = []
    frame_fun.get_bit_array(control, binary_array)
    dir = binary_array[0]
    prm = binary_array[1] 
    acd = binary_array[2]
    fcv = binary_array[3]

    return dir, prm,acd,fcv

def get_control_code_str(control,start_pos):
    contro_result = []
    binary_array = []
    frame_fun.get_bit_array(control, binary_array)
    dir = binary_array[0]
    prm = binary_array[1] 
    acd = binary_array[2]
    fcv = binary_array[3]
    control_code = control & 0x0f
    if prm == 1:
        prm_str = "来自启动站"
        ayalysic_str = "主站发送" if dir == 0 else "终端上送"
        if control_code == 0:
            service_fun = "备用"
        elif control_code == 1:
            service_fun = "复位命令"
        elif control_code in (2,3):
            service_fun = "备用"
        elif control_code == 4:
            service_fun = "用户数据"
        elif control_code >= 5 and control_code <= 8:
            service_fun = "备用"
        elif control_code == 9:
            service_fun = "链路测试"
        elif control_code == 10:
            service_fun = "请求1级数据"
        elif control_code == 11:
            service_fun = "请求2级数据"
        else:
            service_fun = "备用"
    else:
        prm_str = "来自从动站"
        ayalysic_str = "主站响应" if dir == 0 else "终端响应"
        if control_code == 0:
            service_fun = "认可"
        elif control_code >= 1 and control_code <= 7:
            service_fun = "备用"
        elif control_code == 8:
            service_fun = "用户数据"
        elif control_code == 9:
            service_fun = "否定：无所召唤数据"
        elif control_code == 10:
            service_fun = "备用"
        elif control_code == 11:
            service_fun = "链路状态"
        else:
            service_fun = "备用"
    dir_str = "主站发出的下行报文" if dir == 0 else "终端发出的上行报文"
    acd_str = "有效" if fcv == 1 else "无效"
    fcv_str = "FCB位有效" if fcv == 1 else "FCB位无效"
    frame_fun.add_data(contro_result, "D7传输方向位DIR", f"{dir}", dir_str,[start_pos + 6,start_pos + 7])
    frame_fun.add_data(contro_result, "D6启动标志位PRM", f"{prm}", prm_str,[start_pos + 6,start_pos + 7])
    frame_fun.add_data(contro_result, "D5帧计数位FCB(下行)/要求访问位ACD(上行)", f"{acd}", acd_str,[start_pos + 6,start_pos + 7])
    frame_fun.add_data(contro_result, "D4帧计数有效位FCV(下行)/保留(上行)", f"{fcv}", fcv_str,[start_pos + 6,start_pos + 7])
    frame_fun.add_data(contro_result, "D3~D0功能码", f"{control_code}", prm_str + ":" + service_fun,[start_pos + 6,start_pos + 7])
    return contro_result, ayalysic_str + service_fun, dir, prm

def get_adress_result(adress, index):
    adress_result = []
    A1 = adress[:3]
    A2 = adress[3:6]
    A3 = adress[6]
    A1_str = frame_fun.get_data_str_with_space(A1)
    A2_str = frame_fun.get_data_str_with_space(A2)

    frame_fun.add_data(adress_result, "省地市区县码 A1", A1_str, "省地市县码=" + frame_fun.get_data_str_reverser(A1) + f"省{A1[2]:02X},地市{A1[1]:02X},区县{A1[0]:02X}",[index,index+3])
    frame_fun.add_data(adress_result, "终端地址 A2", A2_str, "终端地址=" + frame_fun.get_data_str_reverser(A2),[index + 3,index+6])
    seq = A3 & 0xf0
    master = A3 & 0x0f
    A3_result = []
    frame_fun.add_data(A3_result, "D7~D4帧序号", f"{seq}", f"帧序号={seq}",[index + 6,index+7])
    frame_fun.add_data(A3_result, "D3~D0主站地址", f"{master}", f"主站地址={master}",[index + 6,index+7])
    frame_fun.add_data(adress_result, "主站地址 A3", f"{A3:02X}", "",[index + 6,index+7],A3_result)
    return adress_result, frame_fun.get_data_str_reverser(A1) + frame_fun.get_data_str_reverser(A2)

def get_afn_and_seq_result(data,index,result_list):
    afn = data[0]
    seq = data[1]

    if afn == 0x00:
        afn_str = "确认/否定"
    elif afn == 0x02:
        afn_str = "链路接口检测"
    elif afn == 0x04:
        afn_str = "写参数"
    elif afn == 0x06:
        afn_str = "安全认证"
    elif afn == 0x0A:
        afn_str = "读参数"
    elif afn == 0x0C:
        afn_str = "读当前数据"
    elif afn == 0x0D:
        afn_str = "读历史数据"
    elif afn == 0x0E:
        afn_str = "读事件记录"
    elif afn == 0x0F:
        afn_str = "文件传输"
    elif afn == 0x10:
        afn_str = "中继转发"
    elif afn == 0x12:
        afn_str = "读任务数据"
    elif afn == 0x13:
        afn_str = "读告警数据"
    elif afn == 0x14:
        afn_str = "级联命令"
    elif afn == 0x15:
        afn_str = "用户自定义数据"
    elif afn == 0x16:
        afn_str = "数据安全传输"
    elif afn == 0x17:
        afn_str = "数据转加密"
    elif afn == 0x23:
        afn_str = "主站中转报文"
    else:
        afn_str = "备用"
    binary_array = []
    frame_fun.get_bit_array(seq, binary_array)
    tpv = binary_array[0]
    fir = binary_array[1]
    fin = binary_array[2]
    con = binary_array[3]
    pseq = seq & 0x0f
    seq_result = []
    Tpv_str = "帧末尾无时间标签Tp" if tpv == 0 else "帧末尾带有时间标签Tp"
    if fir == 0 and fin == 0:
        fir_str = "当前帧为多帧：中间帧"
        fin_str = "当前帧为多帧：中间帧"
        seq_str = "多帧：中间帧"
    elif fir == 0 and fin == 1:
        fir_str = "当前帧为多帧：结束帧"
        fin_str = "当前帧为最后一帧：结束帧"
        seq_str = "多帧：结束帧"
    elif fir == 1 and fin == 0:
        fir_str = "当前帧为多帧：第一帧"
        fin_str = "当前帧为多帧：有后续帧"
        seq_str = "多帧：第一帧"
    else:
        fir_str = "当前帧为单帧：第一帧"
        fin_str = "当前帧为单帧：最后一帧"
        seq_str = "单帧：最后一帧"
    con_str = "需要对该帧报文进行确认" if con == 1 else "不需要对该帧报文进行确认"
    pseq_str = f"帧内序号={pseq}"
    frame_fun.add_data(seq_result, "D7帧时间标签有效位TpV", f"{tpv}", Tpv_str, [index + 1, index + 2])
    frame_fun.add_data(seq_result, "D6首帧标志FIR", f"{fir}", fir_str, [index + 1, index + 2])
    frame_fun.add_data(seq_result, "D5首帧标志FIN", f"{fin}", fin_str, [index + 1, index + 2])
    frame_fun.add_data(seq_result, "D4首帧标志FIN", f"{con}", con_str, [index + 1, index + 2])
    frame_fun.add_data(seq_result, "D3~D0帧内序号", f"{pseq}", pseq_str, [index + 1, index + 2])

    frame_fun.add_data(result_list, "功能码AFN", f"{afn:02X}", afn_str, [index, index + 1])
    frame_fun.add_data(result_list, "帧序列SEQ", f"{seq:02X}", seq_str + "，" + pseq_str, [index + 1, index + 2], seq_result)
    return tpv

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

def toDA(iVal):
    low = (iVal - 1) % 8
    high = (iVal - 1) // 8  # Use integer division //
    mask = 0
    ret = 0
    mask = 1

    if iVal == 0:
         ret = 0
    else:
        ret = (high + 1) << 8
        while low:
            mask <<= 1
            low -= 1
        ret |= mask
    da1 = ret & 0x00ff
    da2 = ret >> 8
    return da1, da2

def judge_is_exit_pw(data_segment, item_element=None, data_time=None,with_time=False):
    if item_element is not None:
        if guest_next_data_is_cur_item_data(item_element, data_segment, data_time):
            return False
        else:
            return judge_is_exit_pw(data_segment, None, None, with_time)
    total_len = len(data_segment)
    pos = 0
    while total_len > pos:
        item = data_segment[2 + pos:6 + pos]
        data_item = frame_fun.get_data_str_reverser(item)
        data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
        if data_item_elem is not None:
            sub_length_cont = data_item_elem.find('length').text
            if sub_length_cont is not None:
                if sub_length_cont.upper() in "UNKNOWN":
                    prase_data = PraseFrameData()
                    sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[6:])
                else:
                    sub_length = int(sub_length_cont)
                pos += sub_length + 6
                if with_time:
                    pos += 6
            else:
                return False
        else:
            return True
    return False
def guest_is_exit_pw(length,data_segment, data_item_elem=None, data_time=None,with_time=False):
    if length < 16:
        return False
    if frame_fun.is_array_all_zeros(data_segment[-16:]):
        return True
    else:
        return judge_is_exit_pw(data_segment[-16:], data_item_elem, data_time, with_time)

def guest_next_data_is_cur_item_data(item_element, data_segment, data_time):
    if item_element is not None:
        length, new_data = recaculate_sub_length(item_element, data_segment)
        next_item = frame_fun.get_data_str_reverser(data_segment[2:6])
        if next_item == item_element.get('id'):
            return False
        if is_valid_bcd_time(data_segment[length:length+6]):
            if data_time is not None:
                return is_within_one_month(data_segment[length:length+6], data_time)
    return False

def bcd_array_to_datetime(bcd_array):

    century = frame_fun.bcd2int(bcd_array[0])
    year = frame_fun.bcd2int(bcd_array[1])
    month = frame_fun.bcd2int(bcd_array[2])
    day = frame_fun.bcd2int(bcd_array[3])
    hour = frame_fun.bcd2int(bcd_array[4])
    if len(bcd_array) > 5:
        minute = frame_fun.bcd2int(bcd_array[5])
    else:
        minute = 0
    
    full_year = century * 100 + year
    try:
        dt = datetime(full_year, month, day, hour, minute)
        return dt
    except ValueError:
        return False

def is_within_one_month(bcd_array1, bcd_array2):
    # 解析BCD码数组为日期时间对象
    dt1 = bcd_array_to_datetime(bcd_array1)
    dt2 = bcd_array_to_datetime(bcd_array2)
    
    if dt1 is False or dt2 is False:
        return False
    # 计算日期时间对象之间的差值
    if dt1 <= dt2:
        return False
    time_difference = dt2 - dt1
    if abs(dt2.year - dt1.year) > 1:
        return False
    # 检查差值是否不超过一个月
    if time_difference <= timedelta(days=30):
        return True
    else:
        return False

def is_valid_bcd_time(bcd_array):
    # 检查BCD码数组长度是否符合时间表示的要求
    if len(bcd_array) != 6:
        return False

    # 分别提取BCD码的各个部分
    century = frame_fun.bcd2int(bcd_array[0])
    year = frame_fun.bcd2int(bcd_array[1])
    month = frame_fun.bcd2int(bcd_array[2])
    day = frame_fun.bcd2int(bcd_array[3])
    hour = frame_fun.bcd2int(bcd_array[4])
    minute = frame_fun.bcd2int(bcd_array[5])

    # 检查各个部分是否在合法范围内
    if century > 99 or year > 99 or month < 1 or month > 12 or day < 1 or day > 31 or hour >= 24 or minute >= 60:
        return False

    # 检查特殊情况，如闰年和月份的天数
    if month in [4, 6, 9, 11] and day > 30:
        return False
    year = century * 100 + year
    if month == 2 and ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)) and day > 29:
        return False
    if month == 2 and day > 28:
        return False

    return True


def prase_tpv_data(tpv):
    time = tpv[:4]
    delay = tpv[4]
    time_str = frame_fun.parse_time_data(time,"ssmmhhDD",False)
    tpv_str = "启动帧发送时标：" + time_str + "。" + f"允许发送传输延迟时间：{delay}分"
    return tpv_str

def prase_err_code_result(errcode):
    if errcode == 0x00:
        err_str = "正确"
    elif errcode == 0x01:
        err_str= "中继命令没有返回"
    elif errcode == 0x02:
        err_str = "设置内容非法"
    elif errcode == 0x03:
        err_str = "密码权限不足"
    elif errcode == 0x04:
        err_str = "无此数据项"
    elif errcode == 0x05:
        err_str = "命令时间失效"
    elif errcode == 0x06:
        err_str = "目标地址不存在"
    elif errcode == 0x07:
        err_str = "校验失败"
    else:
        err_str = "未知错误"
    
    return err_str

def prase_DA_data(DA):
    point_str = ""
    total_measurement_points, measurement_points_array = calculate_measurement_points(DA)
    if measurement_points_array[0] == 0 and total_measurement_points == 1:
        point_str = "Pn=测量点：0(终端)"
    elif measurement_points_array[0] == 0xffff and total_measurement_points == 1:
        point_str = "Pn=测量点：FFFF(除了终端信息点以外的所有测量点)"
    else:
        formatted_string = ', '.join(map(str, measurement_points_array))
        point_str = "Pn=第" + formatted_string + "测量点"
    return point_str

def recaculate_sub_length(data_item_elem, data_segment):
    sub_length_cont = data_item_elem.find('length').text
    if sub_length_cont.upper() in "UNKNOWN":
        prase_data = PraseFrameData()
        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment)
    else:
        sub_length = int(sub_length_cont)
        if data_item_elem.get("protocol") and data_item_elem.get("region"):
            #块数据
            if data_item_elem.find('.//dataItem[@id="费率数"]'):
                data_item_count = len(data_item_elem.findall("dataItem"))
                length = (sub_length - 1)/ (data_item_count - 1)
                sub_length = (data_segment[0] + 1) * length + 1
                sub_length = int(sub_length)
    return sub_length,data_segment[:sub_length]

def try_get_item_and_point(item, DA):
    data_item = frame_fun.get_data_str_reverser(item)
    data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
    return data_item_elem,data_item

def get_data_dinsty(dinsty):
    dinsty_str = ""
    if dinsty == 0:
        dinsty_str = "按终端实际存储数据的时间间隔"
    elif dinsty == 1:
        dinsty_str = "1分钟"
    elif dinsty == 2:
        dinsty_str = "5分钟"
    elif dinsty == 3:
        dinsty_str = "15分钟"
    elif dinsty == 4:
        dinsty_str = "30分钟"
    elif dinsty == 5:
        dinsty_str = "60分钟"
    elif dinsty == 6:
        dinsty_str = "1日"
    elif dinsty == 7:
        dinsty_str = "1月"
    else:
        dinsty_str = "备用"
    return dinsty_str

def Analysic_csg_custom_head_frame(frame, result_list, start_pos):
    try:
        dir = frame[2]
        receive_time = frame[5:9]
        head_point_start = frame[15]
        head_point_end = frame[20:22]
        head_point_port = frame[24:26]
        ip = frame[26:30][::-1]
        port = frame[30:32]
        regesit_addr = frame[32:44]
        logic_addr = frame[44:57]
        regsit_time = frame[58:62]
        process_label = frame[75]
        begin_time = frame[76:80]

        timestamp = frame_fun.hex_array_to_int(receive_time, False)
        dt_object = datetime.fromtimestamp(timestamp)
        # 将datetime对象格式化为可读字符串
        receive_time_str = f"接收时间[{dt_object.strftime('%Y-%m-%d %H:%M:%S')}]"
        head_point_str = f"前置节点[{head_point_start}:{frame_fun.hex_array_to_int(head_point_end, False)}]"
        head_point_port_str = f"前置端口号[{frame_fun.hex_array_to_int(head_point_port, False)}]"
        ip_str = f"终端IP[{frame_fun.prase_ip_str(ip)}:{frame_fun.prase_port(port)}]"
        regesit_addr_str = f"注册地址[{frame_fun.ascii_to_str(regesit_addr)}]"
        logic_addr_str = f"逻辑地址[{frame_fun.ascii_to_str(logic_addr)}]"

        timestamp = frame_fun.hex_array_to_int(regsit_time, False)
        dt_object = datetime.fromtimestamp(timestamp)
        regsit_time_str = f"注册时间[{dt_object.strftime('%Y-%m-%d %H:%M:%S')}]"
        process_label_str = f"处理标志[{'YES' if process_label == 1 else 'NO'}]"

        timestamp = frame_fun.hex_array_to_int(begin_time, False)
        if timestamp > 0:
            dt_object = datetime.fromtimestamp(timestamp)
            begin_time_str = f"开始时间[{dt_object.strftime('%Y-%m-%d %H:%M:%S')}]"
        else:
            begin_time_str = "开始时间[无]"

        if dir & 0x01:
            dir_str = "从终端接收报文"
        else:
            dir_str = "向终端接收报文"

        restlt_str = f"{dir_str}:{receive_time_str} {regsit_time_str} {head_point_str} {ip_str} {head_point_port_str} {regesit_addr_str} {logic_addr_str} {process_label_str} {begin_time_str}"

        print(restlt_str)

        frame_fun.add_data(result_list, "内部规约", frame_fun.get_data_str_with_space(frame[:48]), restlt_str,[start_pos,start_pos + 84])
    except Exception as e:
        print(e)
        CustomMessageBox("告警",'解析数据失败！')
        return

def Analysic_csg_ack_frame(frame, dir, prm, result_list,start_pos):
    data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []
    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = data_segment[-16:]
        pw_pos = [-18,-2]

    data_segment = data_segment[:length]
    pw = False

    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]
            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                sublength = data_item_elem.find('length')
                if sublength is not None:
                    sub_length = int(sublength.text)
                else:
                    sub_length = len(sub_datament[4:])
                sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                prase_data = PraseFrameData()
                alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,sub_datament, index + pos + 4)
                frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                sub_datament = data_segment[pos + 4:]
                sub_length = len(sub_datament)
                item_data = None
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            result_str = f"数据标识[{data_item}]数据内容："
            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识内容",frame_fun.get_data_str_with_space(sub_datament),result_str + frame_fun.get_data_str_reverser(sub_datament),[index + pos + 4, index + pos + 4 + sub_length], item_data)

            pos += (sub_length + 4)
            num += 1
            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data,None, None, False)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)
    

def Analysic_csg_link_frame(frame,dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]

    data_segment = valid_data_segment[:length]
    pw = False
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)
            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:
                    sub_length = 1
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    err_str = prase_err_code_result(sub_datament[0])
                else:
                    sub_length_cont = data_item_elem.find('length')
                    if sub_length_cont is not None:
                        sub_length = sub_length_cont.text
                        if sub_length.upper() in "UNKNOWN":
                            sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        else:
                            sub_length = int(sub_length)
                    else:
                        sub_length = len(data_segment[4:])

                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,sub_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    sub_length = 1
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    err_str = prase_err_code_result(sub_datament[0]);
                else:
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"
            if dir == 1 and prm == 0:
                result_str = "写参数返回结果：" + frame_fun.get_data_str_reverser(sub_datament) +  "-" + err_str
            else:
                result_str = f"数据标识[{data_item}]数据内容：" + frame_fun.get_data_str_reverser(sub_datament)
            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            if dir == 1 and prm == 0:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>ERR",frame_fun.get_data_str_with_space(sub_datament),result_str,[index + pos + 4, index + pos + 4 + sub_length], item_data)
            else:
                if len(item_data):
                    frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识内容",frame_fun.get_data_str_with_space(sub_datament),result_str,[index + pos + 4, index + pos + 4 + sub_length], item_data)

            pos += (sub_length + 4)
            num += 1
            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data, None, None, False)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break

    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)

def Analysic_csg_write_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]

    data_segment = valid_data_segment[:length]
    pw = False
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)
            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:
                    sub_length = 1
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    err_str = prase_err_code_result(sub_datament[0]);
                else:
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                    else:
                        sub_length = int(sub_length_cont)
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,sub_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    sub_length = 1
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    err_str = prase_err_code_result(sub_datament[0]);
                else:
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"
            if dir == 1 and prm == 0:
                result_str = "写参数返回结果：" + frame_fun.get_data_str_reverser(sub_datament) +  "-" + err_str
            else:
                result_str = f"数据标识[{data_item}]数据内容：" + frame_fun.get_data_str_reverser(sub_datament)
            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            if dir == 1 and prm == 0:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>ERR",frame_fun.get_data_str_with_space(sub_datament),result_str,[index + pos + 4, index + pos + 4 + sub_length], item_data)
            else:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识内容",frame_fun.get_data_str_with_space(sub_datament),result_str,[index + pos + 4, index + pos + 4 + sub_length], item_data)

            pos += (sub_length + 4)
            num += 1
            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)


def Analysic_csg_security_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item == "E0010182":
                dir = 1
                prm = 0
            if data_item_elem is not None:
                if dir == 1 and prm == 0:#上行回复
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    pw = guest_is_exit_pw(length,data_segment)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            if dir == 1 and prm == 0:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos + 4, index + pos + 4 + sub_length], item_data)
            pos += (sub_length + 4)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)


def Analysic_csg_read_cur_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:#上行回复
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)
                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    pw = guest_is_exit_pw(length,data_segment)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            if dir == 1 and prm == 0:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos + 4, index + pos + 4 + sub_length], item_data)
            pos += (sub_length + 4)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)



def Analysic_csg_read_history_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []
    fiirst = True
    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    data_item_elem = None
    sub_length = 0
    data_time = None
    prase_data = PraseFrameData()
    sub_pos = 0
    while pos < length:
        try:
            if guest_next_data_is_cur_item_data(data_item_elem, data_segment[pos:], data_time) == False:
                DA = data_segment[pos:pos + 2]
                item = data_segment[pos + 2: pos + 6]
                point_str = prase_DA_data(DA)
                data_item_elem,data_item = try_get_item_and_point(item, DA)
                if data_item_elem is not None:
                    name = data_item_elem.find('name').text
                    dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
                else:
                    dis_data_identifier = "数据标识编码：" + f"[{data_item}]"
                frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
                pos += 2
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
                pos += 4
                if frame_fun.globregion == "海南":
                    data_count = data_segment[pos]
                    identifier = "数据时间个数:" + f"{data_count:02d}"
                    frame_fun.add_data(sub_result, f"<第{num + 1}组>数据时间个数",frame_fun.get_data_str_with_space(data_segment[pos:pos+1]),identifier,[index + pos, index + pos + 1])
                    pos += 1

            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:#上行回复
                    sub_length = int(data_item_elem.find('length').text)
                    sub_datament = data_segment[pos:pos + sub_length]
                    sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)
                    alalysic_result = prase_data.parse_data_item(data_item_elem,new_datament, index + pos, False)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
            else:
                if dir == 1 and prm == 0:
                    sub_length = len(data_segment)
                    pw = guest_is_exit_pw(length,data_segment, data_item_elem, data_time, True)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0

            if dir == 1:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos, index + pos + sub_length + 6], item_data)
                data_time = data_segment[pos + sub_length:pos + sub_length + 6]
                time_str = frame_fun.parse_time_data(data_time, "CCYYMMDDhhmm", False)
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据时间",frame_fun.get_data_str_with_space(data_time),f"数据时间：" + time_str,[index + pos + sub_length,index + pos + sub_length + 6])
                pos += 6
            else:
                start_time = data_segment[pos:pos + 6]
                end_time = data_segment[pos + 6:pos + 12]
                data_dinsty = data_segment[pos + 12]
                start_time_str = frame_fun.parse_time_data(start_time, "CCYYMMDDhhmm", False)
                end_time_str = frame_fun.parse_time_data(end_time, "CCYYMMDDhhmm", False)
                data_dinsty_str = get_data_dinsty(data_dinsty)
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据起始时间",frame_fun.get_data_str_with_space(start_time),start_time_str,[index + pos, index + pos + 6])
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据结束时间",frame_fun.get_data_str_with_space(end_time),end_time_str,[index + pos + 6, index + pos + 12])
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据密度",f"{data_dinsty:02X}",f"数据间隔时间："+data_dinsty_str,[index + pos + 12, index + pos + 13])
                pos += 13
            pos += sub_length
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data, data_item_elem, data_time, True)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)


def Analysic_csg_read_param_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:#上行回复
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    pw = guest_is_exit_pw(length,data_segment)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            if dir == 1 and prm == 0:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos + 4, index + pos + 4 + sub_length], item_data)
            pos += (sub_length + 4)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)


def Analysic_csg_read_task_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + 9 + start_pos
    num = 0
    sub_result = []
    task_result = []
    pw = False
    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
        pw = True
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]

    if dir == 1:#上行回复
        DA = frame[16:18]
        item = frame[18: 22]
        point_str = prase_DA_data(DA)
        data_item_elem,data_item = try_get_item_and_point(item, DA)
        if data_item_elem is not None:
            name = data_item_elem.find('name').text
            task_name = f"{name}号： {data_item}"
        else:
            task_name = f"任务号：{data_item}"
        frame_fun.add_data(sub_result,f"信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [16,18])

        frame_fun.add_data(sub_result, f"数据标识编码DI",frame_fun.get_data_str_with_space(item),task_name,[18,22])
        task_kind = frame[22]
        frame_fun.add_data(task_result, f"数据结构方式",frame_fun.to_hex_string_with_space(task_kind),"自描述方式",[22,23])
        pncount = frame[23]

        item_count = frame[24]
        frame_fun.add_data(task_result, f"数据组数",frame_fun.to_hex_string_with_space(frame[23:25]),f"信息点标识数{pncount},数据标识编码数{item_count},共有{pncount * item_count}个数据组数",[23,25])
        data_segment = valid_data_segment[9:]
        length -= 9
    else:
        data_segment = valid_data_segment
    data_item_elem = None
    data_time=None
    prase_data = PraseFrameData()
    while pos < length:
        try:
            if guest_next_data_is_cur_item_data(data_item_elem, data_segment[pos:], data_time) == False:
                DA = data_segment[pos:pos + 2]
                item = data_segment[pos + 2: pos + 6]
                data_item_elem,data_item = try_get_item_and_point(item, DA)
                point_str = prase_DA_data(DA)
                if data_item_elem is not None:
                    name = data_item_elem.find('name').text
                    dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
                else:
                    dis_data_identifier = "数据标识编码：" + f"[{data_item}]"
                if dir == 1:#上行回复
                    frame_fun.add_data(task_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
                    pos += 2
                    frame_fun.add_data(task_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
                    pos += 4
                else:
                    frame_fun.add_data(sub_result,f"信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
                    pos += 2
                    frame_fun.add_data(sub_result, f"数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
                    pos += 4

            item_data = []
            if data_item_elem is not None:
                if dir == 1:#上行回复
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos:])
                        sub_datament = data_segment[pos:pos + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos:pos + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)
                    alalysic_result = prase_data.parse_data_item(data_item_elem,new_datament, index + pos, False)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
            else:
                CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                break

            if dir == 1:
                frame_fun.add_data(task_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos, index + pos + sub_length], item_data)
                data_time = data_segment[pos + sub_length:pos + sub_length + 5]
                time_str = frame_fun.parse_time_data(data_time, "YYMMDDhhmm", False)
                frame_fun.add_data(task_result, f"<第{num + 1}组>数据时间",frame_fun.get_data_str_with_space(data_time),f"数据时间：" + time_str,[index + pos + sub_length,index + pos + sub_length + 5])
                pos += 5
            else:
                start_time = data_segment[pos:pos + 6]
                end_time = data_segment[pos + 6:pos + 12]
                data_dinsty = data_segment[pos + 12]
                start_time_str = frame_fun.parse_time_data(start_time, "CCYYMMDDhhmm", False)
                end_time_str = frame_fun.parse_time_data(end_time, "CCYYMMDDhhmm", False)
                data_dinsty_str = get_data_dinsty(data_dinsty)
                frame_fun.add_data(sub_result, f"数据起始时间",frame_fun.get_data_str_with_space(start_time),start_time_str,[index + pos, index + pos + 6])
                frame_fun.add_data(sub_result, f"数据结束时间",frame_fun.get_data_str_with_space(end_time),end_time_str,[index + pos + 6, index + pos + 12])
                frame_fun.add_data(sub_result, f"数据密度",f"{data_dinsty:02X}",f"数据间隔时间："+data_dinsty_str,[index + pos + 12, index + pos + 13])
                pos += 13
            pos += sub_length
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data, data_item_elem, data_time, True)
                if pw:
                    length -= 16

            if dir == 1:
                if num >= item_count * pncount:
                    break
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    
    if dir == 1:
        frame_fun.add_data(sub_result, "任务数据内容", frame_fun.get_data_str_with_space(frame[22:-2]), f"{task_name}数据内容", [22,-2],task_result)
        if pw:
            length -= 16;
        if length - pos == 6:
            data_time = data_segment[pos:pos + 6]
            time_str = frame_fun.parse_time_data(data_time, "CCYYMMDDhhmm", False)
            frame_fun.add_data(sub_result, f"任务数据时间",frame_fun.get_data_str_with_space(data_time),time_str,[index + pos,index + pos + 6])
        
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)

def Analysic_csg_read_alarm_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1:#上行回复
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1:
                    pw = guest_is_exit_pw(length,data_segment)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            pos += 4
            if dir == 1:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(new_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos, index + pos + sub_length], item_data)
            else:
                start_time = data_segment[pos:pos + 6]
                end_time = data_segment[pos + 6:pos + 12]
                start_time_str = frame_fun.parse_time_data(start_time, "CCYYMMDDhhmm", False)
                end_time_str = frame_fun.parse_time_data(end_time, "CCYYMMDDhhmm", False)
                frame_fun.add_data(sub_result, f"数据起始时间",frame_fun.get_data_str_with_space(start_time),start_time_str,[index + pos, index + pos + 6])
                frame_fun.add_data(sub_result, f"数据结束时间",frame_fun.get_data_str_with_space(end_time),end_time_str,[index + pos + 6, index + pos + 12])
                pos += 12
            pos += (sub_length)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)

def Analysic_csg_read_event_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:#上行回复
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                else:
                    sub_length = 0#下行读取报文
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    pw = guest_is_exit_pw(length,data_segment)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            pos += 4
            if dir == 1 and prm == 0:
                frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos, index + pos + sub_length], item_data)
            else:
                start_time = data_segment[pos:pos + 6]
                end_time = data_segment[pos + 6:pos + 12]
                start_time_str = frame_fun.parse_time_data(start_time, "CCYYMMDDhhmm", False)
                end_time_str = frame_fun.parse_time_data(end_time, "CCYYMMDDhhmm", False)
                frame_fun.add_data(sub_result, f"数据起始时间",frame_fun.get_data_str_with_space(start_time),start_time_str,[index + pos, index + pos + 6])
                frame_fun.add_data(sub_result, f"数据结束时间",frame_fun.get_data_str_with_space(end_time),end_time_str,[index + pos + 6, index + pos + 12])
                pos += 12
            pos += (sub_length)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)

def Analysic_csg_relay_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [-23,-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [-18,-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                if dir == 1 and prm == 0:#上行回复
                    frame_result = []
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                    sub_length, frame_len = prase_data.get_sub_length(data_segment[pos+5:],data_item_elem,"中继报文长度")
                    replay_type = prase_data.get_relay_type(data_segment[pos +4])
                    frame_fun.add_data(item_data, "中继类型",frame_fun.get_data_str_with_space(data_segment[pos +4:pos + 5]), f"中继类型:{replay_type}", [index +pos +4,index+pos + 5])
                    frame_fun.add_data(item_data, "中继应答长度",frame_fun.get_data_str_with_space(data_segment[pos +5:pos + 5 +sub_length]), f"中继应答长度{frame_len}", [index +pos +5,index+pos + 5 +sub_length])
                    FRAME_645.Analysis_645_fram_by_afn(data_segment[pos + 5 + sub_length:pos + 5 + frame_len + sub_length],frame_result,pos + 5 + sub_length  + index)
                    frame_fun.add_data(item_data, "中继应答内容",frame_fun.get_data_str_with_space(data_segment[pos + 5 + sub_length:pos + 5 + frame_len]), f"中继应答内容", [index + pos + 5 + sub_length,index+pos + 5 + frame_len],frame_result)
                    sub_length += frame_len
                    sub_length+=1
                    sub_datament = data_segment[pos + 4:pos + 4+sub_length]
                else:
                    sub_length_cont = data_item_elem.find('length').text
                    if sub_length_cont.upper() in "UNKNOWN":
                        sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        new_datament = sub_datament
                    else:
                        sub_length = int(sub_length_cont)
                        sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                        sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                    alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                    frame_fun.prase_data_with_config(alalysic_result, False,item_data)
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                pw = guest_is_exit_pw(length,data_segment)
                CustomMessageBox("警告",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                break

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos + 4, index + pos + 4 + sub_length], item_data)
            pos += (sub_length + 4)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[-7, -2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [16,-2],sub_result)

def Analysic_csg_topo_frame(frame, dir, prm,result_list,start_pos):
    valid_data_segment = frame[16:-2]
    tpv = get_afn_and_seq_result(frame[14:16], start_pos + 14,result_list)
    length = len(valid_data_segment)
    pos = 0
    index = 16 + start_pos
    num = 0
    sub_result = []

    if tpv:
        tpv_data = frame[-7:-2]
        pw_data = valid_data_segment[-21:-5]
        length -= 5
        pw_pos = [start_pos + len(frame)-23,start_pos + len(frame)-7]
    else:
        pw_data = valid_data_segment[-16:]
        pw_pos = [start_pos + len(frame)-18,start_pos + len(frame)-2]
    pw =False

    data_segment = valid_data_segment[:length]
    prase_data = PraseFrameData()
    while pos < length:
        try:
            DA = data_segment[pos:pos + 2]
            item = data_segment[pos + 2: pos + 6]

            point_str = prase_DA_data(DA)

            data_item = frame_fun.get_data_str_reverser(item)

            frame_fun.add_data(sub_result,f"<第{num + 1}组>信息点标识DA", frame_fun.get_data_str_with_space(DA), point_str, [index + pos, index + pos + 2])
            pos += 2

            data_item_elem = frame_fun.get_config_xml(data_item, frame_fun.globalprotocol, frame_fun.globregion)
            item_data = []
            if data_item_elem is not None:
                sub_length_cont = data_item_elem.find('length').text
                if sub_length_cont.upper() in "UNKNOWN":
                    sub_length = prase_data.caculate_item_length(data_item_elem, data_segment[pos + 4:])
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    new_datament = sub_datament
                else:
                    sub_length = int(sub_length_cont)
                    sub_datament = data_segment[pos + 4:pos + 4 + sub_length]
                    sub_length, new_datament = recaculate_sub_length(data_item_elem, sub_datament)

                alalysic_result = prase_data.parse_data(data_item,frame_fun.globalprotocol, frame_fun.globregion,new_datament, index + pos + 4)
                # print(alalysic_result)
                frame_fun.prase_data_with_config(alalysic_result, False, item_data)
                # else:
                #     sub_length = 0#下行读取报文
                name = data_item_elem.find('name').text
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name
            else:
                if dir == 1 and prm == 0:
                    pw = guest_is_exit_pw(length,data_segment)
                    CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
                    break
                else:
                    sub_length = 0
                dis_data_identifier = "数据标识编码：" + f"[{data_item}]"

            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据标识编码DI",frame_fun.get_data_str_with_space(item),dis_data_identifier,[index + pos, index + pos + 4])
            frame_fun.add_data(sub_result, f"<第{num + 1}组>数据内容",frame_fun.get_data_str_with_space(sub_datament),point_str[len("Pn="):] + "-" + dis_data_identifier[len("数据标识编码："):],[index + pos + 4, index + pos + 4 + sub_length], item_data)
            pos += (sub_length + 4)
            num += 1

            if length - pos == 16:
                pw  = guest_is_exit_pw(length, pw_data)
                if pw:
                    length -= 16
        except Exception as e:
            CustomMessageBox("告警",'解析数据失败！')
            break
    if pw:
        pw_str = "PW由16个字节组成，是由主站按系统约定的认证算法产生，并在主站发送的报文中下发给终端，由终端进行校验认证。"
        frame_fun.add_data(sub_result, f"消息验证码Pw",frame_fun.get_data_str_with_space(pw_data),pw_str,pw_pos)
    if tpv:
        tpv_str = prase_tpv_data(tpv_data)
        frame_fun.add_data(sub_result, f"时间标签Tp",frame_fun.get_data_str_with_space(tpv_data),tpv_str,[start_pos + len(frame)-7, start_pos + len(frame)-2])
    frame_fun.add_data(result_list, "信息体", frame_fun.get_data_str_with_space(frame[16:-2]), "", [index, start_pos + len(frame)-2],sub_result)