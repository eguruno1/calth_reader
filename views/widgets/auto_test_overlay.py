from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout,
    QFrame, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont


class AutoTestOverlayWidget(QWidget):
    """
    🔁 Auto Test 중단 확인 Overlay

    동작 요약:
    - 위젯이 열리면 자동으로 10초 카운트다운 시작
    - OK 클릭 → Auto Test 중지 (signal_stop)
    - 10초 경과 → 자동 다음 진단 (signal_timeout)
    """

    signal_stop = pyqtSignal()
    signal_timeout = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # ===============================
        # Window 설정 (Power Overlay 동일)
        # ===============================
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_TranslucentBackground)

        if parent:
            self.resize(parent.size())

        # ===============================
        # 상태 변수
        # ===============================
        self._is_open = False
        self._count = 10

        # ===============================
        # UI 구성
        # ===============================
        self._build_ui()

        # ===============================
        # 타이머 (⚠ showEvent 에서 start)
        # ===============================
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    # ======================================================
    # UI 구성 (디자인 전용)
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

        # 타이틀
        title = QLabel("⚠ Auto Test")
        title.setFont(QFont("Arial", 26, QFont.Bold))
        title.setStyleSheet("color: yellow;")
        title.setAlignment(Qt.AlignCenter)

        # 안내 + 카운트 (하나로 통합)
        self.label_message = QLabel("Do you want to stop Auto Test?\n\n10 Sec")
        self.label_message.setFont(QFont("Arial", 18))
        self.label_message.setStyleSheet("color: white;")
        self.label_message.setAlignment(Qt.AlignCenter)
        self.label_message.setWordWrap(True)
        self.label_message.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        # OK 버튼
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setFixedSize(140, 48)
        self.btn_ok.setFont(QFont("Arial", 16, QFont.Bold))
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #D32F2F; }
            QPushButton:pressed { background-color: #B71C1C; }
        """)
        self.btn_ok.clicked.connect(self._on_ok_clicked)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addStretch()

        inner.addWidget(title)
        inner.addWidget(self.label_message)
        inner.addSpacing(10)
        inner.addLayout(btn_layout)

        layout.addWidget(frame)

    # ======================================================
    # Overlay 표시 API (외부에서 호출)
    # ======================================================
    def show_overlay(self):
        """
        Auto Test 단계 전환 시 호출
        """
        if self._is_open:
            return

        self._is_open = True
        self._count = 10
        self._update_message()

        self.show()
        self.raise_()
        self.activateWindow()

        QTimer.singleShot(0, self._move_to_center)

    # ======================================================
    # showEvent → 타이머 시작 (🔥 핵심)
    # ======================================================
    def showEvent(self, event):
        super().showEvent(event)

        # 타이머 중복 방지
        if self._timer.isActive():
            self._timer.stop()

        self._timer.start(1000)

    # ======================================================
    # Timer Tick
    # ======================================================
    def _on_tick(self):
        self._count -= 1
        self._update_message()

        if self._count <= 0:
            self._timer.stop()
            self._is_open = False
            self.close()
            self.signal_timeout.emit()

    # ======================================================
    # OK 클릭
    # ======================================================
    def _on_ok_clicked(self):
        self._timer.stop()
        self._is_open = False
        self.close()
        self.signal_stop.emit()

    # ======================================================
    # 텍스트 갱신
    # ======================================================
    def _update_message(self):
        self.label_message.setText(
            "Do you want to stop Auto Test?\n\n"
            f"{self._count} Sec"
        )
        self.label_message.adjustSize()

    # ======================================================
    # 중앙 정렬
    # ======================================================
    def _move_to_center(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return

        rect = screen.availableGeometry()
        self.adjustSize()

        self.move(
            rect.center().x() - self.width() // 2,
            rect.center().y() - self.height() // 2
        )
