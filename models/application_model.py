# -*- coding: utf-8 -*-
"""
Application Model - 애플리케이션 전체 상태 관리
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SystemMode(Enum):
    """시스템 모드"""
    DEBUG = "debug"
    PRODUCTION = "production"
    TESTING = "testing"

class SystemStatus(Enum):
    """시스템 상태"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    SHUTDOWN = "shutdown"

@dataclass
class ApplicationSettings:
    """애플리케이션 설정"""
    debug_mode: bool = True
    camera_enabled: bool = False
    uart_enabled: bool = False
    auto_save_enabled: bool = True
    language: str = "ko"
    theme: str = "default"

@dataclass
class SystemInfo:
    """시스템 정보"""
    mode: SystemMode
    status: SystemStatus
    startup_time: datetime
    last_update: datetime
    error_count: int = 0
    warning_count: int = 0

class ApplicationModel:
    """애플리케이션 전체 모델"""
    
    def __init__(self):
        self.settings = ApplicationSettings()
        self.system_info = SystemInfo(
            mode=SystemMode.DEBUG,
            status=SystemStatus.INITIALIZING,
            startup_time=datetime.now(),
            last_update=datetime.now()
        )
        self.error_log = []
        self.performance_metrics = {}
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
            if hasattr(observer, 'on_app_event'):
                observer.on_app_event(event_type, data)
    
    def set_debug_mode(self, enabled: bool):
        """디버그 모드 설정"""
        old_mode = self.settings.debug_mode
        self.settings.debug_mode = enabled
        self.settings.camera_enabled = not enabled
        self.settings.uart_enabled = not enabled
        
        if enabled:
            self.system_info.mode = SystemMode.DEBUG
        else:
            self.system_info.mode = SystemMode.PRODUCTION
        
        self._update_timestamp()
        self.notify_observers('debug_mode_changed', {
            'old_mode': old_mode,
            'new_mode': enabled
        })
    
    def set_system_status(self, status: SystemStatus):
        """시스템 상태 설정"""
        old_status = self.system_info.status
        self.system_info.status = status
        self._update_timestamp()
        
        self.notify_observers('system_status_changed', {
            'old_status': old_status,
            'new_status': status
        })
    
    def add_error(self, error_message: str, error_type: str = "general"):
        """오류 추가"""
        error_entry = {
            'message': error_message,
            'type': error_type,
            'timestamp': datetime.now(),
            'id': len(self.error_log) + 1
        }
        
        self.error_log.append(error_entry)
        self.system_info.error_count += 1
        
        # 로그 크기 제한 (최대 1000개)
        if len(self.error_log) > 1000:
            self.error_log.pop(0)
        
        self._update_timestamp()
        self.notify_observers('error_added', error_entry)
    
    def add_warning(self, warning_message: str):
        """경고 추가"""
        self.system_info.warning_count += 1
        self._update_timestamp()
        self.notify_observers('warning_added', warning_message)
    
    def update_performance_metric(self, metric_name: str, value: Any):
        """성능 지표 업데이트"""
        self.performance_metrics[metric_name] = {
            'value': value,
            'timestamp': datetime.now()
        }
        self._update_timestamp()
        self.notify_observers('performance_updated', {
            'metric': metric_name,
            'value': value
        })
    
    def _update_timestamp(self):
        """마지막 업데이트 시간 갱신"""
        self.system_info.last_update = datetime.now()
    
    def get_system_status_info(self) -> Dict[str, Any]:
        """시스템 상태 정보 반환"""
        return {
            'mode': self.system_info.mode.value,
            'status': self.system_info.status.value,
            'debug_mode': self.settings.debug_mode,
            'camera_enabled': self.settings.camera_enabled,
            'uart_enabled': self.settings.uart_enabled,
            'startup_time': self.system_info.startup_time,
            'last_update': self.system_info.last_update,
            'error_count': self.system_info.error_count,
            'warning_count': self.system_info.warning_count,
            'uptime': datetime.now() - self.system_info.startup_time
        }
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """최근 오류 목록 반환"""
        return self.error_log[-limit:] if self.error_log else []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """성능 요약 반환"""
        return {
            'metrics': self.performance_metrics,
            'total_metrics': len(self.performance_metrics)
        }
