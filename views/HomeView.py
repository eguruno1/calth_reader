import os
import json

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore    import QTimer, pyqtSignal, QDateTime
from PyQt5.QtGui     import QPixmap
from PyQt5           import uic

from views.Utils     import update_date_time, start_date_time_update, stop_date_time_update

class HomeView(QMainWindow):
    switch_to_select     = pyqtSignal()
    switch_to_info       = pyqtSignal()
    switch_to_resultList = pyqtSignal()
    switch_to_operator   = pyqtSignal()
    switch_to_settings   = pyqtSignal()
    switch_to_login      = pyqtSignal()  # 로그인 화면으로 전환

    def __init__(self, parent=None):
        super().__init__(parent)

        # 프로젝트 루트 디렉토리
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'HomeViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")   
        
        # 버튼 연결
        self.pushButton_StandardTest.clicked.connect(self.on_standard_test_button_clicked)
        self.pushButton_ReadOnly.clicked.connect(self.on_read_only_button_clicked)

        self.pushButton_QCTest.clicked.connect(self.on_qc_test_button_clicked)
        self.pushButton_Calibration.clicked.connect(self.on_calibration_button_clicked)
        self.pushButton_Review.clicked.connect(self.on_review_button_clicked)
        self.pushButton_Settings.clicked.connect(self.on_settings_button_clicked)
        self.pushButton_Statistics.clicked.connect(self.on_statistics_button_clicked)

        # 날짜와 시간 표시
        self.update_date_time()

        # JSON 파일 경로 설정
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')
        
        # 배터리 상태 초기화
        self.init_battery_status()
        
        # 배터리 상태 업데이트 타이머 (30초마다)
        self.battery_timer = QTimer()
        self.battery_timer.timeout.connect(self.update_battery_status)
        self.battery_timer.start(30000)  # 30초
        
        # 로그인 상태 초기화
        self.init_login_status()
        
        # 사용자 서비스 시그널 연결
        self.connect_user_signals()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def update_date_time(self):
        current_datetime = QDateTime.currentDateTime()
        formatted_datetime = current_datetime.toString("yyyy-MM-dd  HH:mm")
        if hasattr(self, 'label_DateNClock'):
            self.label_DateNClock.setText(formatted_datetime)

        # 기존 타이머가 있다면 중지
        if hasattr(self, 'date_time_timer'):
            self.date_time_timer.stop()

        # 새 타이머 생성 및 시작
        self.date_time_timer = QTimer(self)
        self.date_time_timer.timeout.connect(self.update_date_time)
        self.date_time_timer.start(1000)  # 1초마다 업데이트

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def update_json_file(self, button_name):
        try:
            with open(self.current_json_path, 'r+') as f:
                data = json.load(f)
                data['test_type0'] = button_name
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"JSON 파일 업데이트 중 오류 발생: {e}")

    def on_standard_test_button_clicked(self):
        print("Standard Test 버튼이 클릭되었습니다.")
        self.update_json_file("StandardTest")
        self.switch_to_select.emit()

    def on_read_only_button_clicked(self):
        print("Read Only 버튼이 클릭되었습니다.")
        self.update_json_file("ReadOnly")
        self.switch_to_select.emit()

    def on_qc_test_button_clicked(self):
        print("QC Test 버튼이 클릭되었습니다.")
        # QC Test 관련 로직 추가 예정
        pass

    def on_calibration_button_clicked(self):
        print("Calibration 버튼이 클릭되었습니다.")
        try:
            from controllers import app_controller
            from models.user_model import UserRole
            
            # Admin 권한 확인
            if app_controller.user_service.has_permission(UserRole.ADMIN):
                print("Admin 권한 확인됨: Calibration 기능 접근 허용")
                # Calibration 관련 로직 추가 예정
                pass
            else:
                from PyQt5.QtWidgets import QMessageBox
                current_user = app_controller.user_service.get_current_user()
                if current_user:
                    QMessageBox.warning(self, "권한 부족", 
                                      f"Calibration 기능은 Admin 권한이 필요합니다.\n현재 권한: {current_user.role.value}")
                else:
                    QMessageBox.warning(self, "로그인 필요", 
                                      "Calibration 기능을 사용하려면 Admin 계정으로 로그인해주세요.")
        except Exception as e:
            print(f"Calibration 버튼 처리 오류: {e}")

    def on_review_button_clicked(self):
        print("Review 버튼이 클릭되었습니다.")
        self.switch_to_resultList.emit()

    def on_settings_button_clicked(self):
        print("Settings 버튼이 클릭되었습니다.")
        try:
            from controllers import app_controller
            from models.user_model import UserRole
            
            # Admin 권한 확인
            if app_controller.user_service.has_permission(UserRole.ADMIN):
                print("Admin 권한 확인됨: Settings 기능 접근 허용")
                self.switch_to_settings.emit()
            else:
                current_user = app_controller.user_service.get_current_user()
                if current_user:
                    QMessageBox.warning(self, "권한 부족", 
                                      f"Settings 기능은 Admin 권한이 필요합니다.\n현재 권한: {current_user.role.value}")
                else:
                    QMessageBox.warning(self, "로그인 필요", 
                                      "Settings 기능을 사용하려면 Admin 계정으로 로그인해주세요.")
        except Exception as e:
            print(f"Settings 버튼 처리 오류: {e}")
            # 오류 시 기본 동작
            self.switch_to_settings.emit()

    def on_statistics_button_clicked(self):
        print("로그인/로그아웃 버튼이 클릭되었습니다.")
        try:
            from controllers import app_controller
            if app_controller.user_service.is_logged_in():
                # 로그아웃 후 로그인 화면으로 이동
                app_controller.user_service.logout()
                self.switch_to_login.emit()
            else:
                # 로그인 화면으로 이동
                self.switch_to_login.emit()
        except Exception as e:
            print(f"로그인/로그아웃 처리 오류: {e}")
            self.switch_to_info.emit()  # 오류 시 기존 동작

    def update_date_time(self):
        update_date_time(self)

    def init_battery_status(self):
        """배터리 상태 초기화"""
        try:
            # 실제 배터리 상태로 초기화
            self.update_battery_status()
        except Exception as e:
            print(f"배터리 상태 초기화 오류: {e}")
            # 기본값으로 설정
            try:
                from controllers import app_controller
                app_controller.uart_model.update_battery_info(75, False)
                self.update_battery_display()
            except:
                self.set_battery_icon("Battery_Icon-050.png")
    
    def update_battery_status(self):
        """배터리 상태 업데이트 (UART 서비스를 통해 실제 배터리 정보 읽기)"""
        try:
            from controllers import app_controller
            
            # 컨트롤러를 통해 배터리 상태 읽기
            battery_data = app_controller.get_battery_status()
            
            if battery_data:
                print(f"배터리 상태 업데이트: {battery_data.get('level', 50)}% (충전중: {battery_data.get('is_charging', False)})")
            else:
                print("배터리 상태를 읽을 수 없습니다.")
            
            # UI 업데이트
            self.update_battery_display()
            
        except Exception as e:
            print(f"배터리 상태 업데이트 오류: {e}")
            # 오류 발생 시 기본값으로 설정
            try:
                from controllers import app_controller
                app_controller.uart_model.update_battery_info(50, False)
                self.update_battery_display()
            except:
                pass
    
    def update_battery_display(self):
        """배터리 디스플레이 업데이트"""
        try:
            from controllers import app_controller
            battery_info = app_controller.uart_model.get_battery_info()
            
            if battery_info:
                # 아이콘 업데이트
                icon_name = battery_info.get_icon_name()
                self.set_battery_icon(icon_name)
                
                # 텍스트 업데이트
                # status_text = battery_info.get_status_text()
                # self.label_BatteryGuage.setText(status_text)
                
                # 배터리 레벨에 따른 색상 변경
                if battery_info.level <= 10:
                    color = "color: red;"
                elif battery_info.level <= 25:
                    color = "color: orange;"
                else:
                    color = "color: black;"
                
                # self.label_BatteryGuage.setStyleSheet(f"QLabel {{ {color} }}")
                
        except Exception as e:
            print(f"배터리 디스플레이 업데이트 오류: {e}")
    
    def set_battery_icon(self, icon_filename: str):
        """배터리 아이콘 설정"""
        try:
            # 프로젝트 루트에서 이미지 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            icon_path = os.path.join(project_root, 'ui', 'image', 'Icon', icon_filename)
            
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                self.label_4.setPixmap(pixmap)
                print(f"배터리 아이콘 변경: {icon_filename}")
            else:
                print(f"배터리 아이콘 파일 없음: {icon_path}")
                
        except Exception as e:
            print(f"배터리 아이콘 설정 오류: {e}")
    
    def on_uart_event(self, event_type: str, data=None):
        """UART 이벤트 핸들러 (옵저버 패턴)"""
        if event_type == 'battery_changed':
            self.update_battery_display()
    
    # 로그인 관련 메서드들
    def init_login_status(self):
        """로그인 상태 초기화"""
        self.update_login_button()
    
    def connect_user_signals(self):
        """사용자 서비스 시그널 연결"""
        try:
            from controllers import app_controller
            app_controller.user_service.user_changed.connect(self.on_user_changed)
            app_controller.user_service.logout_completed.connect(self.on_logout_completed)
        except Exception as e:
            print(f"사용자 시그널 연결 오류: {e}")
    
    def on_user_changed(self, user_info: dict):
        """사용자 정보 변경 시 호출"""
        print(f"사용자 변경: {user_info}")
        self.update_login_button()
    
    def on_logout_completed(self):
        """로그아웃 완료 시 호출"""
        print("로그아웃 완료")
        self.update_login_button()
    
    def update_login_button(self):
        """로그인 상태에 따라 버튼 텍스트 업데이트"""
        try:
            from controllers import app_controller
            
            if app_controller.user_service.is_logged_in():
                # 로그인된 상태: 사용자 ID와 Log Out 표시
                user_id = app_controller.user_service.get_current_user_id()
                user_name = app_controller.user_service.get_current_user_display_name()
                
                # 버튼 텍스트 변경
                button_text = f"{user_id}\nLog Out"
                self.pushButton_Statistics.setText(button_text)
                
                print(f"로그인 상태: {user_name} ({user_id})")
            else:
                # 로그아웃된 상태: Log In 표시
                self.pushButton_Statistics.setText("Log In")
                print("로그아웃 상태")
            
            # 권한 기반 UI 업데이트
            self.update_permission_based_ui()
                
        except Exception as e:
            print(f"로그인 버튼 업데이트 오류: {e}")
            self.pushButton_Statistics.setText("Log In")
    
    def update_permission_based_ui(self):
        """권한에 따른 UI 업데이트"""
        try:
            from controllers import app_controller
            from models.user_model import UserRole
            
            # Admin 권한 확인
            has_admin_permission = app_controller.user_service.has_permission(UserRole.ADMIN)
            
            # Calibration 버튼 권한 제어
            self.update_button_permission(
                self.pushButton_Calibration, 
                has_admin_permission, 
                "Calibration"
            )
            
            # Settings 버튼 권한 제어
            self.update_button_permission(
                self.pushButton_Settings, 
                has_admin_permission, 
                "Settings"
            )
            
            if has_admin_permission:
                print("Admin 권한: Calibration, Settings 버튼 활성화")
            else:
                current_user = app_controller.user_service.get_current_user()
                if current_user:
                    print(f"{current_user.role.value} 권한: Calibration, Settings 버튼 비활성화")
                else:
                    print("비로그인 상태: Calibration, Settings 버튼 비활성화")
                    
        except Exception as e:
            print(f"권한 기반 UI 업데이트 오류: {e}")
    
    def update_button_permission(self, button, has_permission: bool, button_name: str):
        """버튼 권한 상태 업데이트"""
        try:
            if has_permission:
                # 권한 있음: 버튼 활성화
                button.setEnabled(True)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #505050;
                        color: white;
                        border: none;
                        border-radius: 5px;
                    }
                    QPushButton:hover {
                        background-color: #606060;
                    }
                    QPushButton:pressed {
                        background-color: #404040;
                    }
                """)
            else:
                # 권한 없음: 버튼 비활성화
                button.setEnabled(False)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #303030;
                        color: #808080;
                        border: none;
                        border-radius: 5px;
                    }
                    QPushButton:disabled {
                        background-color: #303030;
                        color: #606060;
                    }
                """)
                
        except Exception as e:
            print(f"{button_name} 버튼 권한 업데이트 오류: {e}")
    
    def showEvent(self, event):
        """화면 표시시 로그인 상태 업데이트"""
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        # 로그인 상태 및 권한 업데이트
        QTimer.singleShot(200, self.update_login_button)
