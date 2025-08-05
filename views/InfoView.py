import json
import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore    import pyqtSignal, QTimer
from PyQt5           import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update

class InfoView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'InfoViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Home', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")

    def init_ui(self):
        # 뒤로 가기 버튼 연결
        self.pushButton_InfoBackArrow.clicked.connect(self.on_back_button_clicked)

        # info.json 파일에서 정보 읽어오기
        self.load_info_from_json()

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

    def load_info_from_json(self):
        try:
            # info 폴더의 info.json 파일 경로
            json_path = os.path.join('info', 'info.json')
            
            # JSON 파일 읽기
            with open(json_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            
            # name 값을 label_name에 설정
            if 'name' in info_data:
                self.label_name.setText(info_data['name'])
            else:
                print("'name' key not found in info.json")
            
            # version 값을 label_version에 설정
            if 'version' in info_data:
                self.label_version.setText(info_data['version'])
            else:
                print("'version' key not found in info.json")
            
            # Serial 값을 label_Serial에 설정
            if 'sn' in info_data:
                self.label_Serial.setText(info_data['sn'])
            else:
                print("'sn' key not found in info.json")

        except FileNotFoundError:
            print(f"info.json file not found at {json_path}")
        except json.JSONDecodeError:
            print("Error decoding info.json file")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def update_date_time(self):
        update_date_time(self)
