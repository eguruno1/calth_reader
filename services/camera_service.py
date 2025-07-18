# -*- coding: utf-8 -*-
"""
Camera Service - 카메라 하드웨어 제어 서비스
"""
import cv2
import numpy as np
import os
import logging
from datetime import datetime
from typing import Optional

try:
    from services.database_service import get_database_service
    DATABASE_SERVICE_AVAILABLE = True
except ImportError:
    DATABASE_SERVICE_AVAILABLE = False

from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from models.camera_model import CameraModel
from config.config import app_config

class CameraService(QObject):
    """카메라 하드웨어 제어 서비스"""
    
    # 시그널 정의
    frame_captured = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, camera_model: CameraModel):
        super().__init__()
        self.model = camera_model
        self.cap = None
        self.timer = None
        self.dummy_frame = None
        self._is_debug_mode = app_config.is_debug_mode()
        
        # 시그널 연결
        self.frame_captured.connect(self._on_frame_captured)
    
    def initialize(self) -> bool:
        """카메라 서비스 초기화"""
        try:
            if self._is_debug_mode or not app_config.is_camera_enabled():
                return self._initialize_debug_camera()
            else:
                return self._initialize_real_camera()
        except Exception as e:
            error_msg = f"카메라 초기화 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _initialize_real_camera(self) -> bool:
        """실제 카메라 초기화"""
        try:
            gst_pipeline = (
                "nvarguscamerasrc ! "
                "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
                "nvvidconv flip-method=2 ! "
                "video/x-raw, format=BGRx ! "
                "videoconvert ! "
                "video/x-raw, format=BGR ! appsink max-buffers=1 drop=true"
            )
            self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if not self.cap.isOpened():
                raise Exception("실제 카메라를 열 수 없습니다.")
            
            self.model.set_initialized(True)
            print("실제 카메라 초기화 성공")
            return True
            
        except Exception as e:
            print(f"실제 카메라 초기화 실패: {str(e)}")
            # 실패시 디버그 모드로 폴백
            app_config.set_debug_mode(True)
            self._is_debug_mode = True
            return self._initialize_debug_camera()
    
    def _initialize_debug_camera(self) -> bool:
        """디버그용 가상 카메라 초기화"""
        print("디버그 모드: 가상 카메라 초기화")
        self._create_dummy_frame()
        self.model.set_initialized(True)
        return True
    
    def _create_dummy_frame(self):
        """디버그용 더미 프레임 생성"""
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # 테스트 패턴 생성
        cv2.rectangle(self.dummy_frame, (50, 50), (590, 430), (100, 100, 100), 2)
        cv2.putText(self.dummy_frame, "DEBUG MODE", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(self.dummy_frame, "Virtual Camera", (220, 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    
    def start_capture(self) -> bool:
        """캡처 시작"""
        if not self.model.is_initialized:
            return False
        
        if self.timer is None:
            self.timer = QTimer()
            if self._is_debug_mode:
                self.timer.timeout.connect(self._capture_dummy_frame)
            else:
                self.timer.timeout.connect(self._capture_real_frame)
        
        if not self.timer.isActive():
            self.timer.start(33)  # 30fps
            self.model.set_capturing(True)
        
        return True
    
    def stop_capture(self):
        """캡처 중지"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
            self.model.set_capturing(False)
    
    def _capture_real_frame(self):
        """실제 카메라에서 프레임 캡처"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame_captured.emit(frame)
    
    def _capture_dummy_frame(self):
        """디버그용 더미 프레임 캡처"""
        import time
        # 시간에 따라 변화하는 더미 프레임
        frame = self.dummy_frame.copy()
        timestamp = int(time.time() * 10) % 360
        
        # 색상 변화하는 원 추가
        color = (
            int(127 + 127 * np.sin(np.radians(timestamp))),
            int(127 + 127 * np.sin(np.radians(timestamp + 120))),
            int(127 + 127 * np.sin(np.radians(timestamp + 240)))
        )
        cv2.circle(frame, (320, 240), 20, color, -1)
        
        self.frame_captured.emit(frame)
    
    def _on_frame_captured(self, frame: np.ndarray):
        """프레임 캡처 완료 시 모델 업데이트"""
        self.model.set_frame(frame)
    
    def get_current_frame(self):
        """현재 프레임 가져오기"""
        if self._is_debug_mode or not app_config.is_camera_enabled():
            if self.dummy_frame is not None:
                return self.dummy_frame.copy()
            else:
                self._create_dummy_frame()
                return self.dummy_frame.copy()
        
        current_frame = self.model.get_current_frame()
        if current_frame is not None:
            return current_frame.copy()
        else:
            print("실제 카메라에서 프레임을 가져올 수 없습니다.")
            return None
    
    def save_image(self, filename: str, folder_path: str = "./CalthReaderResult/images") -> bool:
        """현재 프레임을 이미지로 저장"""
        try:
            # 폴더가 없으면 생성
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            # 현재 프레임 가져오기
            frame = self.get_current_frame()
            if frame is None:
                print("저장할 프레임이 없습니다.")
                return False
            
            # 파일 경로 생성
            file_path = os.path.join(folder_path, filename)
            
            # 이미지 저장
            success = cv2.imwrite(file_path, frame)
            if success:
                print(f"이미지 저장 성공: {file_path}")
                return True
            else:
                print(f"이미지 저장 실패: {file_path}")
                return False
                
        except Exception as e:
            error_msg = f"이미지 저장 오류: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def save_current_frame(self, filename: str, folder_path: str = "./CalthReaderResult/images") -> bool:
        """현재 프레임 저장"""
        current_frame = self.model.get_current_frame()
        if current_frame is None or not current_frame.is_valid:
            return False
        
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        
        try:
            success = cv2.imwrite(file_path, current_frame.frame_data)
            if success:
                print(f"이미지 저장 성공: {file_path}")
            return success
        except Exception as e:
            error_msg = f"이미지 저장 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def shutdown(self):
        """서비스 종료"""
        self.stop_capture()
        if self.cap:
            self.cap.release()
        self.model.set_initialized(False)
        print("카메라 서비스 종료")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """프레임 캡처"""
        if not self.model.is_initialized:
            return None
        
        frame = None
        try:
            if self._is_debug_mode:
                frame = self._capture_debug_frame()
            else:
                frame = self._capture_real_frame()
            
            # 데이터베이스에 이벤트 로그 기록
            if DATABASE_SERVICE_AVAILABLE and frame is not None:
                db_service = get_database_service()
                log_data = {
                    'log_level': 'INFO',
                    'module': 'camera_service',
                    'function_name': 'capture_frame',
                    'message': f'Frame captured successfully. Shape: {frame.shape}',
                    'details': {
                        'frame_shape': frame.shape,
                        'debug_mode': self._is_debug_mode,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                db_service.create_system_log(log_data)
            
            return frame
        except Exception as e:
            error_msg = f"프레임 캡처 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            
            # 에러 로그 기록
            if DATABASE_SERVICE_AVAILABLE:
                db_service = get_database_service()
                log_data = {
                    'log_level': 'ERROR',
                    'module': 'camera_service',
                    'function_name': 'capture_frame',
                    'message': error_msg,
                    'details': {'error_type': type(e).__name__}
                }
                db_service.create_system_log(log_data)
            
            return None
