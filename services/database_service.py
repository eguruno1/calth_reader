# -*- coding: utf-8 -*-
"""
Database Service Layer
PostgreSQL + SQLAlchemy ORM 기반 서비스
"""

import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session

from database.models import (
    Patient,
    TestType,
    User,
    TestSession,
    MeasurementResult,
    SystemLog
)
from database.models import get_db_session

logger = logging.getLogger(__name__)


@contextmanager
def session_scope() -> Session:
    """
    트랜잭션 단위 세션 컨텍스트
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("Database transaction failed")
        raise
    finally:
        session.close()


class DatabaseService:
    """
    ORM 기반 DB 접근 서비스
    """

    # ---------------------------
    # Patient
    # ---------------------------
    def create_patient(self, patient_code: str, birth_year: int | None, gender: str | None):
        with session_scope() as session:
            patient = Patient(
                patient_code=patient_code,
                birth_year=birth_year,
                gender=gender
            )
            session.add(patient)
            return patient

    # ---------------------------
    # Test Session
    # ---------------------------
    def create_test_session(
        self,
        test_type: TestType,
        operator: User,
        patient: Patient | None,
        device_serial: str | None = None
    ) -> TestSession:
        with session_scope() as session:
            session.add(test_type)
            session.add(operator)
            if patient:
                session.add(patient)

            test_session = TestSession(
                test_type=test_type,
                operator=operator,
                patient=patient,
                device_serial=device_serial,
                status="in_progress"
            )
            session.add(test_session)
            return test_session

    # ---------------------------
    # Measurement Result
    # ---------------------------
    def add_measurement_result(
        self,
        session_obj: TestSession,
        measurement_type: str,
        result_data: dict,
        quality_score: float | None = None
    ) -> MeasurementResult:
        with session_scope() as session:
            session.add(session_obj)

            result = MeasurementResult(
                session=session_obj,
                measurement_type=measurement_type,
                result_data=result_data,
                quality_score=quality_score,
                is_valid=True
            )
            session.add(result)
            return result

    # ---------------------------
    # Logging
    # ---------------------------
    def write_system_log(
        self,
        level: str,
        module: str,
        message: str,
        user: User | None = None,
        session_obj: TestSession | None = None
    ):
        with session_scope() as session:
            log = SystemLog(
                log_level=level,
                module=module,
                message=message,
                user=user,
                session=session_obj
            )
            session.add(log)
            return log
