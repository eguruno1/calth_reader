import cv2
from PyQt5.QtCore import QTimer
import os
import numpy as np
from config.config import app_config

class CameraManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def init_camera(self):
        """카메라 초기화"""
        if self._initialized:
            return True
        
        # 디버그 모드일 경우 가상 카메라 사용
        if app_config.is_debug_mode() or not app_config.is_camera_enabled():
            print("디버그 모드: 가상 카메라 사용")
            self._create_dummy_frame()
            self.latest_frame = self.dummy_frame.copy()
            self.timer = None
            self._initialized = True
            return True
            
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
                print("하드웨어 카메라 연결 실패, 디버그 모드로 전환")
                app_config.set_debug_mode(True)
                return self.init_camera()  # 디버그 모드로 재시도
            
            self.latest_frame = None
            self.timer = None
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"카메라 초기화 실패, 디버그 모드로 전환: {str(e)}")
            app_config.set_debug_mode(True)
            return self.init_camera()  # 디버그 모드로 재시도
    
    def _create_dummy_frame(self):
        """디버그용 더미 프레임 생성"""
        self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # 간단한 테스트 패턴 생성
        cv2.rectangle(self.dummy_frame, (50, 50), (590, 430), (100, 100, 100), 2)
        cv2.putText(self.dummy_frame, "DEBUG MODE", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(self.dummy_frame, "Virtual Camera", (220, 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

    def start_capture(self):
        """카메라 캡처 시작"""
        if not self._initialized:
            return False
        
        # 디버그 모드일 경우 더미 프레임 업데이트 타이머 시작
        if app_config.is_debug_mode() or not app_config.is_camera_enabled():
            if self.timer is None:
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_dummy_frame)
            self.timer.start(33)  # 30fps
            return True
            
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_frame)
        
        self.timer.start(33)  # 30fps
        return True

    def update_frame(self):
        """프레임 업데이트"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.latest_frame = frame
    
    def update_dummy_frame(self):
        """디버그용 더미 프레임 업데이트"""
        import time
        # 시간에 따라 약간씩 변화하는 더미 프레임 생성
        frame = self.dummy_frame.copy()
        timestamp = int(time.time() * 10) % 360
        color = (
            int(127 + 127 * np.sin(np.radians(timestamp))),
            int(127 + 127 * np.sin(np.radians(timestamp + 120))),
            int(127 + 127 * np.sin(np.radians(timestamp + 240)))
        )
        cv2.circle(frame, (320, 240), 20, color, -1)
        self.latest_frame = frame

    def get_current_frame(self):
        """현재 프레임 가져오기"""
        return self.latest_frame

    def save_image(self, filename, folder_path="./CalthReaderResult/images"):
        """현재 프레임을 이미지로 저장"""
        if self.latest_frame is None:
            return False
            
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        return cv2.imwrite(file_path, self.latest_frame)

    def close(self):
        """카메라 종료"""
        if self.timer:
            self.timer.stop()
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        self._initialized = False
