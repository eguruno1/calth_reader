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
# views/AdminPwEdit2View.py
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

from database.connection import get_db_session
from database.models import User
from services.user_service import user_service
from common.session_context import (
    get_session_context,
    set_session_context,
    clear_session_context
)

from database.audit_logger import write_audit_log


class AdminPwEdit2View(QWidget):
    """
    관리자 비밀번호 변경 (2단계)
    """
    switch_to_manage_operator = pyqtSignal()
    password_updated          = pyqtSignal()  # refresh 용

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
            "AdminPwEdit2ViewWindow.ui"
        )
        uic.loadUi(ui_path, self)

        # user_id는 표시만
        self.lineEdit_user_id.setReadOnly(True)

    def _connect_signals(self):
        self.pushButton_ok.clicked.connect(self.on_save_clicked)
        self.pushButton_cancel.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )
        self.pushButton_back.clicked.connect(
            lambda: self.switch_to_manage_operator.emit()
        )

    # ==================================================
    # Public
    # ==================================================
    def set_user(self):
        """현재 로그인된 관리자 정보 세팅"""
        session_user = get_session_context()
        if not session_user or not session_user.get("user_id"):
            raise Exception("세션 사용자 정보가 없습니다.")

        self.lineEdit_user_id.setText(session_user["user_id"])
        self.lineEdit_password.clear()
        self.lineEdit_password_2.clear()

    # ==================================================
    # Save
    # ==================================================
    def on_save_clicked(self):
        pw1 = self.lineEdit_password.text().strip()
        pw2 = self.lineEdit_password_2.text().strip()

        if not pw1 or not pw2:
            QMessageBox.warning(
                self,
                "입력 오류",
                "새 비밀번호를 입력해주세요."
            )
            return

        if pw1 != pw2:
            QMessageBox.warning(
                self,
                "입력 오류",
                "비밀번호가 일치하지 않습니다."
            )
            return

        try:
            self._update_admin_password(pw1)

            QMessageBox.information(
                self,
                "변경 완료",
                "비밀번호가 정상적으로 변경되었습니다."
            )

            self.password_updated.emit()
            self.switch_to_manage_operator.emit()
            """
            로그인이 필요하면 위 주석 처리 후 이부분 주석 해제.
            clear_session_context()
            self.switch_to_login.emit()
            """
            

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"비밀번호 변경 중 오류가 발생했습니다.\n{str(e)}"
            )

    # ==================================================
    # DB + Audit + Session
    # ==================================================
    def _update_admin_password(self, new_password: str):
        session_user = get_session_context()
        if not session_user:
            raise Exception("로그인 정보가 없습니다.")
        
        # ✅ 반드시 user_id 사용
        admin_user_id = session_user.get("user_id")

        if not admin_user_id:
            raise Exception("세션 사용자 정보가 올바르지 않습니다.")

        session = get_db_session()
        try:
            admin = (
                session.query(User)
                .filter(User.user_id == admin_user_id)
                .first()
            )

            if not admin:
                raise Exception("관리자 정보를 찾을 수 없습니다.")

            old_hash = admin.password_hash

            # 비밀번호 변경
            new_hash = user_service.create_user_password(new_password)
            admin.password_hash = new_hash
            session.commit()

            # =========================
            # Audit Log
            # =========================
            write_audit_log(
                action="UPDATE",
                table_name="users",
                record_id=admin.id, # 여기서만 PK 사용 (DB 내부)
                old_values={"password_hash": old_hash},
                new_values={"password_hash": "******"},
                user_id=admin.id
            )

            # =======================================
            # 비밀번호 변경 후 세션 재인증(세션 컨텍스트 재설정) 
            # 로그인 필요하지 않음.
            # =======================================
            set_session_context(
                user_pk=admin.id,
                user_id=admin.user_id,
                ip_address=session_user.get("ip_address"),
                user_agent=session_user.get("user_agent"),
            )

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
