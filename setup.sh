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
mkdir -p infra/minio/data infra/minio/config
mkdir -p backend/app/data backend/app/models
echo "✅ Directories created"

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up --build -d

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
sleep 15

# Initialize MinIO buckets
echo "🪣 Initializing MinIO buckets..."
docker exec -it hilabs-minio /usr/local/bin/init-buckets.sh

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Setup Complete!"
echo "==================="
echo "🌐 Frontend: http://localhost:3000"
echo "📦 MinIO API: http://localhost:9000"
echo "🖥️  MinIO Console: http://localhost:9001"
echo "🔐 MinIO Credentials: hilabs / hilabsminio"
echo ""
echo "📚 Next steps:"
echo "   - Access MinIO console to verify buckets"
echo "   - Upload test contracts via frontend"
echo "   - Check logs: docker-compose logs -f"
echo ""
