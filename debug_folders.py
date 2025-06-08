#!/usr/bin/env python3
"""
Debug script to check Google Drive folder access and permissions
"""

import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

def debug_drive_access():
    """Debug Google Drive access and folder listing"""
    
    # Load configuration
    load_dotenv()
    
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json')
    token_path = os.getenv('GOOGLE_TOKEN_PATH', './token.json')
    
    print("🔍 Debugging Google Drive Access")
    print("=" * 50)
    
    # Check files exist
    if not Path(credentials_path).exists():
        print(f"❌ Credentials file not found: {credentials_path}")
        return
    
    if not Path(token_path).exists():
        print(f"⚠️  Token file not found: {token_path}")
        print("   This is normal for first run - will be created after authentication")
    
    # Authenticate
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(credentials_path, SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f'Please visit this URL to authorize the application: {auth_url}')
            
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    # Build service
    drive_service = build('drive', 'v3', credentials=creds)
    
    print("✅ Authentication successful")
    
    # Test basic Drive access
    try:
        print("\n📊 Testing basic Drive access...")
        
        # Get user info
        about = drive_service.about().get(fields="user").execute()
        user = about.get('user', {})
        print(f"   Authenticated as: {user.get('displayName', 'Unknown')} ({user.get('emailAddress', 'Unknown')})")
        
        # Test simple file list
        print("\n📄 Testing file listing (first 5 files)...")
        files_result = drive_service.files().list(
            pageSize=5,
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = files_result.get('files', [])
        print(f"   Found {len(files)} files")
        
        for i, file in enumerate(files):
            print(f"   {i+1}. {file.get('name', 'NO NAME')} ({file.get('mimeType', 'unknown type')})")
        
        # Test folder listing with detailed fields
        print("\n📁 Testing folder listing (detailed)...")
        folders_result = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed = False",
            pageSize=10,
            fields="files(id, name, parents, owners, permissions)",
            orderBy="name"
        ).execute()
        
        folders = folders_result.get('files', [])
        print(f"   Found {len(folders)} folders")
        
        if folders:
            print("\n📋 First 5 folders (detailed):")
            for i, folder in enumerate(folders[:5]):
                folder_name = folder.get('name', '**NO NAME FIELD**')
                folder_id = folder.get('id', '**NO ID**')
                parents = folder.get('parents', [])
                
                print(f"   {i+1}. Name: '{folder_name}'")
                print(f"      ID: {folder_id}")
                print(f"      Parents: {parents}")
                print(f"      Raw data: {folder}")
                print()
        else:
            print("   ❌ No folders found!")
        
        # Check permissions
        print("\n🔒 Checking API permissions...")
        try:
            # Try to access a specific folder
            if folders:
                test_folder = folders[0]
                folder_details = drive_service.files().get(
                    fileId=test_folder['id'],
                    fields="id, name, parents, owners, permissions"
                ).execute()
                print(f"   ✅ Can access folder details: {folder_details.get('name', 'NO NAME')}")
            else:
                print("   ⚠️  No folders to test permissions with")
                
        except HttpError as e:
            print(f"   ❌ Permission error: {e}")
    
    except HttpError as error:
        print(f"❌ API Error: {error}")
        
        if "insufficient authentication scopes" in str(error):
            print("\n🔧 Fix: Delete token.json and re-authenticate with proper scopes")
            print("   rm token.json")
            print("   python3 debug_folders.py")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    debug_drive_access()