# -*- coding: utf-8 -*-
"""
Update Settings View - 소프트웨어 및 펌웨어 업데이트 화면
"""
import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update


class UpdateSettingsView(QMainWindow):
    """소프트웨어 및 펌웨어 업데이트 화면"""
    
    switch_to_settings = pyqtSignal()  # 설정 화면으로 돌아가기

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'UpdateSettingsViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Settings', ui_filename)
        
        # UI 파일 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        self.init_ui()
        self.load_current_versions()

    def init_ui(self):
        """UI 초기화 및 이벤트 연결"""
        # 뒤로 가기 버튼 연결
        self.pushButton_BackArrow.clicked.connect(self.on_back_button_clicked)
        
        # 업데이트 버튼 이벤트 연결
        self.btn_software_update.clicked.connect(self.on_software_update_clicked)
        self.btn_firmware_update.clicked.connect(self.on_firmware_update_clicked)
        
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def load_current_versions(self):
        """현재 버전 정보 로드"""
        try:
            # 소프트웨어 버전 (예시)
            software_version = "v1.2.3"
            self.label_software_version.setText(f"현재 버전: {software_version}")
            
            # 펌웨어 버전 (예시)
            firmware_version = "v2.1.0"
            self.label_firmware_version.setText(f"현재 버전: {firmware_version}")
            
        except Exception as e:
            print(f"버전 정보 로드 실패: {e}")

    def on_software_update_clicked(self):
        """소프트웨어 업데이트 버튼 클릭"""
        try:
            # 업데이트 확인 대화상자
            reply = QMessageBox.question(
                self, 
                "소프트웨어 업데이트", 
                "소프트웨어 업데이트를 진행하시겠습니까?\n업데이트 중에는 시스템을 종료하지 마세요.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 여기에 실제 소프트웨어 업데이트 로직 구현
                QMessageBox.information(self, "업데이트", "소프트웨어 업데이트가 시작됩니다.")
                # TODO: 실제 업데이트 로직 구현
                print("소프트웨어 업데이트 시작")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"소프트웨어 업데이트 중 오류가 발생했습니다: {e}")

    def on_firmware_update_clicked(self):
        """펌웨어 업데이트 버튼 클릭"""
        try:
            # 업데이트 확인 대화상자
            reply = QMessageBox.question(
                self, 
                "펌웨어 업데이트", 
                "펌웨어 업데이트를 진행하시겠습니까?\n업데이트 중에는 시스템을 종료하지 마세요.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 여기에 실제 펌웨어 업데이트 로직 구현
                QMessageBox.information(self, "업데이트", "펌웨어 업데이트가 시작됩니다.")
                # TODO: 실제 업데이트 로직 구현
                print("펌웨어 업데이트 시작")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"펌웨어 업데이트 중 오류가 발생했습니다: {e}")

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
