import os
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore    import pyqtSignal, QTimer
from PyQt5           import uic

from views.Utils     import start_date_time_update, stop_date_time_update

class OperatorView(QMainWindow):
    switch_to_home = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'OperatorViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")   
        
        # 뒤로 가기 버튼 연결
        self.pushButton_OperatorBackArrow.clicked.connect(self.on_back_button_clicked)

        # 버튼들 연결
        self.pushButton_Camset.clicked.connect(self.on_camset_button_clicked)
        self.pushButton_Settings.clicked.connect(self.on_settings_button_clicked)
        self.pushButton_Network.clicked.connect(self.on_network_button_clicked)
        self.pushButton_Update.clicked.connect(self.on_update_button_clicked)

        # 날짜와 시간 업데이트를 위한 타이머 설정
        self.date_time_timer = None

    def showEvent(self, event):
        super().showEvent(event)
        # 뷰가 표시될 때 날짜/시간 업데이트 시작
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        # 뷰가 닫힐 때 타이머 정지
        stop_date_time_update(self)
        super().closeEvent(event)

    def on_back_button_clicked(self):
        self.switch_to_home.emit()

    def on_camset_button_clicked(self):
        #self.switch_to_home.emit()
        print("Camset 버튼 클릭됨")

    def on_settings_button_clicked(self):
        #self.switch_to_home.emit()
        print("Settings 버튼 클릭됨")

    def on_network_button_clicked(self):
        #self.switch_to_home.emit()
        print("Network 버튼 클릭됨")

    def on_update_button_clicked(self):
        #self.switch_to_home.emit()
        print("Update 버튼 클릭됨")