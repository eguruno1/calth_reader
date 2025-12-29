"""
controllers.session_context의 Docstring
로그인 정보를 세션에 담는다.
CREATE = "CREATE"
READ   = "READ"
UPDATE = "UPDATE"
DELETE = "DELETE"
LOGIN  = "LOGIN"
LOGOUT = "LOGOUT"
"""
# controllers/session_context.py

import uuid

_current_context = {
    "user_pk"    : None,     # ⭐ users.id (BIGINT)
    "user_id"    : None,     # users.user_id (문자)
    "role"       : None,     # 사용자 권한.
    "session_id" : None,
    "ip_address" : None,
    "user_agent" : None,
}

def set_session_context(*, user_pk, user_id, role, ip_address=None, user_agent=None):
    global _current_context

    _current_context["user_pk"]    = user_pk
    _current_context["user_id"]    = user_id
    _current_context["role"]       = role
    _current_context["session_id"] = uuid.uuid4()
    _current_context["ip_address"] = ip_address
    _current_context["user_agent"] = user_agent


def clear_session_context():
    """
    세션 컨텍스트 초기화 (로그아웃 / 재인증 실패 시 사용)
    """
    global _current_context

    _current_context.update({
        "user_pk"    : None,
        "user_id"    : None,
        "role"       : None,
        "session_id" : None,
        "ip_address" : None,
        "user_agent" : None,
    })


def get_session_context():
    return _current_context
