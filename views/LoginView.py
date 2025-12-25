# -*- coding: utf-8 -*-
"""
Login View - 로그인 화면
"""
import os
from PyQt5.QtWidgets import QWidget, QMessageBox, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QEvent, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5 import uic
from controllers import app_controller
from views.VKeyboard import VKeyboard

"""
Session Save
"""
from database.audit_logger import write_audit_log
from common.session_context import get_session_context

class LoginView(QWidget):
    """로그인 화면"""
    
    # 시그널 정의
    login_success = pyqtSignal()
    switch_to_home = pyqtSignal()
    switch_to_qc = pyqtSignal()  # QC Test로 진입
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.keyboard_animation = None  # 키보드 애니메이션
        self.form_animation = None  # 폼 애니메이션
        self.original_form_pos = None  # 원래 폼 위치
        self.target_context = None  # QC 진입 컨텍스트 등
        self.keyboard_auto_shown = False  # 키보드 자동 표시 여부 플래그
        self.setup_ui()
        self.setup_virtual_keyboard()
        self.connect_signals()
    
    def setup_ui(self):
        """UI 설정 - UI 파일 로드"""
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'LoginViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Login', ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # UI 요소 참조 설정 (애니메이션용)
        self.login_frame = self.frame_login
        self.password_input = self.lineEdit_password
        self.user_id_input = self.lineEdit_user_id
        self.login_button = self.pushButton_login
        self.back_button = self.pushButton_back

    # =========================
    # Signals
    # =========================    
    def connect_signals(self):
        """시그널 연결"""
        # UI 요소 시그널 연결
        self.back_button.clicked.connect(self.go_back)
        self.login_button.clicked.connect(self.attempt_login)
        
        # Enter 키 처리 추가
        self.user_id_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        
        # 이벤트 필터 설치 (키보드 표시용)
        self.user_id_input.installEventFilter(self)
        self.password_input.installEventFilter(self)
    
    def _connect_login_signals(self):
        """로그인 시그널 연결"""
        try:
            # 사용자 서비스 시그널 연결
            app_controller.user_service.login_success.connect(self.on_login_success)
            app_controller.user_service.login_failed.connect(self.on_login_failed)
        except Exception as e:
            print(f"로그인 시그널 연결 오류: {e}")
    
    def _disconnect_login_signals(self):
        """로그인 시그널 연결 해제"""
        try:
            # 시그널 연결 해제
            app_controller.user_service.login_success.disconnect(self.on_login_success)
            app_controller.user_service.login_failed.disconnect(self.on_login_failed)
        except Exception as e:
            print(f"로그인 시그널 연결 해제 오류: {e}")
    
    # =========================
    # Login Logic
    # =========================
    def attempt_login(self):
        """로그인 시도"""
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text().strip()
        
        if not user_id or not password:
            QMessageBox.warning(self, "입력 오류", "사용자 ID와 비밀번호를 모두 입력해주세요.")
            return
        
        # 로그인 버튼 비활성화
        self.login_button.setText("Logging in...")
        self.login_button.setEnabled(False)
        
        # 로그인 시도
        try:
            # 실제 검증은 UserService에서 수행
            success = app_controller.user_service.login(user_id, password)
            # 버튼 상태 복원
            QTimer.singleShot(1000, self.reset_login_button)
        except Exception as e:
            print(f"로그인 시도 오류: {e}")
            self.reset_login_button()
            QMessageBox.critical(self, "오류", f"로그인 중 오류가 발생했습니다: {str(e)}")
    
    def reset_login_button(self):
        """로그인 버튼 상태 복원"""
        self.login_button.setText("Login")
        self.login_button.setEnabled(True)
    
    def set_context(self, context: str):
        """로그인 컨텍스트 설정 (예: 'qc' - QC Test 진입용)"""
        self.target_context = context
    
    def on_login_success(self, user_id: str):
        """로그인 성공 처리"""
        print(f"로그인 성공: {user_id}, 컨텍스트: {self.target_context}")

        """
        로그인 성공
        role 판단은 반드시 UserService 결과 기준
        """
        user_info = app_controller.user_service.get_user_info()

        role = user_info.get("role", "").lower()
        print(f"Login success: {user_id}, role={role}")

        """Session + Audit Log Save"""
        ctx = get_session_context()

        write_audit_log(
            action      = "LOGIN",
            table_name  = "users",
            record_id   = ctx["user_pk"],       # ⭐ BIGINT
            user_id     = ctx["user_pk"],       # ⭐ FK
            old_values  = {"password": "***"},
            new_values  = {"password": "***"},
            session_id  = ctx["session_id"],
            ip_address  = ctx["ip_address"],
            user_agent  = ctx["user_agent"]
        )

        self.clear_form()
        
        # QC 컨텍스트인 경우 권한 확인 후 QC로 진입
        if self.target_context == "qc":
            try:
                # Operator 만 권한이 있는지 확인
                if (role == "operator"):
                    # QC로 진입하도록 시그널 발생
                    print("QC 권한 확인됨 - QC Test로 진입")
                    self.switch_to_qc.emit()
                else:
                    # 권한이 없으면 홈으로 이동
                    QMessageBox.warning(self, "권한 부족", "QC Test는 Operator 권한이 필요합니다.")
                    self.login_success.emit()
            except Exception as e:
                print(f"QC 진입 처리 오류: {e}")
                self.login_success.emit()
        else:
            # 일반 로그인 성공
            self.login_success.emit()

        # 컨텍스트 초기화
        self.target_context = None
    
    def on_login_failed(self, error_message: str):
        """로그인 실패 처리"""
        QMessageBox.warning(self, "로그인 실패", error_message)
        self.password_input.clear()
        self.password_input.setFocus()
    
    # =========================
    # Utils
    # =========================
    def clear_form(self):
        """폼 초기화"""
        self.user_id_input.clear()
        self.password_input.clear()
        # 키보드 자동 표시 플래그 초기화
        self.keyboard_auto_shown = False
    
    def go_back(self):
        """뒤로가기"""
        self.clear_form()
        self.switch_to_home.emit()
    
    # =========================
    # Qt Events
    # =========================
    def showEvent(self, event):
        """화면 표시시 포커스 설정 및 시그널 연결"""
        super().showEvent(event)
        # 로그인 화면이 표시될 때만 시그널 연결
        self._connect_login_signals()
        # 사용자 ID 입력 필드에 포커스를 주고 키보드를 자동으로 표시
        QTimer.singleShot(100, self._focus_and_show_keyboard)

    def hideEvent(self, event):
        """화면 숨김시 시그널 연결 해제 및 상태 초기화"""
        super().hideEvent(event)
        # 로그인 화면이 숨겨질 때 시그널 연결 해제
        self._disconnect_login_signals()
        # 키보드 자동 표시 플래그 초기화
        self.keyboard_auto_shown = False
        # 키보드가 표시되어 있다면 숨기기
        if not self.vkeyboard.isHidden():
            self.vkeyboard.hide()
            if self.original_form_pos:
                self.login_frame.move(self.original_form_pos)

    # =========================
    # Virtual Keyboard
    # =========================
    def setup_virtual_keyboard(self):
        """가상 키보드 설정"""
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()
        self.vkeyboard.key_pressed.connect(self.handle_key_press)
        self.vkeyboard.backspace_pressed.connect(self.handle_backspace)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)
        self.vkeyboard.enter_pressed.connect(self.handle_enter)
        self.position_keyboard()

    def position_keyboard(self):
        """키보드 위치 설정"""
        keyboard_x = (self.width() - self.vkeyboard.width()) // 2
        keyboard_y = self.height()
        self.vkeyboard.move(keyboard_x, keyboard_y)

    def resizeEvent(self, event):
        """화면 크기 변경 시 키보드 위치 재조정"""
        super().resizeEvent(event)
        if hasattr(self, 'vkeyboard'):
            self.position_keyboard()

    def eventFilter(self, obj, event):
        """이벤트 필터링 - 입력 필드 클릭 시 키보드 표시"""
        if obj in [self.user_id_input, self.password_input] and event.type() == QEvent.MouseButtonPress:
            # 키보드가 이미 표시되어 있지 않을 때만 표시
            if self.vkeyboard.isHidden():
                self.show_virtual_keyboard()
            return True
        elif event.type() == QEvent.MouseButtonPress:
            if not self.is_click_on_keyboard(event.globalPos()) and not self.is_click_on_input_field(event.globalPos()):
                self.hide_keyboard()
        return super().eventFilter(obj, event)

    def show_virtual_keyboard(self):
        """가상 키보드 표시"""
        # 이미 키보드가 표시되어 있으면 중복 실행 방지
        if not self.vkeyboard.isHidden():
            return
            
        if self.keyboard_animation and self.keyboard_animation.state() == QPropertyAnimation.Running:
            self.keyboard_animation.stop()
        
        # 로그인 폼을 위로 이동
        self.move_form_up()
        
        self.vkeyboard.show()
        start_y = self.height()
        end_y = self.height() - self.vkeyboard.height()
        
        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
        self.keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.keyboard_animation.start()

    def hide_keyboard(self):
        """가상 키보드 숨기기"""
        # 이미 키보드가 숨겨져 있으면 중복 실행 방지
        if self.vkeyboard.isHidden():
            return
            
        if self.keyboard_animation and self.keyboard_animation.state() == QPropertyAnimation.Running:
            self.keyboard_animation.stop()
        
        start_y = self.vkeyboard.y()
        end_y = self.height()
        
        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
        self.keyboard_animation.setEasingCurve(QEasingCurve.InCubic)
        self.keyboard_animation.finished.connect(self.on_keyboard_hidden)
        self.keyboard_animation.start()
    
    def on_keyboard_hidden(self):
        """키보드가 완전히 숨겨진 후 호출"""
        self.vkeyboard.hide()
        # 로그인 폼을 원래 위치로 복원
        self.restore_form_position()

    def move_form_up(self):
        """로그인 폼을 위로 이동"""
        if self.form_animation:
            self.form_animation.stop()
        
        # 원래 위치 저장 (한 번만)
        if self.original_form_pos is None:
            self.original_form_pos = self.login_frame.pos()
        
        # 키보드 높이만큼 위로 이동 (적절한 여백 포함)
        keyboard_height = self.vkeyboard.height()
        move_distance = keyboard_height // 2  # 키보드 높이의 절반만큼 위로
        
        current_pos = self.login_frame.pos()
        target_y = max(50, current_pos.y() - move_distance)  # 최소 50px 여백 유지
        target_pos = QPoint(current_pos.x(), target_y)
        
        self.form_animation = QPropertyAnimation(self.login_frame, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(current_pos)
        self.form_animation.setEndValue(target_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    def restore_form_position(self):
        """로그인 폼을 원래 위치로 복원"""
        if self.form_animation:
            self.form_animation.stop()
        
        if self.original_form_pos is None:
            return
        
        current_pos = self.login_frame.pos()
        
        self.form_animation = QPropertyAnimation(self.login_frame, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(current_pos)
        self.form_animation.setEndValue(self.original_form_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    def handle_key_press(self, key):
        """키 입력 처리"""
        focused_widget = self.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            if key == ' ':  # Space key
                focused_widget.insert(' ')
            else:
                focused_widget.insert(key)

    def handle_backspace(self):
        """백스페이스 처리"""
        focused_widget = self.focusWidget()
        if isinstance(focused_widget, QLineEdit):
            focused_widget.backspace()

    def handle_enter(self):
        """Enter 키 처리"""
        self.hide_keyboard()
        self.attempt_login()

    def is_click_on_keyboard(self, global_pos):
        """키보드 영역 클릭 확인"""
        if self.vkeyboard.isHidden():
            return False
        keyboard_rect = self.vkeyboard.geometry()
        keyboard_global_pos = self.mapToGlobal(keyboard_rect.topLeft())
        keyboard_global_rect = keyboard_rect.translated(keyboard_global_pos - keyboard_rect.topLeft())
        return keyboard_global_rect.contains(global_pos)

    def is_click_on_input_field(self, global_pos):
        """입력 필드 영역 클릭 확인"""
        for field in [self.user_id_input, self.password_input]:
            field_rect = field.geometry()
            field_global_pos = self.mapToGlobal(field_rect.topLeft())
            field_global_rect = field_rect.translated(field_global_pos - field_rect.topLeft())
            if field_global_rect.contains(global_pos):
                return True
        return False

    def _focus_and_show_keyboard(self):
        """사용자 ID 필드에 포커스를 주고 키보드를 표시"""
        self.user_id_input.setFocus()
        # 자동 표시 플래그가 설정되지 않았을 때만 키보드 표시
        if not self.keyboard_auto_shown:
            self.keyboard_auto_shown = True
            # 잠시 후 키보드 표시 (포커스가 완전히 설정된 후)
            QTimer.singleShot(200, self.show_virtual_keyboard)
    
    def _set_focus_only(self):
        """사용자 ID 필드에 포커스만 설정 (키보드는 표시하지 않음)"""
        self.user_id_input.setFocus()
