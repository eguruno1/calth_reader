from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QFrame, QPushButton, QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from controllers import app_controller
import subprocess   # 안전한 시스템 명령 실행용


class PowerStatusOverlayWidget(QWidget):
    """
    ⚠ Power 전역 안내 위젯
    - 항상 단 하나만 표시됨 (중복 오픈 방지)
    - 오픈 시 전체 UI 입력 차단
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.confirm_message = None

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
        self._shutdown_in_progress = False  # 🔒 중복 shutdown 방지

        self.hide()
        self._build_ui()

        # 카운트 다운 변수
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)
        self._countdown_sec = 0


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

        self.label_desc = QLabel("Power Status")
        self.label_desc.setFont(QFont("Arial", 18))
        self.label_desc.setStyleSheet("color: white;")
        self.label_desc.setAlignment(Qt.AlignCenter)

        self.label_desc2 = QLabel("Power Ask")
        self.label_desc2.setFont(QFont("Arial", 12))
        self.label_desc2.setStyleSheet("color: white;")
        # 멀티라인 표시
        self.label_desc2.setWordWrap(True)
        self.label_desc2.setAlignment(Qt.AlignCenter)
        # 레이아웃에서 높이 자동 확장 허용
        self.label_desc2.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        # =========================
        # 버튼 생성
        # =========================
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
        self.btn_ok.clicked.connect(self.on_ok_clicked)


        self.btn_cancle = QPushButton("Cancle")
        self.btn_cancle.setFixedSize(140, 48)
        self.btn_cancle.setFont(QFont("Arial", 16, QFont.Bold))
        self.btn_cancle.setStyleSheet("""
            QPushButton {
                background-color: #616161;
                color: white;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #424242; }
            QPushButton:pressed { background-color: #212121; }
        """)
        self.btn_cancle.clicked.connect(self.on_cancle_clicked)

        # ==========================================
        # 🔥 OK / Cancel 버튼 중앙 정렬 (같은 라인)
        # ==========================================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancle)
        btn_layout.addStretch()

        inner.addWidget(label_title)
        inner.addWidget(self.label_desc)
        inner.addWidget(self.label_desc2)
        inner.addSpacing(10)
        inner.addLayout(btn_layout)  

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
        self.confirm_message = ""
        self.label_desc2.setText(self.confirm_message)
        #self._show("Power ON")

    def show_off(self):
        self.confirm_message = (
            "When the system shuts down, it will\n"
            "automatically log out.\n\n"
            "Do you want to proceed?"
        )
        self._show("Power Off Confirmation.\n")

    def _show(self, message):
        # shutdown 진행 중에는 재오픈 금지
        if self._shutdown_in_progress:
            print("[PowerStatusOverlay] shutdown in progress → ignore show")
            return
        
        if self._is_open:
            return
        self.label_desc.setText(message)
        self.label_desc2.setText(self.confirm_message)
        # 텍스트 변경 후 크기 재계산
        self.label_desc2.adjustSize()

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
            print("[PowerStatusOverlay] already open → ignore")
            return

        print("[PowerStatusOverlay] SHOW")
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

        print("[PowerStatusOverlay] HIDE")
        self._is_open = False
        self.hide()

    # ======================================================
    # 버튼 이벤트
    # ======================================================
    def on_ok_clicked(self):
        """
        사용자가 OK 선택 → 장비 전원 종료
        """
        self._is_open = True

        # 이미 shutdown 진행 중이면 무시
        if self._shutdown_in_progress:
            print("[PowerStatusOverlay] Shutdown already in progress → ignore")
            return
    
        print("[PowerStatusOverlay] OK clicked → shutdown start")

        # shutdown 시작 플래그 설정
        self._shutdown_in_progress = True

        # 버튼 즉시 비활성화 (중복 클릭 방지)
        #self.btn_ok.setEnabled(False)
        #self.btn_cancle.setEnabled(False)
        #self.btn_ok.setText("Shutting down...")

        # 🔥 버튼 숨김
        self.btn_ok.hide()
        self.btn_cancle.hide()

        # 🔥 20초 카운트 시작
        self._countdown_sec = 20
        self.label_desc.setText("Shutting down...")
        self._update_countdown_text()
        self._countdown_timer.start(1000)

        # UART로 Power OFF 신호 전송
        app_controller.send_uart_command("P0")
        # → 위젯 유지
        #self.hide_warning()

        # sudoers에 의해 비밀번호 없이 실행됨
        try:
            subprocess.Popen(
                ["/sbin/shutdown", "-h", "now"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"[PowerStatusOverlay] shutdown failed: {e}")

    def on_cancle_clicked(self):
        """
        사용자가 경고를 확인하고 Cancle 때
        """
        # shutdown 시작 후 Cancel 무효
        if self._shutdown_in_progress:
            return
    
        print("[PowerStatusOverlay] Cancle clicked")

        # 파워 유지 P1 을 보냄.
        app_controller.send_uart_command("P1")
        self._is_open = False
        self.hide_warning()    

    # 카운트 표시용
    def _update_countdown_text(self):
        self.label_desc2.setText(
            f"The system will shut down in\n\n{self._countdown_sec} seconds."
        )
        self.label_desc2.adjustSize()

    # 타이머 tick 처리
    def _on_countdown_tick(self):
        self._countdown_sec -= 1

        if self._countdown_sec <= 0:
            self._countdown_timer.stop()
            print("[PowerStatusOverlay] Countdown finished → system shutdown")

            try:
                subprocess.Popen(
                    ["/sbin/shutdown", "-h", "now"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"[PowerStatusOverlay] shutdown failed: {e}")
            return

        self._update_countdown_text()
    
    