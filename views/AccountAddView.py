# AccountAddView.py
import os

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QMessageBox
)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

from services.user_service import user_service
from database.connection import get_db_session
from database.models import User


class AccountAddView(QWidget):
    """
    사용자 등록 화면 
    """
    switch_to_manage_operator = pyqtSignal()
    user_created              = pyqtSignal()   # ✅ 추가

    def __init__(self, parent=None):
        super().__init__(parent)

        self._load_ui()
        self._init_ui()
        self._connect_signals()

    # ==================================================
    # UI
    # ==================================================
    def _load_ui(self):
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        ui_path = os.path.join(
            project_root,
            "ui",
            "Settings",
            "AccountAddViewWindow.ui"
        )

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")

        uic.loadUi(ui_path, self)

    def _init_ui(self):
        self.comboBox_role.clear()
        self.comboBox_role.addItems([
            "admin",
            "operator",
            "viewer"
        ])

    def _connect_signals(self):
        self.pushButton_save.clicked.connect(self.on_create_user)
        self.pushButton_cancel.clicked.connect(self.on_back)
        self.pushButton_back.clicked.connect(self.on_back)

    # ==================================================
    # Navigation
    # ==================================================
    def on_back(self):
        """이전 화면 (ManageOperatorView)으로 이동"""
        self.switch_to_manage_operator.emit()

    # ==================================================
    # Create User
    # ==================================================
    def on_create_user(self):
        user_id   = self.lineEdit_user_id.text().strip()
        password  = self.lineEdit_password.text()
        password2 = self.lineEdit_password_2.text()
        role      = self.comboBox_role.currentText()

        if not user_id or not password:
            QMessageBox.warning(self, "입력 오류", "User ID와 Password는 필수입니다.")
            return

        if password != password2:
            QMessageBox.warning(self, "입력 오류", "비밀번호가 일치하지 않습니다.")
            return

        if self._is_duplicate_user(user_id):
            QMessageBox.warning(self, "중복 오류", "이미 존재하는 사용자 ID입니다.")
            return

        try:
            self._create_user(user_id, password, role)

            QMessageBox.information(
                self,
                "등록 완료",
                "사용자가 정상적으로 등록되었습니다."
            )

            # 등록 완료 → 목록 화면으로
            self.user_created.emit()    # 목록 재조회
            self.switch_to_manage_operator.emit() # 이전화면으로

        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"사용자 등록 중 오류가 발생했습니다.\n{str(e)}"
            )

    # ==================================================
    # Service / DB
    # ==================================================
    def _is_duplicate_user(self, user_id: str) -> bool:
        session = get_db_session()
        try:
            return (
                session.query(User)
                .filter(User.user_id == user_id)
                .first()
                is not None
            )
        finally:
            session.close()

    def _create_user(self, user_id: str, password: str, role: str):
        session = get_db_session()
        try:
            password_hash = user_service.create_user_password(password)

            user = User(
                user_id       = user_id,
                name          = "Add "+role,
                password_hash = password_hash,
                role          = role,
                is_active     = True
            )

            session.add(user)
            session.commit()

            print(f"✅ User created: {user_id}")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
