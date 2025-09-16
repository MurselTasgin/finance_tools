#!/bin/bash
# finance_tools/start_backend.sh

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Finance Tools Backend Startup Script"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean, -c    Clean virtual environment and reinstall dependencies"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Start backend with existing environment"
    echo "  $0 --clean      # Clean and recreate environment"
    exit 0
fi

if [ "$1" = "--clean" ] || [ "$1" = "-c" ]; then
    echo "Cleaning virtual environment and reinstalling dependencies..."
    rm -rf venv
    rm -f .last_install
    echo "Cleanup completed. Virtual environment will be recreated."
fi

echo "Starting Finance Tools Backend API..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Navigate to backend directory
cd backend

# Check if virtual environment exists, create only if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created successfully."
else
    echo "Using existing virtual environment..."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify virtual environment is working
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi
echo "Virtual environment activated: $VIRTUAL_ENV"

# Install dependencies only if requirements.txt is newer than last install
if [ ! -f ".last_install" ] || [ requirements.txt -nt .last_install ]; then
    echo "Installing/updating backend dependencies..."
    pip install -r requirements.txt
    touch .last_install
    echo "Dependencies installed successfully."
else
    echo "Dependencies are up to date, skipping installation."
fi

# Install the finance_tools package in development mode
cd ..
echo "Installing finance_tools package in development mode..."
pip install -e .

# Set environment variable for test database
export DATABASE_NAME="test_finance_tools.db"

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8070"
echo "Using database: test_finance_tools.db"
cd backend
uvicorn main:app --host 0.0.0.0 --port 8070 --reload
