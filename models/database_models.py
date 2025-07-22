# -*- coding: utf-8 -*-
"""
Database Models - SQLAlchemy 모델
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Enum
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
            
        except Exception as e:
            session.rollback()
            print(f"초기 데이터 삽입 오류: {e}")
        finally:
            session.close()

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
