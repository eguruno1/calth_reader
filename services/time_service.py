# -*- coding: utf-8 -*-
"""
Time Service - 시간 설정 관리 서비스
"""
import os
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal
from services.settings_service import SettingsService


class TimeService(QObject):
    """시간 설정 관리 서비스"""
    
    # 시그널 정의
    time_setting_changed = pyqtSignal(str)  # 시간 설정 변경 시그널
    error_occurred = pyqtSignal(str)  # 에러 발생 시그널
    
    def __init__(self):
        super().__init__()
        self.settings_service = SettingsService()
        
        # 시간 설정 모드
        self.TIME_MODE_SYSTEM = "system"
        self.TIME_MODE_UTC = "utc"
        self.TIME_MODE_CUSTOM = "custom"
        
        # 지원하는 UTC 오프셋
        self.UTC_OFFSETS = [
            ("UTC-12:00", -12),
            ("UTC-11:00", -11),
            ("UTC-10:00", -10),
            ("UTC-09:00", -9),
            ("UTC-08:00", -8),
            ("UTC-07:00", -7),
            ("UTC-06:00", -6),
            ("UTC-05:00", -5),
            ("UTC-04:00", -4),
            ("UTC-03:00", -3),
            ("UTC-02:00", -2),
            ("UTC-01:00", -1),
            ("UTC+00:00", 0),
            ("UTC+01:00", 1),
            ("UTC+02:00", 2),
            ("UTC+03:00", 3),
            ("UTC+04:00", 4),
            ("UTC+05:00", 5),
            ("UTC+06:00", 6),
            ("UTC+07:00", 7),
            ("UTC+08:00", 8),
            ("UTC+09:00", 9),  # Korea Standard Time
            ("UTC+10:00", 10),
            ("UTC+11:00", 11),
            ("UTC+12:00", 12),
        ]
    
    def get_time_mode(self) -> str:
        """현재 시간 설정 모드 반환"""
        try:
            return self.settings_service.get_setting("system", "time_mode", "system")
        except Exception as e:
            print(f"시간 모드 조회 실패: {e}")
            return self.TIME_MODE_SYSTEM
    
    def set_time_mode(self, mode: str) -> bool:
        """시간 설정 모드 변경"""
        try:
            if mode not in [self.TIME_MODE_SYSTEM, self.TIME_MODE_UTC, self.TIME_MODE_CUSTOM]:
                raise ValueError(f"지원되지 않는 시간 모드: {mode}")
            
            success = self.settings_service.set_setting("system", "time_mode", mode)
            if success:
                self.time_setting_changed.emit(mode)
            return success
        except Exception as e:
            error_msg = f"시간 모드 설정 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def get_utc_offset(self) -> int:
        """현재 UTC 오프셋 반환"""
        try:
            return int(self.settings_service.get_setting("system", "utc_offset", "9"))
        except Exception as e:
            print(f"UTC 오프셋 조회 실패: {e}")
            return 9  # 기본값: KST (UTC+9)
    
    def set_utc_offset(self, offset: int) -> bool:
        """UTC 오프셋 설정"""
        try:
            if offset < -12 or offset > 12:
                raise ValueError(f"지원되지 않는 UTC 오프셋: {offset}")
            
            success = self.settings_service.set_setting("system", "utc_offset", str(offset))
            if success:
                self.time_setting_changed.emit(f"utc_offset_{offset}")
            return success
        except Exception as e:
            error_msg = f"UTC 오프셋 설정 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def get_custom_datetime(self) -> Optional[datetime]:
        """커스텀 날짜/시간 반환"""
        try:
            custom_time_str = self.settings_service.get_setting("system", "custom_datetime", "")
            if custom_time_str:
                return datetime.fromisoformat(custom_time_str)
            return None
        except Exception as e:
            print(f"커스텀 날짜/시간 조회 실패: {e}")
            return None
    
    def set_custom_datetime(self, dt: datetime) -> bool:
        """커스텀 날짜/시간 설정"""
        try:
            dt_str = dt.isoformat()
            success = self.settings_service.set_setting("system", "custom_datetime", dt_str)
            if success:
                self.time_setting_changed.emit(f"custom_datetime_{dt_str}")
            return success
        except Exception as e:
            error_msg = f"커스텀 날짜/시간 설정 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False
    
    def get_current_display_time(self) -> datetime:
        """현재 표시할 시간 반환 (설정에 따라)"""
        mode = self.get_time_mode()
        
        if mode == self.TIME_MODE_SYSTEM:
            return datetime.now()
        
        elif mode == self.TIME_MODE_UTC:
            offset = self.get_utc_offset()
            utc_time = datetime.utcnow()
            # UTC 오프셋 적용
            return utc_time + timedelta(hours=offset)
        
        elif mode == self.TIME_MODE_CUSTOM:
            custom_time = self.get_custom_datetime()
            if custom_time:
                return custom_time
            else:
                # 커스텀 시간이 설정되지 않은 경우 시스템 시간 사용
                return datetime.now()
        
        return datetime.now()
    
    def get_utc_offset_list(self) -> list:
        """UTC 오프셋 리스트 반환"""
        return self.UTC_OFFSETS
    
    def get_utc_offset_display_name(self, offset: int) -> str:
        """UTC 오프셋의 표시명 반환"""
        for display_name, value in self.UTC_OFFSETS:
            if value == offset:
                return display_name
        return f"UTC{'+' if offset >= 0 else ''}{offset}:00"
    
    def sync_system_time(self) -> bool:
        """시스템 시간과 동기화 (관리자 권한 필요)"""
        try:
            # macOS/Linux에서 시스템 시간 동기화
            if os.name == 'posix':
                result = subprocess.run(['sudo', 'sntp', '-sS', 'time.apple.com'], 
                                      capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            else:
                # Windows의 경우
                result = subprocess.run(['w32tm', '/resync'], 
                                      capture_output=True, text=True, timeout=10)
                return result.returncode == 0
        except Exception as e:
            error_msg = f"시스템 시간 동기화 실패: {e}"
            self.error_occurred.emit(error_msg)
            return False