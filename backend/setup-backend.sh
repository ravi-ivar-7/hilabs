#!/bin/bash

echo "Setting up backend virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create upload directories
echo "Creating upload directories..."
mkdir -p ../upload/contracts-tn ../upload/contracts-wa

# Create database tables
echo "Setting up database..."
python -c "from app.core.database import engine; from app.models.base import BaseModel; BaseModel.metadata.create_all(bind=engine); print('Database tables created')"

echo "Backend setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To start the server, run: uvicorn app.main:app --reload --port 8000"
