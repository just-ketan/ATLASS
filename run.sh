#!/bin/bash
# ATLASS Local Launcher
# Runs the FastAPI backend locally

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting ATLASS Backend...${NC}"

export PYTHONPATH=$(pwd)

# Use virtual environment python if it exists
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python"
fi

$PYTHON_CMD -m uvicorn atlasse.platform.api:app --host 0.0.0.0 --port 8000 --reload
