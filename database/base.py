# -*- coding: utf-8 -*-
"""
SQLAlchemy Base Classes and Common Mixins
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base

# Base 클래스 생성
Base = declarative_base()

class TimestampMixin:
    """타임스탬프 믹스인 - 생성/수정 시간 자동 관리"""
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="생성 시간"
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 시간"
    )

class SoftDeleteMixin:
    """소프트 삭제 믹스인 - 물리적 삭제 대신 삭제 플래그 사용"""
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="삭제 시간"
    )
    
    def soft_delete(self):
        """소프트 삭제 실행"""
        self.deleted_at = datetime.now()
    
    def restore(self):
        """삭제 취소"""
        self.deleted_at = None
    
    @property
    def is_deleted(self) -> bool:
        """삭제 여부 확인"""
        return self.deleted_at is not None

class BaseModel(Base, TimestampMixin):
    """모든 모델의 기본 클래스"""
    
    __abstract__ = True
    
    id = Column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="기본키"
    )
    
    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        """문자열 표현"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={getattr(self, 'id', None)})>"
