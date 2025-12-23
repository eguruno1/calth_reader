#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
권한 기반 UI 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_permission_system():
    """권한 시스템 테스트"""
    print("=== 권한 기반 UI 시스템 테스트 ===")
    
    try:
        # from controllers.application_controller import app_controller
        from controllers import app_controller
        from models.user_model import UserRole
        
        # 애플리케이션 초기화
        app_controller.initialize()
        
        # 1. 비로그인 상태 테스트
        print("\n1. 비로그인 상태 테스트:")
        print(f"  - 로그인 상태: {app_controller.user_service.is_logged_in()}")
        print(f"  - Admin 권한: {app_controller.user_service.has_permission(UserRole.ADMIN)}")
        print(f"  - Operator 권한: {app_controller.user_service.has_permission(UserRole.OPERATOR)}")
        print(f"  - Viewer 권한: {app_controller.user_service.has_permission(UserRole.VIEWER)}")
        
        # 2. Admin 계정 로그인 테스트
        print("\n2. Admin 계정 로그인 테스트:")
        admin_login = app_controller.user_service.login("admin", "admin123")
        print(f"  - 로그인 성공: {admin_login}")
        if admin_login:
            user = app_controller.user_service.get_current_user()
            print(f"  - 사용자: {user.name} ({user.role.value})")
            print(f"  - Admin 권한: {app_controller.user_service.has_permission(UserRole.ADMIN)}")
            print(f"  - Operator 권한: {app_controller.user_service.has_permission(UserRole.OPERATOR)}")
            print(f"  - Viewer 권한: {app_controller.user_service.has_permission(UserRole.VIEWER)}")
        
        # 3. Operator 계정 로그인 테스트
        print("\n3. Operator 계정 로그인 테스트:")
        app_controller.user_service.logout()
        operator_login = app_controller.user_service.login("operator1", "op123")
        print(f"  - 로그인 성공: {operator_login}")
        if operator_login:
            user = app_controller.user_service.get_current_user()
            print(f"  - 사용자: {user.name} ({user.role.value})")
            print(f"  - Admin 권한: {app_controller.user_service.has_permission(UserRole.ADMIN)}")
            print(f"  - Operator 권한: {app_controller.user_service.has_permission(UserRole.OPERATOR)}")
            print(f"  - Viewer 권한: {app_controller.user_service.has_permission(UserRole.VIEWER)}")
        
        # 4. Viewer 계정 로그인 테스트
        print("\n4. Viewer 계정 로그인 테스트:")
        app_controller.user_service.logout()
        viewer_login = app_controller.user_service.login("viewer1", "view123")
        print(f"  - 로그인 성공: {viewer_login}")
        if viewer_login:
            user = app_controller.user_service.get_current_user()
            print(f"  - 사용자: {user.name} ({user.role.value})")
            print(f"  - Admin 권한: {app_controller.user_service.has_permission(UserRole.ADMIN)}")
            print(f"  - Operator 권한: {app_controller.user_service.has_permission(UserRole.OPERATOR)}")
            print(f"  - Viewer 권한: {app_controller.user_service.has_permission(UserRole.VIEWER)}")
        
        # 정리
        app_controller.user_service.logout()
        app_controller.shutdown()
        
        print("\n✅ 권한 시스템 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 권한 시스템 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_permission_system()
