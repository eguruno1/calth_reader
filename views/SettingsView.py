import os
import json
import threading

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update)

from controllers import app_controller

class SettingsView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_datetime_settings = pyqtSignal()  # DateTimeSettings 화면으로 전환
    switch_to_manage_operator = pyqtSignal()  # ManageOperator 화면으로 전환
    switch_to_update_settings = pyqtSignal()  # UpdateSettings 화면으로 전환
    switch_to_calibration_qc_settings = pyqtSignal()  # CalibrationQCSettings 화면으로 전환
    switch_to_general_settings = pyqtSignal()  # GeneralSettings 화면으로 전환
    switch_to_power_management = pyqtSignal()  # PowerManagement 화면으로 전환
    switch_to_info = pyqtSignal()  # Info 화면으로 전환

    def __init__(self, parent=None, uart_model=None):
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

        # 배터리
        self.uart_model = uart_model
        print(f"[SettingsView] uart_model injected: {self.uart_model}")

    def init_ui(self):
        """UI 초기화 및 이벤트 연결"""
        # 뒤로 가기 버튼 연결
        self.pushButton_SettingsBackArrow.clicked.connect(self.on_back_button_clicked)
        
        # 설정 버튼들 이벤트 연결
        self.btn_date_time.clicked.connect(self.on_date_time_clicked)
        self.btn_manage_operator.clicked.connect(self.on_manage_operator_clicked)
        self.btn_update.clicked.connect(self.on_update_clicked)
        self.btn_general_settings.clicked.connect(self.on_general_settings_clicked)
        # 인증을 위해 UI 삭제
        # self.btn_calibration_qc.clicked.connect(self.on_calibration_qc_clicked)
        # self.btn_power_management.clicked.connect(self.on_power_management_clicked)

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
        #self.switch_to_general_settings.emit()
        self.switch_to_info.emit()
    
    def on_power_management_clicked(self):
        """Power Management 버튼 클릭"""
        print("Power Management가 클릭되었습니다.")
        self.switch_to_power_management.emit()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

        # 배터리 상태 업데이트
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)

    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def update_date_time(self):
        update_date_time(self)

    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[SettingsView] on_uart_event: {event_type}, {data}")
        print(
            f"[SettingsView][{self.__class__.__name__}] on_uart_event "
            f"thread={threading.current_thread().name}"
        )

        # 배터리 (기존)
        if event_type == "battery_changed" and data:
            # ❗ UART RX 스레드 → UI 스레드로 전달
            QMetaObject.invokeMethod(
                self,
                "_update_battery_ui",
                Qt.QueuedConnection,
                Q_ARG(object, data)
            )

    @pyqtSlot(object)
    def _update_battery_ui(self, battery_info):
        if not hasattr(self, "label_BatteryGuage") or not hasattr(self, "label_BatteryGuageTxt"):
            return

        try:
            icon_name = battery_info.get_icon_name()
            print(f"[SettingsView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[SettingsView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[SettingsView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[SettingsView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[SettingsView] Battery UI update error: {e}") 