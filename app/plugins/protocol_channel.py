from ..plugins.signalCommunication import SerialPortThread,MQTTClientThread,TcpClient,ClientWorker,MqttMessageDetails
from PyQt5.QtCore import QObject,pyqtSlot,pyqtSignal,QTimer,QThread
from .frame_fun import FrameFun as frame_fun
import binascii,threading,queue
from .frame_csg import *
import asyncio

class AsyncCommunicator(QObject):
    def __init__(self, channel,callback):
        super().__init__()
        self.callback = callback
        self.channel = channel
        self.receive_event = asyncio.Event()
        self.received_data = None
        self.stop_flag = False
        self.afn = 0
        self.dir = 0
        self.prm = 0
        self.seq = 0
        self.adress = None

    async def send_and_receive(self, index, send_signal, timeout=10):
        try:
            print("send data", datetime.now())
            await self.send_signal(send_signal)
            received_data = await self.receive_signal(timeout)
            if self.callback and received_data is not None:
                print("receive data", datetime.now())
                self.callback(index, received_data)
        except asyncio.TimeoutError:
            if not self.stop_flag:
                print("Operation timed out")
        except asyncio.CancelledError:
            print("send_and_receive Operation cancelled")

    async def send_signal(self, frame):
        frame_bytearray = bytearray(frame)
        message = bytes(frame_bytearray)
        print("send_message", frame, message)
        self.dir, self.prm, self.seq, self.afn, self.adress = get_frame_info(frame)
        print("send dir, prm, seq, afn, adress", self.dir, self.prm,self.seq,self.afn, self.adress)
        if self.channel is None:
            return
        if isinstance(self.channel, SerialPortThread):
            self.channel.data_sended.emit(message)
        elif isinstance(self.channel, TcpClient):
            self.channel.data_sended.emit(message)
        elif isinstance(self.channel, ClientWorker):
            self.channel.data_sended.emit(message)

    async def receive_signal(self, timeout):
        print("Waiting to receive signal...")
        try:
            await asyncio.wait_for(self._wait_for_event_or_stop(), timeout)
            if self.stop_flag:
                print("Operation cancelled")
                self.received_data = None
                raise asyncio.CancelledError
            return self.received_data
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError
        finally:
            self.receive_event.clear()
            print("quit receive signal...")

    async def _wait_for_event_or_stop(self):
        while not self.receive_event.is_set():
            if self.stop_flag:
                return
            await asyncio.sleep(0.01)

    def on_receive_data(self, data):
        rec_frame = frame_fun.bytes_to_decimal_list(data)
        if rec_frame is None:
            return
        dir, prm, seq, afn, adress = get_frame_info(rec_frame)
        print("reveice dir, prm, seq, afn, adress", dir, prm, seq, afn, adress, datetime.now())
        if dir == 1 and prm == 0 and self.seq == seq and self.afn == afn:
            self.received_data = rec_frame
            self.receive_event.set()

    def stop(self):
        self.stop_flag = True
        self.receive_event.set()  # Unblock any waiting coroutines
        print("AsyncCommunicator stopped.")

    def init_slot(self):
        if self.channel is not None:
            print("init_slot")
            if isinstance(self.channel, SerialPortThread):
                self.channel.data_received.connect(self.on_receive_data)
            elif isinstance(self.channel, TcpClient):
                self.channel.data_received.connect(self.on_receive_data)
            elif isinstance(self.channel, ClientWorker):
                self.channel.receive_data.connect(self.on_receive_data)
    
    def close_slot(self):
        if self.channel is not None:
            print("close_slot")
            if isinstance(self.channel, SerialPortThread):
                self.channel.data_received.disconnect(self.on_receive_data)
            elif isinstance(self.channel, TcpClient):
                self.channel.data_received.disconnect(self.on_receive_data)
            elif isinstance(self.channel, ClientWorker):
                self.channel.receive_data.disconnect(self.on_receive_data)

class WorkerThread(QThread):
    result_signal = pyqtSignal(object)

    def __init__(self, channel, timeout, callback=None, parent=None):
        super().__init__(parent)
        self.communicator = AsyncCommunicator(channel, callback)
        self.channel = channel
        self.timeout = timeout
        self.callback = callback
        self.loop = None
        self.tasks = []
        self.send_data_list = []
        self.stop_flag = False

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.communicator.init_slot()
        try:
            self.loop.run_until_complete(self.process_send_list())
        except Exception as e:
            print(f"Exception in worker thread: {e}")
        finally:
            self.cleanup_tasks()
            if self.loop.is_running():
                self.loop.stop()
            self.loop.close()
            self.communicator.close_slot()


    def stop(self):
        self.stop_flag = True
        self.communicator.stop()
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait()
        self.quit()
        print("Worker thread stopped.")

    def __del__(self):
        if not self.loop.is_closed():
            self.cleanup_tasks()
            if self.loop.is_running():
                self.loop.stop()
            self.loop.close()
        print("Worker thread destroyed.")

    def cleanup_tasks(self):
        if self.loop and not self.loop.is_closed():
            pending = [task for task in asyncio.all_tasks(loop=self.loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                try:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except asyncio.CancelledError:
                    pass  # Ignore exceptions due to cancellation

    def set_send_data(self, data_list):
        self.send_data_list = data_list

    async def process_send_list(self):
        for i, send_data in enumerate(self.send_data_list):
            if self.stop_flag:
                break
            try:
                await self.communicator.send_and_receive(i, send_data, self.timeout)
            except asyncio.CancelledError:
                break        