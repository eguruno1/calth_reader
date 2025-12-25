# views/AccountIdEditView.py
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from database.connection import get_db_session
from database.models import User


class AccountIdEditView(QWidget):

    switch_to_manage_operator = pyqtSignal()
    user_id_updated = pyqtSignal()   # refresh 용

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_user_id = None
        self._load_ui()
        self._connect_signals()

    def _load_ui(self):
        ui_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ui",
            "Settings",
            "AccountIdEditViewWindow.ui"
        )
        uic.loadUi(ui_path, self)

    def _connect_signals(self):
        self.pushButton_save.clicked.connect(self.on_save_clicked)
        self.pushButton_cancel.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )

    # ==================================================
    # Public
    # ==================================================
    def set_user(self, user_id: str):
        """수정 대상 사용자 세팅"""
        self._current_user_id = user_id
        self.lineEdit_user_id.setText(user_id)
        self.lineEdit_change_user_id.clear()

    # ==================================================
    # Save
    # ==================================================
    def on_save_clicked(self):
        new_user_id = self.lineEdit_change_user_id.text().strip()

        if not new_user_id:
            QMessageBox.warning(
                self,
                "입력 오류",
                "변경할 사용자 ID를 입력해주세요."
            )
            return

        if new_user_id == self._current_user_id:
            QMessageBox.warning(
                self,
                "입력 오류",
                "기존 ID와 다른 ID를 입력해주세요."
            )
            return

        try:
            self._update_user_id(new_user_id)

            QMessageBox.information(
                self,
                "변경 완료",
                "사용자 ID가 정상적으로 변경되었습니다."
            )

            self.user_id_updated.emit()
            self.switch_to_manage_operator.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"사용자 ID 변경 중 오류가 발생했습니다.\n{str(e)}"
            )

    # ==================================================
    # DB
    # ==================================================
    def _update_user_id(self, new_user_id: str):
        session = get_db_session()
        try:
            # 중복 체크
            exists = (
                session.query(User)
                .filter(User.user_id == new_user_id)
                .first()
            )
            if exists:
                raise Exception("이미 존재하는 사용자 ID입니다.")

            user = (
                session.query(User)
                .filter(User.user_id == self._current_user_id)
                .first()
            )

            if not user:
                raise Exception("사용자를 찾을 수 없습니다.")

            user.user_id = new_user_id
            session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
