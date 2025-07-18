# Calth Reader Database

PostgreSQL 기반의 Calth Reader 애플리케이션 데이터베이스 환경입니다.

## 🚀 빠른 시작

### 1. 데이터베이스 시작
```bash
./scripts/start-db.sh
```

### 2. 데이터베이스 중지
```bash
./scripts/stop-db.sh
```

### 3. 데이터베이스 초기화 (모든 데이터 삭제)
```bash
./scripts/reset-db.sh
```

## 📋 접속 정보

데이터베이스가 시작되면 다음 정보로 접속할 수 있습니다:

- **Host**: localhost
- **Port**: 5433
- **Database**: calth_reader
- **Username**: admin
- **Password**: CalthReader2024!

### psql 접속
```bash
psql -h localhost -p 5433 -U admin -d calth_reader
```

### Adminer (웹 UI) 접속
- URL: http://localhost:8080
- System: PostgreSQL
- Server: postgres
- Username: admin
- Password: CalthReader2024!
- Database: calth_reader

## 🏗️ 데이터베이스 구조

### 주요 테이블
- `users` - 사용자 관리
- `patients` - 환자 정보 (익명화)
- `test_types` - 테스트 유형 마스터
- `test_sessions` - 테스트 세션
- `measurement_results` - 측정 결과
- `system_logs` - 시스템 로그
- `device_status` - 하드웨어 상태
- `system_settings` - 시스템 설정
- `backup_history` - 백업 이력
- `audit_logs` - 감사 로그
- `notifications` - 시스템 알림

### 기본 사용자 계정
- **admin** / admin123! (관리자)
- **operator1** / admin123! (운영자)
- **viewer1** / admin123! (조회자)

⚠️ **보안 주의사항**: 운영 환경에서는 반드시 기본 비밀번호를 변경하세요!

## ⚙️ 설정

### 환경 변수 (.env)
```bash
POSTGRES_DB=calth_reader
POSTGRES_USER=admin
POSTGRES_PASSWORD=CalthReader2024!
DB_PORT=5433
ADMINER_PORT=8080
```

### 포트 변경
다른 서비스와 포트 충돌이 발생하는 경우 `.env` 파일에서 포트를 변경할 수 있습니다.

## 🔧 관리 작업

### 백업 생성
```bash
docker exec calth_reader_db pg_dump -U admin calth_reader > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 백업 복원
```bash
docker exec -i calth_reader_db psql -U admin calth_reader < backup_file.sql
```

### 로그 확인
```bash
docker logs calth_reader_db -f
```

### 컨테이너 상태 확인
```bash
docker ps --filter "name=calth_reader"
```

## 📊 성능 최적화

### 인덱스
모든 주요 쿼리에 대한 인덱스가 자동으로 생성됩니다:
- 기본 키 및 외래 키
- 자주 검색되는 컬럼
- JSONB 데이터용 GIN 인덱스
- 복합 인덱스

### 통계 정보
데이터베이스 초기화 시 통계 정보가 자동으로 업데이트됩니다.

## 🔒 보안

- 기본 비밀번호 변경 필수
- 네트워크 격리 (calth_network)
- 감사 로그 자동 기록
- 사용자 계정 잠금 기능
- 패스워드 복잡도 정책

## 🚨 문제 해결

### 컨테이너가 시작되지 않는 경우
1. Docker 데몬 실행 확인
2. 포트 충돌 확인 (5433, 8080)
3. 권한 문제 확인
4. 로그 확인: `docker logs calth_reader_db`

### 데이터베이스 연결 실패
1. 컨테이너 상태 확인
2. 헬스체크 상태 확인
3. 네트워크 설정 확인
4. 방화벽 설정 확인

### 성능 이슈
1. 통계 정보 업데이트: `ANALYZE;`
2. 인덱스 재구성: `REINDEX DATABASE calth_reader;`
3. 로그 파일 크기 확인
4. 디스크 공간 확인

## 📚 추가 정보

- PostgreSQL 15 공식 문서: https://www.postgresql.org/docs/15/
- Docker Compose 문서: https://docs.docker.com/compose/
- Adminer 사용법: https://www.adminer.org/
