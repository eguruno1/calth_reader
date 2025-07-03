#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 스크립트 - 백엔드 매니저 및 설정 확인
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

def test_backend_manager():
    """백엔드 매니저 테스트"""
    print("\n=== 백엔드 매니저 테스트 ===")
    try:
        from backend.backend_manager import backend_manager
        
        # 백엔드 초기화 (디버그 모드)
        print("백엔드 초기화 중...")
        success = backend_manager.initialize_all()
        print(f"초기화 결과: {success}")
        
        # 상태 정보 확인
        status = backend_manager.get_status_info()
        print("\n시스템 상태:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # 카메라 테스트
        print("\n카메라 기능 테스트...")
        if backend_manager.start_camera_capture():
            print("✅ 카메라 캡처 시작 성공")
            
            frame = backend_manager.get_current_frame()
            if frame is not None:
                print(f"✅ 프레임 가져오기 성공 (크기: {frame.shape if hasattr(frame, 'shape') else 'N/A'})")
            else:
                print("⚠️ 프레임 가져오기 실패 (정상 - 디버그 모드)")
        else:
            print("⚠️ 카메라 캡처 시작 실패")
        
        # UART 테스트
        print("\nUART 기능 테스트...")
        if backend_manager.led_on(30):
            print("✅ LED 켜기 성공")
        else:
            print("⚠️ LED 켜기 실패")
            
        if backend_manager.led_off():
            print("✅ LED 끄기 성공")
        else:
            print("⚠️ LED 끄기 실패")
        
        # 정리
        backend_manager.shutdown()
        print("✅ 백엔드 매니저 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 백엔드 매니저 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("Calth Reader 백엔드 구조 테스트")
    print("=" * 50)
    
    # 설정 테스트
    config_ok = test_config()
    
    # 백엔드 매니저 테스트
    backend_ok = test_backend_manager()
    
    print("\n" + "=" * 50)
    print("테스트 결과 요약:")
    print(f"설정 시스템: {'✅ 성공' if config_ok else '❌ 실패'}")
    print(f"백엔드 매니저: {'✅ 성공' if backend_ok else '❌ 실패'}")
    
    if config_ok and backend_ok:
        print("\n🎉 모든 테스트 통과! 프로젝트 구조가 올바르게 설정되었습니다.")
        return 0
    else:
        print("\n⚠️ 일부 테스트 실패. 설정을 확인해주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
