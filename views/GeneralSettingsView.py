# -*- coding: utf-8 -*-
"""
General Settings View - 일반 설정 화면
"""
import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update


class GeneralSettingsView(QMainWindow):
    """일반 설정 화면"""
    
    switch_to_settings = pyqtSignal()  # 설정 화면으로 돌아가기
    switch_to_info     = pyqtSignal()  # Info 화면으로

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'GeneralSettingsViewWindow.ui'
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
        
        # 설정 버튼들 이벤트 연결
        self.btn_network.clicked.connect(self.on_network_clicked)
        self.btn_lis_parameter.clicked.connect(self.on_lis_parameter_clicked)
        self.btn_print.clicked.connect(self.on_print_clicked)
        self.btn_language.clicked.connect(self.on_language_clicked)
        self.btn_unit.clicked.connect(self.on_unit_clicked)
        self.btn_info.clicked.connect(self.on_info_clicked)
        
        # 하단 버튼들 연결
        self.btn_reset.clicked.connect(self.on_reset_clicked)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def load_current_settings(self):
        """현재 설정 정보 로드"""
        try:
            # 기본 설정값들 설정
            self.label_network_status.setText("연결됨")
            self.label_lis_status.setText("설정됨")
            self.label_print_status.setText("준비됨")
            self.label_language_current.setText("English")
            self.label_unit_current.setText("mg/dL")
            self.label_device_name.setText("CalthReader v1.0")
            
        except Exception as e:
            print(f"설정 로드 실패: {e}")

    def on_network_clicked(self):
        """Network 설정 버튼 클릭"""
        try:
            QMessageBox.information(
                self, 
                "Network 설정", 
                "Network 설정 화면을 엽니다.\n(추후 구현 예정)"
            )
            print("Network 설정 클릭됨")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Network 설정 중 오류가 발생했습니다: {e}")

    def on_lis_parameter_clicked(self):
        """LIS Parameter 설정 버튼 클릭"""
        try:
            QMessageBox.information(
                self, 
                "LIS Parameter 설정", 
                "LIS Parameter 설정 화면을 엽니다.\n(추후 구현 예정)"
            )
            print("LIS Parameter 설정 클릭됨")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"LIS Parameter 설정 중 오류가 발생했습니다: {e}")

    def on_print_clicked(self):
        """Print 설정 버튼 클릭"""
        try:
            QMessageBox.information(
                self, 
                "Print 설정", 
                "프린터 설정 화면을 엽니다.\n(추후 구현 예정)"
            )
            print("Print 설정 클릭됨")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Print 설정 중 오류가 발생했습니다: {e}")

    def on_language_clicked(self):
        """Language 설정 버튼 클릭"""
        try:
            QMessageBox.information(
                self, 
                "Language 설정", 
                "언어 설정 화면을 엽니다.\n지원 언어: 영어, 프랑스어, 독일어, 스페인어, 이탈리아어\n(추후 구현 예정)"
            )
            print("Language 설정 클릭됨")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Language 설정 중 오류가 발생했습니다: {e}")

    def on_unit_clicked(self):
        """Unit 설정 버튼 클릭"""
        try:
            QMessageBox.information(
                self, 
                "Unit 설정", 
                "단위 설정 화면을 엽니다.\n국가별 단위 변경이 가능합니다.\n(추후 구현 예정)"
            )
            print("Unit 설정 클릭됨")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Unit 설정 중 오류가 발생했습니다: {e}")

    def on_info_clicked(self):
        """Info 버튼 클릭"""
        self.switch_to_info.emit()
        """
        try:
            info_text = ""장비 정보:
• 장비명칭: CalthReader v1.0
• Serial Number: CR-2024-001
• Software 버전: v1.2.3
• QC 정보: 최근 실행 2024-08-06
• Calibration 정보: 최근 실행 2024-08-05

메모리 정보:
• Patient: 150/3,000
• QC: 25/200  
• Calibration: 10/100""
            
            QMessageBox.information(
                self, 
                "장비 정보", 
                info_text
            )
            print("Info 클릭됨")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"Info 조회 중 오류가 발생했습니다: {e}")
            """

    def on_reset_clicked(self):
        """실행취소 버튼 클릭 - 마지막 저장한 시점으로 돌리기"""
        try:
            reply = QMessageBox.question(
                self, 
                "설정 초기화", 
                "마지막 저장한 설정으로 되돌리시겠습니까?\n현재 변경사항은 모두 취소됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 설정 초기화 로직
                self.load_current_settings()
                QMessageBox.information(self, "초기화 완료", "설정이 마지막 저장 시점으로 복원되었습니다.")
                print("설정 초기화 완료")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 초기화 중 오류가 발생했습니다: {e}")

    def on_apply_clicked(self):
        """적용 버튼 클릭 - 현재 설정으로 저장하기"""
        try:
            reply = QMessageBox.question(
                self, 
                "설정 저장", 
                "현재 설정을 저장하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 설정 저장 로직
                QMessageBox.information(self, "저장 완료", "설정이 성공적으로 저장되었습니다.")
                print("설정 저장 완료")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 중 오류가 발생했습니다: {e}")

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
