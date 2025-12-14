#!/bin/bash

# setup_cron.sh
# -----------------------------------------------------------------------------
# Reconciliation strategy.
# Usage: ./scripts/setup_cron.sh
# -----------------------------------------------------------------------------

# Get the absolute path of the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXEC="python3"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "#########################################################################"
echo "# TFT DATA EXTRACTION - CRON CONFIGURATION"
echo "#########################################################################"
echo ""
echo "Add the following lines to your crontab (run 'crontab -e'):"
echo ""

# Daily Collection (Incremental) - 2:00 AM UTC every day
# Captures matches from the previous day
echo "# Daily Collection (Incremental) - Runs at 02:00 UTC daily"
echo "0 2 * * * cd \"$PROJECT_ROOT\" && $PYTHON_EXEC scripts/automated_collection.py --mode incremental >> \"$LOG_DIR/cron_daily.log\" 2>&1"
echo ""

# Weekly Reconciliation - 3:00 PM UTC every Monday
echo "# Weekly Reconciliation - Runs at 15:00 UTC every Monday"
echo "0 15 * * 1 cd \"$PROJECT_ROOT\" && $PYTHON_EXEC scripts/automated_collection.py --mode weekly >> \"$LOG_DIR/cron_weekly.log\" 2>&1"

echo ""
echo "#########################################################################"
echo "# VALIDATION"
echo "#########################################################################"
echo "1. Ensure '$PYTHON_EXEC' is the correct python interpreter."
echo "   If using a venv, replace it with '/path/to/venv/bin/python'."
echo "2. Ensure the RIOT_API_KEY is available to cron."
echo "   You may need to load it in the command or source .env:"
echo "   Example: 0 2 * * * cd ... && source .env && python ..."
