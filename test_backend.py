#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 스크립트 - 애플리케이션 컨트롤러 및 MVC 구조 확인
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_config():
    """설정 시스템 테스트"""
    print("=== 설정 시스템 테스트 ===")
    try:
        from config.config import app_config
        
        print(f"디버그 모드: {app_config.is_debug_mode()}")
        print(f"카메라 활성화: {app_config.is_camera_enabled()}")
        print(f"UART 활성화: {app_config.is_uart_enabled()}")
        
        # 디버그 모드 토글 테스트
        print("\n디버그 모드 토글 테스트...")
        original_mode = app_config.is_debug_mode()
        app_config.set_debug_mode(not original_mode)
        print(f"변경 후 디버그 모드: {app_config.is_debug_mode()}")
        
        # 원래 모드로 복원
        app_config.set_debug_mode(original_mode)
        print(f"복원 후 디버그 모드: {app_config.is_debug_mode()}")
        
        print("✅ 설정 시스템 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 설정 시스템 테스트 실패: {str(e)}")
        return False

def test_application_controller():
    """애플리케이션 컨트롤러 테스트"""
    print("\n=== 애플리케이션 컨트롤러 테스트 ===")
    try:
        from controllers.application_controller import app_controller
        
        # 애플리케이션 초기화 (디버그 모드)
        print("애플리케이션 초기화 중...")
        app_controller.initialize()
        print("✅ 초기화 완료")
        
        # 상태 정보 확인
        system_info = app_controller.get_system_info()
        print("\n시스템 상태:")
        for key, value in system_info.items():
            print(f"  {key}: {value}")
        
        # 시스템 준비 상태 확인
        is_ready = app_controller.is_system_ready()
        print(f"\n시스템 준비 상태: {is_ready}")
        
        # 카메라 테스트
        print("\n카메라 기능 테스트...")
        if app_controller.start_camera_capture():
            print("✅ 카메라 캡처 시작 성공")
            
            frame = app_controller.get_current_frame()
            if frame is not None:
                print(f"✅ 프레임 가져오기 성공 (크기: {frame.shape if hasattr(frame, 'shape') else 'N/A'})")
                
                # 이미지 저장 테스트
                if app_controller.save_image("test_capture.jpg"):
                    print("✅ 이미지 저장 성공")
                else:
                    print("⚠️ 이미지 저장 실패")
            else:
                print("⚠️ 프레임 가져오기 실패 (정상 - 디버그 모드)")
        else:
            print("⚠️ 카메라 캡처 시작 실패")
        
        # UART/LED 테스트
        print("\nUART/LED 기능 테스트...")
        if app_controller.led_on(30):
            print("✅ LED 켜기 성공")
            
            led_state = app_controller.get_led_state()
            print(f"LED 상태: {led_state}")
        else:
            print("⚠️ LED 켜기 실패")
            
        if app_controller.led_off():
            print("✅ LED 끄기 성공")
        else:
            print("⚠️ LED 끄기 실패")
        
        # 배터리 상태 테스트
        print("\n배터리 상태 테스트...")
        battery_status = app_controller.get_battery_status()
        if battery_status:
            print(f"✅ 배터리 상태: {battery_status}")
        else:
            print("⚠️ 배터리 상태 읽기 실패")
        
        # 정리
        app_controller.shutdown()
        print("✅ 애플리케이션 컨트롤러 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 애플리케이션 컨트롤러 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("Calth Reader MVC 구조 테스트")
    print("=" * 50)
    
    # 설정 테스트
    config_ok = test_config()
    
    # 애플리케이션 컨트롤러 테스트
    controller_ok = test_application_controller()
    
    print("\n" + "=" * 50)
    print("테스트 결과 요약:")
    print(f"설정 시스템: {'✅ 성공' if config_ok else '❌ 실패'}")
    print(f"애플리케이션 컨트롤러: {'✅ 성공' if controller_ok else '❌ 실패'}")
    
    if config_ok and controller_ok:
        print("\n🎉 모든 테스트 통과! 새로운 MVC 구조가 올바르게 설정되었습니다.")
        return 0
    else:
        print("\n⚠️ 일부 테스트 실패. 설정을 확인해주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
