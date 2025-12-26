"""
views.AdminPwEdit1View의 Docstring
"""
# views/AdminPwEdit1View.py
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

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
            "AdminPwEdit1ViewWindow.ui"
        )
        uic.loadUi(ui_path, self)
        # ID는 수정 불가
        self.lineEdit_user_id.setReadOnly(True)

    def _connect_signals(self):
        self.pushButton_back.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )
        self.pushButton_ok.clicked.connect(self.on_check_password)

    def set_user(self, user_id: str):
        """수정 대상 ID 세팅"""
        self._current_user_id = user_id
        self.lineEdit_user_id.setText(user_id)
        self.lineEdit_password.clear()    

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

        print(f"_verify_admin_password session_user: {session_user}")

        if not session_user:
            raise Exception("로그인 정보가 없습니다.")

        # ✅ session_context 에서 user_id 만 사용
        admin_user_id = session_user.get("user_id") or session_user.get("id")

        if not admin_user_id:
            raise Exception("세션 사용자 정보가 올바르지 않습니다.")

        # ✅ UserService 에서 검증
        return user_service.verify_password(admin_user_id, password)

