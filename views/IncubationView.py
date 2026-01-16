# -*- coding: utf-8 -*-


import sys
import os
import threading
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QResizeEvent, QPixmap
from views.Utils import (center_window, update_date_time, start_date_time_update, stop_date_time_update)
from config.pretest_config import PretestConfig


class IncubationView(QMainWindow):

    switch_to_home = pyqtSignal()

    def __init__(self, parent=None, uart_model=None):

        super().__init__(parent)
        
        self.load_ui()
        self.init_ui()

        # JSON 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        # 배터리
        self.uart_model = uart_model
        print(f"[IncubationView] uart_model injected: {self.uart_model}")


    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'IncubationViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Test', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 🔙 뒤로 가기 버튼 (UI objectName 불일치 대비)
        if hasattr(self, "pushButton_BackArrow"):
            self.pushButton_BackArrow.clicked.connect(self.on_back_button_clicked)
        else:
            print(
                "[IncubationView][WARN] pushButton_BackArrow not found in UI. "
                "Back button connection skipped."
            )
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

        # 배터리 상태 업데이트
        from controllers import app_controller
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        print("[IncubationView] on_back_button_clicked")
        self.switch_to_home.emit()    

    def update_date_time(self):
        update_date_time(self)    

    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[IncubationView] on_uart_event: {event_type}, {data}")
        print(
            f"[IncubationView][{self.__class__.__name__}] on_uart_event "
            f"thread={threading.current_thread().name}"
        )

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
            print(f"[IncubationView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[IncubationView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[IncubationView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[IncubationView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[IncubationView] Battery UI update error: {e}")    