# -*- coding: utf-8 -*-
"""
UART Model - UART 통신 데이터 모델
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum

class LEDState(Enum):
    """LED 상태 열거형"""
    OFF = 0
    ON = 1
    DIMMED = 2

@dataclass
class UARTSettings:
    """UART 설정 데이터 클래스"""
    port: str = '/dev/ttyTHS1'
    baudrate: int = 115200
    timeout: float = 1.0
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1

@dataclass
class LEDControl:
    """LED 제어 데이터 클래스"""
    brightness: int  # 0-45
    state: LEDState
    timestamp: datetime
    
    def __post_init__(self):
        # 밝기 값 검증
        self.brightness = max(0, min(45, self.brightness))
        # 상태 자동 결정
        if self.brightness == 0:
            self.state = LEDState.OFF
        elif self.brightness == 45:
            self.state = LEDState.ON
        else:
            self.state = LEDState.DIMMED

class BatteryStatus(Enum):
    """배터리 상태 열거형"""
    CHARGING = "charging"           # 충전 중 (전원 연결됨)
    FULL = "full"                   # 완전 충전
    NORMAL = "normal"               # 정상 (50% 이상)
    LOW = "low"                     # 낮음 (20-50%)
    CRITICAL = "critical"           # 위험 (5-20%)
    EMPTY = "empty"                 # 거의 없음 (5% 미만)
    UNKNOWN = "unknown"             # 상태 불명

@dataclass
class BatteryInfo:
    """배터리 정보 데이터 클래스"""
    level: int                      # 배터리 레벨 (0-100)
    status: BatteryStatus           # 배터리 상태
    is_charging: bool               # 충전 중 여부
    voltage: float                  # 배터리 전압
    temperature: float              # 배터리 온도
    timestamp: datetime             # 마지막 업데이트 시간
    
    def get_icon_name(self) -> str:
        """배터리 상태에 따른 아이콘 파일명 반환"""
        if self.is_charging or self.status == BatteryStatus.CHARGING:
            return "Battery_Icon-100.png"  # 충전 중일 때는 항상 풀 아이콘
        
        # 배터리 레벨에 따른 아이콘 선택
        if self.level >= 95:
            return "Battery_Icon-100.png"
        elif self.level >= 85:
            return "Battery_Icon-090.png"
        elif self.level >= 75:
            return "Battery_Icon-080.png"
        elif self.level >= 65:
            return "Battery_Icon-070.png"
        elif self.level >= 55:
            return "Battery_Icon-060.png"
        elif self.level >= 45:
            return "Battery_Icon-050.png"
        elif self.level >= 35:
            return "Battery_Icon-040.png"
        elif self.level >= 25:
            return "Battery_Icon-030.png"
        elif self.level >= 15:
            return "Battery_Icon-020.png"
        elif self.level >= 5:
            return "Battery_Icon-010.png"
        else:
            return "Battery_Icon-000.png"
    
    def get_status_text(self) -> str:
        """배터리 상태 텍스트 반환"""
        if self.is_charging:
            return f"충전중 {self.level}%"
        else:
            return f"{self.level}%"

class UARTModel:
    """UART 데이터 모델"""
    
    def __init__(self):
        self.settings = UARTSettings()
        self.is_connected = False
        self.current_led_control: Optional[LEDControl] = None
        self.command_history = []
        self._observers = []
        self.battery_info: Optional[BatteryInfo] = None
    
    def add_observer(self, observer):
        """옵저버 추가"""
        self._observers.append(observer)
    
    def remove_observer(self, observer):
        """옵저버 제거"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, event_type: str, data=None):
        """옵저버들에게 변경사항 알림"""
        for observer in self._observers:
            if hasattr(observer, 'on_uart_event'):
                observer.on_uart_event(event_type, data)
    
    def set_connected(self, status: bool):
        """연결 상태 설정"""
        self.is_connected = status
        self.notify_observers('connection_changed', status)
    
    def set_led_brightness(self, brightness: int) -> LEDControl:
        """LED 밝기 설정"""
        led_control = LEDControl(
            brightness=brightness,
            state=LEDState.OFF,  # __post_init__에서 자동 결정
            timestamp=datetime.now()
        )
        
        self.current_led_control = led_control
        self.command_history.append(led_control)
        
        # 히스토리 크기 제한 (최대 100개)
        if len(self.command_history) > 100:
            self.command_history.pop(0)
        
        self.notify_observers('led_changed', led_control)
        return led_control
    
    def get_current_led_state(self) -> Optional[LEDControl]:
        """현재 LED 상태 반환"""
        return self.current_led_control
    
    def get_led_brightness(self) -> int:
        """현재 LED 밝기 반환"""
        return self.current_led_control.brightness if self.current_led_control else 0
    
    def get_command_history(self, limit: int = 10) -> list:
        """명령 히스토리 반환"""
        return self.command_history[-limit:] if self.command_history else []
    
    def get_info(self) -> dict:
        """UART 정보 반환"""
        return {
            'connected': self.is_connected,
            'settings': self.settings.__dict__,
            'current_led': {
                'brightness': self.current_led_control.brightness,
                'state': self.current_led_control.state.name,
                'timestamp': self.current_led_control.timestamp
            } if self.current_led_control else None,
            'command_count': len(self.command_history),
            'battery': {
                'level': self.battery_info.level,
                'status': self.battery_info.status.value,
                'is_charging': self.battery_info.is_charging,
                'voltage': self.battery_info.voltage,
                'temperature': self.battery_info.temperature,
                'timestamp': self.battery_info.timestamp
            } if self.battery_info else None
        }
    
    def update_battery_info(self, level: int, is_charging: bool = False, 
                           voltage: float = 0.0, temperature: float = 0.0):
        """배터리 정보 업데이트"""
        # 배터리 상태 결정
        if is_charging:
            status = BatteryStatus.CHARGING
        elif level >= 90:
            status = BatteryStatus.FULL
        elif level >= 50:
            status = BatteryStatus.NORMAL
        elif level >= 20:
            status = BatteryStatus.LOW
        elif level >= 5:
            status = BatteryStatus.CRITICAL
        else:
            status = BatteryStatus.EMPTY
        
        self.battery_info = BatteryInfo(
            level=level,
            status=status,
            is_charging=is_charging,
            voltage=voltage,
            temperature=temperature,
            timestamp=datetime.now()
        )
        
        # 옵저버들에게 배터리 상태 변경 알림
        self.notify_observers('battery_changed', self.battery_info)
    
    def get_battery_info(self) -> Optional[BatteryInfo]:
        """현재 배터리 정보 반환"""
        return self.battery_info
