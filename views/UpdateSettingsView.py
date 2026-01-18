# -*- coding: utf-8 -*-
"""
Update Settings View - 소프트웨어 업데이트 화면
(UI 파일 수정 없이 내부 위젯만 사용)
"""
import os
import json

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QProgressDialog
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update


class UpdateSettingsView(QMainWindow):
    """소프트웨어 업데이트 화면"""

    switch_to_settings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # --------------------------------------------------
        # 프로젝트 루트 경로
        # --------------------------------------------------
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(current_dir)

        # --------------------------------------------------
        # UI 로드
        # --------------------------------------------------
        ui_file = os.path.join(
            self.project_root,
            'ui', 'Settings', 'UpdateSettingsViewWindow.ui'
        )

        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(ui_file)

        # --------------------------------------------------
        # 내부 변수
        # --------------------------------------------------
        self.progress_dialog = None
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_update_progress)
        self.progress_value = 0
        self.new_version = None

        self.init_ui()
        self.load_current_versions()

    # ==================================================
    # UI 초기화
    # ==================================================
    def init_ui(self):
        self.pushButton_BackArrow.clicked.connect(self.on_back_button_clicked)
        self.btn_software_update.clicked.connect(self.on_software_update_clicked)
        self.update_date_time()

    # ==================================================
    # 현재 버전 로드
    # ==================================================
    def load_current_versions(self):
        version = self._get_local_sw_version()
        self.label_software_version.setText(f"현재 버전: {version}")

    def _get_local_sw_version(self):
        try:
            info_path = os.path.join(self.project_root, 'info', 'info.json')
            with open(info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('sw_version', 'Unknown')
        except Exception:
            return "Unknown"

    # ==================================================
    # 업데이트 버튼 클릭
    # ==================================================
    def on_software_update_clicked(self):
        try:
            local_version = self._get_local_sw_version()
            usb_info = self._find_usb_info_json()

            if not usb_info:
                QMessageBox.warning(self, "업데이트", "USB 메모리를 찾을 수 없습니다.")
                return

            usb_version = self._get_usb_sw_version(usb_info)

            if self._compare_versions(local_version, usb_version) >= 0:
                QMessageBox.information(self, "업데이트", "최신버전 입니다.")
                return

            reply = QMessageBox.question(
                self,
                "소프트웨어 업데이트",
                f"새 버전이 있습니다.\n\n"
                f"현재: {local_version}\n"
                f"USB: {usb_version}\n\n"
                f"업데이트 하시겠습니까?",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel
            )

            if reply == QMessageBox.Ok:
                self._start_update(usb_version)

        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    # ==================================================
    # USB 탐색
    # ==================================================
    def _find_usb_info_json(self):
        media_root = "/media/calth"

        if not os.path.exists(media_root):
            return None

        for user in os.listdir(media_root):
            candidate = os.path.join(
                media_root, user,
                "calth_reader", "info", "info.json"
            )
            if os.path.exists(candidate):
                return candidate

        return None

    def _get_usb_sw_version(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get("sw_version", "0.0.0")

    # ==================================================
    # 버전 비교
    # ==================================================
    def _compare_versions(self, v1, v2):
        a = [int(x) for x in v1.split(".")]
        b = [int(x) for x in v2.split(".")]
        return (a > b) - (a < b)

    # ==================================================
    # 업데이트 시작 (ProgressDialog 사용)
    # ==================================================
    def _start_update(self, new_version):
        self.new_version = new_version
        self.progress_value = 0

        # ----------------------------------------------
        # UpdateSettingsView 전용 프로그레스 다이얼로그
        # ----------------------------------------------
        self.progress_dialog = QProgressDialog(
            "소프트웨어 업데이트 진행 중입니다...",
            None,          # Cancel 버튼 제거
            0,
            100,
            self
        )
        self.progress_dialog.setWindowTitle("업데이트")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.show()

        # 2분 ≒ 120초 → 100단계 → 1.2초
        self.update_timer.start(1200)

    def _on_update_progress(self):
        self.progress_value += 1
        self.progress_dialog.setValue(self.progress_value)
        self.progress_dialog.setLabelText(
            f"업데이트 진행 중입니다... ({self.progress_value}%)"
        )

        if self.progress_value >= 100:
            self.update_timer.stop()
            self.progress_dialog.close()
            self._finish_update()

    # ==================================================
    # 업데이트 완료
    # ==================================================
    def _finish_update(self):
        try:
            info_path = os.path.join(self.project_root, 'info', 'info.json')

            with open(info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data['sw_version'] = self.new_version

            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "업데이트 완료", "업데이트가 완료되었습니다.")
            self.load_current_versions()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"업데이트 실패: {e}")

    # ==================================================
    # 공통
    # ==================================================
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_settings.emit()

    def update_date_time(self):
        update_date_time(self)
