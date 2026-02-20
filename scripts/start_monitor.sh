#!/bin/bash
# OpenCode Task Monitor Starter
# Usage: ./start_monitor.sh <session_id> <task_name> [chat_id]
#
# Example:
#   ./start_monitor.sh ses_abc123 "Code Review"
#   ./start_monitor.sh ses_abc123 "Code Review" 6186153489

set -e

SESSION_ID="$1"
TASK_NAME="$2"
CHAT_ID="${3:-6186153489}"

if [ -z "$SESSION_ID" ] || [ -z "$TASK_NAME" ]; then
    echo "Usage: $0 <session_id> <task_name> [chat_id]"
    echo ""
    echo "Examples:"
    echo "  $0 ses_abc123 'Code Review Task'"
    echo "  $0 ses_abc123 'Code Review Task' 6186153489"
    exit 1
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

echo "🚀 Starting OpenCode Task Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Session ID : $SESSION_ID"
echo "Task Name  : $TASK_NAME"
echo "Chat ID    : $CHAT_ID"
echo "Log File   : $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start monitor in background
nohup python3 "$MONITOR_SCRIPT" "$SESSION_ID" "$TASK_NAME" --chat-id "$CHAT_ID" > "$LOG_FILE" 2>&1 &

PID=$!

sleep 1

if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Monitor started successfully!"
    echo "   PID: $PID"
    echo ""
    echo "You will receive a Telegram notification when the task completes."
    echo ""
    echo "To stop monitoring: kill $PID"
    echo "To view logs: tail -f $LOG_FILE"
else
    echo "❌ Failed to start monitor"
    exit 1
fi
