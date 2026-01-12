import os
import threading

from PyQt5           import uic
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtCore    import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QPixmap

from views.Utils     import (update_date_time, start_date_time_update, stop_date_time_update)

from controllers import app_controller

class ResultView0(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

        # 배터리
        self.uart_model = uart_model
        print(f"[ResultView0] uart_model injected: {self.uart_model}")

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'ResultView0Window.ui'
        ui_file = os.path.join(project_root, 'ui', 'Review', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # label 찾기
        self.label_18 = self.findChild(QLabel, "label_18") #Test Item Title
        self.label_18.setStyleSheet("Color : blue") #글자색 변환
        self.label_20 = self.findChild(QLabel, "label_20") #Result
        self.label_20.setStyleSheet("Color : blue") #글자색 변환
        self.label_25_testItem = self.findChild(QLabel, "label_25_testItem") #Test Item Name
        self.label_25_testItem.setStyleSheet("Color : red") #글자색 변환

        # 버튼들 연결
        self.pushButton_ResultHome.clicked.connect(self.on_resultHome_button_clicked)
        self.pushButton_Retest.clicked.connect(self.on_resiltRetest_button_clicked)
        self.pushButton_ResultSend.clicked.connect(self.on_resultSend_button_clicked)
        self.pushButton_Print.clicked.connect(self.on_resultPrint_button_clicked)
        
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        # QTimer.singleShot(100, lambda: start_battery_update(self))

        # 배터리 상태 업데이트
        model = app_controller.uart_model
        battery_info = model.get_battery_info()
        if battery_info:
            self._update_battery_ui(battery_info)

    def closeEvent(self, event):
        stop_date_time_update(self)
        # stop_battery_update(self)
        super().closeEvent(event)

    def on_resultHome_button_clicked(self):
        print("ResultView: HOME 버튼이 클릭되었습니다." )
        self.switch_to_home.emit()
        
    def on_resiltRetest_button_clicked(self):
        print("ResultView: RE-TEST 버튼이 클릭되었습니다.")
        
    def on_resultSend_button_clicked(self):
        print("ResultView: Send 버튼이 클릭되었습니다.")
        
    def on_resultPrint_button_clicked(self):
        print("ResultView: Print 버튼이 클릭되었습니다.")

    def update_date_time(self):
        update_date_time(self)

    #####################################################
    # Battery Status (UART 기반)
    #####################################################
    def on_uart_event(self, event_type: str, data):
        print(f"[ResultView0] on_uart_event: {event_type}, {data}")
        print(
            f"[ResultView0][{self.__class__.__name__}] on_uart_event "
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
            print(f"[ResultView0] Battery UI icon_name: {icon_name}")

            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)

            icon_path = os.path.join(
                project_root,
                "ui", "image", "Icon",
                icon_name
            )

            if not os.path.exists(icon_path):
                print(f"[ResultView0] Battery icon not found: {icon_path}")
                return

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"[ResultView0] Failed to load pixmap: {icon_path}")
                return

            self.label_BatteryGuage.setPixmap(pixmap)
            self.label_BatteryGuage.setScaledContents(True)

            self.label_BatteryGuageTxt.setText(
                battery_info.get_status_text()
            )

            print(f"[ResultView0] Battery UI updated: {battery_info.level}%")

        except Exception as e:
            print(f"[ResultView0] Battery UI update error: {e}")