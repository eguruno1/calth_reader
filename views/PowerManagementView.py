# -*- coding: utf-8 -*-
"""
Power Management View - 전원 관리 설정 화면
"""
import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update


class PowerManagementView(QMainWindow):
    """전원 관리 설정 화면"""
    
    switch_to_settings = pyqtSignal()  # 설정 화면으로 돌아가기

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'PowerManagementViewWindow.ui'
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
        self.btn_timeout_setting.clicked.connect(self.on_timeout_setting_clicked)
        self.btn_shutdown.clicked.connect(self.on_shutdown_clicked)
        
        # 하단 버튼들 연결
        self.btn_reset.clicked.connect(self.on_reset_clicked)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def load_current_settings(self):
        """현재 설정 정보 로드"""
        try:
            # 기본 설정값들 설정
            self.label_timeout_current.setText("10분")
            self.label_shutdown_status.setText("활성화됨")
            
        except Exception as e:
            print(f"설정 로드 실패: {e}")

    def on_timeout_setting_clicked(self):
        """Set Timeout 설정 버튼 클릭"""
        try:
            from PyQt5.QtWidgets import QInputDialog
            
            # 현재 타임아웃 값 가져오기
            current_timeout = 10  # 기본값 10분
            
            # 타임아웃 값 입력 대화상자
            timeout_options = ["5분", "10분", "15분", "30분", "60분", "절전 해제"]
            item, ok = QInputDialog.getItem(
                self, 
                "절전 타임아웃 설정", 
                "절전 모드 진입 시간을 선택하세요:",
                timeout_options,
                1,  # 기본 선택 (10분)
                False
            )
            
            if ok and item:
                # 설정 적용 확인
                reply = QMessageBox.question(
                    self, 
                    "Info", 
                    f"절전 타임아웃을 '{item}'으로 설정하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 실제 타임아웃 설정 로직
                    self.label_timeout_current.setText(item)
                    QMessageBox.information(self, "Info", f"절전 타임아웃이 '{item}'으로 설정되었습니다.")
                    print(f"절전 타임아웃 설정: {item}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def on_shutdown_clicked(self):
        """Shutdown 버튼 클릭"""
        try:
            # 시스템 종료 확인 대화상자
            reply = QMessageBox.question(
                self, 
                "Info", 
                "시스템을 종료하시겠습니까?\n모든 작업이 저장되고 시스템이 안전하게 종료됩니다.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 종료 전 마지막 확인
                final_reply = QMessageBox.warning(
                    self, 
                    "Warning", 
                    "정말로 시스템을 종료하시겠습니까?\n이 작업은 취소할 수 없습니다.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if final_reply == QMessageBox.Yes:
                    # 실제 시스템 종료 로직
                    QMessageBox.information(self, "Info", "시스템을 종료합니다.\n잠시 후 전원이 꺼집니다.")
                    print("시스템 종료 요청")
                    # TODO: 실제 시스템 종료 명령 실행
                    # import os
                    # os.system("shutdown -h now")  # Linux/macOS
                    # os.system("shutdown /s /t 0")  # Windows
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

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
                print("전원 관리 설정 초기화 완료")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 초기화 중 오류가 발생했습니다: {e}")

    def on_apply_clicked(self):
        """적용 버튼 클릭 - 현재 설정으로 저장하기"""
        try:
            reply = QMessageBox.question(
                self, 
                "설정 저장", 
                "현재 전원 관리 설정을 저장하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 설정 저장 로직
                QMessageBox.information(self, "저장 완료", "전원 관리 설정이 성공적으로 저장되었습니다.")
                print("전원 관리 설정 저장 완료")
                
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
