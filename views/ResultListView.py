import os

from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)
from repositories.result_repository import patient_result_repo, calibration_result_repo, qc_result_repo
from models.database_models import CalibrationItemTypeEnum, ControlTypeEnum

class ResultListView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_result_category = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_type = "patient"  # 기본값: patient, calibration, qc
        self.selected_rows = set()  # 선택된 행을 추적하기 위한 세트
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
        self.pushButton_RListExport.clicked.connect(self.on_rlistExport_button_clicked)
        self.pushButton_RListDelete.clicked.connect(self.on_rlistDelete_button_clicked)

        # 테이블 설정 (textBrowser 대신 테이블 사용)
        self.setup_table()
        
        # 다중 선택을 위한 선택된 행 집합 초기화
        self.selected_rows = set()

        # 초기 날짜와 시간 설정
        self.update_date_time()
        self.update_battery_status()

    def setup_table(self):
        """기존 textBrowser를 QTableWidget으로 교체"""
        if hasattr(self, 'textBrowser'):
            # textBrowser 숨기기
            self.textBrowser.hide()
            
            # 새 테이블 위젯 생성 (textBrowser와 같은 위치에)
            self.table_widget = QTableWidget(self)
            self.table_widget.setGeometry(42, 93, 793, 483)  # textBrowser와 같은 크기
            # 테이블 설정
            self.table_widget.setAlternatingRowColors(True)  # 교대 색상 활성화 - 커스텀 색상 사용
            self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table_widget.setSelectionMode(QAbstractItemView.NoSelection)  # Qt 기본 선택 완전히 비활성화
            self.table_widget.verticalHeader().setVisible(False)
            
            # 헤더 초기 설정 - 깜빡임 방지
            header = self.table_widget.horizontalHeader()
            header.setStretchLastSection(False)  # 초기에는 false로 설정
            
            # 행 클릭 이벤트 연결 (itemSelectionChanged 대신 itemClicked 사용)
            self.table_widget.itemClicked.connect(self.on_table_item_clicked)
            
            # 헤더 스타일 설정
            self.table_widget.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    gridline-color: #d0d0d0;
                    font-family: Pretendard;
                    font-size: 12px;
                    selection-background-color: transparent;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #e0e0e0;
                }
                QTableWidget::item:selected {
                    background-color: transparent;
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
        self.clear_table_selection()  # 결과 타입 변경 시 선택 초기화
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
            # 데이터 로드 시 선택 상태 초기화
            self.selected_rows.clear()
            
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
        if hasattr(self, 'table_widget') and hasattr(self, 'selected_rows'):
            # 선택된 행들의 스타일을 기본으로 되돌리기
            for row in self.selected_rows:
                self.update_row_style(row, False)
            
            # 선택된 행 집합 초기화
            self.selected_rows.clear()
            print(f"테이블 선택 완전히 초기화됨")

    def update_row_style(self, row, selected):
        """행의 스타일을 업데이트 (프로그래밍 방식으로 직접 색상 설정)"""
        if not hasattr(self, 'table_widget'):
            return
            
        # 프로그래밍 방식으로 직접 색상 설정
        if selected:
            bg_color = QColor("#1976d2")  # 진한 파란색
            text_color = QColor("#ff0000")  # 흰색 텍스트
        else:
            # 기본 행 스타일
            if row % 2 == 0:
                bg_color = QColor("#ffffff")  # 흰색
            else:
                bg_color = QColor("#f5f5f5")  # 연한 회색
            text_color = QColor("#000000")  # 검은색 텍스트
        
        # 해당 행의 모든 셀에 색상 적용
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(row, col)
            if item:
                item.setBackground(bg_color)
                item.setForeground(text_color)

    def on_table_item_clicked(self, item):
        """테이블 항목 클릭 시 토글 선택 처리"""
        print(f"테이블 항목 클릭됨: 행 {item.row() + 1}, 열 {item.column() + 1}")
        
        if not hasattr(self, 'selected_rows'):
            print("selected_rows 초기화")
            self.selected_rows = set()
            
        row = item.row()
        
        # 행 선택 토글 (클릭 피드백 없이 즉시 선택 상태 변경)
        if row in self.selected_rows:
            # 이미 선택된 행이면 선택 해제
            self.selected_rows.remove(row)
            self.update_row_style(row, False)
            print(f"행 {row + 1} 선택 해제됨")
        else:
            # 선택되지 않은 행이면 선택
            self.selected_rows.add(row)
            self.update_row_style(row, True)
            print(f"행 {row + 1} 선택됨")
        
        # 현재 선택된 행들의 정보 출력
        self.print_selected_rows_info()
        
        # 선택 상태 업데이트 (UI에 선택된 항목 수 표시 등)
        self.update_selection_status()
    
    def update_selection_status(self):
        """선택 상태 정보 업데이트"""
        count = len(self.selected_rows)
        if count > 0:
            print(f"현재 {count}개 항목이 선택되어 있습니다.")
            # UI에 선택된 항목 수를 표시할 라벨이 있다면 업데이트
            # 예: if hasattr(self, 'label_selection_count'):
            #        self.label_selection_count.setText(f"선택됨: {count}개")
        else:
            print("선택된 항목이 없습니다.")
    
    def print_selected_rows_info(self):
        """선택된 행들의 정보 출력"""
        if not self.selected_rows:
            print("선택된 행이 없습니다.")
            return
            
        print(f"총 {len(self.selected_rows)}개 행이 선택됨:")
        for row in sorted(self.selected_rows):
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
                print(f"  - Row {row + 1}: {row_data[0]} | {row_data[3]} | {row_data[1]} | Result: {row_data[4]}")
            elif self.result_type == "calibration":
                print(f"  - Row {row + 1}: {row_data[0]} | {row_data[3]} | {row_data[1]} | Result: {row_data[4]}")
            elif self.result_type == "qc":
                print(f"  - Row {row + 1}: {row_data[0]} | {row_data[3]} | {row_data[1]} | Result: {row_data[4]}")
            else:
                print(f"  - Row {row + 1}: {' | '.join(row_data)}")
    
    def get_selected_rows_data(self):
        """선택된 행들의 데이터를 반환"""
        if not hasattr(self, 'selected_rows') or not self.selected_rows:
            return []
            
        selected_data = []
        for row in sorted(self.selected_rows):
            row_data = {}
            headers = []
            
            # 헤더 정보 가져오기
            for col in range(self.table_widget.columnCount()):
                header_item = self.table_widget.horizontalHeaderItem(col)
                if header_item:
                    headers.append(header_item.text())
                else:
                    headers.append(f"Column_{col}")
            
            # 행 데이터 가져오기
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                value = item.text() if item else ""
                row_data[headers[col]] = value
            
            selected_data.append({
                'row_number': row,
                'data': row_data
            })
        
        return selected_data

    def showEvent(self, event):
        """화면이 표시될 때 호출"""
        super().showEvent(event)
        # 날짜/시간 및 배터리 업데이트 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
        print("ResultListView가 표시되었습니다.")
    
    def hideEvent(self, event):
        """화면이 숨김될 때 호출"""
        super().hideEvent(event)
        # 날짜/시간 및 배터리 업데이트 중지
        stop_date_time_update(self)
        stop_battery_update(self)
        print("ResultListView가 숨겨졌습니다.")
    
    def closeEvent(self, event):
        """화면이 닫힐 때 호출"""
        stop_date_time_update(self)
        stop_battery_update(self)
        super().closeEvent(event)

    def on_rlistHome_button_clicked(self):
        """SELECT ALL 버튼 - 모든 행 선택/해제 토글"""
        if not hasattr(self, 'table_widget') or not hasattr(self, 'selected_rows'):
            return
            
        total_rows = self.table_widget.rowCount()
        if total_rows == 0:
            return
        
        # 현재 모든 행이 선택되어 있는지 확인
        all_selected = len(self.selected_rows) == total_rows
        
        if all_selected:
            # 모든 행이 선택되어 있으면 모두 해제
            self.clear_table_selection()
            print("모든 행 선택 해제됨")
        else:
            # 일부만 선택되어 있거나 아무것도 선택되지 않았으면 모든 행 선택
            self.selected_rows.clear()
            for row in range(total_rows):
                self.selected_rows.add(row)
                self.update_row_style(row, True)
            print(f"모든 행({total_rows}개) 선택됨")
        
        self.update_selection_status()

    def on_rlistSend_button_clicked(self):
        print("ResultListView: Send 버튼이 클릭되었습니다.")
        selected_data = self.get_selected_rows_data()
        
        if not selected_data:
            print("전송할 데이터가 선택되지 않았습니다.")
            return
        
        print(f"전송할 데이터 {len(selected_data)}개:")
        for item in selected_data:
            print(f"  Row {item['row_number'] + 1}: {item['data']}")
        
        # 여기에 실제 전송 로직을 추가할 수 있습니다
        # self.send_data(selected_data)

    def on_rlistExport_button_clicked(self):
        print("ResultListView: Export 버튼이 클릭되었습니다.")
        selected_data = self.get_selected_rows_data()
        
        if not selected_data:
            print("내보낼 데이터가 선택되지 않았습니다.")
            return
        
        print(f"내보낼 데이터 {len(selected_data)}개:")
        for item in selected_data:
            print(f"  Row {item['row_number'] + 1}: {item['data']}")
        
        # 여기에 실제 데이터 내보내기 로직을 추가할 수 있습니다
        # self.export_data(selected_data)

    def on_rlistDelete_button_clicked(self):
        print("ResultListView: Delete 버튼이 클릭되었습니다.")
        selected_data = self.get_selected_rows_data()
        
        if not selected_data:
            print("삭제할 데이터가 선택되지 않았습니다.")
            return
        
        print(f"삭제할 데이터 {len(selected_data)}개:")
        for item in selected_data:
            print(f"  Row {item['row_number'] + 1}: {item['data']}")
        
        # 여기에 실제 삭제 로직을 추가할 수 있습니다
        # self.delete_data(selected_data)

    def on_back_button_clicked(self):
        """뒤로가기 버튼 - Result Category View로 이동"""
        self.clear_table_selection()  # 페이지 전환 시 선택 초기화
        self.switch_to_result_category.emit()

    def update_date_time(self):
        update_date_time(self)

    def update_battery_status(self):
        """배터리 상태 업데이트"""
        update_battery_status(self)
