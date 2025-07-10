#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MVC 구조 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_mvc_structure():
    """MVC 구조 테스트"""
    print("=== MVC 구조 테스트 ===")
    try:
        # Models 테스트
        from models import CameraModel, UARTModel, ApplicationModel
        print("✅ Models 임포트 성공")
        
        # Services 테스트
        from services import CameraService, UARTService
        print("✅ Services 임포트 성공")
        
        # Controllers 테스트
        from controllers import ApplicationController, MeasurementController
        print("✅ Controllers 임포트 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ MVC 구조 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """모델 테스트"""
    print("\n=== 모델 테스트 ===")
    try:
        from models import CameraModel, UARTModel, ApplicationModel, SystemStatus
        
        # 애플리케이션 모델 테스트
        app_model = ApplicationModel()
        print(f"초기 디버그 모드: {app_model.settings.debug_mode}")
        
        app_model.set_debug_mode(False)
        print(f"변경 후 디버그 모드: {app_model.settings.debug_mode}")
        
        app_model.set_system_status(SystemStatus.READY)
        print(f"시스템 상태: {app_model.system_info.status.value}")
        
        # 카메라 모델 테스트
        camera_model = CameraModel()
        camera_model.set_initialized(True)
        print(f"카메라 초기화 상태: {camera_model.is_initialized}")
        
        # UART 모델 테스트
        uart_model = UARTModel()
        led_control = uart_model.set_led_brightness(30)
        print(f"LED 밝기 설정: {led_control.brightness}, 상태: {led_control.state.name}")
        
        print("✅ 모델 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 모델 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_controllers():
    """컨트롤러 테스트"""
    print("\n=== 컨트롤러 테스트 ===")
    try:
        from controllers import app_controller, measurement_controller
        
        # 애플리케이션 컨트롤러 테스트
        system_info = app_controller.get_system_info()
        print("시스템 정보 조회 성공")
        print(f"  - 모드: {system_info['app_status']['mode']}")
        print(f"  - 상태: {system_info['app_status']['status']}")
        
        # 측정 컨트롤러 테스트
        progress_info = measurement_controller.get_current_progress()
        print(f"측정 진행률: {progress_info['progress']}%")
        print(f"현재 단계: {progress_info['current_phase']}")
        print(f"측정 중: {progress_info['is_measuring']}")
        
        print("✅ 컨트롤러 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 컨트롤러 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """설정 테스트"""
    print("\n=== 설정 테스트 ===")
    try:
        from config.config import app_config
        
        print(f"디버그 모드: {app_config.is_debug_mode()}")
        print(f"카메라 활성화: {app_config.is_camera_enabled()}")
        print(f"UART 활성화: {app_config.is_uart_enabled()}")
        
        # 디버그 모드 토글 테스트
        original_mode = app_config.is_debug_mode()
        app_config.set_debug_mode(not original_mode)
        print(f"토글 후 디버그 모드: {app_config.is_debug_mode()}")
        
        # 원래 상태로 복원
        app_config.set_debug_mode(original_mode)
        print(f"복원 후 디버그 모드: {app_config.is_debug_mode()}")
        
        print("✅ 설정 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 설정 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("Calth Reader MVC 구조 테스트")
    print("=" * 60)
    
    # 구조 테스트
    mvc_ok = test_mvc_structure()
    
    # 모델 테스트
    models_ok = test_models()
    
    # 컨트롤러 테스트
    controllers_ok = test_controllers()
    
    # 설정 테스트
    config_ok = test_config()
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print(f"MVC 구조: {'✅ 성공' if mvc_ok else '❌ 실패'}")
    print(f"모델: {'✅ 성공' if models_ok else '❌ 실패'}")
    print(f"컨트롤러: {'✅ 성공' if controllers_ok else '❌ 실패'}")
    print(f"설정: {'✅ 성공' if config_ok else '❌ 실패'}")
    
    if mvc_ok and models_ok and controllers_ok and config_ok:
        print("\n🎉 모든 MVC 구조 테스트 통과!")
        print("💡 완전한 애플리케이션 실행을 위해서는 PyQt5 설치가 필요합니다:")
        print("   pip install PyQt5")
        return 0
    else:
        print("\n⚠️ 일부 테스트 실패. MVC 구조를 확인해주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
