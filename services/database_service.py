# -*- coding: utf-8 -*-
"""
Database Service - ORM 기반 데이터베이스 서비스
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

# ORM이 설치되지 않은 경우를 대비한 예외 처리
try:
    from database.connection import db_manager, get_db_session
    from database.repositories import RepositoryFactory
    from database.schemas import (
        PatientCreate, PatientUpdate, PatientResponse,
        TestTypeCreate, TestTypeUpdate, TestTypeResponse,
        UserCreate, UserUpdate, UserResponse,
        TestSessionCreate, TestSessionUpdate, TestSessionResponse,
        MeasurementResultCreate, MeasurementResultUpdate, MeasurementResultResponse,
        SystemLogCreate, SystemLogResponse
    )
    ORM_AVAILABLE = True
except ImportError:
    ORM_AVAILABLE = False
    logging.warning("ORM dependencies not available. Database service will use fallback mode.")

logger = logging.getLogger(__name__)

class DatabaseService:
    """ORM 기반 데이터베이스 서비스"""
    
    def __init__(self):
        self.orm_available = ORM_AVAILABLE
        self._repository_factory = None
        
        if self.orm_available:
            try:
                # 데이터베이스 연결 테스트
                if db_manager.test_connection():
                    self._repository_factory = RepositoryFactory(get_db_session())
                    logger.info("Database service initialized with ORM")
                else:
                    self.orm_available = False
                    logger.warning("Database connection failed. Using fallback mode.")
            except Exception as e:
                self.orm_available = False
                logger.error(f"Failed to initialize database service: {e}")
        
        if not self.orm_available:
            logger.info("Database service initialized in fallback mode")
    
    def is_available(self) -> bool:
        """ORM 사용 가능 여부"""
        return self.orm_available
    
    # Patient 관련 메서드들
    def create_patient(self, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """환자 생성"""
        if not self.orm_available:
            return self._create_patient_fallback(patient_data)
        
        try:
            patient_schema = PatientCreate(**patient_data)
            patient_repo = self._repository_factory.get_patient_repository()
            patient = patient_repo.create(patient_schema)
            return PatientResponse.from_orm(patient).dict()
        except Exception as e:
            logger.error(f"Failed to create patient: {e}")
            return None
    
    def get_patient(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """환자 조회"""
        if not self.orm_available:
            return self._get_patient_fallback(patient_id)
        
        try:
            patient_repo = self._repository_factory.get_patient_repository()
            patient = patient_repo.get(patient_id)
            if patient:
                return PatientResponse.from_orm(patient).dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get patient: {e}")
            return None
    
    def get_patient_by_code(self, patient_code: str) -> Optional[Dict[str, Any]]:
        """환자 코드로 조회"""
        if not self.orm_available:
            return self._get_patient_by_code_fallback(patient_code)
        
        try:
            patient_repo = self._repository_factory.get_patient_repository()
            patient = patient_repo.get_by_patient_code(patient_code)
            if patient:
                return PatientResponse.from_orm(patient).dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get patient by code: {e}")
            return None
    
    def update_patient(self, patient_id: int, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """환자 정보 업데이트"""
        if not self.orm_available:
            return self._update_patient_fallback(patient_id, patient_data)
        
        try:
            patient_repo = self._repository_factory.get_patient_repository()
            patient = patient_repo.get(patient_id)
            if patient:
                patient_schema = PatientUpdate(**patient_data)
                updated_patient = patient_repo.update(patient, patient_schema)
                return PatientResponse.from_orm(updated_patient).dict()
            return None
        except Exception as e:
            logger.error(f"Failed to update patient: {e}")
            return None
    
    # TestSession 관련 메서드들
    def create_test_session(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """테스트 세션 생성"""
        if not self.orm_available:
            return self._create_test_session_fallback(session_data)
        
        try:
            session_schema = TestSessionCreate(**session_data)
            session_repo = self._repository_factory.get_test_session_repository()
            session = session_repo.create(session_schema)
            return TestSessionResponse.from_orm(session).dict()
        except Exception as e:
            logger.error(f"Failed to create test session: {e}")
            return None
    
    def get_test_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """테스트 세션 조회"""
        if not self.orm_available:
            return self._get_test_session_fallback(session_id)
        
        try:
            session_repo = self._repository_factory.get_test_session_repository()
            session = session_repo.get(session_id)
            if session:
                return TestSessionResponse.from_orm(session).dict()
            return None
        except Exception as e:
            logger.error(f"Failed to get test session: {e}")
            return None
    
    def update_test_session(self, session_id: int, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """테스트 세션 업데이트"""
        if not self.orm_available:
            return self._update_test_session_fallback(session_id, session_data)
        
        try:
            session_repo = self._repository_factory.get_test_session_repository()
            session = session_repo.get(session_id)
            if session:
                session_schema = TestSessionUpdate(**session_data)
                updated_session = session_repo.update(session, session_schema)
                return TestSessionResponse.from_orm(updated_session).dict()
            return None
        except Exception as e:
            logger.error(f"Failed to update test session: {e}")
            return None
    
    # MeasurementResult 관련 메서드들
    def create_measurement_result(self, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """측정 결과 생성"""
        if not self.orm_available:
            return self._create_measurement_result_fallback(result_data)
        
        try:
            result_schema = MeasurementResultCreate(**result_data)
            result_repo = self._repository_factory.get_measurement_result_repository()
            result = result_repo.create(result_schema)
            return MeasurementResultResponse.from_orm(result).dict()
        except Exception as e:
            logger.error(f"Failed to create measurement result: {e}")
            return None
    
    def get_measurement_results_by_session(self, session_id: int) -> List[Dict[str, Any]]:
        """세션별 측정 결과 조회"""
        if not self.orm_available:
            return self._get_measurement_results_by_session_fallback(session_id)
        
        try:
            result_repo = self._repository_factory.get_measurement_result_repository()
            results = result_repo.get_by_session(session_id)
            return [MeasurementResultResponse.from_orm(result).dict() for result in results]
        except Exception as e:
            logger.error(f"Failed to get measurement results: {e}")
            return []
    
    # SystemLog 관련 메서드들
    def create_system_log(self, log_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """시스템 로그 생성"""
        if not self.orm_available:
            return self._create_system_log_fallback(log_data)
        
        try:
            log_schema = SystemLogCreate(**log_data)
            log_repo = self._repository_factory.get_system_log_repository()
            log = log_repo.create(log_schema)
            return SystemLogResponse.from_orm(log).dict()
        except Exception as e:
            logger.error(f"Failed to create system log: {e}")
            return None
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """최근 로그 조회"""
        if not self.orm_available:
            return self._get_recent_logs_fallback(limit)
        
        try:
            log_repo = self._repository_factory.get_system_log_repository()
            logs = log_repo.get_recent_logs(limit)
            return [SystemLogResponse.from_orm(log).dict() for log in logs]
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    # Fallback 메서드들 (ORM 없이 동작)
    def _create_patient_fallback(self, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """환자 생성 fallback"""
        logger.info("Creating patient in fallback mode")
        # 메모리 기반 더미 데이터 생성
        return {
            'id': 1,
            'patient_code': patient_data.get('patient_code', 'DUMMY001'),
            'birth_year': patient_data.get('birth_year'),
            'gender': patient_data.get('gender'),
            'notes': patient_data.get('notes'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _get_patient_fallback(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """환자 조회 fallback"""
        logger.info(f"Getting patient {patient_id} in fallback mode")
        return {
            'id': patient_id,
            'patient_code': f'DUMMY{patient_id:03d}',
            'birth_year': 1990,
            'gender': 'U',
            'notes': 'Fallback patient data',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _get_patient_by_code_fallback(self, patient_code: str) -> Optional[Dict[str, Any]]:
        """환자 코드 조회 fallback"""
        logger.info(f"Getting patient by code {patient_code} in fallback mode")
        return self._get_patient_fallback(1)
    
    def _update_patient_fallback(self, patient_id: int, patient_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """환자 업데이트 fallback"""
        logger.info(f"Updating patient {patient_id} in fallback mode")
        result = self._get_patient_fallback(patient_id)
        if result:
            result.update(patient_data)
            result['updated_at'] = datetime.now()
        return result
    
    def _create_test_session_fallback(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """테스트 세션 생성 fallback"""
        logger.info("Creating test session in fallback mode")
        return {
            'id': 1,
            'session_id': 'dummy-session-uuid',
            'test_type_id': session_data.get('test_type_id', 1),
            'operator_id': session_data.get('operator_id', 1),
            'patient_id': session_data.get('patient_id'),
            'started_at': datetime.now(),
            'status': 'in_progress',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _get_test_session_fallback(self, session_id: int) -> Optional[Dict[str, Any]]:
        """테스트 세션 조회 fallback"""
        logger.info(f"Getting test session {session_id} in fallback mode")
        return {
            'id': session_id,
            'session_id': f'dummy-session-{session_id}',
            'test_type_id': 1,
            'operator_id': 1,
            'patient_id': 1,
            'started_at': datetime.now(),
            'status': 'in_progress',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _update_test_session_fallback(self, session_id: int, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """테스트 세션 업데이트 fallback"""
        logger.info(f"Updating test session {session_id} in fallback mode")
        result = self._get_test_session_fallback(session_id)
        if result:
            result.update(session_data)
            result['updated_at'] = datetime.now()
        return result
    
    def _create_measurement_result_fallback(self, result_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """측정 결과 생성 fallback"""
        logger.info("Creating measurement result in fallback mode")
        return {
            'id': 1,
            'session_id': result_data.get('session_id', 1),
            'measurement_type': result_data.get('measurement_type', 'dummy'),
            'result_data': result_data.get('result_data', {}),
            'is_valid': True,
            'measured_at': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _get_measurement_results_by_session_fallback(self, session_id: int) -> List[Dict[str, Any]]:
        """세션별 측정 결과 조회 fallback"""
        logger.info(f"Getting measurement results for session {session_id} in fallback mode")
        return [self._create_measurement_result_fallback({'session_id': session_id})]
    
    def _create_system_log_fallback(self, log_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """시스템 로그 생성 fallback"""
        return {
            'id': 1,
            'log_level': log_data.get('log_level', 'INFO'),
            'module': log_data.get('module', 'fallback'),
            'message': log_data.get('message', 'Fallback log message'),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def _get_recent_logs_fallback(self, limit: int = 100) -> List[Dict[str, Any]]:
        """최근 로그 조회 fallback"""
        logger.info(f"Getting recent logs (limit: {limit}) in fallback mode")
        return [self._create_system_log_fallback({'message': f'Fallback log {i}'}) for i in range(min(limit, 5))]

# 전역 데이터베이스 서비스 인스턴스
database_service = DatabaseService()

# 편의 함수들
def get_database_service() -> DatabaseService:
    """데이터베이스 서비스 인스턴스 반환"""
    return database_service

def is_orm_available() -> bool:
    """ORM 사용 가능 여부"""
    return database_service.is_available()
