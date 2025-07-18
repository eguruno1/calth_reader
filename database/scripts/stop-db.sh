#!/bin/bash

# ============================================================================
# Calth Reader Database Stop Script
# PostgreSQL 도커 컨테이너 중지
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

echo -e "${BLUE}🛑 Stopping Calth Reader Database...${NC}"
echo "=============================================="

# Docker Compose 실행 디렉토리로 이동
cd "$PROJECT_DIR"

# 컨테이너 상태 확인
CONTAINER_NAME="calth_reader_db"
if docker ps --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo -e "${YELLOW}📋 Container is currently running${NC}"
    
    # Docker Compose로 서비스 중지
    echo -e "${CYAN}🔄 Stopping containers...${NC}"
    docker-compose down
    
    echo -e "${GREEN}✅ Database stopped successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Container is not running${NC}"
fi

# 컨테이너 상태 확인
echo ""
echo -e "${PURPLE}📋 Final Container Status:${NC}"
if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "calth_reader"; then
    docker ps -a --format "table {{.Names}}\t{{.Status}}" --filter "name=calth_reader"
else
    echo -e "${CYAN}No Calth Reader containers found${NC}"
fi

echo ""
echo -e "${PURPLE}🛠️  Available Commands:${NC}"
echo -e "  ${CYAN}Start database:${NC}  $SCRIPT_DIR/start-db.sh"
echo -e "  ${CYAN}Reset database:${NC} $SCRIPT_DIR/reset-db.sh"
echo ""
echo -e "${GREEN}✨ Database shutdown completed!${NC}"
