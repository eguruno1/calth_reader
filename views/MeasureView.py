import os

from PyQt5.QtWidgets    import QMainWindow
from PyQt5.QtCore       import QTimer, pyqtSignal, Qt
from PyQt5              import uic

from views.Utils        import update_date_time, start_date_time_update, stop_date_time_update
from backend.backend_manager import backend_manager


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
        
        # 측정 단계
        self.measurement_phases = [
            {"name": "LED 켜기", "duration": 1000},
            {"name": "카메라 캡처", "duration": 2000},
            {"name": "이미지 분석", "duration": 1500},
            {"name": "LED 끄기", "duration": 500}
        ]
        self.current_phase = 0
        self.phase_start_time = 0

        # 날짜와 시간 표시
        self.update_date_time()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(500, self.start_measurement)  # 측정 시작

    def start_measurement(self):
        """측정 시작"""
        print("측정 시작")
        self.elapsed_time = 0
        self.current_phase = 0
        self.phase_start_time = 0
        self.progressBar_Meas.setValue(0)
        
        # 카메라 캡처 시작 (아직 시작되지 않았다면)
        if backend_manager.is_camera_ready():
            backend_manager.start_camera_capture()
        
        self.timer.start(50)  # 50ms마다 update_progress 호출
        self.execute_current_phase()

    def execute_current_phase(self):
        """현재 측정 단계 실행"""
        if self.current_phase >= len(self.measurement_phases):
            return
            
        phase = self.measurement_phases[self.current_phase]
        print(f"측정 단계: {phase['name']}")
        
        if phase['name'] == "LED 켜기":
            backend_manager.led_on(45)  # 최대 밝기로 LED 켜기
        elif phase['name'] == "카메라 캡처":
            # 카메라에서 이미지 캡처 및 저장
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"measurement_{timestamp}.jpg"
            success = backend_manager.save_image(filename)
            if success:
                print(f"이미지 캡처 완료: {filename}")
            else:
                print("이미지 캡처 실패 (디버그 모드에서는 정상)")
        elif phase['name'] == "LED 끄기":
            backend_manager.led_off()

    def update_progress(self):
        """진행률 업데이트"""
        self.elapsed_time += 50
        
        # 현재 단계가 완료되었는지 확인
        if self.current_phase < len(self.measurement_phases):
            current_phase_duration = self.measurement_phases[self.current_phase]['duration']
            phase_elapsed = self.elapsed_time - self.phase_start_time
            
            if phase_elapsed >= current_phase_duration:
                self.current_phase += 1
                self.phase_start_time = self.elapsed_time
                if self.current_phase < len(self.measurement_phases):
                    self.execute_current_phase()
        
        # 전체 진행률 계산
        progress = min(100, int(self.elapsed_time / self.total_time * 100))
        self.progressBar_Meas.setValue(progress)
        
        # 현재 단계 표시
        if self.current_phase < len(self.measurement_phases):
            phase_name = self.measurement_phases[self.current_phase]['name']
            self.progressBar_Meas.setFormat(f"{phase_name} - %p%")
        
        if self.elapsed_time >= self.total_time:
            self.timer.stop()
            self.measurement_finished()

    def measurement_finished(self):
        """측정 완료"""
        print("측정이 완료되었습니다.")
        self.progressBar_Meas.setFormat("측정 완료 - %p%")
        
        # LED 끄기 (확실히 하기 위해)
        backend_manager.led_off()
        
        # 결과 화면으로 전환
        QTimer.singleShot(1000, lambda: self.switch_to_result.emit())

    def closeEvent(self, event):
        """뷰 종료시 정리"""
        stop_date_time_update(self)
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # LED 끄기
        backend_manager.led_off()
        
        super().closeEvent(event)

    def update_date_time(self):
        update_date_time(self)
