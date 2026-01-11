# -*- coding: utf-8 -*-
"""
Camera Service
------------------------------------
카메라 하드웨어를 직접 제어하는 서비스 레이어입니다.

역할:
- 카메라 초기화 (실제 / 디버그)
- 프레임 캡처 루프 관리 (QTimer)
- CameraModel 에 최신 프레임 전달
- 현재 프레임 조회 및 저장

⚠️ 주의:
- CameraService는 "카메라 제어"만 담당합니다.
- 프레임 선택 / 분석 판단은 MeasurementController의 책임입니다.
"""

try:
    import cv2
except ImportError:
    print("OpenCV(cv2) not found. Camera service will work in debug mode only.")
    cv2 = None

import time
import os
import numpy as np
from datetime import datetime
from typing import Optional
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from models.camera_model import CameraModel, CameraFrame
from config.config import app_config


class CameraService(QObject):
    """
    카메라 제어 전담 서비스
    """

    # 외부에서 구독 가능한 시그널
    frame_captured = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)

    def __init__(self, camera_model: CameraModel):
        super().__init__()

        # CameraModel: 최신 프레임을 보관하는 데이터 계층
        self.model = camera_model

        # OpenCV VideoCapture 객체
        self.cap = None

        # 프레임 캡처용 타이머 (30fps)
        self.timer = None

        # 디버그용 가상 프레임
        self.dummy_frame = None

        # 디버그 모드 여부 (config 기반)
        self._is_debug_mode = app_config.is_debug_mode()

        # 프레임 수신 → 모델에 저장
        self.frame_captured.connect(self._on_frame_captured)

    # =========================================================
    # 초기화
    # =========================================================

    def initialize(self) -> bool:
        """
        카메라 서비스 초기화
        - 실제 카메라 or 디버그 카메라 선택
        """
        try:
            if self._is_debug_mode or not app_config.is_camera_enabled():
                return self._initialize_debug_camera()
            else:
                return self._initialize_real_camera()
        except Exception as e:
            self.error_occurred.emit(f"카메라 초기화 실패: {e}")
            return False

    def _initialize_real_camera(self) -> bool:
        """
        Jetson nvargus 기반 실제 카메라 초기화
        """
        gst_pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1 ! "
            "nvvidconv ! video/x-raw,format=BGRx ! "
            "videoconvert ! video/x-raw,format=BGR ! appsink"
        )

        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            raise RuntimeError("실제 카메라를 열 수 없습니다.")

        self.model.set_initialized(True)
        print("[CameraService] 실제 카메라 초기화 성공")
        return True

    def _initialize_debug_camera(self) -> bool:
        """
        디버그용 가상 카메라 초기화
        """
        print("[CameraService] DEBUG MODE 활성화")
        self._create_dummy_frame()
        self.model.set_initialized(True)
        return True

    def _create_dummy_frame(self):
        """
        디버그용 테스트 프레임 생성
        """
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(self.dummy_frame, (50, 50), (590, 430), (100, 100, 100), 2)
        cv2.putText(self.dummy_frame, "DEBUG MODE", (180, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # =========================================================
    # 캡처 루프
    # =========================================================

    def start_capture(self) -> bool:
        """
        프레임 캡처 시작 (QTimer 기반)
        """
        if not self.model.is_initialized:
            return False

        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(
                self._capture_dummy_frame if self._is_debug_mode
                else self._capture_real_frame
            )

        if not self.timer.isActive():
            self.timer.start(33)  # 약 30fps
            self.model.set_capturing(True)

        return True

    def stop_capture(self):
        """
        프레임 캡처 중지
        """
        if self.timer and self.timer.isActive():
            self.timer.stop()
            self.model.set_capturing(False)

    def _capture_real_frame(self):
        """
        실제 카메라에서 프레임 1장 읽기
        """
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.frame_captured.emit(frame)

    def _capture_dummy_frame(self):
        """
        디버그용 가상 프레임
        """
        frame = self.dummy_frame.copy()
        cv2.circle(frame, (320, 240), 20, (0, 0, 255), -1)
        self.frame_captured.emit(frame)

    def _on_frame_captured(self, frame: np.ndarray):
        """
        캡처된 프레임을 CameraModel에 저장
        """
        self.model.set_frame(frame)

    # =========================================================
    # 프레임 조회 / 저장
    # =========================================================

    def get_current_frame(self) -> Optional[CameraFrame]:
        """
        현재 CameraModel에 저장된 프레임 반환
        Returns:
            CameraFrame or None
        """
        if self._is_debug_mode:
            return CameraFrame(
                frame_data=self.dummy_frame.copy(),
                timestamp=datetime.now(),
                frame_id=0,
                is_valid=True
            )

        return self.model.get_current_frame()

    def save_current_frame(self, filename: str,
                           folder_path: str = "./CalthReaderResult/images") -> bool:
        """
        현재 프레임을 파일로 저장
        """
        frame = self.get_current_frame()

        if frame is None or not frame.is_valid:
            print("[CameraService] 저장할 프레임 없음")
            return False

        os.makedirs(folder_path, exist_ok=True)
        path = os.path.join(folder_path, filename)

        success = cv2.imwrite(path, frame.frame_data)
        if success:
            print(f"[CameraService] 이미지 저장 성공: {path}")
        return success


    def discard_frames(self, duration_sec=1.0):
        """
        AE / AWB 안정화를 위해 일정 시간 동안 프레임을 버림

        Args:
            duration_sec (float): 프레임 버릴 시간 (초)
        """
        if self._is_debug_mode:
            # 디버그 모드에서는 의미 없음
            time.sleep(duration_sec)
            return

        if not self.model.is_initialized:
            return

        start = time.time()
        while time.time() - start < duration_sec:
            if self.cap and self.cap.isOpened():
                self.cap.read()
            time.sleep(0.03)  # 약 30fps


    # =========================================================
    # 종료 / 재시작
    # =========================================================

    def shutdown(self):
        """
        카메라 서비스 종료
        """
        self.stop_capture()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.model.set_initialized(False)
        print("[CameraService] 종료 완료")
