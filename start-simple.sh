#!/bin/bash

# Simple start script for Replit
set -e

# Ensure we're in the workspace directory
cd /home/runner/workspace

echo "Starting Performa - Autonomous CyberSec AI Agent System..."

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    cat > .env << 'ENVFILE'
OPENROUTER_API_KEY=your_key
LOG_DIR=./logs
FINDINGS_DIR=./findings
HOST=0.0.0.0
PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
ENVFILE
fi

# Create directories
mkdir -p logs findings
chmod 777 logs findings

# Build Go backend if binary doesn't exist or source is newer
echo "Checking Go backend..."
if [ ! -f "backend-go/performa-backend" ] || [ "backend-go/main.go" -nt "backend-go/performa-backend" ]; then
    echo "Building Go backend..."
    cd backend-go && go build -o performa-backend . && cd ..
fi

# Start Go backend in background
echo "Starting Go backend server on port 8000..."
cd backend-go && ./performa-backend > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 2

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Backend failed to start. Check logs/backend.log"
    cat logs/backend.log
    exit 1
fi

echo "Backend started successfully (PID: $BACKEND_PID)"

# Start frontend (foreground - this is what Replit monitors)
echo "Starting frontend server on port 5000..."
cd /home/runner/workspace
npm run dev
