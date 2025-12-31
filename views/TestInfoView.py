import os
import json
from datetime import datetime

from PyQt5.QtWidgets import QMainWindow, QLineEdit, QWidget, QLabel, QMessageBox
from PyQt5.QtCore    import pyqtSignal, QPoint, QRect, QEvent, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui     import QResizeEvent
from PyQt5           import uic

from views.Utils     import set_current_date, update_date_time, start_date_time_update, stop_date_time_update, start_battery_update, stop_battery_update, update_battery_status
from views.VKeyboard import VKeyboard
from controllers import app_controller

class TestInfoView(QMainWindow):
    switch_to_select  = pyqtSignal()  
    switch_to_measure = pyqtSignal()  

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.load_ui()
        self.init_ui()
        self.widgets_moved = False
        self.selected_test_type = ""
        self.setup_virtual_keyboard()
        self.installEventFilter(self)
        self.keyboard_animation = None

        # JSON 파일 경로 설정
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        self.current_json_path = os.path.join(project_root, 'info', 'current.json')
        self.load_operator_from_json()

    def load_ui(self):
        # 프로젝트 루트 디렉토리
        current_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # UI 파일 경로 설정 (대소문자 구분 없이)
        ui_filename = 'TestInfoViewWindow.ui'
        ui_file = os.path.join(project_root, 'ui', 'Test', ui_filename)
        
        # 파일 존재 여부 확인 및 로드
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        else:
            raise FileNotFoundError(f"UI file not found: {ui_file}")
        
    def init_ui(self):
        set_current_date(self)
        
        # Back Arrow 버튼 연결
        self.pushButton_TestInfoBackArrow.clicked.connect(self.on_back_button_clicked)

        # OK 버튼 연결
        self.pushButton_TestInfoOK.clicked.connect(self.on_testinfok_button_clicked)

        # lineEdit 위젯 설정
        self.setup_line_edits()

        # label_NOTE1 찾기
        self.label_NOTE1 = self.findChild(QLabel, "label_NOTE1")
        if not self.label_NOTE1:
            print("Warning: label_NOTE1 not found")

        self.update_date_time()
        
        # 배터리 상태 초기화
        self.update_battery_status()

        # centralwidget 찾기
        self.central_widget = self.centralWidget()
        if not self.central_widget:
            print("Warning: centralwidget not found")

        # 이동하지 않을 위젯들의 이름 리스트
        self.static_widgets = [
            "pushButton_TestInfoBackArrow",
            "label",
            "label_DateNClock",
            "label_BatteryGuage",
            "label_2"
        ]

        # 원래 위치 저장
        self.original_positions = {}
        for child in self.central_widget.findChildren(QWidget):
            if child.objectName() not in self.static_widgets:
                self.original_positions[child] = child.pos()

    def setup_line_edits(self):
        self.lineEdit_Operator = self.findChild(QLineEdit, "lineEdit_Operator")
        self.lineEdit_PatientID = self.findChild(QLineEdit, "lineEdit_PatientID")
        self.current_line_edit = None

        if self.lineEdit_Operator:
            self.lineEdit_Operator.setFocus()
            self.lineEdit_Operator.installEventFilter(self)
        else:
            print("Warning: lineEdit_Operator not found")

        if self.lineEdit_PatientID:
            self.lineEdit_PatientID.installEventFilter(self)
        else:
            print("Warning: lineEdit_PatientID not found")

    def setup_virtual_keyboard(self):
        self.vkeyboard = VKeyboard(self)
        self.vkeyboard.hide()
        self.vkeyboard.key_pressed.connect(self.handle_key_press)
        self.vkeyboard.backspace_pressed.connect(self.handle_backspace)
        self.vkeyboard.hide_keyboard_signal.connect(self.hide_keyboard)
        self.vkeyboard.enter_pressed.connect(self.hide_keyboard)
        self.position_keyboard()

    def position_keyboard(self):
        keyboard_x = (self.width() - self.vkeyboard.width()) // 2
        keyboard_y = self.height()
        self.vkeyboard.move(keyboard_x, keyboard_y)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.position_keyboard()

    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and event.type() == QEvent.MouseButtonPress:
            self.show_virtual_keyboard(obj)
            return True
        elif event.type() == QEvent.MouseButtonPress:
            if not self.is_click_on_keyboard(event.globalPos()) and not self.is_click_on_line_edit(event.globalPos()):
                self.hide_keyboard()
                return True
        return super().eventFilter(obj, event)

    def is_click_on_keyboard(self, global_pos):
        if self.vkeyboard.isVisible():
            keyboard_rect = self.vkeyboard.geometry()
            keyboard_global_rect = QRect(self.mapToGlobal(keyboard_rect.topLeft()), 
                                         self.mapToGlobal(keyboard_rect.bottomRight()))
            return keyboard_global_rect.contains(global_pos)
        return False

    def is_click_on_line_edit(self, global_pos):
        for line_edit in [self.lineEdit_Operator, self.lineEdit_PatientID]:
            if line_edit.isVisible():
                line_edit_rect = line_edit.geometry()
                line_edit_global_rect = QRect(self.mapToGlobal(line_edit_rect.topLeft()), 
                                              self.mapToGlobal(line_edit_rect.bottomRight()))
                if line_edit_global_rect.contains(global_pos):
                    return True
        return False

    def show_virtual_keyboard(self, target_line_edit):
        self.current_line_edit = target_line_edit
        if self.keyboard_animation:
            self.keyboard_animation.stop()
        
        self.vkeyboard.show()
        start_y = self.height()
        end_y = self.height() - self.vkeyboard.height()
        
        self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
        self.keyboard_animation.setDuration(300)
        self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
        self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
        self.keyboard_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.keyboard_animation.start()
        
        self.move_widgets_up()

    def handle_key_press(self, key):
        if self.current_line_edit:
            if key == '\n':  # Enter key
                self.hide_keyboard()
            else:
                self.current_line_edit.insert(key)

    def handle_backspace(self):
        if self.current_line_edit:
            self.current_line_edit.backspace()

    def hide_keyboard(self):
        if not self.vkeyboard.isHidden():
            if self.keyboard_animation:
                self.keyboard_animation.stop()
            
            start_y = self.vkeyboard.y()
            end_y = self.height()
            
            self.keyboard_animation = QPropertyAnimation(self.vkeyboard, b"pos")
            self.keyboard_animation.setDuration(300)
            self.keyboard_animation.setStartValue(QPoint(self.vkeyboard.x(), start_y))
            self.keyboard_animation.setEndValue(QPoint(self.vkeyboard.x(), end_y))
            self.keyboard_animation.setEasingCurve(QEasingCurve.InCubic)
            self.keyboard_animation.finished.connect(self.vkeyboard.hide)
            self.keyboard_animation.finished.connect(self.reset_widget_positions)
            self.keyboard_animation.start()

    def move_widgets_up(self):
        if self.central_widget and not self.widgets_moved:
            move_distance = 110
            for child in self.central_widget.findChildren(QWidget):
                if child.objectName() not in self.static_widgets:
                    current_pos = child.pos()
                    new_pos = current_pos - QPoint(0, move_distance)
                    child.move(new_pos)
            self.widgets_moved = True

    def reset_widget_positions(self):
        if self.central_widget and self.widgets_moved:
            for child, original_pos in self.original_positions.items():
                child.move(original_pos)
            self.widgets_moved = False

    def on_back_button_clicked(self):
        self.reset_widget_positions()
        self.switch_to_select.emit()  # SelectView로 전환 시그널 발생

    def on_testinfok_button_clicked(self):
        """테스트 진단 시작"""
        operator = self.lineEdit_Operator.text() if self.lineEdit_Operator else ""
        patient_id = self.lineEdit_PatientID.text() if self.lineEdit_PatientID else ""
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create test data dictionary
        test_data = {
            'patient_id': patient_id,
            'operator': operator,
            'test_type': self.selected_test_type,
            'datetime': current_datetime
        }

        # Validate data
        if not patient_id or not operator:
            QMessageBox.warning(self, "Validation Error", 
                              "Please fill in all required fields (Patient ID, Operator)")
            return

        # Save test data
        self.update_json_file(operator, patient_id, current_datetime)
        
        # Proceed to measure view
        self.reset_widget_positions()
        self.switch_to_measure.emit()

    def update_json_file(self, operator, patient_id, datentime):
        """JSON 파일 업데이트 - 현재 로그인 사용자 정보 반영"""
        try:
            # current.json 파일을 읽어서 기존 데이터 유지하되, 새로운 데이터로 업데이트
            with open(self.current_json_path, 'r+') as f:
                data = json.load(f)
                
                # 현재 로그인한 사용자 정보가 있으면 사용, 없으면 전달받은 operator 사용
                if app_controller.user_service.is_logged_in():
                    current_user_id = app_controller.user_service.get_current_user_id()
                    data['operator'] = current_user_id
                else:
                    data['operator'] = operator if operator else "GUEST"
                
                data['patient_id'] = patient_id
                data['datentime'] = datentime
                
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            print("JSON 파일이 성공적으로 업데이트되었습니다.")
        except Exception as e:
            print(f"JSON 파일 업데이트 중 오류 발생: {e}")

    def update_date_time(self):
        update_date_time(self)
    
    def update_battery_status(self):
        update_battery_status(self)

    def set_selected_test_type(self, test_type):
        self.selected_test_type = test_type
        if self.label_NOTE1:
            # Simple test type display
            self.label_NOTE1.setText(f"Selected Test: {test_type}")
        else:
            print("Warning: Cannot set selected test type. label_NOTE1 not found.")

    def hide_keyboard(self):
        if not self.vkeyboard.isHidden():
            self.vkeyboard.hide()
            self.reset_widget_positions()

    def load_operator_from_json(self):
        """현재 로그인한 사용자 정보에서 Operator 설정"""
        try:
            # 현재 로그인한 사용자 정보 가져오기
            if app_controller.user_service.is_logged_in():
                current_user_id = app_controller.user_service.get_current_user_id()
                if self.lineEdit_Operator:
                    self.lineEdit_Operator.setText(current_user_id)
                else:
                    print("Warning: lineEdit_Operator not found")
            else:
                # 로그인되지 않은 경우 GUEST로 설정
                if self.lineEdit_Operator:
                    self.lineEdit_Operator.setText("GUEST")
                else:
                    print("Warning: lineEdit_Operator not found")
        except Exception as e:
            print(f"현재 사용자 정보 읽기 중 오류 발생: {e}")
            # 오류 발생 시 GUEST로 폴백
            if self.lineEdit_Operator:
                self.lineEdit_Operator.setText("GUEST")

    def showEvent(self, event):
        super().showEvent(event)
        self.load_operator_from_json()  # TestInfoView가 표시될 때마다 operator 정보를 새로 로드
        
        # 시간과 배터리 상태 업데이트 시작
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: start_date_time_update(self))
        QTimer.singleShot(100, lambda: start_battery_update(self))

        # TestInfoView가 표시될 때 lineEdit_PatientID에 포커스 설정
        if self.lineEdit_PatientID:
            self.lineEdit_PatientID.setFocus()
            self.show_virtual_keyboard(self.lineEdit_PatientID)
        else:
            print("Warning: lineEdit_PatientID not found when trying to set focus")

    def closeEvent(self, event):
        stop_date_time_update(self)
        stop_battery_update(self)
        super().closeEvent(event)