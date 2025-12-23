#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jetson Nano UART LED 제어 테스트 스크립트
사용법: python3 uart_test.py
"""

import serial
import time
import sys

def test_uart_connection():
    """UART 연결 테스트"""
    print("=== UART LED 제어 테스트 ===")
    print("Jetson Nano UART(/dev/ttyTHS1) LED 제어 테스트를 시작합니다.")
    
    # UART 설정
    port = '/dev/ttyTHS1'
    baudrate = 115200
    
    try:
        # Serial 포트 열기
        print(f"\n1. UART 포트 연결 중... ({port}, {baudrate}bps)")
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        
        if ser.is_open:
            print("   ✓ UART 포트 연결 성공!")
        else:
            print("   ✗ UART 포트 연결 실패!")
            return False
            
        # 포트 정보 출력
        print(f"   포트: {ser.name}")
        print(f"   보드레이트: {ser.baudrate}")
        print(f"   타임아웃: {ser.timeout}")
        
        # LED 테스트 시퀀스
        print("\n2. LED 제어 테스트 시작...")
        
        # 테스트할 LED 밝기 값들 (0~45)
        test_values = [0, 10, 20, 30, 45, 0]
        
        for i, brightness in enumerate(test_values):
            command = f"L{brightness:02d}"
            print(f"   {i+1}. LED 밝기 {brightness} 설정 (명령: '{command}')")
            
            # 명령 전송
            ser.write(command.encode('utf-8'))
            ser.flush()
            
            # 전송된 바이트 확인
            print(f"      전송된 바이트: {command.encode('utf-8')}")
            
            # 잠시 대기
            time.sleep(1)
            
            # 응답 읽기 시도
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"      응답: {response}")
            else:
                print("      응답 없음")
        
        # 포트 닫기
        ser.close()
        print("\n3. UART 포트 연결 종료")
        print("   ✓ 테스트 완료!")
        
        return True
        
    except serial.SerialException as e:
        print(f"\n   ✗ UART 오류: {e}")
        if "Permission denied" in str(e):
            print("\n   권한 문제 해결 방법:")
            print("   1. sudo usermod -a -G dialout $USER")
            print("   2. 재부팅 또는 재로그인")
            print("   3. 또는 sudo python3 uart_test.py")
        return False
        
    except Exception as e:
        print(f"\n   ✗ 예상치 못한 오류: {e}")
        return False

def check_uart_device():
    """UART 디바이스 존재 확인"""
    import os
    
    print("\n=== UART 디바이스 확인 ===")
    uart_devices = ['/dev/ttyTHS0', '/dev/ttyTHS1', '/dev/ttyUSB0', '/dev/ttyACM0']
    
    available_devices = []
    for device in uart_devices:
        if os.path.exists(device):
            print(f"   ✓ {device} 존재")
            available_devices.append(device)
        else:
            print(f"   ✗ {device} 없음")
    
    if available_devices:
        print(f"\n   사용 가능한 UART 디바이스: {available_devices}")
    else:
        print("\n   ⚠️  사용 가능한 UART 디바이스가 없습니다!")
    
    return available_devices

def interactive_led_control():
    """대화형 LED 제어"""
    print("\n=== 대화형 LED 제어 ===")
    print("LED 밝기를 직접 제어해보세요 (0-45, 'q'로 종료)")
    
    port = '/dev/ttyTHS1'
    baudrate = 115200
    
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        print(f"UART 연결 성공: {port}")
        
        while True:
            try:
                user_input = input("\nLED 밝기 입력 (0-45): ").strip()
                
                if user_input.lower() == 'q':
                    break
                
                brightness = int(user_input)
                if 0 <= brightness <= 45:
                    command = f"L{brightness:02d}"
                    ser.write(command.encode('utf-8'))
                    ser.flush()
                    print(f"명령 전송: {command}")
                else:
                    print("밝기는 0-45 사이의 값이어야 합니다.")
                    
            except ValueError:
                print("숫자를 입력해주세요.")
            except KeyboardInterrupt:
                break
        
        ser.close()
        print("UART 연결 종료")
        
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    print("Jetson Nano UART LED 테스트 도구")
    print("=" * 40)
    
    # 1. UART 디바이스 확인
    available_devices = check_uart_device()
    
    if not available_devices:
        print("\n⚠️  UART 디바이스를 찾을 수 없습니다!")
        print("Jetson Nano UART가 활성화되어 있는지 확인해주세요.")
        sys.exit(1)
    
    # 2. 자동 테스트
    success = test_uart_connection()
    
    if success:
        # 3. 대화형 테스트 옵션
        choice = input("\n대화형 LED 제어를 시작하시겠습니까? (y/n): ").strip().lower()
        if choice == 'y':
            interactive_led_control()
    
    print("\n테스트 완료!") 