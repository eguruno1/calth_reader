# -*- coding: utf-8 -*-
"""
Result Category View - 결과 카테고리 선택 화면
"""

import os
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QTimer, QDateTime
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)

class ResultCategoryView(QMainWindow):
    """결과 카테고리 선택 뷰"""
    
    # 시그널 정의
    switch_to_home = pyqtSignal()
    switch_to_patient_results = pyqtSignal()
    switch_to_calibration_results = pyqtSignal()
    switch_to_qc_results = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
            self.pushButton_CalibrationResults.clicked.connect(self.on_calibration_results_clicked)
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
        QTimer.singleShot(100, lambda: start_battery_update(self))
        print("ResultCategoryView가 표시되었습니다.")
    
    def hideEvent(self, event):
        """화면이 숨김될 때 호출"""
        super().hideEvent(event)
        # 날짜/시간 및 배터리 업데이트 중지
        stop_date_time_update(self)
        stop_battery_update(self)
        print("ResultCategoryView가 숨겨졌습니다.")
    
    def closeEvent(self, event):
        """화면이 닫힐 때 호출"""
        stop_date_time_update(self)
        stop_battery_update(self)
        super().closeEvent(event)
        print("ResultCategoryView가 닫혔습니다.")
    
    def update_date_time(self):
        """날짜와 시간 업데이트"""
        update_date_time(self)
    
    def update_battery_status(self):
        """배터리 상태 업데이트"""
        update_battery_status(self)
    
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
        self.update_battery_status()
