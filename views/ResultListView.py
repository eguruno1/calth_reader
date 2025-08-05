import os

from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update
from repositories.result_repository import patient_result_repo, calibration_result_repo, qc_result_repo
from models.database_models import CalibrationItemTypeEnum, ControlTypeEnum

class ResultListView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_result_category = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_type = "patient"  # 기본값: patient, calibration, qc
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'ResultListViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Review', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 뒤로 가기 버튼 연결
        self.pushButton_ResultListBackArrow.clicked.connect(self.on_back_button_clicked)

        # 버튼들 연결
        self.pushButton_RListHome.clicked.connect(self.on_rlistHome_button_clicked)
        self.pushButton_RListSend.clicked.connect(self.on_rlistSend_button_clicked)
        self.pushButton_RListDelete.clicked.connect(self.on_rlistDelete_button_clicked)

        # 테이블 설정 (textBrowser 대신 테이블 사용)
        self.setup_table()

        # 초기 날짜와 시간 설정
        self.update_date_time()

    def setup_table(self):
        """기존 textBrowser를 QTableWidget으로 교체"""
        if hasattr(self, 'textBrowser'):
            # textBrowser 숨기기
            self.textBrowser.hide()
            
            # 새 테이블 위젯 생성 (textBrowser와 같은 위치에)
            self.table_widget = QTableWidget(self)
            self.table_widget.setGeometry(42, 138, 793, 438)  # textBrowser와 같은 크기
            
            # 테이블 설정
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table_widget.verticalHeader().setVisible(False)
            
            # 헤더 초기 설정 - 깜빡임 방지
            header = self.table_widget.horizontalHeader()
            header.setStretchLastSection(False)  # 초기에는 false로 설정
            
            # 행 선택 이벤트 연결
            self.table_widget.itemSelectionChanged.connect(self.on_table_selection_changed)
            
            # 헤더 스타일 설정
            self.table_widget.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    gridline-color: #d0d0d0;
                    font-family: Pretendard;
                    font-size: 12px;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #e0e0e0;
                }
                QTableWidget::item:selected {
                    background-color: #e3f2fd;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    padding: 8px;
                    border: 1px solid #d0d0d0;
                    font-weight: bold;
                    font-family: Pretendard;
                    font-size: 14px;
                }
            """)
            
            self.table_widget.show()

    def set_result_type(self, result_type: str):
        """결과 타입 설정 및 데이터 로드"""
        self.result_type = result_type
        self.load_data()
        self.update_title()

    def update_title(self):
        """타이틀 업데이트"""
        title_map = {
            "patient": "PATIENT RESULTS",
            "calibration": "CALIBRATION RESULTS", 
            "qc": "QC RESULTS"
        }
        # UI에서 title 라벨을 찾아서 업데이트
        title = title_map.get(self.result_type, "TEST RESULT")
        
        # 가능한 title 라벨들을 찾아서 업데이트
        for label_name in ['label_Title', 'label_title', 'label_TitleText']:
            if hasattr(self, label_name):
                getattr(self, label_name).setText(title)
                break

    def load_data(self):
        """결과 타입에 따라 데이터 로드"""
        try:
            if self.result_type == "patient":
                self.load_patient_results()
            elif self.result_type == "calibration":
                self.load_calibration_results()
            elif self.result_type == "qc":
                self.load_qc_results()
        except Exception as e:
            print(f"데이터 로드 오류: {e}")

    def load_patient_results(self):
        """환자 결과 데이터 로드"""
        results = patient_result_repo.get_all()
        self.setup_patient_table(results)

    def load_calibration_results(self):
        """교정 결과 데이터 로드"""
        results = calibration_result_repo.get_all()
        self.setup_calibration_table(results)

    def load_qc_results(self):
        """QC 결과 데이터 로드"""
        results = qc_result_repo.get_all()
        self.setup_qc_table(results)

    def setup_patient_table(self, results):
        """Patient Results 테이블 설정"""
        if not hasattr(self, 'table_widget'):
            return
            
        # 컬럼 설정
        headers = ['Item', 'Date', 'Operator ID', 'Patient ID', 'Result', 'Lot. No.', 'Control']
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 헤더 설정을 먼저 하여 깜빡임 방지
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(False)  # 먼저 false로 설정
        
        # 행 설정
        self.table_widget.setRowCount(len(results))
        
        # 데이터 입력
        for row, result in enumerate(results):
            self.table_widget.setItem(row, 0, QTableWidgetItem(result.item))
            self.table_widget.setItem(row, 1, QTableWidgetItem(result.test_date.strftime('%Y-%m-%d %H:%M')))
            self.table_widget.setItem(row, 2, QTableWidgetItem(result.operator_id))
            self.table_widget.setItem(row, 3, QTableWidgetItem(result.patient_id))
            self.table_widget.setItem(row, 4, QTableWidgetItem(self.format_result_data(result.result_data, result.item)))
            self.table_widget.setItem(row, 5, QTableWidgetItem(result.lot_number))
            self.table_widget.setItem(row, 6, QTableWidgetItem(result.control or 'N/A'))
        
        # 컬럼 너비를 컨텐츠에 맞게 조정한 후, 마지막 컬럼만 확장
        self.table_widget.resizeColumnsToContents()
        header.setStretchLastSection(True)

    def setup_calibration_table(self, results):
        """Calibration Results 테이블 설정"""
        if not hasattr(self, 'table_widget'):
            return
            
        # 컬럼 설정
        headers = ['Item', 'Date', 'Operator ID', 'Device ID', 'Result', 'Lot. No.', 'Control']
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 헤더 설정을 먼저 하여 깜빡임 방지
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(False)  # 먼저 false로 설정
        
        # 행 설정
        self.table_widget.setRowCount(len(results))
        
        # 데이터 입력
        for row, result in enumerate(results):
            self.table_widget.setItem(row, 0, QTableWidgetItem(result.item_type.value))
            self.table_widget.setItem(row, 1, QTableWidgetItem(result.test_date.strftime('%Y-%m-%d %H:%M')))
            self.table_widget.setItem(row, 2, QTableWidgetItem(result.operator_id))
            self.table_widget.setItem(row, 3, QTableWidgetItem(result.device_id))
            self.table_widget.setItem(row, 4, QTableWidgetItem(self.format_calibration_result_data(result.result_data, result.item_type)))
            self.table_widget.setItem(row, 5, QTableWidgetItem(result.lot_number))
            self.table_widget.setItem(row, 6, QTableWidgetItem(result.control or 'N/A'))
        
        # 컬럼 너비를 컨텐츠에 맞게 조정한 후, 마지막 컬럼만 확장
        self.table_widget.resizeColumnsToContents()
        header.setStretchLastSection(True)

    def setup_qc_table(self, results):
        """QC Results 테이블 설정"""
        if not hasattr(self, 'table_widget'):
            return
            
        # 컬럼 설정
        headers = ['Item', 'Date', 'Operator ID', 'Control Type', 'Result', 'Lot. No.', 'Control']
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 헤더 설정을 먼저 하여 깜빡임 방지
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(False)  # 먼저 false로 설정
        
        # 행 설정
        self.table_widget.setRowCount(len(results))
        
        # 데이터 입력
        for row, result in enumerate(results):
            self.table_widget.setItem(row, 0, QTableWidgetItem(result.item))
            self.table_widget.setItem(row, 1, QTableWidgetItem(result.test_date.strftime('%Y-%m-%d %H:%M')))
            self.table_widget.setItem(row, 2, QTableWidgetItem(result.operator_id))
            self.table_widget.setItem(row, 3, QTableWidgetItem(f"{result.control_type.value} Control"))
            self.table_widget.setItem(row, 4, QTableWidgetItem(self.format_result_data(result.result_data, result.item)))
            self.table_widget.setItem(row, 5, QTableWidgetItem(result.lot_number))
            self.table_widget.setItem(row, 6, QTableWidgetItem(result.control or 'N/A'))
        
        # 컬럼 너비를 컨텐츠에 맞게 조정한 후, 마지막 컬럼만 확장
        self.table_widget.resizeColumnsToContents()
        header.setStretchLastSection(True)

    def format_result_data(self, result_data, item):
        """결과 데이터를 읽기 쉬운 형태로 포맷"""
        if not result_data:
            return "No result data"
        
        if item.lower() == "influenza":
            # Influenza A/B 결과 처리
            parts = []
            if "influenza_a" in result_data:
                parts.append(f"A: {result_data['influenza_a']}")
            if "influenza_b" in result_data:
                parts.append(f"B: {result_data['influenza_b']}")
            return ", ".join(parts) if parts else str(result_data)
        elif item.lower() == "covid-19":
            # COVID-19 결과 처리
            if "covid19" in result_data:
                return result_data['covid19']
            return str(result_data)
        else:
            # 기타 결과
            return str(result_data)

    def format_calibration_result_data(self, result_data, item_type):
        """교정 결과 데이터를 읽기 쉬운 형태로 포맷"""
        if not result_data:
            return "No result data"
        
        if item_type == CalibrationItemTypeEnum.TYPE1:
            # Type1은 result 값
            if "result" in result_data:
                result_str = result_data['result']
                if "value" in result_data:
                    result_str += f" ({result_data['value']})"
                return result_str
            return str(result_data)
        elif item_type == CalibrationItemTypeEnum.TYPE2:
            # Type2는 T1, T2 값
            parts = []
            if "t1" in result_data:
                parts.append(f"T1: {result_data['t1']}")
            if "t2" in result_data:
                parts.append(f"T2: {result_data['t2']}")
            return ", ".join(parts) if parts else str(result_data)
        else:
            return str(result_data)

    def display_content(self, content):
        """컨텐츠를 화면에 표시 (호환성을 위해 유지)"""
        # 테이블 방식으로 변경되어 더 이상 사용하지 않음
        pass

    def clear_table_selection(self):
        """테이블 선택 해제"""
        if hasattr(self, 'table_widget'):
            self.table_widget.clearSelection()

    def hideEvent(self, event):
        super().hideEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        # 화면이 표시될 때 데이터 새로고침
        QTimer.singleShot(200, self.load_data)
        # 페이지 재진입 시 테이블 선택 초기화
        QTimer.singleShot(300, self.clear_table_selection)

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_rlistHome_button_clicked(self):
        #print("ResultListView: HOME 버튼이 클릭되었습니다.")
        self.switch_to_home.emit()

    def on_rlistSend_button_clicked(self):
        print("ResultListView: Send 버튼이 클릭되었습니다.")
        #self.switch_to_home.emit()

    def on_rlistDelete_button_clicked(self):
        print("ResultListView: Delete 버튼이 클릭되었습니다.")
        #self.switch_to_home.emit()

    def on_back_button_clicked(self):
        """뒤로가기 버튼 - Result Category View로 이동"""
        self.switch_to_result_category.emit()

    def update_date_time(self):
        update_date_time(self)

    def on_table_selection_changed(self):
        """테이블 선택 변경 이벤트 처리"""
        if not hasattr(self, 'table_widget'):
            return
            
        selected_ranges = self.table_widget.selectedRanges()
        if not selected_ranges:
            return
            
        # 선택된 행 번호
        row = selected_ranges[0].topRow()
        
        # 행 데이터 수집
        row_data = []
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(row, col)
            if item:
                row_data.append(item.text())
            else:
                row_data.append("")
        
        # 결과 타입별 출력 형식
        if self.result_type == "patient":
            print(f"[Patient Result 선택] Row {row + 1}: {row_data[0]} | {row_data[3]} | {row_data[1]} | Result: {row_data[4]}")
        elif self.result_type == "calibration":
            print(f"[Calibration Result 선택] Row {row + 1}: {row_data[0]} | {row_data[3]} | {row_data[1]} | Result: {row_data[4]}")
        elif self.result_type == "qc":
            print(f"[QC Result 선택] Row {row + 1}: {row_data[0]} | {row_data[3]} | {row_data[1]} | Result: {row_data[4]}")
        else:
            print(f"[선택된 행] Row {row + 1}: {' | '.join(row_data)}")
