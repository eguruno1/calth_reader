#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QC 로그인 플로우 테스트
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controllers.ui_controller import AppController
from controllers import app_controller

def test_qc_login_flow():
    """QC 로그인 플로우 테스트"""
    app = QApplication(sys.argv)
    
    # UI Controller 생성 및 표시
    controller = AppController()
    controller.show()
    
    print("=== QC 로그인 플로우 테스트 ===")
    print("1. 애플리케이션이 시작되었습니다.")
    print("2. HomeView에서 QC Test 버튼을 클릭해보세요.")
    print("3. 로그인 페이지에서 다음 계정으로 로그인해보세요:")
    print("   - Admin: admin / admin123")
    print("   - Operator: operator1 / op123")
    print("4. 로그인 후 QC Test로 바로 진입하는지 확인하세요.")
    print("5. 홈 화면의 로그인 버튼이 사용자 ID로 변경되는지 확인하세요.")
    
    # 자동 테스트를 위한 함수들
    def auto_test_login():
        """자동 로그인 테스트"""
        print("\n--- 자동 로그인 테스트 시작 ---")
        
        # Admin으로 로그인
        result = app_controller.user_service.login('admin', 'admin123')
        if result:
            print("✓ Admin 로그인 성공")
            print(f"✓ 홈 버튼 텍스트: {controller.home_view.pushButton_Statistics.text()}")
        else:
            print("✗ Admin 로그인 실패")
        
        # 3초 후 로그아웃
        QTimer.singleShot(3000, lambda: [
            app_controller.user_service.logout(),
            print("✓ 로그아웃 완료"),
            print(f"✓ 홈 버튼 텍스트: {controller.home_view.pushButton_Statistics.text()}")
        ])
    
    # 5초 후 자동 테스트 실행
    QTimer.singleShot(5000, auto_test_login)
    
    return app.exec_()

if __name__ == "__main__":
    test_qc_login_flow()
