#!/usr/bin/env python3
"""
Agentic RAG Google Drive Monitor
A comprehensive system for monitoring Google Drive, analyzing documents,
extracting insights, and taking automated actions.
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Core dependencies
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# AI/ML dependencies
import openai
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Document processing
import docx
import PyPDF2
from openpyxl import load_workbook

# Scheduling and notifications
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class DocumentMetadata:
    """Metadata for tracked documents"""
    file_id: str
    name: str
    mime_type: str
    modified_time: str
    size: int
    content_summary: str = ""
    action_items: List[str] = None
    follow_ups: List[str] = None
    priority: str = "medium"
    
    def __post_init__(self):
        if self.action_items is None:
            self.action_items = []
        if self.follow_ups is None:
            self.follow_ups = []

@dataclass
class ActionItem:
    """Structured action item extracted from documents"""
    description: str
    due_date: Optional[str]
    priority: str
    source_document: str
    calendar_event_needed: bool = False
    calendar_event_id: Optional[str] = None

class GoogleDriveMonitor:
    """Core Google Drive monitoring and document processing"""
    
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.drive_service = None
        self.calendar_service = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('drive_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def authenticate_google_services(self):
        """Authenticate with Google Drive and Calendar APIs"""
        SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/calendar'
        ]
        
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = Flow.from_client_secrets_file(self.credentials_path, SCOPES)
                flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                
                auth_url, _ = flow.authorization_url(prompt='consent')
                print(f'Please visit this URL to authorize the application: {auth_url}')
                
                code = input('Enter the authorization code: ')
                flow.fetch_token(code=code)
                creds = flow.credentials
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.drive_service = build('drive', 'v3', credentials=creds)
        self.calendar_service = build('calendar', 'v3', credentials=creds)
        self.logger.info("Google services authenticated successfully")
    
    def get_folder_id_by_name(self, folder_name: str) -> Optional[str]:
        """Get folder ID by folder name"""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed = False"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                self.logger.info(f"Found folder '{folder_name}' with ID: {folders[0]['id']}")
                return folders[0]['id']
            else:
                self.logger.warning(f"Folder '{folder_name}' not found")
                return None
                
        except HttpError as error:
            self.logger.error(f"Error finding folder: {error}")
            return None
    
    def list_available_folders(self) -> List[Dict[str, str]]:
        """List all available folders for user selection"""
        try:
            query = "mimeType='application/vnd.google-apps.folder' and trashed = False"
            
            results = self.drive_service.files().list(
                q=query,
                pageSize=50,
                fields="files(id, name, parents)",
                orderBy="name"
            ).execute()
            
            folders = results.get('files', [])
            self.logger.info(f"Found {len(folders)} folders")
            
            return [{"id": folder["id"], "name": folder["name"]} for folder in folders]
            
        except HttpError as error:
            self.logger.error(f"Error listing folders: {error}")
            return []
    
    def get_recent_files(self, hours_back: int = 24, folder_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve files modified in the last N hours from a specific folder"""
        try:
            # Calculate time threshold
            time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
            time_str = time_threshold.isoformat() + 'Z'
            
            # Build query for specific folder or all files
            if folder_id:
                query = f"'{folder_id}' in parents and modifiedTime >= '{time_str}' and trashed = False"
                self.logger.info(f"Scanning folder {folder_id} for files modified in the last {hours_back} hours")
            else:
                query = f"modifiedTime >= '{time_str}' and trashed = False"
                self.logger.info(f"Scanning all Drive files modified in the last {hours_back} hours")
            
            results = self.drive_service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            self.logger.info(f"Found {len(files)} files modified in the last {hours_back} hours")
            
            return files
            
        except HttpError as error:
            self.logger.error(f"An error occurred: {error}")
            return []
    
    def get_files_in_folder_recursive(self, folder_id: str, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get all files in folder and subfolders modified in the last N hours"""
        try:
            all_files = []
            
            # Get direct files in folder
            direct_files = self.get_recent_files(hours_back, folder_id)
            all_files.extend(direct_files)
            
            # Get subfolders
            subfolder_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed = False"
            
            results = self.drive_service.files().list(
                q=subfolder_query,
                fields="files(id, name)"
            ).execute()
            
            subfolders = results.get('files', [])
            
            # Recursively get files from subfolders
            for subfolder in subfolders:
                subfolder_files = self.get_files_in_folder_recursive(subfolder['id'], hours_back)
                all_files.extend(subfolder_files)
            
            return all_files
            
        except HttpError as error:
            self.logger.error(f"Error getting files from folder recursively: {error}")
            return []
    
    def download_file_content(self, file_id: str, mime_type: str) -> str:
        """Download and extract text content from various file types"""
        try:
            if 'google-apps' in mime_type:
                # Handle Google Workspace files
                if 'document' in mime_type:
                    export_mime = 'text/plain'
                elif 'spreadsheet' in mime_type:
                    export_mime = 'text/csv'
                elif 'presentation' in mime_type:
                    export_mime = 'text/plain'
                else:
                    return "Unsupported Google Workspace file type"
                
                request = self.drive_service.files().export_media(
                    fileId=file_id, mimeType=export_mime
                )
            else:
                # Handle regular files
                request = self.drive_service.files().get_media(fileId=file_id)
            
            content = request.execute()
            
            # Decode content based on file type
            if isinstance(content, bytes):
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    return content.decode('utf-8', errors='ignore')
            else:
                return str(content)
                
        except HttpError as error:
            self.logger.error(f"Error downloading file {file_id}: {error}")
            return f"Error downloading file: {error}"

class DocumentAnalyzer:
    """AI-powered document analysis and insight extraction"""
    
    def __init__(self, openai_api_key: str):
        import openai
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.setup_vector_store()
        
    def setup_vector_store(self):
        """Initialize ChromaDB for document embeddings"""
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db"
        ))
        
        try:
            self.collection = self.chroma_client.get_collection("documents")
        except:
            self.collection = self.chroma_client.create_collection("documents")
    
    async def analyze_document(self, content: str, metadata: DocumentMetadata) -> DocumentMetadata:
        """Analyze document content and extract insights"""
        
        # Generate summary
        summary = await self.generate_summary(content)
        metadata.content_summary = summary
        
        # Extract action items and follow-ups
        actions_and_followups = await self.extract_action_items(content)
        metadata.action_items = actions_and_followups.get('action_items', [])
        metadata.follow_ups = actions_and_followups.get('follow_ups', [])
        
        # Determine priority
        metadata.priority = await self.assess_priority(content, summary)
        
        # Store in vector database
        self.store_document_embedding(content, metadata)
        
        return metadata
    
    async def generate_summary(self, content: str) -> str:
        """Generate AI summary of document content"""
        try:
            prompt = f"""
            Please provide a concise summary of the following document content.
            Focus on key points, decisions, and important information:
            
            {content[:4000]}  # Limit content to avoid token limits
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return "Summary generation failed"
    
    async def extract_action_items(self, content: str) -> Dict[str, List[str]]:
        """Extract action items and follow-ups from document content"""
        try:
            prompt = f"""
            Analyze the following document and extract:
            1. Action items (specific tasks that need to be completed)
            2. Follow-ups (items that need monitoring or future attention)
            
            Format your response as JSON with keys 'action_items' and 'follow_ups', 
            each containing a list of strings.
            
            Document content:
            {content[:4000]}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback: extract manually
                return {
                    'action_items': [],
                    'follow_ups': []
                }
                
        except Exception as e:
            logging.error(f"Error extracting action items: {e}")
            return {'action_items': [], 'follow_ups': []}
    
    async def assess_priority(self, content: str, summary: str) -> str:
        """Assess document priority based on content analysis"""
        try:
            prompt = f"""
            Based on the document content and summary below, assess the priority level.
            Respond with only one word: 'high', 'medium', or 'low'
            
            Consider factors like:
            - Deadlines mentioned
            - Urgency indicators
            - Decision requirements
            - Stakeholder importance
            
            Summary: {summary}
            Content: {content[:2000]}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            priority = response.choices[0].message.content.strip().lower()
            return priority if priority in ['high', 'medium', 'low'] else 'medium'
            
        except Exception as e:
            logging.error(f"Error assessing priority: {e}")
            return 'medium'
    
    def store_document_embedding(self, content: str, metadata: DocumentMetadata):
        """Store document embedding in vector database"""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content)
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=[embedding.tolist()],
                documents=[content[:1000]],  # Store first 1000 chars
                metadatas=[asdict(metadata)],
                ids=[metadata.file_id]
            )
            
        except Exception as e:
            logging.error(f"Error storing embedding: {e}")

