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
        print(f"DEBUG (SerialWorker): SerialWorker thread started for port {self.port}")
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=5)
            self.connection_status.emit(True)
            print(f"DEBUG (SerialWorker): Successfully opened serial port {self.port}")
            while self.running:
                # print(f"DEBUG (SerialWorker): Loop active. Attempting to read line...")
                raw_data = self.ser.readline()
                # print(f"DEBUG (SerialWorker): Raw data read: {raw_data!r}") # Too verbose in loop, uncomment if needed

                if not raw_data: # If readline returns empty bytes (timeout), just continue
                    continue

                try:
                    data = raw_data.decode('utf-8').strip()
                    if data:
                        # RELAXED VALIDATION: Accept almost anything for debugging purposes
                        # Check if it at least contains a comma to be considered valid sensor data
                        if ',' in data:
                             print(f"DEBUG (SerialWorker): Data accepted: '{data}'")
                             self.data_received.emit(data)
                        else:
                             print(f"DEBUG (SerialWorker): Ignored non-CSV data: '{data}'")
                             
                except UnicodeDecodeError as e:
                    print(f"DEBUG (SerialWorker): UnicodeDecodeError for raw data: {raw_data!r} - {e}. Discarding.")
                except Exception as e:
                    print(f"DEBUG (SerialWorker): Unexpected error during data processing: {e}. Raw data: {raw_data!r}")
        except serial.SerialException as e:
            print(f"DEBUG (SerialWorker): Serial Error in run(): {e}")
            self.error_occurred.emit(f"Serial Error: {e}")
            self.connection_status.emit(False)
        except Exception as e:
            print(f"DEBUG (SerialWorker): Unexpected error in run(): {e}")
            self.error_occurred.emit(f"An unexpected error occurred: {e}")
            self.connection_status.emit(False)
        finally:
            print(f"DEBUG (SerialWorker): SerialWorker thread exiting for port {self.port}")
            if self.ser and self.ser.is_open:
                self.ser.close()
                print(f"DEBUG (SerialWorker): Serial port {self.port} closed.")
            self.connection_status.emit(False) # This always emits False on exit

    def stop(self):
        print(f"DEBUG (SerialWorker): Stop requested for {self.port}")
        self.running = False
        self.wait() # Wait for the thread to finish

def get_available_ports():
    """Lists serial port names"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

