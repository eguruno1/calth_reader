# -*- coding: utf-8 -*-
"""
AppController - 전체 화면 흐름 및 뷰/시그널 관리
"""
import os
import sys
import json
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QShortcut
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence

from views.Utils          import set_app_font
from views.LoadView       import LoadView
from views.HomeView       import HomeView
from views.LoginView      import LoginView
from views.AdminLoginView import AdminLoginView
from views.OperatorView   import OperatorView
from views.PreTestingIntroView import PreTestingIntroView
from views.PreTestingCautionView import PreTestingCautionView
from views.PreTestingInsertDeviceView import PreTestingInsertDeviceView
from views.PreTestingDeviceCheckView import PreTestingDeviceCheckView
from views.PreTestingEjectDeviceView import PreTestingEjectDeviceView
from views.PreTestingResultView import PreTestingResultView
from views.PreTestingCompleteView import PreTestingCompleteView
from views.ResultListView import ResultListView
from views.ResultCategoryView import ResultCategoryView
from views.SettingsView   import SettingsView
from views.DateTimeSettingsView import DateTimeSettingsView
from views.UpdateSettingsView import UpdateSettingsView
from views.CalibrationQCSettingsView import CalibrationQCSettingsView
from views.GeneralSettingsView import GeneralSettingsView
from views.PowerManagementView import PowerManagementView
from views.ManageOperatorView import ManageOperatorView
from views.InfoView       import InfoView
from views.SelectView     import SelectView
from views.TestInfoView   import TestInfoView
from views.MeasureView    import MeasureView
from views.ResultView0    import ResultView0
from views.ResultView1    import ResultView1
from config.pretest_config import PretestConfig
from views.ResultView0    import ResultView0

# 계정관리 관련 
from views.AccountAddView    import AccountAddView
from views.AccountIdEditView import AccountIdEditView
from views.AccountPwEditView import AccountPwEditView
from views.AdminPwEdit1View  import AdminPwEdit1View
from views.AdminPwEdit2View  import AdminPwEdit2View
from views.AccountDeleteView  import AccountDeleteView

# 테스트 진행 추가 
from views.IncubationView import IncubationView
from views.InsertDeviceView import InsertDeviceView


from controllers import app_controller as backend_controller
from config.config import app_config
# 배터리 충전량 알림.
from views.widgets.Low_battery_overlay import LowBatteryOverlayWidget
from views.widgets.slot_status_overlay import SlotStatusOverlayWidget
from views.widgets.power_status_overlay import PowerStatusOverlayWidget
from views.widgets.usb_status_overlay import USBStatusOverlayWidget


