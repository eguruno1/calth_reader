import os
import json
import threading

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore    import QTimer, pyqtSignal, QDateTime, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QPixmap
from PyQt5           import uic

from common.session_context import get_session_context

from views.Utils     import (update_date_time, start_date_time_update, stop_date_time_update)

class HomeView(QMainWindow):
    switch_to_select      = pyqtSignal()
    switch_to_info        = pyqtSignal()
    switch_to_resultList  = pyqtSignal()
    switch_to_operator    = pyqtSignal()
    switch_to_settings    = pyqtSignal()
    switch_to_login       = pyqtSignal(str)  # 로그인 화면으로 전환 (컨텍스트 포함)
    switch_to_admin_login = pyqtSignal(str)  # Admin 전용 로그인 (target 포함)
    switch_to_qc          = pyqtSignal()  # QC Test로 전환

    def __init__(self, controller, uart_model=None, parent=None):
        super().__init__(parent)

        # 프로젝트 루트 디렉토리
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'HomeViewWindow.ui'
        ui_file     = os.path.join(project_root, 'ui', 'Home', ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")   
        
        # 버튼 연결
        self.pushButton_StandardTest.clicked.connect(self.on_standard_test_button_clicked)
        self.pushButton_ReadOnly.clicked.connect(self.on_read_only_button_clicked)

        self.pushButton_QCTest.clicked.connect(self.on_qc_test_button_clicked)
        # 인증을 위해 UI에서 버튼 삭제
        # self.pushButton_Calibration.clicked.connect(self.on_calibration_button_clicked)
        self.pushButton_Review.clicked.connect(self.on_review_button_clicked)
        self.pushButton_Settings.clicked.connect(self.on_settings_button_clicked)
        self.pushButton_Statistics.clicked.connect(self.on_statistics_button_clicked)

        # 날짜와 시간 표시
        self.update_date_time()
        
        # 사용자 시그널 연결
        self.connect_user_signals()
        
        # 초기 로그인 상태 설정
        self.init_login_status()

        # JSON 파일 경로 설정
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        # Version
        # info.json에서 버전 정보 읽기 및 표시
        self.display_version()

        #####################################################
        # Battery Status
        self.uart_model = uart_model


    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)
        # stop_battery_update(self)

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def update_json_file(self, button_name):
        try:
            with open(self.current_json_path, 'r+') as f:
                data = json.load(f)
                data['select_menu'] = button_name
                # 인증 COVID19  고정.
                data['test_type1'] = "COVID19" 
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"JSON 파일 업데이트 중 오류 발생: {e}")

    def on_standard_test_button_clicked(self):
        # TestInfoView 로 이동.
        print("Standard Test 버튼이 클릭되었습니다.")

        # ▶ 로그인 체크
        if not self._require_login("StandardTest"):
            return
        
        self.update_json_file("StandardTest")
        self.switch_to_select.emit()

    def on_read_only_button_clicked(self):
        print("Read Only 버튼이 클릭되었습니다.")

        # ▶ 로그인 체크
        if not self._require_login("ReadOnly"):
            return
        
        self.update_json_file("ReadOnly")
        self.switch_to_select.emit()

    def on_qc_test_button_clicked(self):
        print("QC Test 버튼이 클릭되었습니다.")

        # ▶ 로그인 체크
        if not self._require_login("ReadOnly"):
            return
        
        self.update_json_file("QCTest")
        """
        try:
            from controllers import app_controller
            from models.user_model import UserRole
            
            if app_controller.user_service.is_logged_in():
                # 현재 사용자의 권한 확인
                if (app_controller.user_service.has_permission(UserRole.OPERATOR) or 
                    app_controller.user_service.has_permission(UserRole.ADMIN)):
                    # Admin 또는 Operator로 로그인된 상태: 바로 QC로 진입
                    print("Admin/Operator로 로그인됨 - QC Test로 바로 진입")
                    self.switch_to_qc.emit()
                else:
                    # Viewer로 로그인된 상태: 일반 로그인 페이지로 안내
                    print("Viewer 계정으로 로그인됨 - 일반 로그인 페이지로 안내")
                    self.switch_to_login.emit("qc")
            else:
                # 로그인되지 않은 상태: 일반 로그인 페이지로 안내
                print("로그인 필요 - 일반 로그인 페이지로 이동")
                self.switch_to_login.emit("qc")
        except Exception as e:
            print(f"QC Test 진입 오류: {e}")
            # 오류 시 일반 로그인 페이지로 이동
            self.switch_to_login.emit("qc")
        """

    def on_calibration_button_clicked(self):
        print("Calibration 버튼이 클릭되었습니다.")
        # Admin 전용 로그인 창으로 이동 (target: calibration)
        self.switch_to_admin_login.emit("calibration")

    def on_review_button_clicked(self):
        print("Review 버튼이 클릭되었습니다.")

        # ▶ 로그인 체크
        if not self._require_login("Review"):
            return
        
        self.switch_to_resultList.emit()

    def on_settings_button_clicked(self):
        print("Settings 버튼이 클릭되었습니다.")
        # Admin 전용 로그인 창으로 이동 (target: settings)
        self.switch_to_admin_login.emit("settings")

    def on_statistics_button_clicked(self):
        print("로그인/로그아웃 버튼이 클릭되었습니다.")
        try:
            from controllers import app_controller
            if app_controller.user_service.is_logged_in():
                # 로그아웃 후 로그인 화면으로 이동
                app_controller.user_service.logout()
                self.switch_to_login.emit("")
            else:
                # 로그인 화면으로 이동
                self.switch_to_login.emit("")
        except Exception as e:
            print(f"로그인/로그아웃 처리 오류: {e}")
            self.switch_to_info.emit()  # 오류 시 기존 동작

    def update_date_time(self):
        update_date_time(self)


    # 로그인 관련 메서드들
    def init_login_status(self):
        """로그인 상태 초기화"""
        self.update_login_button()
    
    def connect_user_signals(self):
        """사용자 서비스 시그널 연결"""
        try:
            from controllers import app_controller
            # 기존 연결이 있으면 해제
            try:
                app_controller.user_service.user_changed.disconnect(self.on_user_changed)
                app_controller.user_service.logout_completed.disconnect(self.on_logout_completed)
                app_controller.user_service.login_success.disconnect(self.on_login_success_update)
            except:
                pass
            
            # 새로운 연결 설정
            app_controller.user_service.user_changed.connect(self.on_user_changed)
            app_controller.user_service.logout_completed.connect(self.on_logout_completed)
            app_controller.user_service.login_success.connect(self.on_login_success_update)
            print("HomeView: 사용자 시그널 연결 완료")
        except Exception as e:
            print(f"사용자 시그널 연결 오류: {e}")
    
    def on_login_success_update(self, user_id: str):
        """로그인 성공 시 UI 업데이트"""
        print(f"HomeView: 로그인 성공 시그널 수신 - {user_id}")
        self.update_login_button()
    
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
                if not user_id:
                    user_id = "Unknown"
                button_text = f"{user_id}\nLog Out"
                self.pushButton_Statistics.setText(button_text)
                print(f"{user_id} 로그인 상태")
            else:
                # 로그아웃된 상태: Log In 표시
                self.pushButton_Statistics.setText("Log In")
                print("로그아웃 상태")
                
        except Exception as e:
            print(f"로그인 버튼 업데이트 오류: {e}")
            self.pushButton_Statistics.setText("Log In")
    
    def showEvent(self, event):
        """화면 표시시 로그인 상태 업데이트"""
        super().showEvent(event)
        # 날짜/시간 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        # 로그인 상태 업데이트
        QTimer.singleShot(200, self.update_login_button)
        # 배터리 상태 업데이트s
        from controllers import app_controller
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)

    #==========================================
    # --- 권한 체크 ---
    #==========================================
    def _check_admin_access(self, target: str) -> bool:
        """
        admin 전용 메뉴 접근 체크
        :param target: 'settings' | 'calibration'
        :return: True (접근 허용), False (차단)
        """
        session_user = get_session_context()
        print(f"[HomeView] {target} 접근 체크 - session_user: {session_user}")

        # 로그인 안 된 경우 → admin 로그인 화면
        if not session_user:
            self.switch_to_admin_login.emit(target)
            return False

        # admin 이 아닌 경우
        if session_user.get("role") != "admin":
            QMessageBox.warning(
                self,
                "접근 제한",
                "관리자만 이용할 수 있는 메뉴 입니다."
            )
            return False

        return True
    
    # ==========================================================
    # LOGIN CHECK (COMMON)
    # ==========================================================
    def _require_login(self, target: str = "") -> bool:
        """
        로그인 필요 여부 체크
        :param target: 로그인 후 이동 목적 (optional)
        :return: True (로그인됨), False (차단됨)
        """
        try:
            from controllers import app_controller

            if app_controller.user_service.is_logged_in():
                return True

            # 로그인 안 된 경우 → 로그인 화면으로 이동
            QMessageBox.information(
                self,
                "로그인 필요",
                "해당 기능을 사용하려면 로그인이 필요합니다."
            )
            self.switch_to_login.emit(target)
            return False

        except Exception as e:
            print(f"[HomeView] 로그인 체크 오류: {e}")
            self.switch_to_login.emit(target)
            return False

    def display_version(self):
        version = self.get_version_from_info()
        self.label_device_info.setText(f"Device: Ready | Version: {version}")

    def get_version_from_info(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            info_path = os.path.join(current_dir, '../info', 'info.json')
            
            with open(info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
            return info.get('sw_version', 'Unknown')
        except Exception as e:
            print(f"Error reading version from info.json: {str(e)}")
            return "Unknown"
    
    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        """
        옵저버 콜백
        UARTModel.notify_observers()와 1:1 대응
        """
        print(f"[HomeView] on_uart_event: {event_type}, {data}")
        print(
            f"[HomeView][{self.__class__.__name__}] on_uart_event "
            f"thread={threading.current_thread().name}"
        )

        if event_type == "battery_changed" and data:
            # ❗ UART RX 스레드 → UI 스레드로 전달
            QMetaObject.invokeMethod(
                self,
                "_update_battery_ui",
                Qt.QueuedConnection,
                Q_ARG(object, data)
            )

    @pyqtSlot(object)
    def _update_battery_ui(self, battery_info):
        """
        UARTModel battery_changed 이벤트 수신 시 호출
        battery_info: BatteryInfo
        """
        # 🔒 UI 위젯 생성 여부 확인
        if not hasattr(self, "label_BatteryGuage") or not hasattr(self, "label_BatteryGuageTxt"):
            return

        try:
            icon_name = battery_info.get_icon_name()
            print(f"[HomeView] Battery UI icon_name: {icon_name}")

            # ✅ 프로젝트 루트 기준 아이콘 경로
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[HomeView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[HomeView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[HomeView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[HomeView] Battery UI update error: {e}")
