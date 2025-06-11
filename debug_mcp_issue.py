#!/usr/bin/env python3
"""
Debug MCP issue and create a working alternative
"""

import asyncio
import os
import sys
from pathlib import Path

def check_mcp_version():
    """Check MCP version and imports"""
    try:
        import mcp
        print(f"✅ MCP version: {mcp.__version__ if hasattr(mcp, '__version__') else 'unknown'}")
        
        from mcp.types import ListToolsResult, Tool
        print("✅ MCP types imported successfully")
        
        # Test creating a ListToolsResult
        tools = [
            Tool(
                name="test_tool",
                description="Test tool",
                inputSchema={"type": "object", "properties": {}, "required": []}
            )
        ]
        
        result = ListToolsResult(tools=tools)
        print(f"✅ ListToolsResult created: {type(result)}")
        print(f"   Tools count: {len(result.tools)}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP issue: {e}")
        return False

def create_simple_working_server():
    """Create a very simple MCP server to test the basic functionality"""
    content = '''#!/usr/bin/env python3
"""
Ultra-simple MCP server for testing
"""

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolRequest, CallToolResult, ListToolsResult

class SimpleTestServer:
    def __init__(self):
        self.server = Server("simple-test")
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools():
            # Try the most basic approach possible
            tools = [
                Tool(
                    name="ping",
                    description="Simple ping test",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
            
            # Debug: Print what we're trying to return
            print(f"DEBUG: Creating ListToolsResult with {len(tools)} tools", file=sys.stderr)
            print(f"DEBUG: Tool types: {[type(t) for t in tools]}", file=sys.stderr)
            
            result = ListToolsResult(tools=tools)
            print(f"DEBUG: ListToolsResult type: {type(result)}", file=sys.stderr)
            print(f"DEBUG: ListToolsResult.__dict__: {result.__dict__}", file=sys.stderr)
            
            return result
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest):
            if request.name == "ping":
                return CallToolResult(
                    content=[TextContent(type="text", text="pong")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")],
                    isError=True
                )

async def main():
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    server = SimpleTestServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    return content

def create_alternative_approach():
    """Create an alternative non-MCP approach that works"""
    content = '''#!/usr/bin/env python3
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
            print("\\n🎉 All components working! You can use the direct approach:")
            print("   python direct_monitor.py")
            
            # Run a test scan
            await monitor.run_scan()
        else:
            print("\\n❌ Some components failed. Check your setup.")
    
    except Exception as e:
        print(f"\\n❌ Setup error: {e}")
        print("\\nMake sure you have:")
        print("1. OPENAI_API_KEY in your .env file")
        print("2. Google credentials.json file")
        print("3. All dependencies installed")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    return content

def main():
    """Main diagnostic and fix function"""
    print("🔍 Diagnosing MCP Issue")
    print("=" * 40)
    
    # Check MCP installation
    if not check_mcp_version():
        print("\\n❌ MCP installation has issues")
        return
    
    # Create test files
    print("\\n📝 Creating diagnostic files...")
    
    # Create simple test server
    with open("simple_test_server.py", "w") as f:
        f.write(create_simple_working_server())
    print("✅ Created simple_test_server.py")
    
    # Create direct alternative
    with open("direct_monitor.py", "w") as f:
        f.write(create_alternative_approach())
    print("✅ Created direct_monitor.py")
    
    print("\\n🔧 Next steps:")
    print("1. Test the simple server:")
    print("   python simple_test_server.py")
    print("\\n2. Or skip MCP entirely and use:")
    print("   python direct_monitor.py")
    print("\\n3. The direct approach will work without MCP complexity")

if __name__ == "__main__":
    main()