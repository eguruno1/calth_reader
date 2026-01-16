# -*- coding: utf-8 -*-
"""
Database ORM Models - SQLAlchemy models for all database tables
(PostgreSQL Only)
"""

from uuid import uuid4
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    Numeric, ForeignKey, CheckConstraint,
    JSON, LargeBinary, text,
    BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET

from sqlalchemy.sql import func

from database.base import BaseModel, SoftDeleteMixin, Base


# -------------------------------------------------
# Patient
# -------------------------------------------------
class Patient(BaseModel):
    """환자 정보 모델"""

    __tablename__ = "patients"

    patient_code = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="익명화된 환자 코드"
    )
    birth_year = Column(
        Integer,
        comment="출생년도 (년도만 저장)"
    )
    gender = Column(
        String(1),
        CheckConstraint("gender IN ('M', 'F', 'U')"),
        comment="성별"
    )
    notes = Column(Text, comment="비고")

    test_sessions = relationship(
        "TestSession",
        back_populates="patient"
    )


# -------------------------------------------------
# TestType
# -------------------------------------------------
class TestType(BaseModel):
    """테스트 유형 마스터"""

    __tablename__ = "test_types"

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
    description = Column(Text)
    is_active = Column(
        Boolean,
        default=True
    )
    measurement_time_seconds = Column(
        Integer,
        default=300,
        comment="예상 측정 시간(초)"
    )

    test_sessions = relationship(
        "TestSession",
        back_populates="test_type"
    )


# -------------------------------------------------
# User
# -------------------------------------------------
class User(BaseModel):
    """사용자"""

    __tablename__ = "users"

    user_id = Column(
        String(50),
        unique=True,
        nullable=False
    )
    password_hash = Column(
        String(255),
        nullable=False
    )
    name = Column(
        String(100),
        nullable=False
    )
    role = Column(
        String(20),
        CheckConstraint(
            "role IN ('admin', 'operator', 'viewer', 'maintenance')"
        ),
        nullable=False
    )
    email = Column(String(255))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)

    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))

    test_sessions = relationship(
        "TestSession",
        back_populates="operator"
    )
    system_logs = relationship(
        "SystemLog",
        back_populates="user"
    )


# -------------------------------------------------
# TestSession
# -------------------------------------------------
class TestSession(BaseModel):
    """테스트 세션"""

    __tablename__ = "test_sessions"

    session_id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid4
    )

    test_type_id = Column(
        Integer,
        ForeignKey("test_types.id"),
        nullable=False
    )
    operator_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    patient_id = Column(
        Integer,
        ForeignKey("patients.id")
    )

    device_serial = Column(String(100))
    cartridge_lot = Column(String(50))

    temperature = Column(Numeric(4, 1))
    humidity = Column(Numeric(4, 1))

    started_at = Column(
        DateTime(timezone=True),
        server_default=text("now()")
    )
    completed_at = Column(DateTime(timezone=True))

    status = Column(
        String(20),
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'failed', 'cancelled', 'error')"
        ),
        default="in_progress"
    )

    error_message = Column(Text)

    # ❗ 예약어 metadata 충돌 해결
    extra_metadata = Column(
        "metadata",
        JSONB,
        comment="추가 메타데이터"
    )

    test_type = relationship(
        "TestType",
        back_populates="test_sessions"
    )
    operator = relationship(
        "User",
        back_populates="test_sessions"
    )
    patient = relationship(
        "Patient",
        back_populates="test_sessions"
    )
    measurement_results = relationship(
        "MeasurementResult",
        back_populates="session",
        cascade="all, delete-orphan"
    )


# -------------------------------------------------
# MeasurementResult
# -------------------------------------------------
class MeasurementResult(BaseModel):
    """측정 결과"""

    __tablename__ = "measurement_results"

    session_id = Column(
        Integer,
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    measurement_type = Column(
        String(50),
        nullable=False
    )

    result_data = Column(
        JSONB,
        nullable=False
    )

    select_menu = Column(String(50))
    image_path = Column(String(500))
    thumbnail_path = Column(String(500))

    quality_score = Column(
        Numeric(5, 2),
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100"
        )
    )

    is_valid = Column(Boolean, default=True)
    validation_notes = Column(Text)

    measured_at = Column(
        DateTime(timezone=True),
        server_default=text("now()")
    )
    processed_at = Column(DateTime(timezone=True))

    raw_data = Column(LargeBinary)

    session = relationship(
        "TestSession",
        back_populates="measurement_results"
    )


# -------------------------------------------------
# SystemLog
# -------------------------------------------------
class SystemLog(BaseModel):
    """시스템 로그"""

    __tablename__ = "system_logs"

    log_level = Column(
        String(20),
        CheckConstraint(
            "log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')"
        ),
        nullable=False
    )

    module = Column(String(100), nullable=False)
    function_name = Column(String(100))
    message = Column(Text, nullable=False)

    details = Column(JSONB)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )
    session_id = Column(
        Integer,
        ForeignKey("test_sessions.id")
    )

    ip_address = Column(INET)
    user_agent = Column(Text)

    user = relationship(
        "User",
        back_populates="system_logs"
    )

# -------------------------------------------------
# AuditLog
# -------------------------------------------------
class AuditLog(Base):
    """데이터 작업내역 로그"""
    __tablename__ = "audit_logs"

    id         = Column(BigInteger, primary_key=True)
    action     = Column(String(50), nullable=False)

    table_name = Column(String(50))
    record_id  = Column(BigInteger)

    old_values = Column(JSONB)
    new_values = Column(JSONB)

    user_id    = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    session_id = Column(UUID)
    ip_address = Column(INET)
    user_agent = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# -------------------------------------------------
# Public Model API
# -------------------------------------------------
__all__ = [
    "Patient",
    "TestType",
    "User",
    "TestSession",
    "MeasurementResult",
    "SystemLog",
]