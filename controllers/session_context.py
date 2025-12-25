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
    "user_id": None,
    "session_id": None,
    "ip_address": None,
    "user_agent": None,
}

def set_session_context(*, user_id, ip_address=None, user_agent=None):
    _current_context["user_id"] = user_id
    _current_context["session_id"] = uuid.uuid4()
    _current_context["ip_address"] = ip_address
    _current_context["user_agent"] = user_agent

def clear_session_context():
    _current_context.update({
        "user_id": None,
        "session_id": None,
        "ip_address": None,
        "user_agent": None,
    })

def get_session_context():
    return _current_context
