import os
import threading
from datetime import datetime

from PyQt5           import uic
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtCore    import pyqtSignal, QTimer, QMetaObject, Qt, Q_ARG, pyqtSlot
from PyQt5.QtGui     import QPixmap, QTransform

from views.Utils     import (update_date_time, start_date_time_update, stop_date_time_update)

from controllers import app_controller

# DB
from database.connection import get_db_session
from database.models import (
    TestSession,
    MeasurementResult,
    TestType,
    User,
    Patient
)

class ResultView0(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

        self._test_session_id = None

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

    # DB 저장을 위해...
    def set_test_session_id(self, test_session_id):
        print(f"[ResultView0] set_test_session_id: {test_session_id}")
        self._test_session_id = test_session_id

        self.load_result_data()
        

    def showEvent(self, event):
        super().showEvent(event)
        
        if self._test_session_id:
            self.load_result_data()

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


    # ==================================================
    # Data Load
    # ==================================================
    def load_result_data(self):
        if not self._test_session_id:
            print("[ResultView0] test_session_id 없음")
            return

        session = get_db_session()
        try:
            ts = (
                session.query(TestSession)
                .filter(TestSession.id == self._test_session_id)
                .first()
            )

            if not ts:
                raise Exception("TestSession not found")

            mr = (
                session.query(MeasurementResult)
                .filter(MeasurementResult.session_id == ts.id)
                .order_by(MeasurementResult.measured_at.desc())
                .first()
            )

            test_type = session.query(TestType).get(ts.test_type_id)
            operator = session.query(User).get(ts.operator_id)
            patient = (
                session.query(Patient).get(ts.patient_id)
                if ts.patient_id else None
            )

            self._bind_ui(ts, mr, test_type, operator, patient)

        finally:
            session.close()            

    # ==================================================
    # UI Binding
    # ==================================================
    def _bind_ui(self, ts, mr, test_type, operator, patient):
        analysis = mr.result_data.get("analysis_result", {})

        # 3-1 테스트 타입
        self.label_25_testItem.setText(test_type.code)

        # 3-2 측정 날짜
        self.label_23_date.setText(
            ts.completed_at.strftime("%Y-%m-%d %H:%M")
        )

        # 3-3 검사자
        self.label_26_operatorId.setText(operator.user_id)

        # 3-4 환자 ID
        self.label_21_patientId.setText(
            patient.patient_id if patient else "-"
        )

        # 3-5 컨트롤
        self.label_24_control.setText(
            "Positive" if analysis.get("positive") else "Negative"
        )

        # 3-6 진단 결과
        self.label_22_result.setText(
            "POS" if analysis.get("positive") else "NEG"
        )

        # 3-7 썸네일 이미지
        self._load_thumbnail(mr.thumbnail_path)

    def _load_thumbnail(self, image_path: str):
        if not image_path or not os.path.exists(image_path):
            print("[ResultView0] thumbnail not found")
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("[ResultView0] Failed to load thumbnail pixmap")
            return

        # 🔁 90도 회전 (가로 → 세로)
        transform = QTransform()
        transform.rotate(90)   # 시계 방향
        rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)

        self.label_4_resultImage.setPixmap(rotated_pixmap)
        self.label_4_resultImage.setScaledContents(True)        