import os
import json

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore    import QTimer, pyqtSignal, QDateTime
from PyQt5           import uic

from views.Utils     import update_date_time, start_date_time_update, stop_date_time_update

class HomeView(QMainWindow):
    switch_to_select     = pyqtSignal()
    switch_to_info       = pyqtSignal()
    switch_to_resultList = pyqtSignal()
    switch_to_operator   = pyqtSignal()
    switch_to_settings   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 프로젝트 루트 디렉토리
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'HomeViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # UI 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")   
        
        # 버튼 연결
        self.pushButton_Qualitative.clicked.connect(self.on_qualitative_button_clicked)
        self.pushButton_Quantitative.clicked.connect(self.on_quantitative_button_clicked)

        self.pushButton_Operator.clicked.connect(self.on_operator_button_clicked)
        self.pushButton_Settings.clicked.connect(self.on_settings_button_clicked)        
        self.pushButton_ResultList.clicked.connect(self.on_resultList_button_clicked)
        self.pushButton_Info.clicked.connect(self.on_info_button_clicked)

        # 날짜와 시간 표시
        self.update_date_time()

        # JSON 파일 경로 설정
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def update_date_time(self):
        current_datetime = QDateTime.currentDateTime()
        formatted_datetime = current_datetime.toString("yyyy-MM-dd  HH:mm")
        if hasattr(self, 'label_DateNClock'):
            self.label_DateNClock.setText(formatted_datetime)

        # 기존 타이머가 있다면 중지
        if hasattr(self, 'date_time_timer'):
            self.date_time_timer.stop()

        # 새 타이머 생성 및 시작
        self.date_time_timer = QTimer(self)
        self.date_time_timer.timeout.connect(self.update_date_time)
        self.date_time_timer.start(1000)  # 1초마다 업데이트

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def update_json_file(self, button_name):
        try:
            with open(self.current_json_path, 'r+') as f:
                data = json.load(f)
                data['test_type0'] = button_name
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"JSON 파일 업데이트 중 오류 발생: {e}")

    def on_qualitative_button_clicked(self):
        print("Qualitative 버튼이 클릭되었습니다.")
        self.update_json_file("Qualitative")
        self.switch_to_select.emit()

    def on_quantitative_button_clicked(self):
        print("Quantitative 버튼이 클릭되었습니다.")
        self.update_json_file("Quantitative")
        self.switch_to_select.emit()

    def on_operator_button_clicked(self):
        self.switch_to_operator.emit()

    def on_settings_button_clicked(self):
        self.switch_to_settings.emit()

    def on_info_button_clicked(self):
        self.switch_to_info.emit()

    def on_resultList_button_clicked(self):
        self.switch_to_resultList.emit()

    def update_date_time(self):
        update_date_time(self)
