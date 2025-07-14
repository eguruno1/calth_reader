# -*- coding: utf-8 -*-
"""
Login View - 로그인 화면
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QSpacerItem, 
                             QSizePolicy, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor
from controllers import app_controller

class LoginView(QWidget):
    """로그인 화면"""
    
    # 시그널 정의
    login_success = pyqtSignal()
    switch_to_home = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """UI 설정"""
        self.setFixedSize(1024, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: 'Pretendard';
            }
        """)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 상단 헤더
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(50, 30, 50, 30)
        
        # 뒤로가기 버튼
        self.back_button = QPushButton("← Back")
        self.back_button.setFixedSize(100, 40)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #606060;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
        """)
        self.back_button.clicked.connect(self.go_back)
        
        # 타이틀
        title_label = QLabel("LOGIN")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #000000;
            }
        """)
        
        header_layout.addWidget(self.back_button)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel(""))  # 공간 맞추기용
        
        # 로그인 폼 프레임
        login_frame = QFrame()
        login_frame.setFixedSize(400, 350)
        login_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #d0d0d0;
                border-radius: 10px;
            }
        """)
        
        # 로그인 폼 레이아웃
        form_layout = QVBoxLayout(login_frame)
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(20)
        
        # 로그인 타이틀
        login_title = QLabel("User Login")
        login_title.setAlignment(Qt.AlignCenter)
        login_title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
                margin-bottom: 10px;
            }
        """)
        form_layout.addWidget(login_title)
        
        # 사용자 ID 입력
        id_label = QLabel("User ID:")
        id_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #555555;")
        form_layout.addWidget(id_label)
        
        self.user_id_input = QLineEdit()
        self.user_id_input.setFixedHeight(40)
        self.user_id_input.setPlaceholderText("Enter your ID")
        self.user_id_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #606060;
            }
        """)
        form_layout.addWidget(self.user_id_input)
        
        # 비밀번호 입력
        password_label = QLabel("Password:")
        password_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #555555;")
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setFixedHeight(40)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #606060;
            }
        """)
        form_layout.addWidget(self.password_input)
        
        # 로그인 버튼
        self.login_button = QPushButton("Login")
        self.login_button.setFixedHeight(45)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #606060;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #707070;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
        """)
        self.login_button.clicked.connect(self.attempt_login)
        form_layout.addWidget(self.login_button)
        
        # 더미 사용자 안내 (개발용)
        info_label = QLabel("Demo Users:\nadmin/admin123, operator1/op123, viewer1/view123")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
        """)
        form_layout.addWidget(info_label)
        
        # 메인 레이아웃에 추가
        main_layout.addLayout(header_layout)
        
        # 로그인 폼을 중앙에 배치
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(login_frame)
        center_layout.addStretch()
        
        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        
        # Enter 키로 로그인
        self.user_id_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.attempt_login)
    
    def connect_signals(self):
        """시그널 연결"""
        # 사용자 서비스 시그널 연결
        app_controller.user_service.login_success.connect(self.on_login_success)
        app_controller.user_service.login_failed.connect(self.on_login_failed)
    
    def attempt_login(self):
        """로그인 시도"""
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text().strip()
        
        if not user_id or not password:
            QMessageBox.warning(self, "입력 오류", "사용자 ID와 비밀번호를 모두 입력해주세요.")
            return
        
        # 로그인 버튼 비활성화
        self.login_button.setText("Logging in...")
        self.login_button.setEnabled(False)
        
        # 로그인 시도
        success = app_controller.user_service.login(user_id, password)
        
        # 버튼 상태 복원
        QTimer.singleShot(1000, self.reset_login_button)
    
    def reset_login_button(self):
        """로그인 버튼 상태 복원"""
        self.login_button.setText("Login")
        self.login_button.setEnabled(True)
    
    def on_login_success(self, user_id: str):
        """로그인 성공 처리"""
        print(f"로그인 성공: {user_id}")
        self.clear_form()
        self.login_success.emit()
        self.switch_to_home.emit()
    
    def on_login_failed(self, error_message: str):
        """로그인 실패 처리"""
        QMessageBox.warning(self, "로그인 실패", error_message)
        self.password_input.clear()
        self.password_input.setFocus()
    
    def clear_form(self):
        """폼 초기화"""
        self.user_id_input.clear()
        self.password_input.clear()
    
    def go_back(self):
        """뒤로가기"""
        self.clear_form()
        self.switch_to_home.emit()
    
    def showEvent(self, event):
        """화면 표시시 포커스 설정"""
        super().showEvent(event)
        self.user_id_input.setFocus()
