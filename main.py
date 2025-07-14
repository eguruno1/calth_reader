# -*- coding: utf-8 -*-
#
# Created by: BenchSoft.co.
#

import sys
import os
from PyQt5.QtWidgets      import QApplication, QShortcut, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore         import Qt, QTimer
from PyQt5.QtGui          import QKeySequence

from views.Utils          import set_app_font
from views.LoadView       import LoadView
from views.HomeView       import HomeView
from views.LoginView      import LoginView
from views.OperatorView   import OperatorView
from views.ResultListView import ResultListView
from views.SettingsView   import SettingsView
from views.InfoView       import InfoView
from views.SelectView     import SelectView
from views.TestInfoView   import TestInfoView
from views.MeasureView    import MeasureView
from views.ResultView0    import ResultView0

from controllers import app_controller
from config.config import app_config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCalthReader")
        self.setFixedSize(1280, 720)  # 창 크기를 1280x720으로 고정
        self.setFixedSize(1024, 600)  # 창 크기를 1024x600으로 고정
        # self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)  # 윈도우 상단 바 제거
        
        # 창을 화면 전체 크기로 설정
        # self.setWindowState(Qt.WindowFullScreen)
        
        # CTRL+Q 단축키 설정        
        self.quit_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q), self)
        self.quit_shortcut.activated.connect(self.close)

        # CTRL+X 단축키 설정 (새로 추가)
        self.shutdown_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_X), self)
        self.shutdown_shortcut.activated.connect(self.confirm_shutdown)

        # CTRL+D 단축키 설정 (디버그 모드 토글)
        self.debug_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_D), self)
        self.debug_shortcut.activated.connect(self.toggle_debug_mode)

        # 창 테두리 제거
        # self.setWindowFlags(Qt.FramelessWindowHint)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # 백엔드 초기화
        self.init_application_controller()

        self.load_view       = LoadView(self)
        self.home_view       = HomeView(self)
        self.login_view      = LoginView(self)
        self.operator_view   = OperatorView(self)
        self.settings_view   = SettingsView(self)
        self.resultList_view = ResultListView(self)
        self.info_view       = InfoView(self)        
        self.select_view     = SelectView(self)
        self.test_info_view  = TestInfoView(self)
        self.measure_view    = MeasureView(self)
        self.result_view0    = ResultView0(self)
        #self.result_view1    = ResultView1(self)

        self.stacked_widget.addWidget(self.load_view)
        self.stacked_widget.addWidget(self.home_view)
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.operator_view)
        self.stacked_widget.addWidget(self.settings_view)
        self.stacked_widget.addWidget(self.resultList_view)
        self.stacked_widget.addWidget(self.info_view)
        self.stacked_widget.addWidget(self.select_view)
        self.stacked_widget.addWidget(self.test_info_view)
        self.stacked_widget.addWidget(self.measure_view)
        self.stacked_widget.addWidget(self.result_view0)
        #self.stacked_widget.addWidget(self.result_view1)

        # LoadView의 finished 시그널을 HomeView로의 전환과 연결
        self.load_view.finished.connect(self.switch_to_home_view)

        # HomeView의 시그널을 MainWindow의 슬롯에 연결
        self.home_view.switch_to_select.connect(self.switch_to_select_view)
        self.home_view.switch_to_operator.connect(self.switch_to_operator_view)
        self.home_view.switch_to_resultList.connect(self.switch_to_resultList_view)
        self.home_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.home_view.switch_to_info.connect(self.switch_to_info_view)
        self.home_view.switch_to_login.connect(self.switch_to_login_view)

        # LoginView의 시그널 연결
        self.login_view.switch_to_home.connect(self.switch_to_home_view)
        self.login_view.login_success.connect(self.switch_to_home_view)

        # View의 시그널을 HomeView의 슬롯에 연결
        self.info_view.switch_to_home.connect(self.switch_to_home_view)
        self.operator_view.switch_to_home.connect(self.switch_to_home_view)
        self.settings_view.switch_to_home.connect(self.switch_to_home_view)
        self.resultList_view.switch_to_home.connect(self.switch_to_home_view)

        # SelectView의 버튼 연결
        self.select_view.switch_to_home.connect(self.switch_to_home_view)
        self.select_view.switch_to_test_info.connect(self.switch_to_test_info_view)

        # TestInfoView의 버튼 연결
        self.test_info_view.switch_to_select.connect(self.switch_to_select_view)
        self.test_info_view.switch_to_measure.connect(self.switch_to_measure_view)

        # MeasureView의 프로그레스 fininsh 연결
        self.measure_view.switch_to_result.connect(self.switch_to_result_view)

        # ResultView의 버튼 연결
        self.result_view0.switch_to_home.connect(self.switch_to_home_view)

        # 시작화면으로 LoadView 표시
        self.stacked_widget.setCurrentWidget(self.load_view)

    def init_application_controller(self):
        """애플리케이션 컨트롤러 초기화"""
        try:
            # 애플리케이션 컨트롤러 시그널 연결
            app_controller.system_ready.connect(self.on_system_ready)
            app_controller.initialization_complete.connect(self.on_initialization_complete)
            app_controller.error_occurred.connect(self.on_controller_error)
            app_controller.status_changed.connect(self.on_status_changed)
            
            # 애플리케이션 초기화를 별도 타이머로 실행 (UI 블로킹 방지)
            QTimer.singleShot(1000, self.initialize_application)
            
        except Exception as e:
            print(f"애플리케이션 컨트롤러 초기화 설정 실패: {str(e)}")
    
    def initialize_application(self):
        """애플리케이션 실제 초기화"""
        try:
            app_controller.initialize()
        except Exception as e:
            print(f"애플리케이션 초기화 실패: {str(e)}")
    
    def on_system_ready(self, ready: bool):
        """시스템 준비 완료 시 호출"""
        if ready:
            print("전체 시스템 준비 완료")
        else:
            print("시스템 일부 기능 제한")
    
    def on_initialization_complete(self):
        """초기화 완료 시 호출"""
        print("애플리케이션 초기화 완료")
    
    def on_controller_error(self, error_message: str):
        """컨트롤러 오류 발생 시 호출"""
        print(f"애플리케이션 오류: {error_message}")
    
    def on_status_changed(self, status_message: str):
        """상태 변경 시 호출"""
        print(f"상태: {status_message}")

    def toggle_debug_mode(self):
        """디버그 모드 토글"""
        app_controller.toggle_debug_mode()
        QMessageBox.information(self, '모드 변경', 
                               "모드가 변경되었습니다.\n재시작 후 적용됩니다.")

    def closeEvent(self, event):
        # 애플리케이션 컨트롤러 종료
        try:
            app_controller.shutdown()
        except Exception as e:
            print(f"애플리케이션 종료 중 오류: {str(e)}")
        
        event.accept()

    def confirm_shutdown(self):
        reply = QMessageBox.question(self, '시스템 종료', 
                                     "정말로 시스템을 종료하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.shutdown_system()

    def shutdown_system(self):
        # 시스템 종료 명령 실행
        os.system("sudo shutdown -h now")

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if   event.key() == Qt.Key_Q:
                self.close()
            elif event.key() == Qt.Key_X:
                self.confirm_shutdown()
        else:
            super().keyPressEvent(event)

    def switch_to_home_view(self):
        self.stacked_widget.setCurrentWidget(self.home_view)

    def switch_to_operator_view(self):
        self.stacked_widget.setCurrentWidget(self.operator_view)

    def switch_to_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.settings_view)
    
    def switch_to_resultList_view(self):
        self.stacked_widget.setCurrentWidget(self.resultList_view)

    def switch_to_info_view(self):
        self.stacked_widget.setCurrentWidget(self.info_view)

    def switch_to_select_view(self):
        self.stacked_widget.setCurrentWidget(self.select_view)
    
    def switch_to_test_info_view(self, test_type):
        self.test_info_view.set_selected_test_type(test_type)
        self.stacked_widget.setCurrentWidget(self.test_info_view)

    def switch_to_measure_view(self):
        self.stacked_widget.setCurrentWidget(self.measure_view)

    def switch_to_result_view(self):
        self.stacked_widget.setCurrentWidget(self.result_view0)

    def switch_to_login_view(self):
        self.stacked_widget.setCurrentWidget(self.login_view)

# 메인 코드에서 set_app_font 함수 호출
if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_app_font()
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
