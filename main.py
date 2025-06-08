#!/usr/bin/env python3
"""
Agentic RAG Google Drive Monitor - Simplified Version
Compatible with Python 3.13 without heavy ML dependencies
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

# Core dependencies
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# AI dependencies
import openai

# Document processing
import docx
import PyPDF2
from openpyxl import load_workbook

# Scheduling and notifications
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Simple text processing
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle

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
        """List all available folders for user selection - Working Method 3 approach"""
        try:
            self.logger.info("Using individual folder lookup method (Method 3)")
            
            # First, get all folder IDs without names
            results = self.drive_service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed = False",
                pageSize=100,  # Get more folders
                fields="files(id)"
            ).execute()
            
            folder_ids = [f['id'] for f in results.get('files', [])]
            self.logger.info(f"Found {len(folder_ids)} folder IDs, looking up individual details...")
            
            valid_folders = []
            
            # Look up each folder individually to get the real name
            for i, folder_id in enumerate(folder_ids):
                try:
                    folder_detail = self.drive_service.files().get(
                        fileId=folder_id,
                        fields="id, name, parents"
                    ).execute()
                    
                    folder_name = folder_detail.get('name', '')
                    
                    # Only include folders with valid names
                    if folder_name and folder_name != '0' and len(folder_name.strip()) > 0:
                        valid_folders.append({
                            "id": folder_id, 
                            "name": folder_name.strip()
                        })
                        self.logger.debug(f"Found folder: {folder_name}")
                    else:
                        self.logger.debug(f"Skipped folder with invalid name: '{folder_name}'")
                        
                except Exception as e:
                    self.logger.warning(f"Could not get details for folder {folder_id[:10]}...: {e}")
                    continue
            
            # Sort folders alphabetically by name
            valid_folders.sort(key=lambda x: x['name'].lower())
            
            self.logger.info(f"Successfully retrieved {len(valid_folders)} valid folders")
            return valid_folders
            
        except HttpError as error:
            self.logger.error(f"Error listing folders: {error}")
            return []
    
    def list_folders_alternative(self) -> List[Dict[str, str]]:
        """Alternative method - not needed anymore, but keeping as backup"""
        try:
            # This method is now redundant since we fixed the main method
            return []
            
        except Exception as e:
            self.logger.error(f"Alternative folder listing failed: {e}")
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

class SimpleDocumentAnalyzer:
    """Simplified document analysis without heavy ML dependencies"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.setup_simple_storage()
        
    def setup_simple_storage(self):
        """Initialize simple file-based storage instead of vector DB"""
        self.storage_dir = Path("./simple_db")
        self.storage_dir.mkdir(exist_ok=True)
        self.documents_file = self.storage_dir / "documents.json"
        
        # Load existing documents
        if self.documents_file.exists():
            with open(self.documents_file, 'r') as f:
                self.stored_documents = json.load(f)
        else:
            self.stored_documents = {}
    
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
        
        # Store in simple storage
        self.store_document_simple(content, metadata)
        
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
    
    def store_document_simple(self, content: str, metadata: DocumentMetadata):
        """Store document in simple file-based storage"""
        try:
            # Create document hash for unique identification
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            document_entry = {
                "metadata": asdict(metadata),
                "content_preview": content[:500],  # Store first 500 chars
                "content_hash": content_hash,
                "stored_at": datetime.now().isoformat()
            }
            
            self.stored_documents[metadata.file_id] = document_entry
            
            # Save to file
            with open(self.documents_file, 'w') as f:
                json.dump(self.stored_documents, f, indent=2)
            
        except Exception as e:
            logging.error(f"Error storing document: {e}")

