"""
views.AccountDeleteView의 Docstring
"""
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from database.connection import get_db_session
from database.models import User
from database.audit_logger import write_audit_log
from common.session_context import get_session_context
from services.user_service import user_service


class AccountDeleteView(QWidget):
    """
    사용자 계정 삭제 (논리 삭제)
    """
    switch_to_manage_operator = pyqtSignal()
    user_deleted              = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_user_id = None
        self._load_ui()
        self._connect_signals()

    def _load_ui(self):
        ui_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ui",
            "Settings",
            "AccountDeleteViewWindow.ui"
        )
        uic.loadUi(ui_path, self)

        # ID는 수정 불가
        self.lineEdit_user_id.setReadOnly(True)

    def _connect_signals(self):
        self.pushButton_delete.clicked.connect(self.on_delete_clicked)
        self.pushButton_cancel.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )

    # ==================================================
    # Public
    # ==================================================
    def set_target_user(self, user_id: str):
        self._target_user_id = user_id
        self.lineEdit_user_id.setText(user_id)
        self.lineEdit_password.clear()

    # ==================================================
    # Delete Logic
    # ==================================================
    def on_delete_clicked(self):
        password = self.lineEdit_password.text().strip()

        if not password:
            QMessageBox.warning(
                self,
                "입력 오류",
                "비밀번호를 입력해주세요."
            )
            return

        # 현재 로그인한 사용자 정보 확인.
        session_user = get_session_context()
        print(f"로그인 성공: admin, 컨텍스트: {session_user}")

        if not session_user:
            QMessageBox.critical(self, "오류", "로그인 정보가 없습니다.")
            return

        if session_user.get("user_id") != "admin":
            QMessageBox.warning(
                self,
                "권한 오류",
                "관리자만 사용자를 삭제 할 수 있습니다."
            )
            return

        # 🔐 관리자 비밀번호 검증
        success, message = user_service.verify_admin_password_with_lock_policy(
            admin_user_id = session_user.get("user_id"),
            password      = self.lineEdit_password.text().strip()
        )

        if not success:
            QMessageBox.warning(
                self,
                "삭제 불가",
                message
            )
            return

        try:
            self._delete_user()
            QMessageBox.information(
                self,
                "삭제 완료",
                "정상적으로 삭제 되었습니다."
            )

            """Session + Audit Log Save"""
            write_audit_log(
                action     = "DELETE",
                table_name = "users",
                record_id  = session_user["user_pk"],
                user_id    = session_user["user_pk"],
                new_values = {
                    "user_id" : self._target_user_id,
                    "is_active" : False
                },
                session_id  = session_user["session_id"],
                ip_address  = session_user["ip_address"],
                user_agent  = session_user["user_agent"]
            )

            self.user_deleted.emit()
            self.switch_to_manage_operator.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"사용자 삭제 중 오류가 발생했습니다.\n{str(e)}"
            )

    # ==================================================
    # DB
    # ==================================================
    def _delete_user(self):
        session = get_db_session()
        try:
            user = (
                session.query(User)
                .filter(
                    User.user_id == self._target_user_id,
                    User.is_active.is_(True)
                )
                .first()
            )

            if not user:
                raise Exception("사용자를 찾을 수 없습니다.")

            if user.user_id == "admin" and user.role == "admin":
                raise Exception("관리자는 삭제할 수 없습니다.")

            user.is_active = False
            session.commit()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