class CalendarManager:
    """Manage calendar events and scheduling"""
    
    def __init__(self, calendar_service):
        self.calendar_service = calendar_service
        self.logger = logging.getLogger(__name__)
    
    async def create_calendar_event(self, action_item: ActionItem) -> Optional[str]:
        """Create calendar event for action item"""
        try:
            # Parse due date or set default
            if action_item.due_date:
                try:
                    due_date = datetime.fromisoformat(action_item.due_date)
                except:
                    due_date = datetime.now() + timedelta(days=1)
            else:
                due_date = datetime.now() + timedelta(days=1)
            
            # Create event
            event = {
                'summary': f"Action: {action_item.description}",
                'description': f"Source: {action_item.source_document}\nPriority: {action_item.priority}",
                'start': {
                    'dateTime': due_date.isoformat(),
                    'timeZone': 'America/New_York',  # Adjust as needed
                },
                'end': {
                    'dateTime': (due_date + timedelta(hours=1)).isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60}        # 1 hour before
                    ]
                }
            }
            
            created_event = self.calendar_service.events().insert(
                calendarId='primary', body=event
            ).execute()
            
            self.logger.info(f"Created calendar event: {created_event['id']}")
            return created_event['id']
            
        except Exception as e:
            self.logger.error(f"Error creating calendar event: {e}")
            return None

