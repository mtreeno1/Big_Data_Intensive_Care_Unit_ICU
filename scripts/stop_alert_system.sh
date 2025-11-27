#!/bin/bash
###############################################################################
# ICU Monitoring System - Stop All Services
###############################################################################

echo "🛑 Stopping ICU Monitoring System..."
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Stop Python processes
if [ -f /tmp/icu_producer.pid ]; then
    PID=$(cat /tmp/icu_producer.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping Producer (PID: $PID)...${NC}"
        kill "$PID"
    fi
    rm /tmp/icu_producer.pid
fi

if [ -f /tmp/icu_consumer.pid ]; then
    PID=$(cat /tmp/icu_consumer.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping Consumer (PID: $PID)...${NC}"
        kill "$PID"
    fi
    rm /tmp/icu_consumer.pid
fi

if [ -f /tmp/icu_alert_server.pid ]; then
    PID=$(cat /tmp/icu_alert_server.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping Alert Server (PID: $PID)...${NC}"
        kill "$PID"
    fi
    rm /tmp/icu_alert_server.pid
fi

if [ -f /tmp/icu_dashboard.pid ]; then
    PID=$(cat /tmp/icu_dashboard.pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping Dashboard (PID: $PID)...${NC}"
        kill "$PID"
    fi
    rm /tmp/icu_dashboard.pid
fi

# Stop Docker services
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Stopping Docker services...${NC}"
cd "$PROJECT_ROOT"
docker compose down

echo ""
echo -e "${GREEN}✅ All services stopped!${NC}"
echo ""
