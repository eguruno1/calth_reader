import os

from PyQt5.QtCore       import QDateTime, QTimer, QDate
from PyQt5.QtGui        import QFontDatabase, QFont
from PyQt5.QtWidgets    import QApplication


################################################################################
# 시간 업데이트
################################################################################

def update_date_time(view):
    current_datetime = QDateTime.currentDateTime()
    formatted_datetime = current_datetime.toString("yyyy-MM-dd  HH:mm")
    if hasattr(view, 'label_DateNClock'):
        view.label_DateNClock.setText(formatted_datetime)

def set_current_date(view):
    current_date = QDate.currentDate().toString("yyyy-MM-dd")
    if hasattr(view, 'label_Input_Date'):
        view.label_Input_Date.setText(current_date)
    if hasattr(view, 'lineEdit_label_Input_Date'):
        view.lineEdit_label_Input_Date.setText(current_date)

def start_date_time_update(view):
    update_date_time(view)
    if not hasattr(view, 'date_time_timer') or view.date_time_timer is None:
        view.date_time_timer = QTimer(view)
        view.date_time_timer.timeout.connect(lambda: update_date_time(view))
    
    if not view.date_time_timer.isActive():
        view.date_time_timer.start(1000)  # 1초마다 업데이트

def stop_date_time_update(view):
    if hasattr(view, 'date_time_timer') and view.date_time_timer is not None:
        view.date_time_timer.stop()


################################################################################
# 폰트 설정
################################################################################

def set_app_font():
    # 프로젝트 루트 디렉토리 경로 (PyCalth_Qt5 폴더)
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 폰트 파일 경로
    font_path = os.path.join(base_path, 'fonts', 'Pretendard-Regular.ttf')
    
    #print(f"폰트 파일 경로: {font_path}")  # 디버깅을 위한 출력
    
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app_font = QFont(font_family)
            app_font.setPointSize(10)  # 원하는 폰트 크기로 설정
            QApplication.setFont(app_font)
            #print(f"폰트 '{font_family}'가 성공적으로 로드되었습니다.")
        else:
            print("폰트 로딩에 실패했습니다.")
    else:
        print(f"폰트 파일을 찾을 수 없습니다: {font_path}")
        print(f"현재 디렉토리: {os.getcwd()}")  # 현재 작업 디렉토리 출력
        
        # fonts 폴더 내용 출력
        fonts_dir = os.path.join(base_path, 'fonts')
        if os.path.exists(fonts_dir):
            print("fonts 폴더의 내용:")
            for item in os.listdir(fonts_dir):
                print(f"  {item}")
        else:
            print(f"fonts 폴더를 찾을 수 없습니다: {fonts_dir}")


################################################################################
# 배터리 상태 업데이트
################################################################################

def update_battery_status(view):
    """배터리 상태 업데이트"""
    try:
        from controllers import app_controller
        
        # 컨트롤러를 통해 배터리 상태 읽기
        battery_data = app_controller.get_battery_status()
        
        if battery_data:
            level = battery_data.get('level', 50)
            is_charging = battery_data.get('is_charging', False)
            
            # 배터리 레벨 텍스트 업데이트
            if hasattr(view, 'label_BatteryGuage'):
                if is_charging:
                    view.label_BatteryGuage.setText(f"{level}%⚡")
                else:
                    view.label_BatteryGuage.setText(f"{level}%")
            
            # 배터리 아이콘 업데이트 (View에 아이콘 라벨이 있는 경우)
            if hasattr(view, 'label_4') or hasattr(view, 'label_9') or hasattr(view, 'label_battery_icon'):
                icon_name = get_battery_icon_name(level, is_charging)
                set_battery_icon(view, icon_name)
                
            print(f"배터리 상태 업데이트: {level}% (충전중: {is_charging})")
        else:
            print("배터리 상태를 읽을 수 없습니다.")
            # 기본값으로 설정
            if hasattr(view, 'label_BatteryGuage'):
                view.label_BatteryGuage.setText("100%")
            
    except Exception as e:
        print(f"배터리 상태 업데이트 오류: {e}")
        # 오류 발생 시 기본값으로 설정
        if hasattr(view, 'label_BatteryGuage'):
            view.label_BatteryGuage.setText("100%")

def get_battery_icon_name(level, is_charging=False):
    """배터리 레벨에 따른 아이콘 파일명 반환"""
    if is_charging:
        return "Battery_Icon-charging.png"
    
    if level >= 90:
        return "Battery_Icon-100.png"
    elif level >= 75:
        return "Battery_Icon-075.png"
    elif level >= 50:
        return "Battery_Icon-050.png"
    elif level >= 25:
        return "Battery_Icon-025.png"
    else:
        return "Battery_Icon-000.png"

def set_battery_icon(view, icon_filename):
    """배터리 아이콘 설정"""
    try:
        from PyQt5.QtGui import QPixmap
        
        # 프로젝트 루트에서 이미지 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        icon_path = os.path.join(project_root, 'ui', 'image', 'Icon', icon_filename)
        
        # View에 따라 다른 아이콘 라벨 확인
        icon_label = None
        if hasattr(view, 'label_4'):  # HomeView
            icon_label = view.label_4
        elif hasattr(view, 'label_9'):  # SettingsView
            icon_label = view.label_9
        elif hasattr(view, 'label_battery_icon'):  # 다른 View들
            icon_label = view.label_battery_icon
            
        if icon_label and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap)
            print(f"배터리 아이콘 변경: {icon_filename}")
        else:
            if not icon_label:
                print("배터리 아이콘 라벨을 찾을 수 없습니다.")
            else:
                print(f"배터리 아이콘 파일 없음: {icon_path}")
                
    except Exception as e:
        print(f"배터리 아이콘 설정 오류: {e}")

def start_battery_update(view):
    """배터리 상태 주기적 업데이트 시작"""
    update_battery_status(view)
    if not hasattr(view, 'battery_timer') or view.battery_timer is None:
        view.battery_timer = QTimer(view)
        view.battery_timer.timeout.connect(lambda: update_battery_status(view))
    
    if not view.battery_timer.isActive():
        view.battery_timer.start(10000)  # 10초마다 업데이트

def stop_battery_update(view):
    """배터리 상태 업데이트 중지"""
    if hasattr(view, 'battery_timer') and view.battery_timer is not None:
        view.battery_timer.stop()
