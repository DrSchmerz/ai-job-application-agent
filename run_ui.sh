#!/bin/bash
# Launch Application Tracker

echo "🚀 Starting Application Tracker"
echo ""

# Check venv
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Run Streamlit
echo "🌐 Launching at http://localhost:8501"
echo ""
streamlit run ui/app.py
