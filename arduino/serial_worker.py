import serial
import serial.tools.list_ports
from PyQt6.QtCore import QThread, pyqtSignal

class SerialWorker(QThread):
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, port, baud_rate=9600):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.running = True

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.connection_status.emit(True)
            while self.running:
                if self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    if data:
                        self.data_received.emit(data)
                self.msleep(10) # Small delay to prevent busy-waiting
        except serial.SerialException as e:
            self.error_occurred.emit(f"Serial Error: {e}")
            self.connection_status.emit(False)
        except Exception as e:
            self.error_occurred.emit(f"An unexpected error occurred: {e}")
            self.connection_status.emit(False)
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.connection_status.emit(False)

    def stop(self):
        self.running = False
        self.wait() # Wait for the thread to finish

def get_available_ports():
    """Lists serial port names"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

