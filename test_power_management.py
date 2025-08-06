#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerManagementView 테스트 스크립트
"""
import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from PyQt5.QtWidgets import QApplication
from controllers.ui_controller import AppController

def test_power_management_navigation():
    """Power Management 네비게이션 테스트"""
    app = QApplication(sys.argv)
    
    # UI 컨트롤러 생성
    ui_controller = AppController()
    ui_controller.show()
    
    # Settings로 이동
    ui_controller.switch_to_settings_view()
    print("Settings 화면으로 이동")
    
    # Power Management로 이동
    ui_controller.switch_to_power_management_view()
    print("Power Management 화면으로 이동")
    
    print("Power Management View 테스트 시작")
    print("1. Set Timeout 버튼 - 절전 시간 설정")
    print("2. Shutdown 버튼 - 시스템 종료")
    print("3. Reset 버튼 - 설정 초기화")
    print("4. Apply 버튼 - 설정 저장")
    print("5. Back 버튼 - Settings로 돌아가기")
    
    # 애플리케이션 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_power_management_navigation()
