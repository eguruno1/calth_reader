# -*- coding: utf-8 -*-
"""
Date and Time Settings View - 날짜 및 시간 설정 화면
"""
import os
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QDateTime
from PyQt5.QtGui import QFont
from PyQt5 import uic

from views.Utils import update_date_time, start_date_time_update, stop_date_time_update, get_time_service
from services.time_service import TimeService


class DateTimeSettingsView(QMainWindow):
    """날짜 및 시간 설정 화면"""
    
    switch_to_settings = pyqtSignal()  # 설정 화면으로 돌아가기

    def __init__(self, parent=None):
        super().__init__(parent)
        self.time_service = TimeService()
        
        # 프로젝트 루트 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정
        ui_filename = 'DateTimeSettingsViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Settings', ui_filename)
        
        # UI 파일 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
        self.init_ui()
        self.load_current_settings()

    def init_ui(self):
        """UI 초기화 및 이벤트 연결"""
        # UTC 오프셋 목록 추가
        for display_name, offset in self.time_service.get_utc_offset_list():
            self.combo_utc_offset.addItem(display_name, offset)
        
        # 커스텀 날짜/시간 편집기에 현재 시간 설정
        self.datetime_custom.setDateTime(QDateTime.currentDateTime())
        
        # 뒤로 가기 버튼 연결
        self.pushButton_BackArrow.clicked.connect(self.on_back_button_clicked)
        
        # 라디오 버튼 이벤트 연결
        self.radio_system_time.toggled.connect(self.on_time_source_changed)
        self.radio_utc_time.toggled.connect(self.on_time_source_changed)
        self.radio_custom_time.toggled.connect(self.on_time_source_changed)
        
        # 액션 버튼 이벤트 연결
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        
        # 시간 서비스 이벤트 연결
        self.time_service.time_setting_changed.connect(self.on_time_setting_changed)
        self.time_service.error_occurred.connect(self.on_error_occurred)
        
        # 현재 시간 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_current_time_display)
        self.update_timer.start(1000)  # 1초마다 업데이트
        
        # 초기 날짜와 시간 설정
        self.update_date_time()

    def load_current_settings(self):
        """현재 설정 로드"""
        try:
            # 현재 시간 모드 가져오기
            current_mode = self.time_service.get_time_mode()
            
            if current_mode == self.time_service.TIME_MODE_SYSTEM:
                self.radio_system_time.setChecked(True)
            elif current_mode == self.time_service.TIME_MODE_UTC:
                self.radio_utc_time.setChecked(True)
                # UTC 오프셋 설정
                current_offset = self.time_service.get_utc_offset()
                for i in range(self.combo_utc_offset.count()):
                    if self.combo_utc_offset.itemData(i) == current_offset:
                        self.combo_utc_offset.setCurrentIndex(i)
                        break
            elif current_mode == self.time_service.TIME_MODE_CUSTOM:
                self.radio_custom_time.setChecked(True)
                # 커스텀 시간 설정
                custom_time = self.time_service.get_custom_datetime()
                if custom_time:
                    qt_datetime = QDateTime.fromSecsSinceEpoch(int(custom_time.timestamp()))
                    self.datetime_custom.setDateTime(qt_datetime)
            
            # UI 상태 업데이트
            self.on_time_source_changed()
            
        except Exception as e:
            print(f"설정 로드 실패: {e}")

    def on_time_source_changed(self):
        """시간 소스 변경 시 UI 업데이트"""
        # UTC 콤보박스 활성화/비활성화
        self.combo_utc_offset.setEnabled(self.radio_utc_time.isChecked())
        
        # 커스텀 날짜/시간 편집 활성화/비활성화
        self.datetime_custom.setEnabled(self.radio_custom_time.isChecked())
        
        # 현재 시간 표시 업데이트
        self.update_current_time_display()

    def update_current_time_display(self):
        """현재 시간 표시 업데이트"""
        try:
            if self.radio_system_time.isChecked():
                current_time = datetime.now()
                mode_text = "시스템 시간"
            elif self.radio_utc_time.isChecked():
                offset = self.combo_utc_offset.currentData()
                from datetime import timedelta
                current_time = datetime.utcnow() + timedelta(hours=offset)
                mode_text = f"UTC{'+' if offset >= 0 else ''}{offset}"
            elif self.radio_custom_time.isChecked():
                qt_datetime = self.datetime_custom.dateTime()
                current_time = datetime.fromtimestamp(qt_datetime.toSecsSinceEpoch())
                mode_text = "커스텀 시간"
            else:
                current_time = datetime.now()
                mode_text = "시스템 시간"
            
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            self.label_current_time.setText(f"현재 시간 ({mode_text}): {time_str}")
            
        except Exception as e:
            print(f"시간 표시 업데이트 실패: {e}")

    def on_apply_clicked(self):
        """적용 버튼 클릭"""
        try:
            success = False
            
            if self.radio_system_time.isChecked():
                success = self.time_service.set_time_mode(self.time_service.TIME_MODE_SYSTEM)
                
            elif self.radio_utc_time.isChecked():
                # UTC 모드 설정
                success = self.time_service.set_time_mode(self.time_service.TIME_MODE_UTC)
                if success:
                    # UTC 오프셋 설정
                    offset = self.combo_utc_offset.currentData()
                    success = self.time_service.set_utc_offset(offset)
                    
            elif self.radio_custom_time.isChecked():
                # 커스텀 모드 설정
                success = self.time_service.set_time_mode(self.time_service.TIME_MODE_CUSTOM)
                if success:
                    # 커스텀 시간 설정
                    qt_datetime = self.datetime_custom.dateTime()
                    custom_time = datetime.fromtimestamp(qt_datetime.toSecsSinceEpoch())
                    success = self.time_service.set_custom_datetime(custom_time)
            
            if success:
                # 전역 시간 서비스 인스턴스도 업데이트
                global_time_service = get_time_service()
                # Utils.py의 전역 인스턴스와 현재 인스턴스가 다를 수 있으므로 동기화
                if global_time_service != self.time_service:
                    # 설정을 다시 로드하여 동기화
                    global_time_service.settings_service.load_settings()
                
                QMessageBox.information(self, "성공", "시간 설정이 적용되었습니다.")
            else:
                QMessageBox.warning(self, "실패", "시간 설정 적용에 실패했습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 적용 중 오류가 발생했습니다: {e}")

    def on_time_setting_changed(self, setting):
        """시간 설정 변경 시그널 처리"""
        print(f"시간 설정 변경됨: {setting}")
        self.update_current_time_display()

    def on_error_occurred(self, error):
        """에러 발생 시그널 처리"""
        QMessageBox.critical(self, "오류", f"시간 서비스 오류: {error}")

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: start_date_time_update(self))

    def closeEvent(self, event):
        stop_date_time_update(self)
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        super().closeEvent(event)

    def on_back_button_clicked(self):
        """뒤로 가기 버튼 클릭"""
        self.switch_to_settings.emit()

    def update_date_time(self):
        """날짜/시간 업데이트 (헤더용)"""
        update_date_time(self)
