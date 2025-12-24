import os

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                            update_battery_status, start_battery_update, stop_battery_update)

class SettingsView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_datetime_settings = pyqtSignal()  # DateTimeSettings 화면으로 전환
    switch_to_manage_operator = pyqtSignal()  # ManageOperator 화면으로 전환
    switch_to_update_settings = pyqtSignal()  # UpdateSettings 화면으로 전환
    switch_to_calibration_qc_settings = pyqtSignal()  # CalibrationQCSettings 화면으로 전환
    switch_to_general_settings = pyqtSignal()  # GeneralSettings 화면으로 전환
    switch_to_power_management = pyqtSignal()  # PowerManagement 화면으로 전환

    def __init__(self, parent=None):
        super().__init__(parent)

        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'SettingsViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Settings', ui_filename)
        
        # UI 파일 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        self.init_ui()

    def init_ui(self):
        """UI 초기화 및 이벤트 연결"""
        # 뒤로 가기 버튼 연결
        self.pushButton_SettingsBackArrow.clicked.connect(self.on_back_button_clicked)
        
        # 설정 버튼들 이벤트 연결
        self.btn_date_time.clicked.connect(self.on_date_time_clicked)
        self.btn_manage_operator.clicked.connect(self.on_manage_operator_clicked)
        self.btn_update.clicked.connect(self.on_update_clicked)
        self.btn_calibration_qc.clicked.connect(self.on_calibration_qc_clicked)
        self.btn_general_settings.clicked.connect(self.on_general_settings_clicked)
        self.btn_power_management.clicked.connect(self.on_power_management_clicked)

        # 초기 날짜와 시간 설정
        self.update_date_time()

    def on_date_time_clicked(self):
        """Date and Time 버튼 클릭"""
        print("Date and Time 설정이 클릭되었습니다.")
        self.switch_to_datetime_settings.emit()
    
    def on_manage_operator_clicked(self):
        """Manage Operator 버튼 클릭"""
        print("Manage Operator가 클릭되었습니다.")
        self.switch_to_manage_operator.emit()
    
    def on_update_clicked(self):
        """Update 버튼 클릭"""
        print("Update가 클릭되었습니다.")
        self.switch_to_update_settings.emit()
    
    def on_calibration_qc_clicked(self):
        """Calibration / QC days 버튼 클릭"""
        print("Calibration / QC days가 클릭되었습니다.")
        self.switch_to_calibration_qc_settings.emit()
    
    def on_general_settings_clicked(self):
        """General Settings 버튼 클릭"""
        print("General Settings가 클릭되었습니다.")
        self.switch_to_general_settings.emit()
    
    def on_power_management_clicked(self):
        """Power Management 버튼 클릭"""
        print("Power Management가 클릭되었습니다.")
        self.switch_to_power_management.emit()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)
        stop_battery_update(self)

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def update_date_time(self):
        update_date_time(self)
