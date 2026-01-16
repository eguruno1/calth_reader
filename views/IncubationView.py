# -*- coding: utf-8 -*-


import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal
from views.Utils import (center_window, update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)
from config.pretest_config import PretestConfig


class IncubationView(QMainWindow):

    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'IncubationViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Test', ui_filename)
        
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")