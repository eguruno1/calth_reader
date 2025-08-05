import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal
from views.Utils import (center_window, update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)
from config.pretest_config import PretestConfig


class PreTestingInsertDeviceView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_file = os.path.join(project_root, 'ui', 'PreTesting', 'InsertDevice.ui')
        
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 윈도우 설정
        center_window(self)
        
        # 데이터 저장
        self.data = None
        self.pretest_type = PretestConfig.TYPE_CALIBRATION  # 기본값
        self.config = {}
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        
        # 버튼 연결
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.go_back)
        if hasattr(self, 'pushButton_next'):
            self.pushButton_next.clicked.connect(self.go_next)
        
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
        
        # Insert 제목 업데이트
        if hasattr(self, 'label_insert_title'):
            self.label_insert_title.setText(self.config.get('insert_title', '📋 Insert Device'))
        
        # Insert 설명 업데이트
        if hasattr(self, 'label_insert_instruction'):
            self.label_insert_instruction.setText(self.config.get('insert_instruction', 'Please insert the device...'))
        
        # 윈도우 타이틀 업데이트
        self.setWindowTitle(f"{self.config.get('window_title_suffix', 'Pre-Testing')} - Insert Device")
        
    def update_kit_info(self):
        """현재 키트 정보를 UI에 표시"""
        if self.data and 'current_kit' in self.data:
            current_kit = self.data['current_kit']
            total_kits = self.data.get('total_kits', 4)
            kit_names = self.data.get('kit_names', ['음성', '저농도', '중농도', '고농도'])
            
            if current_kit <= len(kit_names):
                kit_name = kit_names[current_kit - 1]
                
                # 제목 업데이트
                if hasattr(self, 'label_insert_title'):
                    self.label_insert_title.setText(f"📋 Insert Calibration Device ({current_kit}/{total_kits})")
                
                # 지시사항 업데이트
                if hasattr(self, 'label_insert_instruction'):
                    instruction_text = f"""Please insert the {kit_name} calibration kit into the designated slot.

Current Kit: {current_kit}/{total_kits} - {kit_name}

Ensure the device is properly aligned and fully inserted.
The device should click into place when correctly positioned.

Press "Next" when the device is properly inserted."""
                    self.label_insert_instruction.setText(instruction_text)
        
    def go_back(self):
        """이전 페이지로 이동"""
        print("Going back to Caution page")
        self.switch_to_home.emit()
        
    def go_next(self):
        """다음 페이지로 이동"""
        print("Going to Device Check page")
        self.switch_to_next_step.emit(self.data)
        
    def showEvent(self, event):
        super().showEvent(event)
        # 즉시 시간과 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)
        # 그 다음 타이머 시작
        from views.Utils import start_date_time_update, start_battery_update
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
        
    def hideEvent(self, event):
        super().hideEvent(event)
        from views.Utils import stop_date_time_update, stop_battery_update
        stop_date_time_update(self)
        stop_battery_update(self)
        # UI 상태 초기화
        self.reset_ui_state()
        
    def reset_ui_state(self):
        """UI 상태를 초기 상태로 리셋"""
        # 데이터 초기화 (다음 진입 시를 위해)
        self.data = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CalibrationInsertDeviceView()
    window.show()
    sys.exit(app.exec_())
