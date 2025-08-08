@echo off
echo 🚀 Starting Agentic RAG Backend (SQLite version)...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo 📦 Installing requirements...
pip install -r requirements.txt

REM Start the server
echo 🌐 Starting server on http://localhost:8000
python -m app.main
