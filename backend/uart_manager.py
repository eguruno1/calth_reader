import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal
from config.config import app_config

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
        
        # 디버그 모드일 경우 가상 UART 사용
        if app_config.is_debug_mode() or not app_config.is_uart_enabled():
            print("디버그 모드: 가상 UART 사용")
            self.is_connected = True
            self._led_state = 0  # 가상 LED 상태
            return True
        
        try:
            if serial is None:
                print("pyserial 모듈이 없습니다. 디버그 모드로 전환합니다.")
                app_config.set_debug_mode(True)
                return self.init_uart(port, baudrate, timeout)  # 디버그 모드로 재시도
                
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
                print("UART 포트를 열 수 없습니다. 디버그 모드로 전환합니다.")
                app_config.set_debug_mode(True)
                return self.init_uart(port, baudrate, timeout)  # 디버그 모드로 재시도
                
        except serial.SerialException as e:
            print(f"UART 연결 실패, 디버그 모드로 전환: {str(e)}")
            app_config.set_debug_mode(True)
            return self.init_uart(port, baudrate, timeout)  # 디버그 모드로 재시도
        except Exception as e:
            print(f"UART 초기화 실패, 디버그 모드로 전환: {str(e)}")
            app_config.set_debug_mode(True)
            return self.init_uart(port, baudrate, timeout)  # 디버그 모드로 재시도

    def set_led_brightness(self, brightness):
        """LED 밝기 설정 (0~45)"""
        if not self.is_connected:
            return False
        
        # 디버그 모드일 경우 가상 LED 제어
        if app_config.is_debug_mode() or not app_config.is_uart_enabled():
            brightness = max(0, min(45, int(brightness)))
            self._led_state = brightness
            print(f"디버그 모드: LED 밝기 설정 = {brightness}")
            return True
            
        if not self.ser:
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
            # 디버그 모드가 아닐 경우에만 실제 시리얼 포트 처리
            if not app_config.is_debug_mode() and app_config.is_uart_enabled():
                if self.ser and self.ser.is_open:
                    self.led_off()
                    time.sleep(0.1)
                    self.ser.close()
            elif app_config.is_debug_mode():
                print("디버그 모드: 가상 UART 연결 종료")
                
            self.is_connected = False
        except Exception as e:
            print(f"UART 종료 실패: {str(e)}")
    
    def get_led_state(self):
        """현재 LED 상태 반환 (디버그용)"""
        if hasattr(self, '_led_state'):
            return self._led_state
        return 0