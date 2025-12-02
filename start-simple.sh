#!/bin/bash

set -e

cd /home/runner/workspace

echo "Starting Performa - Autonomous CyberSec AI Agent System..."
echo "=============================================="

if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    cat > .env << 'ENVFILE'
OPENROUTER_API_KEY=your_key
LOG_DIR=./logs
FINDINGS_DIR=./findings
HOST=0.0.0.0
PORT=8000
BRAIN_PORT=8001
BRAIN_SERVICE_URL=http://localhost:8001
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
ENVFILE
fi

mkdir -p logs findings agent-brain/knowledge

echo "Starting Python Agent Brain (Intelligence Service) on port 8001..."
cd /home/runner/workspace/agent-brain
python main.py > ../logs/brain.log 2>&1 &
BRAIN_PID=$!
cd /home/runner/workspace

sleep 3

if ! kill -0 $BRAIN_PID 2>/dev/null; then
    echo "Warning: Agent Brain service may have failed to start. Check logs/brain.log"
    echo "Continuing without brain service..."
else
    echo "Agent Brain started successfully (PID: $BRAIN_PID)"
fi

echo "Checking Go backend..."
if [ ! -f "backend-go/performa-backend" ] || [ "backend-go/main.go" -nt "backend-go/performa-backend" ]; then
    echo "Building Go backend..."
    cd backend-go && go build -o performa-backend . && cd ..
fi

echo "Starting Go backend server on port 8000..."
cd backend-go && ./performa-backend > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

sleep 2

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Backend failed to start. Check logs/backend.log"
    cat logs/backend.log
    exit 1
fi

echo "Backend started successfully (PID: $BACKEND_PID)"

echo "Starting frontend server on port 5000..."
cd /home/runner/workspace
npm run dev
