# -*- coding: utf-8 -*-
"""
AppController - 전체 화면 흐름 및 뷰/시그널 관리
"""
import os
import sys
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QShortcut
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence

from views.Utils          import set_app_font
from views.LoadView       import LoadView
from views.HomeView       import HomeView
from views.LoginView      import LoginView
from views.AdminLoginView import AdminLoginView
from views.OperatorView   import OperatorView
from views.CalibrationIntroView import CalibrationIntroView
from views.CalibrationCautionView import CalibrationCautionView
from views.CalibrationInsertDeviceView import CalibrationInsertDeviceView
from views.CalibrationDeviceCheckView import CalibrationDeviceCheckView
from views.CalibrationEjectDeviceView import CalibrationEjectDeviceView
from views.CalibrationResultView import CalibrationResultView
from views.CalibrationCompleteView import CalibrationCompleteView
from views.ResultListView import ResultListView
from views.ResultCategoryView import ResultCategoryView
from views.SettingsView   import SettingsView
from views.DateTimeSettingsView import DateTimeSettingsView
from views.InfoView       import InfoView
from views.SelectView     import SelectView
from views.TestInfoView   import TestInfoView
from views.MeasureView    import MeasureView
from views.ResultView0    import ResultView0

from controllers import app_controller as backend_controller
from config.config import app_config

