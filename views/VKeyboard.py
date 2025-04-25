import os

from PyQt5.QtWidgets    import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui        import QPainter, QColor, QPainterPath
from PyQt5.QtCore       import Qt, pyqtSignal


class VKeyboard(QWidget):
    key_pressed          = pyqtSignal(str)
    backspace_pressed    = pyqtSignal()
    hide_keyboard_signal = pyqtSignal()  # 시그널 이름 변경
    enter_pressed        = pyqtSignal()  # 새로운 시그널 추가

    def __init__(self, parent=None):
        super().__init__(parent)
        self.caps_lock = False
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.button_layout = QVBoxLayout()
        self.button_layout.setContentsMargins(20, 20, 20, 20)
        self.create_buttons(self.button_layout)
        
        main_layout.addLayout(self.button_layout)
        
        self.setFixedSize(1024, 310)  # 전체 키보드 위젯 크기 설정
        self.setStyleSheet("""
            QWidget#VKeyboard {
                background-color: transparent;
            }
            QPushButton {
                background-color: rgb(100, 100, 100);
                color: white;
                border: 1px solid #646464;
                border-radius: 7px;
                padding: 5px;
                font-size: 28px;
            }
            QPushButton:pressed {
                background-color: rgb(160, 160, 160);
            }
            QPushButton:checked {
                background-color: rgb(180, 180, 180);
            }
        """)
        self.setObjectName("VKeyboard")  # 위젯에 객체 이름 설정

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 90% 불투명한 검정색 배경 (10% 투명)
        background_color = QColor(0, 0, 0, 230)  # 230은 90% 불투명도를 나타냅니다 (255 * 0.9 ≈ 230)
        painter.setBrush(background_color)
        painter.setPen(Qt.NoPen)

        # 위쪽 모서리만 둥글게 처리된 사각형 그리기
        path = QPainterPath()
        rect = self.rect()
        radius = 30

        # 위쪽 왼쪽 모서리
        path.moveTo(0, radius)
        path.arcTo(0, 0, radius * 2, radius * 2, 180, -90)

        # 위쪽 오른쪽 모서리
        path.lineTo(rect.right() - radius, 0)
        path.arcTo(rect.right() - radius * 2, 0, radius * 2, radius * 2, 90, -90)

        # 아래쪽 직선
        path.lineTo(rect.right(), rect.bottom())
        path.lineTo(0, rect.bottom())
        path.closeSubpath()

        # 경로를 따라 그리기
        painter.drawPath(path)

    def create_buttons(self, layout):
        layouts = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['Caps Lock', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'Backspace'],
            ['Hide', 'Space', 'Enter']
        ]

        layout.setSpacing(12)
        default_height = 43
        special_height = default_height + 11
        button_width = 80
        button_spacing = 20

        dark_gray_style = """
            QPushButton {
                background-color: rgb(70, 70, 70);
                color: white;
                border: 1px solid #464646;
                border-radius: 12px;
                padding: 5px;
                font-size: 26px;
            }
        """
        normal_style = """
            QPushButton {
                background-color: rgb(100, 100, 100);
                color: white;
                border: 1px solid #646464;
                border-radius: 12px;
                padding: 5px;
                font-size: 26px;
            }
        """
        small_font_style = """
            QPushButton {
                background-color: rgb(70, 70, 70);
                color: white;
                border: 1px solid #464646;
                border-radius: 12px;
                padding: 5px;
                font-size: 20px;
            }
        """

        for row_index, row in enumerate(layouts):
            h_layout = QHBoxLayout()
            h_layout.setSpacing(button_spacing)

            for key in row:
                button = QPushButton(key)
                
                if key == 'Space':
                    button.setFixedWidth(530)
                    button.setFixedHeight(special_height)
                    button.setStyleSheet(dark_gray_style)
                elif key in ['Hide', 'Enter']:
                    button.setFixedWidth(200)
                    button.setFixedHeight(special_height)
                    button.setStyleSheet(dark_gray_style)
                elif key in ['Backspace', 'Caps Lock']:
                    button.setFixedWidth(125)
                    button.setFixedHeight(default_height)
                    button.setStyleSheet(small_font_style)
                else:
                    button.setFixedWidth(button_width)
                    button.setFixedHeight(default_height)
                    if key.isdigit():
                        button.setStyleSheet(dark_gray_style)
                    else:
                        button.setStyleSheet(normal_style)
                
                if key == 'Backspace':
                    button.clicked.connect(self.backspace_pressed.emit)
                elif key == 'Caps Lock':
                    button.clicked.connect(self.toggle_caps_lock)
                    button.setCheckable(True)
                elif key == 'Enter':
                    button.clicked.connect(self.enter_key_pressed)  # Enter 키 처리 변경
                elif key == 'Space':
                    button.clicked.connect(lambda: self.key_pressed.emit(' '))
                elif key == 'Hide':
                    button.clicked.connect(self.hide_keyboard_signal.emit)
                else:
                    button.clicked.connect(lambda _, x=key: self.key_pressed.emit(x.lower() if not self.caps_lock else x.upper()))
                h_layout.addWidget(button)

            # 각 행의 양쪽에 동일한 stretch 추가
            h_layout.insertStretch(0, 1)
            h_layout.addStretch(1)

            layout.addLayout(h_layout)

        # 전체 레이아웃을 중앙 정렬
        layout.setAlignment(Qt.AlignCenter)

    def toggle_caps_lock(self):
        self.caps_lock = not self.caps_lock
        self.update_key_labels()
        
        # Caps Lock 버튼의 상태를 업데이트합니다
        caps_lock_button = self.findChild(QPushButton, "Caps Lock")
        if caps_lock_button:
            caps_lock_button.setChecked(self.caps_lock)

    def update_key_labels(self):
        for row in range(self.button_layout.count()):
            h_layout = self.button_layout.itemAt(row).layout()
            for col in range(h_layout.count()):
                button = h_layout.itemAt(col).widget()
                if isinstance(button, QPushButton) and len(button.text()) == 1:
                    button.setText(button.text().upper() if self.caps_lock else button.text().lower())

    def button_clicked(self, key):
        self.parent().key_pressed(key)

    def backspace_clicked(self):
        self.parent().key_backspace()

    def mousePressEvent(self, event):
        self.raise_()  # 키보드를 최상위로 올립니다.
        super().mousePressEvent(event)

    def enter_key_pressed(self):
        self.key_pressed.emit('\n')
        self.enter_pressed.emit()  # Enter 키 누를 때 새로운 시그널 발생