# -*- coding: utf-8 -*-
"""
Base Repository Pattern Implementation
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from abc import ABC, abstractmethod

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import and_, or_, desc, asc
except ImportError:
    # SQLAlchemy가 설치되지 않은 경우 기본 클래스들 정의
    class Session:
        pass

# Generic type for model
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """기본 Repository 클래스"""
    
    def __init__(self, model: Type[ModelType], db_session: Session):
        self.model = model
        self.db_session = db_session
    
    def get(self, id: int) -> Optional[ModelType]:
        """ID로 단일 레코드 조회"""
        return self.db_session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """모든 레코드 조회 (페이징)"""
        return self.db_session.query(self.model).offset(skip).limit(limit).all()
    
    def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """특정 필드값으로 레코드 조회"""
        field = getattr(self.model, field_name)
        return self.db_session.query(self.model).filter(field == value).first()
    
    def get_multi_by_field(self, field_name: str, value: Any, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """특정 필드값으로 여러 레코드 조회"""
        field = getattr(self.model, field_name)
        return self.db_session.query(self.model).filter(field == value).offset(skip).limit(limit).all()
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """새 레코드 생성"""
        if hasattr(obj_in, 'dict'):
            obj_in_data = obj_in.dict()
        else:
            obj_in_data = obj_in
            
        db_obj = self.model(**obj_in_data)
        self.db_session.add(db_obj)
        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj
    
    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """기존 레코드 업데이트"""
        if hasattr(obj_in, 'dict'):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in
            
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db_session.add(db_obj)
        self.db_session.commit()
        self.db_session.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """레코드 삭제"""
        obj = self.db_session.query(self.model).filter(self.model.id == id).first()
        if obj:
            self.db_session.delete(obj)
            self.db_session.commit()
            return True
        return False
    
    def count(self) -> int:
        """전체 레코드 수"""
        return self.db_session.query(self.model).count()
    
    def exists(self, id: int) -> bool:
        """레코드 존재 여부"""
        return self.db_session.query(self.model).filter(self.model.id == id).first() is not None
    
    def search(self, filters: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[ModelType]:
        """동적 필터링 검색"""
        query = self.db_session.query(self.model)
        
        for field_name, value in filters.items():
            if hasattr(self.model, field_name) and value is not None:
                field = getattr(self.model, field_name)
                if isinstance(value, str) and '%' in value:
                    query = query.filter(field.like(value))
                else:
                    query = query.filter(field == value)
        
        return query.offset(skip).limit(limit).all()

# 특화된 Repository 클래스들
class PatientRepository(BaseRepository):
    """환자 Repository"""
    
    def get_by_patient_code(self, patient_code: str):
        """환자 코드로 조회"""
        return self.get_by_field('patient_code', patient_code)
    
    def get_by_birth_year(self, birth_year: int):
        """출생년도로 조회"""
        return self.get_multi_by_field('birth_year', birth_year)

class TestTypeRepository(BaseRepository):
    """테스트 유형 Repository"""
    
    def get_by_code(self, code: str):
        """테스트 유형 코드로 조회"""
        return self.get_by_field('code', code)
    
    def get_active_test_types(self):
        """활성화된 테스트 유형들"""
        return self.db_session.query(self.model).filter(self.model.is_active == True).all()

class UserRepository(BaseRepository):
    """사용자 Repository"""
    
    def get_by_user_id(self, user_id: str):
        """사용자 ID로 조회"""
        return self.get_by_field('user_id', user_id)
    
    def get_by_role(self, role: str):
        """역할별 사용자 조회"""
        return self.get_multi_by_field('role', role)
    
    def get_active_users(self):
        """활성화된 사용자들"""
        return self.db_session.query(self.model).filter(self.model.is_active == True).all()
    
    def authenticate(self, user_id: str, password_hash: str):
        """사용자 인증"""
        return self.db_session.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.password_hash == password_hash,
                self.model.is_active == True
            )
        ).first()

class TestSessionRepository(BaseRepository):
    """테스트 세션 Repository"""
    
    def get_by_session_id(self, session_id):
        """세션 ID로 조회"""
        return self.get_by_field('session_id', session_id)
    
    def get_by_operator(self, operator_id: int):
        """운영자별 세션 조회"""
        return self.get_multi_by_field('operator_id', operator_id)
    
    def get_by_patient(self, patient_id: int):
        """환자별 세션 조회"""
        return self.get_multi_by_field('patient_id', patient_id)
    
    def get_by_status(self, status: str):
        """상태별 세션 조회"""
        return self.get_multi_by_field('status', status)
    
    def get_recent_sessions(self, limit: int = 10):
        """최근 세션들"""
        return self.db_session.query(self.model).order_by(desc(self.model.started_at)).limit(limit).all()

class MeasurementResultRepository(BaseRepository):
    """측정 결과 Repository"""
    
    def get_by_session(self, session_id: int):
        """세션별 측정 결과 조회"""
        return self.get_multi_by_field('session_id', session_id)
    
    def get_by_measurement_type(self, measurement_type: str):
        """측정 유형별 결과 조회"""
        return self.get_multi_by_field('measurement_type', measurement_type)
    
    def get_valid_results(self):
        """유효한 측정 결과들"""
        return self.db_session.query(self.model).filter(self.model.is_valid == True).all()

class SystemLogRepository(BaseRepository):
    """시스템 로그 Repository"""
    
    def get_by_level(self, log_level: str):
        """로그 레벨별 조회"""
        return self.get_multi_by_field('log_level', log_level)
    
    def get_by_module(self, module: str):
        """모듈별 로그 조회"""
        return self.get_multi_by_field('module', module)
    
    def get_by_user(self, user_id: int):
        """사용자별 로그 조회"""
        return self.get_multi_by_field('user_id', user_id)
    
    def get_recent_logs(self, limit: int = 100):
        """최근 로그들"""
        return self.db_session.query(self.model).order_by(desc(self.model.created_at)).limit(limit).all()
    
    def get_error_logs(self, limit: int = 50):
        """에러 로그들"""
        return self.db_session.query(self.model).filter(
            self.model.log_level.in_(['ERROR', 'CRITICAL'])
        ).order_by(desc(self.model.created_at)).limit(limit).all()

# Repository 팩토리
class RepositoryFactory:
    """Repository 팩토리 클래스"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._repositories = {}
    
    def get_patient_repository(self) -> PatientRepository:
        """환자 Repository 반환"""
        if 'patient' not in self._repositories:
            from database.models import Patient
            self._repositories['patient'] = PatientRepository(Patient, self.db_session)
        return self._repositories['patient']
    
    def get_test_type_repository(self) -> TestTypeRepository:
        """테스트 유형 Repository 반환"""
        if 'test_type' not in self._repositories:
            from database.models import TestType
            self._repositories['test_type'] = TestTypeRepository(TestType, self.db_session)
        return self._repositories['test_type']
    
    def get_user_repository(self) -> UserRepository:
        """사용자 Repository 반환"""
        if 'user' not in self._repositories:
            from database.models import User
            self._repositories['user'] = UserRepository(User, self.db_session)
        return self._repositories['user']
    
    def get_test_session_repository(self) -> TestSessionRepository:
        """테스트 세션 Repository 반환"""
        if 'test_session' not in self._repositories:
            from database.models import TestSession
            self._repositories['test_session'] = TestSessionRepository(TestSession, self.db_session)
        return self._repositories['test_session']
    
    def get_measurement_result_repository(self) -> MeasurementResultRepository:
        """측정 결과 Repository 반환"""
        if 'measurement_result' not in self._repositories:
            from database.models import MeasurementResult
            self._repositories['measurement_result'] = MeasurementResultRepository(MeasurementResult, self.db_session)
        return self._repositories['measurement_result']
    
    def get_system_log_repository(self) -> SystemLogRepository:
        """시스템 로그 Repository 반환"""
        if 'system_log' not in self._repositories:
            from database.models import SystemLog
            self._repositories['system_log'] = SystemLogRepository(SystemLog, self.db_session)
        return self._repositories['system_log']
