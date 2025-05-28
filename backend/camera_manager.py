import cv2
from PyQt5.QtCore import QTimer
import os

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
                raise Exception("카메라를 열 수 없습니다.")
            
            self.latest_frame = None
            self.timer = None
            self._initialized = True
            return True
            
        except Exception as e:
            self._initialized = False
            raise Exception(f"카메라 초기화 실패: {str(e)}")

    def start_capture(self):
        """카메라 캡처 시작"""
        if not self._initialized:
            return False
            
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
        if self.cap:
            self.cap.release()
        self._initialized = False
