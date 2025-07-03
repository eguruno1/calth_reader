# -*- coding: utf-8 -*-
"""
Backend Service Manager
백엔드 서비스들을 통합 관리하는 클래스
"""
from PyQt5.QtCore import QObject, pyqtSignal
from backend.camera_manager import CameraManager
from backend.uart_manager import UARTManager
from config.config import app_config

class BackendManager(QObject):
    """백엔드 서비스들을 통합 관리하는 클래스"""
    
    # 시그널 정의
    camera_initialized = pyqtSignal(bool)
    uart_initialized = pyqtSignal(bool)
    system_ready = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackendManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            super().__init__()
            self.camera_manager = None
            self.uart_manager = None
            self._camera_ready = False
            self._uart_ready = False
            self._initialized = True
    
    def initialize_all(self):
        """모든 백엔드 서비스 초기화"""
        try:
            # 카메라 매니저 초기화
            self.camera_manager = CameraManager()
            self._camera_ready = self.camera_manager.init_camera()
            self.camera_initialized.emit(self._camera_ready)
            
            if not self._camera_ready and not app_config.is_debug_mode():
                self.error_occurred.emit("카메라 초기화 실패")
            
            # UART 매니저 초기화
            self.uart_manager = UARTManager()
            self._uart_ready = self.uart_manager.init_uart()
            self.uart_initialized.emit(self._uart_ready)
            
            if not self._uart_ready and not app_config.is_debug_mode():
                self.error_occurred.emit("UART 초기화 실패")
            
            # 시스템 준비 상태 확인
            system_ready = self._camera_ready and self._uart_ready
            self.system_ready.emit(system_ready)
            
            if app_config.is_debug_mode():
                print("백엔드 초기화 완료 (디버그 모드)")
            else:
                print("백엔드 초기화 완료 (실제 하드웨어)")
            
            return system_ready
            
        except Exception as e:
            error_msg = f"백엔드 초기화 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            print(error_msg)
            return False
    
    def get_camera_manager(self):
        """카메라 매니저 인스턴스 반환"""
        return self.camera_manager
    
    def get_uart_manager(self):
        """UART 매니저 인스턴스 반환"""
        return self.uart_manager
    
    def is_camera_ready(self):
        """카메라 준비 상태 반환"""
        return self._camera_ready
    
    def is_uart_ready(self):
        """UART 준비 상태 반환"""
        return self._uart_ready
    
    def is_system_ready(self):
        """전체 시스템 준비 상태 반환"""
        return self._camera_ready and self._uart_ready
    
    def start_camera_capture(self):
        """카메라 캡처 시작"""
        if self.camera_manager and self._camera_ready:
            return self.camera_manager.start_capture()
        return False
    
    def stop_camera_capture(self):
        """카메라 캡처 정지"""
        if self.camera_manager:
            self.camera_manager.close()
    
    def get_current_frame(self):
        """현재 카메라 프레임 가져오기"""
        if self.camera_manager and self._camera_ready:
            return self.camera_manager.get_current_frame()
        return None
    
    def save_image(self, filename, folder_path="./CalthReaderResult/images"):
        """현재 프레임을 이미지로 저장"""
        if self.camera_manager and self._camera_ready:
            return self.camera_manager.save_image(filename, folder_path)
        return False
    
    def set_led_brightness(self, brightness):
        """LED 밝기 설정"""
        if self.uart_manager and self._uart_ready:
            return self.uart_manager.set_led_brightness(brightness)
        return False
    
    def led_on(self, brightness=45):
        """LED 켜기"""
        if self.uart_manager and self._uart_ready:
            return self.uart_manager.led_on(brightness)
        return False
    
    def led_off(self):
        """LED 끄기"""
        if self.uart_manager and self._uart_ready:
            return self.uart_manager.led_off()
        return False
    
    def shutdown(self):
        """모든 백엔드 서비스 종료"""
        try:
            if self.camera_manager:
                self.camera_manager.close()
            
            if self.uart_manager:
                self.uart_manager.close()
            
            print("백엔드 서비스 종료 완료")
            
        except Exception as e:
            error_msg = f"백엔드 종료 중 오류: {str(e)}"
            print(error_msg)
    
    def get_status_info(self):
        """시스템 상태 정보 반환"""
        return {
            'debug_mode': app_config.is_debug_mode(),
            'camera_enabled': app_config.is_camera_enabled(),
            'uart_enabled': app_config.is_uart_enabled(),
            'camera_ready': self._camera_ready,
            'uart_ready': self._uart_ready,
            'system_ready': self.is_system_ready()
        }

# 전역 백엔드 매니저 인스턴스
backend_manager = BackendManager()
