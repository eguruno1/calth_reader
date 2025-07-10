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

class UARTModel:
    """UART 데이터 모델"""
    
    def __init__(self):
        self.settings = UARTSettings()
        self.is_connected = False
        self.current_led_control: Optional[LEDControl] = None
        self.command_history = []
        self._observers = []
    
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
            'command_count': len(self.command_history)
        }