class CalendarManager:
    """Manage calendar events and scheduling"""
    
    def __init__(self, calendar_service):
        self.calendar_service = calendar_service
        self.logger = logging.getLogger(__name__)
        self.scheduled_times = []  # Track scheduled times to avoid conflicts
    
    def parse_due_date_from_description(self, description: str) -> Optional[datetime]:
        """Extract due date from action item description"""
        import re
        
        # Common date patterns
        date_patterns = [
            r'by\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s+\d{4})?)',  # "by December 20th, 2024"
            r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s+\d{4})?)',       # "December 20th, 2024"
            r'(\d{1,2}/\d{1,2}/\d{4})',                             # "12/20/2024"
            r'(\d{4}-\d{2}-\d{2})',                                 # "2024-12-20"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try to parse various date formats
                    from dateutil import parser
                    parsed_date = parser.parse(date_str, fuzzy=True)
                    
                    # If no year specified, assume current year or next year if date has passed
                    if parsed_date.year == 1900:  # Default year from parser
                        current_year = datetime.now().year
                        parsed_date = parsed_date.replace(year=current_year)
                        
                        # If the date is in the past, move to next year
                        if parsed_date < datetime.now():
                            parsed_date = parsed_date.replace(year=current_year + 1)
                    
                    return parsed_date
                except:
                    continue
        
        return None
    
    def get_next_available_slot(self, preferred_date: datetime, priority: str) -> datetime:
        """Get next available time slot, avoiding conflicts"""
        
        # Priority-based time slots
        if priority == "high":
            # High priority: Morning slots (9 AM - 12 PM)
            base_hours = [9, 10, 11]
        elif priority == "medium":
            # Medium priority: Afternoon slots (1 PM - 4 PM)
            base_hours = [13, 14, 15]
        else:
            # Low priority: End of day slots (4 PM - 6 PM)
            base_hours = [16, 17]
        
        # Start from preferred date
        current_date = preferred_date.replace(hour=base_hours[0], minute=0, second=0, microsecond=0)
        
        # Try to find an available slot within 14 days
        for day_offset in range(14):
            check_date = current_date + timedelta(days=day_offset)
            
            # Skip weekends for work-related tasks
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            # Try each hour slot for this priority level
            for hour in base_hours:
                candidate_time = check_date.replace(hour=hour)
                
                # Check if this slot is already taken (within 30 minutes)
                is_available = True
                for scheduled_time in self.scheduled_times:
                    time_diff = abs((candidate_time - scheduled_time).total_seconds())
                    if time_diff < 1800:  # 30 minutes = 1800 seconds
                        is_available = False
                        break
                
                if is_available:
                    self.scheduled_times.append(candidate_time)
                    return candidate_time
        
        # If no slot found, just add to the end
        fallback_time = current_date + timedelta(days=len(self.scheduled_times) // 3)
        self.scheduled_times.append(fallback_time)
        return fallback_time
    
    def determine_event_duration(self, description: str, priority: str) -> int:
        """Determine event duration based on action type and priority"""
        
        # Keywords that suggest longer meetings
        long_meeting_keywords = [
            'meeting', 'presentation', 'review', 'discussion', 'training',
            'session', 'workshop', 'interview', 'negotiation'
        ]
        
        # Keywords that suggest shorter tasks
        short_task_keywords = [
            'submit', 'send', 'call', 'email', 'update', 'change',
            'check', 'verify', 'approve', 'sign'
        ]
        
        description_lower = description.lower()
        
        # Check for meeting-type activities
        if any(keyword in description_lower for keyword in long_meeting_keywords):
            return 2 if priority == "high" else 1  # 2 hours for high priority meetings, 1 for others
        
        # Check for quick tasks
        elif any(keyword in description_lower for keyword in short_task_keywords):
            return 1  # 30 minutes for quick tasks
        
        # Default duration based on priority
        elif priority == "high":
            return 1  # 1 hour for high priority items
        else:
            return 1  # 30 minutes for medium/low priority
    
    async def create_calendar_event(self, action_item: ActionItem) -> Optional[str]:
        """Create calendar event for action item with intelligent scheduling"""
        try:
            # Try to extract due date from description
            extracted_due_date = self.parse_due_date_from_description(action_item.description)
            
            # Determine the target date
            if extracted_due_date:
                # Schedule a few days before the due date for preparation
                if action_item.priority == "high":
                    target_date = extracted_due_date - timedelta(days=1)  # 1 day before for urgent items
                else:
                    target_date = extracted_due_date - timedelta(days=3)  # 3 days before for others
                
                # Don't schedule in the past
                if target_date < datetime.now():
                    target_date = datetime.now() + timedelta(days=1)
            else:
                # No specific due date found, schedule based on priority
                if action_item.priority == "high":
                    target_date = datetime.now() + timedelta(days=1)      # Tomorrow for high priority
                elif action_item.priority == "medium":
                    target_date = datetime.now() + timedelta(days=2)      # Day after tomorrow for medium
                else:
                    target_date = datetime.now() + timedelta(days=3)      # 3 days for low priority
            
            # Get next available time slot
            scheduled_time = self.get_next_available_slot(target_date, action_item.priority)
            
            # Determine event duration
            duration_hours = self.determine_event_duration(action_item.description, action_item.priority)
            
            # Create event with better formatting
            event_title = f"📋 {action_item.description[:50]}{'...' if len(action_item.description) > 50 else ''}"
            
            # Add priority emoji
            priority_emoji = {"high": "🚨", "medium": "⚠️", "low": "📝"}
            
            event_description = f"""{priority_emoji.get(action_item.priority, '📝')} Priority: {action_item.priority.upper()}

📄 Source: {action_item.source_document}

📋 Full Description: {action_item.description}

🤖 Auto-generated by Agentic RAG Drive Monitor"""
            
            # Handle due date display
            due_date_text = ""
            if extracted_due_date:
                due_date_text = f"\n⏰ Due Date: {extracted_due_date.strftime('%B %d, %Y')}"
                event_description += due_date_text
            
            event = {
                'summary': event_title,
                'description': event_description,
                'start': {
                    'dateTime': scheduled_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': (scheduled_time + timedelta(hours=duration_hours)).isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60 if action_item.priority == 'high' else 60},
                        {'method': 'popup', 'minutes': 15}
                    ]
                },
                'colorId': '11' if action_item.priority == 'high' else '5' if action_item.priority == 'medium' else '2'  # Red for high, yellow for medium, green for low
            }
            
            created_event = self.calendar_service.events().insert(
                calendarId='primary', body=event
            ).execute()
            
            self.logger.info(f"Created calendar event for {action_item.priority} priority: {action_item.description[:30]}... on {scheduled_time.strftime('%m/%d %H:%M')}")
            return created_event['id']
            
        except Exception as e:
            self.logger.error(f"Error creating calendar event: {e}")
            return None

