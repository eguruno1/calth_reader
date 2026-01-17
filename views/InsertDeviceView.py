# -*- coding: utf-8 -*-
"""
Pre-Testing Insert Device View - Calibration 및 QC 공통 장치 삽입 화면
"""
import sys
import os
import json
import threading
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QResizeEvent, QPixmap
from views.Utils import (center_window, update_date_time, start_date_time_update, stop_date_time_update)

from controllers import app_controller

class InsertDeviceView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)

    switch_to_test_info_view = pyqtSignal(str)
    switch_to_measure_view = pyqtSignal()

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        
        self.test_type = "COVID19"

        # ★ 추가: 슬롯 체크 상태 플래그
        self._waiting_slot_check = False

        # ★ 추가: 슬롯 상태 안내 위젯 (TestInfoView 전용)
        from .widgets.slot_status_overlay import SlotStatusOverlayWidget
        self.slot_overlay = SlotStatusOverlayWidget(self)

        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        ui_file = os.path.join(project_root, 'ui', 'Test', 'InsertDevice.ui')
        
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 윈도우 설정
        center_window(self)

        # 배터리
        self.uart_model = uart_model
        print(f"[InsertDeviceView] uart_model injected: {self.uart_model}")
        
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        
        # 버튼 연결
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.go_back)

        if hasattr(self, 'pushButton_cancel'):
            self.pushButton_cancel.clicked.connect(self.go_back)

        if hasattr(self, 'pushButton_ok'):
            self.pushButton_ok.clicked.connect(self.go_next)    
        
    def go_back(self):
        """이전 페이지로 이동"""
        print("Going back to Home")
        #self.switch_to_home.emit()
        self.switch_to_test_info_view.emit(self.test_type)
        
    def go_next(self):
        """다음 페이지로 이동"""
        print("Going to Measure")
        # self.switch_to_measure_view.emit()

        # ★ 추가: 슬롯 상태 확인 요청
        print("[TestInfoView] Send slot check command: H1")
        self._waiting_slot_check = True

        app_controller.send_uart_command("H1")


        
    def showEvent(self, event):
        super().showEvent(event)
        # 즉시 시간과 배터리 상태 업데이트
        update_date_time(self)

        # 배터리 상태 업데이트
        from controllers import app_controller
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)


    def _load_test_info(self):
        """
        JSON에서 검사 정보 읽기 (Read Only)
        """
        try:
            with open(self.current_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.test_type = data.get("test_type1", "")

            print(f"[InsertDeviceView] _load_test_info test_type 로드: {self.test_type}")

        except Exception as e:
            print(f"[InsertDeviceView] JSON 로드 오류: {e}")

    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[InsertDeviceView] on_uart_event: {event_type}, {data}")
        print(
            f"[InsertDeviceView][{self.__class__.__name__}] on_uart_event "
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
        # ★ 추가: 슬롯 상태 응답 처리
        elif event_type == "slot_status_changed" and self._waiting_slot_check:
            """
            슬롯 상태 확인 후
            실제 화면 이동은 ui_controller에서 select_menu 기준으로 처리
            """
            
            self._waiting_slot_check = False

            from models.uart_model import SlotStatus

            if data == SlotStatus.OUT:
                print("[InsertDeviceView] Slot OPEN → show warning")
                QMetaObject.invokeMethod(
                    self.slot_overlay,
                    "show_off",
                    Qt.QueuedConnection
                )

            elif data == SlotStatus.IN:
                print("[InsertDeviceView] Slot CLOSED → move to MeasureView")
                QMetaObject.invokeMethod(
                    self,
                    "_go_to_measure_view",
                    Qt.QueuedConnection
                )    

    @pyqtSlot(object)
    def _update_battery_ui(self, battery_info):
        if not hasattr(self, "label_BatteryGuage") or not hasattr(self, "label_BatteryGuageTxt"):
            return

        try:
            icon_name = battery_info.get_icon_name()
            print(f"[InsertDeviceView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[InsertDeviceView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[InsertDeviceView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[InsertDeviceView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[InsertDeviceView] Battery UI update error: {e}")  

    @pyqtSlot()
    def _go_to_measure_view(self):
        """MmeasureView 이동"""
        self.switch_to_measure_view.emit()        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InsertDeviceView()
    window.show()
    sys.exit(app.exec_())