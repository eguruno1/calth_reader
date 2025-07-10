import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore    import pyqtSignal, QTimer
from PyQt5           import uic

from views.Utils     import start_date_time_update, stop_date_time_update
from views.SystemStatus import add_status_overlay, remove_status_overlay
from controllers import app_controller
from config.config import app_config

class OperatorView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'OperatorViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")   
        
        # 뒤로 가기 버튼 연결
        self.pushButton_OperatorBackArrow.clicked.connect(self.on_back_button_clicked)

        # 버튼들 연결
        self.pushButton_Camset.clicked.connect(self.on_camset_button_clicked)
        self.pushButton_Settings.clicked.connect(self.on_settings_button_clicked)
        self.pushButton_Network.clicked.connect(self.on_network_button_clicked)
        self.pushButton_Update.clicked.connect(self.on_update_button_clicked)

        # 디버그 모드 토글 버튼 추가 (기존 버튼이 있다면)
        if hasattr(self, 'pushButton_Debug'):
            self.pushButton_Debug.clicked.connect(self.on_debug_toggle_clicked)

        # 날짜와 시간 업데이트를 위한 타이머 설정
        self.date_time_timer = None

    def showEvent(self, event):
        super().showEvent(event)
        # 뷰가 표시될 때 날짜/시간 업데이트 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        # 시스템 상태 오버레이 추가
        QTimer.singleShot(200, lambda: add_status_overlay(self))

    def closeEvent(self, event):
        # 뷰가 닫힐 때 타이머 정지
        stop_date_time_update(self)
        # 상태 오버레이 제거
        remove_status_overlay(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def on_camset_button_clicked(self):
        """카메라 설정 버튼 클릭"""
        print("Camset 버튼 클릭됨")
        
        # 카메라 상태 확인 및 테스트
        try:
            system_info = app_controller.get_system_info()
            if system_info['camera_ready']:
                # 카메라 테스트 이미지 캡처
                success = app_controller.capture_test_image("test_capture.jpg")
                if success:
                    QMessageBox.information(self, "카메라 테스트", "테스트 이미지가 저장되었습니다.")
                else:
                    QMessageBox.warning(self, "카메라 테스트", "이미지 저장에 실패했습니다.")
            else:
                QMessageBox.warning(self, "카메라 상태", "카메라가 연결되지 않았습니다.")
        except Exception as e:
            QMessageBox.warning(self, "카메라 오류", f"카메라 테스트 중 오류가 발생했습니다: {str(e)}")

    def on_settings_button_clicked(self):
        """설정 버튼 클릭"""
        print("Settings 버튼 클릭됨")
        
        # 현재 시스템 상태 정보 표시
        try:
            system_info = app_controller.get_system_info()
            status_text = f"""현재 시스템 상태:
        
디버그 모드: {'켜짐' if system_info['debug_mode'] else '꺼짐'}
카메라: {'연결됨' if system_info['camera_ready'] else '연결 실패'}
UART: {'연결됨' if system_info['uart_ready'] else '연결 실패'}
전체 시스템: {'준비됨' if system_info['system_ready'] else '제한 모드'}

Ctrl+D: 디버그 모드 토글
Ctrl+Q: 애플리케이션 종료
Ctrl+X: 시스템 종료"""
        
            QMessageBox.information(self, "시스템 정보", status_text)
        except Exception as e:
            QMessageBox.warning(self, "시스템 오류", f"시스템 정보 조회 중 오류가 발생했습니다: {str(e)}")

    def on_network_button_clicked(self):
        """네트워크 버튼 클릭"""
        print("Network 버튼 클릭됨")
        
        # 네트워크 상태 확인 (추후 구현)
        QMessageBox.information(self, "네트워크", "네트워크 설정 기능은 추후 구현 예정입니다.")

    def on_update_button_clicked(self):
        """업데이트 버튼 클릭"""
        print("Update 버튼 클릭됨")
        
        # 업데이트 기능 (추후 구현)
        QMessageBox.information(self, "업데이트", "소프트웨어 업데이트 기능은 추후 구현 예정입니다.")
    
    def on_debug_toggle_clicked(self):
        """디버그 모드 토글 버튼 클릭"""
        current_mode = app_config.is_debug_mode()
        new_mode = not current_mode
        app_config.set_debug_mode(new_mode)
        
        mode_text = "디버그 모드" if new_mode else "실제 하드웨어 모드"
        QMessageBox.information(self, '모드 변경', 
                               f"{mode_text}로 변경되었습니다.\n재시작 후 적용됩니다.")