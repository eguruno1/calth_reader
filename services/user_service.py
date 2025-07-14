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
        """사용 가능한 사용자 목록 (개발/테스트용)"""
        return [
            {'id': 'admin', 'name': 'Administrator', 'role': 'admin'},
            {'id': 'operator1', 'name': 'Operator One', 'role': 'operator'},
            {'id': 'viewer1', 'name': 'Viewer One', 'role': 'viewer'}
        ]
