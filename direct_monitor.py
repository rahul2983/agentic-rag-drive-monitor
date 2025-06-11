#!/usr/bin/env python3
"""
Alternative: Direct Google Drive Monitor without MCP
This bypasses MCP entirely and works directly
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Import the main application directly
from main import AgenticRAGApplication

class DirectDriveMonitor:
    """Direct Drive Monitor without MCP complexity"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_config()
    
    def setup_config(self):
        """Setup configuration"""
        self.config = {
            'google_credentials_path': os.getenv('GOOGLE_CREDENTIALS_PATH', './credentials.json'),
            'google_token_path': os.getenv('GOOGLE_TOKEN_PATH', './token.json'),
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'email_notifications': os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
        }
        
        # Validate config
        if not self.config['openai_api_key']:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if not Path(self.config['google_credentials_path']).exists():
            raise ValueError(f"Google credentials file not found: {self.config['google_credentials_path']}")
    
    async def run_scan(self):
        """Run a direct scan without MCP"""
        self.logger.info("🚀 Starting Direct Drive Monitor (no MCP)")
        
        try:
            # Create the main application
            app = AgenticRAGApplication(self.config)
            
            # Run the scan directly
            await app.run_daily_scan()
            
            self.logger.info("✅ Direct scan completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Direct scan failed: {e}")
            raise
    
    async def test_components(self):
        """Test individual components"""
        self.logger.info("🧪 Testing individual components...")
        
        try:
            # Test 1: OpenAI API
            import openai
            client = openai.OpenAI(api_key=self.config['openai_api_key'])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test successful'"}],
                max_tokens=10
            )
            self.logger.info("✅ OpenAI API test successful")
            
            # Test 2: Google APIs import
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            self.logger.info("✅ Google API imports successful")
            
            # Test 3: Document processing
            import pandas as pd
            import numpy as np
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.logger.info("✅ Document processing libraries available")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Component test failed: {e}")
            return False

async def main():
    """Main entry point for direct approach"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        monitor = DirectDriveMonitor()
        
        # Test components first
        if await monitor.test_components():
            print("\n🎉 All components working! You can use the direct approach:")
            print("   python direct_monitor.py")
            
            # Run a test scan
            await monitor.run_scan()
        else:
            print("\n❌ Some components failed. Check your setup.")
    
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        print("\nMake sure you have:")
        print("1. OPENAI_API_KEY in your .env file")
        print("2. Google credentials.json file")
        print("3. All dependencies installed")

if __name__ == "__main__":
    asyncio.run(main())
