import os
from sqlalchemy import text
from database.base import engine


INIT_SQL_DIR = os.path.dirname(__file__)


def load_init_sql():
    """
    database/init/*.sql 파일을 순서대로 실행
    """
    sql_files = sorted(
        f for f in os.listdir(INIT_SQL_DIR)
        if f.endswith(".sql")
    )

    with engine.begin() as conn:
        for file in sql_files:
            path = os.path.join(INIT_SQL_DIR, file)
            with open(path, "r", encoding="utf-8") as f:
                conn.execute(text(f.read()))
