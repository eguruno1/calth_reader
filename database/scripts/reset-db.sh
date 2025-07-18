#!/bin/bash

# ============================================================================
# Calth Reader Database Reset Script
# PostgreSQL 도커 컨테이너 및 데이터 완전 초기화
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

echo -e "${RED}🔥 Resetting Calth Reader Database...${NC}"
echo "=============================================="
echo -e "${YELLOW}⚠️  WARNING: This will permanently delete all data!${NC}"
echo ""

# 확인 메시지
read -p "Are you sure you want to reset the database? (type 'yes' to confirm): " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo -e "${BLUE}❌ Reset cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}🔄 Starting reset process...${NC}"

# Docker Compose 실행 디렉토리로 이동
cd "$PROJECT_DIR"

# 1. 컨테이너 중지 및 제거
echo -e "${YELLOW}📋 Step 1: Stopping and removing containers...${NC}"
docker-compose down -v --remove-orphans || true

# 2. 컨테이너 강제 제거 (혹시 남아있는 경우)
echo -e "${YELLOW}📋 Step 2: Force removing containers...${NC}"
CONTAINERS=$(docker ps -a --format "{{.Names}}" | grep "calth_reader" || true)
if [ ! -z "$CONTAINERS" ]; then
    echo "$CONTAINERS" | xargs docker rm -f || true
    echo -e "${GREEN}✅ Containers removed${NC}"
else
    echo -e "${CYAN}ℹ️  No containers to remove${NC}"
fi

# 3. 볼륨 제거
echo -e "${YELLOW}📋 Step 3: Removing data volumes...${NC}"
VOLUMES=$(docker volume ls --format "{{.Name}}" | grep "calth_reader" || true)
if [ ! -z "$VOLUMES" ]; then
    echo "$VOLUMES" | xargs docker volume rm -f || true
    echo -e "${GREEN}✅ Volumes removed${NC}"
else
    echo -e "${CYAN}ℹ️  No volumes to remove${NC}"
fi

# 4. 네트워크 제거
echo -e "${YELLOW}📋 Step 4: Removing networks...${NC}"
NETWORKS=$(docker network ls --format "{{.Name}}" | grep "calth_reader" || true)
if [ ! -z "$NETWORKS" ]; then
    echo "$NETWORKS" | xargs docker network rm || true
    echo -e "${GREEN}✅ Networks removed${NC}"
else
    echo -e "${CYAN}ℹ️  No networks to remove${NC}"
fi

# 5. 로컬 데이터 디렉토리 정리
echo -e "${YELLOW}📋 Step 5: Cleaning local data directory...${NC}"
if [ -d "$PROJECT_DIR/data" ]; then
    rm -rf "$PROJECT_DIR/data"/*
    echo -e "${GREEN}✅ Local data directory cleaned${NC}"
else
    echo -e "${CYAN}ℹ️  No local data directory found${NC}"
fi

# 6. Docker 시스템 정리 (선택적)
echo -e "${YELLOW}📋 Step 6: Cleaning Docker system...${NC}"
docker system prune -f --volumes
echo -e "${GREEN}✅ Docker system cleaned${NC}"

echo ""
echo -e "${GREEN}🎉 Database reset completed successfully!${NC}"
echo "=============================================="
echo -e "${PURPLE}🛠️  Next Steps:${NC}"
echo -e "  ${CYAN}Start fresh database:${NC} $SCRIPT_DIR/start-db.sh"
echo ""
echo -e "${YELLOW}💡 Note: All previous data has been permanently deleted${NC}"
echo -e "${YELLOW}💡 A fresh database will be created when you start it again${NC}"
echo ""

# 최종 상태 확인
echo -e "${PURPLE}📋 Final Status:${NC}"
echo -e "  ${CYAN}Containers:${NC} $(docker ps -a --format "{{.Names}}" | grep "calth_reader" | wc -l)"
echo -e "  ${CYAN}Volumes:${NC}    $(docker volume ls --format "{{.Name}}" | grep "calth_reader" | wc -l)"
echo -e "  ${CYAN}Networks:${NC}   $(docker network ls --format "{{.Name}}" | grep "calth_reader" | wc -l)"

echo ""
echo -e "${GREEN}✨ Reset process completed!${NC}"