class AgenticRAGApplication:
    """Main Agentic RAG application orchestrator - Simplified Version"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.drive_monitor = GoogleDriveMonitor(
            config['google_credentials_path'],
            config['google_token_path']
        )
        self.doc_analyzer = SimpleDocumentAnalyzer(config['openai_api_key'])
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
        
        # Debug: Print raw folder data
        print(f"Debug: Retrieved {len(folders)} folders")
        for i, folder in enumerate(folders[:3]):
            print(f"Debug folder {i}: {folder}")
        
        # Display folders with numbers
        for i, folder in enumerate(folders, 1):
            folder_name = folder.get('name', 'Unknown Folder')
            print(f"{i:2d}. {folder_name}")
        
        print(f"{len(folders) + 1:2d}. Monitor entire Google Drive")
        
        while True:
            try:
                choice = input(f"\nSelect folder (1-{len(folders) + 1}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(folders):
                    selected_folder = folders[choice_num - 1]
                    self.target_folder_id = selected_folder['id']
                    self.target_folder_name = selected_folder.get('name', 'Unknown Folder')
                    
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
        
        self.logger.info("Daily scan completed successfully")
    
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
    
    parser = argparse.ArgumentParser(description="Agentic RAG Drive Monitor - Simple Version")
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
        print("  python main-simple.py --mode=scan      # Manual scan")
        print("  python scheduler.py --mode=schedule  # Start daily monitoring")
        
    elif args.mode == 'scan':
        # Run manual scan
        asyncio.run(app.run_daily_scan())
        
    elif args.mode == 'schedule':
        # Import and run scheduler
        try:
            from scheduler import AdvancedScheduler, ConfigManager
            
            config_obj = ConfigManager.load_config()
            scheduler = AdvancedScheduler(config_obj)
            scheduler.run_scheduler()
        except ImportError:
            print("❌ Scheduler module not found or has dependency issues")
            print("   Running in simple scan mode instead...")
            asyncio.run(app.run_daily_scan())

if __name__ == "__main__":
    main()