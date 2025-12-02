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

# Copy .env to backend (filtered)
if [ -f ".env" ]; then
    grep -v "^NEXT_PUBLIC_" .env > backend/.env
fi

# Create directories
mkdir -p logs findings
chmod 777 logs findings

# Start backend in background
echo "Starting backend server on port 8000..."
cd backend && python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 3

# Start frontend (foreground - this is what Replit monitors)
echo "Starting frontend server on port 5000..."
cd /home/runner/workspace
npm run dev