class AppController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyCalthReader")
        # self.setFixedSize(1024, 600)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowFullScreen)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_application_controller()
        self._create_views()
        self._add_views_to_stack()
        self._connect_signals()
        self.stacked_widget.setCurrentWidget(self.load_view)
        self._setup_shortcuts()

        # 배터리 상태를 위해..
        self.low_battery_overlay = LowBatteryOverlayWidget(self)    # 🔥 Low Battery 전역 위젯
        # 🔌 System status overlays
        self.slot_status_overlay = SlotStatusOverlayWidget(self)
        self.power_status_overlay = PowerStatusOverlayWidget(self)
        self.usb_status_overlay = USBStatusOverlayWidget(self)

        self.backend_controller = backend_controller
        self._active_uart_view = None
        # UART 옵저버로 UIController 자체 등록
        self.backend_controller.uart_model.add_observer(self)       

    #==========================================
    # --- View 선언 ---
    #==========================================
    def _create_views(self):
        self.load_view        = LoadView(self)
        self.home_view        = HomeView(self, uart_model=backend_controller.uart_model)
        self.login_view       = LoginView(self)
        self.admin_login_view = AdminLoginView(self)
        self.operator_view    = OperatorView(self)
        # Calibration 전용 views
        self.calibration_view               = PreTestingIntroView(self, PretestConfig.TYPE_CALIBRATION)
        self.calibration_caution_view       = None  # Caution 단계 뷰는 필요 시 생성
        self.calibration_insert_device_view = None  # Insert Device 단계 뷰는 필요 시 생성
        self.calibration_device_check_view  = None  # Device Check 단계 뷰는 필요 시 생성
        self.calibration_eject_device_view  = None  # Eject Device 단계 뷰는 필요 시 생성
        self.calibration_result_view        = None  # Result 단계 뷰는 필요 시 생성
        self.calibration_complete_view      = None  # Complete 단계 뷰는 필요 시 생성
        # QC 전용 views (필요 시 생성)
        self.qc_view               = None
        self.qc_caution_view       = None
        self.qc_insert_device_view = None
        self.qc_device_check_view  = None
        self.qc_eject_device_view  = None
        self.qc_result_view        = None
        self.qc_complete_view      = None
        # 기타 views
        self.settings_view                = SettingsView(self)
        self.datetime_settings_view       = DateTimeSettingsView(self)
        self.update_settings_view         = UpdateSettingsView(self)
        self.calibration_qc_settings_view = CalibrationQCSettingsView(self)
        self.general_settings_view        = GeneralSettingsView(self)
        self.power_management_view        = PowerManagementView(self)
        self.manage_operator_view         = ManageOperatorView(self)  # 계정관리
        self.resultList_view              = ResultListView(self)
        self.result_category_view         = ResultCategoryView(self)
        self.info_view                    = InfoView(self)
        self.select_view                  = SelectView(self, uart_model=backend_controller.uart_model)
        self.test_info_view               = TestInfoView(self, uart_model=backend_controller.uart_model)
        self.measure_view                 = MeasureView(self, uart_model=backend_controller.uart_model)
        self.result_view0                 = ResultView0(self, uart_model=backend_controller.uart_model)
        #self.result_view1                = ResultView1(self)

        # 테스트 진행 추가
        self.incubation_view              = IncubationView(self, uart_model=backend_controller.uart_model)
        self.insert_device_view           = InsertDeviceView(self, uart_model=backend_controller.uart_model)

        # 계정관련 views
        self.account_add_view             = AccountAddView(self)    # 신규 사용자 추가.
        self.account_id_edit_view         = AccountIdEditView(self) # ID 변경.
        self.account_pw_edit_view         = AccountPwEditView(self) # PW 변경.
        self.admin_pw_edit1_view          = AdminPwEdit1View(self)  # admin PW 1차 확인.
        self.admin_pw_edit2_view          = AdminPwEdit2View(self)  # admin PW 2차 확인.
        self.account_delete_view          = AccountDeleteView(self) # 사용자 삭제(is_active:false)

    #==========================================
    # --- View Stack Add ---
    #==========================================
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
        self.stacked_widget.addWidget(self.update_settings_view)
        self.stacked_widget.addWidget(self.calibration_qc_settings_view)
        self.stacked_widget.addWidget(self.general_settings_view)
        self.stacked_widget.addWidget(self.power_management_view)
        self.stacked_widget.addWidget(self.manage_operator_view)
        self.stacked_widget.addWidget(self.resultList_view)
        self.stacked_widget.addWidget(self.result_category_view)
        self.stacked_widget.addWidget(self.info_view)
        self.stacked_widget.addWidget(self.select_view)
        self.stacked_widget.addWidget(self.test_info_view)
        self.stacked_widget.addWidget(self.measure_view)
        self.stacked_widget.addWidget(self.result_view0)
        #self.stacked_widget.addWidget(self.result_view1)

        # 테스트 진행 추가
        self.stacked_widget.addWidget(self.incubation_view)
        self.stacked_widget.addWidget(self.insert_device_view)

        # 계정관련
        self.stacked_widget.addWidget(self.account_add_view)
        self.stacked_widget.addWidget(self.account_id_edit_view)
        self.stacked_widget.addWidget(self.account_pw_edit_view)
        self.stacked_widget.addWidget(self.admin_pw_edit1_view)
        self.stacked_widget.addWidget(self.admin_pw_edit2_view)
        self.stacked_widget.addWidget(self.account_delete_view)



    #==========================================
    # --- 시그널 연결 ---
    #==========================================
    def _connect_signals(self):
        self.load_view.finished.connect(self.switch_to_home_view)
        # self.home_view.switch_to_select.connect(self.switch_to_select_view) select not used
        self.home_view.switch_to_select.connect(self.switch_to_test_info_view)
        self.home_view.switch_to_operator.connect(self.switch_to_operator_view)
        self.home_view.switch_to_resultList.connect(self.switch_to_result_category_view)
        self.home_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.home_view.switch_to_info.connect(self.switch_to_info_view)
        self.home_view.switch_to_login.connect(self.switch_to_login_view_with_context)
        self.home_view.switch_to_admin_login.connect(self.switch_to_admin_login_view)
        self.home_view.switch_to_qc.connect(self.switch_to_qc_view)  # QC 직접 진입 연결 추가
        self.login_view.switch_to_home.connect(self.switch_to_home_view)
        self.login_view.login_success.connect(self.switch_to_home_view)
        self.login_view.switch_to_qc.connect(self.switch_to_qc_view)  # QC 진입 연결 추가
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
        self.settings_view.switch_to_update_settings.connect(self.switch_to_update_settings_view)
        self.settings_view.switch_to_calibration_qc_settings.connect(self.switch_to_calibration_qc_settings_view)
        self.settings_view.switch_to_general_settings.connect(self.switch_to_general_settings_view)
        self.settings_view.switch_to_power_management.connect(self.switch_to_power_management_view)
        self.settings_view.switch_to_manage_operator.connect(self.switch_to_manage_operator_view)
        self.datetime_settings_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.update_settings_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.calibration_qc_settings_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.general_settings_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.power_management_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.manage_operator_view.switch_to_settings.connect(self.switch_to_settings_view)
        self.resultList_view.switch_to_home.connect(self.switch_to_home_view)
        self.resultList_view.switch_to_result_category.connect(self.switch_to_result_category_view)
        self.select_view.switch_to_home.connect(self.switch_to_home_view)
        self.select_view.switch_to_test_info.connect(self.switch_to_test_info_view)
        # self.test_info_view.switch_to_select.connect(self.switch_to_select_view)
        # self.test_info_view.switch_to_measure.connect(self.switch_to_measure_view)
        self.test_info_view.switch_to_home.connect(self.switch_to_home_view)
        self.test_info_view.switch_to_measure.connect(self._on_testinfo_next_requested)#선택한 메뉴에 따라 이동처리를 위해.
        self.measure_view.switch_to_result.connect(self.switch_to_result_view)
        self.result_view0.switch_to_home.connect(self.switch_to_home_view)
        self.datetime_settings_view.time_service.time_setting_changed.connect(self.on_time_setting_changed)
        self.calibration_view.switch_to_home.connect(self.switch_to_home_view)
        self.calibration_view.switch_to_next_step.connect(self.on_calibration_intro_next)
        # info
        self.general_settings_view.switch_to_info.connect(self.switch_to_info_view)


        # 테스트 진행 추가
        self.incubation_view.switch_to_test_info_view.connect(
            self.switch_to_test_info_view
        )
        self.incubation_view.switch_to_measure_view.connect(
            self.switch_to_measure_view
        )

        self.insert_device_view.switch_to_test_info_view.connect(
            self.switch_to_test_info_view
        )
        self.insert_device_view.switch_to_measure_view.connect(
            # self.switch_to_measure_view
            # 인서트디바이스 뷰는 스탠다드, 리드온리, 큐시테스트 모두 사용.
            self._on_insert_device_next_requested
        )

        # 계정관련
        self.manage_operator_view.switch_to_account_add.connect(
            self.switch_to_account_add_view
        )

        self.account_add_view.switch_to_manage_operator.connect(
            self.switch_to_manage_operator_view
        )
        # 계정 추가후 기존 목록 Refresh
        self.account_add_view.user_created.connect(
            self.manage_operator_view.load_user_data
        )

        # ManageOperator → Edit ID
        self.manage_operator_view.switch_to_account_edit.connect(
            self.switch_to_account_id_edit
        )

        # Edit ID → ManageOperator
        self.account_id_edit_view.switch_to_manage_operator.connect(
            self.switch_to_manage_operator_view
        )

        # ID 변경 완료 → refresh
        self.account_id_edit_view.user_id_updated.connect(
            self.manage_operator_view.load_user_data
        )

        # ManageOperator → Edit PW
        self.manage_operator_view.switch_to_account_pw_edit.connect(
            self.switch_to_account_pw_edit
        )

        # Edit PW → ManageOperator
        self.account_pw_edit_view.switch_to_manage_operator.connect(
            self.switch_to_manage_operator_view
        )

        # PW 변경 완료 → refresh
        self.account_pw_edit_view.user_pw_updated.connect(
            self.manage_operator_view.load_user_data
        )

        # admin PW 변경 1차 확인.
        # ManageOperator → Edit PW
        self.manage_operator_view.switch_to_admin_pw_edit.connect(
            self.switch_to_admin_pw_edit
        )

        self.admin_pw_edit1_view.switch_to_manage_operator.connect(
            self.switch_to_manage_operator_view
        )

        self.admin_pw_edit1_view.switch_to_admin_pw_edit2.connect(
            self.switch_to_admin_pw_edit2
        )

        # admin PW 변경 2차 확인.
        self.admin_pw_edit1_view.switch_to_admin_pw_edit2.connect(
            self.switch_to_admin_pw_edit2
        )

        self.admin_pw_edit2_view.switch_to_manage_operator.connect(
            self.switch_to_manage_operator_view
        )
        # PW 변경 완료 → refresh
        self.admin_pw_edit2_view.password_updated.connect(
            self.manage_operator_view.load_user_data
        )

        # 사용자 삭제 시그널 연결
        self.manage_operator_view.switch_to_account_delete.connect(
            self.switch_to_account_delete
        )

        self.account_delete_view.switch_to_manage_operator.connect(
            self.switch_to_manage_operator_view
        )
        self.account_delete_view.user_deleted.connect(
            self.manage_operator_view.load_user_data
        )



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

    #==========================================
    # --- 페이지 전환 함수들 ---
    #==========================================
    def switch_to_home_view(self):
        print("[UIController] switch_to_home_view")

        self.stacked_widget.setCurrentWidget(self.home_view)
        self._set_active_uart_view(self.home_view)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.home_view._update_battery_ui(battery)

    def switch_to_operator_view(self):
        self.stacked_widget.setCurrentWidget(self.operator_view)

    def switch_to_calibration_view(self):
        self.stacked_widget.setCurrentWidget(self.calibration_view)

    def switch_to_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.settings_view)

    def switch_to_datetime_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.datetime_settings_view)

    def switch_to_update_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.update_settings_view)

    def switch_to_calibration_qc_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.calibration_qc_settings_view)

    def switch_to_general_settings_view(self):
        self.stacked_widget.setCurrentWidget(self.general_settings_view)
    
    def switch_to_power_management_view(self):
        self.stacked_widget.setCurrentWidget(self.power_management_view)
    
    def switch_to_manage_operator_view(self):
        self.stacked_widget.setCurrentWidget(self.manage_operator_view)

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
        print("[UIController] switch_to_select_view")
        self.stacked_widget.setCurrentWidget(self.select_view)
        self._set_active_uart_view(self.select_view)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.select_view._update_battery_ui(battery)

    def switch_to_test_info_view(self, test_type):
        print("[UIController] switch_to_test_info_view")
        self.test_info_view.set_selected_test_type(test_type)
        self.stacked_widget.setCurrentWidget(self.test_info_view)
        self._set_active_uart_view(self.test_info_view)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.test_info_view._update_battery_ui(battery)

    def switch_to_measure_view(self):
        self.stacked_widget.setCurrentWidget(self.measure_view)
        self._set_active_uart_view(self.measure_view)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.measure_view._update_battery_ui(battery)

    def switch_to_result_view(self, test_session_id=None):
        if test_session_id is not None:
            self.result_view0.set_test_session_id(test_session_id)
            
        self.stacked_widget.setCurrentWidget(self.result_view0)
        self._set_active_uart_view(self.result_view0)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.result_view0._update_battery_ui(battery)

    def switch_to_login_view(self):
        self.stacked_widget.setCurrentWidget(self.login_view)

    def switch_to_login_view_with_context(self, context: str):
        """컨텍스트와 함께 로그인 뷰로 전환"""
        if hasattr(self.login_view, 'set_context'):
            self.login_view.set_context(context)
        self.stacked_widget.setCurrentWidget(self.login_view)
        
    def switch_to_login_view_with_context(self, context: str):
        """컨텍스트와 함께 로그인 화면으로 전환"""
        self.login_view.set_context(context)
        self.stacked_widget.setCurrentWidget(self.login_view)

    def switch_to_admin_login_view(self, target: str):
        self.admin_login_view.set_target(target)
        self.stacked_widget.setCurrentWidget(self.admin_login_view)

    # 계정관련
    def switch_to_account_add_view(self):
        """사용자 추가"""
        self.stacked_widget.setCurrentWidget(self.account_add_view)

    def switch_to_account_id_edit(self, user_id: str):
        """사용자 ID 변경"""
        self.account_id_edit_view.set_user(user_id)
        self.stacked_widget.setCurrentWidget(self.account_id_edit_view)

    def switch_to_account_pw_edit(self, user_id: str):
        """사용자 PW 변경"""
        self.account_pw_edit_view.set_user(user_id)
        self.stacked_widget.setCurrentWidget(self.account_pw_edit_view)

    def switch_to_admin_pw_edit(self, user_id: str):
        """Admin PW 변경"""
        self.admin_pw_edit1_view.set_user(user_id)
        self.stacked_widget.setCurrentWidget(self.admin_pw_edit1_view)

    def switch_to_admin_pw_edit2(self):
        self.admin_pw_edit2_view.set_user()
        self.stacked_widget.setCurrentWidget(self.admin_pw_edit2_view)

    def switch_to_account_delete(self, user_id: str):
        """사용자 삭제"""
        self.account_delete_view.set_target_user(user_id)
        self.stacked_widget.setCurrentWidget(self.account_delete_view)    


    # 테스트 진행 추가    
    def switch_to_incubation_view(self):
        """incubation"""
        self.stacked_widget.setCurrentWidget(self.incubation_view)
        self._set_active_uart_view(self.incubation_view)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.incubation_view._update_battery_ui(battery)

    def switch_to_insert_device_view(self):
        """insert device"""
        self.stacked_widget.setCurrentWidget(self.insert_device_view)  
        self._set_active_uart_view(self.insert_device_view)
        # 초기 배터리 상태
        battery = self.backend_controller.uart_model.get_battery_info()
        if battery:
            self.insert_device_view._update_battery_ui(battery)  
    
    
    #==========================================
    # --- 여기까지 페이지 전환 함수들 ---
    #==========================================    

    def on_admin_login_success(self, target: str):
        if target == "calibration":
            print("Admin 로그인 성공: Calibration 기능으로 이동")
            self.switch_to_calibration_view()
        elif target == "qc":
            print("Admin 로그인 성공: QC Test 기능으로 이동")
            self.switch_to_qc_view()
        elif target == "settings":
            print("Admin 로그인 성공: Settings 화면으로 이동")
            self.switch_to_settings_view()
        else:
            print("Admin 로그인 성공: 홈 화면으로 이동")
            self.switch_to_home_view()

    def switch_to_qc_view(self):
        """QC Test 화면으로 전환"""
        if self.qc_view is None:
            self.qc_view = PreTestingIntroView(self, PretestConfig.TYPE_QC)
            self.qc_view.switch_to_home.connect(self.switch_to_home_view)
            self.qc_view.switch_to_next_step.connect(self.on_qc_intro_next)
            self.stacked_widget.addWidget(self.qc_view)
        self.stacked_widget.setCurrentWidget(self.qc_view)

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
        Pre-Testing IntroView에서 '다음' 클릭 시 호출. CautionView로 데이터 전달 및 화면 전환
        """
        # 캘리브레이션 키트 순서 초기화
        if data is None:
            data = {}
        pretest_type = data.get('pretest_type', PretestConfig.TYPE_CALIBRATION)
        config = PretestConfig.get_config(pretest_type)
        
        data['current_kit'] = 1
        data['total_kits'] = config['total_kits']
        data['kit_names'] = config['kit_names']
        
        if self.calibration_caution_view is None:
            self.calibration_caution_view = PreTestingCautionView(self)
            self.calibration_caution_view.switch_to_home.connect(self.switch_to_home_view)
            self.calibration_caution_view.switch_to_next_step.connect(self.on_calibration_caution_next)
            self.stacked_widget.addWidget(self.calibration_caution_view)
        self.calibration_caution_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_caution_view)

    def on_calibration_caution_next(self, data):
        """Caution에서 다음 단계(Insert Device)로 이동"""
        if self.calibration_insert_device_view is None:
            self.calibration_insert_device_view = PreTestingInsertDeviceView(self)
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
            self.calibration_device_check_view = PreTestingDeviceCheckView(self)
            self.calibration_device_check_view.switch_to_home.connect(self.switch_to_home_view)
            self.calibration_device_check_view.switch_to_next_step.connect(self.on_calibration_device_check_next)
            self.stacked_widget.addWidget(self.calibration_device_check_view)
        self.calibration_device_check_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_device_check_view)

    def on_calibration_device_check_next(self, data):
        """Device Check에서 다음 단계(Eject Device)로 이동"""
        if self.calibration_eject_device_view is None:
            self.calibration_eject_device_view = PreTestingEjectDeviceView(self)
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
                self.calibration_result_view = PreTestingResultView(self)
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
            self.calibration_complete_view = PreTestingCompleteView(self)
            self.calibration_complete_view.switch_to_home.connect(self.switch_to_home_view)
            self.stacked_widget.addWidget(self.calibration_complete_view)
        self.calibration_complete_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.calibration_complete_view)

    def on_calibration_retry(self, data):
        """캘리브레이션 재시도 - Intro로 돌아가기"""
        # 키트 순서 초기화
        if data is None:
            data = {}
        
        pretest_type = data.get('pretest_type', PretestConfig.TYPE_CALIBRATION)
        config = PretestConfig.get_config(pretest_type)
        
        data['current_kit'] = 1
        data['total_kits'] = config['total_kits']
        data['kit_names'] = config['kit_names']
        
        if hasattr(self.calibration_view, 'reset_view'):
            self.calibration_view.reset_view()
        self.stacked_widget.setCurrentWidget(self.calibration_view)

    # QC Test 관련 메서드들
    def on_qc_intro_next(self, data):
        """QC IntroView에서 '다음' 클릭 시 호출"""
        if data is None:
            data = {}
        pretest_type = data.get('pretest_type', PretestConfig.TYPE_QC)
        config = PretestConfig.get_config(pretest_type)
        
        data['current_kit'] = 1
        data['total_kits'] = config['total_kits']
        data['kit_names'] = config['kit_names']
        
        if self.qc_caution_view is None:
            self.qc_caution_view = PreTestingCautionView(self)
            self.qc_caution_view.switch_to_home.connect(self.switch_to_home_view)
            self.qc_caution_view.switch_to_next_step.connect(self.on_qc_caution_next)
            self.stacked_widget.addWidget(self.qc_caution_view)
        self.qc_caution_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.qc_caution_view)

    def on_qc_caution_next(self, data):
        """QC Caution에서 다음 단계로 이동"""
        if self.qc_insert_device_view is None:
            self.qc_insert_device_view = PreTestingInsertDeviceView(self)
            self.qc_insert_device_view.switch_to_home.connect(self.switch_to_home_view)
            self.qc_insert_device_view.switch_to_next_step.connect(self.on_qc_insert_device_next)
            self.stacked_widget.addWidget(self.qc_insert_device_view)
        
        if data is None:
            data = {}
        if 'current_kit' not in data:
            config = PretestConfig.get_config(data.get('pretest_type', PretestConfig.TYPE_QC))
            data['current_kit'] = 1
            data['total_kits'] = config['total_kits']
            data['kit_names'] = config['kit_names']
        
        self.qc_insert_device_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.qc_insert_device_view)

    def on_qc_insert_device_next(self, data):
        """QC Insert Device에서 다음 단계로 이동"""
        if self.qc_device_check_view is None:
            self.qc_device_check_view = PreTestingDeviceCheckView(self)
            self.qc_device_check_view.switch_to_home.connect(self.switch_to_home_view)
            self.qc_device_check_view.switch_to_next_step.connect(self.on_qc_device_check_next)
            self.stacked_widget.addWidget(self.qc_device_check_view)
        self.qc_device_check_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.qc_device_check_view)

    def on_qc_device_check_next(self, data):
        """QC Device Check에서 다음 단계로 이동"""
        if self.qc_eject_device_view is None:
            self.qc_eject_device_view = PreTestingEjectDeviceView(self)
            self.qc_eject_device_view.switch_to_home.connect(self.switch_to_home_view)
            self.qc_eject_device_view.switch_to_next_step.connect(self.on_qc_eject_device_next)
            self.stacked_widget.addWidget(self.qc_eject_device_view)
        self.qc_eject_device_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.qc_eject_device_view)

    def on_qc_eject_device_next(self, data):
        """QC Eject Device에서 다음 단계로 이동"""
        if data is None:
            data = {}
        
        current_kit = data.get('current_kit', 1)
        total_kits = data.get('total_kits', 3)
        
        # 아직 더 처리할 키트가 있는 경우
        if current_kit < total_kits:
            data['current_kit'] = current_kit + 1
            self.qc_insert_device_view.set_data(data)
            self.stacked_widget.setCurrentWidget(self.qc_insert_device_view)
        else:
            # 모든 키트를 처리했으므로 Result로 이동
            if self.qc_result_view is None:
                self.qc_result_view = PreTestingResultView(self)
                self.qc_result_view.switch_to_home.connect(self.switch_to_home_view)
                self.qc_result_view.switch_to_next_step.connect(self.on_qc_result_next)
                self.qc_result_view.switch_to_retry.connect(self.on_qc_retry)
                self.stacked_widget.addWidget(self.qc_result_view)
            
            # 임시로 랜덤하게 PASSED/FAILED 결정
            import random
            result_status = "PASSED" if random.choice([True, False]) else "FAILED"
            
            self.qc_result_view.set_data(data)
            self.qc_result_view.set_result_status(result_status)
            self.stacked_widget.setCurrentWidget(self.qc_result_view)

    def on_qc_result_next(self, data):
        """QC Result에서 다음 단계로 이동"""
        if self.qc_complete_view is None:
            self.qc_complete_view = PreTestingCompleteView(self)
            self.qc_complete_view.switch_to_home.connect(self.switch_to_home_view)
            self.stacked_widget.addWidget(self.qc_complete_view)
        self.qc_complete_view.set_data(data)
        self.stacked_widget.setCurrentWidget(self.qc_complete_view)

    def on_qc_retry(self, data):
        """QC 재시도 - Intro로 돌아가기"""
        if data is None:
            data = {}
        
        pretest_type = data.get('pretest_type', PretestConfig.TYPE_QC)
        config = PretestConfig.get_config(pretest_type)
        
        data['current_kit'] = 1
        data['total_kits'] = config['total_kits']
        data['kit_names'] = config['kit_names']
        
        if hasattr(self.qc_view, 'reset_view'):
            self.qc_view.reset_view()
        self.stacked_widget.setCurrentWidget(self.qc_view)

    #==========================================
    # --- 홈에서 Standard Test, Read Only, QC Test 분기 위해 ---
    #==========================================
    def _get_select_menu(self):
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        # TestInfoView 정보를 json에서 읽는다.
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')

        with open(self.current_json_path, "r") as f:
            data = json.load(f)
        return data.get("select_menu")
    
    def _on_testinfo_next_requested(self):
        """
        TestInfoView에서 슬롯 체크 OK 후 호출됨
        기존 switch_to_measure를 그대로 사용
        """

        select_menu = self._get_select_menu()

        if select_menu == "StandardTest":
            # TestInfo → InsertDevice
            # self.switch_to_incubation_view()
            self.switch_to_insert_device_view()

        elif select_menu == "ReadOnly":
            # TestInfo → InsertDevice
            self.switch_to_insert_device_view()

        elif select_menu == "QCTest":
            # TestInfo → InsertDevice (QC는 이후 Incubation 있음)
            self.switch_to_insert_device_view()

        else:
            raise ValueError(f"Unknown Select Menu: {select_menu}")

    def _on_insert_device_next_requested(self):
        """
        InsertDeviceView 완료 후 다음 화면 결정
        - StandardTest / QCTest → Incubation
        - ReadOnly → Measure
        """

        select_menu = self._get_select_menu()

        if select_menu in ("StandardTest", "QCTest"):
            # InsertDevice → Incubation
            self.switch_to_incubation_view()

        elif select_menu == "ReadOnly":
            # InsertDevice → Measure
            self.switch_to_measure_view()

        else:
            raise ValueError(f"Unknown Select Menu: {select_menu}")


    #==========================================
    # --- 배터리 상태 확인 및 UART 을 위해 ---
    #========================================== 
    def _set_active_uart_view(self, view):
        """
        현재 화면에 보이는 View만 UART 옵저버로 유지
        """
        print(f"[UIController] set active uart view: {view.__class__.__name__}")

        # 기존 observer 제거
        if self._active_uart_view:
            self.backend_controller.uart_model.remove_observer(self._active_uart_view)

        self._active_uart_view = view
        self.backend_controller.uart_model.add_observer(view)

        # 🔥🔥🔥 핵심 추가 🔥🔥🔥
        battery_info = self.backend_controller.uart_model.get_battery_info()
        if battery_info and hasattr(view, "on_uart_event"):
            print("[UIController] push cached battery info to new view")
            view.on_uart_event("battery_changed", battery_info)


    def on_uart_event(self, event_type: str, data):
        """
        UIController 레벨에서 전역 UART 이벤트 처리
        """
        print(f"[UIController] on_uart_event:{event_type}")

        # =========================
        # 🔋 Battery
        # =========================
        if event_type == "battery_changed":
            level = data.level
            if level <= 20:
                self.low_battery_overlay.show_warning()
            else:
                self.low_battery_overlay.hide_warning()

        # =========================
        # ⚡ Power
        # =========================
        elif event_type == "power_status_changed":
            if data.name == "ON":
                self.power_status_overlay.show_on()
            else:
                self.power_status_overlay.show_off()

        """ 추후 필요하면 사용
        # =========================
        # 🔌 Slot
        # =========================
        elif event_type == "slot_status_changed":
            if data.name == "IN":
                self.slot_status_overlay.show_on()
            else:
                self.slot_status_overlay.show_off()

        # =========================
        # 🔌 USB
        # =========================
        elif event_type == "usb_status_changed":
            if data.name == "CONNECTED":
                self.usb_status_overlay.show_connected()
            else:
                self.usb_status_overlay.show_disconnected()
        """
        
