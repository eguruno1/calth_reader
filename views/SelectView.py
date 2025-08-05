import os
import json

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore    import pyqtSignal, QTimer
from PyQt5           import uic

from views.Utils     import update_date_time, start_date_time_update, stop_date_time_update

class SelectView(QMainWindow):
    switch_to_home = pyqtSignal()
    switch_to_test_info = pyqtSignal(str)  # 테스트 유형을 전달하기 위한 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

        # JSON 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'SelectViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Home', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 뒤로 가기 버튼 연결
        self.pushButton_SelectBackArrow.clicked.connect(self.on_back_button_clicked)

        # 버튼들 연결
        self.pushButton_Covid19.clicked.connect(lambda: self.on_test_button_clicked("Covid-19"))
        self.pushButton_Influenza.clicked.connect(lambda: self.on_test_button_clicked("Influenza A & B"))
        self.pushButton_Cadiac.clicked.connect(lambda: self.on_test_button_clicked("Cardiac Troponin I"))

        # 초기 날짜와 시간 설정
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def on_test_button_clicked(self, test_type):
        self.update_json_file(test_type)
        self.switch_to_test_info.emit(test_type)

    def update_date_time(self):
        update_date_time(self)

    def update_json_file(self, test_type):
        try:
            with open(self.current_json_path, 'r+') as f:
                data = json.load(f)
                data['test_type1'] = test_type
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except Exception as e:
            print(f"JSON 파일 업데이트 중 오류 발생: {e}")
