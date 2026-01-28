# -*- coding: utf-8 -*-


import sys
import os
import json
import threading
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QResizeEvent, QPixmap
from views.Utils import (center_window, update_date_time, start_date_time_update, stop_date_time_update)
from config.pretest_config import PretestConfig
# AutoTest
from views.widgets.auto_test_overlay import AutoTestOverlayWidget

class IncubationView(QMainWindow):

    switch_to_home = pyqtSignal()
    switch_to_test_info_view = pyqtSignal(str)
    switch_to_measure_view = pyqtSignal()

    def __init__(self, parent=None, uart_model=None):

        super().__init__(parent)
        
        self.test_type = "COVID19"
        self.auto_test = False

        # ==============================
        # ⏱️ Incubation Countdown 설정
        # ==============================
        self.incubation_total_seconds = 10 * 60  # 10분
        # self.incubation_total_seconds = 1 * 60  # 1분
        self.incubation_elapsed = 0
        self.incubation_timer = None

        self.load_ui()
        self.init_ui()

        # JSON 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        # 배터리
        self.uart_model = uart_model
        print(f"[IncubationView] uart_model injected: {self.uart_model}")

        

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'IncubationViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Test', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        # ProgressBar 스타일 설정
        progress_bar_style = """
            QProgressBar {
                border: 2px solid grey;
                border-radius: 10px;
                text-align: center;
                color: gray;
                font-size: 12pt;
                font-weight: bold;
            }

            QProgressBar::chunk {
                background-color: #4A4A6A;
                border-radius: 8px;
            }
        """
        self.progressBar.setStyleSheet(progress_bar_style)
        
        # ProgressBar에 숫자로 진행률 표시
        self.progressBar.setFormat("%p%")
        self.progressBar.setAlignment(Qt.AlignCenter)
        
        # ProgressBar의 텍스트 표시 활성화
        self.progressBar.setTextVisible(True)

        # 프로그레스바 초기화
        self.progressBar.setValue(0)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(self.incubation_total_seconds)


    def init_ui(self):
        # 초기 날짜와 시간 설정
        self.update_date_time()

        self._load_test_info()
        print(f"[IncubationView] 1 start_measurement test_type 로드: {self.test_type}")

        # 🔙 뒤로 가기 버튼 (UI objectName 불일치 대비)
        if hasattr(self, "pushButton_BackArrow"):
            self.pushButton_BackArrow.clicked.connect(self.on_back_button_clicked)
        else:
            print(
                "[IncubationView][WARN] pushButton_BackArrow not found in UI. "
                "Back button connection skipped."
            )
        

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

        # 배터리 상태 업데이트
        from controllers import app_controller
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)


        # ==============================
        # ⏱️ Incubation 카운트다운 시작
        # ==============================
        self.incubation_elapsed = 0

        # 초기 표시: 10:00
        if hasattr(self, "label_Countdown"):
            self.label_Countdown.setText("10:00")

        self.incubation_timer = QTimer(self)
        self.incubation_timer.timeout.connect(self.update_incubation_countdown)
        self.incubation_timer.start(1000)  # 1초   


    def closeEvent(self, event):
        stop_date_time_update(self)

        if self.incubation_timer and self.incubation_timer.isActive():
            self.incubation_timer.stop()

        super().closeEvent(event)


    def on_back_button_clicked(self):
        print(f"[IncubationView] Back clicked, auto_test={self.auto_test}")

        try:
            with open(self.current_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.test_type = data.get("test_type1", "")
            self.auto_test = data.get("auto_test", False)

            # ⏱️ Back 버튼 클릭 시 타이머 일시 중지
            if self.incubation_timer and self.incubation_timer.isActive():
                print("[IncubationView] Stop incubation timer for back action")
                self.incubation_timer.stop()

            # ✅ Standard Test → 기존 동작 유지
            if not self.auto_test:
                self.switch_to_test_info_view.emit(self.test_type)
                return

            # ✅ Auto Test → Overlay 표시
            self._show_auto_test_overlay()

        except Exception as e:
            print(f"[IncubationView] Back button flow error: {e}")
    

    """ Old
    def on_back_button_clicked(self):
        print(f"[IncubationView] 1 on_back_button_clicked self.auto_test:{self.auto_test}")

        # 🔴 타이머가 돌고 있으면 QMessageBox 전에 정지 (중요)
        if self.incubation_timer and self.incubation_timer.isActive():
            print("[IncubationView] Stop incubation timer before QMessageBox")
            self.incubation_timer.stop()

        try:
            # ✅ 1단계: JSON 읽기 (읽기 전용 OK)
            with open(self.current_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.test_type = data.get("test_type1", "")
            self.auto_test = data.get("auto_test", False)

            print(f"[IncubationView] 2 on_back_button_clicked self.auto_test:{self.auto_test}")

            # ✅ Auto Test 아닐 경우 → 기존 흐름 유지
            if not self.auto_test:
                self.switch_to_test_info_view.emit(self.test_type)
                return

            # ✅ Auto Test 일 경우 QMessageBox
            reply = QMessageBox.question(
                self,
                "Warning",
                "This is Auto Test mode.\n\nDo you want to stop it?",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel
            )

            print(f"[IncubationView] QMessageBox reply = {reply}")

            # ✅ OK 클릭 시
            if reply == QMessageBox.Ok:
                try:
                    # 수정: r+ 모드 (읽기 + 쓰기)
                    with open(self.current_json_path, "r+", encoding="utf-8") as f:
                        data = json.load(f)
                        data["auto_test"] = False
                        f.seek(0)
                        json.dump(data, f, indent=4)
                        f.truncate()

                    print("[IncubationView] auto_test successfully set to False")

                except Exception as e:
                    print(f"[IncubationView] auto_test update failed: {e}")

                # ✅ 홈으로 이동
                self.switch_to_home.emit()

            else:
                # ❗ Cancel 시 타이머 재개 (UX 안정성)
                if self.incubation_timer:
                    self.incubation_timer.start(1000)

        except Exception as e:
            print(f"[IncubationView] Auto Test flow error: {e}")
    """


    def update_date_time(self):
        update_date_time(self)    


    def update_progress(self):
        self.progress_value += 1
        self.progressBar.setValue(self.progress_value)
        
        if self.progress_value >= 100:
            self.timer.stop()
            self.switch_to_measure_view.emit()

    def _go_to_measure_view(self):
        """MeasureView 이동"""
        #self.reset_widget_positions()
        self.switch_to_measure_view.emit()


    def _load_test_info(self):
        """
        JSON에서 검사 정보 읽기 (Read Only)
        """
        try:
            with open(self.current_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.test_type = data.get("test_type1", "")
            self.auto_test = data.get("auto_test", False)

            print(f"[IncubationView] _load_test_info test_type / auto_test 로드: {self.test_type}, {self.auto_test}")

        except Exception as e:
            print(f"[IncubationView] JSON 로드 오류: {e}")


    def update_incubation_countdown(self):
        """카운트다운"""
        self.incubation_elapsed += 1

        remaining = self.incubation_total_seconds - self.incubation_elapsed
        if remaining < 0:
            remaining = 0

        # ProgressBar 업데이트 (경과 기준)
        self.progressBar.setValue(self.incubation_elapsed)

        # MM:SS 포맷
        minutes = remaining // 60
        seconds = remaining % 60
        time_text = f"{minutes:02d}:{seconds:02d}"

        # QLabel 업데이트
        if hasattr(self, "label_Countdown"):
            self.label_Countdown.setText(time_text)

        # 종료 조건
        if self.incubation_elapsed >= self.incubation_total_seconds:
            print("[IncubationView] Incubation 완료 → MeasureView 이동")
            self.incubation_timer.stop()
            self.switch_to_measure_view.emit()


    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[IncubationView] on_uart_event: {event_type}, {data}")
        print(
            f"[IncubationView][{self.__class__.__name__}] on_uart_event "
            f"thread={threading.current_thread().name}"
        )

        if event_type == "battery_changed" and data:
            # ❗ UART RX 스레드 → UI 스레드로 전달
            QMetaObject.invokeMethod(
                self,
                "_update_battery_ui",
                Qt.QueuedConnection,
                Q_ARG(object, data)
            )

    @pyqtSlot(object)
    def _update_battery_ui(self, battery_info):
        if not hasattr(self, "label_BatteryGuage") or not hasattr(self, "label_BatteryGuageTxt"):
            return

        try:
            icon_name = battery_info.get_icon_name()
            print(f"[IncubationView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[IncubationView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[IncubationView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[IncubationView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[IncubationView] Battery UI update error: {e}")    


    # -------------------------------------------------
    # Auto Test Overlay (Back Button용)
    # -------------------------------------------------
    def _show_auto_test_overlay(self):
        """
        Auto Test 중지 확인 Overlay 표시
        - OK  → Auto Test 종료 + Home 이동
        - Cancel → Overlay 닫힘, Incubation 계속
        """
        print("[IncubationView] Show Auto Test Overlay")

        self.auto_test_overlay = AutoTestOverlayWidget(parent=self)

        # OK → Auto Test 중지
        self.auto_test_overlay.signal_stop.connect(
            self._stop_auto_test_and_go_home
        )

        # Cancel → 아무 것도 하지 않음 (Overlay만 닫힘)
        self.auto_test_overlay.signal_timeout.connect(
            self._resume_incubation_after_overlay
        )

        self.auto_test_overlay.show()


    def _stop_auto_test_and_go_home(self):
        """
        Auto Test 중지 → Home 이동
        + Incubation 진행 상태 완전 초기화
        """
        print("[IncubationView] Auto Test stopped by overlay")

        # ==================================================
        # ⏹️ Incubation 타이머 정지
        # ==================================================
        if self.incubation_timer and self.incubation_timer.isActive():
            self.incubation_timer.stop()

        # ==================================================
        # 🔄 Incubation 상태 변수 초기화
        # ==================================================
        self.incubation_elapsed = 0

        # ==================================================
        # 📊 ProgressBar 초기화
        # ==================================================
        if hasattr(self, "progressBar"):
            self.progressBar.setValue(0)

        # ==================================================
        # ⏳ Countdown Label 초기화
        # ==================================================
        if hasattr(self, "label_Countdown"):
            minutes = self.incubation_total_seconds // 60
            seconds = self.incubation_total_seconds % 60
            self.label_Countdown.setText(f"{minutes:02d}:{seconds:02d}")

        # ==================================================
        # 📝 auto_test = False 로 JSON 업데이트
        # ==================================================
        try:
            with open(self.current_json_path, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["auto_test"] = False
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"[IncubationView] auto_test update error: {e}")

        # ==================================================
        # 🏠 Home 이동
        # ==================================================
        self.switch_to_home.emit()



    def _resume_incubation_after_overlay(self):
        """
        Cancel 클릭 시 → Incubation 계속
        """
        print("[IncubationView] Auto Test 유지 (Cancel)")

        if self.incubation_timer and not self.incubation_timer.isActive():
            self.incubation_timer.start(1000)
            