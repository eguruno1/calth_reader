# views/AccountPwEditView.py
# -*- coding: utf-8 -*-

import os
import bcrypt
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from database.connection import get_db_session
from database.models import User


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
        self._load_ui()
        self._connect_signals()

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

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
