#!/bin/bash
###############################################################################
# ICU Monitoring System - Complete Setup Script
# Starts all components for the active alerting system
###############################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🏥 ICU Monitoring System - Active Alerting Setup"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Virtual environment not activated!${NC}"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "Please start Docker first."
    exit 1
fi

echo -e "${BLUE}Step 1: Starting Docker services...${NC}"
cd "$PROJECT_ROOT"
docker compose up -d
sleep 10

echo -e "${GREEN}✅ Docker services started${NC}"
echo ""

echo -e "${BLUE}Step 2: Verifying services...${NC}"
docker compose ps

echo ""
echo -e "${BLUE}Step 3: Initializing databases...${NC}"
python "$SCRIPT_DIR/init_databases.py"

# Check if patients exist
PATIENT_COUNT=$(python -c "from src.database.session import SessionLocal; from src.database.models import Patient; db = SessionLocal(); count = db.query(Patient).filter(Patient.active_monitoring == True).count(); db.close(); print(count)")

if [ "$PATIENT_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠️  No patients found. Loading 50 ICU patients...${NC}"
    python "$SCRIPT_DIR/load_icu_patients.py" --limit 50
else
    echo -e "${GREEN}✅ Found $PATIENT_COUNT patients ready for monitoring${NC}"
fi

echo ""
echo -e "${BLUE}Step 4: Starting Kafka Producer (Patient Vitals)...${NC}"
python "$SCRIPT_DIR/run_producer.py" &
PRODUCER_PID=$!
echo -e "${GREEN}✅ Producer started (PID: $PRODUCER_PID)${NC}"

echo ""
echo -e "${BLUE}Step 4: Starting Kafka Producer (Patient Vitals)...${NC}"
python "$SCRIPT_DIR/run_producer.py" &
PRODUCER_PID=$!
echo -e "${GREEN}✅ Producer started (PID: $PRODUCER_PID)${NC}"

sleep 3

echo ""
echo -e "${BLUE}Step 5: Starting Kafka Consumer (Data Pipeline)...${NC}"
python "$SCRIPT_DIR/run_consumer.py" &
CONSUMER_PID=$!
echo -e "${GREEN}✅ Consumer started (PID: $CONSUMER_PID)${NC}"

sleep 3

echo ""
echo -e "${BLUE}Step 6: Starting WebSocket Alert Server...${NC}"
python "$SCRIPT_DIR/run_alert_server.py" &
ALERT_SERVER_PID=$!
echo -e "${GREEN}✅ Alert Server started (PID: $ALERT_SERVER_PID)${NC}"

sleep 3

echo ""
echo -e "${BLUE}Step 7: Starting Streamlit Dashboard...${NC}"
cd "$PROJECT_ROOT/src/dashboard"
streamlit run streamlit_app.py --server.port 8501 &
DASHBOARD_PID=$!
echo -e "${GREEN}✅ Dashboard started (PID: $DASHBOARD_PID)${NC}"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ ALL SYSTEMS ONLINE!${NC}"
echo "=================================================="
echo ""
echo "📊 Dashboard: http://localhost:8501"
echo "🔌 WebSocket: ws://localhost:8765/ws/alerts"
echo "🐳 Docker Services:"
echo "   - Kafka: localhost:9092"
echo "   - Zookeeper: localhost:2181"
echo "   - PostgreSQL: localhost:5432"
echo "   - InfluxDB: localhost:8086"
echo ""
echo "Process IDs:"
echo "   - Producer: $PRODUCER_PID"
echo "   - Consumer: $CONSUMER_PID"
echo "   - Alert Server: $ALERT_SERVER_PID"
echo "   - Dashboard: $DASHBOARD_PID"
echo ""
echo "To stop all services:"
echo "   kill $PRODUCER_PID $CONSUMER_PID $ALERT_SERVER_PID $DASHBOARD_PID"
echo "   docker-compose down"
echo ""
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop monitoring...${NC}"
echo ""

# Save PIDs to file
echo "$PRODUCER_PID" > /tmp/icu_producer.pid
echo "$CONSUMER_PID" > /tmp/icu_consumer.pid
echo "$ALERT_SERVER_PID" > /tmp/icu_alert_server.pid
echo "$DASHBOARD_PID" > /tmp/icu_dashboard.pid

# Monitor logs
tail -f /dev/null
