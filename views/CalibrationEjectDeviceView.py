# -*- coding: utf-8 -*-
"""
CalibrationEjectDeviceView - Calibration Eject Device 단계 화면
"""
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal
from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)


class CalibrationEjectDeviceView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_filename = 'EjectDevice.ui'
        ui_file = os.path.join(project_root, 'ui', 'Calibration', ui_filename)
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 데이터 저장
        self.data = None
        
        # Eject 프로세스 관련 변수
        self.eject_step = 0
        self.eject_timer = QTimer()
        self.eject_timer.timeout.connect(self.update_eject_progress)
        
        # 연결 설정
        self.setup_connections()
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)

    def setup_connections(self):
        """버튼 및 신호 연결"""
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.go_back)
        if hasattr(self, 'pushButton_next'):
            self.pushButton_next.clicked.connect(self.go_next)

    def set_data(self, data: dict):
        """이전 단계에서 전달받은 데이터 설정"""
        self.data = data
        self.update_kit_info()
        
    def update_kit_info(self):
        """현재 키트 정보를 UI에 표시"""
        if self.data and 'current_kit' in self.data:
            current_kit = self.data['current_kit']
            total_kits = self.data.get('total_kits', 4)
            kit_names = self.data.get('kit_names', ['음성', '저농도', '중농도', '고농도'])
            
            if current_kit <= len(kit_names):
                kit_name = kit_names[current_kit - 1]
                
                # 제목 업데이트
                if hasattr(self, 'label_eject_title'):
                    self.label_eject_title.setText(f"📤 Remove {kit_name} Kit ({current_kit}/{total_kits})")
                
                # 지시사항 업데이트  
                if hasattr(self, 'label_eject_instruction'):
                    next_action = "Insert next calibration kit" if current_kit < total_kits else "View calibration results"
                    instruction_text = f"""Please remove the {kit_name} calibration kit from the device.

Current Kit: {current_kit}/{total_kits} - {kit_name} completed

Gently pull the kit straight out from the slot.
Do not force or twist the kit during removal.

Press "Next" when the kit is completely removed.
Next step: {next_action}"""
                    self.label_eject_instruction.setText(instruction_text)
                    
                # 버튼 텍스트 업데이트
                if hasattr(self, 'pushButton_next'):
                    if current_kit < total_kits:
                        self.pushButton_next.setText("Next Kit →")
                    else:
                        self.pushButton_next.setText("View Results →")
        
    def update_date_time(self):
        """현재 시간을 라벨에 업데이트"""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("yyyy-MM-dd hh:mm")
        if hasattr(self, 'label_DateNClock'):
            self.label_DateNClock.setText(time_str)
        
    def go_back(self):
        """이전 페이지로 이동"""
        print("Going back to Device Check page")
        self.switch_to_home.emit()
        
    def go_next(self):
        """결과 페이지로 이동"""
        print("Going to Result page")
        self.switch_to_next_step.emit(self.data)

    def start_eject_process(self):
        """디바이스 제거 프로세스 시작"""
        self.eject_step = 0
        if hasattr(self, 'progressBar_eject'):
            self.progressBar_eject.setValue(0)
        if hasattr(self, 'label_status'):
            self.label_status.setText("Please remove the calibration device...")
        self.eject_timer.start(3000)  # 3초마다 진행
        
    def update_eject_progress(self):
        """제거 진행상황 업데이트"""
        self.eject_step += 1
        
        if self.eject_step == 1:
            if hasattr(self, 'progressBar_eject'):
                self.progressBar_eject.setValue(25)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Waiting for device removal...")
            
        elif self.eject_step == 2:
            if hasattr(self, 'progressBar_eject'):
                self.progressBar_eject.setValue(50)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Device removal detected...")
            
        elif self.eject_step == 3:
            if hasattr(self, 'progressBar_eject'):
                self.progressBar_eject.setValue(75)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Finalizing calibration data...")
            
        elif self.eject_step == 4:
            if hasattr(self, 'progressBar_eject'):
                self.progressBar_eject.setValue(100)
            if hasattr(self, 'label_status'):
                self.label_status.setText("Device successfully removed!")
            self.eject_timer.stop()
            
            # 3초 후 자동으로 다음 페이지로 이동
            QTimer.singleShot(3000, self.go_next)

    def showEvent(self, event):
        super().showEvent(event)
        # 즉시 시간과 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        # 그 다음 타이머 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
        # 화면이 표시될 때마다 제거 프로세스 시작
        QTimer.singleShot(500, self.start_eject_process)
        
    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)
        stop_battery_update(self)
        # UI 상태 초기화
        self.reset_ui_state()
        
    def reset_ui_state(self):
        """UI 상태를 초기 상태로 리셋"""
        # 타이머 중지
        if hasattr(self, 'eject_timer'):
            self.eject_timer.stop()
        
        # 프로그레스바 초기화
        if hasattr(self, 'progressBar_eject'):
            self.progressBar_eject.setValue(0)
        
        # 상태 텍스트 초기화
        if hasattr(self, 'label_status'):
            self.label_status.setText("Please remove the calibration device...")
        
        # 단계 초기화
        self.eject_step = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalibrationEjectDeviceView()
    window.show()
    sys.exit(app.exec_())
