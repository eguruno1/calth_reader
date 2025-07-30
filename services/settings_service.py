# -*- coding: utf-8 -*-
"""
Settings Service - 설정 관리 서비스
"""
import json
import os
from typing import Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal


class SettingsService(QObject):
    """애플리케이션 설정 관리 서비스"""
    
    # 시그널 정의
    setting_changed = pyqtSignal(str, str, str)  # category, key, value
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        
        # 설정 파일 경로
        self.config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        self.config_file = os.path.join(self.config_dir, 'app_settings.json')
        
        # 메모리 캐시
        self._settings_cache = {}
        
        # 설정 파일 로드
        self.load_settings()
    
    def load_settings(self) -> bool:
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._settings_cache = json.load(f)
                return True
            else:
                # 기본 설정으로 초기화
                self._initialize_default_settings()
                return self.save_settings()
        except Exception as e:
            error_msg = f"설정 파일 로드 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def save_settings(self) -> bool:
        """설정 파일 저장"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings_cache, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            error_msg = f"설정 파일 저장 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def get_setting(self, category: str, key: str, default_value: Any = None) -> Any:
        """설정값 조회"""
        try:
            if category in self._settings_cache:
                return self._settings_cache[category].get(key, default_value)
            return default_value
        except Exception as e:
            print(f"설정 조회 실패: {e}")
            return default_value
    
    def set_setting(self, category: str, key: str, value: Any) -> bool:
        """설정값 저장"""
        try:
            if category not in self._settings_cache:
                self._settings_cache[category] = {}
            
            self._settings_cache[category][key] = value
            
            # 파일에 저장
            if self.save_settings():
                self.setting_changed.emit(category, key, str(value))
                return True
            return False
        except Exception as e:
            error_msg = f"설정 저장 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def get_category_settings(self, category: str) -> Dict[str, Any]:
        """카테고리별 모든 설정 조회"""
        return self._settings_cache.get(category, {})
    
    def set_category_settings(self, category: str, settings: Dict[str, Any]) -> bool:
        """카테고리별 모든 설정 저장"""
        try:
            self._settings_cache[category] = settings
            if self.save_settings():
                for key, value in settings.items():
                    self.setting_changed.emit(category, key, str(value))
                return True
            return False
        except Exception as e:
            error_msg = f"카테고리 설정 저장 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def remove_setting(self, category: str, key: str) -> bool:
        """설정값 삭제"""
        try:
            if category in self._settings_cache and key in self._settings_cache[category]:
                del self._settings_cache[category][key]
                if self.save_settings():
                    self.setting_changed.emit(category, key, "")
                    return True
            return False
        except Exception as e:
            error_msg = f"설정 삭제 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def remove_category(self, category: str) -> bool:
        """카테고리 삭제"""
        try:
            if category in self._settings_cache:
                del self._settings_cache[category]
                return self.save_settings()
            return False
        except Exception as e:
            error_msg = f"카테고리 삭제 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def reset_to_defaults(self) -> bool:
        """기본값으로 리셋"""
        try:
            self._initialize_default_settings()
            return self.save_settings()
        except Exception as e:
            error_msg = f"기본값 리셋 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def _initialize_default_settings(self):
        """기본 설정 초기화"""
        self._settings_cache = {
            "system": {
                "debug_mode": True,
                "camera_enabled": True,
                "uart_enabled": True,
                "language": "ko",
                "theme": "light",
                "auto_sleep": False,
                "sleep_timeout": 10,
                "time_mode": "system",  # system, utc, custom
                "utc_offset": "9",      # UTC+9 (KST)
                "custom_datetime": ""   # ISO 형식 문자열
            },
            "device": {
                "uart_port": "/dev/ttyUSB0",
                "uart_baudrate": 115200,
                "camera_resolution": "1920x1080"
            },
            "business": {
                "auto_save_interval": 300,
                "measurement_timeout": 30,
                "qc_reminder_days": 7,
                "backup_retention_days": 26
            },
            "user_template": {
                "default_operator": "",
                "quick_patient_id": True,
                "sound_enabled": True
            }
        }
    
    def export_settings(self, file_path: str) -> bool:
        """설정 내보내기"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings_cache, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            error_msg = f"설정 내보내기 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """설정 가져오기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # 기존 설정과 병합
            for category, settings in imported_settings.items():
                if category not in self._settings_cache:
                    self._settings_cache[category] = {}
                self._settings_cache[category].update(settings)
            
            return self.save_settings()
        except Exception as e:
            error_msg = f"설정 가져오기 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """모든 설정 반환"""
        return self._settings_cache.copy()
    
    def validate_setting(self, category: str, key: str, value: Any) -> bool:
        """설정값 유효성 검사"""
        try:
            # 시스템 카테고리 유효성 검사
            if category == "system":
                if key == "time_mode" and value not in ["system", "utc", "custom"]:
                    return False
                if key == "utc_offset":
                    try:
                        offset = int(value)
                        return -12 <= offset <= 12
                    except ValueError:
                        return False
                if key in ["debug_mode", "camera_enabled", "uart_enabled", "auto_sleep"]:
                    return isinstance(value, bool)
                if key in ["sleep_timeout"]:
                    return isinstance(value, (int, float)) and value > 0
            
            # 디바이스 카테고리 유효성 검사
            elif category == "device":
                if key == "uart_baudrate":
                    return value in [9600, 19200, 38400, 57600, 115200, 230400]
                if key == "camera_resolution":
                    valid_resolutions = ["640x480", "800x600", "1024x768", "1920x1080"]
                    return value in valid_resolutions
            
            return True
        except Exception:
            return False