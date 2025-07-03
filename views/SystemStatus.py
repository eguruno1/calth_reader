# -*- coding: utf-8 -*-
"""
System status utility for displaying debug information
"""
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from backend.backend_manager import backend_manager
from config.config import app_config

class SystemStatusWidget(QWidget):
    """시스템 상태를 표시하는 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 상태 라벨들
        self.debug_label = QLabel()
        self.camera_label = QLabel()
        self.uart_label = QLabel()
        self.system_label = QLabel()
        
        # 폰트 설정
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        
        for label in [self.debug_label, self.camera_label, self.uart_label, self.system_label]:
            label.setFont(font)
            layout.addWidget(label)
        
        self.setLayout(layout)
        self.update_status()
    
    def setup_timer(self):
        """상태 업데이트 타이머 설정"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(2000)  # 2초마다 업데이트
    
    def update_status(self):
        """상태 정보 업데이트"""
        try:
            status = backend_manager.get_status_info()
            
            # 디버그 모드 상태
            debug_text = "🟡 디버그 모드" if status['debug_mode'] else "🟢 실제 하드웨어 모드"
            self.debug_label.setText(debug_text)
            
            # 카메라 상태
            if status['camera_ready']:
                camera_text = "📷 카메라: 연결됨"
                self.camera_label.setStyleSheet("color: green;")
            else:
                camera_text = "📷 카메라: 디버그 모드" if status['debug_mode'] else "📷 카메라: 연결 실패"
                self.camera_label.setStyleSheet("color: orange;" if status['debug_mode'] else "color: red;")
            self.camera_label.setText(camera_text)
            
            # UART 상태
            if status['uart_ready']:
                uart_text = "⚡ UART: 연결됨"
                self.uart_label.setStyleSheet("color: green;")
            else:
                uart_text = "⚡ UART: 디버그 모드" if status['debug_mode'] else "⚡ UART: 연결 실패"
                self.uart_label.setStyleSheet("color: orange;" if status['debug_mode'] else "color: red;")
            self.uart_label.setText(uart_text)
            
            # 전체 시스템 상태
            if status['system_ready']:
                system_text = "✅ 시스템: 준비됨"
                self.system_label.setStyleSheet("color: green;")
            else:
                system_text = "⚠️ 시스템: 제한 모드" if status['debug_mode'] else "❌ 시스템: 오류"
                self.system_label.setStyleSheet("color: orange;" if status['debug_mode'] else "color: red;")
            self.system_label.setText(system_text)
            
        except Exception as e:
            self.debug_label.setText(f"상태 업데이트 오류: {str(e)}")
    
    def closeEvent(self, event):
        """위젯 종료시 타이머 정지"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)


def add_status_overlay(parent_widget):
    """부모 위젯에 상태 오버레이 추가"""
    if not hasattr(parent_widget, 'status_widget'):
        parent_widget.status_widget = SystemStatusWidget(parent_widget)
        parent_widget.status_widget.setGeometry(10, 10, 200, 120)
        parent_widget.status_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        parent_widget.status_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border-radius: 5px;
                padding: 5px;
            }
            QLabel {
                color: white;
                margin: 2px;
            }
        """)
        parent_widget.status_widget.show()

def remove_status_overlay(parent_widget):
    """부모 위젯에서 상태 오버레이 제거"""
    if hasattr(parent_widget, 'status_widget'):
        parent_widget.status_widget.close()
        delattr(parent_widget, 'status_widget')
