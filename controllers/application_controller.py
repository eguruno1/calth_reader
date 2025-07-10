# -*- coding: utf-8 -*-
"""
Application Controller - 애플리케이션 전체 제어
MVC 패턴의 메인 컨트롤러
"""
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from models import ApplicationModel, CameraModel, UARTModel, SystemStatus
from services import CameraService, UARTService
from config.config import app_config

class ApplicationController(QObject):
    """애플리케이션 메인 컨트롤러"""
    
    # 시그널 정의
    system_ready = pyqtSignal(bool)
    initialization_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 모델 생성
        self.app_model = ApplicationModel()
        self.camera_model = CameraModel()
        self.uart_model = UARTModel()
        
        # 서비스 생성
        self.camera_service = CameraService(self.camera_model)
        self.uart_service = UARTService(self.uart_model)
        
        # 시그널 연결
        self._connect_signals()
        
        # 옵저버 등록
        self.app_model.add_observer(self)
        self.camera_model.add_observer(self)
        self.uart_model.add_observer(self)
    
    def _connect_signals(self):
        """시그널 연결"""
        # 서비스 시그널 연결
        self.camera_service.error_occurred.connect(self._on_camera_error)
        self.uart_service.error_occurred.connect(self._on_uart_error)
        self.uart_service.connection_changed.connect(self._on_uart_connection_changed)
    
    def initialize(self):
        """애플리케이션 초기화"""
        try:
            self.app_model.set_system_status(SystemStatus.INITIALIZING)
            self.status_changed.emit("시스템 초기화 중...")
            
            # 설정 동기화
            self.app_model.set_debug_mode(app_config.is_debug_mode())
            
            # 서비스 초기화를 별도 타이머로 실행 (UI 블로킹 방지)
            QTimer.singleShot(500, self._initialize_services)
            
        except Exception as e:
            error_msg = f"애플리케이션 초기화 실패: {str(e)}"
            self.app_model.add_error(error_msg, "initialization")
            self.error_occurred.emit(error_msg)
    
    def _initialize_services(self):
        """서비스들 초기화"""
        try:
            # 카메라 서비스 초기화
            camera_success = self.camera_service.initialize()
            if camera_success:
                self.status_changed.emit("카메라 초기화 완료")
            else:
                self.app_model.add_warning("카메라 초기화 실패 - 디버그 모드 사용")
            
            # UART 서비스 초기화
            uart_success = self.uart_service.initialize()
            if uart_success:
                self.status_changed.emit("UART 초기화 완료")
            else:
                self.app_model.add_warning("UART 초기화 실패 - 디버그 모드 사용")
            
            # 시스템 상태 업데이트
            if camera_success and uart_success:
                self.app_model.set_system_status(SystemStatus.READY)
                self.status_changed.emit("시스템 준비 완료")
                self.system_ready.emit(True)
            else:
                self.app_model.set_system_status(SystemStatus.READY)  # 디버그 모드에서도 준비 상태
                self.status_changed.emit("제한된 기능으로 시스템 준비 완료")
                self.system_ready.emit(True)
            
            self.initialization_complete.emit()
            
        except Exception as e:
            error_msg = f"서비스 초기화 실패: {str(e)}"
            self.app_model.add_error(error_msg, "service_initialization")
            self.app_model.set_system_status(SystemStatus.ERROR)
            self.error_occurred.emit(error_msg)
    
    def toggle_debug_mode(self):
        """디버그 모드 토글"""
        current_mode = self.app_model.settings.debug_mode
        new_mode = not current_mode
        
        self.app_model.set_debug_mode(new_mode)
        app_config.set_debug_mode(new_mode)
        
        mode_text = "디버그 모드" if new_mode else "실제 하드웨어 모드"
        self.status_changed.emit(f"{mode_text}로 변경됨 (재시작 필요)")
    
    def start_camera_capture(self) -> bool:
        """카메라 캡처 시작"""
        if self.camera_service.start_capture():
            self.app_model.set_system_status(SystemStatus.RUNNING)
            return True
        return False
    
    def stop_camera_capture(self):
        """카메라 캡처 중지"""
        self.camera_service.stop_capture()
    
    def capture_image(self, filename: str) -> bool:
        """이미지 캡처"""
        success = self.camera_service.save_current_frame(filename)
        if success:
            self.app_model.update_performance_metric("images_captured", 
                self.app_model.performance_metrics.get("images_captured", {}).get("value", 0) + 1)
        return success
    
    def set_led_brightness(self, brightness: int) -> bool:
        """LED 밝기 설정"""
        return self.uart_service.set_led_brightness(brightness)
    
    def led_on(self, brightness: int = 45) -> bool:
        """LED 켜기"""
        return self.uart_service.led_on(brightness)
    
    def led_off(self) -> bool:
        """LED 끄기"""
        return self.uart_service.led_off()
    
    def get_system_info(self) -> dict:
        """시스템 정보 반환"""
        return {
            'app_status': self.app_model.get_system_status_info(),
            'camera_info': self.camera_model.get_info(),
            'uart_info': self.uart_model.get_info(),
            'performance': self.app_model.get_performance_summary(),
            'recent_errors': self.app_model.get_recent_errors(5)
        }
    
    def shutdown(self):
        """애플리케이션 종료"""
        try:
            self.app_model.set_system_status(SystemStatus.SHUTDOWN)
            self.status_changed.emit("시스템 종료 중...")
            
            # 서비스 종료
            self.camera_service.shutdown()
            self.uart_service.shutdown()
            
            self.status_changed.emit("시스템 종료 완료")
            
        except Exception as e:
            error_msg = f"시스템 종료 중 오류: {str(e)}"
            self.app_model.add_error(error_msg, "shutdown")
    
    # 옵저버 메서드들
    def on_app_event(self, event_type: str, data):
        """애플리케이션 모델 이벤트 처리"""
        if event_type == 'debug_mode_changed':
            print(f"디버그 모드 변경: {data['new_mode']}")
        elif event_type == 'system_status_changed':
            print(f"시스템 상태 변경: {data['new_status'].value}")
    
    def on_camera_event(self, event_type: str, data):
        """카메라 모델 이벤트 처리"""
        if event_type == 'frame_updated':
            # 프레임 업데이트 성능 지표
            self.app_model.update_performance_metric("frames_processed", 
                self.app_model.performance_metrics.get("frames_processed", {}).get("value", 0) + 1)
    
    def on_uart_event(self, event_type: str, data):
        """UART 모델 이벤트 처리"""
        if event_type == 'led_changed':
            # LED 변경 성능 지표
            self.app_model.update_performance_metric("led_commands", 
                self.app_model.performance_metrics.get("led_commands", {}).get("value", 0) + 1)
    
    def _on_camera_error(self, error_message: str):
        """카메라 오류 처리"""
        self.app_model.add_error(f"카메라 오류: {error_message}", "camera")
    
    def _on_uart_error(self, error_message: str):
        """UART 오류 처리"""
        self.app_model.add_error(f"UART 오류: {error_message}", "uart")
    
    def _on_uart_connection_changed(self, connected: bool):
        """UART 연결 상태 변경"""
        status = "연결됨" if connected else "연결 해제됨"
        self.status_changed.emit(f"UART {status}")

# 전역 컨트롤러 인스턴스
app_controller = ApplicationController()
