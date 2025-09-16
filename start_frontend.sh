#!/bin/bash
# finance_tools/start_frontend.sh

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Finance Tools Frontend Startup Script"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean, -c    Clean node_modules and reinstall dependencies"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Start frontend with existing dependencies"
    echo "  $0 --clean      # Clean and reinstall dependencies"
    exit 0
fi

if [ "$1" = "--clean" ] || [ "$1" = "-c" ]; then
    echo "Cleaning frontend dependencies..."
    rm -rf node_modules package-lock.json
    echo "Cleanup completed. Dependencies will be reinstalled."
fi

echo "Starting Finance Tools Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install npm and try again."
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies if node_modules doesn't exist or package.json is newer
if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
    echo "Installing frontend dependencies..."
    # Try normal install first, fallback to legacy peer deps if needed
    if ! npm install; then
        echo "Retrying with legacy peer deps to resolve conflicts..."
        npm install --legacy-peer-deps
    fi
    echo "Dependencies installed successfully."
else
    echo "Dependencies are up to date, skipping installation."
fi

# Start the development server
echo "Starting React development server on http://localhost:3000"
npm start
