# -*- coding: utf-8 -*-
"""
Measurement Controller - 측정 프로세스 제어
"""
import os
import time
import cv2
import json
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from controllers.system_controller import app_controller
from datetime import datetime

from analysis.analyzer import Analyzer # ✅ 추가
from analysis.focus import focus_score
from analysis.utils import draw_result_boxes, create_thumbnail

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

        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        # TestInfoView 정보를 json에서 읽는다.
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        # ✅ 추가
        self.select_menu = None
        self.test_type = None
        self.analysis_result = None
        self.captured_frame = None   # 🔥 최종 선택된 프레임
        self.test_session_id = None  # DB
        
        # 측정 단계 정의
        self.measurement_phases = [
            {"name": "LED 켜기", "duration": 1000, "action": self._phase_led_on},
            {"name": "카메라 캡처", "duration": 2000, "action": self._phase_capture},
            #{"name": "이미지 분석", "duration": 1500, "action": self._phase_analysis},
            {"name": "이미지 분석", "duration": 4000, "action": self._phase_analysis},
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
        """
        2단계: 카메라 캡처
        test_3line_auto 기반 최적 프레임 획득
        """
        print("[MeasurementController] 최적 프레임 선택 시작")
        # LED ON 이후 ISP 안정화 대기
        # print("[MeasurementController] LED ON")
        # app_controller.led_on(45)
        # time.sleep(1.0)

        #print("[MeasurementController] Restart camera after LED ON")
        #app_controller.camera_service.restart_camera()
        #time.sleep(1.5)

        # ✅ AE 안정화 대기
        #print("[MeasurementController] Waiting for AE stabilization...")
        #app_controller.camera_service.discard_frames(duration_sec=2.0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"measurement_{timestamp}.jpg"
        save_dir = "./CalthReaderResult/images"
        os.makedirs(save_dir, exist_ok=True)

        # 🔥 핵심: 최적 프레임 선택
        best_frame = self._select_best_frame()   # np.ndarray

        if best_frame is None:
            raise RuntimeError("카메라 캡처 실패: 유효한 프레임이 없습니다.")

        # 🔥 MeasurementController가 직접 저장
        image_path = os.path.join(save_dir, filename)
        cv2.imwrite(image_path, best_frame)

        self.captured_frame = best_frame
        self.captured_filename = filename
        self.captured_image_path = image_path

        print(f"[MeasurementController] 이미지 캡처 완료: {filename}")
    
    def _phase_analysis(self):
        """3단계: 이미지 분석 (시뮬레이션)"""
        # 실제 구현에서는 여기서 이미지 분석 알고리즘 실행
        print("_phase_analysis : 이미지 분석 알고리즘 실행...")

        """
        test_3line_auto 기반 실제 분석 Phase
        """
        current_data = self._load_current_json()
        self.select_menu = current_data.get("select_menu")
        self.test_type = current_data.get("test_type1")

        print(f"[MeasurementController] test_type: {self.test_type}")

        if self.captured_frame is None:
            raise RuntimeError("분석할 프레임이 없습니다.")

        analysis = Analyzer.analyze(self.captured_frame, self.test_type)

        if analysis is None:
            raise RuntimeError("이미지 분석 실패: Analyzer 결과가 None 입니다.")

        if not isinstance(analysis, dict):
            raise RuntimeError("이미지 분석 실패: 잘못된 결과 형식")

        mode = analysis.get("mode")
        line_count = analysis.get("line_count")
        metrics = analysis.get("metrics") or {}

        if mode is None or line_count is None:
            raise RuntimeError("분석 결과 형식이 올바르지 않습니다.")

        """
        positive = (
            analysis["line_count"] >= 2
            if analysis["mode"] == 2
            else analysis["line_count"] >= 1
        )
        """
        
        # -------------------------------------------------
        # 🔧 FIX: 진단 모드별 positive 판정 기준 명확화
        #  - mode 2 (C/T): 정확히 2라인 검출 시 positive
        #  - mode 3 (L1/L2/L3): 정확히 3라인 검출 시 positive
        # -------------------------------------------------
        if analysis["mode"] == 2:
            positive = (analysis["line_count"] == 2)
        elif analysis["mode"] == 3:
            positive = (analysis["line_count"] == 3)
        else:
            positive = False

        self.analysis_result = {
            "positive": positive,
            "mode": mode,
            "line_count": line_count,
            "metrics": metrics,
        }

        # ===============================
        # 결과 박스 이미지 생성
        # ===============================
        boxes = analysis.get("boxes", [])
        metrics = analysis.get("metrics", {}).get("lines", [])

        if boxes and metrics:
            # ▶ 박스가 있는 경우만 박스 렌더링
            result_img = draw_result_boxes(
                self.captured_frame,
                boxes,
                metrics
            )
        else:
            # ▶ 반응라인이 없는 경우: 원본 이미지 그대로 사용
            result_img = self.captured_frame.copy()
            #self.result_image_path = None
            #self.thumbnail_path = None

        # QC Test 만 파일명에 명시
        if self.select_menu == "QCTest":
            self.captured_filename = f"QC_{self.captured_filename}"

        # 결과 이미지 저장
        base, ext = os.path.splitext(self.captured_filename)
        result_filename = base + "_result.jpg"
        result_path = os.path.join(
            os.path.dirname(self.captured_image_path),
            result_filename
        )

        cv2.imwrite(result_path, result_img)
        self.result_image_path = result_path

        # ===============================
        # 썸네일 생성
        # ===============================
        thumb = create_thumbnail(result_img, width=320)
        thumb_filename = base + "_thumb.jpg"
        thumb_path = os.path.join(
            os.path.dirname(self.captured_image_path),
            thumb_filename
        )

        cv2.imwrite(thumb_path, thumb)
        self.thumbnail_path = thumb_path    

        
        # 가상의 분석 결과 생성
        """
        import random
        self.analysis_result = {
            'positive': random.choice([True, False]),
            'confidence': random.uniform(0.7, 0.99),
            'detected_lines': random.randint(1, 3)
        }
        """

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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": self.elapsed_time / 1000.0,
            "captured_image": self.captured_filename,
            "result_image": getattr(self, "result_image_path", None),
            "thumbnail_image": getattr(self, "thumbnail_path", None),
            "analysis_result": self.analysis_result,
            "success": True
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
    
    ###################################################
    # 최적 프레임 선택
    ###################################################
    def _select_best_frame(self, sample_count=10):
        """
        camera_service가 관리하는 최신 프레임 중
        focus score 기준 최적 프레임 선택
        """
        best_focus = -1.0
        best_frame = None

        #warm-up discard도 추가 가능
        for _ in range(5):
            app_controller.camera_service.get_current_frame()
            time.sleep(0.05)

        for i in range(sample_count):
            cam_frame = app_controller.camera_service.get_current_frame()

            if cam_frame is None or not cam_frame.is_valid:
                time.sleep(0.05)
                continue

            img = cam_frame.frame_data
            if img is None:
                time.sleep(0.05)
                continue

            mean_val = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
            if mean_val > 245:
                print("[WARN] Frame overexposed, skipping")
                continue

            # focus 계산
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            focus = cv2.Laplacian(gray, cv2.CV_64F).var()

            print(f"[DEBUG] frame {i} focus={focus:.2f}")

            if focus > best_focus:
                best_focus = focus
                best_frame = img.copy()  # ✅ 최종 선택 시점에서만 copy

            time.sleep(0.05)

        if best_frame is None:
            raise RuntimeError("유효한 프레임을 획득하지 못했습니다.")

        print(f"[MeasurementController] Best focus score: {best_focus:.2f}")
        return best_frame


    def _load_current_json(self):
        """
        TestInofView 에서 입력한 정보(json) 값을 다시 로드. 
        """
        try:
            if not os.path.exists(self.current_json_path):
                print("[MeasurementController] current.json not found")
                return {}

            with open(self.current_json_path, "r") as f:
                return json.load(f)

        except Exception as e:
            print(f"[MeasurementController] current.json load error: {e}")
            return {} 

# 전역 측정 컨트롤러 인스턴스
measurement_controller = MeasurementController()
