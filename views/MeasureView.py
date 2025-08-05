import os

from PyQt5.QtWidgets    import QMainWindow
from PyQt5.QtCore       import QTimer, pyqtSignal, Qt
from PyQt5              import uic

from views.Utils        import update_date_time, start_date_time_update, stop_date_time_update
from controllers import measurement_controller


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
        ui_file = os.path.join(project_root, 'ui', 'Test', ui_filename)
        
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

        # 타이머 설정 (측정 컨트롤러 사용)
        self.measurement_controller = measurement_controller
        
        # 측정 컨트롤러 시그널 연결
        self.measurement_controller.measurement_started.connect(self.on_measurement_started)
        self.measurement_controller.measurement_finished.connect(self.on_measurement_finished)
        self.measurement_controller.progress_updated.connect(self.on_progress_updated)
        self.measurement_controller.error_occurred.connect(self.on_measurement_error)

        # 날짜와 시간 표시
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(500, self.start_measurement)  # 측정 시작

    def start_measurement(self):
        """측정 시작 - 컨트롤러에 위임"""
        print("측정 시작 요청")
        success = self.measurement_controller.start_measurement()
        if not success:
            print("측정 시작 실패")

    def on_measurement_started(self):
        """측정 시작됨 (컨트롤러에서 알림)"""
        print("측정이 시작되었습니다")
        self.progressBar_Meas.setValue(0)
        self.progressBar_Meas.setFormat("측정 준비 중... - %p%")

    def on_progress_updated(self, progress: int, phase_name: str):
        """진행률 업데이트 (컨트롤러에서 알림)"""
        self.progressBar_Meas.setValue(progress)
        self.progressBar_Meas.setFormat(f"{phase_name} - %p%")

    def on_measurement_finished(self, result: dict):
        """측정 완료 (컨트롤러에서 알림)"""
        print(f"측정 완료: {result}")
        self.progressBar_Meas.setFormat("측정 완료 - %p%")
        # 1초 후 결과 화면으로 전환
        QTimer.singleShot(1000, lambda: self.switch_to_result.emit())

    def on_measurement_error(self, error_message: str):
        """측정 오류 (컨트롤러에서 알림)"""
        print(f"측정 오류: {error_message}")
        self.progressBar_Meas.setFormat(f"오류: {error_message}")

    def closeEvent(self, event):
        """뷰 종료시 정리"""
        stop_date_time_update(self)
        
        # 측정 중이라면 중지
        if hasattr(self, 'measurement_controller'):
            self.measurement_controller.stop_measurement()
        
        super().closeEvent(event)

    def update_date_time(self):
        update_date_time(self)
