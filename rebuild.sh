#!/bin/bash
# Rebuild and restart the binance-stream application

echo "Stopping existing Python processes..."
pkill -f "python3 /opt/projects/binance-stream/main.py" || true

echo "Stopping Docker containers..."
docker compose down || true

echo "Building new Docker image..."
docker compose build

echo "Starting Docker containers..."
docker compose up -d

echo "Showing Docker logs..."
docker compose logs -f
