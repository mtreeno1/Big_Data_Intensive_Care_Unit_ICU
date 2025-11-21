#!/bin/bash
# Stop all services for ICU Monitoring System

echo "Stopping ICU Monitoring System..."
docker-compose down
echo "All services stopped."
