# -*- coding: utf-8 -*-
"""
Pydantic Schemas for Data Validation
API 요청/응답을 위한 데이터 검증 스키마
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum

try:
    from pydantic import BaseModel, validator, Field
except ImportError:
    # Pydantic이 설치되지 않은 경우 기본 클래스 정의
    class BaseModel:
        pass
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def Field(*args, **kwargs):
        return None

# Enum 클래스들
class GenderEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    MAINTENANCE = "maintenance"

class TestStatusEnum(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"

class LogLevelEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# Base 스키마
class BaseSchema(BaseModel):
    """기본 스키마"""
    
    class Config:
        orm_mode = True  # Pydantic v1 (Python 3.6 호환)

# Patient 스키마들
class PatientBase(BaseSchema):
    """환자 기본 스키마"""
    patient_code: str = Field(..., min_length=1, max_length=50)
    birth_year: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    gender: Optional[GenderEnum] = None
    notes: Optional[str] = None

class PatientCreate(PatientBase):
    """환자 생성 스키마"""
    pass

class PatientUpdate(BaseSchema):
    """환자 수정 스키마"""
    patient_code: Optional[str] = Field(None, min_length=1, max_length=50)
    birth_year: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    gender: Optional[GenderEnum] = None
    notes: Optional[str] = None

class PatientResponse(PatientBase):
    """환자 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

# TestType 스키마들
class TestTypeBase(BaseSchema):
    """테스트 유형 기본 스키마"""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    measurement_time_seconds: int = Field(300, ge=1)

class TestTypeCreate(TestTypeBase):
    """테스트 유형 생성 스키마"""
    pass

class TestTypeUpdate(BaseSchema):
    """테스트 유형 수정 스키마"""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    measurement_time_seconds: Optional[int] = Field(None, ge=1)

class TestTypeResponse(TestTypeBase):
    """테스트 유형 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

# User 스키마들
class UserBase(BaseSchema):
    """사용자 기본 스키마"""
    user_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRoleEnum
    email: Optional[str] = Field(None, pattern=r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
    phone: Optional[str] = Field(None, max_length=20)
    is_active: bool = True

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=6)

class UserUpdate(BaseSchema):
    """사용자 수정 스키마"""
    user_id: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRoleEnum] = None
    email: Optional[str] = Field(None, pattern=r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# TestSession 스키마들
class TestSessionBase(BaseSchema):
    """테스트 세션 기본 스키마"""
    test_type_id: int
    operator_id: int
    patient_id: Optional[int] = None
    device_serial: Optional[str] = Field(None, max_length=100)
    cartridge_lot: Optional[str] = Field(None, max_length=50)
    temperature: Optional[float] = Field(None, ge=-50, le=100)
    humidity: Optional[float] = Field(None, ge=0, le=100)

class TestSessionCreate(TestSessionBase):
    """테스트 세션 생성 스키마"""
    pass

class TestSessionUpdate(BaseSchema):
    """테스트 세션 수정 스키마"""
    status: Optional[TestStatusEnum] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TestSessionResponse(TestSessionBase):
    """테스트 세션 응답 스키마"""
    id: int
    session_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: TestStatusEnum
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

# MeasurementResult 스키마들
class MeasurementResultBase(BaseSchema):
    """측정 결과 기본 스키마"""
    session_id: int
    measurement_type: str = Field(..., max_length=50)
    result_data: Dict[str, Any]
    image_path: Optional[str] = Field(None, max_length=500)
    thumbnail_path: Optional[str] = Field(None, max_length=500)
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    is_valid: bool = True
    validation_notes: Optional[str] = None

class MeasurementResultCreate(MeasurementResultBase):
    """측정 결과 생성 스키마"""
    pass

class MeasurementResultUpdate(BaseSchema):
    """측정 결과 수정 스키마"""
    result_data: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    is_valid: Optional[bool] = None
    validation_notes: Optional[str] = None
    processed_at: Optional[datetime] = None

class MeasurementResultResponse(MeasurementResultBase):
    """측정 결과 응답 스키마"""
    id: int
    measured_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# SystemLog 스키마들
class SystemLogBase(BaseSchema):
    """시스템 로그 기본 스키마"""
    log_level: LogLevelEnum
    module: str = Field(..., max_length=100)
    function_name: Optional[str] = Field(None, max_length=100)
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    """시스템 로그 생성 스키마"""
    pass

class SystemLogResponse(SystemLogBase):
    """시스템 로그 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

# 통계 및 집계 스키마들
class TestStatistics(BaseSchema):
    """테스트 통계 스키마"""
    total_tests: int
    completed_tests: int
    failed_tests: int
    success_rate: float
    average_duration: Optional[float] = None

class UserStatistics(BaseSchema):
    """사용자 통계 스키마"""
    total_users: int
    active_users: int
    admin_count: int
    operator_count: int

# 모든 스키마 export
__all__ = [
    # Enums
    'GenderEnum', 'UserRoleEnum', 'TestStatusEnum', 'LogLevelEnum',
    
    # Patient schemas
    'PatientBase', 'PatientCreate', 'PatientUpdate', 'PatientResponse',
    
    # TestType schemas
    'TestTypeBase', 'TestTypeCreate', 'TestTypeUpdate', 'TestTypeResponse',
    
    # User schemas
    'UserBase', 'UserCreate', 'UserUpdate', 'UserResponse',
    
    # TestSession schemas
    'TestSessionBase', 'TestSessionCreate', 'TestSessionUpdate', 'TestSessionResponse',
    
    # MeasurementResult schemas
    'MeasurementResultBase', 'MeasurementResultCreate', 'MeasurementResultUpdate', 'MeasurementResultResponse',
    
    # SystemLog schemas
    'SystemLogBase', 'SystemLogCreate', 'SystemLogResponse',
    
    # Statistics schemas
    'TestStatistics', 'UserStatistics'
]
