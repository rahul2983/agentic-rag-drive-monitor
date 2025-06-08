#!/usr/bin/env python3
"""
Fixed folder listing approach for Google Drive API
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

def get_folder_list_alternative():
    """Alternative approach to get folder list"""
    
    # Load configuration
    load_dotenv()
    
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json')
    token_path = os.getenv('GOOGLE_TOKEN_PATH', './token.json')
    
    # Authenticate (reuse existing token)
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    
    print("🔍 Trying Alternative Folder Listing Methods")
    print("=" * 50)
    
    # Method 1: Simple files().list() with folder filter
    print("\n📁 Method 1: Simple folder query")
    try:
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed = False",
            pageSize=20,
            fields="files(id, name)",
            orderBy="name"
        ).execute()
        
        folders = results.get('files', [])
        print(f"Found {len(folders)} folders:")
        
        for i, folder in enumerate(folders[:10]):
            print(f"  {i+1}. '{folder.get('name', 'NO NAME')}' (ID: {folder.get('id', 'NO ID')[:20]}...)")
    
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Get all files and filter for folders
    print("\n📁 Method 2: Get all files, filter folders")
    try:
        results = drive_service.files().list(
            pageSize=100,
            fields="files(id, name, mimeType)",
            orderBy="name"
        ).execute()
        
        all_files = results.get('files', [])
        folders = [f for f in all_files if f.get('mimeType') == 'application/vnd.google-apps.folder']
        
        print(f"Found {len(folders)} folders from {len(all_files)} total files:")
        
        for i, folder in enumerate(folders[:10]):
            print(f"  {i+1}. '{folder.get('name', 'NO NAME')}' (ID: {folder.get('id', 'NO ID')[:20]}...)")
    
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Method 3: Individual folder lookups
    print("\n📁 Method 3: Individual folder details")
    try:
        # Get folder list first
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed = False",
            pageSize=10,
            fields="files(id)"
        ).execute()
        
        folder_ids = [f['id'] for f in results.get('files', [])]
        print(f"Got {len(folder_ids)} folder IDs, looking up details...")
        
        for i, folder_id in enumerate(folder_ids[:5]):
            try:
                folder_detail = drive_service.files().get(
                    fileId=folder_id,
                    fields="id, name, parents"
                ).execute()
                
                folder_name = folder_detail.get('name', 'NO NAME')
                print(f"  {i+1}. '{folder_name}' (ID: {folder_id[:20]}...)")
                
            except Exception as e:
                print(f"  {i+1}. Error getting folder {folder_id[:20]}...: {e}")
    
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    # Method 4: Search by specific queries
    print("\n📁 Method 4: Search with different queries")
    
    # Different query approaches
    queries = [
        "mimeType='application/vnd.google-apps.folder'",
        "mimeType contains 'folder'",
        "parents in 'root'",  # Only root-level folders
    ]
    
    for query in queries:
        try:
            print(f"\nTrying query: {query}")
            results = drive_service.files().list(
                q=query,
                pageSize=10,
                fields="files(id, name, parents)"
            ).execute()
            
            folders = results.get('files', [])
            print(f"  Found {len(folders)} items")
            
            for i, folder in enumerate(folders[:3]):
                print(f"    {i+1}. '{folder.get('name', 'NO NAME')}' (Type: {folder.get('mimeType', 'unknown')})")
                
        except Exception as e:
            print(f"  Query failed: {e}")

if __name__ == "__main__":
    get_folder_list_alternative()