#!/bin/bash

# ============================================
# Performa - Autonomous CyberSec AI Agent
# Start Script (Final Fix: Robust Detection)
# ============================================

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=5000
BACKEND_DIR="backend"

echo -e "${CYAN}"
cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   ██████╗ ███████╗██████╗ ███████╗ ██████╗ ██████╗ ███╗   ███╗ █████╗   ║
║   ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗████╗ ████║██╔══██╗  ║
║   ██████╔╝█████╗  ██████╔╝█████╗  ██║   ██║██████╔╝██╔████╔██║███████║  ║
║   ██╔═══╝ ██╔══╝  ██╔══██╗██╔══╝  ██║   ██║██╔══██╗██║╚██╔╝██║██╔══██║  ║
║   ██║     ███████╗██║  ██║██║     ╚██████╔╝██║  ██║██║ ╚═╝ ██║██║  ██║  ║
║   ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝  ║
║                                                                ║
║           Autonomous CyberSec AI Agent System                  ║
╚════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use (Updated: More Robust)
port_in_use() {
    local port=$1
    # Method 1: lsof
    if command_exists lsof; then
        if lsof -i :"$port" >/dev/null 2>&1; then return 0; fi
    fi
    # Method 2: ss (modern netstat replacement)
    if command_exists ss; then
        if ss -lnt | grep -q ":$port "; then return 0; fi
    fi
    # Method 3: netstat
    if command_exists netstat; then
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then return 0; fi
    fi
    # Method 4: curl (check if service responds)
    if command_exists curl; then
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then return 0; fi
    fi
    return 1
}

# Function to kill process on port
kill_port() {
    local port=$1
    if port_in_use "$port"; then
        echo -e "${YELLOW}[!] Port $port is in use. Attempting to free it...${NC}"
        if command_exists lsof; then
            lsof -ti :"$port" | xargs kill -9 2>/dev/null || true
        elif command_exists fuser; then
            fuser -k "$port/tcp" >/dev/null 2>&1 || true
        fi
        sleep 1
    fi
}

# Function to cleanup on exit
cleanup() {
    # Only cleanup if we are exiting with error or user interrupt
    # We want to keep processes running if successful
    echo -e "\n${YELLOW}[*] Shutting down services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then kill $BACKEND_PID 2>/dev/null || true; fi
    if [ ! -z "$FRONTEND_PID" ]; then kill $FRONTEND_PID 2>/dev/null || true; fi
    
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    echo -e "${GREEN}[✓] Services stopped successfully${NC}"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Check prerequisites
echo -e "${BLUE}[*] Checking prerequisites...${NC}"

if ! command_exists python3; then echo -e "${RED}[✗] Python 3 not found.${NC}"; exit 1; fi
if ! command_exists node; then echo -e "${RED}[✗] Node.js not found.${NC}"; exit 1; fi
if ! command_exists npm; then echo -e "${RED}[✗] npm not found.${NC}"; exit 1; fi

echo -e "${GREEN}  [✓] Prerequisites OK${NC}"

# Check for .env file
if [ ! -f ".env" ] && [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}[!] Creating default .env file...${NC}"
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

# Copy .env to backend (Filtered)
if [ -f ".env" ]; then
    grep -v "^NEXT_PUBLIC_" .env > "$BACKEND_DIR/.env"
    echo -e "${GREEN}[✓] Syncing .env to backend${NC}"
fi

# Kill existing ports
echo -e "\n${BLUE}[*] Freeing up ports...${NC}"
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT

# Backend Setup - Handle both venv and Replit's .pythonlibs
echo -e "\n${BLUE}[*] Activating Python environment...${NC}"
if [ -d "$BACKEND_DIR/venv" ]; then
    source $BACKEND_DIR/venv/bin/activate
    echo -e "${GREEN}[✓] Python venv activated${NC}"
elif [ -d ".pythonlibs/bin" ]; then
    # Replit's native python environment
    echo -e "${GREEN}[✓] Using Replit Python environment${NC}"
else
    echo -e "${RED}[✗] Python environment not found${NC}"
    exit 1
fi

# Node Setup
echo -e "\n${BLUE}[*] Setting up Node.js...${NC}"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}  [*] Installing dependencies...${NC}"
    npm install --silent
fi
echo -e "${GREEN}[✓] Node.js ready${NC}"

# Create directories with proper permissions
rm -rf logs findings 2>/dev/null
mkdir -p logs findings
chmod 777 logs findings

# --- START BACKEND ---
echo -e "\n${BLUE}[*] Starting Backend Server on port $BACKEND_PORT...${NC}"
cd $BACKEND_DIR
python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo -e "${YELLOW}  [*] Waiting for backend to initialize...${NC}"
for i in {1..20}; do
    if port_in_use $BACKEND_PORT; then break; fi
    sleep 1
done

if port_in_use $BACKEND_PORT; then
    echo -e "${GREEN}  [✓] Backend server started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}  [✗] Failed to start backend server${NC}"
    echo -e "${YELLOW}  [*] Check logs/backend.log for details${NC}"
    cleanup
    exit 1
fi

# --- START FRONTEND ---
echo -e "\n${BLUE}[*] Starting Frontend Server on port $FRONTEND_PORT...${NC}"
npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${YELLOW}  [*] Waiting for frontend to initialize...${NC}"
FRONTEND_READY=false
for i in {1..30}; do
    # Cek Port
    if port_in_use $FRONTEND_PORT; then 
        FRONTEND_READY=true
        break
    fi
    # Cek Log sebagai backup (jika deteksi port gagal)
    if grep -q "Ready in" logs/frontend.log 2>/dev/null; then
        FRONTEND_READY=true
        break
    fi
    sleep 1
done

if [ "$FRONTEND_READY" = true ]; then
    echo -e "${GREEN}  [✓] Frontend server started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}  [✗] Failed to start frontend server (Timeout)${NC}"
    echo -e "${YELLOW}  [*] Check logs/frontend.log - It might be running but slow.${NC}"
    # Kita tidak force cleanup disini agar user bisa cek
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                      SERVICES RUNNING                          ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  🌐 Frontend:   ${CYAN}http://localhost:$FRONTEND_PORT${GREEN}                       ║${NC}"
echo -e "${GREEN}║  🔧 Backend:    ${CYAN}http://localhost:$BACKEND_PORT${GREEN}                        ║${NC}"
echo -e "${GREEN}║  📝 Logs:       logs/backend.log | logs/frontend.log           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}[*] Tailing logs (Ctrl+C to stop)...${NC}"

# Tunggu prosesed
wait $BACKEND_PID $FRONTEND_PID