
from .frame_fun import FrameFun
from .frame_fun import CustomMessageBox
from ..common.config import oad_finder

MS_TYPE_ALL_USER                      = 0x01  #全部用户类型*/
MS_TYPE_A_SET_OF_USER                 = 0x02  #一组用户类型 */
MS_TYPE_A_SET_OF_ADDRESSES            = 0x03  #一组用户地址*/
MS_TYPE_A_SET_OF_NUMBERS              = 0x04  #一组配置序号*/
MS_TYPE_A_RANGE_OF_USER_TYPES         = 0x05  #一组用户类型区间*/
MS_TYPE_A_SET_OF_USER_ADDRESS_RANGES  = 0x06  #一组用户地址区间*/
MS_TYPE_A_SET_OF_NUMBER_RANGES        = 0x07  #一组配置序号区间*/
MS_TYPE_ALL_USER_WITHOUT_JC           = 0xF7  #除交采外的所有表 247*/
MS_TYPE_A_SET_OF_VIP_USER_BY_PORT     = 0xF8  #一组用户类型区分端口*/
MS_TYPE_A_SET_OF_USER_BY_PORT         = 0xF9  #一组用户类型区分端口*/
MS_TYPE_A_GROUP_OF_VIP_USER_TYPES     = 0xFB  #一组重点用户类型 251*/
MS_TYPE_A_SET_OF_USER_EVENT_LEVELS    = 0xFC  #一组用户事件等级 252*/
MS_TYPE_VIP_USER_TYPES                = 0xFD  #重点用户 253*/
MS_TYPE_A_SET_OF_USER_PORT_NUMBERS    = 0xFE  #一组用户端口号 254*/
    
