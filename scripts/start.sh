#!/bin/bash
# Start all services for ICU Monitoring System

echo "Starting ICU Monitoring System..."
echo ""

# Start Docker containers
echo "Starting infrastructure (Kafka, PostgreSQL, InfluxDB)..."
docker compose up -d

echo ""
echo "Services started!"
echo ""
echo "Access points:"
echo "  - Kafka: localhost:9092"
echo "  - PostgreSQL: localhost:5432"
echo "  - InfluxDB UI: http://localhost:8086"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"
echo ""
