# -*- coding: utf-8 -*-
"""
CalibrationCompleteView - Calibration Complete 단계 화면
"""
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal
from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)
from config.pretest_config import PretestConfig


class PreTestingCompleteView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_filename = 'Complete.ui'
        ui_file = os.path.join(project_root, 'ui', 'PreTesting', ui_filename)
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 데이터 저장
        self.data = None
        self.pretest_type = PretestConfig.TYPE_CALIBRATION
        self.config = {}
        
        # 연결 설정
        self.setup_connections()
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)

    def setup_connections(self):
        """버튼 및 신호 연결"""
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.go_back)
        if hasattr(self, 'pushButton_home'):
            self.pushButton_home.clicked.connect(self.go_home)
        if hasattr(self, 'pushButton_print_report'):
            self.pushButton_print_report.clicked.connect(self.print_report)

    def set_data(self, data: dict):
        """이전 단계에서 전달받은 데이터 설정"""
        self.data = data
        
        # Pre-Testing 타입 설정 및 UI 업데이트
        if data and 'pretest_type' in data:
            self.pretest_type = data['pretest_type']
        self.config = PretestConfig.get_config(self.pretest_type)
        self.update_ui_texts()
        self.update_summary_info()
        
    def update_ui_texts(self):
        """Pre-Testing 타입에 따라 UI 텍스트 업데이트"""
        # 메인 타이틀 업데이트
        if hasattr(self, 'label_title'):
            self.label_title.setText(self.config.get('title', 'PRE-TESTING'))
        
        # Complete 타이틀 업데이트
        if hasattr(self, 'label_complete_title'):
            process_name = self.config.get('title', 'Pre-Testing')
            self.label_complete_title.setText(f"🎉 {process_name} Complete!")
        
        # Complete 메시지 업데이트
        if hasattr(self, 'label_complete_message'):
            if self.pretest_type == PretestConfig.TYPE_QC:
                message = """The QC test process has been completed successfully.

Your device quality has been verified and all QC parameters are within acceptable ranges.
All QC data has been saved and documented for quality assurance.

Thank you for following the QC procedure."""
            else:
                message = """The calibration process has been completed successfully.

Your device is now properly calibrated and ready for accurate measurements.
All calibration data has been saved and the next calibration date has been scheduled.

Thank you for following the calibration procedure."""
            self.label_complete_message.setText(message)
        
        # Summary 정보 업데이트
        if hasattr(self, 'label_summary1'):
            process_name = "QC" if self.pretest_type == PretestConfig.TYPE_QC else "Calibration"
            self.label_summary1.setText(f"✓ {process_name} Status: PASSED")
        
        # 윈도우 타이틀 업데이트
        self.setWindowTitle(f"{self.config.get('window_title_suffix', 'Pre-Testing')} - Complete")

    def update_summary_info(self):
        """요약 정보 업데이트"""
        current_time = QDateTime.currentDateTime()
        date_str = current_time.toString("yyyy-MM-dd")
        
        if hasattr(self, 'label_summary2'):
            self.label_summary2.setText(f"✓ Date: {date_str}")
        
    def go_back(self):
        """이전 페이지로 이동"""
        print("Going back to Result page")
        self.switch_to_home.emit()
        
    def go_home(self):
        """홈 페이지로 이동"""
        print("Going to Home page")
        self.switch_to_home.emit()
        
    def print_report(self):
        """보고서 인쇄"""
        process_name = "QC" if self.pretest_type == PretestConfig.TYPE_QC else "calibration"
        print(f"Printing {process_name} report")
        # 여기에 실제 인쇄 로직 구현

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
        self.reset_ui_state()
        
    def reset_ui_state(self):
        """UI 상태를 초기 상태로 리셋"""
        # 완료 화면은 대부분 정적이므로 기본적인 초기화만 수행
        if hasattr(self, 'label_complete_time'):
            self.label_complete_time.setText("")
        
        # 데이터 초기화
        self.data = None
        
    def print_report(self):
        """보고서 출력"""
        process_name = "QC" if self.pretest_type == PretestConfig.TYPE_QC else "calibration"
        print(f"Printing {process_name} report...")
        # 여기에 실제 보고서 출력 로직을 구현할 수 있습니다


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PreTestingCompleteView()
    window.show()
    sys.exit(app.exec_())
