"""
views.AdminPwEdit1View의 Docstring
"""
# views/AdminPwEdit1View.py
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import (
    pyqtSignal,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    QTimer
)
from PyQt5 import uic

from views.VKeyboard import VKeyboard

from database.connection import get_db_session
from database.models import User
from common.session_context import get_session_context
from services.user_service import user_service


class AdminPwEdit1View(QWidget):
    """
    관리자 비밀번호 변경 - 1단계
    (현재 비밀번호 확인)
    """

    switch_to_manage_operator = pyqtSignal()
    switch_to_admin_pw_edit2  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # ==============================
        # Virtual Keyboard
        # ==============================
        self.vkeyboard = None
        self.keyboard_animation = None
        self.form_animation = None
        self.original_frame_pos = None
        self.keyboard_auto_shown = False

        self.current_input = None

        self._load_ui()
        self._connect_signals()
        self._setup_virtual_keyboard()

    # ==================================================
    # UI
    # ==================================================
    def _load_ui(self):
        ui_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ui",
            "Settings",
            "AdminPwEdit1ViewWindow.ui"
        )
        uic.loadUi(ui_path, self)

        # ID는 수정 불가
        self.lineEdit_user_id.setReadOnly(True)

        # 가상키보드 이벤트 필터
        self.lineEdit_password.installEventFilter(self)

    def _connect_signals(self):
        self.pushButton_back.clicked.connect(self.go_back)
        self.pushButton_cancel.clicked.connect(self.go_back)
        self.pushButton_ok.clicked.connect(self.on_check_password)

    def set_user(self, user_id: str):
        """수정 대상 ID 세팅"""
        self._current_user_id = user_id
        self.lineEdit_user_id.setText(user_id)
        self.lineEdit_password.clear()
        self.current_input = None


    # ==================================================
    # Qt Events
    # ==================================================
    def showEvent(self, event):
        """
        화면 표시 후 자동 포커스 + 키보드 표시
        """
        super().showEvent(event)

        if not self.keyboard_auto_shown:
            self.keyboard_auto_shown = True
            QTimer.singleShot(100, self._focus_and_show_keyboard)

    def _focus_and_show_keyboard(self):
        self.lineEdit_password.setFocus()
        self.current_input = self.lineEdit_password
        self.show_keyboard()    

    def clear_form(self):
        """폼 초기화"""
        self.lineEdit_password.clear()
        # 키보드 자동 표시 플래그 초기화
        self.keyboard_auto_shown = False    

    def go_back(self):
        self.clear_form()
        self.hide_keyboard()
        self.switch_to_manage_operator.emit()        

    # ==================================================
    # Logic
    # ==================================================
    def on_check_password(self):
        password = self.lineEdit_password.text().strip()

        if not password:
            QMessageBox.warning(
                self,
                "입력 오류",
                "현재 비밀번호를 입력해주세요."
            )
            return

        try:
            if self._verify_admin_password(password):
                QMessageBox.information(
                    self,
                    "확인 완료",
                    "비밀번호가 확인되었습니다."
                )
                self.lineEdit_password.clear()
                self.hide_keyboard()
                self.switch_to_admin_pw_edit2.emit()
            else:
                QMessageBox.warning(
                    self,
                    "인증 실패",
                    "현재 비밀번호가 올바르지 않습니다."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"비밀번호 확인 중 오류가 발생했습니다.\n{str(e)}"
            )

    # ==================================================
    # DB
    # ==================================================
    def _verify_admin_password(self, password: str) -> bool:
        session_user = get_session_context()

        if not session_user:
            raise Exception("로그인 정보가 없습니다.")

        admin_user_id = session_user.get("user_id")
        if not admin_user_id:
            raise Exception("세션 사용자 정보가 올바르지 않습니다.")

        return user_service.verify_password(admin_user_id, password)

    # ==================================================
    # Virtual Keyboard
    # ==================================================
    def _setup_virtual_keyboard(self):
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()

        self.vkeyboard.key_pressed.connect(self._on_key_pressed)
        self.vkeyboard.backspace_pressed.connect(self._on_backspace)
        self.vkeyboard.enter_pressed.connect(self.handle_enter)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)

    def eventFilter(self, obj, event):
        if obj == self.lineEdit_password and event.type() == QEvent.FocusIn:
            self.current_input = obj
            self.show_keyboard()
        return super().eventFilter(obj, event)

    def _on_key_pressed(self, key):
        if self.current_input:
            self.current_input.insert(key)

    def _on_backspace(self):
        if self.current_input:
            self.current_input.backspace()

    def handle_enter(self):
        """Enter 키 처리"""
        self.hide_keyboard()
        self.on_check_password()

    # ==================================================
    # Keyboard + Frame 이동
    # ==================================================
    def show_keyboard(self):
        if not self.vkeyboard.isHidden():
            return

        keyboard_x = (self.width() - self.vkeyboard.width()) // 2
        keyboard_y = self.height()
        self.vkeyboard.move(keyboard_x, keyboard_y)
        self.vkeyboard.show()

        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(keyboard_x, self.height()))
        self.keyboard_animation.setEndValue(
            QPoint(keyboard_x, self.height() - self.vkeyboard.height())
        )
        self.keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.keyboard_animation.start()

        self._move_frame_up()

    def hide_keyboard(self):
        if self.vkeyboard.isHidden():
            return

        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(250)
        self.keyboard_animation.setStartValue(self.vkeyboard.pos())
        self.keyboard_animation.setEndValue(
            QPoint(self.vkeyboard.x(), self.height())
        )
        self.keyboard_animation.setEasingCurve(QEasingCurve.InCubic)
        self.keyboard_animation.finished.connect(self.vkeyboard.hide)
        self.keyboard_animation.start()

        self._restore_frame_position()

    def _move_frame_up(self):
        if self.original_frame_pos is None:
            self.original_frame_pos = self.frame_login.pos()

        move_distance = int(self.vkeyboard.height() * 0.6)
        target_pos = QPoint(
            self.frame_login.x(),
            max(30, self.frame_login.y() - move_distance)
        )

        self.form_animation = QPropertyAnimation(self.frame_login, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(self.frame_login.pos())
        self.form_animation.setEndValue(target_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    def _restore_frame_position(self):
        if not self.original_frame_pos:
            return

        self.form_animation = QPropertyAnimation(self.frame_login, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(self.frame_login.pos())
        self.form_animation.setEndValue(self.original_frame_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()
