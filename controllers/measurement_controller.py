# -*- coding: utf-8 -*-
"""
Measurement Controller - 측정 프로세스 제어
"""
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from controllers.system_controller import app_controller
from datetime import datetime

class MeasurementController(QObject):
    """측정 프로세스 컨트롤러"""
    
    # 시그널 정의
    measurement_started = pyqtSignal()
    measurement_finished = pyqtSignal(dict)  # 측정 결과
    progress_updated = pyqtSignal(int, str)  # 진행률, 현재 단계
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.timer = None
        self.elapsed_time = 0
        self.total_time = 5000  # 5초
        self.current_phase = 0
        self.phase_start_time = 0
        self.is_measuring = False
        
        # 측정 단계 정의
        self.measurement_phases = [
            {"name": "LED 켜기", "duration": 1000, "action": self._phase_led_on},
            {"name": "카메라 캡처", "duration": 2000, "action": self._phase_capture},
            {"name": "이미지 분석", "duration": 1500, "action": self._phase_analysis},
            {"name": "LED 끄기", "duration": 500, "action": self._phase_led_off}
        ]
    
    def start_measurement(self):
        """측정 시작"""
        if self.is_measuring:
            return False
        
        try:
            print("측정 프로세스 시작")
            self.is_measuring = True
            self.elapsed_time = 0
            self.current_phase = 0
            self.phase_start_time = 0
            
            # 카메라 캡처 시작
            app_controller.start_camera_capture()
            
            # 타이머 시작
            if self.timer is None:
                self.timer = QTimer()
                self.timer.timeout.connect(self._update_measurement)
            
            self.timer.start(50)  # 50ms마다 업데이트
            self._execute_current_phase()
            
            self.measurement_started.emit()
            return True
            
        except Exception as e:
            error_msg = f"측정 시작 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _update_measurement(self):
        """측정 진행률 업데이트"""
        self.elapsed_time += 50
        
        # 현재 단계가 완료되었는지 확인
        if self.current_phase < len(self.measurement_phases):
            current_phase_duration = self.measurement_phases[self.current_phase]['duration']
            phase_elapsed = self.elapsed_time - self.phase_start_time
            
            if phase_elapsed >= current_phase_duration:
                self.current_phase += 1
                self.phase_start_time = self.elapsed_time
                if self.current_phase < len(self.measurement_phases):
                    self._execute_current_phase()
        
        # 전체 진행률 계산
        progress = min(100, int(self.elapsed_time / self.total_time * 100))
        
        # 현재 단계 이름
        if self.current_phase < len(self.measurement_phases):
            phase_name = self.measurement_phases[self.current_phase]['name']
        else:
            phase_name = "완료"
        
        self.progress_updated.emit(progress, phase_name)
        
        # 측정 완료 확인
        if self.elapsed_time >= self.total_time:
            self._finish_measurement()
    
    def _execute_current_phase(self):
        """현재 측정 단계 실행"""
        if self.current_phase >= len(self.measurement_phases):
            return
        
        phase = self.measurement_phases[self.current_phase]
        print(f"측정 단계 실행: {phase['name']}")
        
        try:
            # 단계별 액션 실행
            phase['action']()
        except Exception as e:
            error_msg = f"측정 단계 '{phase['name']}' 실행 실패: {str(e)}"
            self.error_occurred.emit(error_msg)
    
    def _phase_led_on(self):
        """1단계: LED 켜기"""
        success = app_controller.led_on(45)
        if not success:
            print("LED 켜기 실패 (디버그 모드에서는 정상)")
    
    def _phase_capture(self):
        """2단계: 카메라 캡처"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"measurement_{timestamp}.jpg"
        
        success = app_controller.capture_image(filename)
        if success:
            print(f"이미지 캡처 완료: {filename}")
            self.captured_filename = filename
        else:
            print("이미지 캡처 실패 (디버그 모드에서는 정상)")
            self.captured_filename = None
    
    def _phase_analysis(self):
        """3단계: 이미지 분석 (시뮬레이션)"""
        # 실제 구현에서는 여기서 이미지 분석 알고리즘 실행
        print("이미지 분석 시뮬레이션...")
        
        # 가상의 분석 결과 생성
        import random
        self.analysis_result = {
            'positive': random.choice([True, False]),
            'confidence': random.uniform(0.7, 0.99),
            'detected_lines': random.randint(1, 3)
        }
    
    def _phase_led_off(self):
        """4단계: LED 끄기"""
        success = app_controller.led_off()
        if not success:
            print("LED 끄기 실패 (디버그 모드에서는 정상)")
    
    def _finish_measurement(self):
        """측정 완료"""
        if self.timer:
            self.timer.stop()
        
        self.is_measuring = False
        
        # 최종 LED 끄기 (안전장치)
        app_controller.led_off()
        
        # 측정 결과 생성
        measurement_result = {
            'timestamp': datetime.now(),
            'duration': self.elapsed_time / 1000.0,  # 초 단위
            'captured_image': getattr(self, 'captured_filename', None),
            'analysis_result': getattr(self, 'analysis_result', None),
            'success': True
        }
        
        print("측정 프로세스 완료")
        self.measurement_finished.emit(measurement_result)
    
    def stop_measurement(self):
        """측정 중지"""
        if not self.is_measuring:
            return
        
        if self.timer:
            self.timer.stop()
        
        self.is_measuring = False
        
        # LED 끄기
        app_controller.led_off()
        
        print("측정 프로세스 중지됨")
    
    def get_current_progress(self) -> dict:
        """현재 진행 상황 반환"""
        progress = min(100, int(self.elapsed_time / self.total_time * 100))
        
        if self.current_phase < len(self.measurement_phases):
            phase_name = self.measurement_phases[self.current_phase]['name']
        else:
            phase_name = "완료"
        
        return {
            'progress': progress,
            'current_phase': phase_name,
            'elapsed_time': self.elapsed_time,
            'is_measuring': self.is_measuring
        }

# 전역 측정 컨트롤러 인스턴스
measurement_controller = MeasurementController()
