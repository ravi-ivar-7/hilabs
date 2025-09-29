#!/bin/bash

set -e

echo "Setting up Backend Server..."

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the backend directory"
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

echo "Creating upload directories..."
mkdir -p ../upload/contracts-tn ../upload/contracts-wa

echo "Setting up database..."
mkdir -p app/data
chmod 755 app/data
export DATABASE_URL="sqlite:///./app/data/contracts.db"
python -c "from app.core.database import engine; from app.models.base import BaseModel; BaseModel.metadata.create_all(bind=engine); print('Database tables created')"

echo "Backend setup complete!"

start_server() {
    echo ""
    echo "🏃 Starting FastAPI backend server..."
    echo "Server will be available at: http://localhost:8000"
    echo "API docs available at: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
}

check_server() {
    echo "🔍 Checking backend server status..."
    
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "Backend server is running at http://localhost:8000"
        echo "API docs: http://localhost:8000/docs"
        return 0
    else
        echo "Backend server is not responding"
        echo "Try: curl http://localhost:8000/ to test basic connectivity"
        return 1
    fi
}

case "${1:-start}" in
    "start")
        if check_server; then
            echo "Server is already running"
            echo "Use 'stop' to stop it first, or access it at http://localhost:8000"
        else
            start_server
        fi
        ;;
    "stop")
        echo "Stopping backend server..."
        pkill -f "uvicorn app.main:app" || echo "No backend server process found"
        ;;
    "restart")
        echo "Restarting backend server..."
        pkill -f "uvicorn app.main:app" || echo "No existing server to stop"
        sleep 2
        start_server
        ;;
    "status")
        check_server
        ;;
    "setup")
        echo "Setup already completed during script execution"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|setup}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the FastAPI backend server"
        echo "  stop    - Stop the backend server"
        echo "  restart - Restart the backend server"
        echo "  status  - Check if server is running"
        echo "  setup   - Setup is done automatically"
        exit 1
        ;;
esac
