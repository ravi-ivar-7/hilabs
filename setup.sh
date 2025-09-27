#!/bin/bash

# HiLabs Healthcare Contract Classifier - Setup Script
# Automated initialization for the entire project

set -e

echo "🚀 HiLabs Healthcare Contract Classifier Setup"
echo "=============================================="

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p backend/app/data backend/app/models
mkdir -p upload/contracts-tn upload/contracts-wa
echo "✅ Directories created"

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Setup Complete!"
echo "==================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo ""
echo "📚 Next steps:"
echo "   - Upload test contracts via frontend"
echo "   - Files will be stored in ./upload/ directory"
echo "   - Check logs: docker-compose logs -f"
echo ""