class MeterTask:
    def is_meter_task(self, task_content:bytes):
        if len(task_content) <= 26:
            return False
        if (task_content[0] == 0x01 
            and task_content[4] == 0x51 
            and task_content[9] == 0x51 
            and task_content[14] == 0x51 
            and task_content[25]==0x5c):
            return True
        return False

    def get_oad(self, task_content:bytes):
        master_oad = FrameFun.cosem_bin2_int32u(task_content[0:4])
        return master_oad, 4
    
    def get_master_oad_info(self, master_oad:int):
        if master_oad == 0x00000000:
            return "当前数据"
        if master_oad == 0x50020200:
            return "分钟冻结"
        if master_oad == 0x50040200:
            return "日冻结"
        if master_oad == 0x50060200:  
            return "月冻结"
        
    def get_sub_oad_info(self, master_oad:int, sub_oad:int):
        result = oad_finder.find_oad_info(master_oad, sub_oad)
        if result is None:
            return None, ""
        item = result['item_07'] 
        item_set = f'{item:08x}'.upper()
        protocol = "DLT/645"
        if FrameFun.globregion is not None:
            region = FrameFun.globregion
        else:
            region = "南网"
        template_element = FrameFun.get_config_xml(item_set, protocol,region)
        if template_element is not None:
            name = template_element.find('name')
            if name is not None:
                return item_set, name.text
        
        return item_set, ""
    
    def check_item_is_in_plan(self, task_content, find_item):
        try:
            self.oad_count = task_content[1]
            if self.oad_count == 0:
                return
            pos = 2
            for i in range(self.oad_count):
                pos += 3
                master_oad, len = self.get_oad(task_content[pos:])
                pos += (len + 1)
                sub_oad, len = self.get_oad(task_content[pos:])
                item, info = self.get_sub_oad_info(master_oad, sub_oad)
                if item is not None:
                    print("master_oad",master_oad,"sub_oad",sub_oad, "item",item)
                    if item.upper() == f'{find_item:08x}'.upper():
                        return True
                pos += (len + 1)

                sub_oad, len = self.get_oad(task_content[pos:])
                pos += len
                pos += 6
                pos += 1
                ms_type = task_content[pos]
                pos += 1
                ms_data = []
                len, me_info = self.get_ms_len(ms_type, task_content[pos:], ms_data, pos)
                pos += len
                i += 1
            return False
        except Exception as e:
            return False
    

    def get_range_type(self, type):
        if type == 0:
            return "前闭后开"
        if type == 1:
            return "前开后闭"
        if type == 2:
            return "前闭后闭"
        if type == 3:
            return "前开后开"
        return "未知"
        
    def get_ms_len(self, ms_type:int, task_content:bytes, sub_result, start_pos):
        try:
            pos = 0
            if ms_type == MS_TYPE_ALL_USER:
                dis_data_identifier = "全部用户类型"
                return 0, dis_data_identifier
            if ms_type == MS_TYPE_A_SET_OF_USER:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    dis_data_identifier = f'用户类型:{task_content[pos]}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户类型",FrameFun.to_hex_string_with_space(task_content[pos:pos + 1]),dis_data_identifier,[start_pos + pos, start_pos + pos + 1])
                    pos += 1
                dis_data_identifier = f"用户类型个数:{task_content[0]}"
                FrameFun.add_data(sub_result, f"用户类型个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组用户类型"
                return pos, dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_ADDRESSES:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    pos += 1
                    len = task_content[pos] + 1
                    pos += 1
                    adress = FrameFun.get_data_str_order(task_content[pos:pos + len])
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户地址",FrameFun.to_hex_string_with_space(task_content[pos:pos+len]),adress,[start_pos + pos, start_pos + pos + len])
                    pos += len
                dis_data_identifier = f"用户地址个数:{task_content[0]}"
                FrameFun.add_data(sub_result, f"用户地址个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组用户地址"
                return pos,dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_NUMBERS:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    range_type = self.get_range_type(task_content[pos])
                    spot_id = FrameFun.cosem_bin2_int32u(task_content[pos: pos + 2])
                    dis_data_identifier = f'测量点号:{spot_id:04d}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>测量点号",FrameFun.to_hex_string_with_space(task_content[pos: pos + 2]),dis_data_identifier,[start_pos + pos, start_pos + pos + 2])
                    pos += 2
                dis_data_identifier = f"测量点个数:{task_content[0]:02d}"
                FrameFun.add_data(sub_result, f"测量点个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组配置序号"
                
                return pos, dis_data_identifier
        
            if ms_type == MS_TYPE_A_RANGE_OF_USER_TYPES:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    range_type = self.get_range_type(task_content[pos])
                    FrameFun.add_data(ms_result, f"<第{i+1}组>区间类型",FrameFun.to_hex_string_with_space(task_content[pos]),range_type,[start_pos + pos, start_pos + pos + 1])
                    pos += 2
                    user1 = f'用户类型:{task_content[pos]:02d}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户类型",FrameFun.to_hex_string_with_space(task_content[pos]),user1,[start_pos + pos, start_pos + pos + 1])
                    pos += 2
                    user2 = f'用户类型:{task_content[pos]:02d}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户类型",FrameFun.to_hex_string_with_space(task_content[pos]),user2,[start_pos + pos, start_pos + pos + 1])
                    pos += 1
                dis_data_identifier = f"区间个数:{task_content[0]:02d}"
                FrameFun.add_data(sub_result, f"区间个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组用户类型区间"                
                return pos, dis_data_identifier
        
            if ms_type == MS_TYPE_A_SET_OF_USER_ADDRESS_RANGES:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    range_type = self.get_range_type(task_content[pos])
                    FrameFun.add_data(ms_result, f"<第{i+1}组>区间类型",FrameFun.to_hex_string_with_space(task_content[pos]),range_type,[start_pos + pos, start_pos + pos + 1])
                    pos += 3
                    len = task_content[pos] + 1
                    pos += 1
                    adress = FrameFun.get_data_str_order(task_content[pos:pos + len])
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户地址",FrameFun.to_hex_string_with_space(task_content[pos:pos+len]),adress,[start_pos + pos, start_pos + pos + len])
                    pos += len
                    pos += 2
                    len = task_content[pos] + 1
                    pos += 1
                    adress = FrameFun.get_data_str_order(task_content[pos:pos + len])
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户地址",FrameFun.to_hex_string_with_space(task_content[pos:pos+len]),adress,[start_pos + pos, start_pos + pos + len])
                    pos += len

                dis_data_identifier = f"区间个数:{task_content[0]:02d}"
                FrameFun.add_data(sub_result, f"区间个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组用户地址区间"            
                return pos,dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_NUMBER_RANGES:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    range_type = self.get_range_type(task_content[pos])
                    FrameFun.add_data(ms_result, f"<第{i+1}组>区间类型",FrameFun.to_hex_string_with_space(task_content[pos]),range_type,[start_pos + pos, start_pos + pos + 1])
                    pos += 2
                    spot_id = FrameFun.cosem_bin2_int32u(task_content[pos: pos + 2])
                    dis_data_identifier = f'测量点号:{spot_id:04d}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>测量点号",FrameFun.to_hex_string_with_space(task_content[pos: pos + 2]),dis_data_identifier,[start_pos + pos, start_pos + pos + 2])
                    pos += 2
                    pos += 1
                    spot_id = FrameFun.cosem_bin2_int32u(task_content[pos: pos + 2])
                    dis_data_identifier = f'测量点号:{spot_id:04d}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>测量点号",FrameFun.to_hex_string_with_space(task_content[pos: pos + 2]),dis_data_identifier,[start_pos + pos, start_pos + pos + 2])
                    pos += 2
                dis_data_identifier = f"区间个数:{task_content[0]}"
                FrameFun.add_data(sub_result, f"区间个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组配置序号区间"                
                return pos,dis_data_identifier
            
            if ms_type == MS_TYPE_ALL_USER_WITHOUT_JC:
                dis_data_identifier = "除交采外所有表"
                return 0,dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_VIP_USER_BY_PORT:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    dis_data_identifier = f'用户类型:{task_content[pos]}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户类型",FrameFun.to_hex_string_with_space(task_content[pos:pos + 1]),dis_data_identifier,[start_pos + pos, start_pos + pos + 1])
                    pos += 1
                dis_data_identifier = f"用户类型个数:{task_content[0]}"
                FrameFun.add_data(sub_result, f"用户类型个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组重点用户类型区分端口(300<=任务号<=500:载波，其他：非载波)"
                return pos, dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_USER_BY_PORT:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    dis_data_identifier = f'用户类型:{task_content[pos]}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>用户类型",FrameFun.to_hex_string_with_space(task_content[pos:pos + 1]),dis_data_identifier,[start_pos + pos, start_pos + pos + 1])
                    pos += 1
                dis_data_identifier = f"用户类型个数:{task_content[0]}"
                FrameFun.add_data(sub_result, f"用户类型个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组用户类型区分端口(300<=任务号<=500:载波，其他：非载波)"
                return pos, dis_data_identifier
            
            if ms_type == MS_TYPE_A_GROUP_OF_VIP_USER_TYPES:
                dis_data_identifier = f"用户类型:{task_content[pos]:02d}"
                FrameFun.add_data(sub_result, f"用户类型",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos + pos, start_pos + pos + 1])
                pos += 1
                dis_data_identifier = "一组重点用户类型"
                return pos,dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_USER_EVENT_LEVELS:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    dis_data_identifier = f'事件等级:{task_content[pos]:02d}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>事件等级",FrameFun.to_hex_string_with_space(task_content[pos]),dis_data_identifier,[start_pos + pos, start_pos + pos + 1])
                    pos += 1
                dis_data_identifier = f"事件等级个数:{task_content[0]:02d}"
                FrameFun.add_data(sub_result, f"事件等级个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组用户事件等级"
                
                return pos,dis_data_identifier
            
            if ms_type == MS_TYPE_VIP_USER_TYPES:
                dis_data_identifier = "重点用户"
                return 0,dis_data_identifier
            
            if ms_type == MS_TYPE_A_SET_OF_USER_PORT_NUMBERS:
                pos += 1
                ms_result = []
                for i in range(task_content[0]):
                    dis_data_identifier = f'端口号:{task_content[pos]:02X}'
                    FrameFun.add_data(ms_result, f"<第{i+1}组>端口号",FrameFun.to_hex_string_with_space(task_content[pos]),dis_data_identifier,[start_pos + pos, start_pos + pos + 1])
                    pos += 1
                dis_data_identifier = f"端口号个数:{task_content[0]:02d}"
                FrameFun.add_data(sub_result, f"端口号个数",FrameFun.to_hex_string_with_space(task_content[0]),dis_data_identifier,[start_pos, start_pos + 1],ms_result)
                dis_data_identifier = "一组端口号"                
                return pos,dis_data_identifier
        except Exception as e:
            CustomMessageBox("告警",f'解析MS：{ms_type}失败！')
        return 0,""

    def analysic_meter_task(self, task_content:bytes, result_list, index):
        try:
            self.oad_count = task_content[1]
            if self.oad_count == 0:
                return
            pos = 1
            dis_data_identifier = f'采集数据项个数：{self.oad_count}'
            FrameFun.add_data(result_list, f"数据项个数",FrameFun.to_hex_string_with_space(self.oad_count),dis_data_identifier,[index + pos, index + pos + 1])
            pos = 2
            sub_result = []
            for i in range(self.oad_count):
                start_pos = pos
                sub_result = []
                pos += 3
                master_oad, len = self.get_oad(task_content[pos:])
                oad_info = self.get_master_oad_info(master_oad)
                dis_data_identifier = f'主数据项:{master_oad:08X}-{oad_info}'
                FrameFun.add_data(sub_result, f"主数据项",FrameFun.to_hex_string_with_space(task_content[pos: pos + len]),dis_data_identifier,[index + pos, index + pos + len])
                pos += (len + 1)
                sub_oad, len = self.get_oad(task_content[pos:])
                item, info = self.get_sub_oad_info(master_oad, sub_oad)
                if item is not None:
                    if info != '':
                        dis_data_identifier = f'分数据项:{sub_oad:08X}-{item}:{info}'
                    else:
                        dis_data_identifier = f'分数据项:{sub_oad:08X}-{item}'
                else:
                    dis_data_identifier = f'分数据项:{sub_oad:08X}'
                FrameFun.add_data(sub_result, f"分数据项",FrameFun.to_hex_string_with_space(task_content[pos: pos + len]),dis_data_identifier,[index + pos, index + pos + len])
                pos += (len + 1)

                sub_oad, len = self.get_oad(task_content[pos:])
                dis_data_identifier = f'分数据项:{sub_oad:08X}'
                FrameFun.add_data(sub_result, f"分数据项",FrameFun.to_hex_string_with_space(task_content[pos: pos + len]),dis_data_identifier,[index + pos, index + pos + len])
                pos += len
                pos += 6
                pos += 1
                ms_type = task_content[pos]
                pos += 1
                ms_data = []
                len, me_info = self.get_ms_len(ms_type, task_content[pos:], ms_data, pos + index)
                FrameFun.add_data(sub_result, f"MS",FrameFun.to_hex_string_with_space(ms_type),me_info,[index + pos - 1, index + pos])
                if len > 0:
                    dis_data_identifier = f'MS内容:'+ FrameFun.get_data_str_order(task_content[pos + index: pos + index + len])
                    FrameFun.add_data(sub_result, f"MS内容",FrameFun.to_hex_string_with_space(task_content[pos + index: pos + index + len]),dis_data_identifier,[pos + index, pos + index + len], ms_data)
                pos += len

                dis_data_identifier = f'<第{i + 1}组>数据采集:{master_oad:08X}'
                FrameFun.add_data(result_list, f"<第{i + 1}组>数据采集",FrameFun.to_hex_string_with_space(task_content[index + start_pos: index + pos]),dis_data_identifier,[index + start_pos, index + pos],sub_result)   
                i += 1
        except Exception as e:
            CustomMessageBox("告警",'解析任务失败！')