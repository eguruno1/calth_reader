# -*- coding: utf-8 -*-
"""
UART Service - UART 하드웨어 제어 서비스
"""
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal
from models.uart_model import UARTModel, LEDControl
from config.config import app_config

try:
    import serial
except ImportError as e:
    print(f"Serial import error: {e}")
    print("Please install pyserial: pip install pyserial")
    serial = None

class UARTService(QObject):
    """UART 하드웨어 제어 서비스"""
    
    # 시그널 정의
    led_changed = pyqtSignal(LEDControl)
    connection_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, uart_model: UARTModel):
        super().__init__()

        # RX 스레드 제어 : UART 수신용
        self._rx_thread = None
        self._rx_running = False

        self.model = uart_model
        self.ser = None
        self._lock = threading.Lock()
        self._is_debug_mode = app_config.is_debug_mode()

        # 🔋 배터리 수신 주기 제어 (1분)
        self._battery_interval_sec = 60
        self._last_battery_read_time = 0.0
        
        # 모델 옵저버 등록
        self.model.add_observer(self)
    
    def on_uart_event(self, event_type: str, data):
        """모델 이벤트 처리"""
        if event_type == 'led_changed':
            self.led_changed.emit(data)
    
    def initialize(self, port: str = '/dev/ttyTHS1', baudrate: int = 115200, timeout: float = 1.0) -> bool:
        """UART 서비스 초기화"""
        try:
            # 모델 설정 업데이트
            self.model.settings.port = port
            self.model.settings.baudrate = baudrate
            self.model.settings.timeout = timeout
            
            if self._is_debug_mode or not app_config.is_uart_enabled():
                return self._initialize_debug_uart()
            else:
                return self._initialize_real_uart()
        except Exception as e:
            error_msg = f"UART 초기화 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _initialize_real_uart(self) -> bool:
        """실제 UART 초기화"""
        try:
            if serial is None:
                raise Exception("pyserial 모듈이 설치되지 않음")
            
            if self.ser and self.ser.is_open:
                self.ser.close()
            
            self.ser = serial.Serial(
                port=self.model.settings.port,
                baudrate=self.model.settings.baudrate,
                bytesize=self.model.settings.bytesize,
                parity=self.model.settings.parity,
                stopbits=self.model.settings.stopbits,
                timeout=self.model.settings.timeout
            )
            
            if self.ser.is_open:
                self.model.set_connected(True)
                self.connection_changed.emit(True)
                print("실제 UART 초기화 성공")
                
                # LED 초기화 (끄기)
                self.set_led_brightness(0)
                # RX 스레드 시작
                self._start_rx_loop()
                return True
            else:
                raise Exception("UART 포트를 열 수 없음")
                
        except Exception as e:
            print(f"실제 UART 초기화 실패: {str(e)}")
            # 실패시 디버그 모드로 폴백
            app_config.set_debug_mode(True)
            self._is_debug_mode = True
            return self._initialize_debug_uart()
    
    def _initialize_debug_uart(self) -> bool:
        """디버그용 가상 UART 초기화"""
        print("디버그 모드: 가상 UART 초기화")
        self.model.set_connected(True)
        self.connection_changed.emit(True)
        
        # 가상 LED 초기화
        self.model.set_led_brightness(0)
        # RX 스레드 시작
        self._start_rx_loop()
        return True
    
    def set_led_brightness(self, brightness: int) -> bool:
        """LED 밝기 설정"""
        try:
            # 모델에 LED 상태 설정
            led_control = self.model.set_led_brightness(brightness)
            
            if self._is_debug_mode or not app_config.is_uart_enabled():
                return self._set_debug_led(brightness)
            else:
                return self._set_real_led(brightness)
                
        except Exception as e:
            error_msg = f"LED 제어 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _set_real_led(self, brightness: int) -> bool:
        """실제 LED 제어"""
        if not self.model.is_connected or not self.ser:
            return False
        
        try:
            brightness = max(0, min(45, int(brightness)))
            command = f"L{brightness:02d}"
            
            with self._lock:
                self.ser.write(command.encode('utf-8'))
                self.ser.flush()
            
            print(f"실제 LED 제어: {brightness}")
            return True
            
        except Exception as e:
            error_msg = f"실제 LED 제어 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _set_debug_led(self, brightness: int) -> bool:
        """디버그용 가상 LED 제어"""
        brightness = max(0, min(45, int(brightness)))
        print(f"디버그 모드: 가상 LED 밝기 = {brightness}")
        return True
    
    def led_on(self, brightness: int = 45) -> bool:
        """LED 켜기"""
        return self.set_led_brightness(brightness)
    
    def led_off(self) -> bool:
        """LED 끄기"""
        return self.set_led_brightness(0)
    
    def get_led_brightness(self) -> int:
        """현재 LED 밝기 반환"""
        return self.model.get_led_brightness()
    
    def get_led_state(self) -> dict:
        """LED 상태 반환"""
        brightness = self.model.get_led_brightness()
        return {
            'brightness': brightness,
            'is_on': brightness > 0
        }
    
    def get_battery_status(self):
        """
        배터리 상태 읽기 (RX only, 1분 주기 제한)
        사용하지 않음.
        """

        now = time.time()

        # ⏱️ 1분 주기 제한
        if now - self._last_battery_read_time < self._battery_interval_sec:
            return None

        # 디버그 모드
        if self._is_debug_mode or not app_config.is_uart_enabled():
            import random

            self._last_battery_read_time = now

            current_time = int(now)
            base_level = 60 + (current_time % 40)
            is_charging = (current_time // 60) % 2 == 0

            voltage = 3.7 + (base_level / 100) * 0.5
            temperature = 25.0 + random.uniform(-5, 10)

            return {
                'level': base_level,
                'is_charging': is_charging,
                'voltage': voltage,
                'temperature': temperature
            }

        # 실제 UART
        if not self.ser or not self.model.is_connected:
            return None

        try:
            with self._lock:
                if self.ser.in_waiting <= 0:
                    return None

                response = self.ser.readline().decode(
                    'utf-8', errors='ignore'
                ).strip()

            if not response:
                return None

            parsed = self._parse_battery_response(response)
            if parsed:
                # ✅ 정상 수신 시에만 시간 갱신
                self._last_battery_read_time = now

            return parsed

        except Exception as e:
            print(f"배터리 상태 읽기 실패: {str(e)}")
            return None


    
    def _parse_battery_response(self, response):
        """UART 응답에서 배터리 정보 파싱 (B+ 프로토콜)"""
        try:
            # 예상 형식: B+FF 또는 B+90
            if not response.startswith("B+"):
                return None

            hex_value = response[2:4]

            if hex_value.upper() == "FF":
                level = 100
            else:
                level = int(hex_value, 16)
                level = max(0, min(100, level))

            return {
                'level': level,
                'is_charging': None,     # 프로토콜에 없음
                'voltage': None,         # 프로토콜에 없음
                'temperature': None      # 프로토콜에 없음
            }

        except ValueError as e:
            print(f"UART: 배터리 응답 파싱 오류: {response}, {str(e)}")
            return None

    

    def shutdown(self):
        """서비스 종료"""
        try:
            # RX 종료
            self._rx_running = False
            
            # LED 끄기
            self.led_off()
            time.sleep(0.1)
            
            # 실제 시리얼 포트 닫기
            if not self._is_debug_mode and self.ser and self.ser.is_open:
                self.ser.close()
            
            self.model.set_connected(False)
            self.connection_changed.emit(False)
            
            if self._is_debug_mode:
                print("디버그 모드: 가상 UART 종료")
            else:
                print("실제 UART 서비스 종료")
                
        except Exception as e:
            error_msg = f"UART 종료 실패: {str(e)}"
            self.error_occurred.emit(error_msg)

    #####################################################
    # Battery Status
    #####################################################
    def _handle_received_data(self, data: dict):
        if "battery" not in data:
            return

        battery = data["battery"]

        self.model.update_battery_info(
            level=battery.get("level", 0),
            is_charging=battery.get("is_charging", False),
            voltage=battery.get("voltage", 0.0),
            temperature=battery.get("temperature", 0.0)
        )

    def _start_rx_loop(self):
        """RX 루프 구현"""
        if self._rx_running:
            return

        self._rx_running = True
        self._rx_thread = threading.Thread(
            target=self._rx_loop,
            daemon=True
        )
        self._rx_thread.start()

    def _rx_loop(self):
        print("[UARTService] RX loop started")

        while self._rx_running:
            try:
                line = self.ser.readline()   # blocking
                if not line:
                    continue

                raw = line.decode("utf-8", errors="ignore").strip()
                print(f"[UARTService] RX raw: {raw}")

                # 🔋 배터리 데이터 처리
                if raw.startswith("B+"):
                    self._handle_battery_raw(raw) # 수신데이터 처리.

            except Exception as e:
                print(f"[UARTService] RX loop error: {e}")

    def _handle_battery_raw(self, raw: str):
        """
        수신 예:
        B+FF  → 100%
        B+95  → 95%
        B+10  → 10%
        """
        try:
            value = raw[2:]  # "FF" or "95" or "10"

            if value.upper() == "FF":
                level = 100
            else:
                level = int(value)

            print(f"[UARTService] 배터리 수신 파싱됨: {level}%")

            self.model.update_battery_info(
                level=level,
                is_charging=False,   # 장비 프로토콜상 정보 없음
                voltage=0.0,
                temperature=0.0
            )

        except Exception as e:
            print(f"[UARTService] 배터리 파싱 오류 ({raw}): {e}")



