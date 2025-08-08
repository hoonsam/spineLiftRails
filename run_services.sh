#!/bin/bash
# Run all services for SpineLift

echo "Starting SpineLift services..."

# Start Python service in background
echo "Starting Python service..."
cd python_service
./run.sh &
PYTHON_PID=$!
cd ..

# Wait for Python service to start
echo "Waiting for Python service to start..."
sleep 5

# Check if Python service is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Python service is running"
else
    echo "❌ Python service failed to start"
    exit 1
fi

# Run Rails migrations
echo "Running Rails migrations..."
rails db:migrate

# Start Rails server
echo "Starting Rails server..."
rails server

# Cleanup on exit
trap "kill $PYTHON_PID" EXIT