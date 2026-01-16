-- ============================================================================
-- Calth Reader Database Schema
-- PostgreSQL 최적화 버전
-- 생성일: 2025-07-16
-- ============================================================================

-- 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 1. 환자 정보 테이블 (개인정보 보호 고려)
CREATE TABLE patients (
    id BIGSERIAL PRIMARY KEY,
    patient_code VARCHAR(50) UNIQUE NOT NULL, -- 익명화된 환자 코드
    birth_year INTEGER, -- 개인정보 보호를 위해 년도만 저장
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'U')), -- M/F/Unknown
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. 테스트 유형 마스터 테이블
CREATE TABLE test_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    measurement_time_seconds INTEGER DEFAULT 300, -- 예상 측정 시간
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. 사용자 관리 테이블 (개선된 버전)
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer', 'maintenance')),
    email VARCHAR(255) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. 테스트 세션 테이블 (개선된 버전)
CREATE TABLE test_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    test_type_id INTEGER NOT NULL REFERENCES test_types(id),
    operator_id BIGINT NOT NULL REFERENCES users(id),
    patient_id BIGINT REFERENCES patients(id),
    device_serial VARCHAR(100),
    cartridge_lot VARCHAR(50), -- 카트리지 로트 번호
    temperature DECIMAL(4,1), -- 측정 시 온도
    humidity DECIMAL(4,1), -- 측정 시 습도
    started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'in_progress' 
        CHECK (status IN ('in_progress', 'completed', 'failed', 'cancelled', 'error')),
    error_message TEXT,
    metadata JSONB, -- 추가 메타데이터
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. 측정 결과 테이블 (개선된 버전)
CREATE TABLE measurement_results (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    measurement_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL, -- JSON 형태로 저장
    select_menu VARCHAR(50) NOT NULL, --홈 선택 메뉴명
    image_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    quality_score DECIMAL(5,2) CHECK (quality_score >= 0 AND quality_score <= 100),
    is_valid BOOLEAN DEFAULT TRUE,
    validation_notes TEXT,
    measured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ,
    raw_data BYTEA, -- 원시 데이터 저장 (선택적)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. 시스템 로그 테이블 (개선된 버전)
CREATE TABLE system_logs (
    id BIGSERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL 
        CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module VARCHAR(100) NOT NULL,
    function_name VARCHAR(100),
    message TEXT NOT NULL,
    details JSONB, -- 구조화된 로그 데이터
    user_id BIGINT REFERENCES users(id),
    session_id BIGINT REFERENCES test_sessions(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. 기기 상태 테이블 (개선된 버전)
CREATE TABLE device_status (
    id BIGSERIAL PRIMARY KEY,
    component VARCHAR(50) NOT NULL, -- 'camera', 'uart', 'led', 'battery', 'temperature'
    status VARCHAR(20) NOT NULL,
    value DECIMAL(10,3), -- 수치값 (온도, 배터리 등)
    unit VARCHAR(10), -- 단위 (°C, %, V 등)
    details JSONB, -- JSON 형태로 상세 정보 저장
    threshold_min DECIMAL(10,3), -- 최소 임계값
    threshold_max DECIMAL(10,3), -- 최대 임계값
    is_critical BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 8. 설정 테이블 (개선된 버전)
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    data_type VARCHAR(20) DEFAULT 'string' 
        CHECK (data_type IN ('string', 'integer', 'decimal', 'boolean', 'json')),
    description TEXT,
    is_editable BOOLEAN DEFAULT TRUE,
    requires_restart BOOLEAN DEFAULT FALSE,
    updated_by BIGINT REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, key)
);

-- 9. 백업 이력 테이블
CREATE TABLE backup_history (
    id BIGSERIAL PRIMARY KEY,
    backup_type VARCHAR(20) NOT NULL CHECK (backup_type IN ('manual', 'automatic', 'scheduled')),
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    checksum VARCHAR(64), -- SHA-256 해시
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'in_progress' 
        CHECK (status IN ('in_progress', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

-- 10. 감사 로그 테이블 (의료기기 규정 준수)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL, -- 'CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT'
    table_name VARCHAR(50),
    record_id BIGINT,
    old_values JSONB,
    new_values JSONB,
    user_id BIGINT NOT NULL REFERENCES users(id),
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 11. 알림 테이블
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL 
        CHECK (type IN ('info', 'warning', 'error', 'maintenance', 'system')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    recipient_role VARCHAR(20), -- 특정 역할에게만 표시
    recipient_user_id BIGINT REFERENCES users(id), -- 특정 사용자에게만 표시
    is_read BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id)
);

-- 트리거 함수 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 트리거 적용
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 코멘트 추가
COMMENT ON TABLE patients IS '환자 정보 (개인정보 보호를 위해 최소한의 정보만 저장)';
COMMENT ON TABLE test_types IS '테스트 유형 마스터 테이블';
COMMENT ON TABLE users IS '시스템 사용자 관리';
COMMENT ON TABLE test_sessions IS '테스트 세션 정보';
COMMENT ON TABLE measurement_results IS '측정 결과 데이터';
COMMENT ON TABLE system_logs IS '시스템 로그';
COMMENT ON TABLE device_status IS '하드웨어 기기 상태';
COMMENT ON TABLE system_settings IS '시스템 설정';
COMMENT ON TABLE backup_history IS '백업 이력';
COMMENT ON TABLE audit_logs IS '감사 로그 (의료기기 규정 준수)';
COMMENT ON TABLE notifications IS '시스템 알림';
