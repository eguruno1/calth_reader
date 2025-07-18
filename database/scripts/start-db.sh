#!/bin/bash

# ============================================================================
# Calth Reader Database Start Script
# PostgreSQL 도커 컨테이너 시작 및 접속 정보 출력
# ============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"

# .env 파일 로드
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found. Using default values.${NC}"
fi

# 기본값 설정
DB_PORT=${DB_PORT:-5433}
ADMINER_PORT=${ADMINER_PORT:-8080}
POSTGRES_DB=${POSTGRES_DB:-calth_reader}
POSTGRES_USER=${POSTGRES_USER:-admin}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-CalthReader2024!}

echo -e "${BLUE}🚀 Starting Calth Reader Database...${NC}"
echo "=============================================="

# Docker 및 Docker Compose 확인
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed or not in PATH${NC}"
    exit 1
fi

# Docker daemon 실행 확인
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    exit 1
fi

# 기존 컨테이너 상태 확인
CONTAINER_NAME="calth_reader_db"
if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "$CONTAINER_NAME"; then
    CONTAINER_STATUS=$(docker ps -a --format "{{.Status}}" --filter "name=$CONTAINER_NAME")
    echo -e "${YELLOW}📋 Existing container found: $CONTAINER_STATUS${NC}"
    
    if docker ps --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
        echo -e "${GREEN}✅ Container is already running${NC}"
    else
        echo -e "${YELLOW}🔄 Starting existing container...${NC}"
        docker start "$CONTAINER_NAME" || {
            echo -e "${RED}❌ Failed to start existing container${NC}"
            exit 1
        }
    fi
else
    echo -e "${CYAN}🆕 Creating new container...${NC}"
fi

# Docker Compose로 서비스 시작
cd "$PROJECT_DIR"
echo -e "${CYAN}📁 Working directory: $PROJECT_DIR${NC}"

# 컨테이너 시작
docker-compose up -d

# 컨테이너가 준비될 때까지 대기
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
sleep 5

# 헬스체크 대기 (최대 60초)
TIMEOUT=60
COUNTER=0

while [ $COUNTER -lt $TIMEOUT ]; do
    if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" &> /dev/null; then
        echo -e "${GREEN}✅ Database is ready!${NC}"
        break
    fi
    
    echo -ne "${YELLOW}⏳ Waiting... ($((COUNTER + 1))/$TIMEOUT)\r${NC}"
    sleep 1
    ((COUNTER++))
done

if [ $COUNTER -eq $TIMEOUT ]; then
    echo -e "${RED}❌ Database failed to start within $TIMEOUT seconds${NC}"
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker logs "$CONTAINER_NAME" --tail 20
    exit 1
fi

# 접속 정보 출력
echo ""
echo -e "${GREEN}🎉 Database is now running!${NC}"
echo "=============================================="
echo -e "${PURPLE}📊 Connection Information:${NC}"
echo -e "  ${CYAN}Host:${NC}       localhost"
echo -e "  ${CYAN}Port:${NC}       $DB_PORT"
echo -e "  ${CYAN}Database:${NC}   $POSTGRES_DB"
echo -e "  ${CYAN}Username:${NC}   $POSTGRES_USER"
echo -e "  ${CYAN}Password:${NC}   $POSTGRES_PASSWORD"
echo ""
echo -e "${PURPLE}🌐 Database URL:${NC}"
echo -e "  postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:$DB_PORT/$POSTGRES_DB"
echo ""
echo -e "${PURPLE}🔧 Adminer (Web UI):${NC}"
echo -e "  ${CYAN}URL:${NC}        http://localhost:$ADMINER_PORT"
echo -e "  ${CYAN}System:${NC}     PostgreSQL"
echo -e "  ${CYAN}Server:${NC}     postgres"
echo -e "  ${CYAN}Username:${NC}   $POSTGRES_USER"
echo -e "  ${CYAN}Password:${NC}   $POSTGRES_PASSWORD"
echo -e "  ${CYAN}Database:${NC}   $POSTGRES_DB"
echo ""
echo -e "${PURPLE}🛠️  Quick Commands:${NC}"
echo -e "  ${CYAN}psql connect:${NC}   psql -h localhost -p $DB_PORT -U $POSTGRES_USER -d $POSTGRES_DB"
echo -e "  ${CYAN}Stop database:${NC}  $SCRIPT_DIR/stop-db.sh"
echo -e "  ${CYAN}Reset database:${NC} $SCRIPT_DIR/reset-db.sh"
echo -e "  ${CYAN}View logs:${NC}      docker logs $CONTAINER_NAME -f"
echo ""
echo -e "${YELLOW}💡 Note: Use PGPASSWORD=$POSTGRES_PASSWORD to avoid password prompt${NC}"
echo "=============================================="

# 컨테이너 상태 확인
echo -e "${PURPLE}📋 Container Status:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=calth_reader"

# 디스크 사용량 확인
echo ""
echo -e "${PURPLE}💾 Storage Usage:${NC}"
docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}"

echo ""
echo -e "${GREEN}✨ Database startup completed successfully!${NC}"
