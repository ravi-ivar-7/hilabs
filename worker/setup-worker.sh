#!/bin/bash

set -e

echo "Setting up Worker..."

# Check if we're in the worker directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the worker directory"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Checking spaCy model..."
if ! python3 -c "import spacy; spacy.load('en_core_web_sm')" > /dev/null 2>&1; then
    echo "Downloading spaCy English model..."
    python3 -m spacy download en_core_web_sm
else
    echo "spaCy English model already installed"
fi

echo "Testing task imports..."
if python3 -c "
import sys
sys.path.insert(0, '.')
from tasks.stage2_spacy_classification import classify_contract
from tasks.stage1_preprocessing import preprocess_contract
print('All task modules imported successfully')
" > /dev/null 2>&1; then
    echo "Task imports verified"
else
    echo "Warning: Some task imports failed - worker may have issues"
fi

echo "Worker environment setup complete!"

start_worker() {
    echo ""
    echo "Starting Celery worker for contract processing..."
    echo "Queues: contract_preprocessing, contract_classification"
    echo "Broker: redis://localhost:6379/0"
    echo ""
    
    celery -A worker worker \
        --loglevel=info \
        --concurrency=2 \
        --queues=contract_preprocessing,contract_classification \
        --hostname=worker@%h
}

stop_worker() {
    echo "Stopping Celery worker..."
    pkill -f "celery.*worker" || echo "No worker process found"
}

restart_worker() {
    echo "Restarting Celery worker..."
    pkill -f "celery.*worker" || echo "No existing worker to stop"
    sleep 2
    if check_redis; then
        start_worker
    fi
}

check_worker_status() {
    echo "🔍 Checking worker status..."
    
    if pgrep -f "celery.*worker" > /dev/null; then
        echo "Celery worker is running"
        echo "Process info:"
        pgrep -f "celery.*worker" | while read pid; do
            echo "   PID: $pid"
        done
    else
        echo "Celery worker is not running"
    fi
}

monitor_worker() {
    echo ""
    echo "Starting Celery monitoring..."
    echo "Flower will be available at: http://localhost:5555"
    echo ""
    celery -A worker flower --port=5555
}

stop_monitor() {
    echo "Stopping Flower monitoring..."
    pkill -f "celery.*flower" || echo "No Flower process found"
}

check_redis() {
    echo "Checking Redis connection..."
    
    if source venv/bin/activate && python3 -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" > /dev/null 2>&1; then
        echo "Redis is running"
        return 0
    else
        echo "Redis is not running!"
        echo "Start Redis with: sudo systemctl start redis-server"
        echo "Or with Docker: docker run -d -p 6379:6379 redis:alpine"
        return 1
    fi
}

case "${1:-start}" in
    "start")
        if check_redis; then
            start_worker
        fi
        ;;
    "stop")
        stop_worker
        ;;
    "restart")
        restart_worker
        ;;
    "status")
        check_worker_status
        ;;
    "monitor")
        if check_redis; then
            monitor_worker
        fi
        ;;
    "stop-monitor")
        stop_monitor
        ;;
    "setup")
        echo "✅ Setup already completed during script execution"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|monitor|stop-monitor|setup}"
        echo ""
        echo "Commands:"
        echo "  start        - Setup environment and start worker (default)"
        echo "  stop         - Stop the Celery worker"
        echo "  restart      - Restart the Celery worker"
        echo "  status       - Check if worker is running"
        echo "  monitor      - Start Flower monitoring interface"
        echo "  stop-monitor - Stop Flower monitoring"
        echo "  setup        - Setup is done automatically"
        echo ""
        echo "Prerequisites:"
        echo "  - Redis server running on localhost:6379"
        echo "  - Backend database migrated and running"
        exit 1
        ;;
esac