class AppController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCalthReader")
        self.setFixedSize(1024, 600)
        # self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_application_controller()
        self._create_views()
        self._add_views_to_stack()
        self._connect_signals()
        self.stacked_widget.setCurrentWidget(self.load_view)
        self._setup_shortcuts()

    def _create_views(self):
        self.load_view       = LoadView(self)
        self.home_view       = HomeView(self)
        self.login_view      = LoginView(self)
        self.admin_login_view = AdminLoginView(self)
        self.operator_view   = OperatorView(self)
        self.calibration_view = CalibrationIntroView(self)
        self.calibration_caution_view = None  # Caution 단계 뷰는 필요 시 생성
        self.calibration_insert_device_view = None  # Insert Device 단계 뷰는 필요 시 생성
        self.calibration_device_check_view = None  # Device Check 단계 뷰는 필요 시 생성
        self.calibration_eject_device_view = None  # Eject Device 단계 뷰는 필요 시 생성
        self.calibration_result_view = None  # Result 단계 뷰는 필요 시 생성
        self.calibration_complete_view = None  # Complete 단계 뷰는 필요 시 생성
        self.settings_view   = SettingsView(self)
        self.datetime_settings_view = DateTimeSettingsView(self)
        self.resultList_view = ResultListView(self)
        self.result_category_view = ResultCategoryView(self)
        self.info_view       = InfoView(self)
        self.select_view     = SelectView(self)
        self.test_info_view  = TestInfoView(self)
        self.measure_view    = MeasureView(self)
        self.result_view0    = ResultView0(self)
        #self.result_view1    = ResultView1(self)

    def _add_views_to_stack(self):
        self.stacked_widget.addWidget(self.load_view)
        self.stacked_widget.addWidget(self.home_view)
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.admin_login_view)
        self.stacked_widget.addWidget(self.operator_view)
        self.stacked_widget.addWidget(self.calibration_view)  # ← 추가
        # Caution 단계 뷰는 동적 추가
        self.stacked_widget.addWidget(self.settings_view)
        self.stacked_widget.addWidget(self.datetime_settings_view)
        self.stacked_widget.addWidget(self.resultList_view)
        self.stacked_widget.addWidget(self.result_category_view)
        self.stacked_widget.addWidget(self.info_view)
        self.stacked_widget.addWidget(self.select_view)
        self.stacked_widget.addWidget(self.test_info_view)
        self.stacked_widget.addWidget(self.measure_view)
        self.stacked_widget.addWidget(self.result_view0)
        #self.stacked_widget.addWidget(self.result_view1)

    def _connect_signals(self):
        self.load_view.finished.connect(self.switch_to_home_view)
        self.home_view.switch_to_select.connect(self.switch_to_select_view)
        self.home_view.switch_to_operator.connect(self.switch_to_operator_view)
        self.home_view.switch_to_resultList.connect(self.switch_to_result_category_view)
        self.home_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.home_view.switch_to_info.connect(self.switch_to_info_view)
        self.home_view.switch_to_login.connect(self.switch_to_login_view)
        self.home_view.switch_to_admin_login.connect(self.switch_to_admin_login_view)
        self.login_view.switch_to_home.connect(self.switch_to_home_view)
        self.login_view.login_success.connect(self.switch_to_home_view)
        self.admin_login_view.switch_to_home.connect(self.switch_to_home_view)
        self.admin_login_view.login_success.connect(self.on_admin_login_success)
        self.result_category_view.switch_to_home.connect(self.switch_to_home_view)
        self.result_category_view.switch_to_patient_results.connect(self.switch_to_resultList_view)
        self.result_category_view.switch_to_calibration_results.connect(self.switch_to_calibration_results)
        self.result_category_view.switch_to_qc_results.connect(self.switch_to_qc_results)
        self.info_view.switch_to_home.connect(self.switch_to_home_view)
        self.operator_view.switch_to_home.connect(self.switch_to_home_view)
        self.settings_view.switch_to_home.connect(self.switch_to_home_view)
        self.settings_view.switch_to_datetime_settings.connect(self.switch_to_datetime_settings_view)
        self.datetime_settings_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.resultList_view.switch_to_home.connect(self.switch_to_home_view)
        self.resultList_view.switch_to_result_category.connect(self.switch_to_result_category_view)
        self.select_view.switch_to_home.connect(self.switch_to_home_view)
        self.select_view.switch_to_test_info.connect(self.switch_to_test_info_view)
        self.test_info_view.switch_to_select.connect(self.switch_to_select_view)
        self.test_info_view.switch_to_measure.connect(self.switch_to_measure_view)
        self.measure_view.switch_to_result.connect(self.switch_to_result_view)
        self.result_view0.switch_to_home.connect(self.switch_to_home_view)
        self.datetime_settings_view.time_service.time_setting_changed.connect(self.on_time_setting_changed)
        self.calibration_view.switch_to_next_step.connect(self.on_calibration_intro_next)

    def _setup_shortcuts(self):
        self.quit_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Q), self)
        self.quit_shortcut.activated.connect(self.close)
        self.shutdown_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_X), self)
        self.shutdown_shortcut.activated.connect(self.confirm_shutdown)
        self.debug_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_D), self)
        self.debug_shortcut.activated.connect(self.toggle_debug_mode)

    def init_application_controller(self):
        try:
            backend_controller.system_ready.connect(self.on_system_ready)
            backend_controller.initialization_complete.connect(self.on_initialization_complete)
            backend_controller.error_occurred.connect(self.on_controller_error)
            backend_controller.status_changed.connect(self.on_status_changed)
            QTimer.singleShot(1000, self.initialize_application)
        except Exception as e:
            print(f"애플리케이션 컨트롤러 초기화 설정 실패: {str(e)}")

    def initialize_application(self):
        try:
            backend_controller.initialize()
        except Exception as e:
            print(f"애플리케이션 초기화 실패: {str(e)}")

    def on_system_ready(self, ready: bool):
        if ready:
            print("전체 시스템 준비 완료")
        else:
            print("시스템 일부 기능 제한")

    def on_initialization_complete(self):
        print("애플리케이션 초기화 완료")

    def on_controller_error(self, error_message: str):
        print(f"애플리케이션 오류: {error_message}")

    def on_status_changed(self, status_message: str):
        print(f"상태: {status_message}")

    def toggle_debug_mode(self):
        backend_controller.toggle_debug_mode()
        QMessageBox.information(self, '모드 변경', "모드가 변경되었습니다.\n재시작 후 적용됩니다.")

    def closeEvent(self, event):
        try:
            backend_controller.shutdown()
        except Exception as e:
            print(f"애플리케이션 종료 중 오류: {str(e)}")
        event.accept()

    def confirm_shutdown(self):
        reply = QMessageBox.question(self, '시스템 종료', "정말로 시스템을 종료하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.shutdown_system()

    def shutdown_system(self):
        os.system("sudo shutdown -h now")

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if   event.key() == Qt.Key_Q:
                self.close()
            elif event.key() == Qt.Key_X:
                self.confirm_shutdown()
        else:
            super().keyPressEvent(event)

    # --- 페이지 전환 함수들 ---
    def switch_to_home_view(self):
        self.stacked_widget.setCurrentWidget(self.home_view)
    def switch_to_operator_view(self):
        self.stacked_widget.setCurrentWidget(self.operator_view)
    def switch_to_calibration_view(self):
        self.stacked_widget.setCurrentWidget(self.calibration_view)
    def switch_to_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.settings_view)
    def switch_to_datetime_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.datetime_settings_view)
    def switch_to_resultList_view(self):
        print("Patient Results로 전환")
        self.resultList_view.set_result_type("patient")
        self.stacked_widget.setCurrentWidget(self.resultList_view)
    def switch_to_result_category_view(self):
        print("Result Category View로 전환")
        self.result_category_view.reset_view()
        self.stacked_widget.setCurrentWidget(self.result_category_view)
    def switch_to_calibration_results(self):
        print("Calibration Results로 전환")
        self.resultList_view.set_result_type("calibration")
        self.stacked_widget.setCurrentWidget(self.resultList_view)
    def switch_to_qc_results(self):
        print("QC Results로 전환")
        self.resultList_view.set_result_type("qc")
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
    def switch_to_admin_login_view(self, target: str):
        self.admin_login_view.set_target(target)
        self.stacked_widget.setCurrentWidget(self.admin_login_view)
    def on_admin_login_success(self, target: str):
        if target == "calibration":
            print("Admin 로그인 성공: Calibration 기능으로 이동")
            # QMessageBox.information(self, "Calibration", "Calibration 기능에 접근했습니다.\n(기능 구현 예정)")
            # self.switch_to_home_view()
            # TODO: Calibration 화면 구현 후 실제 이동
            self.switch_to_calibration_view()
        elif target == "settings":
            print("Admin 로그인 성공: Settings 화면으로 이동")
            self.switch_to_settings_view()
        else:
            print("Admin 로그인 성공: 홈 화면으로 이동")
            self.switch_to_home_view()
    def on_time_setting_changed(self, setting):
        print(f"시간 설정 변경됨: {setting}")
        views_to_update = [
            self.load_view,
            self.home_view,
            self.login_view,
            self.admin_login_view,
            self.operator_view,
            self.settings_view,
            self.datetime_settings_view,
            self.resultList_view,
            self.result_category_view,
            self.info_view,
            self.select_view,
            self.test_info_view,
            self.measure_view,
            self.result_view0
        ]
        from views.Utils import update_date_time
        for view in views_to_update:
            if hasattr(view, 'label_DateNClock'):
                update_date_time(view)

    def on_calibration_intro_next(self, data):
        """
        CalibrationIntroView에서 '다음' 클릭 시 호출. CautionView로 데이터 전달 및 화면 전환
        """
        # 캘리브레이션 키트 순서 초기화
        if data is None:
            data = {}
        data['current_kit'] = 1
        data['total_kits'] = 4
        data['kit_names'] = ['음성', '저농도', '중농도', '고농도']
        
        if self.calibration_caution_view is None:
            self.calibration_caution_view = CalibrationCautionView(self)
            self.calibration_caution_view.switch_to_home.connect(self.switch_to_home_view)
            self.calibration_caution_view.switch_to_next_step.connect(self.on_calibration_caution_next)
            self.stacked_widget.addWidget(self.calibration_caution_view)
        self.calibration_caution_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_caution_view)

    def on_calibration_caution_next(self, data):
        """Caution에서 다음 단계(Insert Device)로 이동"""
        if self.calibration_insert_device_view is None:
            self.calibration_insert_device_view = CalibrationInsertDeviceView(self)
            self.calibration_insert_device_view.switch_to_home.connect(self.switch_to_home_view)
            self.calibration_insert_device_view.switch_to_next_step.connect(self.on_calibration_insert_device_next)
            self.stacked_widget.addWidget(self.calibration_insert_device_view)
        
        # 현재 키트 정보 설정
        if data is None:
            data = {}
        if 'current_kit' not in data:
            data['current_kit'] = 1
            data['total_kits'] = 4
            data['kit_names'] = ['음성', '저농도', '중농도', '고농도']
        
        self.calibration_insert_device_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_insert_device_view)

    def on_calibration_insert_device_next(self, data):
        """Insert Device에서 다음 단계(Device Check)로 이동"""
        if self.calibration_device_check_view is None:
            self.calibration_device_check_view = CalibrationDeviceCheckView(self)
            self.calibration_device_check_view.switch_to_home.connect(self.switch_to_home_view)
            self.calibration_device_check_view.switch_to_next_step.connect(self.on_calibration_device_check_next)
            self.stacked_widget.addWidget(self.calibration_device_check_view)
        self.calibration_device_check_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_device_check_view)

    def on_calibration_device_check_next(self, data):
        """Device Check에서 다음 단계(Eject Device)로 이동"""
        if self.calibration_eject_device_view is None:
            self.calibration_eject_device_view = CalibrationEjectDeviceView(self)
            self.calibration_eject_device_view.switch_to_home.connect(self.switch_to_home_view)
            self.calibration_eject_device_view.switch_to_next_step.connect(self.on_calibration_eject_device_next)
            self.stacked_widget.addWidget(self.calibration_eject_device_view)
        self.calibration_eject_device_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_eject_device_view)

    def on_calibration_eject_device_next(self, data):
        """Eject Device에서 다음 단계로 이동 - 키트 반복 또는 Result로"""
        if data is None:
            data = {}
        
        current_kit = data.get('current_kit', 1)
        total_kits = data.get('total_kits', 4)
        
        # 아직 더 처리할 키트가 있는 경우
        if current_kit < total_kits:
            # 다음 키트로 이동
            data['current_kit'] = current_kit + 1
            
            # Insert Device로 다시 이동
            self.calibration_insert_device_view.set_data(data)
            self.stacked_widget.setCurrentWidget(self.calibration_insert_device_view)
        else:
            # 모든 키트를 처리했으므로 Result로 이동
            if self.calibration_result_view is None:
                self.calibration_result_view = CalibrationResultView(self)
                self.calibration_result_view.switch_to_home.connect(self.switch_to_home_view)
                self.calibration_result_view.switch_to_next_step.connect(self.on_calibration_result_next)
                self.calibration_result_view.switch_to_retry.connect(self.on_calibration_retry)
                self.stacked_widget.addWidget(self.calibration_result_view)
            
            # 임시로 랜덤하게 PASSED/FAILED 결정 (실제로는 캘리브레이션 결과에 따라)
            import random
            result_status = "PASSED" if random.choice([True, False]) else "FAILED"
            
            self.calibration_result_view.set_data(data)
            self.calibration_result_view.set_result_status(result_status)
            self.stacked_widget.setCurrentWidget(self.calibration_result_view)

    def on_calibration_result_next(self, data):
        """Result에서 다음 단계(Complete)로 이동"""
        if self.calibration_complete_view is None:
            self.calibration_complete_view = CalibrationCompleteView(self)
            self.calibration_complete_view.switch_to_home.connect(self.switch_to_home_view)
            self.stacked_widget.addWidget(self.calibration_complete_view)
        self.calibration_complete_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_complete_view)

    def on_calibration_retry(self, data):
        """캘리브레이션 재시도 - Intro로 돌아가기"""
        # 키트 순서 초기화
        if data is None:
            data = {}
        data['current_kit'] = 1
        data['total_kits'] = 4
        data['kit_names'] = ['음성', '저농도', '중농도', '고농도']
        
        self.calibration_view.reset_view()
        self.stacked_widget.setCurrentWidget(self.calibration_view)
