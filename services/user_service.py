# -*- coding: utf-8 -*-
"""
User Service - 사용자 관리 서비스 (PostgreSQL 단일화)
"""
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional, List
import bcrypt
import hashlib
from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Tuple

from database.connection import get_db_session
from database.models import User

from common.session_context import (set_session_context, get_session_context, clear_session_context)

class UserService(QObject):
    """사용자 관리 서비스"""

    # =========================
    # Signals
    # =========================
    login_success    = pyqtSignal(str)    # user_id
    login_failed     = pyqtSignal(str)    # error message
    logout_completed = pyqtSignal()
    user_changed     = pyqtSignal(dict)   # user info

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
            self.login_failed.emit("Please enter your user ID and password.")
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
                self.login_failed.emit("The user does not exist.")
                return False

            stored_hash = user.password_hash or ""
            input_pw    = password.encode("utf-8")

            # ==================================================
            # 1️⃣ bcrypt 비밀번호 (두 번째 로그인부터)
            # ==================================================
            if self._is_bcrypt_hash(stored_hash):
                if not bcrypt.checkpw(input_pw, stored_hash.encode("utf-8")):
                    self.login_failed.emit("Password Mismatch")
                    return False

            # ==================================================
            # 2️⃣ SHA-256 비밀번호 (기존 시스템)
            # ==================================================
            elif len(stored_hash) == 64 and all(c in "0123456789abcdef" for c in stored_hash.lower()):
                sha256 = hashlib.sha256(input_pw).hexdigest()
                if sha256 != stored_hash:
                    self.login_failed.emit("Password Mismatch")
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
                    self.login_failed.emit("Password Mismatch")
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
                user_pk    = user.id,          # ⭐ BIGINT PK
                user_id    = user.user_id,     # 문자열 ID
                role       = role_value,       # 권한.
                ip_address = None,
                user_agent = None
            )
            self.login_success.emit(user.user_id)
            self.user_changed.emit(self._build_user_info(user))

            print(f"Admin Login success: {user.user_id}")
            return True

        except Exception as e:
            session.rollback()
            self.login_failed.emit(f"Error: {str(e)}")
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
        # return self._current_user
        return get_session_context()

    def get_current_user_id(self) -> str:
        """현재 사용자 ID"""
        ctx = get_session_context()
        return ctx["user_id"] if ctx else None

    def get_current_user_display_name(self) -> str:
        """현재 사용자 표시 이름"""
        ctx = get_session_context()
        return ctx["name"] if ctx else None

    def has_permission(self, required_role: str) -> bool:
        """권한 확인"""
        ctx = get_session_context()
        return ctx["role"] if ctx else None

    def get_user_info(self) -> dict:
        """사용자 정보 반환"""
        if not self._current_user:
            return {}
        return self._build_user_info(self._current_user)

    # =========================
    # Password Verify (현재 비밀번호 확인)
    # =========================
    def verify_password(self, user_id: str, plain_password: str) -> bool:
        if not user_id or not plain_password:
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
                return False

            stored_hash = user.password_hash or ""
            input_pw = plain_password.encode("utf-8")

            # 1️⃣ bcrypt
            if self._is_bcrypt_hash(stored_hash):
                return bcrypt.checkpw(input_pw, stored_hash.encode("utf-8"))

            # 2️⃣ SHA-256
            if len(stored_hash) == 64 and all(c in "0123456789abcdef" for c in stored_hash.lower()):
                return hashlib.sha256(input_pw).hexdigest() == stored_hash

            # 3️⃣ Plain
            return plain_password == stored_hash

        except Exception as e:
            print(f"verify_password error: {e}")
            return False

        finally:
            session.close()


    # =========================
    # Password Update (비밀번호 변경)
    # =========================
    def update_password(self, user_id: str, new_password: str) -> bool:
        if not user_id or not new_password:
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
                return False

            # 🔐 항상 bcrypt로 저장
            user.password_hash = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            session.commit()
            print(f"[SECURITY] Password updated: {user.user_id}")
            return True

        except Exception as e:
            session.rollback()
            print(f"update_password error: {e}")
            return False

        finally:
            session.close()


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
            "id"   : user.user_id,
            "name" : user.name,
            "role" : (
                user.role.value
                if hasattr(user.role, "value")
                else str(user.role)
            ),
            "created_at" : user.created_at,
            "last_login" : user.last_login,
            "is_active"  : user.is_active,
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
    # Users 삭제시 관리자 로그인 실패 관리.
    # =========================    
    def verify_admin_password_with_lock_policy(self, admin_user_id: str, password: str) -> Tuple[bool, str]:
        """
        관리자 비밀번호 검증 (삭제용)
        - users.login_attempts
        - users.locked_until 사용
        """
        session = get_db_session()

        try:
            admin = (
                session.query(User)
                .filter(
                    User.user_id == admin_user_id,
                    User.is_active.is_(True)
                )
                .first()
            )

            if not admin:
                return False, "Administrator information not found"

            now = session.execute(text("SELECT now()")).scalar()

            # 🔒 Lock 상태 확인
            if admin.locked_until and admin.locked_until > now:
                remain = int((admin.locked_until - now).total_seconds() / 60) + 1
                return False, f"{remain}분 후 다시 시도해주세요."

            # 🔑 비밀번호 검증
            if self.verify_password(admin.user_id, password):
                # ✅ 성공 → 초기화
                admin.login_attempts = 0
                admin.locked_until = None
                session.commit()
                return True, "OK"

            # ❌ 실패 처리
            admin.login_attempts = (admin.login_attempts or 0) + 1

            if admin.login_attempts >= 5:
                admin.locked_until = now + timedelta(minutes=10)
                session.commit()
                return False, "After 5 failures, deletion is restricted for 10 minutes."

            session.commit()
            return False, f"The password is incorrect. ({admin.login_attempts}/5)"

        finally:
            session.close()

    # =========================
    # Admin 사용자 삭제시 잠금 상태 조회
    # =========================
    def get_admin_delete_lock_status(self, admin_user_id: str):
        """
        관리자 삭제 잠금 상태 조회
        return:
        {
            "locked": bool,
            "remain_minutes": int | None
        }
        """
        session = get_db_session()
        try:
            admin = (
                session.query(User)
                .filter(User.user_id == admin_user_id)
                .first()
            )

            if not admin or not admin.locked_until:
                return {"locked": False, "remain_minutes": None}

            now = session.execute(text("SELECT now()")).scalar()

            if admin.locked_until <= now:
                return {"locked": False, "remain_minutes": None}

            remain_sec = (admin.locked_until - now).total_seconds()
            remain_min = int(remain_sec // 60) + 1

            return {
                "locked": True,
                "remain_minutes": remain_min
            }

        finally:
            session.close()



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