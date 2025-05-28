import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal

try:
    import serial
except ImportError as e:
    print(f"Serial import error: {e}")
    print("Please install pyserial: pip install pyserial")
    serial = None

class UARTManager(QObject):
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UARTManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            super().__init__()
            self.ser = None
            self.is_connected = False
            self._lock = threading.Lock()
            self._initialized = True

    def init_uart(self, port='/dev/ttyTHS1', baudrate=115200, timeout=1):
        """UART 초기화"""
        try:
            if serial is None:
                raise Exception("pyserial module not available. Please install: pip install pyserial")
                
            if self.ser and self.ser.is_open:
                self.ser.close()
                
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            
            if self.ser.is_open:
                self.is_connected = True
                # LED 초기화 (꺼진 상태로)
                self.set_led_brightness(45)
                return True
            else:
                raise Exception("UART 포트를 열 수 없습니다.")
                
        except Exception as e:
            self.is_connected = False
            raise Exception(f"UART 초기화 실패: {str(e)}")

    def set_led_brightness(self, brightness):
        """LED 밝기 설정 (0~45)"""
        if not self.is_connected or not self.ser:
            return False
            
        try:
            brightness = max(0, min(45, int(brightness)))
            command = f"L{brightness:02d}"
            
            with self._lock:
                self.ser.write(command.encode('utf-8'))
                self.ser.flush()
            return True
            
        except Exception as e:
            print(f"LED 제어 실패: {str(e)}")
            return False

    def led_on(self, brightness=45):
        """LED 켜기"""
        return self.set_led_brightness(brightness)

    def led_off(self):
        """LED 끄기"""
        return self.set_led_brightness(0)

    def close(self):
        """UART 연결 종료"""
        try:
            if self.ser and self.ser.is_open:
                self.led_off()
                time.sleep(0.1)
                self.ser.close()
            self.is_connected = False
        except Exception as e:
            print(f"UART 종료 실패: {str(e)}")