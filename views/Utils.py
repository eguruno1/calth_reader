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
    if not hasattr(view, 'date_time_timer'):
        view.date_time_timer = QTimer(view)
        view.date_time_timer.timeout.connect(lambda: update_date_time(view))
    view.date_time_timer.start(1000)  # 1초마다 업데이트

def stop_date_time_update(view):
    if hasattr(view, 'date_time_timer'):
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
