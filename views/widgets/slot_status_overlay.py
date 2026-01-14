from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont


class SlotStatusOverlayWidget(QWidget):
    """
    ⚠ Slot 전역 안내 위젯
    - 항상 단 하나만 표시됨 (중복 오픈 방지)
    - 오픈 시 전체 UI 입력 차단
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )

        # 전체 앱 입력 차단
        self.setWindowModality(Qt.ApplicationModal)

        self.setAttribute(Qt.WA_TranslucentBackground)

        if parent:
            self.resize(parent.size())

        # 상태 플래그 : 위젯은 한번만 오픈
        self._is_open = False

        self.hide()
        self._build_ui()

    # ======================================================
    # UI 구성
    # ======================================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        frame = QFrame()
        frame.setFixedSize(520, 260)
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 190);
                border-radius: 20px;
            }
        """)

        inner = QVBoxLayout(frame)
        inner.setAlignment(Qt.AlignCenter)
        inner.setSpacing(16)

        label_title = QLabel("⚠ Warning")
        label_title.setFont(QFont("Arial", 26, QFont.Bold))
        label_title.setStyleSheet("color: yellow;")
        label_title.setAlignment(Qt.AlignCenter)

        self.label_desc = QLabel("Slot Status")
        self.label_desc.setFont(QFont("Arial", 18))
        self.label_desc.setStyleSheet("color: white;")
        self.label_desc.setAlignment(Qt.AlignCenter)

        btn_ok = QPushButton("OK")
        btn_ok.setFixedSize(140, 48)
        btn_ok.setFont(QFont("Arial", 16, QFont.Bold))
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #D32F2F; }
            QPushButton:pressed { background-color: #B71C1C; }
        """)
        btn_ok.clicked.connect(self.on_ok_clicked)

        # ==========================================
        # 🔥 OK 버튼 중앙 정렬용 레이아웃
        # ==========================================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()

        inner.addWidget(label_title)
        inner.addWidget(self.label_desc)
        inner.addSpacing(10)
        inner.addLayout(btn_layout)   # 🔥 변경 포인트

        layout.addWidget(frame)

    # ======================================================
    # 중앙 배치 (show 이후 호출 필수)
    # ======================================================
    def _move_to_screen_center(self):
        """
        현재 화면 기준으로 위젯을 정확히 중앙에 배치
        """
        screen = QApplication.primaryScreen()
        if not screen:
            return

        screen_rect = screen.availableGeometry()
        self.adjustSize()

        x = screen_rect.center().x() - self.width() // 2
        y = screen_rect.center().y() - self.height() // 2

        self.move(x, y)

    # ======================================================
    # 외부 제어 API
    # ======================================================
    def show_on(self):
        self._show("SLOT Insert")

    @pyqtSlot()
    def show_off(self):
        self._show("SLOT Removed")

    def _show(self, message):
        if self._is_open:
            return
        self.label_desc.setText(message)
        self._is_open = True
        self.show()
        self.raise_()
        self.activateWindow()

        # show 이후 중앙 이동
        QTimer.singleShot(0, self._move_to_screen_center)

    def show_warning(self):
        """
        🔔 조건 만족 시 호출
        - 이미 열려 있으면 무시
        - 화면 정중앙에 표시
        - 전체 화면 입력 차단
        """
        if self._is_open:
            print("[SlotStatusOverlay] already open → ignore")
            return

        print("[SlotStatusOverlay] SHOW")
        self._is_open = True

        self.show()
        self.raise_()
        self.activateWindow()

        # show 이후 중앙 이동
        QTimer.singleShot(0, self._move_to_screen_center)

    def hide_warning(self):
        """
        배터리 상태 회복 시 자동 숨김
        """
        if not self._is_open:
            return

        print("[SlotStatusOverlay] HIDE")
        self._is_open = False
        self.hide()

    # ======================================================
    # 버튼 이벤트
    # ======================================================
    def on_ok_clicked(self):
        """
        사용자가 경고를 확인하고 닫을 때
        """
        print("[SlotStatusOverlay] OK clicked")
        self.hide_warning()