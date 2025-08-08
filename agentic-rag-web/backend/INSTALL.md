# 🚀 Quick Installation Guide

## Option 1: Automatic (Recommended)

### macOS/Linux:
```bash
cd agentic-rag-web/backend
./start.sh
```

### Windows:
```cmd
cd agentic-rag-web\backend
start.bat
```

## Option 2: Manual

```bash
cd agentic-rag-web/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install requirements (no compilation needed!)
pip install -r requirements.txt

# Start the backend
python -m app.main
```

## Option 3: System Python (if venv has issues)

```bash
cd agentic-rag-web/backend

# Install directly to system Python
pip install -r requirements.txt

# Start the backend
python -m app.main
```

## Frontend Setup (separate terminal)

```bash
cd agentic-rag-web/frontend
npm install
npm run dev
```

## Your App URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend Health: http://localhost:8000/health

## Database

Using SQLite (drive_monitor.db file) - no setup needed!
