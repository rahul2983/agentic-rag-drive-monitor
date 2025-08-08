#!/bin/bash
echo "🚀 Starting Agentic RAG Backend (SQLite version)..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Start the server
echo "🌐 Starting server on http://localhost:8000"
python -m app.main
