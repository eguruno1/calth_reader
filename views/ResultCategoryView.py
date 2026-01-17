# -*- coding: utf-8 -*-
"""
Result Category View - 결과 카테고리 선택 화면
"""

import os
import threading

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QTimer, QDateTime, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QPixmap
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,)

from controllers import app_controller

class ResultCategoryView(QMainWindow):
    """결과 카테고리 선택 뷰"""
    
    # 시그널 정의
    switch_to_home = pyqtSignal()
    switch_to_patient_results = pyqtSignal()
    switch_to_calibration_results = pyqtSignal()
    switch_to_qc_results = pyqtSignal()
    
    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        
        # 배터리
        self.uart_model = uart_model
        print(f"[ResultCategoryView] uart_model injected: {self.uart_model}")

        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'ResultCategoryViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Review', ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 버튼 시그널 연결
        self.setup_connections()
        
        # 날짜/시간 표시 초기화
        self.update_date_time()
    
    def setup_connections(self):
        """버튼 시그널 연결"""
        try:
            # 결과 카테고리 버튼들
            self.pushButton_PatientResults.clicked.connect(self.on_patient_results_clicked)
            # self.pushButton_CalibrationResults.clicked.connect(self.on_calibration_results_clicked)
            self.pushButton_QCResults.clicked.connect(self.on_qc_results_clicked)
            
            # 뒤로가기 버튼
            self.pushButton_Back.clicked.connect(self.on_back_clicked)
            
            print("ResultCategoryView 버튼 연결 완료")
        except AttributeError as e:
            print(f"버튼 연결 오류: {e}")
    
    def showEvent(self, event):
        """화면이 표시될 때 호출"""
        super().showEvent(event)
        # 날짜/시간 및 배터리 업데이트 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        
        # 배터리 상태 업데이트
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)
        print("ResultCategoryView가 표시되었습니다.")
    
    def hideEvent(self, event):
        """화면이 숨김될 때 호출"""
        super().hideEvent(event)
        # 날짜/시간 및 배터리 업데이트 중지
        stop_date_time_update(self)

        print("ResultCategoryView가 숨겨졌습니다.")
    
    def closeEvent(self, event):
        """화면이 닫힐 때 호출"""
        stop_date_time_update(self)

        super().closeEvent(event)
        print("ResultCategoryView가 닫혔습니다.")
    
    def update_date_time(self):
        """날짜와 시간 업데이트"""
        update_date_time(self)
    
    
    # 버튼 이벤트 핸들러들
    def on_patient_results_clicked(self):
        """Patient Results 버튼 클릭"""
        print("Patient Results 버튼이 클릭되었습니다.")
        self.switch_to_patient_results.emit()
    
    def on_calibration_results_clicked(self):
        """Calibration Results 버튼 클릭"""
        print("Calibration Results 버튼이 클릭되었습니다.")
        self.switch_to_calibration_results.emit()
    
    def on_qc_results_clicked(self):
        """QC Results 버튼 클릭"""
        print("QC Results 버튼이 클릭되었습니다.")
        self.switch_to_qc_results.emit()
    
    def on_back_clicked(self):
        """Back 버튼 클릭"""
        print("Back 버튼이 클릭되었습니다.")
        self.switch_to_home.emit()
    
    def reset_view(self):
        """뷰 초기화"""
        print("ResultCategoryView 초기화")
        self.update_date_time()


    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[ResultCategoryView] on_uart_event: {event_type}, {data}")
        print(
            f"[ResultCategoryView][{self.__class__.__name__}] on_uart_event "
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
            print(f"[ResultCategoryView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[ResultCategoryView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[ResultCategoryView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[ResultCategoryView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[ResultCategoryView] Battery UI update error: {e}")
