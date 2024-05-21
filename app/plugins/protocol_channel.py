from ..plugins.signalCommunication import SerialPortThread,MQTTClientThread,TcpClient,ClientWorker,MqttMessageDetails
from PyQt5.QtCore import QObject,pyqtSlot,pyqtSignal,QTimer,QThread
from .frame_fun import FrameFun as frame_fun
import binascii,threading,queue
from .frame_csg import *
import asyncio

class AsyncWorker(QThread):
    finished = pyqtSignal(object)  # Signal to emit when the task is finished

    def __init__(self, channel, data, parent=None):
        super().__init__(parent)
        self._future = None
        self.channel = channel
        self.data = data
        self.init_slot()

    def init_slot(self):
        if self.channel is not None:
            if isinstance(self.channel, SerialPortThread):
                self.channel.data_received.connect(self.receive_message_process)
            if isinstance(self.channel, TcpClient):
                self.channel.data_received.connect(self.receive_message_process)
            if isinstance(self.channel, ClientWorker):
                self.channel.receive_data.connect(self.receive_message_process)

    def run(self):
        # Run the asynchronous operation in the thread's event loop
        asyncio.get_event_loop().run_until_complete(self._async_operation())
        self.finished.emit(self.result)

    async def _async_operation(self):
        # Placeholder for your asynchronous operation
        self.result = await self.some_async_function()

    def start(self):
        super().start()

    def wait(self):
        self.finished.connect(lambda result: self.quit())
        self.wait()
        return self.result
    
    async def some_async_function(self):
        self.send_message(self.channel, "HEX", self.data)
        return await self.receive_message_process()

        
    def get_modify_text(self, type, input_text:str):
        if type == 'ASCII':
            return input_text
        formatted_frame = ''
        hex_str = input_text.replace(' ', '').replace('\n', '')
        for i in range(0, len(hex_str), 2):
            formatted_frame += hex_str[i:i + 2] + ' '
        return formatted_frame.upper()
    def is_valid_hex_string(self, input_string):
        try:
            bytes.fromhex(input_string)
            return True
        except ValueError:
            return False    
    def get_message_by_type(self, type, text):
        try:
            formatted_frame = self.get_modify_text(type, text)
            if type== 'HEX':
                if self.is_valid_hex_string(text):
                    send_data = bytes.fromhex(text)
                    return send_data,formatted_frame
            elif type== 'ASCII':
                if isinstance(text, bytes):
                    send_data = text,text
                elif isinstance(text, str):
                    hex_message = binascii.hexlify(text.encode('ascii')).decode('ascii')
                    if self.is_valid_hex_string(hex_message):
                        send_data = bytes.fromhex(hex_message)
                        return send_data,text
                    
            return None,None
        except Exception as e:
            print(e)
            return None,None 
    async def send_message(self, channel, type, text):
        message, formatted_frame = self.get_message_by_type(type, text)
        if message is None:
            return
        print("send_message", message, formatted_frame)
        if isinstance(channel, SerialPortThread):
            channel.data_sended.emit(message)
        if isinstance(channel, TcpClient):
            channel.data_sended.emit(message)
        if isinstance(channel, ClientWorker):
            channel.data_sended.emit(message)

    async def receive_message_process(self, data):
        print("receive_message_process", data)

class CsgProtocolChannel(QObject):
    done = pyqtSignal(bytes)
    def __init__(self, channel, timeout, parent=None):
        super().__init__()
        self.channel = channel
        self.timeout = timeout
        self.received_data = None
        self.init_slot()

    def init_slot(self):
        if self.channel is not None:
            if isinstance(self.channel, SerialPortThread):
                self.channel.data_received.connect(self.receive_message_process)
            if isinstance(self.channel, TcpClient):
                self.channel.data_received.connect(self.receive_message_process)
            if isinstance(self.channel, ClientWorker):
                self.channel.receive_data.connect(self.receive_message_process)

    async def send_data_and_wait_for_reply(self, send_list, timeout=10):
        # 发送数据
        for data in send_list:
            await self.send_message(self.channel, "HEX", data)
        # 等待回复
        try:
            return await asyncio.wait_for(self.receive_message_process(), timeout=timeout)
        except asyncio.TimeoutError:
            print("Timeout occurred")
            return None
        
    def get_modify_text(self, type, input_text:str):
        if type == 'ASCII':
            return input_text
        formatted_frame = ''
        hex_str = input_text.replace(' ', '').replace('\n', '')
        for i in range(0, len(hex_str), 2):
            formatted_frame += hex_str[i:i + 2] + ' '
        return formatted_frame.upper()
    def is_valid_hex_string(self, input_string):
        try:
            bytes.fromhex(input_string)
            return True
        except ValueError:
            return False    
    def get_message_by_type(self, type, text):
        try:
            formatted_frame = self.get_modify_text(type, text)
            if type== 'HEX':
                if self.is_valid_hex_string(text):
                    send_data = bytes.fromhex(text)
                    return send_data,formatted_frame
            elif type== 'ASCII':
                if isinstance(text, bytes):
                    send_data = text,text
                elif isinstance(text, str):
                    hex_message = binascii.hexlify(text.encode('ascii')).decode('ascii')
                    if self.is_valid_hex_string(hex_message):
                        send_data = bytes.fromhex(hex_message)
                        return send_data,text
                    
            return None,None
        except Exception as e:
            print(e)
            return None,None 
    def send_message(self, type, text):
        message, formatted_frame = self.get_message_by_type(type, text)
        if message is None:
            return
        print("send_message", message, formatted_frame)
        channel = self.channel
        if isinstance(channel, SerialPortThread):
            channel.data_sended.emit(message)
        if isinstance(channel, TcpClient):
            channel.data_sended.emit(message)
        if isinstance(channel, ClientWorker):
            channel.data_sended.emit(message)

    def receive_message_process(self, data):
        print("receive_message_process", data)
        self.done.emit(data)
                

class SendReceiveThread(QThread):
    def __init__(self, channel, timeout=5000):
        super().__init__()
        self.worker = CsgProtocolChannel(channel, timeout)
        self.worker.moveToThread(self)
        self.worker.done.connect(self.on_done)

    def send_and_receive(self, message):
        self.start()
        self.worker.send_message("HEX", message)

    def on_done(self, message):
        print("on_done", message)
        self.exit()

    def run(self):
        self.exec_()  # 开始事件循环