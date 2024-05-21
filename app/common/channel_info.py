from ..plugins.signalCommunication import SerialPortThread,MQTTClientThread,TcpClient,ClientWorker,MqttMessageDetails
import binascii
from .signal_bus import signalBus
from ..common.commodule import CommType
from PyQt5.QtCore import pyqtSignal, QThread,QObject

class Channel_info(QObject):
    channelInfoChanel = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self.all_channel = {}
        self.channel_count = 0
        signalBus.channel_connected.connect(self.channel_connected)
        signalBus.channel_disconnected.connect(self.channel_disconnected)

    def get_title_name(self, channel):
        if isinstance(channel, SerialPortThread):
            text = channel.port_name + ':' + str(channel.baud_rate)
        elif isinstance(channel, TcpClient):
            text = channel.host + ':' + str(channel.port)
        elif isinstance(channel, ClientWorker):
            text = channel.socket.peerAddress().toString() + ':' + str(channel.socket.peerPort())
        elif isinstance(channel, MQTTClientThread):
            text = channel.broker_address + ':' + str(channel.broker_port)
        else:
            text = "Unknown"
        return text
    def channel_connected(self, type, channel):
        print("channel_connected")
        channel_name = self.get_title_name(channel)
        self.all_channel[self.channel_count] = (type, channel, channel_name)
        self.channel_count += 1
        print(self.all_channel)
        self.channelInfoChanel.emit(self.all_channel)

    def channel_disconnected(self, type, channel):
        print("Channel_info: 收到 channel_disconnected 信号")
        channel_name = self.get_title_name(channel)
        for key in list(self.all_channel.keys()):
            if self.all_channel[key][1] == channel:
                del self.all_channel[key]
                break

        self.channelInfoChanel.emit(self.all_channel)


    def get_all_channel_info(self):
        return self.all_channel
    
    def get_channel_count(self):
        return len(self.all_channel)
    def is_valid_hex_string(self, input_string):
        try:
            bytes.fromhex(input_string)
            return True
        except ValueError:
            return False    
    def get_modify_text(self, type, input_text:str):
        if type == 'ASCII':
            return input_text
        formatted_frame = ''
        hex_str = input_text.replace(' ', '').replace('\n', '')
        for i in range(0, len(hex_str), 2):
            formatted_frame += hex_str[i:i + 2] + ' '
        return formatted_frame.upper()
    
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
    def send_message(self, channel, type, text):
        message, formatted_frame = self.get_message_by_type(type, text)
        if message is None:
            return
        if isinstance(channel, SerialPortThread):
            channel.data_sended.emit(message)
        if isinstance(channel, TcpClient):
            channel.data_sended.emit(message)
        if isinstance(channel, ClientWorker):
            channel.data_sended.emit(message)
  

channel_info = Channel_info()