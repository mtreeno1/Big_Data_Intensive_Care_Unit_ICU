#!/bin/bash
###############################################################################
# Quick Reset Script - Reset database và load 10 bệnh nhân
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "🔄 Quick Reset - Load 10 Patients"
echo "=================================="
echo ""

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated!${NC}"
    echo "Activating virtual environment..."
    source "$PROJECT_ROOT/venv/bin/activate"
fi

cd "$PROJECT_ROOT"

# Step 1: Reset database
echo -e "${BLUE}Step 1: Resetting database...${NC}"
python "$SCRIPT_DIR/reset_database.py"

# Step 2: Initialize database
echo ""
echo -e "${BLUE}Step 2: Initializing database...${NC}"
python "$SCRIPT_DIR/init_databases.py"

# Step 3: Load 10 patients
echo ""
echo -e "${BLUE}Step 3: Loading 10 patients...${NC}"
python "$SCRIPT_DIR/load_icu_patients.py" --limit 10

# Step 4: Verify
echo ""
echo -e "${BLUE}Step 4: Verifying...${NC}"
python "$SCRIPT_DIR/check_patients.py"

echo ""
echo -e "${GREEN}✅ Reset complete! Database ready with 10 patients.${NC}"
echo ""
echo "Next steps:"
echo "  1. Start dashboard: streamlit run src/dashboard/streamlit_app.py"
echo "  2. Or start full system: ./scripts/setup_alert_system.sh"
echo ""
