#!/bin/bash
set -e

PROJECT_DIR="$HOME/gmail-agent"
cd "$PROJECT_DIR"

if ! pgrep -x "ollama" > /dev/null; then
    brew services start ollama
    sleep 3
fi

ollama run llama3.1:8b "ping" > /dev/null 2>&1 || true

source "$PROJECT_DIR/venv/bin/activate"
python email_agent.py >> "$PROJECT_DIR/agent.log" 2>&1
