# views/AccountPwEditView.py
# -*- coding: utf-8 -*-

import os
import bcrypt

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import (
    pyqtSignal,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QEasingCurve
)
from PyQt5 import uic

from views.VKeyboard import VKeyboard

from database.connection import get_db_session
from database.models import User

from database.audit_logger import write_audit_log
from common.session_context import get_session_context


class AccountPwEditView(QWidget):
    """
    사용자 비밀번호 변경 화면
    """

    # AccountIdEditView 와 동일한 시그널 구조
    switch_to_manage_operator = pyqtSignal()
    user_pw_updated           = pyqtSignal()   # refresh 용

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_user_id = None

        # ==============================
        # Virtual Keyboard / Animation
        # ==============================
        self.vkeyboard = None
        self.keyboard_animation = None
        self.form_animation = None
        self.original_frame_pos = None

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
            "AccountPwEditViewWindow.ui"
        )
        uic.loadUi(ui_path, self)

        # ID는 수정 불가
        self.lineEdit_user_id.setReadOnly(True)

        # 이벤트 필터 (키보드 트리거)
        self.lineEdit_password.installEventFilter(self)
        self.lineEdit_password_2.installEventFilter(self)

    def _connect_signals(self):
        self.pushButton_save.clicked.connect(self.on_save_clicked)
        self.pushButton_cancel.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )
        self.pushButton_back.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )

    # ==================================================
    # Public
    # ==================================================
    def set_user(self, user_id: str):
        """수정 대상 사용자 세팅"""
        self._current_user_id = user_id
        self.lineEdit_user_id.setText(user_id)
        self.lineEdit_password.clear()
        self.lineEdit_password_2.clear()
        self.current_input = None

    # ==================================================
    # Save
    # ==================================================
    def on_save_clicked(self):
        pw1 = self.lineEdit_password.text().strip()
        pw2 = self.lineEdit_password_2.text().strip()

        if not pw1:
            QMessageBox.warning(
                self,
                "입력 오류",
                "변경할 패스워드를 입력해주세요."
            )
            return

        if pw1 != pw2:
            QMessageBox.warning(
                self,
                "입력 오류",
                "패스워드가 서로 일치하지 않습니다."
            )
            return

        try:
            self._update_user_password(pw1)

            QMessageBox.information(
                self,
                "변경 완료",
                "비밀번호가 정상적으로 변경되었습니다."
            )

            self.user_pw_updated.emit()
            self.switch_to_manage_operator.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"비밀번호 변경 중 오류가 발생했습니다.\n{str(e)}"
            )

    # ==================================================
    # DB
    # ==================================================
    def _update_user_password(self, new_password: str):
        session = get_db_session()
        try:
            user = (
                session.query(User)
                .filter(User.user_id == self._current_user_id)
                .first()
            )

            if not user:
                raise Exception("사용자를 찾을 수 없습니다.")

            user.password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            session.commit()

            ctx = get_session_context()
            write_audit_log(
                action      = "UPDATE",
                table_name  = "users",
                record_id   = user.id,
                user_id     = ctx["user_pk"],
                old_values  = {"password": "***"},
                new_values  = {"password": "***"},
                session_id  = ctx["session_id"],
                ip_address  = ctx["ip_address"],
                user_agent  = ctx["user_agent"]
            )

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ==================================================
    # Virtual Keyboard
    # ==================================================
    def _setup_virtual_keyboard(self):
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()

        self.vkeyboard.key_pressed.connect(self._on_key_pressed)
        self.vkeyboard.backspace_pressed.connect(self._on_backspace)
        self.vkeyboard.enter_pressed.connect(self.hide_keyboard)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)

    def eventFilter(self, obj, event):
        if obj in (self.lineEdit_password, self.lineEdit_password_2):
            if event.type() == QEvent.FocusIn:
                self.current_input = obj
                self.show_keyboard()

        return super().eventFilter(obj, event)

    def _on_key_pressed(self, key):
        if self.current_input:
            self.current_input.insert(key)

    def _on_backspace(self):
        if self.current_input:
            self.current_input.backspace()

    # ==================================================
    # Keyboard + Frame Movement
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
        if self.form_animation:
            self.form_animation.stop()

        if self.original_frame_pos is None:
            self.original_frame_pos = self.frame_login.pos()

        move_distance = int(self.vkeyboard.height() * 0.6)
        current_pos = self.frame_login.pos()
        target_pos = QPoint(
            current_pos.x(),
            max(30, current_pos.y() - move_distance)
        )

        self.form_animation = QPropertyAnimation(self.frame_login, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(current_pos)
        self.form_animation.setEndValue(target_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    def _restore_frame_position(self):
        if not self.original_frame_pos:
            return

        if self.form_animation:
            self.form_animation.stop()

        self.form_animation = QPropertyAnimation(self.frame_login, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(self.frame_login.pos())
        self.form_animation.setEndValue(self.original_frame_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()
