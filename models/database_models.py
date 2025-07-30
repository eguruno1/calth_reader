# -*- coding: utf-8 -*-
"""
Database Models - SQLAlchemy 모델
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Enum, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import os

# Base 클래스 생성
Base = declarative_base()

class UserRoleEnum(enum.Enum):
    """사용자 역할 열거형"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class ControlTypeEnum(enum.Enum):
    """컨트롤 타입 열거형 (QC 결과용)"""
    POSITIVE = "pos"
    NEGATIVE = "neg"

class CalibrationItemTypeEnum(enum.Enum):
    """교정 항목 타입 열거형"""
    TYPE1 = "type1"
    TYPE2 = "type2"

class UserDB(Base):
    """사용자 테이블"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<User(user_id='{self.user_id}', name='{self.name}', role='{self.role.value}')>"

class PatientResultDB(Base):
    """환자 결과 테이블"""
    __tablename__ = 'patient_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item = Column(String(100), nullable=False)  # 검사 항목 (예: Influenza, COVID-19)
    test_date = Column(DateTime, nullable=False)
    operator_id = Column(String(50), nullable=False)
    patient_id = Column(String(100), nullable=False)
    result_data = Column(JSON, nullable=False)  # 결과 데이터 (JSON 형태)
    lot_number = Column(String(50), nullable=False)
    control = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PatientResult(item='{self.item}', patient_id='{self.patient_id}', date='{self.test_date}')>"

class CalibrationResultDB(Base):
    """교정 결과 테이블"""
    __tablename__ = 'calibration_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(Enum(CalibrationItemTypeEnum), nullable=False)  # Type 1 or Type 2
    test_date = Column(DateTime, nullable=False)
    operator_id = Column(String(50), nullable=False)
    device_id = Column(String(100), nullable=False)
    result_data = Column(JSON, nullable=False)  # 결과 데이터 (JSON 형태)
    lot_number = Column(String(50), nullable=False)
    control = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CalibrationResult(item_type='{self.item_type.value}', device_id='{self.device_id}', date='{self.test_date}')>"

class QCResultDB(Base):
    """QC 결과 테이블"""
    __tablename__ = 'qc_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item = Column(String(100), nullable=False)  # 검사 항목 (예: Influenza, COVID-19)
    test_date = Column(DateTime, nullable=False)
    operator_id = Column(String(50), nullable=False)
    control_type = Column(Enum(ControlTypeEnum), nullable=False)  # Pos or Neg Control
    result_data = Column(JSON, nullable=False)  # 결과 데이터 (JSON 형태)
    lot_number = Column(String(50), nullable=False)
    control = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<QCResult(item='{self.item}', control_type='{self.control_type.value}', date='{self.test_date}')>"

class DatabaseManager:
    """데이터베이스 관리자"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 프로젝트 루트에 데이터베이스 파일 생성
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'calth_reader.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 테이블 생성
        self.create_tables()
        # 초기 데이터 삽입
        self.insert_initial_data()
    
    def create_tables(self):
        """모든 테이블 생성"""
        Base.metadata.create_all(bind=self.engine)
        print(f"데이터베이스 테이블 생성 완료: {self.db_path}")
    
    def get_session(self):
        """데이터베이스 세션 가져오기"""
        return self.SessionLocal()
    
    def insert_initial_data(self):
        """초기 사용자 데이터 삽입"""
        session = self.get_session()
        try:
            # 기존 사용자가 있는지 확인
            existing_users = session.query(UserDB).count()
            if existing_users > 0:
                return
            
            # 초기 사용자들 생성
            initial_users = [
                UserDB(
                    user_id="admin",
                    password="admin123",
                    name="Administrator",
                    email="admin@calth.com",
                    role=UserRoleEnum.ADMIN
                ),
                UserDB(
                    user_id="operator1",
                    password="op123",
                    name="Operator One",
                    email="op1@calth.com",
                    role=UserRoleEnum.OPERATOR
                ),
                UserDB(
                    user_id="operator2",
                    password="op456",
                    name="Operator Two",
                    email="op2@calth.com",
                    role=UserRoleEnum.OPERATOR
                ),
                UserDB(
                    user_id="viewer1",
                    password="view123",
                    name="Viewer One",
                    email="viewer1@calth.com",
                    role=UserRoleEnum.VIEWER
                ),
                UserDB(
                    user_id="tech",
                    password="tech789",
                    name="Technician",
                    email="tech@calth.com",
                    role=UserRoleEnum.OPERATOR
                )
            ]
            
            # 데이터베이스에 추가
            for user in initial_users:
                session.add(user)
            
            session.commit()
            print(f"초기 사용자 {len(initial_users)}명 데이터베이스에 추가 완료")
            
            # 샘플 결과 데이터도 추가
            self.insert_sample_results(session)
            
        except Exception as e:
            session.rollback()
            print(f"초기 데이터 삽입 오류: {e}")
        finally:
            session.close()
    
    def insert_sample_results(self, session):
        """샘플 결과 데이터 삽입"""
        try:
            # Patient Results 샘플 데이터
            patient_results = [
                PatientResultDB(
                    item="Influenza",
                    test_date=datetime(2025, 7, 20, 10, 30),
                    operator_id="operator1",
                    patient_id="P001234",
                    result_data={"influenza_a": "NEG", "influenza_b": "POS"},
                    lot_number="LOT001",
                    control="Control A"
                ),
                PatientResultDB(
                    item="COVID-19",
                    test_date=datetime(2025, 7, 21, 14, 15),
                    operator_id="operator2",
                    patient_id="P001235",
                    result_data={"covid19": "NEG"},
                    lot_number="LOT002",
                    control="Control B"
                ),
                PatientResultDB(
                    item="Influenza",
                    test_date=datetime(2025, 7, 22, 9, 45),
                    operator_id="tech",
                    patient_id="P001236",
                    result_data={"influenza_a": "POS", "influenza_b": "NEG"},
                    lot_number="LOT001",
                    control="Control A"
                )
            ]
            
            # Calibration Results 샘플 데이터
            calibration_results = [
                CalibrationResultDB(
                    item_type=CalibrationItemTypeEnum.TYPE1,
                    test_date=datetime(2025, 7, 19, 8, 0),
                    operator_id="operator1",
                    device_id="DEV001",
                    result_data={"result": "PASS", "value": "123.45"},
                    lot_number="CAL001",
                    control="Cal Control A"
                ),
                CalibrationResultDB(
                    item_type=CalibrationItemTypeEnum.TYPE2,
                    test_date=datetime(2025, 7, 20, 8, 30),
                    operator_id="operator2",
                    device_id="DEV002",
                    result_data={"t1": "98.2", "t2": "104.7"},
                    lot_number="CAL002",
                    control="Cal Control B"
                )
            ]
            
            # QC Results 샘플 데이터
            qc_results = [
                QCResultDB(
                    item="Influenza",
                    test_date=datetime(2025, 7, 18, 7, 30),
                    operator_id="tech",
                    control_type=ControlTypeEnum.POSITIVE,
                    result_data={"influenza_a": "POS", "influenza_b": "POS"},
                    lot_number="QC001",
                    control="QC Pos Control"
                ),
                QCResultDB(
                    item="COVID-19",
                    test_date=datetime(2025, 7, 19, 7, 45),
                    operator_id="operator1",
                    control_type=ControlTypeEnum.NEGATIVE,
                    result_data={"covid19": "NEG"},
                    lot_number="QC002",
                    control="QC Neg Control"
                ),
                QCResultDB(
                    item="Influenza",
                    test_date=datetime(2025, 7, 21, 7, 30),
                    operator_id="operator2",
                    control_type=ControlTypeEnum.NEGATIVE,
                    result_data={"influenza_a": "NEG", "influenza_b": "NEG"},
                    lot_number="QC001",
                    control="QC Neg Control"
                )
            ]
            
            # 모든 샘플 데이터 추가
            for result in patient_results + calibration_results + qc_results:
                session.add(result)
                
            session.commit()
            print(f"샘플 결과 데이터 추가 완료: Patient({len(patient_results)}), Calibration({len(calibration_results)}), QC({len(qc_results)})")
            
        except Exception as e:
            session.rollback()
            print(f"샘플 데이터 삽입 오류: {e}")
            raise

# 전역 데이터베이스 매니저 인스턴스
db_manager = None

def get_db_manager():
    """데이터베이스 매니저 싱글톤 인스턴스 반환"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def initialize_database():
    """데이터베이스 초기화"""
    return get_db_manager()

if __name__ == "__main__":
    # 테스트 실행
    db_manager = get_db_manager()
    print("데이터베이스 초기화 완료")
    
    # 사용자 목록 조회
    session = db_manager.get_session()
    users = session.query(UserDB).all()
    print(f"등록된 사용자 수: {len(users)}")
    for user in users:
        print(f"  - {user.user_id}: {user.name} ({user.role.value})")
    session.close()
