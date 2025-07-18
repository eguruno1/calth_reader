-- ============================================================================
-- 인덱스 생성 스크립트
-- 성능 최적화를 위한 인덱스 설계
-- ============================================================================

-- 환자 테이블 인덱스
CREATE INDEX idx_patients_patient_code ON patients(patient_code);
CREATE INDEX idx_patients_created_at ON patients(created_at);

-- 사용자 테이블 인덱스
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_last_login ON users(last_login);

-- 테스트 세션 인덱스
CREATE INDEX idx_test_sessions_session_id ON test_sessions(session_id);
CREATE INDEX idx_test_sessions_operator_id ON test_sessions(operator_id);
CREATE INDEX idx_test_sessions_patient_id ON test_sessions(patient_id);
CREATE INDEX idx_test_sessions_test_type_id ON test_sessions(test_type_id);
CREATE INDEX idx_test_sessions_status ON test_sessions(status);
CREATE INDEX idx_test_sessions_started_at ON test_sessions(started_at);
CREATE INDEX idx_test_sessions_completed_at ON test_sessions(completed_at);

-- 복합 인덱스 - 자주 함께 조회되는 컬럼들
CREATE INDEX idx_test_sessions_status_started ON test_sessions(status, started_at);
CREATE INDEX idx_test_sessions_operator_status ON test_sessions(operator_id, status);

-- 측정 결과 인덱스
CREATE INDEX idx_measurement_results_session_id ON measurement_results(session_id);
CREATE INDEX idx_measurement_results_type ON measurement_results(measurement_type);
CREATE INDEX idx_measurement_results_measured_at ON measurement_results(measured_at);
CREATE INDEX idx_measurement_results_is_valid ON measurement_results(is_valid);

-- JSONB 인덱스 (특정 키에 대한 빠른 검색)
CREATE INDEX idx_measurement_results_data_gin ON measurement_results USING GIN (result_data);
CREATE INDEX idx_test_sessions_metadata_gin ON test_sessions USING GIN (metadata);

-- 시스템 로그 인덱스
CREATE INDEX idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_module ON system_logs(module);
CREATE INDEX idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX idx_system_logs_session_id ON system_logs(session_id);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);

-- 복합 인덱스 - 로그 분석용
CREATE INDEX idx_system_logs_level_module ON system_logs(log_level, module);
CREATE INDEX idx_system_logs_module_created ON system_logs(module, created_at);

-- 기기 상태 인덱스
CREATE INDEX idx_device_status_component ON device_status(component);
CREATE INDEX idx_device_status_recorded_at ON device_status(recorded_at);
CREATE INDEX idx_device_status_is_critical ON device_status(is_critical);

-- 복합 인덱스 - 최신 상태 조회용
CREATE INDEX idx_device_status_component_recorded ON device_status(component, recorded_at DESC);

-- 시스템 설정 인덱스
CREATE INDEX idx_system_settings_category ON system_settings(category);
CREATE INDEX idx_system_settings_key ON system_settings(key);

-- 백업 이력 인덱스
CREATE INDEX idx_backup_history_started_at ON backup_history(started_at);
CREATE INDEX idx_backup_history_status ON backup_history(status);
CREATE INDEX idx_backup_history_backup_type ON backup_history(backup_type);

-- 감사 로그 인덱스
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);

-- 복합 인덱스 - 감사 추적용
CREATE INDEX idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action);

-- 알림 인덱스
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_recipient_role ON notifications(recipient_role);
CREATE INDEX idx_notifications_recipient_user_id ON notifications(recipient_user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_expires_at ON notifications(expires_at);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- 부분 인덱스 (조건부 인덱스) - 저장 공간 효율성
CREATE INDEX idx_notifications_unread ON notifications(recipient_user_id, created_at) 
WHERE is_read = FALSE;

CREATE INDEX idx_active_users ON users(user_id, name) 
WHERE is_active = TRUE;

CREATE INDEX idx_failed_test_sessions ON test_sessions(started_at, operator_id) 
WHERE status IN ('failed', 'error');

-- 텍스트 검색 인덱스 (전문 검색)
CREATE INDEX idx_system_logs_message_text ON system_logs USING GIN (to_tsvector('english', message));
CREATE INDEX idx_notifications_message_text ON notifications USING GIN (to_tsvector('english', message));

-- 통계 정보 업데이트 (성능 최적화)
ANALYZE patients;
ANALYZE users;
ANALYZE test_types;
ANALYZE test_sessions;
ANALYZE measurement_results;
ANALYZE system_logs;
ANALYZE device_status;
ANALYZE system_settings;
ANALYZE backup_history;
ANALYZE audit_logs;
ANALYZE notifications;
