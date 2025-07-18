# -*- coding: utf-8 -*-
"""
Alembic Environment Configuration
"""

import os
import sys
from logging.config import fileConfig

try:
    from sqlalchemy import engine_from_config
    from sqlalchemy import pool
    from alembic import context
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False
    print("Alembic not available. Please install with: pip install alembic")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
if ALEMBIC_AVAILABLE:
    # 프로젝트 루트를 sys.path에 추가
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    
    try:
        from database.base import Base
        from database.models import *  # 모든 모델 import
        target_metadata = Base.metadata
    except ImportError:
        print("Warning: Could not import database models. Alembic will run without autogenerate support.")
        target_metadata = None
else:
    target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """데이터베이스 URL 가져오기 (환경변수 우선)"""
    # 환경변수에서 데이터베이스 URL 확인
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # docker-compose 환경변수들로 URL 구성
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'calth_reader')
    db_user = os.getenv('DB_USER', 'calth_user')
    db_password = os.getenv('DB_PASSWORD', 'calth_pass123')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    if not ALEMBIC_AVAILABLE:
        print("Alembic not available. Cannot run offline migrations.")
        return
        
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    if not ALEMBIC_AVAILABLE:
        print("Alembic not available. Cannot run online migrations.")
        return
        
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
