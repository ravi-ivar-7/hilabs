#!/bin/bash

set -e

echo "Starting services..."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_service() {
    local service_name=$1
    local port=$2
    
    if nc -z localhost $port >/dev/null 2>&1; then
        echo -e "${GREEN} $service_name running on port $port${NC}"
        return 0
    else
        echo -e "${RED} $service_name not running on port $port${NC}"
        return 1
    fi
}

check_redis() {
    if docker ps --filter "name=hilabs-redis" --filter "status=running" | grep -q hilabs-redis; then
        echo -e "${GREEN} Redis running${NC}"
        return 0
    else
        echo -e "${RED} Redis not running${NC}"
        return 1
    fi
}

start_redis() {
    echo -e "${BLUE}Starting Redis...${NC}"
    
    if check_redis; then
        echo -e "${YELLOW}Redis already running${NC}"
    else
        docker-compose up -d redis
        sleep 3
        if check_redis; then
            echo -e "${GREEN} Redis started${NC}"
        else
            echo -e "${RED} Failed to start Redis${NC}"
            exit 1
        fi
    fi
}

start_backend() {
    echo -e "${BLUE}Starting Backend...${NC}"
    
    if check_service "Backend" "8000"; then
        echo -e "${YELLOW}Backend already running${NC}"
    else
        cd backend
        ./setup-backend.sh start &
        cd ..
        sleep 5
        if check_service "Backend" "8000"; then
            echo -e "${GREEN} Backend started${NC}"
        else
            echo -e "${YELLOW} Backend starting (may take a moment)${NC}"
        fi
    fi
}

start_worker() {
    echo -e "${BLUE}Starting Worker...${NC}"
    
    cd worker
    ./setup-worker.sh start &
    cd ..
    
    echo -e "${GREEN} Worker started${NC}"
}

start_frontend() {
    echo -e "${BLUE}Starting Frontend...${NC}"
    
    if check_service "Frontend" "3000"; then
        echo -e "${YELLOW}Frontend already running${NC}"
    else
        cd frontend
        echo -e "${BLUE}Installing frontend dependencies...${NC}"
        npm install
        echo -e "${BLUE}Starting development server...${NC}"
        npm run dev &
        cd ..
        sleep 5
        if check_service "Frontend" "3000"; then
            echo -e "${GREEN} Frontend started${NC}"
        else
            echo -e "${YELLOW} Frontend may still be starting${NC}"
        fi
    fi
}

show_status() {
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    echo "=============="
    check_redis || true
    check_service "Backend" "8000" || true
    check_service "Frontend" "3000" || true
    echo ""
    echo -e "${BLUE}URLs:${NC}"
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:3000"
    echo ""
}

stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    
    cd backend && ./setup-backend.sh stop && cd .. || true
    cd worker && ./setup-worker.sh stop && cd .. || true
    pkill -f "npm run dev" || true
    docker-compose down redis 2>/dev/null || true
    
    echo -e "${GREEN} Services stopped${NC}"
}

case "${1:-start}" in
    "start")
        start_redis
        start_backend
        start_worker
        start_frontend
        show_status
        echo ""
        echo -e "${GREEN}All services started${NC}"
        wait
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "redis")
        start_redis
        ;;
    "backend")
        start_backend
        ;;
    "worker")
        start_worker
        ;;
    "frontend")
        start_frontend
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     Start all services"
        echo "  stop      Stop all services"
        echo "  status    Show service status"
        echo "  redis     Start only Redis"
        echo "  backend   Start only Backend"
        echo "  worker    Start only Worker"
        echo "  frontend  Start only Frontend"
        echo "  help      Show this help"
        ;;
    *)
        echo -e "${RED} Unknown command: $1${NC}"
        echo "Use '$0 help' for usage"
        exit 1
        ;;
esac