class AgenticRAGApplication:
    """Main Agentic RAG application orchestrator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.drive_monitor = GoogleDriveMonitor(
            config['google_credentials_path'],
            config['google_token_path']
        )
        self.doc_analyzer = DocumentAnalyzer(config['openai_api_key'])
        self.logger = logging.getLogger(__name__)
        
        # Folder monitoring configuration
        self.target_folder_id = config.get('target_folder_id')
        self.target_folder_name = config.get('target_folder_name')
        self.include_subfolders = config.get('include_subfolders', True)
        
        # State tracking
        self.processed_files = set()
        self.load_state()
    
    def setup_folder_monitoring(self):
        """Interactive setup for folder monitoring"""
        self.drive_monitor.authenticate_google_services()
        
        if not self.target_folder_id and not self.target_folder_name:
            print("\n🔍 Setting up folder monitoring...")
            print("Choose an option:")
            print("1. Monitor a specific folder")
            print("2. Monitor entire Google Drive")
            
            choice = input("Enter your choice (1 or 2): ").strip()
            
            if choice == "1":
                self.select_target_folder()
            else:
                print("✅ Monitoring entire Google Drive")
                self.target_folder_id = None
                self.target_folder_name = None
        
        elif self.target_folder_name and not self.target_folder_id:
            # Find folder by name
            print(f"🔍 Looking for folder: {self.target_folder_name}")
            self.target_folder_id = self.drive_monitor.get_folder_id_by_name(self.target_folder_name)
            
            if not self.target_folder_id:
                print(f"❌ Folder '{self.target_folder_name}' not found. Please select a different folder.")
                self.select_target_folder()
    
    def select_target_folder(self):
        """Interactive folder selection"""
        print("\n📁 Available folders in your Google Drive:")
        folders = self.drive_monitor.list_available_folders()
        
        if not folders:
            print("❌ No folders found in your Google Drive")
            return
        
        # Display folders with numbers
        for i, folder in enumerate(folders, 1):
            print(f"{i:2d}. {folder['name']}")
        
        print(f"{len(folders) + 1:2d}. Monitor entire Google Drive")
        
        while True:
            try:
                choice = input(f"\nSelect folder (1-{len(folders) + 1}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(folders):
                    selected_folder = folders[choice_num - 1]
                    self.target_folder_id = selected_folder['id']
                    self.target_folder_name = selected_folder['name']
                    
                    # Ask about subfolders
                    include_sub = input(f"Include subfolders? (y/n): ").strip().lower()
                    self.include_subfolders = include_sub in ['y', 'yes']
                    
                    print(f"✅ Selected folder: {self.target_folder_name}")
                    if self.include_subfolders:
                        print("✅ Including subfolders")
                    
                    # Save configuration
                    self.save_folder_config()
                    break
                    
                elif choice_num == len(folders) + 1:
                    self.target_folder_id = None
                    self.target_folder_name = None
                    print("✅ Monitoring entire Google Drive")
                    self.save_folder_config()
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def save_folder_config(self):
        """Save folder configuration to file"""
        config = {
            'target_folder_id': self.target_folder_id,
            'target_folder_name': self.target_folder_name,
            'include_subfolders': self.include_subfolders
        }
        
        with open('folder_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("💾 Folder configuration saved")
    
    def load_folder_config(self):
        """Load folder configuration from file"""
        config_file = Path('folder_config.json')
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.target_folder_id = config.get('target_folder_id')
                self.target_folder_name = config.get('target_folder_name')
                self.include_subfolders = config.get('include_subfolders', True)
                
                if self.target_folder_name:
                    print(f"📁 Loaded folder config: {self.target_folder_name}")
    
    async def run_daily_scan(self):
        """Main daily scanning and processing loop"""
        self.logger.info("Starting daily scan...")
        
        # Setup folder monitoring if not configured
        if not hasattr(self, 'target_folder_id'):
            self.load_folder_config()
        
        # Authenticate services
        self.drive_monitor.authenticate_google_services()
        
        # Initialize calendar manager
        calendar_manager = CalendarManager(self.drive_monitor.calendar_service)
        
        # Get recent files based on folder configuration
        if self.target_folder_id:
            if self.include_subfolders:
                recent_files = self.drive_monitor.get_files_in_folder_recursive(
                    self.target_folder_id, 24
                )
                self.logger.info(f"Scanning folder '{self.target_folder_name}' and subfolders")
            else:
                recent_files = self.drive_monitor.get_recent_files(24, self.target_folder_id)
                self.logger.info(f"Scanning folder '{self.target_folder_name}' only")
        else:
            recent_files = self.drive_monitor.get_recent_files(24)
            self.logger.info("Scanning entire Google Drive")
        
        # Process new files
        new_files = [f for f in recent_files if f['id'] not in self.processed_files]
        
        if not new_files:
            self.logger.info("No new files to process")
            return
        
        self.logger.info(f"Processing {len(new_files)} new files")
        
        processed_docs = []
        action_items = []
        
        for file_info in new_files:
            try:
                # Create metadata object
                metadata = DocumentMetadata(
                    file_id=file_info['id'],
                    name=file_info['name'],
                    mime_type=file_info['mimeType'],
                    modified_time=file_info['modifiedTime'],
                    size=file_info.get('size', 0)
                )
                
                # Download and analyze content
                content = self.drive_monitor.download_file_content(
                    file_info['id'], 
                    file_info['mimeType']
                )
                
                if content and len(content.strip()) > 50:  # Skip very small files
                    analyzed_metadata = await self.doc_analyzer.analyze_document(content, metadata)
                    processed_docs.append(analyzed_metadata)
                    
                    # Create action items for calendar
                    for action_desc in analyzed_metadata.action_items:
                        action_item = ActionItem(
                            description=action_desc,
                            due_date=None,  # Could extract from content
                            priority=analyzed_metadata.priority,
                            source_document=analyzed_metadata.name,
                            calendar_event_needed=True
                        )
                        action_items.append(action_item)
                
                # Mark as processed
                self.processed_files.add(file_info['id'])
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_info['name']}: {e}")
        
        # Create calendar events for action items
        for action_item in action_items:
            if action_item.calendar_event_needed:
                event_id = await calendar_manager.create_calendar_event(action_item)
                action_item.calendar_event_id = event_id
        
        # Generate daily summary
        await self.generate_daily_summary(processed_docs, action_items)
        
        # Save state
        self.save_state()
        
    def load_state(self):
        """Load previous state from disk"""
        state_file = Path('app_state.json')
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
                self.processed_files = set(state.get('processed_files', []))
    
    def save_state(self):
        """Save current state to disk"""
        state = {
            'processed_files': list(self.processed_files),
            'last_run': datetime.now().isoformat(),
            'target_folder_id': getattr(self, 'target_folder_id', None),
            'target_folder_name': getattr(self, 'target_folder_name', None)
        }
        with open('app_state.json', 'w') as f:
            json.dump(state, f, indent=2)
    
    async def generate_daily_summary(self, docs: List[DocumentMetadata], actions: List[ActionItem]):
        """Generate and save daily summary report"""
        try:
            summary_content = f"""
