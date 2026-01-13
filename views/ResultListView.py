import os
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QWidget, QCheckBox, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal, Qt
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
from database.models import MeasurementResult


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
        self.pushButton_ResultListBackArrow.clicked.connect(
            self.on_back_button_clicked
        )

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
        self.table.verticalHeader().setVisible(False)

        # ★ FIX: row 클릭 처리
        self.table.cellClicked.connect(self.on_row_clicked)

        self.table.setStyleSheet("""
            QTableWidget { background: white; }
            QTableWidget::item { padding: 8px; }
        """)

    # ==========================================================
    # DATA LOAD
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
            "Check",              # 체크박스
            "Operator ID",
            "Patient ID",
            "Test Item",
            "Result"
        ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(results))

        # ▶ 헤더 텍스트 수동 설정 (색상 제어용)
        for col, text in enumerate(headers):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)

            # ★ FIX: Test Item 헤더 파란색
            if text == "Test Item":
                item.setForeground(QColor("#1976d2"))

            self.table.setHorizontalHeaderItem(col, item)

        # ▶ 헤더 체크박스
        header_check = QTableWidgetItem()
        header_check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        header_check.setCheckState(Qt.Unchecked)
        self.table.setHorizontalHeaderItem(0, header_check)

        for row, mr in enumerate(results):
            # ★ FIX: row 높이 (체크박스 잘림 방지)
            self.table.setRowHeight(row, 44)
            # ▶ Row 체크박스

            # ▶ Row 체크박스 (가운데 정렬)
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(
                lambda state, r=row: self._set_row_selected(r, state == Qt.Checked)
            )

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)

            self.table.setCellWidget(row, 0, container)

            operator_id = (
                mr.session.operator.user_id
                if mr.session and mr.session.operator else ""
            )

            patient_code = (
                mr.session.patient.patient_code
                if mr.session and mr.session.patient else ""
            )

            test_item = (
                mr.session.test_type.code
                if mr.session and mr.session.test_type else ""
            )

            result_text = self._format_result_data(mr.result_data)

            item_op = QTableWidgetItem(operator_id)
            item_op.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_op)

            item_patient = QTableWidgetItem(patient_code)
            item_patient.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_patient)

            item_test = QTableWidgetItem(test_item)
            item_test.setForeground(QColor("#d32f2f"))
            item_test.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_test)

            self.table.setItem(row, 4, QTableWidgetItem(result_text))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    # ==========================================================
    # RESULT FORMAT
    # ==========================================================
    def _format_result_data(self, result_data: dict) -> str:
        """
        measurement_results.result_data(JSONB)를
        Result 컬럼에 표시할 문자열로 변환한다.

        실제 DB 저장 구조 기준:
        {
            "timestamp": "...",
            "analysis_result": {
                "mode": 2 or 3,
                "metrics": {
                    "lines": [
                        { "label": "C|T|L1|L2|L3", ... }
                    ]
                },
                "positive": true | false,
                "line_count": 2 | 3
            }
        }
        """

        # ----------------------------------
        # 1. 기본 방어 로직
        # ----------------------------------
        if not result_data or not isinstance(result_data, dict):
            return "N/A"

        try:
            # ----------------------------------
            # 2. analysis_result 추출
            # ----------------------------------
            analysis = result_data.get("analysis_result")
            if not isinstance(analysis, dict):
                return "INVALID DATA"

            mode = analysis.get("mode")              # 2 or 3
            positive = analysis.get("positive")      # True / False
            line_count = analysis.get("line_count")  # 2 / 3

            # ----------------------------------
            # 3. metrics / lines 안전 추출
            # ----------------------------------
            metrics = analysis.get("metrics", {})
            lines = metrics.get("lines", [])

            if not isinstance(lines, list):
                lines = []

            # 라인 라벨만 추출 (label 키가 있는 경우만)
            labels = [
                line.get("label")
                for line in lines
                if isinstance(line, dict) and "label" in line
            ]

            label_str = "/".join(labels) if labels else "N/A"
            line_cnt_str = f"{line_count}" if line_count is not None else "?"

            # ----------------------------------
            # 4. 2라인 (COVID19)
            # ----------------------------------
            if mode == 2:
                if positive:
                    return f"POSITIVE (C/T) | Lines:{line_cnt_str}"
                else:
                    return f"NEGATIVE (C) | Lines:{line_cnt_str}"

            # ----------------------------------
            # 5. 3라인 (INFLUENZA)
            # ----------------------------------
            if mode == 3:
                if not labels:
                    return f"INVALID | Lines:{line_cnt_str}"

                if positive:
                    return f"POSITIVE ({label_str}) | Lines:{line_cnt_str}"
                else:
                    return f"NEGATIVE ({label_str}) | Lines:{line_cnt_str}"

            # ----------------------------------
            # 6. 알 수 없는 mode
            # ----------------------------------
            return f"UNKNOWN MODE ({mode})"

        except Exception as e:
            print(f"[ResultListView] result_data format error: {e}")
            return "Invalid Result"


    # ==========================================================
    # SELECTION / CHECKBOX
    # ==========================================================
    # ==========================================================
    # ROW / CHECKBOX SYNC
    # ==========================================================
    def on_item_clicked(self, item):
        row = item.row()

        if item.column() == 0:
            checked = item.checkState() == Qt.Checked
            self._set_row_selected(row, checked)

        elif row in self.selected_rows:
            self._set_row_selected(row, False)
        else:
            self._set_row_selected(row, True)

    def on_row_clicked(self, row, column):
        container = self.table.cellWidget(row, 0)
        if not container:
            return

        checkbox = container.findChild(QCheckBox)
        if checkbox:
            checkbox.setChecked(not checkbox.isChecked())            

    def _set_row_selected(self, row: int, selected: bool):
        checkbox = self.table.item(row, 0)
        if checkbox:
            checkbox.setCheckState(Qt.Checked if selected else Qt.Unchecked)

        if selected:
            self.selected_rows.add(row)
        else:
            self.selected_rows.discard(row)

        self._apply_row_style(row, selected)

    def _apply_row_style(self, row: int, selected: bool):
        for c in range(1, self.table.columnCount()):
            item = self.table.item(row, c)
            if not item:
                continue

            if selected:
                item.setBackground(QColor("#1976d2"))
                item.setForeground(QColor("white"))
            else:
                item.setBackground(QColor("white"))
                if c == 3:
                    item.setForeground(QColor("#d32f2f"))
                else:
                    item.setForeground(QColor("black"))

    def clear_selection(self):
        for row in list(self.selected_rows):
            self._set_row_selected(row, False)
        self.selected_rows.clear()

    # ==========================================================
    # BUTTONS
    # ==========================================================
    def on_select_all_clicked(self):
        select_all = len(self.selected_rows) != self.table.rowCount()
        for r in range(self.table.rowCount()):
            container = self.table.cellWidget(r, 0)
            if container:
                cb = container.findChild(QCheckBox)
                if cb:
                    cb.setChecked(select_all)

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
