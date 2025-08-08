#!/bin/bash
# Start Redis using Docker if available, otherwise provide instructions

if command -v docker &> /dev/null; then
  echo "Starting Redis with Docker..."
  docker run -d --name spinelift-redis -p 6379:6379 redis:7-alpine
else
  echo "Docker not available. Please install Redis:"
  echo ""
  echo "Option 1: Install Redis locally"
  echo "  sudo apt-get update"
  echo "  sudo apt-get install redis-server"
  echo "  sudo systemctl start redis-server"
  echo ""
  echo "Option 2: Use Docker"
  echo "  docker run -d --name spinelift-redis -p 6379:6379 redis:7-alpine"
  echo ""
  echo "Option 3: Use the docker-compose setup"
  echo "  docker-compose up -d redis"
fi