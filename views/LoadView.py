import json
import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5 import uic
from backend.camera_manager import CameraManager
from backend.uart_manager import UARTManager


class LoadView(QMainWindow):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
         # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'LoadViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")       
        
        # ProgressBar 스타일 설정
        progress_bar_style = """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 10px;
                text-align: center;
                color: gray;
                font-size: 12pt;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #4A4A6A;
                border-radius: 8px;
            }
        """
        self.progressBar.setStyleSheet(progress_bar_style)
        
        # ProgressBar에 숫자로 진행률 표시
        self.progressBar.setFormat("%p%")
        self.progressBar.setAlignment(Qt.AlignCenter)
        
        # ProgressBar의 텍스트 표시 활성화
        self.progressBar.setTextVisible(True)

        # 프로그레스바 초기화
        self.progressBar.setValue(0)
        
        # 카메라 초기화 상태
        self.camera_initialized = False
        
        # info.json에서 버전 정보 읽기 및 표시
        self.display_version()
        
        # 카메라 초기화 시작 (로딩 시작하자마자)
        self.init_camera()
        
        # UART 초기화
        self.init_uart()
        
        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)  # 50ms 간격으로 업데이트
        
        self.progress_value = 0

    def init_camera(self):
        """카메라 초기화"""
        try:
            camera = CameraManager()
            camera.init_camera()
            camera.start_capture()
            self.camera_initialized = True
            print("카메라 초기화 성공")
            
        except Exception as e:
            self.camera_initialized = False
            QMessageBox.critical(self, "카메라 초기화 실패", f"카메라를 초기화할 수 없습니다.\n\n오류: {str(e)}")
            print(f"카메라 초기화 실패: {str(e)}")

    def init_uart(self):
        """UART 초기화"""
        try:
            uart = UARTManager()
            uart.init_uart()
            print("UART 초기화 성공")
        except Exception as e:
            QMessageBox.critical(self, "UART 초기화 실패", f"UART를 초기화할 수 없습니다.\n\n오류: {str(e)}")
            print(f"UART 초기화 실패: {str(e)}")

    def update_progress(self):
        self.progress_value += 1
        self.progressBar.setValue(self.progress_value)
        
        if self.progress_value >= 100:
            self.timer.stop()
            self.finished.emit()

    def display_version(self):
        version = self.get_version_from_info()
        self.label_Version.setText(f"ver {version}")

    def get_version_from_info(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            info_path = os.path.join(current_dir, '../info', 'info.json')
            
            with open(info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            return info.get('version', 'Unknown')
        except Exception as e:
            print(f"Error reading version from info.json: {str(e)}")
            return "Unknown"
    
    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)
