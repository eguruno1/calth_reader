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

# 진단 분석 진행상태 DB 처리
import uuid
from database.connection import get_db_session
from database.models import TestSession, MeasurementResult, TestType
from common.session_context import get_session_context
from analysis.quality import calculate_quality_score

class MeasureView(QMainWindow):
    #switch_to_test_info = pyqtSignal()
    #measure_finished    = pyqtSignal()
    switch_to_result = pyqtSignal(int)  # ResultView0로 전환하기 위한 시그널

    def __init__(self, parent=None, uart_model=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

        # 배터리
        self.uart_model = uart_model
        print(f"[MeasureView] uart_model injected: {self.uart_model}")

        # 진단결과 처리용
        self.test_session_id = None
        self.test_session_uuid = None
        
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

            print(f"[MeasureView] _load_test_info test_type 로드: {self.test_type}")

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
        print("[MeasureView] 측정 시작 요청")
        print(f"[MeasureView] 0 start_measurement test_type 로드: {self.test_type}")
        # JSON에서 설정된 정보를 기준으로 진행한다.
        self._load_test_info()
        print(f"[MeasureView] 1 start_measurement test_type 로드: {self.test_type}")
        # DB 진단 시작정보 저장.
        self.create_test_session(self.test_type)

        measurement_controller.test_type = self.test_type  # 2 or 3 라인 판독을 위해....
        measurement_controller.test_session_id = self.test_session_id

        success = self.measurement_controller.start_measurement()

        if not success:
            print("측정 시작 실패")

    def on_measurement_started(self):
        """측정 시작됨 (컨트롤러에서 알림)"""
        print("[MeasureView] 측정이 시작되었습니다")
        self.progressBar_Meas.setValue(0)
        self.progressBar_Meas.setFormat("측정 준비 중... - %p%")

        

    def on_progress_updated(self, progress: int, phase_name: str):
        """진행률 업데이트 (컨트롤러에서 알림)"""
        self.progressBar_Meas.setValue(progress)
        self.progressBar_Meas.setFormat(f"{phase_name} - %p%")

    def on_measurement_finished(self, result: dict):
        """측정 완료 (컨트롤러에서 알림)"""
        print(f"[MeasureView] 측정 완료: {result}")

        """
        측정 완료 후 DB 저장을 위한 파라미터 세팅
        및 JSON 결과 반영
        """
        # ✅ 1. 결과 멤버 변수 선 저장 (가장 중요)
        self.analysis_result = result.get("analysis_result")
        self.captured_image_path = result.get("captured_image")
        self.result_image_path = result.get("result_image")
        self.thumbnail_path = result.get("thumbnail_image")

        # 안전성 체크
        if not self.analysis_result:
            self.mark_session_failed("analysis_result is missing")
            return
        
        # ✅ 2. JSON 업데이트 (DB와 분리)
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

        # ✅ 3. DB 저장 (핵심)
        try:
            self.save_measurement_result()
        except Exception as e:
            print(f"[MeasureView] DB 저장 실패: {e}")
            self.mark_session_failed(str(e))
            return

        self.progressBar_Meas.setFormat("측정 완료 - %p%")
        # 1초 후 결과 화면으로 전환 : 현재 test_session_id를 파라미터로 전달 & 데이터 조회용.
        QTimer.singleShot(1000, lambda: self.switch_to_result.emit(self.test_session_id))

    def on_measurement_error(self, error_message: str):
        """측정 오류 (컨트롤러에서 알림)"""
        print(f"측정 오류: {error_message}")
        self.progressBar_Meas.setFormat(f"오류: {error_message}")
        # 진단 오류 저장.
        self.mark_session_failed(error_message)

    def closeEvent(self, event):
        """뷰 종료시 정리"""
        stop_date_time_update(self)
        # stop_battery_update(self)
        
        # 측정 중이라면 중지
        if hasattr(self, 'measurement_controller'):
            self.measurement_controller.stop_measurement()

        #프로그레스 초기화.
        self._reset_progress_bar()

        super().closeEvent(event)

    def update_date_time(self):
        update_date_time(self)


    def _reset_progress_bar(self):
        """progressBar 초기화"""
        self.progressBar_Meas.setValue(0)
        self.progressBar_Meas.setFormat("")
        self.progressBar_Meas.repaint()
    #####################################################
    # DB 처리
    #####################################################
    def create_test_session(self, test_type_code: str):
        session = get_db_session()
        try:
            test_type_id = self.get_test_type_id_by_code(test_type_code)

            session_user = get_session_context()
            operator_id = session_user["user_pk"]

            current_data = self._load_current_json()
            json_patient_id = current_data.get("patient_id")
            print(f"[MeasureView] json_patient_id : {json_patient_id}")

            # TestSession 세션 진행중 처리
            test_session = TestSession(
                session_id=uuid.uuid4(),
                test_type_id=test_type_id,     # ✅ int
                operator_id=operator_id,
                patient_id=json_patient_id if json_patient_id else None,
                device_serial=None,
                cartridge_lot=None,
                temperature=None,
                humidity=None,
                status="in_progress",
                started_at=datetime.now()
            )

            session.add(test_session)
            session.commit()
            session.refresh(test_session)

            self.test_session_id = test_session.id
            return test_session

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()     


    def save_measurement_result(self):
        """
        진단결과 저장.
        """
        if not self.test_session_id:
            raise Exception("[MeasureView] save_measurement_result : test_session_id is None")
    
        session = get_db_session()
        try:
            quality_score = calculate_quality_score(
                metrics=self.analysis_result["metrics"],
                line_count=self.analysis_result["line_count"],
                expected_lines=2 if self.analysis_result["mode"] == 2 else 3
            )

            # 결과 저장
            result = MeasurementResult(
                session_id=self.test_session_id,        # FK
                measurement_type=self.test_type,        # 예: COVID19
                result_data={
                    "analysis_result": self.analysis_result,
                    "timestamp": datetime.now().isoformat()
                },
                image_path=self.result_image_path, #self.captured_image_path
                thumbnail_path=self.thumbnail_path,
                quality_score=quality_score,
                is_valid=True
            )
            session.add(result)

            print(f"[MeasureView] save_measurement_result : {result}")

            # TestSession 세션 완료 처리
            ts = session.query(TestSession).get(self.test_session_id)
            ts.status = "completed"
            ts.completed_at = datetime.now()

            session.commit()
            print("[MeasureView] measurement_result + session completed 저장 완료")

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()            

    def mark_session_failed(self, error_msg):
        """
        진단 오류 결과 저장.
        """
        print(f"[MeasureView] mark_session_failed : {error_msg}")

        session = get_db_session()
        try:
            ts = session.query(TestSession).get(self.test_session_id)
            ts.status = "failed"
            ts.error_message = error_msg
            ts.completed_at = datetime.now()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    def get_test_type_id_by_code(self, test_type_code: str) -> int:
        """
        test_type 테이블에서 진단구분에 맞는 id 를 조회.
        
        :param self: 설명
        :param test_type_code: 진단구분 
        :type test_type_code: str
        :return: 진단구분 id
        :rtype: int
        """
        session = get_db_session()
        try:
            test_type = (
                session.query(TestType)
                .filter(TestType.code == test_type_code)
                .first()
            )
            if not test_type:
                raise Exception(f"Unknown test_type_code: {test_type_code}")
            return test_type.id
        finally:
            session.close()            
        

    def _load_current_json(self):
        """
        TestInofView 에서 입력한 정보(json) 값을 다시 로드. 
        """
        try:
            if not os.path.exists(self.current_json_path):
                print("[MeasureView] current.json not found")
                return {}

            with open(self.current_json_path, "r") as f:
                return json.load(f)

        except Exception as e:
            print(f"[MeasureView] current.json load error: {e}")
            return {}


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