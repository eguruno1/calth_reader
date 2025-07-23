import os

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGridLayout, QFrame)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update

class SettingsView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.init_ui()

    def setup_ui(self):
        """UI 설정"""
        self.setFixedSize(1024, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                font-family: 'Pretendard';
            }
        """)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 상단 헤더
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # 설정 버튼 그리드
        settings_widget = self.create_settings_grid()
        main_layout.addWidget(settings_widget)
        
        # 하단 상태바
        status_widget = self.create_status_bar()
        main_layout.addWidget(status_widget)

    def create_header(self):
        """상단 헤더 생성"""
        header_widget = QWidget()
        header_widget.setFixedHeight(80)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 2px solid #d0d0d0;
            }
        """)
        
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(50, 20, 50, 20)
        
        # 뒤로가기 버튼
        self.pushButton_SettingsBackArrow = QPushButton("← Back")
        self.pushButton_SettingsBackArrow.setFixedSize(100, 40)
        self.pushButton_SettingsBackArrow.setStyleSheet("""
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
        
        # 타이틀
        title_label = QLabel("SETTINGS")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
            }
        """)
        
        # 날짜/시간 라벨
        self.label_DateNClock = QLabel("YYYY-MM-DD HH:MM")
        self.label_DateNClock.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label_DateNClock.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666666;
            }
        """)
        
        header_layout.addWidget(self.pushButton_SettingsBackArrow)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.label_DateNClock)
        
        return header_widget

    def create_settings_grid(self):
        """설정 버튼 그리드 생성"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(80, 60, 80, 60)
        settings_layout.setSpacing(40)
        
        # 윗줄 버튼들
        top_row = QHBoxLayout()
        top_row.setSpacing(40)
        
        # Date and Time 버튼
        self.btn_date_time = self.create_setting_button(
            "Date and Time",
            color="#606060"
        )
        
        # Manage Operator 버튼
        self.btn_manage_operator = self.create_setting_button(
            "Manage Operator",
            color="#606060"
        )
        
        # Update 버튼
        self.btn_update = self.create_setting_button(
            "Update",
            color="#606060"
        )
        
        top_row.addWidget(self.btn_date_time)
        top_row.addWidget(self.btn_manage_operator)
        top_row.addWidget(self.btn_update)
        
        # 아랫줄 버튼들
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(40)
        
        # Calibration / QC days 버튼
        self.btn_calibration_qc = self.create_setting_button(
            "Calibration / QC days",
            color="#606060"
        )
        
        # General Settings 버튼
        self.btn_general_settings = self.create_setting_button(
            "General Settings",
            color="#606060"
        )
        
        # Power Management 버튼
        self.btn_power_management = self.create_setting_button(
            "Power Management",
            color="#606060"
        )
        
        bottom_row.addWidget(self.btn_calibration_qc)
        bottom_row.addWidget(self.btn_general_settings)
        bottom_row.addWidget(self.btn_power_management)
        
        settings_layout.addLayout(top_row)
        settings_layout.addLayout(bottom_row)
        
        return settings_widget

    def create_setting_button(self, title, color):
        """설정 버튼 생성"""
        button = QPushButton()
        button.setFixedSize(250, 150)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 10px;
                text-align: center;
                padding: 20px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """)
        
        # 버튼 텍스트 설정
        button.setText(f"{title}")
        
        return button

    def darken_color(self, hex_color, factor=0.9):
        """색상을 어둡게 만드는 헬퍼 함수"""
        # 간단한 색상 어둡게 만들기
        color_map = {
            "#606060":"#707070"
        }
        return color_map.get(hex_color, hex_color)

    def create_status_bar(self):
        """하단 상태바 생성"""
        status_widget = QWidget()
        status_widget.setFixedHeight(60)
        status_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-top: 2px solid #d0d0d0;
            }
        """)
        
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(50, 15, 50, 15)
        
        # 디바이스 정보
        device_label = QLabel("Device: Ready | Version: 1.0.0")
        device_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
            }
        """)
        
        # 연결 상태
        connection_label = QLabel("System: Connected | Status: Online")
        connection_label.setAlignment(Qt.AlignRight)
        connection_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
            }
        """)
        
        status_layout.addWidget(device_label)
        status_layout.addStretch()
        status_layout.addWidget(connection_label)
        
        return status_widget

    def init_ui(self):
        """UI 초기화 및 이벤트 연결"""
        # 뒤로 가기 버튼 연결
        self.pushButton_SettingsBackArrow.clicked.connect(self.on_back_button_clicked)
        
        # 설정 버튼들 이벤트 연결
        self.btn_date_time.clicked.connect(self.on_date_time_clicked)
        self.btn_manage_operator.clicked.connect(self.on_manage_operator_clicked)
        self.btn_update.clicked.connect(self.on_update_clicked)
        self.btn_calibration_qc.clicked.connect(self.on_calibration_qc_clicked)
        self.btn_general_settings.clicked.connect(self.on_general_settings_clicked)
        self.btn_power_management.clicked.connect(self.on_power_management_clicked)

        # 초기 날짜와 시간 설정
        self.update_date_time()

    def on_date_time_clicked(self):
        """Date and Time 버튼 클릭"""
        print("Date and Time 설정이 클릭되었습니다.")
        # TODO: Date and Time 설정 화면으로 이동
    
    def on_manage_operator_clicked(self):
        """Manage Operator 버튼 클릭"""
        print("Manage Operator가 클릭되었습니다.")
        # TODO: Operator 관리 화면으로 이동
    
    def on_update_clicked(self):
        """Update 버튼 클릭"""
        print("Update가 클릭되었습니다.")
        # TODO: 업데이트 화면으로 이동
    
    def on_calibration_qc_clicked(self):
        """Calibration / QC days 버튼 클릭"""
        print("Calibration / QC days가 클릭되었습니다.")
        # TODO: Calibration/QC 설정 화면으로 이동
    
    def on_general_settings_clicked(self):
        """General Settings 버튼 클릭"""
        print("General Settings가 클릭되었습니다.")
        # TODO: 일반 설정 화면으로 이동
    
    def on_power_management_clicked(self):
        """Power Management 버튼 클릭"""
        print("Power Management가 클릭되었습니다.")
        # TODO: 전원 관리 화면으로 이동

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def update_date_time(self):
        update_date_time(self)
