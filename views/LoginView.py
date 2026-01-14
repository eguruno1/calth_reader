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
        self.keyboard_animation = None
        self.form_animation = None
        self.original_form_pos = None
        self.target_context = None
        self.keyboard_auto_shown = False

        # ✅ 현재 키 입력 대상
        self.current_input = None

        self.setup_ui()
        self.setup_virtual_keyboard()
        self.connect_signals()

    # ==================================================
    # UI
    # ==================================================
    def setup_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        ui_file = os.path.join(project_root, 'ui', 'Login', 'LoginViewWindow.ui')
        if not os.path.exists(ui_file):
            raise FileNotFoundError(ui_file)

        uic.loadUi(ui_file, self)

        self.login_frame = self.frame_login
        self.user_id_input = self.lineEdit_user_id
        self.password_input = self.lineEdit_password
        self.login_button = self.pushButton_login
        self.back_button = self.pushButton_back

        # 이벤트 필터 설치
        self.user_id_input.installEventFilter(self)
        self.password_input.installEventFilter(self)

    # ==================================================
    # Signals
    # ==================================================
    def connect_signals(self):
        self.back_button.clicked.connect(self.go_back)
        self.login_button.clicked.connect(self.attempt_login)

        self.user_id_input.returnPressed.connect(self.attempt_login)
        self.password_input.returnPressed.connect(self.attempt_login)

    # ==================================================
    # Context (⚠️ 반드시 유지)
    # ==================================================
    def set_context(self, context: str):
        """로그인 컨텍스트 설정 (예: 'qc')"""
        self.target_context = context

    # ==================================================
    # Virtual Keyboard
    # ==================================================
    def setup_virtual_keyboard(self):
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()

        self.vkeyboard.key_pressed.connect(self._handle_key_press)
        self.vkeyboard.backspace_pressed.connect(self._handle_backspace)
        self.vkeyboard.enter_pressed.connect(self._handle_enter)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)

    def eventFilter(self, obj, event):
        """
        Focus 기반으로 입력 대상 추적
        (MousePress 이벤트를 먹지 않음)
        """
        if obj in (self.user_id_input, self.password_input):
            if event.type() == QEvent.FocusIn:
                self.current_input = obj
                if self.vkeyboard.isHidden():
                    self.show_virtual_keyboard()
        return super().eventFilter(obj, event)

    def _handle_key_press(self, key):
        if isinstance(self.current_input, QLineEdit):
            self.current_input.insert(key)

    def _handle_backspace(self):
        if isinstance(self.current_input, QLineEdit):
            self.current_input.backspace()

    def _handle_enter(self):
        self.hide_keyboard()
        self.attempt_login()

    # ==================================================
    # Keyboard Animation
    # ==================================================
    def show_virtual_keyboard(self):
        if not self.vkeyboard.isHidden():
            return

        self.move_form_up()

        keyboard_x = (self.width() - self.vkeyboard.width()) // 2
        self.vkeyboard.move(keyboard_x, self.height())
        self.vkeyboard.show()

        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(keyboard_x, self.height()))
        self.keyboard_animation.setEndValue(
            QPoint(keyboard_x, self.height() - self.vkeyboard.height())
        )
        self.keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.keyboard_animation.start()

    def hide_keyboard(self):
        if self.vkeyboard.isHidden():
            return

        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(250)
        self.keyboard_animation.setStartValue(self.vkeyboard.pos())
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), self.height()))
        self.keyboard_animation.setEasingCurve(QEasingCurve.InCubic)
        self.keyboard_animation.finished.connect(self.vkeyboard.hide)
        self.keyboard_animation.start()

        self.restore_form_position()

    # ==================================================
    # Form Move
    # ==================================================
    def move_form_up(self):
        if self.original_form_pos is None:
            self.original_form_pos = self.login_frame.pos()

        move_distance = int(self.vkeyboard.height() * 0.6)
        target_y = max(40, self.login_frame.y() - move_distance)

        self.form_animation = QPropertyAnimation(self.login_frame, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(self.login_frame.pos())
        self.form_animation.setEndValue(QPoint(self.login_frame.x(), target_y))
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    def restore_form_position(self):
        if not self.original_form_pos:
            return

        self.form_animation = QPropertyAnimation(self.login_frame, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(self.login_frame.pos())
        self.form_animation.setEndValue(self.original_form_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    # ==================================================
    # Login Logic (기존 유지)
    # ==================================================
    def attempt_login(self):
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text().strip()

        if not user_id or not password:
            QMessageBox.warning(self, "입력 오류", "사용자 ID와 비밀번호를 모두 입력해주세요.")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")

        try:
            app_controller.user_service.login(user_id, password)
        finally:
            QTimer.singleShot(800, self.reset_login_button)

    def reset_login_button(self):
        self.login_button.setEnabled(True)
        self.login_button.setText("Login")

    def go_back(self):
        self.hide_keyboard()
        self.switch_to_home.emit()
