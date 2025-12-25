"""
database.audit_logger의 Docstring
모든 View / Service에서 재사용
JSONB 자동 매핑

CREATE = "CREATE"
READ   = "READ"
UPDATE = "UPDATE"
DELETE = "DELETE"
LOGIN  = "LOGIN"
LOGOUT = "LOGOUT"
"""
from database.connection import get_db_session
from database.models import AuditLog
from typing import Optional, Dict

def write_audit_log(
    *,
    action: str,
    table_name: str,
    record_id: Optional[int],
    user_id: int,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    session_id = None,
    ip_address = None,
    user_agent: Optional[str] = None
):
    session = get_db_session()
    try:
        log = AuditLog(
            action     = action,
            table_name = table_name,
            record_id  = record_id,
            old_values = old_values,
            new_values = new_values,
            user_id    = user_id,
            session_id = session_id,
            ip_address = ip_address,
            user_agent = user_agent
        )
        session.add(log)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
