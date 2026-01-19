import os
import json
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
    switch_to_test_info = pyqtSignal(str)

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)

        self.select_menu = None
        self.test_type = None

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
        # TestInfoView 정보를 json에서 읽는다.
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')
        
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
        #self.label_18.setStyleSheet("Color : blue") #글자색 변환
        self.label_20 = self.findChild(QLabel, "label_20") #Result
        #self.label_20.setStyleSheet("Color : blue") #글자색 변환
        self.label_25_testItem = self.findChild(QLabel, "label_25_testItem") #Test Item Name
        self.label_25_testItem.setStyleSheet("Color : red") #글자색 변환

        # 버튼들 연결
        self.pushButton_ResultHome.clicked.connect(self.on_resultHome_button_clicked)
        self.pushButton_ResultBackArrow.clicked.connect(self.on_resultHome_button_clicked)
        #self.pushButton_Retest.clicked.connect(self.on_resultRetest_button_clicked)
        #self.pushButton_ResultSend.clicked.connect(self.on_resultSend_button_clicked)
        #self.pushButton_Print.clicked.connect(self.on_resultPrint_button_clicked)
        
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

    # 기존 홈 버튼을 OK 버튼으로 대체
    def on_resultHome_button_clicked(self):
        print("ResultView: HOME 버튼이 클릭되었습니다." )
        self.on_retry_measurement() # 모든값 초기화
        # 0.5초 후 결과 화면으로 전환:json 저장후
        QTimer.singleShot(
            500,
            lambda: self.switch_to_test_info.emit(
                self.test_type.code if hasattr(self.test_type, "code") else ""
            )
        )
        #self.switch_to_home.emit()
        
    def on_resultRetest_button_clicked(self):
        print("ResultView: RE-TEST 버튼이 클릭되었습니다.")
        self.on_retry_measurement() # 모든값 초기화
        
    def on_resultSend_button_clicked(self):
        print("ResultView: Send 버튼이 클릭되었습니다.")
        self.on_retry_measurement() # 모든값 초기화
        
    def on_resultPrint_button_clicked(self):
        print("ResultView: Print 버튼이 클릭되었습니다.")
        self.on_retry_measurement() # 모든값 초기화

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

            self.test_type = session.query(TestType).get(ts.test_type_id)
            operator = session.query(User).get(ts.operator_id)
            patient = (
                session.query(Patient).get(ts.patient_id)
                if ts.patient_id else None
            )

            self._bind_ui(ts, mr, self.test_type, operator, patient)

        finally:
            session.close()            

    # ==================================================
    # UI Binding
    # ==================================================
    def _bind_ui(self, ts, mr, test_type, operator, patient):
        analysis = mr.result_data.get("analysis_result", {})

        current_data = self._load_current_json()
        json_test_type1 = current_data.get("test_type1")
        json_operator_id = current_data.get("operator")
        json_patient_id = current_data.get("patient_id")
        """
        print(f"[ResultView0] json_test_type1 : {json_test_type1}")
        print(f"[ResultView0] json_operator_id : {json_operator_id}")
        print(f"[ResultView0] json_patient_id : {json_patient_id}")

        print(f"[ResultView0] test_type.code : {test_type.code}")
        print(f"[ResultView0] operator.user_id : {operator.user_id}")
        print(f"[ResultView0] patient.patient_code : {patient.patient_code}")
        """
        # 3-1 테스트 타입
        self.label_25_testItem.setText(test_type.name)

        # 3-2 측정 날짜
        self.label_23_date.setText(
            ts.completed_at.strftime("%Y-%m-%d %H:%M")
        )

        # 3-3 검사자
        # self.label_26_operatorId.setText(operator.user_id)
        self.label_26_operatorId.setText(json_operator_id)

        # 3-4 환자 ID
        if patient:
            self.label_21_patientId.setText(patient.patient_code)
            print(f"[ResultView0] patient.patient_code : {patient.patient_code}")
        else:
            self.label_21_patientId.setText("-")
            print("[ResultView0] patient 없음 (NULL)")

        # 3-5 컨트롤
        self.label_24_control.setText(
            "Valid" if analysis.get("positive") else "Invalid"
        )

        # 3-6 진단 결과
        self.label_22_result.setText(
            "POS" if analysis.get("positive") else "NEG"
        )

        # 3-7 썸네일 이미지
        #self._load_thumbnail(mr.thumbnail_path)

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

        #self.label_4_resultImage.setPixmap(rotated_pixmap)
        #self.label_4_resultImage.setScaledContents(True)     

    def _load_current_json(self):
        """
        TestInofView 에서 입력한 정보(json) 값을 다시 로드. 
        """
        try:
            if not os.path.exists(self.current_json_path):
                print("[ResultView0] current.json not found")
                return {}

            with open(self.current_json_path, "r") as f:
                return json.load(f)
            
            self.select_menu = data.get("select_menu", "")

            if self.select_menu == "QCTest":
                self.label.setText("QC RESULT");
                self.label_17.setText("QC ID");
            else:
                self.label.setText("RESULT");
                self.label_17.setText("PATIENT ID");

        except Exception as e:
            print(f"[ResultView0] current.json load error: {e}")
            return {}           
        

    def on_retry_measurement(self):
        """
        모든 값 초기화.
        """
        print("[ResultView0] reset for new measurement")

        # 1️⃣ UI 초기화
        # 필요시 결과 관련 라벨 전부 clear
        self.label_25_testItem.clear()
        self.label_23_date.clear()
        self.label_26_operatorId.clear()
        self.label_21_patientId.clear()
        self.label_24_control.clear()
        self.label_22_result.clear()
        #self.label_4_resultImage.clear()

        # 2️⃣ current.json 초기화
        self.reset_current_json()

    def reset_current_json(self):
        try:
            # 1️⃣ 기존 current.json 읽기
            with open(self.current_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 2️⃣ 유지해야 할 값은 그대로 둔다
            # data["select_menu"]
            # data["test_type1"]
            # data["operator"]

            # 3️⃣ 1회성 값만 초기화
            data["patient_id"] = None
            data["datentime"] = None
            data["control"] = None
            data["resultb"] = None
            data["resulta"] = None

            print("[ResultView0] current.json partial reset (keep select_menu, test_type1, operator)")

            # 4️⃣ JSON 저장
            self.update_json_file(data)

        except Exception as e:
            print(f"[ResultView0] current.json reset 중 오류 발생: {e}")

       
    def update_json_file(self, empty):
        try:
            with open(self.current_json_path, 'r+') as f:
                data = empty
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"[ResultView0] JSON 파일 업데이트 중 오류 발생: {e}")        