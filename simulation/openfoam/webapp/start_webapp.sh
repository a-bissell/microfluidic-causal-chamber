#!/bin/bash
# Start the Microfluidic Simulation Web Application

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Microfluidic Simulation Web App    ${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Source OpenFOAM if available
if [ -f "/opt/openfoam11/etc/bashrc" ]; then
    echo -e "${GREEN}Sourcing OpenFOAM 11...${NC}"
    source /opt/openfoam11/etc/bashrc
elif [ -f "$HOME/OpenFOAM/OpenFOAM-11/etc/bashrc" ]; then
    echo -e "${GREEN}Sourcing OpenFOAM 11 from home...${NC}"
    source $HOME/OpenFOAM/OpenFOAM-11/etc/bashrc
else
    echo -e "${YELLOW}Warning: OpenFOAM not found. Simulations won't work.${NC}"
fi

# Check for required system packages
echo ""
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required${NC}"
    echo -e "Install with: ${YELLOW}sudo apt install python3 python3-pip python3-venv${NC}"
    exit 1
fi

# Check if python3-venv is available
if ! python3 -c "import venv" 2>/dev/null; then
    echo -e "${RED}Error: python3-venv is not installed${NC}"
    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
    echo -e "Install with: ${YELLOW}sudo apt install python3-venv${NC}"
    echo -e "   or: ${YELLOW}sudo apt install python${PYTHON_VERSION}-venv${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required${NC}"
    echo -e "Install with:"
    echo -e "  ${YELLOW}curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -${NC}"
    echo -e "  ${YELLOW}sudo apt install -y nodejs${NC}"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is required${NC}"
    echo -e "Install with: ${YELLOW}sudo apt install npm${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites found!${NC}"

# Install backend dependencies if needed
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo ""
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    python3 -m venv "$BACKEND_DIR/venv"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    source "$BACKEND_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$BACKEND_DIR/requirements.txt"
else
    source "$BACKEND_DIR/venv/bin/activate"
fi

# Install frontend dependencies if needed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo ""
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd "$FRONTEND_DIR"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install frontend dependencies${NC}"
        exit 1
    fi
    cd "$SCRIPT_DIR"
fi

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""

# Start backend in background
echo -e "${BLUE}Starting backend on port 8000...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend to start
sleep 2

# Start frontend
echo -e "${BLUE}Starting frontend on port 5173...${NC}"
cd "$FRONTEND_DIR"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for frontend to start
sleep 3

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Web Application Started!           ${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "Frontend: ${BLUE}http://localhost:5173${NC}"
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Done.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
