# -*- coding: utf-8 -*-
"""
Result Category View - 결과 카테고리 선택 화면
"""

import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer, QDateTime
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)

class CalibrationIntroView(QMainWindow):
    """Calibration Intro 뷰"""

    # 시그널 정의
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)  # form 데이터 전달

    def __init__(self, parent=None):
        super().__init__(parent)
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        # UI 파일 경로 설정
        ui_filename = 'Intro.ui'
        ui_file = os.path.join(project_root, 'ui', 'Calibration', ui_filename)
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        self.setup_connections()
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        
        self.selected_type = None
        self._init_type_buttons()
        self._init_calendar()

    def setup_connections(self):
        self.pushButton_next.clicked.connect(self.on_next_clicked)
        self.pushButton_calendar.clicked.connect(self.show_calendar)
        # Exp. Date 텍스트 필드 클릭 시에도 달력 팝업
        self.lineEdit_exp_date.mousePressEvent = lambda event: self.show_calendar()
        self.pushButton_type1.clicked.connect(lambda: self.select_type(1))
        self.pushButton_type2.clicked.connect(lambda: self.select_type(2))
        # 뒤로가기(홈) 버튼이 있다면 연결
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.on_back_clicked)

    def _init_type_buttons(self):
        self.pushButton_type1.setCheckable(True)
        self.pushButton_type2.setCheckable(True)
        self.pushButton_type1.setChecked(False)
        self.pushButton_type2.setChecked(False)

    def select_type(self, type_num):
        if type_num == 1:
            self.pushButton_type1.setChecked(True)
            self.pushButton_type2.setChecked(False)
            self.selected_type = 1
        else:
            self.pushButton_type1.setChecked(False)
            self.pushButton_type2.setChecked(True)
            self.selected_type = 2

    def _init_calendar(self):
        self.calendar_popup = None
        self.lineEdit_exp_date.setReadOnly(True)
        # 오늘 날짜를 기본값으로 설정
        from PyQt5.QtCore import QDate
        today = QDate.currentDate()
        self.lineEdit_exp_date.setText(today.toString('yyyy-MM-dd'))

    def show_calendar(self):
        from PyQt5.QtWidgets import QCalendarWidget, QDialog, QVBoxLayout, QPushButton
        from PyQt5.QtCore import QDate
        class CalendarDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle('날짜 선택')
                self.setFixedSize(320, 320)
                layout = QVBoxLayout(self)
                self.calendar = QCalendarWidget(self)
                self.calendar.setGridVisible(True)
                self.calendar.setSelectedDate(QDate.currentDate())
                layout.addWidget(self.calendar)
                btn = QPushButton('선택', self)
                btn.clicked.connect(self.accept)
                layout.addWidget(btn)
            def selected_date(self):
                return self.calendar.selectedDate()
        dlg = CalendarDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            date = dlg.selected_date()
            self.lineEdit_exp_date.setText(date.toString('yyyy-MM-dd'))

    def on_next_clicked(self):
        # 폼 데이터 수집 및 유효성 검사
        lot = self.lineEdit_lot.text().strip()
        exp_date = self.lineEdit_exp_date.text().strip()
        if not self.selected_type:
            QMessageBox.warning(self, '입력 오류', 'Type을 선택하세요.')
            return
        if not lot:
            QMessageBox.warning(self, '입력 오류', 'Lot#를 입력하세요.')
            return
        if not exp_date:
            QMessageBox.warning(self, '입력 오류', 'Exp. Date를 선택하세요.')
            return
        # 데이터 전달
        data = {
            'operator_id': self.lineEdit_operator_id.text(),
            'device_id': self.lineEdit_device_id.text(),
            'type': self.selected_type,
            'lot': lot,
            'exp_date': exp_date
        }
        self.switch_to_next_step.emit(data)

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
        # 페이지를 벗어날 때 폼 초기화 (비활성 필드는 제외)
        self.reset_form()
    
    def reset_form(self):
        """폼 필드 초기화 (활성 필드만)"""
        self.lineEdit_lot.clear()
        # 오늘 날짜로 재설정
        from PyQt5.QtCore import QDate
        today = QDate.currentDate()
        self.lineEdit_exp_date.setText(today.toString('yyyy-MM-dd'))
        self.pushButton_type1.setChecked(False)
        self.pushButton_type2.setChecked(False)
        self.selected_type = None
    def closeEvent(self, event):
        stop_date_time_update(self)
        stop_battery_update(self)
        super().closeEvent(event)
        
    def reset_view(self):
        update_date_time(self)
        update_battery_status(self)
        self.lineEdit_lot.clear()
        # 오늘 날짜로 재설정
        from PyQt5.QtCore import QDate
        today = QDate.currentDate()
        self.lineEdit_exp_date.setText(today.toString('yyyy-MM-dd'))
        self.pushButton_type1.setChecked(False)
        self.pushButton_type2.setChecked(False)
        self.selected_type = None
