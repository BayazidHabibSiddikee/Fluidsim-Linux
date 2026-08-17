#!/bin/bash
# FluidSim Linux - Run Script

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Error: python3 could not be found. Please install Python 3."
    exit 1
fi

# Install dependencies if needed (only if not already installed)
echo "Checking dependencies..."
python3 -c "import PySide6" 2>/dev/null || pip3 install -r requirements.txt --quiet

# Kill any existing instances
pkill -f "python3 launcher.py" 2>/dev/null || true
sleep 1

# Run the application
echo "Launching FluidSim Linux..."
python3 launcher.py
