#!/usr/bin/env python3
"""
Virtual Environment Fix Script
Creates clean venv to avoid dependency conflicts
"""

import os
import sys
import subprocess
from pathlib import Path

def create_clean_venv():
    """Create clean virtual environment for the backend"""
    
    target_dir = Path("agentic-rag-web")
    
    if not target_dir.exists():
        print("❌ agentic-rag-web directory not found")
        return False
    
    backend_dir = target_dir / "backend"
    if not backend_dir.exists():
        print("❌ backend directory not found")
        return False
    
    print("🐍 Creating clean virtual environment...")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Remove existing venv if it exists
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("🧹 Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_dir)
    
    try:
        # Create new virtual environment
        print("📦 Creating new virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        
        # Determine the correct paths for different OS
        if os.name == 'nt':  # Windows
            python_path = venv_dir / "Scripts" / "python.exe"
            pip_path = venv_dir / "Scripts" / "pip.exe"
        else:  # macOS/Linux
            python_path = venv_dir / "bin" / "python"
            pip_path = venv_dir / "bin" / "pip"
        
        # Upgrade pip first
        print("⬆️  Upgrading pip...")
        subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
        
        # Install requirements in clean environment
        print("📦 Installing requirements in clean environment...")
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Virtual environment created successfully!")
        
        # Create activation scripts
        create_activation_scripts(backend_dir, python_path)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_activation_scripts(backend_dir, python_path):
    """Create easy activation scripts"""
    
    # Create start script for different OS
    if os.name == 'nt':  # Windows
        start_script = '''@echo off
echo 🚀 Starting Agentic RAG Drive Monitor Backend...
call venv\\Scripts\\activate
python -m app.main
'''
        script_path = backend_dir / "start-backend.bat"
    else:  # macOS/Linux
        start_script = '''#!/bin/bash
echo "🚀 Starting Agentic RAG Drive Monitor Backend..."
source venv/bin/activate
python -m app.main
'''
        script_path = backend_dir / "start-backend.sh"
        
    with open(script_path, 'w') as f:
        f.write(start_script)
    
    # Make executable on Unix systems
    if os.name != 'nt':
        try:
            os.chmod(script_path, 0o755)
        except:
            pass
    
    print(f"✅ Created {script_path.name}")

def update_requirements():
    """Update requirements.txt to fix version conflicts"""
    
    backend_dir = Path("agentic-rag-web/backend")
    req_file = backend_dir / "requirements.txt"
    
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print("🔧 Updating requirements.txt to resolve conflicts...")
    
    # Updated requirements with compatible versions
    updated_requirements = '''# Web Framework Dependencies (Compatible versions)
fastapi==0.115.9
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database & Cache
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Your Original Dependencies (Core essentials only)
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
aiofiles>=23.0.0
'''
    
    with open(req_file, 'w') as f:
        f.write(updated_requirements)
    
    print("✅ Updated requirements.txt with compatible versions")
    return True

def main():
    print("🔧 Fixing Virtual Environment and Dependencies...")
    
    # Update requirements first
    if not update_requirements():
        print("❌ Failed to update requirements")
        return
    
    # Create clean virtual environment
    if create_clean_venv():
        print("\n🎉 SUCCESS! Clean environment created!")
        print("\n🚀 Next steps:")
        
        if os.name == 'nt':  # Windows
            print("1. cd agentic-rag-web\\backend")
            print("2. start-backend.bat")
            print("\nOr manually:")
            print("1. cd agentic-rag-web\\backend")
            print("2. venv\\Scripts\\activate")
            print("3. python -m app.main")
        else:  # macOS/Linux
            print("1. cd agentic-rag-web/backend")
            print("2. ./start-backend.sh")
            print("\nOr manually:")
            print("1. cd agentic-rag-web/backend")
            print("2. source venv/bin/activate")
            print("3. python -m app.main")
        
        print("\n🌐 Backend will be available at: http://localhost:8000")
        print("💡 For frontend, open another terminal and run:")
        print("   cd agentic-rag-web/frontend")
        print("   npm install && npm run dev")
        
    else:
        print("\n❌ Failed to create virtual environment")
        print("\n🔧 Alternative: Try with system Python:")
        print("   pip install --force-reinstall -r agentic-rag-web/backend/requirements.txt")

if __name__ == "__main__":
    main()