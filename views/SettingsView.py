import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore    import pyqtSignal, QTimer
from PyQt5           import uic

from views.Utils     import update_date_time, start_date_time_update, stop_date_time_update

class SettingsView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'SettingsViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 뒤로 가기 버튼 연결
        self.pushButton_SettingsBackArrow.clicked.connect(self.on_back_button_clicked)

        # 초기 날짜와 시간 설정
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def update_date_time(self):
        update_date_time(self)
