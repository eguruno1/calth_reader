"""
views.AdminPwEdit2View의 Docstring

ManageOperatorView
  └─ Edit PW (admin)
       └─ AdminPwEdit1View (현재 PW 확인)
             └─ AdminPwEdit2View (새 PW 입력)
                   ├─ 비밀번호 변경
                   ├─ Audit Log 기록
                   ├─ 세션 재인증
                   └─ ManageOperatorView 복귀 + refresh
"""
"""
views.AdminPwEdit2View의 Docstring
"""
# views/AdminPwEdit2View.py
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
from services.user_service import user_service
from common.session_context import (
    get_session_context,
    set_session_context
)
from database.audit_logger import write_audit_log


class AdminPwEdit2View(QWidget):
    """
    관리자 비밀번호 변경 (2단계)
    """
    switch_to_manage_operator = pyqtSignal()
    password_updated          = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

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
            "AdminPwEdit2ViewWindow.ui"
        )
        uic.loadUi(ui_path, self)

        self.lineEdit_user_id.setReadOnly(True)

        self.lineEdit_password.installEventFilter(self)
        self.lineEdit_password_2.installEventFilter(self)

    def _connect_signals(self):
        self.pushButton_ok.clicked.connect(self.on_save_clicked)
        self.pushButton_cancel.clicked.connect(self.go_back)
        self.pushButton_back.clicked.connect(self.go_back)


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
        self.lineEdit_password_2.clear()
        # 키보드 자동 표시 플래그 초기화
        self.keyboard_auto_shown = False    

    def go_back(self):
        self.clear_form()
        self.hide_keyboard()
        self.switch_to_manage_operator.emit()

    # ==================================================
    # Public
    # ==================================================
    def set_user(self):
        session_user = get_session_context()
        if not session_user:
            raise Exception("User not found.")

        self.lineEdit_user_id.setText(session_user["user_id"])
        self.lineEdit_password.clear()
        self.lineEdit_password_2.clear()
        self.current_input = None

    # ==================================================
    # Save
    # ==================================================
    def on_save_clicked(self):
        pw1 = self.lineEdit_password.text().strip()
        pw2 = self.lineEdit_password_2.text().strip()

        if not pw1 or not pw2:
            QMessageBox.critical(self, "Error", "Password Invaild.")
            return

        if pw1 != pw2:
            QMessageBox.critical(self, "Error", "Password Invaild.")
            return

        try:
            self._update_admin_password(pw1)
            QMessageBox.information(self, "Info", "Changed successfully.")
            self.hide_keyboard()
            self.password_updated.emit()
            self.switch_to_manage_operator.emit()

        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"An error occurred.\n{str(e)}"
            )

    # ==================================================
    # DB
    # ==================================================
    def _update_admin_password(self, new_password: str):
        session_user = get_session_context()
        admin_user_id = session_user.get("user_id")

        session = get_db_session()
        try:
            admin = session.query(User).filter(User.user_id == admin_user_id).first()
            old_hash = admin.password_hash

            admin.password_hash = user_service.create_user_password(new_password)
            session.commit()
            """
            write_audit_log(
                action="UPDATE",
                table_name="users",
                record_id=admin.id,
                old_values={"password_hash": old_hash},
                new_values={"password_hash": "******"},
                user_id=admin.id
            )
            """
            set_session_context(
                user_pk=admin.id,
                user_id=admin.user_id,
                role=admin.role,
                ip_address=session_user.get("ip_address"),
                user_agent=session_user.get("user_agent"),
            )

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ==================================================
    # Virtual Keyboard (공통)
    # ==================================================
    def _setup_virtual_keyboard(self):
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()

        self.vkeyboard.key_pressed.connect(self._on_key_pressed)
        self.vkeyboard.backspace_pressed.connect(self._on_backspace)
        self.vkeyboard.enter_pressed.connect(self.handle_enter)
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

    def handle_enter(self):
        """
        엔터키는 입력으로 처리하지 않고
        확인 동작만 수행하도록 한다
        """
        # 엔터키가 QLineEdit에 입력되지 않도록
        if self.current_input:
            # 입력 완료로 간주 → 포커스 유지
            self.current_input.clearFocus()
            
        """Enter 키 처리"""
        self.hide_keyboard()
        self.on_save_clicked()        

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

        if self.original_frame_pos:
            self.form_animation = QPropertyAnimation(self.frame_login, b"pos")
            self.form_animation.setDuration(300)
            self.form_animation.setStartValue(self.frame_login.pos())
            self.form_animation.setEndValue(self.original_frame_pos)
            self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
            self.form_animation.start()
