import os
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5 import uic

# 공통 UI 유틸
from views.Utils import (
    update_date_time,
    start_date_time_update,
    stop_date_time_update,
    update_battery_status,
    start_battery_update,
    stop_battery_update
)

# DB (ResultView0 와 동일)
from database.connection import get_db_session
from database.models import (
    TestSession,
    MeasurementResult,
    TestType,
    User,
    Patient
)


class ResultListView(QMainWindow):
    """
    Result List View
    - patient / qc 결과를 동일 구조로 표시
    - ResultView0 와 동일한 DB 접근 구조 사용
    """

    switch_to_home = pyqtSignal()
    switch_to_result_category = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # patient | qc
        self.mode: str = "patient"

        # 선택된 행 인덱스
        self.selected_rows: set[int] = set()

        self._load_ui()
        self._init_ui()

    # ==========================================================
    # UI LOAD
    # ==========================================================
    def _load_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)

        ui_path = os.path.join(
            project_root,
            "ui", "Review", "ResultListViewWindow.ui"
        )

        if not os.path.exists(ui_path):
            raise FileNotFoundError(ui_path)

        uic.loadUi(ui_path, self)

    def _init_ui(self):
        # Navigation
        self.pushButton_ResultListBackArrow.clicked.connect(
            self.on_back_button_clicked
        )

        # Action buttons
        self.pushButton_RListHome.clicked.connect(
            self.on_select_all_clicked
        )
        self.pushButton_RListSend.clicked.connect(
            self.on_send_clicked
        )
        self.pushButton_RListExport.clicked.connect(
            self.on_export_clicked
        )
        self.pushButton_RListDelete.clicked.connect(
            self.on_delete_clicked
        )

        self._setup_table()

        self.update_date_time()
        self.update_battery_status()


    def set_result_type(self, result_type: str):
        """
        Controller 에서 호출되는 진입점
        patient / qc 모드에 따라 DB 조회 방식을 변경한다
        """
        print(f"[ResultListView] set_result_type: {result_type}")

        if result_type not in ("patient", "qc"):
            print(f"[ResultListView] Unknown result_type: {result_type}")
            return

        self.result_type = result_type

        # 기존 선택 상태 초기화
        self.clear_selection()

        # DB 재조회
        self.load_data()

        # 타이틀 갱신
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
    

    # ==========================================================
    # TABLE
    # ==========================================================
    def _setup_table(self):
        self.textBrowser.hide()

        self.table = QTableWidget(self)
        self.table.setGeometry(42, 93, 793, 483)

        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)

        self.table.itemClicked.connect(self.on_item_clicked)

        self.table.setStyleSheet("""
            QTableWidget { background: white; }
            QTableWidget::item { padding: 8px; }
        """)      

    # ==========================================================
    # MODE
    # ==========================================================
    def set_mode(self, mode: str):
        """
        patient / qc 전환
        """
        self.mode = mode
        self.clear_selection()
        self.load_data()

    # ==========================================================
    # DATA LOAD (ResultView0 구조와 동일)
    # ==========================================================
    def load_data(self):
        session = get_db_session()

        try:
            results: List[MeasurementResult] = (
                session.query(MeasurementResult)
                .order_by(MeasurementResult.measured_at.desc())
                .all()
            )

            self._populate_table(results)

        finally:
            session.close()

    def _populate_table(self, results: List[MeasurementResult]):
        headers = [
            "Test Item",
            "Date",
            "Operator ID",
            "Patient ID",
            "Result"
        ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self._apply_header_style()
        self.table.setRowCount(len(results))

        for row, mr in enumerate(results):
            # Test Item
            test_item = (
                mr.session.test_type.code
                if mr.session and mr.session.test_type else ""
            )

            # Date
            date_text = (
                mr.measured_at.strftime("%Y-%m-%d %H:%M")
                if mr.measured_at else ""
            )

            # Operator ID
            operator_id = (
                mr.session.operator.user_id
                if mr.session and mr.session.operator else ""
            )

            # Patient Code
            patient_code = (
                mr.session.patient.patient_code
                if mr.session and mr.session.patient else ""
            )

            # Result
            result_text = self._format_result_data(mr.result_data)

            #self.table.setItem(row, 0, QTableWidgetItem(test_item))
            # Test Item (붉은색)
            item_test = QTableWidgetItem(test_item)
            item_test.setForeground(QColor("red"))
            item_test.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_test)

            item_date = QTableWidgetItem(date_text)
            item_date.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_date)

            item_op = QTableWidgetItem(operator_id)
            item_op.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_op)

            item_patient = QTableWidgetItem(patient_code)
            item_patient.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_patient)

            self.table.setItem(row, 4, QTableWidgetItem(result_text))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)


    def _format_result_data(self, result_data: dict) -> str:
        """
        result_data(JSONB)를 Result 컬럼에 표시할 문자열로 변환
        - 2라인 / 3라인 공통 처리
        포맷 예)
        {
            "timestamp": "...",
            "analysis_result": {
                "mode": 2 or 3,
                "metrics": {
                    "lines": [
                        { "label": "...", "confidence": ... }
                    ]
                },
                "positive": true,
                "line_count": 2 or 3
            }
        }
        """
        if not result_data:
            return "N/A"

        try:
            analysis = result_data.get("analysis_result", {})
            mode = analysis.get("mode")
            positive = analysis.get("positive")
            metrics = analysis.get("metrics", {})
            lines = metrics.get("lines", [])

            # 라인 라벨 추출
            labels = [line.get("label") for line in lines if "label" in line]

            # -------------------------
            # 2라인 (COVID19)
            # -------------------------
            if mode == 2:
                if positive:
                    return "POSITIVE (C/T)"
                else:
                    return "NEGATIVE (C)"

            # -------------------------
            # 3라인 (INFLUENZA)
            # -------------------------
            if mode == 3:
                if not labels:
                    return "INVALID"

                label_str = "/".join(labels)

                if positive:
                    return f"POSITIVE ({label_str})"
                else:
                    return f"NEGATIVE ({label_str})"

        except Exception as e:
            print(f"[ResultListView] result_data format error: {e}")
            return "Invalid Result"
    

    def _apply_header_style(self):
        """
        Test Item 헤더 색상 파란색 적용
        """
        header = self.table.horizontalHeader()

        for col in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(col)
            if not item:
                continue

            if item.text() == "Test Item":
                item.setForeground(Qt.blue)

    # ==========================================================
    # SELECTION
    # ==========================================================
    def on_item_clicked(self, item):
        row = item.row()
        if row in self.selected_rows:
            self.selected_rows.remove(row)
            self._set_row_style(row, False)
        else:
            self.selected_rows.add(row)
            self._set_row_style(row, True)

    def _set_row_style(self, row: int, selected: bool):
        """
        행 선택/해제 시 스타일 적용
        - 선택됨  : 모든 컬럼 흰색 텍스트
        - 선택해제 : Test Item 컬럼은 붉은색 유지
        """

        SELECT_BG = QColor("#1976d2")
        NORMAL_BG = QColor("#ffffff")

        TEST_ITEM_RED = QColor("#d32f2f")
        NORMAL_TEXT = QColor("#000000")
        SELECT_TEXT = QColor("#ffffff")

        for c in range(self.table.columnCount()):
            item = self.table.item(row, c)
            if not item:
                continue

            if selected:
                # ▶ 선택 상태
                item.setBackground(SELECT_BG)
                item.setForeground(SELECT_TEXT)
            else:
                # ▶ 선택 해제 상태
                item.setBackground(NORMAL_BG)

                if c == 0:  # Test Item 컬럼
                    item.setForeground(TEST_ITEM_RED)
                else:
                    item.setForeground(NORMAL_TEXT)


    def clear_selection(self):
        for row in self.selected_rows:
            self._set_row_style(row, False)
        self.selected_rows.clear()

    # ==========================================================
    # BUTTON HANDLERS
    # ==========================================================
    def on_select_all_clicked(self):
        if len(self.selected_rows) == self.table.rowCount():
            self.clear_selection()
            return

        self.selected_rows.clear()
        for r in range(self.table.rowCount()):
            self.selected_rows.add(r)
            self._set_row_style(r, True)

    def on_send_clicked(self):
        print("SEND:", self.selected_rows)

    def on_export_clicked(self):
        print("EXPORT:", self.selected_rows)

    def on_delete_clicked(self):
        print("DELETE:", self.selected_rows)

    def on_back_button_clicked(self):
        self.clear_selection()
        self.switch_to_result_category.emit()

    # ==========================================================
    # DATE / BATTERY
    # ==========================================================
    def showEvent(self, event):
        super().showEvent(event)
        start_date_time_update(self)
        start_battery_update(self)

    def hideEvent(self, event):
        super().hideEvent(event)
        stop_date_time_update(self)
        stop_battery_update(self)

    def update_date_time(self):
        update_date_time(self)

    def update_battery_status(self):
        update_battery_status(self)
