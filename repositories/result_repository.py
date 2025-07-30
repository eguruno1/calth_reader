# -*- coding: utf-8 -*-
"""
Results Repository - 결과 데이터 접근 계층
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from models.database_models import (
    PatientResultDB, CalibrationResultDB, QCResultDB,
    get_db_manager, CalibrationItemTypeEnum, ControlTypeEnum
)

class BaseResultRepository:
    """기본 결과 Repository"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def get_session(self) -> Session:
        """데이터베이스 세션 반환"""
        return self.db_manager.get_session()

class PatientResultRepository(BaseResultRepository):
    """환자 결과 Repository"""
    
    def get_all(self, order_by: str = 'test_date', ascending: bool = False) -> List[PatientResultDB]:
        """모든 환자 결과 조회"""
        session = self.get_session()
        try:
            query = session.query(PatientResultDB)
            
            # 정렬 처리
            if hasattr(PatientResultDB, order_by):
                order_field = getattr(PatientResultDB, order_by)
                if ascending:
                    query = query.order_by(asc(order_field))
                else:
                    query = query.order_by(desc(order_field))
            
            return query.all()
        finally:
            session.close()
    
    def get_by_patient_id(self, patient_id: str) -> List[PatientResultDB]:
        """환자 ID로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(PatientResultDB).filter(
                PatientResultDB.patient_id == patient_id
            ).order_by(desc(PatientResultDB.test_date)).all()
        finally:
            session.close()
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[PatientResultDB]:
        """날짜 범위로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(PatientResultDB).filter(
                PatientResultDB.test_date >= start_date,
                PatientResultDB.test_date <= end_date
            ).order_by(desc(PatientResultDB.test_date)).all()
        finally:
            session.close()
    
    def get_by_operator(self, operator_id: str) -> List[PatientResultDB]:
        """조작자 ID로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(PatientResultDB).filter(
                PatientResultDB.operator_id == operator_id
            ).order_by(desc(PatientResultDB.test_date)).all()
        finally:
            session.close()

class CalibrationResultRepository(BaseResultRepository):
    """교정 결과 Repository"""
    
    def get_all(self, order_by: str = 'test_date', ascending: bool = False) -> List[CalibrationResultDB]:
        """모든 교정 결과 조회"""
        session = self.get_session()
        try:
            query = session.query(CalibrationResultDB)
            
            # 정렬 처리
            if hasattr(CalibrationResultDB, order_by):
                order_field = getattr(CalibrationResultDB, order_by)
                if ascending:
                    query = query.order_by(asc(order_field))
                else:
                    query = query.order_by(desc(order_field))
            
            return query.all()
        finally:
            session.close()
    
    def get_by_device_id(self, device_id: str) -> List[CalibrationResultDB]:
        """장치 ID로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(CalibrationResultDB).filter(
                CalibrationResultDB.device_id == device_id
            ).order_by(desc(CalibrationResultDB.test_date)).all()
        finally:
            session.close()
    
    def get_by_item_type(self, item_type: CalibrationItemTypeEnum) -> List[CalibrationResultDB]:
        """항목 타입으로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(CalibrationResultDB).filter(
                CalibrationResultDB.item_type == item_type
            ).order_by(desc(CalibrationResultDB.test_date)).all()
        finally:
            session.close()

class QCResultRepository(BaseResultRepository):
    """QC 결과 Repository"""
    
    def get_all(self, order_by: str = 'test_date', ascending: bool = False) -> List[QCResultDB]:
        """모든 QC 결과 조회"""
        session = self.get_session()
        try:
            query = session.query(QCResultDB)
            
            # 정렬 처리
            if hasattr(QCResultDB, order_by):
                order_field = getattr(QCResultDB, order_by)
                if ascending:
                    query = query.order_by(asc(order_field))
                else:
                    query = query.order_by(desc(order_field))
            
            return query.all()
        finally:
            session.close()
    
    def get_by_control_type(self, control_type: ControlTypeEnum) -> List[QCResultDB]:
        """컨트롤 타입으로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(QCResultDB).filter(
                QCResultDB.control_type == control_type
            ).order_by(desc(QCResultDB.test_date)).all()
        finally:
            session.close()
    
    def get_by_item(self, item: str) -> List[QCResultDB]:
        """검사 항목으로 결과 조회"""
        session = self.get_session()
        try:
            return session.query(QCResultDB).filter(
                QCResultDB.item == item
            ).order_by(desc(QCResultDB.test_date)).all()
        finally:
            session.close()

# Repository 인스턴스들
patient_result_repo = PatientResultRepository()
calibration_result_repo = CalibrationResultRepository()
qc_result_repo = QCResultRepository()
