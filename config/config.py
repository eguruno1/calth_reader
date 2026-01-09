# -*- coding: utf-8 -*-
"""
Configuration settings for Calth Reader Application
"""
import os
import json

class Config:
    """애플리케이션 설정 관리 클래스"""
    
    def __init__(self):
        self.debug_mode = False  # 기본값은 디버그 모드 : True
        self.config_file = os.path.join(os.path.dirname(__file__), 'settings.json')
        self.load_config()
    
    def load_config(self):
        """설정 파일에서 설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.debug_mode = config_data.get('debug_mode')
                    self.camera_enabled = config_data.get('camera_enabled')
                    self.uart_enabled = config_data.get('uart_enabled')

                    print(f"load_config 설정 파일 debug_mode: {config_data.get('debug_mode')}")
                    print(f"load_config 설정 파일 camera_enabled: {config_data.get('camera_enabled')}")
                    print(f"load_config 설정 파일 uart_enabled: {config_data.get('uart_enabled')}")
            else:
                self.camera_enabled = not self.debug_mode
                self.uart_enabled = not self.debug_mode
                self.save_config()

            print(f"load_config 설정 파일 로드: {self.debug_mode}")
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            self.debug_mode = True
            self.camera_enabled = False
            self.uart_enabled = False
    
    def save_config(self):
        """설정을 파일에 저장"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config_data = {
                'debug_mode': self.debug_mode,
                'camera_enabled': self.camera_enabled,
                'uart_enabled': self.uart_enabled
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            print(f"save_config 설정 파일 저장: {self.debug_mode}")    
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")
    
    def set_debug_mode(self, enabled):
        """디버그 모드 설정"""
        self.debug_mode = enabled
        self.camera_enabled = not enabled
        self.uart_enabled = not enabled
        print(f"set_debug_mode 설정: {self.debug_mode}")
        self.save_config()
    
    def is_debug_mode(self):
        """디버그 모드 여부 반환"""
        print(f"Config 디버그 모드: {self.debug_mode}")
        return self.debug_mode
    
    def is_camera_enabled(self):
        """카메라 활성화 여부 반환"""
        print(f"Config 카메라 모드: {self.camera_enabled}")
        return self.camera_enabled
    
    def is_uart_enabled(self):
        """UART 활성화 여부 반환"""
        print(f"Config UART 모드: {self.uart_enabled}")
        return self.uart_enabled

# 전역 설정 인스턴스
app_config = Config()
