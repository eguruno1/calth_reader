import os
import json
import threading
from datetime import datetime

from PyQt5              import uic
from PyQt5.QtWidgets    import QMainWindow
from PyQt5.QtCore       import (QTimer, pyqtSignal, QMetaObject, Qt, Q_ARG, pyqtSlot)
from PyQt5.QtGui        import QPixmap

from views.Utils        import (update_date_time, start_date_time_update, stop_date_time_update)
from controllers import measurement_controller, app_controller


class MeasureView(QMainWindow):
    #switch_to_test_info = pyqtSignal()
    #measure_finished    = pyqtSignal()
    switch_to_result = pyqtSignal()  # ResultView로 전환하기 위한 시그널

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

        # 배터리
        self.uart_model = uart_model
        print(f"[MeasureView] uart_model injected: {self.uart_model}")
        
    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        # TestInfoView 정보를 json에서 읽는다.
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')
        
        # UI 파일 경로 설정 
        ui_filename = 'MeasureViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Test', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")   
        
        self._load_test_info()

    def init_ui(self):
        
        self.progressBar_Meas.setMinimum(0)
        self.progressBar_Meas.setMaximum(100)  # 100%로 설정
        self.progressBar_Meas.setValue(0)

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
        self.progressBar_Meas.setStyleSheet(progress_bar_style)
        
        # ProgressBar에 숫자로 진행률 표시
        self.progressBar_Meas.setFormat("%p%")
        self.progressBar_Meas.setAlignment(Qt.AlignCenter)
        
        # ProgressBar의 텍스트 표시 활성화
        self.progressBar_Meas.setTextVisible(True)

        # 프로그레스바 초기화
        self.progressBar_Meas.setValue(0)

        # 타이머 설정 (측정 컨트롤러 사용)
        self.measurement_controller = measurement_controller
        
        # 측정 컨트롤러 시그널 연결
        self.measurement_controller.measurement_started.connect(self.on_measurement_started)
        self.measurement_controller.measurement_finished.connect(self.on_measurement_finished)
        self.measurement_controller.progress_updated.connect(self.on_progress_updated)
        self.measurement_controller.error_occurred.connect(self.on_measurement_error)

        # 날짜와 시간 표시
        self.update_date_time()


    def _load_test_info(self):
        """
        JSON에서 검사 정보 읽기 (Read Only)
        """
        try:
            with open(self.current_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.test_type = data.get("test_type1", "")

            print(f"[MeasureView] test_type 로드: {self.test_type}")

        except Exception as e:
            print(f"[MeasureView] JSON 로드 오류: {e}")


    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        #QTimer.singleShot(100, lambda: start_battery_update(self))
        #QTimer.singleShot(500, self.start_measurement)  # 측정 시작

        # ✅ 1. LED 먼저 켠다
        QTimer.singleShot(300, self._prepare_and_start_measurement)
        
        # 배터리 상태 업데이트
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)

    def _prepare_and_start_measurement(self):
        """
        test_3line_auto와 동일한 흐름:
        LED ON → ISP 안정화 → 측정 시작
        """
        print("[MeasureView] LED ON (pre-measurement)")
        app_controller.led_on(45)

        # ISP / AE 안정화 대기 (중요)
        QTimer.singleShot(1500, self.start_measurement)            

    def start_measurement(self):
        """측정 시작 - 컨트롤러에 위임"""
        print("측정 시작 요청")
        measurement_controller.test_type = self.test_type  # 2 or 3 라인 판독을 위해....
        success = self.measurement_controller.start_measurement()
        if not success:
            print("측정 시작 실패")

    def on_measurement_started(self):
        """측정 시작됨 (컨트롤러에서 알림)"""
        print("측정이 시작되었습니다")
        self.progressBar_Meas.setValue(0)
        self.progressBar_Meas.setFormat("측정 준비 중... - %p%")

    def on_progress_updated(self, progress: int, phase_name: str):
        """진행률 업데이트 (컨트롤러에서 알림)"""
        self.progressBar_Meas.setValue(progress)
        self.progressBar_Meas.setFormat(f"{phase_name} - %p%")

    def on_measurement_finished(self, result: dict):
        """측정 완료 (컨트롤러에서 알림)"""
        print(f"측정 완료: {result}")

        """
        측정 완료 후 JSON 결과 반영
        """
        try:
            with open(self.current_json_path, "r+", encoding="utf-8") as f:
                data = json.load(f)

                # 결과만 갱신
                data["datentime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data["control"]   = "Positive" if result["analysis_result"]["positive"] else "Negative"
                data["resulta"]   = "POS" if result["analysis_result"]["positive"] else "NEG"
                data["resultb"]   = "POS" if result["analysis_result"]["positive"] else "NEG"

                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()

            print("[MeasureView] JSON 결과 업데이트 완료")

        except Exception as e:
            print(f"[MeasureView] JSON 업데이트 오류: {e}")

        self.progressBar_Meas.setFormat("측정 완료 - %p%")
        # 1초 후 결과 화면으로 전환
        QTimer.singleShot(1000, lambda: self.switch_to_result.emit())

    def on_measurement_error(self, error_message: str):
        """측정 오류 (컨트롤러에서 알림)"""
        print(f"측정 오류: {error_message}")
        self.progressBar_Meas.setFormat(f"오류: {error_message}")

    def closeEvent(self, event):
        """뷰 종료시 정리"""
        stop_date_time_update(self)
        # stop_battery_update(self)
        
        # 측정 중이라면 중지
        if hasattr(self, 'measurement_controller'):
            self.measurement_controller.stop_measurement()
        
        super().closeEvent(event)

    def update_date_time(self):
        update_date_time(self)

    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[MeasureView] on_uart_event: {event_type}, {data}")
        print(
            f"[MeasureView][{self.__class__.__name__}] on_uart_event "
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
            print(f"[MeasureView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[MeasureView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[MeasureView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[MeasureView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[MeasureView] Battery UI update error: {e}")    