import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)

class SettingsView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.init_ui()

    def setup_ui(self):
        """UI 설정 - UI 파일 로드"""
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'SettingsViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def connect_signals(self):
        """시그널 연결"""
        # 뒤로가기 버튼
        self.pushButton_SettingsBackArrow.clicked.connect(self.go_back)
        
        # 설정 버튼들
        self.btn_date_time.clicked.connect(self.on_date_time_clicked)
        self.btn_manage_operator.clicked.connect(self.on_manage_operator_clicked)
        self.btn_update.clicked.connect(self.on_update_clicked)
        self.btn_calibration_qc.clicked.connect(self.on_calibration_qc_clicked)
        self.btn_general_settings.clicked.connect(self.on_general_settings_clicked)
        self.btn_power_management.clicked.connect(self.on_power_management_clicked)

    def init_ui(self):
        """UI 초기화"""
        # 날짜와 시간 표시 시작
        start_date_time_update(self)
        
        # 배터리 상태 표시 시작
        start_battery_update(self)

    def go_back(self):
        """뒤로가기"""
        self.switch_to_home.emit()

    def on_date_time_clicked(self):
        """Date and Time 설정"""
        print("Date and Time 설정 클릭")
        # TODO: Date and Time 설정 화면으로 이동

    def on_manage_operator_clicked(self):
        """Manage Operator 설정"""
        print("Manage Operator 설정 클릭")
        # TODO: Operator 관리 화면으로 이동

    def on_update_clicked(self):
        """Update 설정"""
        print("Update 설정 클릭")
        # TODO: 업데이트 화면으로 이동

    def on_calibration_qc_clicked(self):
        """Calibration / QC days 설정"""
        print("Calibration / QC days 설정 클릭")
        # TODO: Calibration/QC 설정 화면으로 이동

    def on_general_settings_clicked(self):
        """General Settings"""
        print("General Settings 클릭")
        # TODO: 일반 설정 화면으로 이동

    def on_power_management_clicked(self):
        """Power Management 설정"""
        print("Power Management 설정 클릭")
        # TODO: 전원 관리 화면으로 이동

    def showEvent(self, event):
        """화면 표시시 처리"""
        super().showEvent(event)
        # 날짜/시간 및 배터리 업데이트 시작
        start_date_time_update(self)
        start_battery_update(self)

    def hideEvent(self, event):
        """화면 숨김시 처리"""
        super().hideEvent(event)
        # 날짜/시간 및 배터리 업데이트 중지
        stop_date_time_update(self)
        stop_battery_update(self)
