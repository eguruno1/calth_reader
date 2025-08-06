# -*- coding: utf-8 -*-
"""
User Service - 사용자 관리 서비스
"""
from PyQt5.QtCore import QObject, pyqtSignal
from models.user_model import UserModel, User, UserRole
from typing import Optional

class UserService(QObject):
    """사용자 관리 서비스"""
    
    # 시그널 정의
    login_success = pyqtSignal(str)  # 사용자 ID
    login_failed = pyqtSignal(str)   # 오류 메시지
    logout_completed = pyqtSignal()
    user_changed = pyqtSignal(dict)  # 사용자 정보
    
    def __init__(self, user_model: UserModel):
        super().__init__()
        self.model = user_model
        self._initialized = False
    
    def initialize(self) -> bool:
        """사용자 서비스 초기화"""
        try:
            if self._initialized:
                return True
                
            # 데이터베이스 연결 및 초기 데이터 확인
            from models.database_models import initialize_database
            initialize_database()
            
            self._initialized = True
            print("사용자 서비스 초기화 완료")
            return True
            
        except Exception as e:
            print(f"사용자 서비스 초기화 실패: {str(e)}")
            return False
    
    def login(self, user_id: str, password: str) -> bool:
        """로그인 시도"""
        try:
            if not user_id or not password:
                self.login_failed.emit("사용자 ID와 비밀번호를 입력해주세요.")
                return False
            
            if self.model.authenticate(user_id, password):
                user_info = self.model.get_user_info()
                self.login_success.emit(user_id)
                self.user_changed.emit(user_info)
                print(f"로그인 성공: {user_info['name']} ({user_info['role']})")
                return True
            else:
                self.login_failed.emit("잘못된 사용자 ID 또는 비밀번호입니다.")
                return False
                
        except Exception as e:
            error_msg = f"로그인 중 오류 발생: {str(e)}"
            self.login_failed.emit(error_msg)
            return False
    
    def logout(self):
        """로그아웃"""
        try:
            if self.model.is_logged_in():
                user_name = self.model.get_current_user_display_name()
                self.model.logout()
                self.logout_completed.emit()
                self.user_changed.emit({})
                print(f"로그아웃 완료: {user_name}")
            
        except Exception as e:
            print(f"로그아웃 중 오류: {str(e)}")
    
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return self.model.is_logged_in()
    
    def get_current_user(self) -> Optional[User]:
        """현재 사용자 반환"""
        return self.model.get_current_user()
    
    def get_current_user_display_name(self) -> str:
        """현재 사용자 표시 이름"""
        return self.model.get_current_user_display_name()
    
    def get_current_user_id(self) -> str:
        """현재 사용자 ID"""
        return self.model.get_current_user_id()
    
    def has_permission(self, required_role: UserRole) -> bool:
        """권한 확인"""
        return self.model.has_permission(required_role)
    
    def get_user_info(self) -> dict:
        """사용자 정보 반환"""
        return self.model.get_user_info()
    
    def get_available_users(self) -> list:
        """사용 가능한 사용자 목록 (데이터베이스 기반)"""
        try:
            from models.database_models import get_db_manager, UserDB, UserRoleEnum
            
            db_manager = get_db_manager()
            session = db_manager.get_session()
            
            db_users = session.query(UserDB).filter(
                UserDB.is_active == True
            ).all()
            
            users = []
            role_mapping = {
                UserRoleEnum.ADMIN: 'admin',
                UserRoleEnum.OPERATOR: 'operator',
                UserRoleEnum.VIEWER: 'viewer'
            }
            
            for db_user in db_users:
                user_info = {
                    'id': db_user.user_id,
                    'name': db_user.name,
                    'role': role_mapping[db_user.role]
                }
                users.append(user_info)
            
            session.close()
            return users
            
        except Exception as e:
            print(f"사용자 목록 조회 오류: {e}")
            # 오류 시 기본값 반환
            return [
                {'id': 'admin', 'name': 'Administrator', 'role': 'admin'},
                {'id': 'operator1', 'name': 'Operator One', 'role': 'operator'},
                {'id': 'viewer1', 'name': 'Viewer One', 'role': 'viewer'}
            ]
    
    def get_all_users(self):
        """모든 사용자 목록 조회 (활성/비활성 포함)"""
        try:
            from models.database_models import get_db_manager, UserDB, UserRoleEnum
            
            db_manager = get_db_manager()
            session = db_manager.get_session()
            
            db_users = session.query(UserDB).all()
            
            users = []
            role_mapping = {
                UserRoleEnum.ADMIN: 'admin',
                UserRoleEnum.OPERATOR: 'operator',
                UserRoleEnum.VIEWER: 'viewer'
            }
            
            for db_user in db_users:
                # User 객체처럼 속성을 가진 객체 생성
                class UserInfo:
                    def __init__(self, db_user):
                        self.user_id = db_user.user_id
                        self.username = db_user.name
                        self.role = role_mapping.get(db_user.role, 'operator')
                        self.created_at = db_user.created_at
                        self.last_login = db_user.last_login_at
                        self.is_active = db_user.is_active
                
                user_info = UserInfo(db_user)
                users.append(user_info)
            
            session.close()
            return users
            
        except Exception as e:
            print(f"전체 사용자 목록 조회 오류: {e}")
            # 오류 시 더미 데이터 반환
            class DummyUser:
                def __init__(self, user_id, username, role, is_active=True):
                    self.user_id = user_id
                    self.username = username
                    self.role = role
                    self.created_at = None
                    self.last_login = None
                    self.is_active = is_active
            
            return [
                DummyUser('admin', 'Administrator', 'admin'),
                DummyUser('operator1', 'Operator One', 'operator'),
                DummyUser('viewer1', 'Viewer One', 'viewer'),
                DummyUser('test_user', 'Test User', 'operator', False)
            ]
        
# UserService 인스턴스 생성
_user_service_instance = None

def get_user_service():
    """UserService 싱글톤 인스턴스 반환"""
    global _user_service_instance
    if _user_service_instance is None:
        from models.user_model import UserModel
        user_model = UserModel()
        _user_service_instance = UserService(user_model)
        _user_service_instance.initialize()
    return _user_service_instance

# 직접 import 가능한 인스턴스
user_service = get_user_service()