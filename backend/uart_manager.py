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
    
    def get_battery_status(self):
        """배터리 상태 읽기"""
        # 디버그 모드일 경우 가상 배터리 상태 반환
        if app_config.is_debug_mode() or not app_config.is_uart_enabled():
            # 가상 배터리 상태 시뮬레이션
            import random
            import time
            
            # 시간 기반으로 일정한 패턴의 배터리 레벨 생성 (테스트용)
            current_time = int(time.time())
            base_level = 60 + (current_time % 40)  # 60-100% 사이에서 변화
            is_charging = (current_time // 60) % 2 == 0  # 1분마다 충전상태 토글
            
            voltage = 3.7 + (base_level / 100) * 0.5  # 3.7V ~ 4.2V
            temperature = 25.0 + random.uniform(-5, 10)  # 20-35도
            
            print(f"디버그 모드: 배터리 상태 - {base_level}%, 충전중: {is_charging}")
            
            return {
                'level': base_level,
                'is_charging': is_charging,
                'voltage': voltage,
                'temperature': temperature
            }
        
        if not self.ser or not self.is_connected:
            return None
            
        try:
            # 실제 UART로 배터리 상태 요청 명령 전송
            command = "BAT"  # 배터리 상태 요청 명령
            
            with self._lock:
                self.ser.write(command.encode('utf-8'))
                self.ser.flush()
                
                # 응답 대기 (최대 2초)
                time.sleep(0.1)
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8').strip()
                    return self._parse_battery_response(response)
                else:
                    print("UART: 배터리 상태 응답 없음")
                    return None
                    
        except Exception as e:
            print(f"배터리 상태 읽기 실패: {str(e)}")
            return None
    
    def _parse_battery_response(self, response):
        """UART 응답에서 배터리 정보 파싱"""
        try:
            # 예상 응답 형식: "BAT:85,0,3.95,28.5"
            # (레벨, 충전상태, 전압, 온도)
            if response.startswith("BAT:"):
                parts = response[4:].split(',')
                if len(parts) >= 4:
                    return {
                        'level': int(parts[0]),
                        'is_charging': bool(int(parts[1])),
                        'voltage': float(parts[2]),
                        'temperature': float(parts[3])
                    }
            
            print(f"UART: 잘못된 배터리 응답 형식: {response}")
            return None
            
        except (ValueError, IndexError) as e:
            print(f"UART: 배터리 응답 파싱 오류: {str(e)}")
            return None