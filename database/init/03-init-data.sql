-- ============================================================================
-- 기본 데이터 및 설정 스크립트
-- 시스템 초기 설정 및 마스터 데이터
-- ============================================================================

-- 테스트 유형 기본 데이터
INSERT INTO test_types (code, name, description, measurement_time_seconds) VALUES
('COVID19', 'COVID-19 Test', 'SARS-CoV-2 Antigen Test', 900),
('INFLUENZA', 'Influenza Test', 'Influenza A/B Antigen Test', 600),
('TROPONIN', 'Troponin Test', 'Cardiac Troponin I Test', 1200),
('STANDARD', 'Standard Test', 'General Purpose Test', 300),
('READONLY', 'Read Only Mode', 'Read-only diagnostic mode', 60),
('CALIBRATION', 'Calibration Test', 'System calibration test', 180);

-- 기본 관리자 계정 생성 (비밀번호: admin123! - 운영시 반드시 변경 필요)
INSERT INTO users (user_id, password_hash, name, role, email, is_active) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdMwehgMOLLqw6iCq', 'System Administrator', 'admin', 'admin@calth.local', TRUE),
('operator1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdMwehgMOLLqw6iCq', 'Default Operator', 'operator', 'operator@calth.local', TRUE),
('viewer1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdMwehgMOLLqw6iCq', 'Default Viewer', 'viewer', 'viewer@calth.local', TRUE);

-- 시스템 설정 기본값
INSERT INTO system_settings (category, key, value, data_type, description, is_editable, requires_restart) VALUES
-- 애플리케이션 설정
('application', 'debug_mode', 'true', 'boolean', 'Debug mode enable/disable', TRUE, TRUE),
('application', 'log_level', 'INFO', 'string', 'System log level', TRUE, TRUE),
('application', 'session_timeout', '3600', 'integer', 'Session timeout in seconds', TRUE, FALSE),
('application', 'auto_logout', 'true', 'boolean', 'Auto logout on inactivity', TRUE, FALSE),

-- 하드웨어 설정
('hardware', 'camera_enabled', 'true', 'boolean', 'Camera module enable/disable', TRUE, TRUE),
('hardware', 'uart_enabled', 'true', 'boolean', 'UART communication enable/disable', TRUE, TRUE),
('hardware', 'led_brightness', '80', 'integer', 'LED brightness percentage (0-100)', TRUE, FALSE),
('hardware', 'measurement_timeout', '1800', 'integer', 'Measurement timeout in seconds', TRUE, FALSE),

-- 데이터 관리 설정
('data', 'auto_backup', 'true', 'boolean', 'Automatic backup enable/disable', TRUE, FALSE),
('data', 'backup_retention_days', '90', 'integer', 'Backup retention period in days', TRUE, FALSE),
('data', 'result_retention_days', '365', 'integer', 'Measurement result retention in days', TRUE, FALSE),
('data', 'log_retention_days', '30', 'integer', 'System log retention in days', TRUE, FALSE),

-- 보안 설정
('security', 'password_min_length', '8', 'integer', 'Minimum password length', TRUE, FALSE),
('security', 'password_complexity', 'true', 'boolean', 'Require complex password', TRUE, FALSE),
('security', 'max_login_attempts', '5', 'integer', 'Maximum login attempts before lock', TRUE, FALSE),
('security', 'lockout_duration', '1800', 'integer', 'Account lockout duration in seconds', TRUE, FALSE),

-- 측정 설정
('measurement', 'auto_save_results', 'true', 'boolean', 'Automatically save measurement results', TRUE, FALSE),
('measurement', 'quality_threshold', '70.0', 'decimal', 'Minimum quality score threshold', TRUE, FALSE),
('measurement', 'auto_retry_on_failure', 'true', 'boolean', 'Automatically retry on measurement failure', TRUE, FALSE),
('measurement', 'max_retry_attempts', '3', 'integer', 'Maximum retry attempts', TRUE, FALSE),

-- UI 설정
('ui', 'language', 'ko', 'string', 'Default language (ko/en)', TRUE, FALSE),
('ui', 'theme', 'light', 'string', 'UI theme (light/dark)', TRUE, FALSE),
('ui', 'font_size', 'medium', 'string', 'Font size (small/medium/large)', TRUE, FALSE),
('ui', 'show_tooltips', 'true', 'boolean', 'Show UI tooltips', TRUE, FALSE),

-- 알림 설정
('notification', 'email_enabled', 'false', 'boolean', 'Email notification enable/disable', TRUE, FALSE),
('notification', 'sound_enabled', 'true', 'boolean', 'Sound notification enable/disable', TRUE, FALSE),
('notification', 'maintenance_alerts', 'true', 'boolean', 'Maintenance alert notifications', TRUE, FALSE),
('notification', 'error_alerts', 'true', 'boolean', 'Error alert notifications', TRUE, FALSE),

