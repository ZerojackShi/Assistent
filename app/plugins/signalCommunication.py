import threading
import serial
import socket, selectors
from ..common.commodule import CommType
from PyQt5.QtCore import QObject, pyqtSignal,QThread
import binascii,time
from enum import Enum
from ..common.signal_bus import signalBus
import re,datetime,os
from ..common.config import cfg
from ..common.trie import format_hex_string
from concurrent.futures import ThreadPoolExecutor
import logging
class SEND_ERR(Enum):
    SUCCESS = 0,
    ERR_TYPE = 1,
    ERR_LINK = 2,
    ERR_SEND = 3,

HEARTBEAT_INTERVAL = 10 # 每10秒发送一次心跳
MAX_MISSED_HEARTBEATS = 3 # 最大允许失踪的心跳数
class CommunicationError(Exception):
    pass

class CommunicationModule(QObject):
    # 定义连接结果信号
    connection_result = pyqtSignal(bool)
    tcpSocketChange = pyqtSignal(list)
    def __init__(self, communication_type, **kwargs):
        super().__init__()
        self.communication_type = communication_type
        self.receive_thread = None
        self.send_thread = None
        self.connected = False
        self.send_type ='HEX'
        self.serial = None
        self.tcp_socket = None
        self.tcp_server_socket = None
        self.clientSocket = []
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        if communication_type == CommType.SERIAL:
            self.serial_port = kwargs.get("serial_port", "/dev/ttyUSB0")
            self.serial_baudrate = kwargs.get("baudrate", 9600)
            self.serial_check = kwargs.get("checktype", 'E')
            self.serial_databit = kwargs.get("databit", 8)
            self.serial_stopbit = kwargs.get("stopbit", 1)
            self.serial = None
        elif communication_type == CommType.TCP_CLIENT:
            self.tcp_ip = kwargs.get("tcp_ip", "127.0.0.1")
            self.tcp_port = kwargs.get("tcp_port", 5555)
            self.tcp_socket = None
        elif communication_type == CommType.TCP_SERVICE:
            self.tcp_ip = kwargs.get("tcp_ip", "127.0.0.1")
            self.tcp_port = kwargs.get("tcp_port", 5555)
            self.tcp_server_socket = None
        else:
            raise ValueError("Unsupported communication type")

    def connect(self):
        def connect_serial():
            try:
                self.serial = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.serial_baudrate,
                    bytesize=self.serial_databit,
                    parity=self.serial_check,
                    stopbits=self.serial_stopbit,
                    timeout=0.3
                )
                if self.serial.is_open:
                    self.connected = True
                    self.receive_thread = threading.Thread(target=self.receive_data)
                    self.receive_thread.start()
                else:
                    self.connected = False
            except Exception as e:
                self.connected = False
            self.connection_result.emit(self.connected)
        def connect_tcp():
            try:
                self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_socket.connect((self.tcp_ip, self.tcp_port))
                self.connected = True
                self.receive_thread = threading.Thread(target=self.receive_data)
                self.receive_thread.start()
            except Exception as e:
                self.connected = False

            self.connection_result.emit(self.connected)

        def connect_tcp_service():
            try:   
                self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.tcp_server_socket.bind((self.tcp_ip, self.tcp_port))
                self.tcp_server_socket.listen(5)  # 最多同时处理5个连接请求
                self.connected = True
                self.connection_result.emit(self.connected)
                while self.connected:
                    client_socket, addr = self.tcp_server_socket.accept()
                    self.thread_pool.submit(handle_client, client_socket)
                    if client_socket not in self.clientSocket:
                        self.clientSocket.append(client_socket)
                        self.tcpSocketChange.emit(self.clientSocket)
            except Exception as e:
                self.connected = False
            finally:
                self.connected = False
                if self.tcp_server_socket:
                    self.tcp_server_socket.close()
                        
        def handle_client(client_socket):
            try:
                while self.connected:
                    try:
                        data = client_socket.recv(1024)
                        if not data:
                            if client_socket in self.clientSocket:
                                self.clientSocket.remove(client_socket)
                                self.tcpSocketChange.emit(self.clientSocket)
                            break
                        # 处理数据
                        self.receive_message_process(data, client_socket)
                    except socket.timeout:
                        logging.warning(f"{client_socket.getpeername()} 连接超时")
                        client_socket.close()
                        self.clientSocket.remove(client_socket)
                        self.tcpSocketChange.emit(self.clientSocket)
                        break
                    except ConnectionResetError:
                        logging.warning(f"{client_socket.getpeername()} 软件中止了一个已建立的连接")
                        client_socket.close()
                        self.clientSocket.remove(client_socket)
                        self.tcpSocketChange.emit(self.clientSocket)
                        break
            except Exception as e:
                logging.exception(e)
            finally:
                client_socket.close()
                self.clientSocket.remove(client_socket)
                self.tcpSocketChange.emit(self.clientSocket)
                            

        if self.communication_type == CommType.SERIAL:
            connection_thread = threading.Thread(target=connect_serial)
        elif self.communication_type == CommType.TCP_CLIENT:
            connection_thread = threading.Thread(target=connect_tcp)
        elif self.communication_type == CommType.TCP_SERVICE:
            connection_thread = threading.Thread(target=connect_tcp_service)
        else:
            self.connected = False

        connection_thread.start()


    def close(self):
        try:
            # 先停止接收和发送线程
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=0)
            if self.send_thread and self.send_thread.is_alive():
                self.send_thread.join(timeout=0)
            self.clientSocket.clear()
            self.tcpSocketChange.emit(self.clientSocket)
            if self.communication_type == CommType.SERIAL:
                if self.serial and self.serial.is_open:
                    self.connected = False
                    self.serial.close()
                    self.connection_result.emit(self.connected)
            elif self.communication_type == CommType.TCP_CLIENT:
                if self.tcp_socket:
                    self.connected = False
                    self.tcp_socket.close()
                    self.connection_result.emit(self.connected)
            elif self.communication_type == CommType.TCP_SERVICE:
                if self.tcp_server_socket:
                    self.connected = False
                    self.tcp_server_socket.close()
                    for client_socket in self.clientSocket:
                        client_socket.close()
                # self.thread_pool.shutdown(False, True)
                self.connection_result.emit(self.connected)
        except Exception as e:
            pass  # 在这里处理关闭时可能出现的异常

    def receive_data(self):
        data = b''
        if not self.connected:
            return None
        while self.connected:
            try:
                if self.communication_type == CommType.SERIAL:
                    if self.serial.is_open:
                        n = self.serial.inWaiting()
                        while n:
                            data += self.serial.read(n)
                            time.sleep(0.1)
                            n = self.serial.inWaiting()
                        if data:
                            self.receive_message_process(data, self.serial_port)
                            data = b''

                elif self.communication_type == CommType.TCP_CLIENT:
                    data = self.tcp_socket.recv(10240)  # 调整需要的缓冲区大小
                    self.receive_message_process(data, self.tcp_ip)
                elif self.communication_type == CommType.TCP_SERVICE:
                    print("receive tcp client message none")
                    return None
                else:
                    return None
            except ConnectionAbortedError:
                # 连接已关闭
                self.connected = False
                break

    def receive_message_process(self, data, client_socket = None):
        if data:
            if self.send_type == 'HEX':
                # 如果数据是十六进制格式，将其转换为字符串
                try:
                    text_data = data.hex() # 转为hex字符串
                    text_data = format_hex_string(text_data)
                except UnicodeDecodeError as e:
                    # 如果解码失败，你可以选择其他解码方式
                    text_data = "Failed to decode hex data: " + data.hex()
            else:
                # 如果数据是ASCII文本格式，可以直接使用
                text_data = data.decode('ascii')
            self.write_log(text_data, 0, client_socket)
            signalBus.messagereceive.emit(text_data, client_socket)
        else:
            return

    def is_valid_hex_string(self, input_string):
        try:
            bytes.fromhex(input_string)
            return True
        except ValueError:
            return False

    def send_messages(self, message, client_socket = None) -> SEND_ERR:
        if not self.connected:
            return SEND_ERR.ERR_LINK
        
        if self.send_type == 'HEX':
            if self.is_valid_hex_string(message):
                send_data = bytes.fromhex(message)
            else:
                return SEND_ERR.ERR_TYPE  # 无效的十六进制字符串
        elif self.send_type == 'ASCII':
            if isinstance(message, bytes):
                send_data = message
            elif isinstance(message, str):
                hex_message = binascii.hexlify(message.encode('ascii')).decode('ascii')
                if self.is_valid_hex_string(hex_message):
                    send_data = bytes.fromhex(hex_message)
                else:
                    return SEND_ERR.ERR_TYPE  # 无效的十六进制字符串
            else:
                return SEND_ERR.ERR_TYPE  # 未知类型，无法发送
        else:
            return SEND_ERR.ERR_TYPE  # 未知发送类型

        if self.communication_type == CommType.SERIAL:
            result = self.serial.write(send_data)
        elif self.communication_type == CommType.TCP_CLIENT:
            result = self.tcp_socket.send(send_data)
        elif self.communication_type == CommType.TCP_SERVICE:
            if isinstance(client_socket, list):
                for socket in client_socket:
                    result = socket.send(send_data)
            else:
                if client_socket:
                    result = client_socket.send(send_data)
                else:
                    result = SEND_ERR.ERR_SEND
        else:
            result = False

        if result:
            self.write_log(message, 1, client_socket)
            return SEND_ERR.SUCCESS
        else:
            return SEND_ERR.ERR_SEND

    def get_current_link_port_and_type(self):
        if self.communication_type == CommType.SERIAL:
            link_port = self.serial
        elif self.communication_type == CommType.TCP_CLIENT:
            link_port = self.tcp_socket
        elif self.communication_type == CommType.TCP_SERVICE:
            link_port = self.tcp_server_socket
        else:
            link_port = None
        return self.communication_type, link_port
    
    def set_message_send_type(self, type):
        self.send_type = type

    def write_log(self, text, diraction, client_socket = None):
        def get_link_type_str():
            if self.communication_type == CommType.SERIAL:
                return self.serial_port
            elif self.communication_type == CommType.TCP_CLIENT:
                return self.tcp_socket.getpeername()
            elif self.communication_type == CommType.TCP_SERVICE:
                if isinstance(client_socket, list):
                    return "AllTcpSession"
                else:
                    client_address = client_socket.getpeername()
                    client_ip, client_port = client_address
                    return f"{client_ip}:{client_port}"
            else:
                return 'unknown'
        path = cfg.get(cfg.logFolder)
        flodername = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_path = os.path.join(path, f"{flodername}/frame.log")
        link_type = get_link_type_str()
          # 判断日志目录是否存在,不存在创建
        if not os.path.exists(os.path.dirname(file_path)): 
            os.makedirs(os.path.dirname(file_path))

        if diraction:
            dir_str = ">>> 发送:"
        else:
            dir_str = "<<< 接收:"
        try:
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write(f"{current_time} [{link_type}] {dir_str} {text}\n")
        except FileNotFoundError:
            # 如果文件不存在，创建新文件并以二进制方式写入内容
            with open(file_path, 'w') as file:
                file.write(f"{current_time} [{link_type}] {dir_str} {text}\n")