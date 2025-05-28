#!/usr/bin/env python3
"""
간단한 UART 터미널 프로그램
MCU와 직접 통신하여 명령/응답을 확인할 수 있습니다.
"""

import serial
import threading
import sys
import time
from datetime import datetime

class UARTTerminal:
    def __init__(self, port='/dev/ttyTHS1', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.monitor_mode = True  # 주기적 데이터 모니터링 모드
        
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
            print("\nUART 연결 종료")
    
    def get_timestamp(self):
        """현재 시간 타임스탬프 반환"""
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 밀리초까지
    
    def read_thread(self):
        """수신 데이터 읽기 스레드 (주기적 모니터링)"""
        print(f"\n[{self.get_timestamp()}] 수신 모니터링 시작...")
        print("=" * 60)
        
        while self.running and self.ser and self.ser.is_open:
            try:
                # 더 자주 체크해서 데이터를 놓치지 않도록
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        timestamp = self.get_timestamp()
                        print(f"\n📨 [{timestamp}] 수신 데이터:")
                        print(f"   Raw bytes: {data}")
                        print(f"   Hex:       {data.hex(' ').upper()}")
                        print(f"   Length:    {len(data)} bytes")
                        
                        # ASCII 디코딩 시도
                        try:
                            ascii_data = data.decode('utf-8', errors='replace')
                            # 제어 문자 표시
                            display_data = ascii_data.replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
                            print(f"   ASCII:     '{display_data}'")
                        except:
                            print(f"   ASCII:     (디코딩 실패)")
                        
                        print("-" * 60)
                        if not self.monitor_mode:
                            print(">>> ", end="", flush=True)
                
                time.sleep(0.01)  # 10ms 간격으로 체크
                
            except Exception as e:
                if self.running:  # 정상 종료가 아닌 경우만 에러 출력
                    print(f"\n❌ [{self.get_timestamp()}] 읽기 오류: {e}")
                break
    
    def send_command(self, command):
        """명령 전송"""
        if not self.ser or not self.ser.is_open:
            print("❌ UART가 연결되지 않았습니다.")
            return
        
        try:
            # 문자열을 바이트로 변환하여 전송
            data = command.encode('utf-8')
            self.ser.write(data)
            self.ser.flush()
            timestamp = self.get_timestamp()
            print(f"\n📤 [{timestamp}] 전송:")
            print(f"   Command: '{command}'")
            print(f"   Bytes:   {data}")
            print(f"   Hex:     {data.hex(' ').upper()}")
            print("-" * 60)
        except Exception as e:
            print(f"❌ 전송 오류: {e}")
    
    def toggle_monitor_mode(self):
        """모니터 모드 토글"""
        self.monitor_mode = not self.monitor_mode
        status = "활성화" if self.monitor_mode else "비활성화"
        print(f"\n🔄 연속 모니터링 모드 {status}")
    
    def run(self):
        """터미널 실행"""
        print("=" * 60)
        print("🔧 UART 터미널 프로그램 (주기적 데이터 모니터링)")
        print("=" * 60)
        print("명령어:")
        print("  quit, exit, q : 종료")
        print("  help, h       : 도움말")
        print("  monitor, m    : 모니터링 모드 토글")
        print("  clear, c      : 화면 클리어")
        print("  그 외 텍스트  : MCU로 전송")
        print("-" * 60)
        
        if not self.connect():
            return
        
        # 수신 스레드 시작
        self.running = True
        read_thread = threading.Thread(target=self.read_thread)
        read_thread.daemon = True
        read_thread.start()
        
        print("🚀 터미널 시작! MCU에서 오는 주기적 데이터를 모니터링합니다.")
        print("   명령을 입력하거나 그냥 수신 데이터를 관찰하세요.")
        
        try:
            while self.running:
                try:
                    if not self.monitor_mode:
                        command = input(">>> ").strip()
                    else:
                        # 모니터 모드에서는 입력 대기 없이 계속 실행
                        try:
                            command = input().strip()  # 비블로킹 입력 시도
                        except:
                            time.sleep(0.1)
                            continue
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    elif command.lower() in ['help', 'h']:
                        print("\n📖 도움말:")
                        print("  L00~L45     : LED 밝기 제어")
                        print("  monitor, m  : 연속 모니터링 모드 토글")
                        print("  clear, c    : 화면 클리어")
                        print("  quit        : 종료")
                        print("  기타        : 입력한 텍스트를 그대로 전송")
                        continue
                    elif command.lower() in ['monitor', 'm']:
                        self.toggle_monitor_mode()
                        continue
                    elif command.lower() in ['clear', 'c']:
                        import os
                        os.system('clear' if os.name == 'posix' else 'cls')
                        continue
                    elif command == "":
                        continue
                    
                    # 명령 전송
                    self.send_command(command)
                    
                except KeyboardInterrupt:
                    print("\n🛑 종료 중...")
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
            print("❌ 보드레이트는 숫자여야 합니다.")
            return
    
    print(f"🔌 사용할 포트: {port}")
    print(f"⚡ 보드레이트: {baudrate}")
    
    # 터미널 실행
    terminal = UARTTerminal(port, baudrate)
    terminal.run()

if __name__ == "__main__":
    main() 