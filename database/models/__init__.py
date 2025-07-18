# -*- coding: utf-8 -*-
"""
Database ORM Models - SQLAlchemy models for all database tables
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    Numeric, ForeignKey, CheckConstraint, UniqueConstraint,
    JSON, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from uuid import uuid4

from database.base import BaseModel, SoftDeleteMixin

class Patient(BaseModel):
    """환자 정보 모델"""
    
    __tablename__ = 'patients'
    
    patient_code = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        comment="익명화된 환자 코드"
    )
    birth_year = Column(
        Integer, 
        comment="출생년도 (개인정보 보호를 위해 년도만)"
    )
    gender = Column(
        String(1), 
        CheckConstraint("gender IN ('M', 'F', 'U')"),
        comment="성별: M/F/U(Unknown)"
    )
    notes = Column(Text, comment="비고")
    
    # 관계 설정
    test_sessions = relationship("TestSession", back_populates="patient")

class TestType(BaseModel):
    """테스트 유형 마스터 모델"""
    
    __tablename__ = 'test_types'
    
    code = Column(
        String(20), 
        unique=True, 
        nullable=False,
        comment="테스트 유형 코드"
    )
    name = Column(
        String(100), 
        nullable=False,
        comment="테스트 유형 이름"
    )
    description = Column(Text, comment="설명")
    is_active = Column(
        Boolean, 
        default=True,
        comment="활성화 여부"
    )
    measurement_time_seconds = Column(
        Integer, 
        default=300,
        comment="예상 측정 시간(초)"
    )
    
    # 관계 설정
    test_sessions = relationship("TestSession", back_populates="test_type")

class User(BaseModel):
    """사용자 모델"""
    
    __tablename__ = 'users'
    
    user_id = Column(
        String(50), 
        unique=True, 
        nullable=False,
        comment="사용자 ID"
    )
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="암호화된 비밀번호"
    )
    name = Column(
        String(100), 
        nullable=False,
        comment="사용자 이름"
    )
    role = Column(
        String(20), 
        CheckConstraint("role IN ('admin', 'operator', 'viewer', 'maintenance')"),
        nullable=False,
        comment="사용자 역할"
    )
    email = Column(String(255), comment="이메일")
    phone = Column(String(20), comment="전화번호")
    is_active = Column(
        Boolean, 
        default=True,
        comment="활성화 여부"
    )
    last_login = Column(
        DateTime(timezone=True),
        comment="마지막 로그인"
    )
    login_attempts = Column(
        Integer, 
        default=0,
        comment="로그인 시도 횟수"
    )
    locked_until = Column(
        DateTime(timezone=True),
        comment="계정 잠금 해제 시간"
    )
    
    # 관계 설정
    test_sessions = relationship("TestSession", back_populates="operator")
    system_logs = relationship("SystemLog", back_populates="user")

class TestSession(BaseModel):
    """테스트 세션 모델"""
    
    __tablename__ = 'test_sessions'
    
    session_id = Column(
        UUID(as_uuid=True), 
        unique=True, 
        nullable=False,
        default=uuid4,
        comment="세션 고유 ID"
    )
    test_type_id = Column(
        Integer, 
        ForeignKey('test_types.id'), 
        nullable=False,
        comment="테스트 유형 ID"
    )
    operator_id = Column(
        Integer, 
        ForeignKey('users.id'), 
        nullable=False,
        comment="운영자 ID"
    )
    patient_id = Column(
        Integer, 
        ForeignKey('patients.id'),
        comment="환자 ID"
    )
    device_serial = Column(String(100), comment="기기 시리얼 번호")
    cartridge_lot = Column(String(50), comment="카트리지 로트 번호")
    temperature = Column(Numeric(4,1), comment="측정 시 온도")
    humidity = Column(Numeric(4,1), comment="측정 시 습도")
    started_at = Column(
        DateTime(timezone=True),
        default="now()",
        comment="시작 시간"
    )
    completed_at = Column(
        DateTime(timezone=True),
        comment="완료 시간"
    )
    status = Column(
        String(20), 
        CheckConstraint("status IN ('in_progress', 'completed', 'failed', 'cancelled', 'error')"),
        default='in_progress',
        comment="상태"
    )
    error_message = Column(Text, comment="오류 메시지")
    metadata = Column(JSONB, comment="추가 메타데이터")
    
    # 관계 설정
    test_type = relationship("TestType", back_populates="test_sessions")
    operator = relationship("User", back_populates="test_sessions")
    patient = relationship("Patient", back_populates="test_sessions")
    measurement_results = relationship("MeasurementResult", back_populates="session")

class MeasurementResult(BaseModel):
    """측정 결과 모델"""
    
    __tablename__ = 'measurement_results'
    
    session_id = Column(
        Integer, 
        ForeignKey('test_sessions.id', ondelete='CASCADE'), 
        nullable=False,
        comment="세션 ID"
    )
    measurement_type = Column(
        String(50), 
        nullable=False,
        comment="측정 유형"
    )
    result_data = Column(
        JSONB, 
        nullable=False,
        comment="결과 데이터 (JSON)"
    )
    image_path = Column(String(500), comment="이미지 경로")
    thumbnail_path = Column(String(500), comment="썸네일 경로")
    quality_score = Column(
        Numeric(5,2),
        CheckConstraint("quality_score >= 0 AND quality_score <= 100"),
        comment="품질 점수"
    )
    is_valid = Column(
        Boolean, 
        default=True,
        comment="유효성"
    )
    validation_notes = Column(Text, comment="검증 노트")
    measured_at = Column(
        DateTime(timezone=True),
        default="now()",
        comment="측정 시간"
    )
    processed_at = Column(
        DateTime(timezone=True),
        comment="처리 시간"
    )
    raw_data = Column(LargeBinary, comment="원시 데이터")
    
    # 관계 설정
    session = relationship("TestSession", back_populates="measurement_results")

class SystemLog(BaseModel):
    """시스템 로그 모델"""
    
    __tablename__ = 'system_logs'
    
    log_level = Column(
        String(20), 
        CheckConstraint("log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')"),
        nullable=False,
        comment="로그 레벨"
    )
    module = Column(
        String(100), 
        nullable=False,
        comment="모듈명"
    )
    function_name = Column(String(100), comment="함수명")
    message = Column(Text, nullable=False, comment="로그 메시지")
    details = Column(JSONB, comment="상세 정보 (JSON)")
    user_id = Column(
        Integer, 
        ForeignKey('users.id'),
        comment="사용자 ID"
    )
    session_id = Column(
        Integer, 
        ForeignKey('test_sessions.id'),
        comment="세션 ID"
    )
    ip_address = Column(INET, comment="IP 주소")
    user_agent = Column(Text, comment="User Agent")
    
    # 관계 설정
    user = relationship("User", back_populates="system_logs")

# 모든 모델을 한 곳에서 import할 수 있도록
__all__ = [
    'Patient',
    'TestType', 
    'User',
    'TestSession',
    'MeasurementResult',
    'SystemLog'
]
