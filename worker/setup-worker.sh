#!/bin/bash

# HiLabs Worker Setup Script
# Creates virtual environment and starts the preprocessing worker

set -e

echo "🚀 Setting up HiLabs Preprocessing Worker..."

# Check if we're in the worker directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the worker directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Worker environment setup complete!"

# Function to start worker
start_worker() {
    echo ""
    echo "🏃 Starting Celery worker for contract preprocessing..."
    echo "📍 Queue: contract_preprocessing"
    echo "🔗 Broker: redis://localhost:6379/0"
    echo ""
    
    # Start the worker with proper configuration
    celery -A tasks.contract_preprocessing worker \
        --loglevel=info \
        --concurrency=2 \
        --queues=contract_preprocessing \
        --hostname=worker@%h
}

# Function to monitor worker
monitor_worker() {
    echo ""
    echo "📊 Starting Celery monitoring..."
    celery -A tasks.contract_preprocessing flower --port=5555
}

# Check if Redis is running
check_redis() {
    echo "🔍 Checking Redis connection..."
    
    # Use Python with redis module to check connection (more reliable)
    if source venv/bin/activate && python3 -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" > /dev/null 2>&1; then
        echo "✅ Redis is running"
        return 0
    else
        echo "❌ Redis is not running!"
        echo "💡 Start Redis with: sudo systemctl start redis-server"
        echo "   Or with Docker: docker run -d -p 6379:6379 redis:alpine"
        return 1
    fi
}

# Main execution
case "${1:-start}" in
    "start")
        if check_redis; then
            start_worker
        fi
        ;;
    "monitor")
        if check_redis; then
            monitor_worker
        fi
        ;;
    "setup-only")
        echo "🎉 Setup complete! Use './setup-worker.sh start' to run the worker"
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start       Setup environment and start worker (default)"
        echo "  monitor     Start Flower monitoring interface"
        echo "  setup-only  Only setup environment, don't start worker"
        echo "  help        Show this help message"
        echo ""
        echo "Prerequisites:"
        echo "  - Redis server running on localhost:6379"
        echo "  - Backend database migrated and running"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
