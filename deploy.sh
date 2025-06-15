#!/bin/bash
# HFT-PacketFilter Production Deployment Script

set -e

echo "🚀 Deploying HFT-PacketFilter to Production"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t hft-packetfilter:latest .

# Run tests before deployment
echo "🧪 Running pre-deployment tests..."
python extended_performance_test.py

# Deploy with Docker Compose
echo "🚀 Starting production deployment..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🏥 Performing health check..."
curl -f http://localhost:8080/health || echo "❌ Health check failed"

echo "✅ Deployment completed!"
echo "📊 Monitor at: http://localhost:3000"
echo "📈 Metrics at: http://localhost:9091"