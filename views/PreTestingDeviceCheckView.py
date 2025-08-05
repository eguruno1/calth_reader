# -*- coding: utf-8 -*-
"""
PreTestingDeviceCheckView - Pre-Testing Device Check 단계 화면 (Calibration/QC 공통)
"""
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal
from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)
from config.pretest_config import PretestConfig


class PreTestingDeviceCheckView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_filename = 'DeviceCheck.ui'
        ui_file = os.path.join(project_root, 'ui', 'PreTesting', ui_filename)
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 체크 프로세스 타이머
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.update_check_progress)
        self.check_step = 0
        
        # 데이터 저장
        self.data = None
        self.pretest_type = PretestConfig.TYPE_CALIBRATION
        self.config = {}
        
        # 연결 설정
        self.setup_connections()
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        
        # 자동으로 체크 프로세스 시작
        self.start_device_check()

    def setup_connections(self):
        """버튼 및 신호 연결"""
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.go_back)
        if hasattr(self, 'pushButton_cancel'):
            self.pushButton_cancel.clicked.connect(self.cancel_check)

    def set_data(self, data: dict):
        """이전 단계에서 전달받은 데이터 설정"""
        self.data = data
        
        # Pre-Testing 타입 설정 및 UI 업데이트
        if data and 'pretest_type' in data:
            self.pretest_type = data['pretest_type']
        self.config = PretestConfig.get_config(self.pretest_type)
        self.update_ui_texts()
        self.update_kit_info()

    def update_ui_texts(self):
        """Pre-Testing 타입에 따라 UI 텍스트 업데이트"""
        # 메인 타이틀 업데이트
        if hasattr(self, 'label_title'):
            self.label_title.setText(self.config.get('title', 'PRE-TESTING'))
        
        # Check 제목 업데이트
        if hasattr(self, 'label_check_title'):
            self.label_check_title.setText(self.config.get('check_title', '🔍 Checking Device'))
        
        # Check 단계별 텍스트 업데이트
        check_steps = self.config.get('check_steps', [])
        for i, step_text in enumerate(check_steps, 1):
            if hasattr(self, f'label_check{i}'):
                getattr(self, f'label_check{i}').setText(step_text)
        
        # 윈도우 타이틀 업데이트
        self.setWindowTitle(f"{self.config.get('window_title_suffix', 'Pre-Testing')} - Device Check")
        
    def update_kit_info(self):
        """현재 키트 정보를 UI에 표시"""
        if self.data and 'current_kit' in self.data:
            current_kit = self.data['current_kit']
            total_kits = self.data.get('total_kits', 4)
            kit_names = self.data.get('kit_names', ['음성', '저농도', '중농도', '고농도'])
            
            if current_kit <= len(kit_names):
                kit_name = kit_names[current_kit - 1]
                
                # 상태 표시 업데이트
                if hasattr(self, 'label_status'):
                    self.label_status.setText(f"Checking {kit_name} kit ({current_kit}/{total_kits})...")
                    
                # 체크 항목들도 키트별로 업데이트
                if hasattr(self, 'label_check1'):
                    self.label_check1.setText(f"Device connection for {kit_name} kit...")
                if hasattr(self, 'label_check2'):
                    self.label_check2.setText(f"Recognizing {kit_name} kit ID...")
                if hasattr(self, 'label_check3'):
                    self.label_check3.setText(f"Calibrating {kit_name} values...")
                if hasattr(self, 'label_check4'):
                    self.label_check4.setText(f"Validating {kit_name} calibration...")
        
    def update_date_time(self):
        """현재 시간을 라벨에 업데이트"""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("yyyy-MM-dd hh:mm")
        if hasattr(self, 'label_DateNClock'):
            self.label_DateNClock.setText(time_str)
        
    def start_device_check(self):
        """디바이스 체크 프로세스 시작"""
        self.check_step = 0
        if hasattr(self, 'progressBar_check'):
            self.progressBar_check.setValue(0)
        self.check_timer.start(2000)  # 2초마다 진행
        
    def update_check_progress(self):
        """체크 진행상황 업데이트"""
        self.check_step += 1
        
        if self.check_step == 1:
            if hasattr(self, 'progressBar_check'):
                self.progressBar_check.setValue(25)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Device connection verified...")
            if hasattr(self, 'label_check1'):
                self.label_check1.setText("✓ Device connection verified")
            
        elif self.check_step == 2:
            if hasattr(self, 'progressBar_check'):
                self.progressBar_check.setValue(50)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Recognizing device ID...")
            if hasattr(self, 'label_check2'):
                self.label_check2.setText("✓ Device ID recognized")
            
        elif self.check_step == 3:
            if hasattr(self, 'progressBar_check'):
                self.progressBar_check.setValue(75)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Performing calibration check...")
            if hasattr(self, 'label_check3'):
                self.label_check3.setText("✓ Calibration check completed")
            
        elif self.check_step == 4:
            if hasattr(self, 'progressBar_check'):
                self.progressBar_check.setValue(100)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Calibration validation complete!")
            if hasattr(self, 'label_check4'):
                self.label_check4.setText("✓ Calibration values validated")
            self.check_timer.stop()
            
            # 3초 후 자동으로 다음 페이지로 이동
            QTimer.singleShot(3000, self.go_to_eject_device)
            
    def go_back(self):
        """이전 페이지로 이동"""
        self.check_timer.stop()
        print("Going back to Insert Device page")
        self.switch_to_home.emit()
        
    def cancel_check(self):
        """체크 취소"""
        self.check_timer.stop()
        print("Calibration check cancelled")
        self.switch_to_home.emit()
        
    def go_to_eject_device(self):
        """Eject Device 페이지로 이동"""
        print("Going to Eject Device page")
        self.switch_to_next_step.emit(self.data)

    def showEvent(self, event):
        super().showEvent(event)
        # 즉시 시간과 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        # 그 다음 타이머 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
        # 화면이 표시될 때마다 체크 프로세스 시작
        QTimer.singleShot(500, self.start_device_check)
        
    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)
        stop_battery_update(self)
        # UI 상태 초기화
        self.reset_ui_state()
        
    def reset_ui_state(self):
        """UI 상태를 초기 상태로 리셋"""
        # 타이머 중지
        if hasattr(self, 'check_timer'):
            self.check_timer.stop()
        
        # 프로그레스바 초기화
        if hasattr(self, 'progressBar_check'):
            self.progressBar_check.setValue(0)
        
        # 상태 텍스트 초기화
        if hasattr(self, 'label_status'):
            self.label_status.setText("Starting device check...")
        
        # 체크 라벨들 초기화
        if hasattr(self, 'label_check1'):
            self.label_check1.setText("Device connection check")
        if hasattr(self, 'label_check2'):
            self.label_check2.setText("Device ID recognition")
        if hasattr(self, 'label_check3'):
            self.label_check3.setText("Calibration check")
        if hasattr(self, 'label_check4'):
            self.label_check4.setText("Calibration validation")
        
        # 체크 단계 초기화
        self.check_step = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PreTestingDeviceCheckView()
    window.show()
    sys.exit(app.exec_())