-- 시스템 정보 (읽기 전용)
('system', 'version', '2.0.0', 'string', 'Application version', FALSE, FALSE),
('system', 'build_date', '2025-07-16', 'string', 'Build date', FALSE, FALSE),
('system', 'database_version', '1.0.0', 'string', 'Database schema version', FALSE, FALSE),
('system', 'installation_date', CURRENT_TIMESTAMP::text, 'string', 'System installation date', FALSE, FALSE);

-- 기본 알림 메시지
INSERT INTO notifications (type, title, message, recipient_role, expires_at, created_by) VALUES
('info', 'Welcome to Calth Reader v2.0', 'System has been successfully initialized. Please review system settings and change default passwords.', 'admin', CURRENT_TIMESTAMP + INTERVAL '7 days', 1),
('warning', 'Default Passwords', 'Please change the default passwords for security purposes.', 'admin', CURRENT_TIMESTAMP + INTERVAL '7 days', 1),
('maintenance', 'Regular Maintenance', 'Please perform regular system maintenance as per the user manual.', 'admin', CURRENT_TIMESTAMP + INTERVAL '30 days', 1);

-- 기본 환자 데이터 (테스트용 - 실제 운영시 제거)
INSERT INTO patients (patient_code, birth_year, gender, notes) VALUES
('TEST001', 1990, 'M', 'Test patient for system validation'),
('TEST002', 1985, 'F', 'Test patient for system validation'),
('DEMO001', 1975, 'M', 'Demo patient for training purposes');

-- 초기 기기 상태 설정
INSERT INTO device_status (component, status, value, unit, details, threshold_min, threshold_max) VALUES
('camera', 'ready', NULL, NULL, '{"resolution": "640x480", "fps": 30}', NULL, NULL),
('uart', 'ready', NULL, NULL, '{"port": "/dev/ttyUSB0", "baudrate": 115200}', NULL, NULL),
('led', 'ready', 80, '%', '{"brightness": 80, "color": "white"}', 0, 100),
('battery', 'unknown', NULL, '%', '{}', 20, 100),
('temperature', 'normal', 23.5, '°C', '{}', 18, 35),
('humidity', 'normal', 45.0, '%', '{}', 30, 70);

-- 시스템 로그 (초기화 완료 로그)
INSERT INTO system_logs (log_level, module, function_name, message, details) VALUES
('INFO', 'database', 'init_schema', 'Database schema initialized successfully', '{"version": "1.0.0", "tables_created": 11}'),
('INFO', 'database', 'init_data', 'Initial data loaded successfully', '{"test_types": 6, "users": 3, "settings": 25}');

-- 감사 로그 (초기 설정)
INSERT INTO audit_logs (action, table_name, user_id, new_values, session_id) VALUES
('CREATE', 'database', 1, '{"action": "schema_initialization", "version": "1.0.0"}', uuid_generate_v4());

-- 시퀀스 및 기본값 설정
SELECT setval('users_id_seq', 1000, false); -- 사용자 ID를 1000부터 시작
SELECT setval('patients_id_seq', 10000, false); -- 환자 ID를 10000부터 시작
SELECT setval('test_sessions_id_seq', 100000, false); -- 세션 ID를 100000부터 시작

-- 뷰 생성 (자주 사용되는 조인 쿼리 최적화)
CREATE VIEW v_active_sessions AS
SELECT 
    ts.id,
    ts.session_id,
    tt.name as test_type_name,
    u.name as operator_name,
    p.patient_code,
    ts.started_at,
    ts.status,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ts.started_at))::integer as duration_seconds
FROM test_sessions ts
JOIN test_types tt ON ts.test_type_id = tt.id
JOIN users u ON ts.operator_id = u.id
LEFT JOIN patients p ON ts.patient_id = p.id
WHERE ts.status IN ('in_progress', 'failed', 'error');

CREATE VIEW v_recent_results AS
SELECT 
    mr.id,
    ts.session_id,
    tt.name as test_type_name,
    u.name as operator_name,
    mr.measurement_type,
    mr.quality_score,
    mr.is_valid,
    mr.measured_at
FROM measurement_results mr
JOIN test_sessions ts ON mr.session_id = ts.id
JOIN test_types tt ON ts.test_type_id = tt.id
JOIN users u ON ts.operator_id = u.id
WHERE mr.measured_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY mr.measured_at DESC;

CREATE VIEW v_system_status AS
SELECT 
    component,
    status,
    value,
    unit,
    details,
    recorded_at,
    CASE 
        WHEN threshold_min IS NOT NULL AND value < threshold_min THEN 'below_threshold'
        WHEN threshold_max IS NOT NULL AND value > threshold_max THEN 'above_threshold'
        ELSE 'normal'
    END as threshold_status
FROM device_status ds1
WHERE recorded_at = (
    SELECT MAX(recorded_at) 
    FROM device_status ds2 
    WHERE ds2.component = ds1.component
);

-- 권한 설정 (필요시)
-- GRANT USAGE ON SCHEMA public TO calth_reader_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO calth_reader_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO calth_reader_app;

-- 초기화 완료 로그
INSERT INTO system_logs (log_level, module, message) 
VALUES ('INFO', 'database', 'Database initialization completed successfully');
