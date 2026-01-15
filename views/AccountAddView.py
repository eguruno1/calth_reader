# AccountAddView.py
import os

from PyQt5.QtWidgets import (
    QWidget,
    QMessageBox,
    QLineEdit
)
from PyQt5 import uic
from PyQt5.QtCore import (
    pyqtSignal,
    QTimer,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QEasingCurve
)

from views.VKeyboard import VKeyboard

from services.user_service import user_service
from database.connection import get_db_session
from database.models import User

from database.audit_logger import write_audit_log
from common.session_context import get_session_context


class AccountAddView(QWidget):
    """
    사용자 등록 화면
    """
    switch_to_manage_operator = pyqtSignal()
    user_created              = pyqtSignal()   # ✅ 사용자 등록 완료 시그널

    def __init__(self, parent=None):
        super().__init__(parent)

        # ==============================
        # Virtual Keyboard 상태 변수
        # ==============================
        self.vkeyboard            = None
        self.keyboard_animation   = None
        self.form_animation       = None
        self.original_form_pos    = None
        self.keyboard_auto_shown  = False

        # 현재 입력 중인 필드
        self.current_input        = None

        self._load_ui()
        self._init_ui()
        self._connect_signals()
        self.setup_virtual_keyboard()

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

        # UI 요소 참조
        self.frame_userinfo  = self.frame_userinfo
        self.user_id_input   = self.lineEdit_user_id
        self.password_input  = self.lineEdit_password
        self.password_input2 = self.lineEdit_password_2

        self.save_button     = self.pushButton_save
        self.cancel_button   = self.pushButton_cancel

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

        # 모든 입력 필드에 이벤트 필터 설치
        for field in [
            self.user_id_input,
            self.password_input,
            self.password_input2
        ]:
            field.installEventFilter(self)

    # ==================================================
    # Navigation
    # ==================================================
    def on_back(self):
        """이전 화면으로 이동"""
        self.clear_form()
        self.switch_to_manage_operator.emit()

    # ==================================================
    # Create User
    # ==================================================
    def on_create_user(self):
        user_id   = self.user_id_input.text().strip()
        password  = self.password_input.text()
        password2 = self.password_input2.text()
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

            self.clear_form()
            self.user_created.emit()
            self.switch_to_manage_operator.emit()

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
            return session.query(User).filter(User.user_id == user_id).first() is not None
        finally:
            session.close()

    def _create_user(self, user_id: str, password: str, role: str):
        session = get_db_session()
        try:
            password_hash = user_service.create_user_password(password)

            user = User(
                user_id       = user_id,
                name          = "Add " + role,
                password_hash = password_hash,
                role          = role,
                is_active     = True
            )

            session.add(user)
            session.commit()
            """
            ctx = get_session_context()
            write_audit_log(
                action     = "CREATE",
                table_name = "users",
                record_id  = user.id,
                user_id    = ctx["user_pk"],
                new_values = {
                    "user_id": user.user_id,
                    "role": user.role
                }
            )
            """
            print(f"✅ User created: {user_id}")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ==================================================
    # Virtual Keyboard
    # ==================================================
    def clear_form(self):
        """폼 초기화"""
        self.user_id_input.clear()
        self.password_input.clear()
        self.password_input2.clear()
        self.keyboard_auto_shown = False
        self.current_input = None

    def showEvent(self, event):
        """화면 표시 시 자동 포커스"""
        super().showEvent(event)
        QTimer.singleShot(100, self._focus_and_show_keyboard)

    def _focus_and_show_keyboard(self):
        self.user_id_input.setFocus()
        self.current_input = self.user_id_input

        if not self.keyboard_auto_shown:
            self.keyboard_auto_shown = True
            QTimer.singleShot(200, self.show_virtual_keyboard)

    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and event.type() == QEvent.MouseButtonPress:
            self.current_input = obj
            self.show_virtual_keyboard()
            return True

        elif event.type() == QEvent.MouseButtonPress:
            if not self.is_click_on_keyboard(event.globalPos()) and \
               not self.is_click_on_input_field(event.globalPos()):
                self.hide_keyboard()

        return super().eventFilter(obj, event)

    def setup_virtual_keyboard(self):
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()

        self.vkeyboard.key_pressed.connect(self.handle_key_press)
        self.vkeyboard.backspace_pressed.connect(self.handle_backspace)
        self.vkeyboard.enter_pressed.connect(self.handle_enter)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)

        self.position_keyboard()

    def position_keyboard(self):
        keyboard_x = (self.width() - self.vkeyboard.width()) // 2
        keyboard_y = self.height()
        self.vkeyboard.move(keyboard_x, keyboard_y)

    def handle_key_press(self, key):
        if self.current_input:
            self.current_input.insert(key)

    def handle_backspace(self):
        if self.current_input:
            self.current_input.backspace()

    def handle_enter(self):
        self.hide_keyboard()
        self.on_create_user()

    def show_virtual_keyboard(self):
        if not self.vkeyboard.isHidden():
            return

        if self.keyboard_animation:
            self.keyboard_animation.stop()

        self.move_form_up()
        self.vkeyboard.show()

        start_y = self.height()
        end_y   = self.height() - self.vkeyboard.height()

        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
        self.keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.keyboard_animation.start()

    def hide_keyboard(self):
        if self.vkeyboard.isHidden():
            return

        if self.keyboard_animation:
            self.keyboard_animation.stop()

        start_y = self.vkeyboard.y()
        end_y   = self.height()

        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
        self.keyboard_animation.setEasingCurve(QEasingCurve.InCubic)
        self.keyboard_animation.finished.connect(self.on_keyboard_hidden)
        self.keyboard_animation.start()

    def on_keyboard_hidden(self):
        self.vkeyboard.hide()
        self.restore_form_position()

    def move_form_up(self):
        if self.form_animation:
            self.form_animation.stop()

        if self.original_form_pos is None:
            self.original_form_pos = self.frame_userinfo.pos()

        move_distance = self.vkeyboard.height() // 2
        current_pos   = self.frame_userinfo.pos()
        target_y      = max(50, current_pos.y() - move_distance)

        self.form_animation = QPropertyAnimation(self.frame_userinfo, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(current_pos)
        self.form_animation.setEndValue(QPoint(current_pos.x(), target_y))
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()

    def restore_form_position(self):
        if self.form_animation:
            self.form_animation.stop()

        if self.original_form_pos:
            self.form_animation = QPropertyAnimation(self.frame_userinfo, b"pos")
            self.form_animation.setDuration(300)
            self.form_animation.setStartValue(self.frame_userinfo.pos())
            self.form_animation.setEndValue(self.original_form_pos)
            self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
            self.form_animation.start()

    def is_click_on_keyboard(self, global_pos):
        if self.vkeyboard.isHidden():
            return False

        rect = self.vkeyboard.geometry()
        global_rect = rect.translated(self.mapToGlobal(rect.topLeft()) - rect.topLeft())
        return global_rect.contains(global_pos)

    def is_click_on_input_field(self, global_pos):
        for field in [self.user_id_input, self.password_input, self.password_input2]:
            rect = field.geometry()
            global_rect = rect.translated(self.mapToGlobal(rect.topLeft()) - rect.topLeft())
            if global_rect.contains(global_pos):
                return True
        return False
