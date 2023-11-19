from asyncio.windows_events import NULL
import socket
import os,re
import datetime
import binascii
from ..plugins import frame_fun
import threading
import codecs
def create_tcp_connection(ip, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        print(f"TCP connnect to {ip} port {port}")
        return client_socket
    except Exception as e:
        print(f"Error creating TCP connection: {str(e)}")
        return None

def send_tcp_data(socket, data):
    try:
        socket.sendall(data)
        print(f"TCP send {data}")
    except Exception as e:
        print(f"Error sending TCP data: {str(e)}")

def receive_tcp_data(socket, buffer_size=1024):
    try:
        data = socket.recv(buffer_size)
        print(f"TCP receive {data}")
        return data
    except Exception as e:
        print(f"Error receiving TCP data: {str(e)}")
        return None

def close_tcp_connection(socket):
    try:
        socket.close()
    except Exception as e:
        print(f"Error closing TCP connection: {str(e)}")

client_global_socket = None
log_file = None
def get_new_tcp_client_session(ip, port):
    global client_global_socket
    client_global_socket = create_tcp_connection(ip, port)
    thread1 = threading.Thread(target=receive_data_from_tcp)
    thread1.start()
    return client_global_socket

def send_to_tcp_data(buff, data_type):
    global client_global_socket
    log_data = frame_fun.get_data_str_order(buff)
    if client_global_socket:
        if data_type == 1:#send hex
            send_data = binascii.unhexlify(log_data)
        send_tcp_data(client_global_socket, send_data)
        write_data =  frame_fun.to_hex_string_with_space(buff)
        write_log_to_file(client_global_socket, write_data, True)
    else:
        print("Socket is not initialized.")

def receive_data_from_tcp():
    global client_global_socket
    if client_global_socket:
        buff = receive_tcp_data(client_global_socket)
        log_data = codecs.encode(buff, 'hex').decode() 

        # 在每个两个字符间插入一个空格
        hex_str = re.sub('..(?!$)', '\\g<0> ', log_data)
        hex_str = hex_str.upper()  
        write_log_to_file(client_global_socket, hex_str, False)
    else:
        print("Socket is not initialized.")

def write_log_to_file(socket, write_data, dir=True):
    # 将发送的内容和时间以二进制方式写入文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(current_dir, ":/gallery/images/log.log")
    remote_address = socket.getpeername()
    if dir:
        dir_str = ">>> Send:"
    else:
        dir_str = "<<< Receive:"
    try:
        with open(file_path, 'a') as file:
            file.write(f"{current_time} {remote_address} {dir_str} {write_data}\n")
    except FileNotFoundError:
        # 如果文件不存在，创建新文件并以二进制方式写入内容
        with open(file_path, 'w') as file:
            file.write(f"{current_time} {remote_address} {dir_str} {write_data}\n")