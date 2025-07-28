# -*- coding: utf-8 -*-
"""
Settings Service - 설정 관리 서비스 (실시간 적용 지원)
"""
import json
import os
from typing import Any, Dict, List, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal

class SettingsService(QObject):
    """설정 관리 서비스 클래스 (JSON 파일 기반 + 실시간 적용)"""
    
    # 실시간 적용을 위한 시그널들
    language_changed = pyqtSignal(str)        # 언어 변경
    theme_changed = pyqtSignal(str)           # 테마 변경
    debug_mode_changed = pyqtSignal(bool)     # 디버그 모드 변경
    auto_sleep_changed = pyqtSignal(bool)     # 절전 모드 변경
    timeout_changed = pyqtSignal(int)         # 측정 타임아웃 변경
    
    def __init__(self):
        super().__init__()
        self.json_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'app_settings.json')
        self._ensure_default_settings()
    
    def _ensure_default_settings(self):
        """기본 설정 초기화 (JSON 파일만 사용)"""
        default_settings = {
            # 시스템 설정
            'system': {
                'debug_mode': True,
                'camera_enabled': True,
                'uart_enabled': True,
                'language': 'ko',
                'theme': 'light',
                'auto_sleep': False,
                'sleep_timeout': 10,
                'use_system_time': True,
                'timezone': 'Asia/Seoul',
                'manual_time_offset': 0  # 초 단위 오프셋
            },
            # 장치 설정
            'device': {
                'uart_port': '/dev/ttyUSB0',
                'uart_baudrate': 115200,
                'camera_resolution': '1920x1080',
            },
            # 업무 설정
            'business': {
                'auto_save_interval': 300,
                'measurement_timeout': 30,
                'qc_reminder_days': 7,
                'backup_retention_days': 30,
            },
            # 사용자 설정 템플릿
            'user_template': {
                'default_operator': '',
                'quick_patient_id': True,
                'sound_enabled': True,
            }
        }
        
        # JSON 파일에 기본값 저장
        self._save_json_defaults(default_settings)
    
    def _save_json_defaults(self, settings: Dict):
        """JSON 파일에 기본 설정 저장"""
        # 기존 파일이 있으면 병합, 없으면 새로 생성
        existing_data = {}
        if os.path.exists(self.json_config_path):
            try:
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                pass
        
        # 기본값과 병합 (기존값 우선)
        for category, category_settings in settings.items():
            if category not in existing_data:
                existing_data[category] = {}
            for key, value in category_settings.items():
                if key not in existing_data[category]:
                    existing_data[category][key] = value
        
        # 파일에 저장
        os.makedirs(os.path.dirname(self.json_config_path), exist_ok=True)
        with open(self.json_config_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    def get_setting(self, category: str, key: str, default: Any = None, user_id: str = None) -> Any:
        """설정값 가져오기"""
        try:
            if os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 사용자별 설정인 경우
                    if user_id and category == 'user':
                        user_key = f"user_{user_id}"
                        if user_key in data:
                            return data[user_key].get(key, default)
                        # 사용자별 설정이 없으면 템플릿에서 가져오기
                        return data.get('user_template', {}).get(key, default)
                    
                    # 일반 설정
                    return data.get(category, {}).get(key, default)
        except Exception as e:
            print(f"설정 읽기 실패: {e}")
        return default
    
    def set_setting(self, category: str, key: str, value: Any, user_id: str = None, **kwargs) -> bool:
        """설정값 저장 + 실시간 적용"""
        try:
            # 1. JSON 파일에 저장
            old_value = self.get_setting(category, key, None, user_id)
            
            data = {}
            if os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # 사용자별 설정인 경우
            if user_id and category == 'user':
                user_key = f"user_{user_id}"
                if user_key not in data:
                    data[user_key] = {}
                data[user_key][key] = value
            else:
                # 일반 설정
                if category not in data:
                    data[category] = {}
                data[category][key] = value
            
            with open(self.json_config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 2. 실시간 적용 (값이 실제로 변경된 경우만)
            if old_value != value:
                self._apply_setting_immediately(category, key, value)
            
            return True
        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False
    
    def _apply_setting_immediately(self, category: str, key: str, value: Any):
        """설정 변경 즉시 적용"""
        try:
            if category == 'system':
                if key == 'language':
                    self.language_changed.emit(value)
                    print(f"🌐 언어 즉시 변경: {value}")
                elif key == 'theme':
                    self.theme_changed.emit(value)
                    print(f"🎨 테마 즉시 변경: {value}")
                elif key == 'debug_mode':
                    self.debug_mode_changed.emit(value)
                    print(f"🐛 디버그 모드 즉시 변경: {value}")
                elif key == 'auto_sleep':
                    self.auto_sleep_changed.emit(value)
                    print(f"💤 절전 모드 즉시 변경: {value}")
            
            elif category == 'business':
                if key == 'measurement_timeout':
                    self.timeout_changed.emit(value)
                    print(f"⏱️ 측정 타임아웃 즉시 변경: {value}초")
            
            print(f"✅ 설정 즉시 적용됨: {category}.{key} = {value}")
            
        except Exception as e:
            print(f"❌ 설정 즉시 적용 실패: {e}")
    
    def get_all_settings(self, category: str = None) -> Dict:
        """모든 설정 조회"""
        settings = {}
        try:
            if os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if category:
                        settings[category] = data.get(category, {})
                    else:
                        settings.update(data)
        except Exception as e:
            print(f"설정 전체 조회 실패: {e}")
        
        return settings
    
    def get_settings(self) -> Dict:
        """모든 설정 가져오기 (편의 메서드)"""
        return self.get_all_settings()
    
    # 편의 메서드들
    def get_system_setting(self, key: str, default: Any = None) -> Any:
        """시스템 설정 가져오기"""
        return self.get_setting('system', key, default)
    
    def set_system_setting(self, key: str, value: Any) -> bool:
        """시스템 설정 저장"""
        return self.set_setting('system', key, value)
    
    def get_user_setting(self, user_id: str, key: str, default: Any = None) -> Any:
        """사용자 설정 가져오기"""
        return self.get_setting('user', key, default, user_id)
    
    def set_user_setting(self, user_id: str, key: str, value: Any) -> bool:
        """사용자 설정 저장"""
        return self.set_setting('user', key, value, user_id)
    
    def get_business_setting(self, key: str, default: Any = None) -> Any:
        """업무 설정 가져오기"""
        return self.get_setting('business', key, default)
    
    def set_business_setting(self, key: str, value: Any) -> bool:
        """업무 설정 저장"""
        return self.set_setting('business', key, value)

# 전역 설정 서비스 인스턴스
settings_service = SettingsService()