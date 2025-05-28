#!/usr/bin/env python3
"""
간단한 UART 터미널 프로그램
MCU와 직접 통신하여 명령/응답을 확인할 수 있습니다.
"""

import serial
import threading
import sys
import time

class UARTTerminal:
    def __init__(self, port='/dev/ttyTHS1', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        
    def connect(self):
        """UART 연결"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1  # Non-blocking read
            )
            print(f"✓ UART 연결 성공: {self.port} @ {self.baudrate}bps")
            return True
        except Exception as e:
            print(f"✗ UART 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """UART 연결 해제"""
        if self.ser and self.ser.is_open:
            self.running = False
            self.ser.close()
            print("UART 연결 종료")
    
    def read_thread(self):
        """수신 데이터 읽기 스레드"""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        # 수신 데이터를 다양한 형태로 출력
                        print(f"\n[수신] Raw: {data}")
                        print(f"[수신] Hex: {data.hex()}")
                        try:
                            print(f"[수신] ASCII: {data.decode('utf-8', errors='ignore')}")
                        except:
                            print(f"[수신] ASCII: (decode 실패)")
                        print(">>> ", end="", flush=True)
                time.sleep(0.01)
            except Exception as e:
                if self.running:  # 정상 종료가 아닌 경우만 에러 출력
                    print(f"\n읽기 오류: {e}")
                break
    
    def send_command(self, command):
        """명령 전송"""
        if not self.ser or not self.ser.is_open:
            print("UART가 연결되지 않았습니다.")
            return
        
        try:
            # 문자열을 바이트로 변환하여 전송
            data = command.encode('utf-8')
            self.ser.write(data)
            self.ser.flush()
            print(f"[전송] '{command}' -> {data} -> {data.hex()}")
        except Exception as e:
            print(f"전송 오류: {e}")
    
    def run(self):
        """터미널 실행"""
        print("=" * 50)
        print("UART 터미널 프로그램")
        print("=" * 50)
        print("명령어:")
        print("  quit, exit, q : 종료")
        print("  help, h       : 도움말")
        print("  그 외 텍스트  : MCU로 전송")
        print("-" * 50)
        
        if not self.connect():
            return
        
        # 수신 스레드 시작
        self.running = True
        read_thread = threading.Thread(target=self.read_thread)
        read_thread.daemon = True
        read_thread.start()
        
        print("터미널 시작! (종료: quit)")
        
        try:
            while self.running:
                try:
                    command = input(">>> ").strip()
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    elif command.lower() in ['help', 'h']:
                        print("\n도움말:")
                        print("  L00~L45 : LED 밝기 제어")
                        print("  quit    : 종료")
                        print("  기타    : 입력한 텍스트를 그대로 전송")
                        continue
                    elif command == "":
                        continue
                    
                    # 명령 전송
                    self.send_command(command)
                    
                except KeyboardInterrupt:
                    print("\n종료 중...")
                    break
                except EOFError:
                    break
        finally:
            self.disconnect()

def main():
    # 포트 설정
    port = '/dev/ttyTHS1'
    baudrate = 115200
    
    # 명령행 인수로 포트/보드레이트 변경 가능
    if len(sys.argv) >= 2:
        port = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            baudrate = int(sys.argv[2])
        except ValueError:
            print("보드레이트는 숫자여야 합니다.")
            return
    
    print(f"사용할 포트: {port}")
    print(f"보드레이트: {baudrate}")
    
    # 터미널 실행
    terminal = UARTTerminal(port, baudrate)
    terminal.run()

if __name__ == "__main__":
    main() 