#!/bin/bash
# OpenCode Task Monitor Starter
# Usage: ./start_monitor.sh <session_id> <task_name> [chat_id] [max_no_change] [max_duration]
#
# Example:
#   ./start_monitor.sh ses_abc123 "Code Review"
#   ./start_monitor.sh ses_abc123 "Code Review" 6186153489
#   ./start_monitor.sh ses_abc123 "Code Review" 6186153489 20 7200

set -e

SESSION_ID="$1"
TASK_NAME="$2"
CHAT_ID="${3:-6186153489}"
MAX_NO_CHANGE="${4:-15}"
MAX_DURATION="${5:-3600}"

if [ -z "$SESSION_ID" ] || [ -z "$TASK_NAME" ]; then
    echo "Usage: $0 <session_id> <task_name> [chat_id] [max_no_change] [max_duration]"
    echo ""
    echo "Arguments:"
    echo "  session_id      OpenCode session ID"
    echo "  task_name       Human-readable task name"
    echo "  chat_id         Telegram chat ID (default: 6186153489)"
    echo "  max_no_change   Max no-change checks before stuck (default: 15)"
    echo "  max_duration    Max monitoring duration in seconds (default: 3600)"
    echo ""
    echo "Examples:"
    echo "  $0 ses_abc123 'Code Review Task'"
    echo "  $0 ses_abc123 'Code Review Task' 6186153489"
    echo "  $0 ses_abc123 'Code Review Task' 6186153489 20 7200"
    exit 1
fi

# Check for .env configuration
ENV_FILE="${PWD}/.env"
if [ -f "$ENV_FILE" ]; then
    echo "✓ Found .env file: $ENV_FILE"
    # Check if TELEGRAM_BOT_TOKEN is set
    if grep -q "TELEGRAM_BOT_TOKEN" "$ENV_FILE"; then
        echo "✓ TELEGRAM_BOT_TOKEN configured"
    else
        echo "⚠️  Warning: TELEGRAM_BOT_TOKEN not found in .env"
        echo "   Notifications will not be sent!"
    fi
else
    echo "⚠️  Warning: .env file not found at $ENV_FILE"
    echo "   Looking for system environment variables..."
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/opencode_monitor.py"

if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "Error: Monitor script not found at $MONITOR_SCRIPT"
    exit 1
fi

# Create log directory
LOG_DIR="${PWD}/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/opencode_monitor_${SESSION_ID: -8}_${TIMESTAMP}.log"

echo ""
echo "🚀 Starting OpenCode Task Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Session ID    : $SESSION_ID"
echo "Task Name     : $TASK_NAME"
echo "Chat ID       : $CHAT_ID"
echo "Max No Change : $MAX_NO_CHANGE"
echo "Max Duration  : $MAX_DURATION seconds"
echo "Log File      : $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start monitor in background
nohup python3 "$MONITOR_SCRIPT" "$SESSION_ID" "$TASK_NAME" \
    --chat-id "$CHAT_ID" \
    --max-no-change "$MAX_NO_CHANGE" \
    --max-duration "$MAX_DURATION" \
    > "$LOG_FILE" 2>&1 &

PID=$!

sleep 1

if ps -p $PID > /dev/null 2>&1; then
    echo ""
    echo "✅ Monitor started successfully!"
    echo "   PID: $PID"
    echo ""
    echo "You will receive a Telegram notification when the task completes."
    echo ""
    echo "Commands:"
    echo "  Stop monitoring:  kill $PID"
    echo "  View logs:        tail -f $LOG_FILE"
    echo "  Check status:     ps -p $PID"
else
    echo ""
    echo "❌ Failed to start monitor"
    echo "Check logs: $LOG_FILE"
    exit 1
fi
