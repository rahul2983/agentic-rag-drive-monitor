#!/usr/bin/env python3
"""
Clean up duplicate calendar events created by the Drive Monitor
"""

import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

def cleanup_calendar_events():
    """Remove events created by the Agentic RAG Drive Monitor"""
    
    # Load configuration
    load_dotenv()
    
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json')
    token_path = os.getenv('GOOGLE_TOKEN_PATH', './token.json')
    
    # Authenticate
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    calendar_service = build('calendar', 'v3', credentials=creds)
    
    print("🔍 Looking for Drive Monitor calendar events...")
    
    # Get today's events
    now = datetime.utcnow()
    time_min = (now - timedelta(days=1)).isoformat() + 'Z'
    time_max = (now + timedelta(days=30)).isoformat() + 'Z'
    
    try:
        events_result = calendar_service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Find events created by our system
        monitor_events = []
        for event in events:
            summary = event.get('summary', '')
            description = event.get('description', '')
            
            # Identify our events by summary or description
            if (summary.startswith('Action:') or 
                summary.startswith('📋') or
                'Agentic RAG Drive Monitor' in description):
                monitor_events.append(event)
        
        if not monitor_events:
            print("✅ No Drive Monitor events found to clean up")
            return
        
        print(f"📋 Found {len(monitor_events)} Drive Monitor events")
        
        # Ask for confirmation
        print("\nEvents to be deleted:")
        for i, event in enumerate(monitor_events[:10]):  # Show first 10
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            print(f"  {i+1}. {event.get('summary', 'No title')} - {start_time}")
        
        if len(monitor_events) > 10:
            print(f"  ... and {len(monitor_events) - 10} more")
        
        confirm = input(f"\n❓ Delete all {len(monitor_events)} events? (y/n): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            deleted_count = 0
            for event in monitor_events:
                try:
                    calendar_service.events().delete(
                        calendarId='primary',
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1
                    
                    if deleted_count % 10 == 0:
                        print(f"🗑️  Deleted {deleted_count}/{len(monitor_events)} events...")
                        
                except Exception as e:
                    print(f"❌ Error deleting event {event.get('summary', 'unknown')}: {e}")
            
            print(f"✅ Successfully deleted {deleted_count} calendar events")
        else:
            print("❌ Cleanup cancelled")
    
    except Exception as e:
        print(f"❌ Error accessing calendar: {e}")

if __name__ == "__main__":
    cleanup_calendar_events()