import os

from PyQt5.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QDialog, QMessageBox)
from PyQt5.QtCore import pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5 import uic

from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                        update_battery_status, start_battery_update, stop_battery_update)
from services.user_service import user_service

class ManageOperatorView(QMainWindow):
    switch_to_settings        = pyqtSignal()
    switch_to_home            = pyqtSignal()
    switch_to_account_add     = pyqtSignal()  # 사용자추가 화면으로 전환 (컨텍스트 포함)
    switch_to_account_edit    = pyqtSignal(str)  # ID 변경을 위해 user_id 전달
    switch_to_account_pw_edit = pyqtSignal(str)  # PW 변경을 위해 user_id 전달

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_rows = set()  # 선택된 행을 추적하기 위한 세트
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'ManageOperatorViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Settings', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 뒤로 가기 버튼 연결
        self.pushButton_ResultListBackArrow.clicked.connect(self.on_back_button_clicked)

        # 새로운 5개 버튼들 연결
        self.pushButton_CreateID.clicked.connect(self.on_create_id_button_clicked)
        self.pushButton_EditID.clicked.connect(self.on_edit_id_button_clicked)
        self.pushButton_EditPW.clicked.connect(self.on_edit_pw_button_clicked)
        self.pushButton_DeleteID.clicked.connect(self.on_delete_id_button_clicked)
        self.pushButton_AutoLogout.clicked.connect(self.on_auto_logout_button_clicked)

        # 테이블 설정 (textBrowser 대신 테이블 사용)
        self.setup_table()
        
        # 다중 선택을 위한 선택된 행 집합 초기화
        self.selected_rows = set()

    def showEvent(self, event):
        super().showEvent(event)
        print("🟢 showEvent 진입")
        
        # 초기 날짜와 시간 설정
        self.update_date_time()
        self.update_battery_status()

        # 초기 데이터 로드
        self.load_user_data()

        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
        
    def hideEvent(self, event):
        super().hideEvent(event)

        stop_date_time_update(self)
        stop_battery_update(self)

        # 페이지 벗어날 때 선택 상태 즉시 초기화
        self.clear_table_selection()
        """
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))
        # 화면이 표시될 때 데이터 새로고침
        QTimer.singleShot(200, self.load_user_data)
        """
        
    def closeEvent(self, event):
        stop_date_time_update(self)
        stop_battery_update(self)
        super().closeEvent(event)    

    def setup_table(self):
        """사용자 목록 테이블 생성"""
        print("🔍 setup_table() 호출됨")

        # textBrowser가 있으면 숨기기 (있을 때만)
        if hasattr(self, 'textBrowser'):
            self.textBrowser.hide()

        # ✅ 무조건 테이블 생성
        self.table_widget = QTableWidget(self)
        self.table_widget.setGeometry(42, 93, 793, 483)

        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_widget.verticalHeader().setVisible(False)

        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(False)

        self.table_widget.itemClicked.connect(self.on_table_item_clicked)

        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #d0d0d0;
                font-family: Pretendard;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
            }
        """)

        self.table_widget.show()

    def load_user_data(self):
        """사용자 데이터 로드"""
        print("🔍 load_user_data() 호출됨")

        try:
            # 데이터 로드 시 선택 상태 초기화
            self.selected_rows.clear()
            
            # 모든 사용자 데이터 가져오기
            # users = user_service.get_all_users()
            users = user_service.get_available_users()
            print(f"👥 조회된 사용자 수: {len(users)}")
            self.setup_user_table(users)

        except Exception as e:
            print(f"사용자 데이터 로드 오류: {e}")

    def setup_user_table(self, users):
        """사용자 테이블 설정 (dict 기반)"""
        print(f"📊 setup_user_table() rows = {len(users)}")

        if not hasattr(self, 'table_widget'):
            return
            
        # 컬럼 설정
        headers = ['User ID', 'User Name', 'Role', 'Created Date', 'Last Login', 'Status']
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 헤더 설정을 먼저 하여 깜빡임 방지
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(False)  # 먼저 false로 설정
        
        # 행 설정
        self.table_widget.setRowCount(len(users))
        
        # 데이터 입력
        for row, user in enumerate(users):
            self.table_widget.setItem(row, 0, QTableWidgetItem(user.get("id", "")))
            self.table_widget.setItem(row, 1, QTableWidgetItem(user.get("name", "N/A")))
            self.table_widget.setItem(row, 2, QTableWidgetItem(user.get("role", "Operator")))

            created_at = user.get("created_at")
            last_login = user.get("last_login")

            self.table_widget.setItem(
                row, 3,
                QTableWidgetItem(created_at.strftime('%Y-%m-%d %H:%M') if created_at else "N/A")
            )

            self.table_widget.setItem(
                row, 4,
                QTableWidgetItem(last_login.strftime('%Y-%m-%d %H:%M') if last_login else "Never")
            )

            self.table_widget.setItem(
                row, 5,
                QTableWidgetItem("Active" if user.get("is_active", True) else "Inactive")
            ) # End for
        
        # 컬럼 너비를 컨텐츠에 맞게 조정한 후, 마지막 컬럼만 확장
        self.table_widget.resizeColumnsToContents()
        header.setStretchLastSection(True)

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
            text_color = QColor("#ff0000")  # 빨간색 텍스트
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
            print(f"현재 {count}개 사용자가 선택되어 있습니다.")
        else:
            print("선택된 사용자가 없습니다.")
    
    def print_selected_rows_info(self):
        """선택된 행들의 정보 출력"""
        if not self.selected_rows:
            print("선택된 행이 없습니다.")
            return
            
        print(f"총 {len(self.selected_rows)}개 사용자가 선택됨:")
        for row in sorted(self.selected_rows):
            # 행 데이터 수집
            row_data = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            
            print(f"  - Row {row + 1}: {row_data[0]} | {row_data[1]} | {row_data[2]} | {row_data[5]}")
    
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

    #==========================================
    # --- 화면 이동 ---
    #==========================================
    def on_create_id_button_clicked(self):
        """CREATE ID 버튼 - 새 사용자 생성"""
        print("ManageOperatorView: Create ID 버튼이 클릭되었습니다.")
        
        # 여기에 새 사용자 생성 다이얼로그나 페이지를 열 수 있습니다
        # self.open_create_user_dialog()
        self.switch_to_account_add.emit()
        """
        self.account_add_view = AccountAddView()
        self.account_add_view.switch_to_manage_operator.connect(
            self.on_return_from_account_add
        )

        self.account_add_view.show()
        self.close()
        """

    def on_return_from_account_add(self):
        """사용자 추가후 화면 Refresh"""
        self.show()
        self.load_user_data()
    

    def on_edit_id_button_clicked(self):
        """EDIT ID 버튼 - 선택된 사용자 ID 편집"""
        print("ManageOperatorView: Edit ID 버튼이 클릭되었습니다.")
        selected_rows = self.get_selected_rows_data()
        
        # 1️⃣ 선택 여부 체크
        if not selected_rows:
            QMessageBox.warning(
                self,
                "선택 필요",
                "먼저 사용자를 선택해주세요."
            )
            return

        # 2️⃣ 1명만 선택했는지 체크
        if len(selected_rows) != 1:
            QMessageBox.warning(
                self,
                "선택 오류",
                "한 명의 사용자만 선택해주세요."
            )
            return

        # 3️⃣ 선택된 사용자 데이터 추출
        selected_user = selected_rows[0]["data"]

        user_id = selected_user.get("User ID")

        if not user_id:
            QMessageBox.warning(
                self,
                "오류",
                "선택한 사용자 정보에 User ID가 없습니다."
            )
            return

        print(f"ID 편집할 사용자: {selected_user}")

        # 4️⃣ AppController 로 화면 전환 요청
        self.switch_to_account_edit.emit(user_id)

        # 여기에 사용자 ID 편집 다이얼로그나 페이지를 열 수 있습니다
        # self.open_edit_user_id_dialog(selected_data[0]['data'])

    def on_edit_pw_button_clicked(self):
        """EDIT PW 버튼 - 선택된 사용자 비밀번호 편집"""
        print("ManageOperatorView: Edit PW 버튼이 클릭되었습니다.")
        selected_rows = self.get_selected_rows_data()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "선택 필요",
                "먼저 사용자를 선택해주세요."
            )
            return

        if len(selected_rows) != 1:
            QMessageBox.warning(
                self,
                "선택 오류",
                "한 명의 사용자만 선택해주세요."
            )
            return

        user_data = selected_rows[0]["data"]
        user_id = user_data.get("User ID")

        if not user_id:
            QMessageBox.warning(
                self,
                "오류",
                "User ID 정보를 찾을 수 없습니다."
            )
            return

        self.switch_to_account_pw_edit.emit(user_id)
        
        # 여기에 사용자 비밀번호 변경 다이얼로그나 페이지를 열 수 있습니다
        # self.open_edit_user_password_dialog(selected_data[0]['data'])

    def on_delete_id_button_clicked(self):
        """DELETE ID 버튼 - 선택된 사용자 삭제"""
        print("ManageOperatorView: Delete ID 버튼이 클릭되었습니다.")
        selected_data = self.get_selected_rows_data()
        
        if not selected_data:
            print("삭제할 사용자가 선택되지 않았습니다.")
            return
        
        print(f"삭제할 사용자 {len(selected_data)}개:")
        for item in selected_data:
            print(f"  Row {item['row_number'] + 1}: {item['data']}")
        
        # 여기에 실제 삭제 로직을 추가할 수 있습니다
        # self.delete_users(selected_data)

    def on_auto_logout_button_clicked(self):
        """AUTO LOGOUT 버튼 - 자동 로그아웃 설정"""
        print("ManageOperatorView: Auto Logout 버튼이 클릭되었습니다.")
        
        # 여기에 자동 로그아웃 설정 다이얼로그나 페이지를 열 수 있습니다
        # self.open_auto_logout_settings_dialog()

    def on_back_button_clicked(self):
        """뒤로가기 버튼 - Settings View로 이동"""
        self.clear_table_selection()  # 페이지 전환 시 선택 초기화
        self.switch_to_settings.emit()

    #==========================================
    # --- 헤더 현재시간 & 배터리 상태 연결 ---
    #==========================================
    def update_date_time(self):
        update_date_time(self)

    def update_battery_status(self):
        """배터리 상태 업데이트"""
        update_battery_status(self)
