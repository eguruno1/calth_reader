# -*- coding: utf-8 -*-
#
# Created by: BenchSoft.co.
#

import sys
import os
from PyQt5.QtWidgets      import QApplication, QShortcut, QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore         import Qt
from PyQt5.QtGui          import QKeySequence

from views.Utils          import set_app_font
from views.LoadView       import LoadView
from views.HomeView       import HomeView
from views.OperatorView   import OperatorView
from views.ResultListView import ResultListView
from views.SettingsView   import SettingsView
from views.InfoView       import InfoView
from views.SelectView     import SelectView
from views.TestInfoView   import TestInfoView
from views.MeasureView    import MeasureView
from views.ResultView0    import ResultView0

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

        # 창 테두리 제거
        # self.setWindowFlags(Qt.FramelessWindowHint)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.load_view       = LoadView(self)
        self.home_view       = HomeView(self)
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

    def closeEvent(self, event):
        # 여기에 종료 전 수행할 작업을 추가할 수 있습니다.
        # 예: 설정 저장, 연결 종료 등
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

# 메인 코드에서 set_app_font 함수 호출
if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_app_font()
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
