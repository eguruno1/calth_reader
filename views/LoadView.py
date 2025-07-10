import json
import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5 import uic
from controllers import app_controller


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
        
        # 애플리케이션 컨트롤러 초기화 상태 체크
        self.initialization_complete = False
        
        # info.json에서 버전 정보 읽기 및 표시
        self.display_version()
        
        # 애플리케이션 컨트롤러 시그널 연결
        app_controller.initialization_complete.connect(self.on_initialization_complete)
        app_controller.system_ready.connect(self.on_system_ready)
        
        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)  # 50ms 간격으로 업데이트
        
        self.progress_value = 0

    def on_initialization_complete(self):
        """애플리케이션 초기화 완료 시 호출"""
        self.initialization_complete = True
        print("애플리케이션 초기화 완료")
        
    def on_system_ready(self, ready):
        """시스템 준비 상태 변경 시 호출"""
        if ready:
            print("시스템 준비 완료")
        else:
            print("시스템 일부 제한 모드")

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
