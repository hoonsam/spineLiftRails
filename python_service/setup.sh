#!/bin/bash
# Setup script for SpineLift Python service

echo "Setting up Python virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To run the service:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Or use the run script:"
echo "  ./run.sh"