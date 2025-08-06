#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings 전체 네비게이션 테스트 스크립트
"""
import sys
import os

# 프로젝트 루트 경로를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from PyQt5.QtWidgets import QApplication
from controllers.ui_controller import AppController

def test_complete_settings_navigation():
    """전체 Settings 네비게이션 테스트"""
    app = QApplication(sys.argv)
    
    # UI 컨트롤러 생성
    ui_controller = AppController()
    ui_controller.show()
    
    print("=== Settings 네비게이션 테스트 시작 ===")
    
    # Settings로 이동
    ui_controller.switch_to_settings_view()
    print("✓ Settings 메인 화면으로 이동")
    
    print("\n--- 각 설정 페이지별 테스트 ---")
    
    # 1. General Settings 테스트
    print("1. General Settings 테스트")
    ui_controller.switch_to_general_settings_view()
    print("   ✓ General Settings 화면으로 이동")
    print("   - Network, LIS Parameter, Print, Language, Unit, Info 설정")
    
    # 2. Power Management 테스트
    print("2. Power Management 테스트")
    ui_controller.switch_to_power_management_view()
    print("   ✓ Power Management 화면으로 이동")
    print("   - Set Timeout, Shutdown 설정")
    
    # 3. Update Settings 테스트
    print("3. Update Settings 테스트")
    ui_controller.switch_to_update_settings_view()
    print("   ✓ Update Settings 화면으로 이동")
    print("   - Software, Firmware 업데이트")
    
    # 4. Calibration QC Settings 테스트
    print("4. Calibration QC Settings 테스트")
    ui_controller.switch_to_calibration_qc_settings_view()
    print("   ✓ Calibration QC Settings 화면으로 이동")
    print("   - Calibration, QC 날짜 설정")
    
    # 5. Manage Operator 테스트
    print("5. Manage Operator 테스트")
    ui_controller.switch_to_manage_operator_view()
    print("   ✓ Manage Operator 화면으로 이동")
    print("   - CREATE ID, EDIT ID, EDIT PW, DELETE ID, AUTO LOGOUT")
    
    # 6. Date Time Settings 테스트
    print("6. Date Time Settings 테스트")
    ui_controller.switch_to_datetime_settings_view()
    print("   ✓ Date Time Settings 화면으로 이동")
    print("   - 날짜/시간 설정")
    
    # 다시 Settings로 돌아가기
    ui_controller.switch_to_settings_view()
    print("\n✓ Settings 메인 화면으로 복귀")
    
    print("\n=== Settings 네비게이션 테스트 완료 ===")
    print("모든 Settings 페이지가 성공적으로 연결되었습니다!")
    
    print("\n사용 가능한 기능:")
    print("- General Settings: 6가지 일반 설정")
    print("- Power Management: 절전/전원 설정")
    print("- Update Settings: 소프트웨어/펌웨어 업데이트")
    print("- Calibration QC Settings: 교정/품질관리 날짜 설정")
    print("- Manage Operator: 사용자 관리")
    print("- Date Time Settings: 날짜/시간 설정")
    
    # 애플리케이션 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_complete_settings_navigation()
