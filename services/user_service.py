# -*- coding: utf-8 -*-
"""
User Service - 사용자 관리 서비스 (PostgreSQL 단일화)
"""
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional, List
import bcrypt
import hashlib
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models import User

from controllers.session_context import (set_session_context, clear_session_context)

class UserService(QObject):
    """사용자 관리 서비스"""

    # =========================
    # Signals
    # =========================
    login_success = pyqtSignal(str)    # user_id
    login_failed = pyqtSignal(str)     # error message
    logout_completed = pyqtSignal()
    user_changed = pyqtSignal(dict)    # user info

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._initialized = False
        self._current_user = None

    # =========================
    # Initialization
    # =========================
    def initialize(self) -> bool:
        """서비스 초기화 (DB 연결 확인)"""
        if self._initialized:
            return True

        try:
            session = get_db_session()
            session.execute(text("SELECT 1")) # SQLAlchemy 2.x 대응
            session.close()

            self._initialized = True
            print("UserService 초기화 완료 (PostgreSQL)")
            return True

        except Exception as e:
            print(f"UserService 초기화 failed: {e}")
            return False

    # =========================
    # 로그인
    # =========================
    def login(self, user_id: str, password: str) -> bool:
        """
        로그인 (PostgreSQL)
        로그인 (평문 → bcrypt 자동 마이그레이션 지원)
        """
        if not user_id or not password:
            self.login_failed.emit("사용자 ID와 비밀번호를 입력해주세요.")
            return False

        session: Session = get_db_session()

        try:
            user = (
                session.query(User)
                .filter(
                    User.user_id == user_id,
                    User.is_active.is_(True)
                )
                .first()
            )

            if not user:
                self.login_failed.emit("존재하지 않는 사용자입니다.")
                return False

            stored_hash = user.password_hash or ""
            input_pw    = password.encode("utf-8")

            # ==================================================
            # 1️⃣ bcrypt 비밀번호 (두 번째 로그인부터)
            # ==================================================
            if self._is_bcrypt_hash(stored_hash):
                if not bcrypt.checkpw(input_pw, stored_hash.encode("utf-8")):
                    self.login_failed.emit("비밀번호가 올바르지 않습니다.")
                    return False

            # ==================================================
            # 2️⃣ SHA-256 비밀번호 (기존 시스템)
            # ==================================================
            elif len(stored_hash) == 64 and all(c in "0123456789abcdef" for c in stored_hash.lower()):
                sha256 = hashlib.sha256(input_pw).hexdigest()
                if sha256 != stored_hash:
                    self.login_failed.emit("비밀번호가 올바르지 않습니다.")
                    return False

                # 🔁 bcrypt로 업그레이드
                user.password_hash = bcrypt.hashpw(
                    input_pw, bcrypt.gensalt()
                ).decode("utf-8")

                print(f"[SECURITY] SHA256 → bcrypt migrated: {user.user_id}")

            # ==================================================
            # 3️⃣ 평문 비밀번호 (최초 로그인)
            # ==================================================
            else:
                if password != stored_hash:
                    self.login_failed.emit("비밀번호가 올바르지 않습니다.")
                    return False

                # 🔁 bcrypt로 업그레이드
                user.password_hash = bcrypt.hashpw(
                    input_pw, bcrypt.gensalt()
                ).decode("utf-8")

                print(f"[SECURITY] Plain → bcrypt migrated: {user.user_id}")

            # ==================================================
            # 공통 로그인 성공 처리
            # ==================================================
            role_value = (
                user.role.value if hasattr(user.role, "value") else str(user.role)
            ).lower()

            """
            if role_value != "admin":
                self.login_failed.emit("관리자 계정만 접근 가능합니다.")
                return False
            """
            user.last_login = session.execute(text("SELECT now()")).scalar()
            session.commit()

            # 로그인 성공 처리 직후
            self._current_user = user
            # ✅ session_context 세팅
            set_session_context(
                user_id    = user.id,
                ip_address = None,      # 데스크탑 앱이면 None OK
                user_agent = "CalthReader-App"
            )
            self.login_success.emit(user.user_id)
            self.user_changed.emit(self._build_user_info(user))

            print(f"Admin Login success: {user.user_id}")
            return True

        except Exception as e:
            session.rollback()
            self.login_failed.emit(f"로그인 오류: {str(e)}")
            return False

        finally:
            session.close()

    # =============================
    # 로그아웃
    # =============================
    def logout(self):
        """로그아웃"""
        self._current_user = None
        clear_session_context()  # session Clear
        self.logout_completed.emit()
        self.user_changed.emit({})

    # =========================
    # User 상태 / 정보
    # =========================
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return self._current_user is not None

    def get_current_user(self) -> Optional[User]:
        """현재 사용자 반환"""
        return self._current_user

    def get_current_user_id(self) -> str:
        """현재 사용자 ID"""
        return self._current_user.user_id if self._current_user else ""

    def get_current_user_display_name(self) -> str:
        """현재 사용자 표시 이름"""
        return self._current_user.name if self._current_user else ""

    def has_permission(self, required_role: str) -> bool:
        """권한 확인"""
        if not self._current_user:
            return False
        return self._current_user.role == required_role

    def get_user_info(self) -> dict:
        """사용자 정보 반환"""
        if not self._current_user:
            return {}
        return self._build_user_info(self._current_user)

    # =========================
    # Users 조회
    # =========================
    def get_available_users(self) -> List[dict]:
        """
        활성 사용자 목록 조회 (PostgreSQL)
        Admin / Operator / Viewer
        """
        print("📡 get_available_users() 호출됨")

        session: Session = get_db_session()
        try:
            users = (
                session.query(User)
                .filter(User.is_active.is_(True))
                .order_by(User.user_id)
                .all()
            )

            print(f"👥 DB에서 조회된 사용자 수: {len(users)}")

            result = []
            for user in users:
                result.append({
                    "id": user.user_id,
                    "name": user.name,
                    "role": (
                        user.role.value
                        if hasattr(user.role, "value")
                        else str(user.role)
                    ),
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                    "is_active": user.is_active,
                })

            return result

        except Exception as e:
            print(f"get_available_users error: {e}")
            return []

        finally:
            session.close()

    # =========================
    # Helpers
    # =========================
    def _build_user_info(self, user: User) -> dict:
        return {
            "id": user.user_id,
            "name": user.name,
            "role": (
                user.role.value
                if hasattr(user.role, "value")
                else str(user.role)
            ),
            "created_at": user.created_at,
            "last_login": user.last_login,
            "is_active": user.is_active,
        }
    
    # bcrypt 해시 여부 확인.
    def _is_bcrypt_hash(self, hashed: str) -> bool:
        return hashed.startswith("$2a$") or hashed.startswith("$2b$") or hashed.startswith("$2y$")
    
    """
    계정 생성시 비밀번호 암호화.
    """
    @staticmethod
    def create_user_password(password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")




# =========================
# Singleton
# =========================
_user_service_instance: Optional[UserService] = None

"""UserService 싱글톤 인스턴스 반환"""
def get_user_service() -> UserService:
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
        _user_service_instance.initialize()
    return _user_service_instance

# 직접 import 가능한 인스턴스
# Direct import
user_service = get_user_service()