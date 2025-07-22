# -*- coding: utf-8 -*-
"""
User Model - 사용자 관리 모델
"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class UserRole(Enum):
    """사용자 역할"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

@dataclass
class User:
    """사용자 정보"""
    id: str
    password: str
    name: str
    role: UserRole
    email: Optional[str] = None
    last_login: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class UserModel:
    """사용자 관리 모델"""
    
    def __init__(self):
        self.current_user: Optional[User] = None
        self._observers = []  # 옵저버 패턴을 위한 리스트
    
    def add_observer(self, observer):
        """옵저버 추가"""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer):
        """옵저버 제거"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, event_type: str, data=None):
        """옵저버들에게 이벤트 알림"""
        for observer in self._observers:
            if hasattr(observer, 'on_user_event'):
                try:
                    observer.on_user_event(event_type, data)
                except Exception as e:
                    print(f"옵저버 알림 오류: {e}")
    
    def authenticate(self, user_id: str, password: str) -> bool:
        """사용자 인증 (데이터베이스 기반)"""
        try:
            from models.database_models import get_db_manager, UserDB, UserRoleEnum
            
            db_manager = get_db_manager()
            session = db_manager.get_session()
            
            # 데이터베이스에서 사용자 검색
            db_user = session.query(UserDB).filter(
                UserDB.user_id == user_id,
                UserDB.is_active == True
            ).first()
            
            if db_user is None:
                session.close()
                return False
            
            # 비밀번호 확인
            if db_user.password != password:
                session.close()
                return False
            
            # UserRole Enum 변환
            role_mapping = {
                UserRoleEnum.ADMIN: UserRole.ADMIN,
                UserRoleEnum.OPERATOR: UserRole.OPERATOR,
                UserRoleEnum.VIEWER: UserRole.VIEWER
            }
            
            # User 객체 생성
            user = User(
                id=db_user.user_id,
                password=db_user.password,
                name=db_user.name,
                role=role_mapping[db_user.role],
                email=db_user.email
            )
            
            # 로그인 성공 처리
            self.current_user = user
            
            # 마지막 로그인 시간 업데이트
            from datetime import datetime
            db_user.last_login = datetime.utcnow()
            session.commit()
            session.close()
            
            self.notify_observers('user_authenticated', user)
            return True
            
        except Exception as e:
            print(f"인증 중 오류 발생: {str(e)}")
            return False
    
    def logout(self):
        """로그아웃"""
        if self.current_user:
            self.notify_observers('user_logged_out', self.current_user)
        self.current_user = None
    
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[User]:
        """현재 로그인된 사용자 반환"""
        return self.current_user
    
    def get_current_user_display_name(self) -> str:
        """현재 사용자 표시 이름"""
        if self.current_user:
            return self.current_user.name
        return ""
    
    def get_current_user_id(self) -> str:
        """현재 사용자 ID"""
        if self.current_user:
            return self.current_user.id
        return ""
    
    def has_permission(self, required_role: UserRole) -> bool:
        """권한 확인"""
        if not self.current_user:
            return False
        
        # 권한 레벨: ADMIN > OPERATOR > VIEWER
        role_levels = {
            UserRole.VIEWER: 1,
            UserRole.OPERATOR: 2,
            UserRole.ADMIN: 3
        }
        
        current_level = role_levels.get(self.current_user.role, 0)
        required_level = role_levels.get(required_role, 0)
        
        return current_level >= required_level
    
    def get_user_info(self) -> dict:
        """사용자 정보 반환"""
        if self.current_user:
            return {
                'id': self.current_user.id,
                'name': self.current_user.name,
                'role': self.current_user.role.value,
                'email': self.current_user.email,
                'last_login': self.current_user.last_login,
                'is_active': self.current_user.is_active
            }
        return {}
