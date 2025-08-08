#!/bin/bash
# Run script for SpineLift Python service

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./setup.sh
fi

# Activate virtual environment and run service
source venv/bin/activate
echo "Starting SpineLift Python service..."
python main.py