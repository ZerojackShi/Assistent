from .frame_fun import FrameFun as frame_fun
from ..plugins.protocol import PraseFrameData
from ..plugins.frame_fun import CustomMessageBox
from ..common.config import ProtocolInfo,ConfigManager
FRAME_START = 0x68
FRAME_END = 0x16

class FrameCCO(object):
    def __init__(self):
        pass

    @classmethod
    def is_cco_frame(cls, frame):
        if frame[0] != FRAME_START or frame[-1] != FRAME_END:
            return False
        
        length = frame_fun.bintodecimal(frame[1:3])
        if length != len(frame):
            return False
        
        return True
    
    @classmethod
    def get_control_code_str(cls, control_data, control_result, index=0):
        binary_array = []
        frame_fun.get_bit_array(control_data, binary_array)
        dir = binary_array[0]
        prm = binary_array[1] 
        add = binary_array[2]
        ver = control_data & 0x0c
        keep = control_data & 0x03
        dir_str = "下行报文" if dir == 0 else "上行报文"
        prm_str = "表示此帧报文来自启动站" if prm ==1 else "表示此帧报文来自从动站"
        add_str = "表示此帧报文带地址域" if add == 1 else "表示此帧报文不带地址域"
        ver_str = f"协议版本号:{ver}"

        frame_fun.add_data(control_result, "传输方向位DIR", str(dir), dir_str, [index + 0, index + 1]) 
        frame_fun.add_data(control_result, "启动标志位PRM", str(prm), prm_str, [index + 0, index + 1]) 
        frame_fun.add_data(control_result, "地址域标志位ADD", str(add), add_str, [index + 0, index + 1])
        frame_fun.add_data(control_result, "协议版本号VER", str(ver), ver_str, [index + 0, index + 1])
        frame_fun.add_data(control_result, "保留位", str(keep), f"保留位={keep}", [index + 0, index + 1])

        return dir, prm, add, ver
    @classmethod
    def get_user_data_result(cls, adress_area, add, result_list, index=0):
        source_adress = adress_area[0:6]
        target_adress = adress_area[6:12]

        frame_fun.add_data(result_list, "源地址 ASR", frame_fun.get_data_str_with_space(source_adress), f"源地址:{frame_fun.get_data_str_reverser(source_adress)}", [index + 0, index + 6])
        frame_fun.add_data(result_list, "目的地址 ADST", frame_fun.get_data_str_with_space(target_adress), f"目的地址:{frame_fun.get_data_str_reverser(target_adress)}", [index + 6, index + 12])
      
    @classmethod
    def get_afn_info(cls, dir_type, prm, afn):
        if dir_type == 0xE8:
            if afn == 0x00:
                return "确认/否认"
            if afn == 0x01:
                return "初始化模块"
            if afn == 0x02:
                return "管理任务"
            if afn == 0x03:
                return "读参数"
            if afn == 0x04:
                return "写参数"
            if afn == 0x05:
                return "上报信息"
            if afn == 0x06:
                return "请求信息"
            if afn == 0x07:
                return "传输文件"
            if afn == 0x10:
                return "维护命令"
            if afn == 0xF0:
                return "维护模块"
            return "未知"
        else:
            if afn == 0x00:
                return "确认/否认"
            if afn == 0x21:
                return "管理电表"
            if afn == 0x22:
                return "转发数据"
            if afn == 0x23:
                return "读参数"
            if afn == 0x24:
                return "传输文件"
            if afn == 0x25:
                return "请求信息"
            if afn == 0x31:
                return "管理映射表表计"
            return "未知"
         

    @classmethod
    def Analysis_cco_frame_by_afn(cls, frame:list, result_list, index=0):
        dir, prm, add, afn, pos, user_result = cls.Analysic_cco_head_frame(frame,result_list,index)
        
        app_data = frame[pos:-2]
        app_data_result = []
        cls.Analysic_cco_appdata_frame(app_data, app_data_result, dir, index + pos)
        frame_fun.add_data(user_result,"应用数据域", frame_fun.get_data_str_with_space(app_data), f"应用数据:{frame_fun.get_data_str_reverser(app_data)}",[index + pos, index + pos + len(app_data)],app_data_result)
        frame_fun.add_data(result_list,"用户数据域", frame_fun.get_data_str_with_space(frame[4:-2]), f"用户数据:{frame_fun.get_data_str_reverser(frame[4:-2])}",[index + 4, index + len(frame) -2],user_result)
        cls.Analysic_cco_end_frame(frame, result_list, dir, index)
    
    @classmethod
    def Analysic_cco_head_frame(cls, frame:list, result_list, index=0):
        pos = 0
        start = frame[0]
        len_data = frame[1:3]
        length = frame_fun.bintodecimal(len_data)
        control_data = frame[3]

        pos = 4

        frame_fun.add_data(result_list, "起始符", f"{start:02X}", "起始符",[index + 0, index + 1])
        frame_fun.add_data(result_list,"长度", frame_fun.get_data_str_with_space(len_data), f"总长度={length}",[index + 1, index + 3])

        contro_result = []
        dir, prm, add, ver = cls.get_control_code_str(control_data,contro_result, index + 3)
        frame_fun.add_data(result_list,"控制域C", f"{control_data:02X}", f"控制域:{control_data:02X}",[index + 3, index + 4],contro_result)
        
        user_result = []
        if add:       
            adress_arearesult = []
            adress_area = frame[pos:pos + 12]
            cls.get_user_data_result(adress_area, add, adress_arearesult, index + 4)
            frame_fun.add_data(user_result,"地址域A", frame_fun.get_data_str_with_space(adress_area), f"地址域:{frame_fun.get_data_str_reverser(adress_area)}",[index + pos, index + pos + 12],adress_arearesult)
            pos += 12

        afn = frame[pos]
        dir_type = frame[pos + 5]
        afn_str = cls.get_afn_info(dir_type, prm, afn)
        frame_fun.add_data(user_result,"应用功能码 AFN", f"{afn:02X}", f"AFN:{afn:02X}-{afn_str}",[index + pos, index + pos + 1])
        pos += 1
        seq = frame[pos]
        frame_fun.add_data(user_result,"帧序列域 SEQ", f"{seq:02X}", f"帧序列SEQ:{seq}",[index + pos, index + pos + 1])
        pos += 1
        return dir, prm, add, afn, pos, user_result
    
    @classmethod
    def get_direction_str(cls, dir):
        map = {
            0x00: "上下行均用，但下行无数据内容",
            0x01: "上下行均用，数据内容格式一致",
            0x02: "仅下行用，上行为确认/否认报文",
            0x03: "仅下行用，带数据内容。对应上行报文为 04",
            0x04: "仅上行用，带数据内容。对应下行报文为 03",
            0x05: "示仅上行用，下行为确认/否认报文",
            0x06: "上下行均用，但上行无数据内容",
        }
        return map.get(dir, "未知")
    
    @classmethod
    def Analysic_cco_di_data(cls, di, result, index=0):
        di0 = di[0]
        di1 = di[1]
        di2 = di[2]
        di3 = di[3]
        di0_str = "功能码子类型"
        di1_str = "功能码类型定义,与AFN值保持一致：" + cls.get_afn_info(di3, 1, di1)
        di2_str = "报文上下行类型" + cls.get_direction_str(di2)
        di3_str = f"通信双方类型标识:{di3:02X}-" + "集中器与本地模块通信" if di3 == 0XE8 else "采集器与本地模块通信"

        frame_fun.add_data(result, "DI0", f"{di0:02X}", di0_str, [index + 0, index + 1])
        frame_fun.add_data(result, "DI1", f"{di1:02X}", di1_str, [index + 1, index + 2])
        frame_fun.add_data(result, "DI2", f"{di2:02X}", di2_str, [index + 2, index + 3])
        frame_fun.add_data(result, "DI3", f"{di3:02X}", di3_str, [index + 3, index + 4])

    @classmethod
    def Analysic_cco_appdata_frame(cls, data_content, result, dir, index=0):
        di = data_content[0:4]

        diresult = []
        cls.Analysic_cco_di_data(di, diresult, index)

        didata = data_content[4:]
        prase_data = PraseFrameData()
        data_item = frame_fun.get_data_str_reverser(di)
        data_item_elem = ConfigManager.get_config_xml(data_item, ProtocolInfo.PROTOCOL_CSG16.name(), frame_fun.globregion)
        pos = 0
        item_data = []
        if data_item_elem is not None:
            sub_length_cont = data_item_elem.find('length').text
            if sub_length_cont.upper() in "UNKNOWN":
                sub_length = prase_data.caculate_item_length(data_item_elem, didata, ProtocolInfo.PROTOCOL_CSG16.name())
            else:
                sub_length = int(sub_length_cont)
            sub_datament = didata[pos:pos + sub_length]
            alalysic_result = prase_data.parse_data(data_item,ProtocolInfo.PROTOCOL_CSG16.name(), frame_fun.globregion,sub_datament, index + pos + 4)
            frame_fun.prase_data_with_config(alalysic_result, False, item_data)
            name = data_item_elem.find('name').text
            dis_data_identifier = "数据标识编码：" + f"[{data_item}]" + "-" + name

            frame_fun.add_data(result, "数据标识编码", frame_fun.get_data_str_with_space(di), dis_data_identifier, [index + 0, index + 4], diresult)
            frame_fun.add_data(result, "数据标识内容", frame_fun.get_data_str_with_space(sub_datament), f"数据内容：{frame_fun.get_data_str_reverser(sub_datament)}",[index + 4, index + 4 + sub_length],item_data)
        else:
            CustomMessageBox("告警",'未查找到数据标识：'+ data_item + '请检查配置文件！')
            pass


    @classmethod
    def Analysic_cco_end_frame(cls, data_content, result, dir, index=0):
        crc16 = data_content[3:-2]
        calcrc = frame_fun.caculate_cs(crc16)
        orignal_crc = data_content[-2]
        cs_str = f"正确" if calcrc == orignal_crc else f"错误，应为：{calcrc:02X}"
        crc_str = f"校验和:{cs_str}"
        frame_fun.add_data(result,"校验和CS", f"{orignal_crc:02X}", crc_str, [index + len(data_content)-2, index + len(data_content)-1])
        frame_fun.add_data(result, "结束符", f"{data_content[-1]:02X}","结束符",[index + len(data_content)-1, index + len(data_content)])
    