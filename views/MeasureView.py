import os

from PyQt5.QtWidgets    import QMainWindow
from PyQt5.QtCore       import QTimer, pyqtSignal, Qt
from PyQt5              import uic

from views.Utils        import update_date_time, start_date_time_update, stop_date_time_update


class MeasureView(QMainWindow):
    #switch_to_test_info = pyqtSignal()
    #measure_finished    = pyqtSignal()
    switch_to_result = pyqtSignal()  # ResultView로 전환하기 위한 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_ui()
        self.init_ui()
        
    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 
        ui_filename = 'MeasureViewWindow.ui'
        ui_folder = next(folder for folder in os.listdir(project_root) if folder.lower() == 'ui')
        ui_file = os.path.join(project_root, ui_folder, ui_filename)
        
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

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.elapsed_time = 0
        self.total_time = 5000  # 총 5000ms (5초)

        # 날짜와 시간 표시
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(200, self.start_measurement)  # 측정 시작

    def start_measurement(self):
        print("측정 시작")
        self.elapsed_time = 0
        self.progressBar_Meas.setValue(0)
        self.timer.start(50)  # 50ms마다 update_progress 호출

    def update_progress(self):
        self.elapsed_time += 50
        progress = min(100, int(self.elapsed_time / self.total_time * 100))
        #print(f"진행 중: {progress}%")
        self.progressBar_Meas.setValue(progress)
        
        if self.elapsed_time >= self.total_time:
            self.timer.stop()
            self.measurement_finished()

    def measurement_finished(self):
        print("측정이 완료되었습니다.")
        self.switch_to_result.emit()  # ResultView로 전환

    def closeEvent(self, event):
        stop_date_time_update(self)
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)

    def update_date_time(self):
        update_date_time(self)
