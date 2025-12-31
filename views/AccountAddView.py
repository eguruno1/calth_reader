# AccountAddView.py
import os

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QMessageBox
)
from PyQt5 import uic
from PyQt5.QtCore import (pyqtSignal, QTimer, QEvent, QPoint, QPropertyAnimation, QEasingCurve)

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
    user_created              = pyqtSignal()   # ✅ 추가

    def __init__(self, parent=None):
        super().__init__(parent)

        self.keyboard_animation  = None   # 키보드 애니메이션
        self.form_animation      = None   # 폼 애니메이션
        self.original_form_pos   = None   # 원래 폼 위치
        self.keyboard_auto_shown = False  # 키보드 자동 표시 여부 플래그

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

        # UI 요소 참조 설정 (애니메이션용)
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

        # 이벤트 필터 설치 (키보드 표시용)
        self.user_id_input.installEventFilter(self)
        self.password_input.installEventFilter(self)
        self.password_input2.installEventFilter(self)
        

    # ==================================================
    # Navigation
    # ==================================================
    def on_back(self):
        """이전 화면 (ManageOperatorView)으로 이동"""
        # 폼 클리어.
        self.clear_form()

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

            # 폼 클리어.
            self.clear_form()

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

            """Session + Audit Log Save"""
            ctx = get_session_context()

            write_audit_log(
                action     = "CREATE",
                table_name = "users",
                record_id  = user.id,
                user_id    = ctx["user_pk"],
                new_values = {
                    "user_id": user.user_id,
                    "role"   : user.role
                }
            )

            print(f"✅ User created: {user_id}")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ==================================================
    # VKeyboard
    # ==================================================
    def clear_form(self):
        """폼 초기화"""
        self.user_id_input.clear()
        self.password_input.clear()
        self.password_input2.clear()
        # 키보드 자동 표시 플래그 초기화
        self.keyboard_auto_shown = False

    def showEvent(self, event):
        """화면 표시시 포커스 설정 및 시그널 연결"""
        super().showEvent(event)

        # 사용자 아이디 입력 필드에 포커스를 주고 키보드를 자동으로 표시
        QTimer.singleShot(100, self._focus_and_show_keyboard)    

    def eventFilter(self, obj, event):
        """이벤트 필터링 - 비밀번호 필드 클릭 시 키보드 표시"""
        # 속성이 존재하는지 확인
        if not hasattr(self, 'user_id_input'):
            return super().eventFilter(obj, event)
            
        if obj == self.user_id_input and event.type() == QEvent.MouseButtonPress:
            # 키보드가 이미 표시되어 있지 않을 때만 표시
            if self.vkeyboard.isHidden():
                self.show_virtual_keyboard()
            return True
        elif event.type() == QEvent.MouseButtonPress:
            if not self.is_click_on_keyboard(event.globalPos()) and not self.is_click_on_userid_field(event.globalPos()):
                self.hide_keyboard()
        return super().eventFilter(obj, event)    

    def _focus_and_show_keyboard(self):
        """입력 필드에 포커스를 주고 키보드를 표시"""
        self.user_id_input.setFocus()
        # 자동 표시 플래그가 설정되지 않았을 때만 키보드 표시
        if not self.keyboard_auto_shown:
            self.keyboard_auto_shown = True
            # 잠시 후 키보드 표시 (포커스가 완전히 설정된 후)
            QTimer.singleShot(200, self.show_virtual_keyboard)    

    def setup_virtual_keyboard(self):
        """가상 키보드 설정"""
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()
        self.vkeyboard.key_pressed.connect(self.handle_key_press)
        self.vkeyboard.backspace_pressed.connect(self.handle_backspace)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)
        self.vkeyboard.enter_pressed.connect(self.handle_enter)
        self.position_keyboard()

    def position_keyboard(self):
        """키보드 위치 설정"""
        keyboard_x = (self.width() - self.vkeyboard.width()) // 2
        keyboard_y = self.height()
        self.vkeyboard.move(keyboard_x, keyboard_y)    

    def handle_key_press(self, key):
        """키 입력 처리"""
        if key == ' ':  # Space key
            self.lineEdit_user_id.insert(' ')
        else:
            self.lineEdit_user_id.insert(key)

    def handle_backspace(self):
        """백스페이스 처리"""
        self.lineEdit_user_id.backspace()

    def handle_enter(self):
        """Enter 키 처리"""
        self.hide_keyboard()
        # self.attempt_login()    

    def show_virtual_keyboard(self):
        """가상 키보드 표시"""
        # 이미 키보드가 표시되어 있으면 중복 실행 방지
        if not self.vkeyboard.isHidden():
            return
            
        if self.keyboard_animation and self.keyboard_animation.state() == QPropertyAnimation.Running:
            self.keyboard_animation.stop()
        
        # 로그인 폼을 위로 이동
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
        """가상 키보드 숨기기"""
        # 이미 키보드가 숨겨져 있으면 중복 실행 방지
        if self.vkeyboard.isHidden():
            return
            
        if self.keyboard_animation and self.keyboard_animation.state() == QPropertyAnimation.Running:
            self.keyboard_animation.stop()
        
        start_y = self.vkeyboard.y()
        end_y = self.height()
        
        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
        self.keyboard_animation.setEasingCurve(QEasingCurve.InCubic)
        self.keyboard_animation.finished.connect(self.on_keyboard_hidden)
        self.keyboard_animation.start()    

    def on_keyboard_hidden(self):
        """키보드가 완전히 숨겨진 후 호출"""
        self.vkeyboard.hide()
        # 로그인 폼을 원래 위치로 복원
        self.restore_form_position()    

    def move_form_up(self):
        """폼을 위로 이동"""
        if self.form_animation:
            self.form_animation.stop()
        
        # 원래 위치 저장 (한 번만)
        if self.original_form_pos is None:
            self.original_form_pos = self.login_frame.pos()
        
        # 키보드 높이만큼 위로 이동 (적절한 여백 포함)
        keyboard_height = self.vkeyboard.height()
        move_distance = keyboard_height // 2  # 키보드 높이의 절반만큼 위로
        
        current_pos = self.frame_userinfo.pos()
        target_y = max(50, current_pos.y() - move_distance)  # 최소 50px 여백 유지
        target_pos = QPoint(current_pos.x(), target_y)
        
        self.form_animation = QPropertyAnimation(self.frame_userinfo, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(current_pos)
        self.form_animation.setEndValue(target_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()    

    def restore_form_position(self):
        """폼을 원래 위치로 복원"""
        if self.form_animation:
            self.form_animation.stop()
        
        if self.original_form_pos is None:
            return
        
        current_pos = self.frame_userinfo.pos()
        
        self.form_animation = QPropertyAnimation(self.frame_userinfo, b"pos")
        self.form_animation.setDuration(300)
        self.form_animation.setStartValue(current_pos)
        self.form_animation.setEndValue(self.original_form_pos)
        self.form_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.form_animation.start()    

    def is_click_on_keyboard(self, global_pos):
        """키보드 영역 클릭 확인"""
        if self.vkeyboard.isHidden():
            return False
        keyboard_rect = self.vkeyboard.geometry()
        keyboard_global_pos = self.mapToGlobal(keyboard_rect.topLeft())
        keyboard_global_rect = keyboard_rect.translated(keyboard_global_pos - keyboard_rect.topLeft())
        return keyboard_global_rect.contains(global_pos)    
    
    def is_click_on_userid_field(self, global_pos):
        """아이디 필드 영역 클릭 확인"""
        field_rect = self.user_id_input.geometry()
        field_global_pos = self.mapToGlobal(field_rect.topLeft())
        field_global_rect = field_rect.translated(field_global_pos - field_rect.topLeft())
        return field_global_rect.contains(global_pos)