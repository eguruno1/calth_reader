# -*- coding: utf-8 -*-
"""
Settings Service - 설정 관리 서비스 (간소화 버전)
"""
import json
import os
from typing import Any, Dict, List, Optional, Union

class SettingsService:
    """설정 관리 서비스 클래스"""
    
    def __init__(self):
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
                'sleep_timeout': 10
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
    
    def _save_db_defaults(self, settings: Dict):
        """DB에 기본 설정 저장"""
        try:
            for category, category_settings in settings.items():
                for key, config in category_settings.items():
                    if config['storage'] == 'db':
                        # 이미 존재하는지 확인
                        existing = self.db.query(AppSettings).filter_by(
                            category=category, key=key
                        ).first()
                        
                        if not existing:
                            setting = AppSettings(
                                category=category,
                                key=key,
                                value=str(config['value']),
                                value_type=config['type'],
                                description=f"{category} - {key}",
                                is_user_configurable=True
                            )
                            self.db.add(setting)
            
            self.db.commit()
        except Exception as e:
            print(f"DB 기본 설정 저장 실패: {e}")
            self.db.rollback()
    
    # JSON 설정 관리
    def get_json_setting(self, category: str, key: str, default: Any = None) -> Any:
        """JSON에서 설정값 가져오기"""
        try:
            if os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get(category, {}).get(key, default)
        except Exception as e:
            print(f"JSON 설정 읽기 실패: {e}")
        return default
    
    def set_json_setting(self, category: str, key: str, value: Any) -> bool:
        """JSON에 설정값 저장"""
        try:
            data = {}
            if os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            if category not in data:
                data[category] = {}
            
            data[category][key] = value
            
            with open(self.json_config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"JSON 설정 저장 실패: {e}")
            return False
    
    # DB 설정 관리
    def get_db_setting(self, category: str, key: str, default: Any = None) -> Any:
        """DB에서 설정값 가져오기"""
        try:
            setting = self.db.query(AppSettings).filter_by(
                category=category, key=key
            ).first()
            
            if setting:
                return self._convert_value(setting.value, setting.value_type)
            return default
        except Exception as e:
            print(f"DB 설정 읽기 실패: {e}")
            return default
    
    def set_db_setting(self, category: str, key: str, value: Any, 
                      value_type: str = None, user_id: str = None) -> bool:
        """DB에 설정값 저장"""
        try:
            setting = self.db.query(AppSettings).filter_by(
                category=category, key=key
            ).first()
            
            if setting:
                setting.value = str(value)
                if value_type:
                    setting.value_type = value_type
                if user_id:
                    setting.updated_by = user_id
            else:
                setting = AppSettings(
                    category=category,
                    key=key,
                    value=str(value),
                    value_type=value_type or self._detect_type(value),
                    updated_by=user_id
                )
                self.db.add(setting)
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"DB 설정 저장 실패: {e}")
            self.db.rollback()
            return False
    
    # 사용자별 설정 관리
    def get_user_setting(self, user_id: str, key: str, default: Any = None) -> Any:
        """사용자별 설정 가져오기"""
        try:
            setting = self.db.query(UserSettings).filter_by(
                user_id=user_id, setting_key=key
            ).first()
            
            if setting:
                return self._convert_value(setting.setting_value, setting.value_type)
            return default
        except Exception as e:
            print(f"사용자 설정 읽기 실패: {e}")
            return default
    
    def set_user_setting(self, user_id: str, key: str, value: Any, 
                        value_type: str = None) -> bool:
        """사용자별 설정 저장"""
        try:
            setting = self.db.query(UserSettings).filter_by(
                user_id=user_id, setting_key=key
            ).first()
            
            if setting:
                setting.setting_value = str(value)
                if value_type:
                    setting.value_type = value_type
            else:
                setting = UserSettings(
                    user_id=user_id,
                    setting_key=key,
                    setting_value=str(value),
                    value_type=value_type or self._detect_type(value)
                )
                self.db.add(setting)
            
            self.db.commit()
            return True
        except Exception as e:
            print(f"사용자 설정 저장 실패: {e}")
            self.db.rollback()
            return False
    
    # 통합 설정 API
    def get_setting(self, category: str, key: str, user_id: str = None, 
                   default: Any = None) -> Any:
        """통합 설정값 가져오기 (자동으로 저장소 선택)"""
        # 사용자별 설정 먼저 확인
        if user_id and category == 'user':
            return self.get_user_setting(user_id, key, default)
        
        # 시스템/장치 설정은 JSON에서
        if category in ['system', 'device']:
            return self.get_json_setting(category, key, default)
        
        # 업무 설정은 DB에서
        return self.get_db_setting(category, key, default)
    
    def set_setting(self, category: str, key: str, value: Any, 
                   user_id: str = None, value_type: str = None) -> bool:
        """통합 설정값 저장 (자동으로 저장소 선택)"""
        # 사용자별 설정
        if user_id and category == 'user':
            return self.set_user_setting(user_id, key, value, value_type)
        
        # 시스템/장치 설정은 JSON에
        if category in ['system', 'device']:
            return self.set_json_setting(category, key, value)
        
        # 업무 설정은 DB에
        return self.set_db_setting(category, key, value, value_type, user_id)
    
    # 헬퍼 메서드
    def _convert_value(self, value: str, value_type: str) -> Any:
        """문자열 값을 적절한 타입으로 변환"""
        try:
            if value_type == 'bool':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif value_type == 'int':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'json':
                return json.loads(value)
            return value
        except:
            return value
    
    def _detect_type(self, value: Any) -> str:
        """값의 타입 자동 감지"""
        if isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, (dict, list)):
            return 'json'
        return 'string'
    
    def get_all_settings(self, category: str = None) -> Dict:
        """모든 설정 조회"""
        settings = {}
        
        # JSON 설정
        try:
            if os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    if category:
                        settings[category] = json_data.get(category, {})
                    else:
                        settings.update(json_data)
        except Exception as e:
            print(f"JSON 설정 전체 조회 실패: {e}")
        
        # DB 설정
        try:
            query = self.db.query(AppSettings)
            if category:
                query = query.filter(AppSettings.category == category)
            
            for setting in query.all():
                if setting.category not in settings:
                    settings[setting.category] = {}
                settings[setting.category][setting.key] = self._convert_value(
                    setting.value, setting.value_type
                )
        except Exception as e:
            print(f"DB 설정 전체 조회 실패: {e}")
        
        return settings
    
    def __del__(self):
        """소멸자에서 DB 연결 정리"""
        if hasattr(self, 'db'):
            self.db.close()

# 전역 설정 서비스 인스턴스
settings_service = SettingsService()
