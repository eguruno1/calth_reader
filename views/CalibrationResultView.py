# -*- coding: utf-8 -*-
"""
CalibrationResultView - Calibration Result 단계 화면
"""
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QDateTime, pyqtSignal
from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)


class CalibrationResultView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_next_step = pyqtSignal(dict)
    switch_to_retry = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        ui_filename = 'Result.ui'
        ui_file = os.path.join(project_root, 'ui', 'Calibration', ui_filename)
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # 결과 상태 저장
        self.result_status = "PASSED"
        self.data = None
        
        # 연결 설정
        self.setup_connections()
        
        # 초기 시간 및 배터리 상태 업데이트
        update_date_time(self)
        update_battery_status(self)

    def setup_connections(self):
        """버튼 및 신호 연결"""
        if hasattr(self, 'pushButton_Back'):
            self.pushButton_Back.clicked.connect(self.go_back)
        if hasattr(self, 'pushButton_complete'):
            self.pushButton_complete.clicked.connect(self.complete_calibration)
        if hasattr(self, 'pushButton_retry'):
            self.pushButton_retry.clicked.connect(self.retry_calibration)

    def set_data(self, data: dict):
        """이전 단계에서 전달받은 데이터 설정"""
        self.data = data

    def set_result_status(self, status: str):
        """결과 상태 설정 및 UI 업데이트"""
        self.result_status = status
        self.setup_result_display()
        
    def setup_result_display(self):
        """결과 상태에 따른 UI 설정"""
        if self.result_status == "PASSED":
            if hasattr(self, 'label_result_status'):
                self.label_result_status.setText("✓ CALIBRATION PASSED")
                self.label_result_status.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        font-weight: bold;
                        color: #388e3c;
                        border: none;
                    }
                """)
            if hasattr(self, 'label_result_message'):
                self.label_result_message.setText("Calibration completed successfully. The device is now ready for use.")
                self.label_result_message.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #388e3c;
                        border: none;
                        padding: 15px;
                        background-color: #e8f5e8;
                        border-radius: 8px;
                    }
                """)
            
            # Passed 상태일 때 테스트 결과 업데이트
            if hasattr(self, 'label_test1'):
                self.label_test1.setText("Accuracy Test: ±0.05% (PASS)")
            if hasattr(self, 'label_test2'):
                self.label_test2.setText("Linearity Test: 0.999 R² (PASS)")
            if hasattr(self, 'label_test3'):
                self.label_test3.setText("Repeatability: CV < 2% (PASS)")
            if hasattr(self, 'label_test4'):
                self.label_test4.setText("Temperature Stability: PASS")
                
        else:
            if hasattr(self, 'label_result_status'):
                self.label_result_status.setText("✗ CALIBRATION FAILED")
                self.label_result_status.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        font-weight: bold;
                        color: #d32f2f;
                        border: none;
                    }
                """)
            if hasattr(self, 'label_result_message'):
                self.label_result_message.setText("Calibration failed. Please retry the calibration process.")
                self.label_result_message.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #d32f2f;
                        border: none;
                        padding: 15px;
                        background-color: #ffebee;
                        border-radius: 8px;
                    }
                """)
            
            # Failed 상태일 때 테스트 결과 업데이트
            if hasattr(self, 'label_test1'):
                self.label_test1.setText("Accuracy Test: ±0.15% (FAIL)")
            if hasattr(self, 'label_test2'):
                self.label_test2.setText("Linearity Test: 0.985 R² (FAIL)")
            if hasattr(self, 'label_test3'):
                self.label_test3.setText("Repeatability: CV > 5% (FAIL)")
            if hasattr(self, 'label_test4'):
                self.label_test4.setText("Temperature Stability: FAIL")
        
    def go_back(self):
        """이전 페이지로 이동"""
        print("Going back to Eject Device page")
        self.switch_to_home.emit()
        
    def complete_calibration(self):
        """캘리브레이션 완료"""
        print("Going to Complete page")
        self.switch_to_next_step.emit(self.data)
        
    def retry_calibration(self):
        """캘리브레이션 재시도"""
        print("Retrying calibration")
        self.switch_to_retry.emit(self.data)

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
        # 결과 상태 초기화
        self.result_status = "PASSED"
        
        # 결과 라벨들 초기화
        if hasattr(self, 'label_result_status'):
            self.label_result_status.setText("CALIBRATION RESULT")
            self.label_result_status.setStyleSheet("""
                QLabel {
                    font-size: 32px;
                    font-weight: bold;
                    color: #333333;
                    border: none;
                }
            """)
        
        if hasattr(self, 'label_result_message'):
            self.label_result_message.setText("Processing calibration results...")
            self.label_result_message.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #333333;
                    border: none;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                }
            """)
        
        # 테스트 결과 초기화
        if hasattr(self, 'label_test1'):
            self.label_test1.setText("Accuracy Test: Pending...")
        if hasattr(self, 'label_test2'):
            self.label_test2.setText("Linearity Test: Pending...")
        if hasattr(self, 'label_test3'):
            self.label_test3.setText("Repeatability: Pending...")
        if hasattr(self, 'label_test4'):
            self.label_test4.setText("Temperature Stability: Pending...")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 테스트를 위해 PASSED 또는 FAILED 결과로 실행
    import random
    result = "PASSED" if random.choice([True, False]) else "FAILED"
    
    window = CalibrationResultView()
    window.set_result_status(result)
    window.show()
    sys.exit(app.exec_())