# Daily Google Drive Summary - {datetime.now().strftime('%Y-%m-%d')}

## New Documents Processed: {len(docs)}

"""
            
            for doc in docs:
                summary_content += f"""
### {doc.name}
- **Priority:** {doc.priority.upper()}
- **Summary:** {doc.content_summary}
- **Action Items:** {len(doc.action_items)}
- **Follow-ups:** {len(doc.follow_ups)}

"""
                
                if doc.action_items:
                    summary_content += "**Action Items:**\n"
                    for item in doc.action_items:
                        summary_content += f"- {item}\n"
                    summary_content += "\n"
                
                if doc.follow_ups:
                    summary_content += "**Follow-ups:**\n"
                    for item in doc.follow_ups:
                        summary_content += f"- {item}\n"
                    summary_content += "\n"
            
            summary_content += f"""
## Total Action Items Created: {len(actions)}

### High Priority Items:
"""
            
            high_priority_actions = [a for a in actions if a.priority == 'high']
            for action in high_priority_actions:
                summary_content += f"- {action.description} (from {action.source_document})\n"
            
            # Save summary to file
            summary_file = f"daily_summary_{datetime.now().strftime('%Y%m%d')}.md"
            with open(summary_file, 'w') as f:
                f.write(summary_content)
            
            self.logger.info(f"Daily summary saved to {summary_file}")
            
            # Optional: Send email notification
            if self.config.get('email_notifications'):
                await self.send_email_summary(summary_content)
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
    
    async def send_email_summary(self, summary_content: str):
        """Send email summary (optional feature)"""
        # Implementation would depend on your email setup
        pass

def main():
    """Main entry point with setup mode"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic RAG Drive Monitor")
    parser.add_argument('--mode', choices=['setup', 'scan', 'schedule'], 
                       default='scan', help='Run mode')
    
    args = parser.parse_args()
    
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'google_credentials_path': os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json'),
        'google_token_path': os.getenv('GOOGLE_TOKEN_PATH', './token.json'),
        'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
        'email_notifications': os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
        'target_folder_name': os.getenv('TARGET_FOLDER_NAME'),
        'include_subfolders': os.getenv('INCLUDE_SUBFOLDERS', 'true').lower() == 'true'
    }
    
    # Validate required config
    if not config['openai_api_key']:
        print("❌ OpenAI API key not found. Please run setup first:")
        print("   python setup.py")
        return
    
    if not Path(config['google_credentials_path']).exists():
        print("❌ Google credentials file not found. Please run setup first:")
        print("   python setup.py")
        return
    
    # Create and run application
    app = AgenticRAGApplication(config)
    
    if args.mode == 'setup':
        # Interactive setup mode
        print("🔧 Setting up Agentic RAG Drive Monitor...")
        print("This will help you select which folder to monitor.\n")
        
        app.setup_folder_monitoring()
        
        print("\n✅ Setup complete!")
        print("You can now run:")
        print("  python main.py --mode=scan      # Manual scan")
        print("  python scheduler.py --mode=schedule  # Start daily monitoring")
        
    elif args.mode == 'scan':
        # Run manual scan
        asyncio.run(app.run_daily_scan())
        
    elif args.mode == 'schedule':
        # Import and run scheduler
        from scheduler import AdvancedScheduler, ConfigManager
        
        config_obj = ConfigManager.load_config()
        scheduler = AdvancedScheduler(config_obj)
        scheduler.run_scheduler()

if __name__ == "__main__":
    main()