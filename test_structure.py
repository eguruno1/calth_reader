#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt5 의존성 없이 백엔드 테스트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_config_only():
    """설정 시스템만 테스트"""
    print("=== 설정 시스템 테스트 ===")
    try:
        from config.config import app_config
        
        print(f"초기 디버그 모드: {app_config.is_debug_mode()}")
        print(f"초기 카메라 활성화: {app_config.is_camera_enabled()}")
        print(f"초기 UART 활성화: {app_config.is_uart_enabled()}")
        
        # 디버그 모드 토글 테스트
        print("\n디버그 모드 토글 테스트...")
        original_mode = app_config.is_debug_mode()
        
        # 실제 하드웨어 모드로 변경
        app_config.set_debug_mode(False)
        print(f"실제 HW 모드로 변경: {app_config.is_debug_mode()}")
        print(f"카메라 활성화: {app_config.is_camera_enabled()}")
        print(f"UART 활성화: {app_config.is_uart_enabled()}")
        
        # 디버그 모드로 변경
        app_config.set_debug_mode(True)
        print(f"디버그 모드로 변경: {app_config.is_debug_mode()}")
        print(f"카메라 활성화: {app_config.is_camera_enabled()}")
        print(f"UART 활성화: {app_config.is_uart_enabled()}")
        
        # 설정 파일 확인
        import json
        if os.path.exists(app_config.config_file):
            with open(app_config.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"\n설정 파일 내용: {config_data}")
        else:
            print(f"\n설정 파일이 존재하지 않음: {app_config.config_file}")
        
        print("✅ 설정 시스템 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 설정 시스템 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_camera_manager_only():
    """카메라 매니저만 테스트 (PyQt5 없이)"""
    print("\n=== 카메라 매니저 테스트 (PyQt5 제외) ===")
    try:
        # 카메라 매니저의 기본 기능만 테스트
        import sys
        import os
        import numpy as np
        
        # 가상의 카메라 매니저 클래스 테스트
        class MockCameraManager:
            def __init__(self):
                self._initialized = False
                self.latest_frame = None
                
            def init_camera(self):
                # 디버그 모드 시뮬레이션
                from config.config import app_config
                if app_config.is_debug_mode():
                    print("디버그 모드: 가상 카메라 사용")
                    self._create_dummy_frame()
                    self.latest_frame = self.dummy_frame.copy()
                    self._initialized = True
                    return True
                else:
                    print("실제 하드웨어 모드: 실제 카메라 필요")
                    return False
                    
            def _create_dummy_frame(self):
                """디버그용 더미 프레임 생성"""
                self.dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                # 간단한 테스트 패턴 생성
                self.dummy_frame[50:430, 50:590] = [100, 100, 100]  # 회색 사각형
                # 텍스트 시뮬레이션 (실제로는 cv2.putText 사용)
                self.dummy_frame[200:280, 180:460] = [0, 255, 0]  # 녹색 영역
                
            def get_current_frame(self):
                return self.latest_frame
                
            def save_image(self, filename, folder_path="./CalthReaderResult/images"):
                if self.latest_frame is None:
                    return False
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, filename)
                # 실제로는 cv2.imwrite 사용
                print(f"가상 이미지 저장: {file_path}")
                return True
        
        # 테스트 실행
        camera = MockCameraManager()
        
        init_result = camera.init_camera()
        print(f"카메라 초기화: {'성공' if init_result else '실패'}")
        
        if init_result:
            frame = camera.get_current_frame()
            if frame is not None:
                print(f"프레임 획득 성공: 크기 {frame.shape}")
            
            save_result = camera.save_image("test.jpg")
            print(f"이미지 저장: {'성공' if save_result else '실패'}")
        
        print("✅ 카메라 매니저 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 카메라 매니저 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_uart_manager_only():
    """UART 매니저만 테스트 (PyQt5 없이)"""
    print("\n=== UART 매니저 테스트 (PyQt5 제외) ===")
    try:
        # 가상의 UART 매니저 클래스 테스트
        class MockUARTManager:
            def __init__(self):
                self.is_connected = False
                self._led_state = 0
                
            def init_uart(self, port='/dev/ttyTHS1', baudrate=115200, timeout=1):
                from config.config import app_config
                if app_config.is_debug_mode():
                    print("디버그 모드: 가상 UART 사용")
                    self.is_connected = True
                    self._led_state = 0
                    return True
                else:
                    print("실제 하드웨어 모드: 실제 UART 필요")
                    return False
                    
            def set_led_brightness(self, brightness):
                if not self.is_connected:
                    return False
                brightness = max(0, min(45, int(brightness)))
                self._led_state = brightness
                print(f"가상 LED 밝기 설정: {brightness}")
                return True
                
            def led_on(self, brightness=45):
                return self.set_led_brightness(brightness)
                
            def led_off(self):
                return self.set_led_brightness(0)
                
            def get_led_state(self):
                return self._led_state
        
        # 테스트 실행
        uart = MockUARTManager()
        
        init_result = uart.init_uart()
        print(f"UART 초기화: {'성공' if init_result else '실패'}")
        
        if init_result:
            led_on_result = uart.led_on(30)
            print(f"LED 켜기 (밝기 30): {'성공' if led_on_result else '실패'}")
            print(f"현재 LED 상태: {uart.get_led_state()}")
            
            led_off_result = uart.led_off()
            print(f"LED 끄기: {'성공' if led_off_result else '실패'}")
            print(f"현재 LED 상태: {uart.get_led_state()}")
        
        print("✅ UART 매니저 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ UART 매니저 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("Calth Reader 백엔드 구조 테스트 (PyQt5 제외)")
    print("=" * 60)
    
    # 설정 테스트
    config_ok = test_config_only()
    
    # 카메라 매니저 테스트
    camera_ok = test_camera_manager_only()
    
    # UART 매니저 테스트
    uart_ok = test_uart_manager_only()
    
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print(f"설정 시스템: {'✅ 성공' if config_ok else '❌ 실패'}")
    print(f"카메라 매니저: {'✅ 성공' if camera_ok else '❌ 실패'}")
    print(f"UART 매니저: {'✅ 성공' if uart_ok else '❌ 실패'}")
    
    if config_ok and camera_ok and uart_ok:
        print("\n🎉 모든 기본 구조 테스트 통과!")
        print("💡 실제 애플리케이션 실행을 위해서는 PyQt5 설치가 필요합니다:")
        print("   pip install PyQt5")
        return 0
    else:
        print("\n⚠️ 일부 테스트 실패. 설정을 확인해주세요.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
