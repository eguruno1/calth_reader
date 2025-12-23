#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최소한의 LED 테스트 스크립트
"""

import serial
import time

# UART 설정
PORT = '/dev/ttyTHS1'
BAUDRATE = 115200

def simple_led_test():
    try:
        print("LED 테스트 시작...")
        
        # UART 연결
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        print(f"UART 연결: {PORT} @ {BAUDRATE}bps")
        
        # LED 켜기/끄기 테스트
        commands = ['L45', 'L00', 'L45', 'L00', 'L45']
        
        for i, cmd in enumerate(commands):
            print(f"{i+1}. 명령 전송: {cmd}")
            ser.write(cmd.encode())
            ser.flush()
            time.sleep(2)  # 2초 대기
        
        ser.close()
        print("테스트 완료!")
        
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    simple_led_test() 