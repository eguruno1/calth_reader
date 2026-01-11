import os
import json
import threading

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore    import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QPixmap
from PyQt5           import uic

from views.Utils     import (update_date_time, start_date_time_update, stop_date_time_update)

class SelectView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_test_info = pyqtSignal(str)  # 테스트 유형을 전달하기 위한 시그널

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

        # JSON 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        # 배터리
        self.uart_model = uart_model
        print(f"[SelectView] uart_model injected: {self.uart_model}")

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'SelectViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Home', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 뒤로 가기 버튼 연결
        self.pushButton_SelectBackArrow.clicked.connect(self.on_back_button_clicked)

        # 버튼들 연결
        self.pushButton_Covid19.clicked.connect(lambda: self.on_test_button_clicked("COVID-19 Ag"))
        self.pushButton_Influenza.clicked.connect(lambda: self.on_test_button_clicked("Influenza A & B"))
        self.pushButton_Cadiac.clicked.connect(lambda: self.on_test_button_clicked("Cardiac Troponin I"))

        # 초기 날짜와 시간 설정
        self.update_date_time()
        
        # 초기 배터리 상태 설정
        # self.update_battery_status()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        # QTimer.singleShot(100, lambda: start_battery_update(self))
        # 배터리 상태 업데이트
        from controllers import app_controller
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)

    def closeEvent(self, event):
        stop_date_time_update(self)
        # stop_battery_update(self)    
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def on_test_button_clicked(self, test_type):
        self.update_json_file(test_type)
        self.switch_to_test_info.emit(test_type)

    def update_date_time(self):
        update_date_time(self)
    """    
    def update_battery_status(self):
        update_battery_status(self)
    """
    def update_json_file(self, test_type):
        try:
            with open(self.current_json_path, 'r+') as f:
                data = json.load(f)
                data['test_type1'] = test_type
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"JSON 파일 업데이트 중 오류 발생: {e}")

    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[SelectView] on_uart_event: {event_type}, {data}")
        print(
            f"[SelectView][{self.__class__.__name__}] on_uart_event "
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
            print(f"[SelectView] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[SelectView] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[SelectView] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[SelectView] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[SelectView] Battery UI update error: {e}")

