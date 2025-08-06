# -*- coding: utf-8 -*-
"""
Calibration QC Settings View - 캘리브레이션 및 QC 날짜 설정 화면
"""
import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update


class CalibrationQCSettingsView(QMainWindow):
    """캘리브레이션 및 QC 날짜 설정 화면"""
    
    switch_to_settings = pyqtSignal()  # 설정 화면으로 돌아가기

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'CalibrationQCSettingsViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Settings', ui_filename)
        
        # UI 파일 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        """UI 초기화 및 이벤트 연결"""
        # 뒤로 가기 버튼 연결
        self.pushButton_BackArrow.clicked.connect(self.on_back_button_clicked)
        
        # 적용 버튼 이벤트 연결
        self.btn_calibration_apply.clicked.connect(self.on_calibration_apply_clicked)
        self.btn_qc_apply.clicked.connect(self.on_qc_apply_clicked)
        
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def load_current_settings(self):
        """현재 설정 로드"""
        try:
            # 기본값 7일로 설정
            self.combo_calibration_days.setCurrentText("7")
            self.combo_qc_days.setCurrentText("7")
            
        except Exception as e:
            print(f"설정 로드 실패: {e}")

    def on_calibration_apply_clicked(self):
        """캘리브레이션 적용 버튼 클릭"""
        try:
            selected_days = self.combo_calibration_days.currentText()
            
            # 적용 확인 대화상자
            reply = QMessageBox.question(
                self, 
                "캘리브레이션 설정", 
                f"캘리브레이션 주기를 {selected_days}일로 설정하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 여기에 실제 캘리브레이션 설정 로직 구현
                QMessageBox.information(self, "설정 완료", f"캘리브레이션 주기가 {selected_days}일로 설정되었습니다.")
                # TODO: 실제 설정 저장 로직 구현
                print(f"캘리브레이션 주기 설정: {selected_days}일")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"캘리브레이션 설정 중 오류가 발생했습니다: {e}")

    def on_qc_apply_clicked(self):
        """QC 적용 버튼 클릭"""
        try:
            selected_days = self.combo_qc_days.currentText()
            
            # 적용 확인 대화상자
            reply = QMessageBox.question(
                self, 
                "QC 설정", 
                f"QC 주기를 {selected_days}일로 설정하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 여기에 실제 QC 설정 로직 구현
                QMessageBox.information(self, "설정 완료", f"QC 주기가 {selected_days}일로 설정되었습니다.")
                # TODO: 실제 설정 저장 로직 구현
                print(f"QC 주기 설정: {selected_days}일")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"QC 설정 중 오류가 발생했습니다: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        """뒤로 가기 버튼 클릭"""
        self.switch_to_settings.emit()

    def update_date_time(self):
        """날짜/시간 업데이트 (헤더용)"""
        update_date_time(self)
