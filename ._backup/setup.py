#!/usr/bin/env python3
"""
Simple Setup Script for Agentic RAG Drive Monitor
No Docker required - runs directly with Python
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any

class SimpleSetup:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.python_executable = sys.executable
        
    def print_header(self):
        """Print setup header"""
        print("=" * 60)
        print("🤖 Agentic RAG Google Drive Monitor Setup")
        print("=" * 60)
        print("This setup will help you configure the Drive monitor")
        print("without Docker - running directly with Python.\n")
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print("❌ Python 3.9 or higher is required")
            print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def create_virtual_environment(self):
        """Create virtual environment if it doesn't exist"""
        venv_path = self.base_dir / "venv"
        
        if venv_path.exists():
            print("✅ Virtual environment already exists")
            return True
        
        print("📦 Creating virtual environment...")
        try:
            subprocess.run([self.python_executable, "-m", "venv", "venv"], 
                         check=True, cwd=self.base_dir)
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def get_venv_python(self):
        """Get the Python executable in the virtual environment"""
        if platform.system() == "Windows":
            return self.base_dir / "venv" / "Scripts" / "python.exe"
        else:
            return self.base_dir / "venv" / "bin" / "python"
    
    def install_dependencies(self):
        """Install required Python packages"""
        print("📦 Installing dependencies...")
        
        # Updated requirements for Python 3.13 compatibility - SIMPLIFIED VERSION
        requirements = [
            "google-auth>=2.23.0",
            "google-auth-oauthlib>=1.1.0", 
            "google-auth-httplib2>=0.1.0",
            "google-api-python-client>=2.100.0",
            "openai>=1.0.0",
            "python-docx>=0.8.0",
            "PyPDF2>=3.0.0",
            "openpyxl>=3.1.0",
            "aiofiles>=23.0.0",
            "schedule>=1.2.0",
            "python-dotenv>=1.0.0",
            "rich>=13.0.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "scikit-learn>=1.3.0"
        ]
        
        venv_python = self.get_venv_python()
        
        # First upgrade pip and setuptools
        try:
            print("  Upgrading pip and setuptools...")
            subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to upgrade pip: {e}")
        
        # Install packages one by one with better error handling
        failed_packages = []
        
        for package in requirements:
            try:
                print(f"  Installing {package}...")
                result = subprocess.run([str(venv_python), "-m", "pip", "install", package], 
                                     check=True, capture_output=True, text=True)
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}")
                print(f"   Error: {e.stderr if e.stderr else e.stdout}")
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n⚠️  Some packages failed to install: {failed_packages}")
            print("   You may need to install these manually or use a different Python version.")
            
            # Ask if user wants to continue
            continue_anyway = input("Continue with setup anyway? (y/n): ").strip().lower()
            if continue_anyway not in ['y', 'yes']:
                return False
        
        print("✅ Dependencies installation completed")
        return True
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            "logs",
            "summaries", 
            "simple_db",
            "backups"
        ]
        
        for dir_name in directories:
            dir_path = self.base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {dir_name}")
    
    def create_env_file(self):
        """Interactive creation of .env file"""
        print("\n🔧 Setting up configuration...")
        
        env_file = self.base_dir / ".env"
        
        if env_file.exists():
            overwrite = input("📝 .env file exists. Overwrite? (y/n): ").strip().lower()
            if overwrite not in ['y', 'yes']:
                print("✅ Using existing .env file")
                return True
        
        print("\nPlease provide the following information:")
        
        # Google credentials
        print("\n📁 Google Drive API Setup:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a project and enable Drive & Calendar APIs")
        print("3. Create OAuth 2.0 credentials (Desktop Application)")
        print("4. Download the JSON file")
        
        credentials_path = input("Enter path to Google credentials JSON file: ").strip()
        if not Path(credentials_path).exists():
            print("❌ Credentials file not found")
            return False
        
        # OpenAI API key
        print("\n🤖 OpenAI API Setup:")
        openai_key = input("Enter your OpenAI API key: ").strip()
        if not openai_key:
            print("❌ OpenAI API key is required")
            return False
        
        # Email notifications (optional)
        print("\n📧 Email Notifications (optional):")
        enable_email = input("Enable email notifications? (y/n): ").strip().lower()
        
        email_config = ""
        if enable_email in ['y', 'yes']:
            email_host = input("Email host (e.g., smtp.gmail.com): ").strip()
            email_port = input("Email port (e.g., 587): ").strip()
            email_username = input("Email username: ").strip()
            email_password = input("Email password/app password: ").strip()
            email_recipients = input("Recipients (comma-separated): ").strip()
            
            email_config = f"""
# Email Configuration
EMAIL_NOTIFICATIONS=true
EMAIL_HOST={email_host}
EMAIL_PORT={email_port}
EMAIL_USERNAME={email_username}
EMAIL_PASSWORD={email_password}
EMAIL_RECIPIENTS={email_recipients}
"""
        else:
            email_config = "EMAIL_NOTIFICATIONS=false"
        
        # Other settings
        scan_interval = input("Scan interval in hours (default 24): ").strip() or "24"
        timezone = input("Timezone (default America/New_York): ").strip() or "America/New_York"
        
        # Create .env content
        env_content = f"""# Agentic RAG Drive Monitor Configuration

# Google API Credentials  
GOOGLE_CREDENTIALS_PATH={credentials_path}
GOOGLE_TOKEN_PATH=./token.json

# OpenAI API Key
OPENAI_API_KEY={openai_key}

{email_config}

# Application Settings
SCAN_INTERVAL_HOURS={scan_interval}
DEFAULT_TIMEZONE={timezone}
LOG_LEVEL=INFO
VECTOR_DB_PATH=./simple_db
STATE_FILE_PATH=./app_state.json

# Calendar Settings
DEFAULT_EVENT_DURATION_HOURS=1
REMINDER_MINUTES_BEFORE=60
"""
        
        # Write .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Configuration file created")
        return True
    
    def create_startup_scripts(self):
        """Create convenient startup scripts"""
        
        # Windows batch file
        if platform.system() == "Windows":
            batch_content = f"""@echo off
echo Starting Agentic RAG Drive Monitor...
cd /d "{self.base_dir}"
venv\\Scripts\\python.exe main.py --mode=setup
pause
"""
            with open(self.base_dir / "start_monitor.bat", 'w') as f:
                f.write(batch_content)
            
            print("✅ Created start_monitor.bat")
        
        # Unix shell script
        else:
            shell_content = f"""#!/bin/bash
echo "Starting Agentic RAG Drive Monitor..."
cd "{self.base_dir}"
./venv/bin/python main.py --mode=setup
"""
            script_path = self.base_dir / "start_monitor.sh"
            with open(script_path, 'w') as f:
                f.write(shell_content)
            
            # Make executable
            script_path.chmod(0o755)
            print("✅ Created start_monitor.sh")
    
    def test_installation(self):
        """Test if everything is working"""
        print("\n🧪 Testing installation...")
        
        venv_python = self.get_venv_python()
        
        # Test imports - SIMPLIFIED VERSION (no sentence-transformers or chromadb)
        test_script = """
try:
    import google.auth
    import openai
    import sklearn
    import pandas
    import numpy
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
"""
        
        try:
            subprocess.run([str(venv_python), "-c", test_script], 
                         check=True, cwd=self.base_dir)
            return True
        except subprocess.CalledProcessError:
            print("❌ Installation test failed")
            return False
    
    def create_quick_start_guide(self):
        """Create a quick start guide"""
        guide_content = f"""# 🚀 Quick Start Guide

## Starting the Monitor

### Option 1: Using startup script
- **Windows**: Double-click `start_monitor.bat`
- **Linux/Mac**: Run `./start_monitor.sh`

### Option 2: Manual start
```bash
# Activate virtual environment
{"venv\\Scripts\\activate" if platform.system() == "Windows" else "source venv/bin/activate"}

# Run initial setup and folder selection
python main.py --mode=setup

# Run manual scan
python main.py --mode=scan

# Start scheduled monitoring
python scheduler.py --mode=schedule
```

## Folder Selection

On first run, you'll be prompted to:
1. Select which Google Drive folder to monitor
2. Choose whether to include subfolders
3. Authenticate with Google (browser will open)

## Daily Operation

The system will:
1. Scan your selected folder daily at 9 AM
2. Analyze new documents with AI
3. Extract action items and summaries
4. Create calendar events for follow-ups
5. Send email notifications (if enabled)

## Files Created

- `daily_summary_YYYYMMDD.md` - Daily summaries
- `folder_config.json` - Your folder selection
- `app_state.json` - Tracks processed files
- `drive_monitor.log` - Application logs
- `simple_db/` - Simple document database

## Viewing Results

- Check `summaries/` folder for daily reports
- View logs in `logs/` folder for troubleshooting
- Calendar events appear in your Google Calendar
- Email summaries sent to configured recipients

## Troubleshooting

1. **Authentication Issues**:
   ```bash
   # Delete token and re-authenticate
   rm token.json
   python main.py --mode=setup
   ```

2. **Folder Not Found**:
   ```bash
   # Reconfigure folder selection
   rm folder_config.json
   python main.py --mode=setup
   ```

3. **API Rate Limits**:
   - Wait a few minutes and try again
   - Check your OpenAI usage limits

4. **View Logs**:
   ```bash
   tail -f drive_monitor.log
   ```

## Customization

Edit `.env` file to change:
- Scan frequency
- Email settings
- Timezone
- Log levels
"""
        
        with open(self.base_dir / "QUICK_START.md", 'w') as f:
            f.write(guide_content)
        
        print("✅ Created QUICK_START.md")
    
    def run_setup(self):
        """Run the complete setup process"""
        self.print_header()
        
        # Check prerequisites
        if not self.check_python_version():
            return False
        
        # Setup steps
        steps = [
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up directories", self.setup_directories),
            ("Creating configuration", self.create_env_file),
            ("Creating startup scripts", self.create_startup_scripts),
            ("Testing installation", self.test_installation),
            ("Creating quick start guide", self.create_quick_start_guide)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        # Success message
        print("\n" + "=" * 60)
        print("🎉 Setup completed successfully!")
        print("=" * 60)
        print("\n📖 Next steps:")
        print("1. Read QUICK_START.md for usage instructions")
        
        if platform.system() == "Windows":
            print("2. Double-click start_monitor.bat to begin")
        else:
            print("2. Run ./start_monitor.sh to begin")
        
        print("3. Follow the folder selection prompts")
        print("4. The system will start monitoring your chosen folder")
        
        return True

def main():
    setup = SimpleSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Quick health check
        print("🔍 Checking installation...")
        if setup.test_installation():
            print("✅ Installation is working correctly")
        else:
            print("❌ Installation has issues - run setup again")
        return
    
    # Run full setup
    success = setup.run_setup()
    
    if not success:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()