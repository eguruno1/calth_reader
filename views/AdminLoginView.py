# -*- coding: utf-8 -*-
"""
Admin Login View - Admin 전용 로그인 화면
"""
import os
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QEvent, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5 import uic
from views.VKeyboard import VKeyboard

class AdminLoginView(QWidget):
    """Admin 전용 로그인 화면"""
    
    # 시그널 정의
    login_success = pyqtSignal(str)  # target (calibration/settings)
    switch_to_home = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target = None  # 로그인 성공 후 이동할 대상
        self.keyboard_animation = None  # 키보드 애니메이션
        self.form_animation = None  # 폼 애니메이션
        self.original_form_pos = None  # 원래 폼 위치
        self.setup_ui()
        self.setup_virtual_keyboard()
        self.connect_signals()
    
    def setup_ui(self):
        """UI 설정 - UI 파일 로드"""
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'AdminLoginViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # UI 요소 참조 설정 (애니메이션용)
        self.login_frame = self.frame_login
        self.password_input = self.lineEdit_password
        self.login_button = self.pushButton_login
        self.back_button = self.pushButton_back
    
    def connect_signals(self):
        """시그널 연결"""
        # UI 요소 시그널 연결
        self.back_button.clicked.connect(self.go_back)
        self.login_button.clicked.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)
        
        # 이벤트 필터 설치 (키보드 표시용)
        self.password_input.installEventFilter(self)
    
    def _connect_login_signals(self):
        """로그인 시그널 연결"""
        try:
            from controllers import app_controller
            # 사용자 서비스 시그널 연결
            app_controller.user_service.login_success.connect(self.on_login_success)
            app_controller.user_service.login_failed.connect(self.on_login_failed)
        except Exception as e:
            print(f"Admin 로그인 시그널 연결 오류: {e}")
    
    def _disconnect_login_signals(self):
        """로그인 시그널 연결 해제"""
        try:
            from controllers import app_controller
            # 시그널 연결 해제
            app_controller.user_service.login_success.disconnect(self.on_login_success)
            app_controller.user_service.login_failed.disconnect(self.on_login_failed)
        except Exception as e:
            print(f"Admin 로그인 시그널 연결 해제 오류: {e}")
    
    def set_target(self, target: str):
        """로그인 성공 후 이동할 대상 설정"""
        self.target = target
        
        # 타이틀 업데이트
        title_text = "ADMIN LOGIN"
        
        # 헤더의 타이틀 업데이트
        self.label_title.setText(title_text)
    
    def attempt_login(self):
        """로그인 시도"""
        password = self.password_input.text().strip()
        
        if not password:
            QMessageBox.warning(self, "입력 오류", "비밀번호를 입력해주세요.")
            return
        
        # 로그인 버튼 비활성화
        self.login_button.setText("Logging in...")
        self.login_button.setEnabled(False)
        
        # Admin 계정으로 로그인 시도
        try:
            from controllers import app_controller
            success = app_controller.user_service.login("admin", password)
            
            # 버튼 상태 복원
            QTimer.singleShot(1000, self.reset_login_button)
        except Exception as e:
            print(f"Admin 로그인 시도 오류: {e}")
            self.reset_login_button()
            QMessageBox.critical(self, "오류", f"로그인 중 오류가 발생했습니다: {str(e)}")
    
    def reset_login_button(self):
        """로그인 버튼 상태 복원"""
        self.login_button.setText("Login as Admin")
        self.login_button.setEnabled(True)
    
    def on_login_success(self, user_id: str):
        """로그인 성공 처리"""
        if user_id == "admin":
            print(f"Admin 로그인 성공, 이동할 대상: {self.target}")
            self.clear_form()
            self.login_success.emit(self.target or "")
        else:
            # admin이 아닌 다른 계정으로 로그인됨
            QMessageBox.warning(self, "권한 오류", "Admin 계정만 접근 가능합니다.")
            try:
                from controllers import app_controller
                app_controller.user_service.logout()  # 다른 계정 로그아웃
            except:
                pass
            self.password_input.clear()
            self.password_input.setFocus()
    
    def on_login_failed(self, error_message: str):
        """로그인 실패 처리"""
        QMessageBox.warning(self, "로그인 실패", error_message)
        self.password_input.clear()
        self.password_input.setFocus()
    
    def clear_form(self):
        """폼 초기화"""
        self.password_input.clear()
    
    def go_back(self):
        """뒤로가기"""
        self.clear_form()
        self.switch_to_home.emit()
    
    def showEvent(self, event):
        """화면 표시시 포커스 설정 및 시그널 연결"""
        super().showEvent(event)
        # Admin 로그인 화면이 표시될 때만 시그널 연결
        self._connect_login_signals()
        # 비밀번호 입력 필드에 포커스 및 키보드 표시
        QTimer.singleShot(100, self._focus_and_show_keyboard)
    
    def hideEvent(self, event):
        """화면 숨김시 시그널 연결 해제"""
        super().hideEvent(event)
        # Admin 로그인 화면이 숨겨질 때 시그널 연결 해제
        self._disconnect_login_signals()

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
        """이벤트 필터링 - 비밀번호 필드 클릭 시 키보드 표시"""
        # 속성이 존재하는지 확인
        if not hasattr(self, 'password_input'):
            return super().eventFilter(obj, event)
            
        if obj == self.password_input and event.type() == QEvent.MouseButtonPress:
            self.show_virtual_keyboard()
            return True
        elif event.type() == QEvent.MouseButtonPress:
            if not self.is_click_on_keyboard(event.globalPos()) and not self.is_click_on_password_field(event.globalPos()):
                self.hide_keyboard()
        return super().eventFilter(obj, event)

    def show_virtual_keyboard(self):
        """가상 키보드 표시"""
        if self.keyboard_animation:
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
        if not self.vkeyboard.isHidden():
            if self.keyboard_animation:
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
        if key == ' ':  # Space key
            self.password_input.insert(' ')
        else:
            self.password_input.insert(key)

    def handle_backspace(self):
        """백스페이스 처리"""
        self.password_input.backspace()

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

    def is_click_on_password_field(self, global_pos):
        """비밀번호 필드 영역 클릭 확인"""
        field_rect = self.password_input.geometry()
        field_global_pos = self.mapToGlobal(field_rect.topLeft())
        field_global_rect = field_rect.translated(field_global_pos - field_rect.topLeft())
        return field_global_rect.contains(global_pos)

    def _focus_and_show_keyboard(self):
        """비밀번호 필드에 포커스를 주고 키보드를 표시"""
        self.password_input.setFocus()
        # 잠시 후 키보드 표시 (포커스가 완전히 설정된 후)
        QTimer.singleShot(200, self.show_virtual_keyboard)
