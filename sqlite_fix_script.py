#!/usr/bin/env python3
"""
SQLite Fix Script: Replace PostgreSQL with SQLite for development
This eliminates the problematic psycopg2-binary dependency
"""

import os
import sys
from pathlib import Path

def fix_sqlite_setup():
    """Fix the setup to use SQLite instead of PostgreSQL"""
    
    backend_dir = Path("agentic-rag-web/backend")
    
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    print("🔧 Fixing backend to use SQLite (no PostgreSQL compilation needed)...")
    
    # Updated requirements.txt without psycopg2-binary
    sqlite_requirements = '''# Web Framework Dependencies
fastapi==0.115.9
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database (SQLite - no compilation needed!)
sqlalchemy==2.0.23

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Your Original Dependencies
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-api-python-client>=2.100.0
openai>=1.0.0
python-docx>=0.8.0
PyPDF2>=3.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
pandas>=2.0.0
scikit-learn>=1.3.0

# Optional: Schedule and async
schedule>=1.2.0
aiofiles>=24.1.0
'''
    
    # Write updated requirements
    req_file = backend_dir / "requirements.txt"
    with open(req_file, 'w') as f:
        f.write(sqlite_requirements)
    
    print("✅ Updated requirements.txt (removed PostgreSQL dependency)")
    
    # Updated environment file for SQLite
    env_example = '''# Database (SQLite - no setup needed)
DATABASE_URL=sqlite:///./drive_monitor.db

# Security
SECRET_KEY=dev-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000

# Application
DEBUG=True
LOG_LEVEL=INFO
'''
    
    env_file = backend_dir / ".env.example"
    with open(env_file, 'w') as f:
        f.write(env_example)
    
    print("✅ Updated .env.example for SQLite")
    
    # Create a simple start script
    start_script = '''#!/bin/bash
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
'''
    
    script_path = backend_dir / "start.sh"
    with open(script_path, 'w') as f:
        f.write(start_script)
    
    # Make executable
    try:
        os.chmod(script_path, 0o755)
        print("✅ Created start.sh script")
    except:
        print("✅ Created start.sh script (make executable with: chmod +x start.sh)")
    
    # Windows batch file
    windows_script = '''@echo off
echo 🚀 Starting Agentic RAG Backend (SQLite version)...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\\Scripts\\activate

REM Install requirements
echo 📦 Installing requirements...
pip install -r requirements.txt

REM Start the server
echo 🌐 Starting server on http://localhost:8000
python -m app.main
'''
    
    windows_script_path = backend_dir / "start.bat"
    with open(windows_script_path, 'w') as f:
        f.write(windows_script)
    
    print("✅ Created start.bat script for Windows")
    
    # Update docker-compose to remove PostgreSQL dependency
    docker_compose_sqlite = '''version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: sqlite:///./drive_monitor.db
      SECRET_KEY: dev-secret-key
      CORS_ORIGINS: http://localhost:3000
    volumes:
      - ./backend:/app
      - sqlite_data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  sqlite_data:'''
    
    docker_compose_path = Path("agentic-rag-web/docker-compose.yml")
    with open(docker_compose_path, 'w') as f:
        f.write(docker_compose_sqlite)
    
    print("✅ Updated docker-compose.yml for SQLite")
    
    # Create a simple manual installation guide
    install_guide = '''# 🚀 Quick Installation Guide

## Option 1: Automatic (Recommended)

### macOS/Linux:
```bash
cd agentic-rag-web/backend
./start.sh
```

### Windows:
```cmd
cd agentic-rag-web\\backend
start.bat
```

## Option 2: Manual

```bash
cd agentic-rag-web/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# venv\\Scripts\\activate   # Windows

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
'''
    
    guide_path = backend_dir / "INSTALL.md"
    with open(guide_path, 'w') as f:
        f.write(install_guide)
    
    print("✅ Created INSTALL.md guide")
    
    print(f"\n🎉 SQLite setup completed!")
    return True

def main():
    print("🔧 Fixing PostgreSQL compilation issue...")
    print("💡 Solution: Switch to SQLite (no compilation needed)")
    
    if fix_sqlite_setup():
        print("\n✅ Fix completed!")
        print("\n🚀 Now try one of these options:")
        
        print("\n🎯 Option 1: Automatic Start")
        if os.name == 'nt':  # Windows
            print("cd agentic-rag-web\\backend")
            print("start.bat")
        else:  # macOS/Linux
            print("cd agentic-rag-web/backend")
            print("./start.sh")
        
        print("\n🎯 Option 2: Manual (if automatic fails)")
        print("cd agentic-rag-web/backend")
        print("python3 -m venv venv")
        if os.name == 'nt':
            print("venv\\Scripts\\activate")
        else:
            print("source venv/bin/activate")
        print("pip install -r requirements.txt")
        print("python -m app.main")
        
        print("\n🎯 Option 3: System Python (simplest)")
        print("cd agentic-rag-web/backend")
        print("pip install -r requirements.txt")
        print("python -m app.main")
        
        print("\n💡 All options use SQLite - no PostgreSQL compilation needed!")
        print("🌐 Backend will run on: http://localhost:8000")
        
        print(f"\n📖 See agentic-rag-web/backend/INSTALL.md for detailed instructions")
        
    else:
        print("\n❌ Fix failed")

if __name__ == "__main__":
    main()