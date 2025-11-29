#!/bin/bash

echo "🔧 Setting up virtual environment for Geofence_Service..."

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# Activate venv depending on OS
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate    # Windows
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate        # Linux/Mac
else
    echo "❌ Could not find virtual environment activation script."
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀 Launching Geofence_Service..."
# Keep server alive until reviewer presses CTRL+C
uvicorn app.main:app --reload --loop asyncio --http h11