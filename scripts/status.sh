#!/bin/bash
# Check status of all services

echo "ICU Monitoring System - Service Status"
echo "======================================"
echo ""

# Check Docker containers
echo "Docker Containers:"
docker-compose ps
echo ""

# Check Kafka topics
echo "Kafka Topics:"
docker exec -it icu-kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null || echo "Kafka not ready or no topics created yet"
echo ""

# Check if Python venv is active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Python virtual environment: ACTIVE"
    echo "   Path: $VIRTUAL_ENV"
else
    echo "❌ Python virtual environment: NOT ACTIVE"
    echo "   Run: source venv/bin/activate"
fi
echo ""
