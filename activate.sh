#!/bin/bash
# Activate the MLB Agent Lab environment

echo "🚀 Activating MLB Agent Lab environment..."

# Activate virtual environment
source ~/mlb-agent-lab/venv/bin/activate

# Load configuration
source ~/mlb-agent-lab/config.env

# Navigate to workspace
cd ~/mlb-agent-lab/workspace

echo "✅ Environment ready! You're in: $(pwd)"
echo "📦 Virtual environment: $VIRTUAL_ENV"
echo "🏗️ Project: $PROJECT_ID"