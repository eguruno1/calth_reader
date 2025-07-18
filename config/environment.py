# -*- coding: utf-8 -*-
"""
환경변수 로딩 및 설정
"""

import os
from typing import Optional

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

def load_environment():
    """환경변수 로딩"""
    if DOTENV_AVAILABLE:
        # .env 파일이 있으면 로드
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
        
        # database/.env 파일도 확인
        db_env_file = os.path.join(os.path.dirname(__file__), 'database', '.env')
        if os.path.exists(db_env_file):
            load_dotenv(db_env_file)

def get_database_config() -> dict:
    """데이터베이스 설정 반환"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'calth_reader'),
        'username': os.getenv('DB_USER', 'calth_user'),
        'password': os.getenv('DB_PASSWORD', 'calth_pass123'),
    }

def get_app_config() -> dict:
    """애플리케이션 설정 반환"""
    return {
        'debug_mode': os.getenv('DEBUG_MODE', 'true').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'environment': os.getenv('ENVIRONMENT', 'development'),
    }

# 환경변수 자동 로딩
load_environment()
