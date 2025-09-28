o  #!/bin/bash

# HiLabs Services Startup Script
# Starts Redis, Backend API, and Worker services

set -e

echo "🚀 Starting HiLabs Healthcare Contract Classification Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name is not running on port $port${NC}"
        return 1
    fi
}

# Function to start Redis
start_redis() {
    echo -e "${BLUE}🔧 Starting Redis server...${NC}"
    
    if check_service "Redis" "6379"; then
        echo -e "${YELLOW}Redis already running${NC}"
    else
        # Try to start Redis with systemctl first
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl start redis-server || {
                echo -e "${YELLOW}Systemctl failed, trying Docker...${NC}"
                docker run -d --name hilabs-redis -p 6379:6379 redis:alpine
            }
        else
            # Fallback to Docker
            docker run -d --name hilabs-redis -p 6379:6379 redis:alpine
        fi
        
        # Wait for Redis to start
        sleep 2
        if check_service "Redis" "6379"; then
            echo -e "${GREEN}✅ Redis started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start Redis${NC}"
            exit 1
        fi
    fi
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}🔧 Starting Backend API server...${NC}"
    
    if check_service "Backend API" "8000"; then
        echo -e "${YELLOW}Backend already running${NC}"
    else
        cd backend
        
        # Activate virtual environment and start
        if [ -d "venv" ]; then
            source venv/bin/activate
            echo -e "${GREEN}📦 Backend venv activated${NC}"
        else
            echo -e "${RED}❌ Backend venv not found. Run setup.sh first${NC}"
            exit 1
        fi
        
        # Run database migrations
        echo -e "${BLUE}🗄️  Running database migrations...${NC}"
        alembic upgrade head
        
        # Start FastAPI server in background
        echo -e "${BLUE}🚀 Starting FastAPI server...${NC}"
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
        BACKEND_PID=$!
        
        # Wait for backend to start
        sleep 3
        if check_service "Backend API" "8000"; then
            echo -e "${GREEN}✅ Backend API started successfully (PID: $BACKEND_PID)${NC}"
        else
            echo -e "${RED}❌ Failed to start Backend API${NC}"
            exit 1
        fi
        
        cd ..
    fi
}

# Function to start worker
start_worker() {
    echo -e "${BLUE}🔧 Starting Preprocessing Worker...${NC}"
    
    cd worker
    
    # Setup and start worker
    echo -e "${BLUE}📦 Setting up worker environment...${NC}"
    ./setup-worker.sh setup-only
    
    # Start worker in background
    echo -e "${BLUE}🏃 Starting Celery worker...${NC}"
    source venv/bin/activate
    celery -A tasks.contract_preprocessing worker \
        --loglevel=info \
        --concurrency=2 \
        --queues=contract_preprocessing \
        --hostname=worker@%h &
    WORKER_PID=$!
    
    echo -e "${GREEN}✅ Preprocessing Worker started (PID: $WORKER_PID)${NC}"
    
    cd ..
}

# Function to show status
show_status() {
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo "===================="
    check_service "Redis" "6379" || true
    check_service "Backend API" "8000" || true
    echo ""
    echo -e "${BLUE}🔗 Service URLs:${NC}"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/api/v1/health"
    echo ""
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    # Kill background processes
    pkill -f "uvicorn app.main:app" || true
    pkill -f "celery.*worker" || true
    
    # Stop Redis if running in Docker
    docker stop hilabs-redis 2>/dev/null || true
    docker rm hilabs-redis 2>/dev/null || true
    
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Main execution
case "${1:-start}" in
    "start")
        start_redis
        start_backend
        start_worker
        show_status
        echo ""
        echo -e "${GREEN}🎉 All services started successfully!${NC}"
        echo -e "${YELLOW}💡 Upload a contract PDF to test preprocessing${NC}"
        echo -e "${YELLOW}📝 Use 'Ctrl+C' to stop or run './start-services.sh stop'${NC}"
        
        # Keep script running
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
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start    Start all services (Redis, Backend, Worker)"
        echo "  stop     Stop all services"
        echo "  status   Show service status"
        echo "  redis    Start only Redis"
        echo "  backend  Start only Backend API"
        echo "  worker   Start only Worker"
        echo "  help     Show this help message"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
