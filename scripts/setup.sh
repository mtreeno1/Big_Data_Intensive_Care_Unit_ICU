#!/bin/bash
# Setup script for ICU Monitoring System

set -e  # Exit on error

echo "=================================="
echo "ICU Monitoring System - Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check if Docker is installed
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check if Docker Compose is installed
echo "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose found${NC}"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install requirements
echo "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create .env file
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✅ Logs directory ready${NC}"

# Start Docker containers
echo ""
echo "Starting Big Data infrastructure (Kafka, PostgreSQL, InfluxDB)..."
echo "This may take a few minutes on first run..."
docker-compose up -d

echo ""
echo "Waiting for services to initialize (30 seconds)..."
sleep 30

# Check container status
echo ""
echo "Checking service status..."
docker-compose ps

echo ""
echo "=================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Read the quickstart guide: docs/QUICKSTART.md"
echo "3. Start building the data simulator!"
echo ""
echo "Services running:"
echo "  - Kafka: localhost:9092"
echo "  - PostgreSQL: localhost:5432"
echo "  - InfluxDB: http://localhost:8086"
echo ""
echo "To stop services: docker-compose down"
echo ""
