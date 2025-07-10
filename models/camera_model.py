# -*- coding: utf-8 -*-
"""
Camera Model - 카메라 데이터 모델
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime

@dataclass
class CameraSettings:
    """카메라 설정 데이터 클래스"""
    width: int = 640
    height: int = 480
    fps: int = 30
    flip_method: int = 2
    
@dataclass
class CameraFrame:
    """카메라 프레임 데이터 클래스"""
    frame_data: np.ndarray
    timestamp: datetime
    frame_id: int
    is_valid: bool = True
    
    @property
    def shape(self) -> Tuple[int, int, int]:
        """프레임 크기 반환"""
        return self.frame_data.shape if self.frame_data is not None else (0, 0, 0)
    
    @property
    def size(self) -> int:
        """프레임 데이터 크기 반환"""
        return self.frame_data.size if self.frame_data is not None else 0

class CameraModel:
    """카메라 데이터 모델"""
    
    def __init__(self):
        self.settings = CameraSettings()
        self.current_frame: Optional[CameraFrame] = None
        self.is_initialized = False
        self.is_capturing = False
        self.frame_counter = 0
        self._observers = []
    
    def add_observer(self, observer):
        """옵저버 추가 (MVC 패턴)"""
        self._observers.append(observer)
    
    def remove_observer(self, observer):
        """옵저버 제거"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, event_type: str, data=None):
        """옵저버들에게 변경사항 알림"""
        for observer in self._observers:
            if hasattr(observer, 'on_camera_event'):
                observer.on_camera_event(event_type, data)
    
    def set_frame(self, frame_data: np.ndarray):
        """새 프레임 설정"""
        self.frame_counter += 1
        self.current_frame = CameraFrame(
            frame_data=frame_data,
            timestamp=datetime.now(),
            frame_id=self.frame_counter
        )
        self.notify_observers('frame_updated', self.current_frame)
    
    def get_current_frame(self) -> Optional[CameraFrame]:
        """현재 프레임 반환"""
        return self.current_frame
    
    def set_initialized(self, status: bool):
        """초기화 상태 설정"""
        self.is_initialized = status
        self.notify_observers('initialization_changed', status)
    
    def set_capturing(self, status: bool):
        """캡처 상태 설정"""
        self.is_capturing = status
        self.notify_observers('capture_status_changed', status)
    
    def get_info(self) -> dict:
        """카메라 정보 반환"""
        return {
            'initialized': self.is_initialized,
            'capturing': self.is_capturing,
            'frame_count': self.frame_counter,
            'settings': self.settings.__dict__,
            'current_frame_info': {
                'timestamp': self.current_frame.timestamp if self.current_frame else None,
                'frame_id': self.current_frame.frame_id if self.current_frame else None,
                'shape': self.current_frame.shape if self.current_frame else None,
                'is_valid': self.current_frame.is_valid if self.current_frame else False
            } if self.current_frame else None
        }
