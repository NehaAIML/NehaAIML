#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cd /Users/nehapurohit/gmail-agent
/Users/nehapurohit/gmail-agent/venv/bin/python email_agent.py >> /Users/nehapurohit/gmail-agent/agent.log 2>&1
