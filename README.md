# 🤖 Agentic RAG Google Drive Monitor

An intelligent system that monitors specific Google Drive folders, analyzes documents with AI, extracts actionable insights, and automatically creates calendar events for follow-ups.

## 🚀 Quick Start

### 1. Setup
```bash
# Run the automated setup
python setup.py

# This will:
# - Create virtual environment
# - Install dependencies  
# - Configure credentials
# - Set up directories
```

### 2. Configure Folder Monitoring
```bash
# Interactive folder selection
python main.py --mode=setup

# Choose which Google Drive folder to monitor
# Select whether to include subfolders
# Authenticate with Google (browser opens automatically)
```

### 3. Run
```bash
# Manual scan
python main.py --mode=scan

# Start daily monitoring
python scheduler.py --mode=schedule

# View statistics
python scheduler.py --mode=stats
```

## 🎯 What It Does

- **Monitors** your chosen Google Drive folder daily
- **Analyzes** new documents with GPT-4
- **Extracts** summaries, action items, and follow-ups
- **Creates** calendar events for important tasks
- **Sends** email summaries (optional)
- **Tracks** processed files to avoid duplicates

## 📁 Project Structure

```
agentic-rag-monitor/
├── main.py              # Core application
├── scheduler.py         # Daily scheduling system
├── setup.py            # Automated setup script
├── requirements.txt    # Python dependencies
├── .env.example       # Configuration template
├── README.md          # This file
└── (auto-generated files)
    ├── .env           # Your configuration
    ├── credentials.json   # Google API credentials
    ├── token.json        # Google OAuth token
    ├── folder_config.json # Folder selection
    ├── venv/            # Virtual environment
    ├── logs/            # Application logs
    ├── summaries/       # Daily reports
    └── chroma_db/       # Vector database
```

## 🔧 Prerequisites

- Python 3.9+
- Google Cloud account (Drive & Calendar APIs)
- OpenAI API account (GPT-4 access)

## 📝 Configuration

1. **Google APIs**: Enable Drive and Calendar APIs in Google Cloud Console
2. **Credentials**: Download OAuth 2.0 credentials JSON file
3. **OpenAI**: Get API key from OpenAI Platform
4. **Email** (optional): Configure SMTP settings for notifications

## 🚨 Troubleshooting

### Authentication Issues
```bash
rm token.json
python main.py --mode=setup
```

### Folder Not Found
```bash
rm folder_config.json  
python main.py --mode=setup
```

### Dependencies Issues
```bash
python setup.py --check
```

## 📧 Contact & Support

Check `drive_monitor.log` for detailed error messages and troubleshooting information.