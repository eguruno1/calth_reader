# -*- coding: utf-8 -*-
"""
Database Connection Management
SQLAlchemy 데이터베이스 연결 관리
"""

import os
import logging
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 관리자 (SQLAlchemy 1.3.x 호환)"""

    def __init__(self):
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._current_session: Optional[Session] = None

    def get_database_url(self) -> str:
        """데이터베이스 URL 생성"""

        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5433')
        db_name = os.getenv('DB_NAME', 'calth_reader')
        db_user = os.getenv('DB_USER', 'admin')
        db_password = os.getenv('DB_PASSWORD', 'CalthReader2024!')

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    def create_engine(self) -> Engine:
        """SQLAlchemy Engine 생성 (1.3.x 호환)"""

        if self._engine is None:
            database_url = self.get_database_url()

            self._engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )

            logger.info(
                "Database engine created for: %s",
                database_url.split('@')[1]
            )

        return self._engine

    def get_session_factory(self) -> sessionmaker:
        """세션 팩토리 반환"""

        if self._session_factory is None:
            engine = self.create_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False
            )
        return self._session_factory

    def get_session(self) -> Session:
        """새 DB 세션 생성"""
        return self.get_session_factory()()

    def get_current_session(self) -> Session:
        """현재 세션 반환 (싱글톤)"""

        if self._current_session is None or not self._current_session.is_active:
            self._current_session = self.get_session()
        return self._current_session

    def close_current_session(self):
        """현재 세션 종료"""

        if self._current_session:
            self._current_session.close()
            self._current_session = None

    def test_connection(self) -> bool:
        """DB 연결 테스트 (SQLAlchemy 1.3.x 방식)"""

        try:
            engine = self.create_engine()
            conn = engine.connect()
            try:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
            finally:
                conn.close()
        except Exception as e:
            logger.error("Database connection test failed: %s", e)
            return False

    def close_all_connections(self):
        """모든 DB 연결 종료"""

        if self._current_session:
            self._current_session.close()
            self._current_session = None

        if self._engine:
            self._engine.dispose()
            self._engine = None

        self._session_factory = None
        logger.info("All database connections closed")


# 전역 DB 매니저
db_manager = DatabaseManager()


# === 편의 함수 ===

def get_db_session() -> Session:
    return db_manager.get_session()


def get_current_db_session() -> Session:
    return db_manager.get_current_session()


def close_db_session():
    db_manager.close_current_session()


def test_db_connection() -> bool:
    return db_manager.test_connection()

