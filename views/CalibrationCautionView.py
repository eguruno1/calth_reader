# -*- coding: utf-8 -*-
"""
CalibrationCautionView - Calibration Caution 단계 화면
"""
import os
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic
from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)

class CalibrationCautionView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_filename = 'Caution.ui'
        ui_file = os.path.join(project_root, 'ui', 'Calibration', ui_filename)
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        self.setup_connections()
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        
        self.data = None

    def setup_connections(self):
        if hasattr(self, 'pushButton_next'):
            self.pushButton_next.clicked.connect(self.on_next_clicked)
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.on_back_clicked)

    def set_data(self, data: dict):
        self.data = data
        # 필요시 폼에 데이터 표시 가능

    def on_next_clicked(self):
        self.switch_to_next_step.emit(self.data)

    def on_back_clicked(self):
        self.switch_to_home.emit()

    def showEvent(self, event):
        super().showEvent(event)
        # 즉시 시간과 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        # 그 다음 타이머 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)
        stop_battery_update(self)
        # UI 상태 초기화
        self.reset_view()
    def closeEvent(self, event):
        stop_date_time_update(self)
        stop_battery_update(self)
        super().closeEvent(event)
    
    def reset_view(self):
        """뷰 상태를 초기화"""
        self.data = None
