#!/usr/bin/env python3
"""
Create properly working MCP servers with correct initialization
"""

import os
from pathlib import Path

def create_working_google_drive_server():
    """Create properly working Google Drive server"""
    content = '''#!/usr/bin/env python3
"""
Working Google Drive Server with proper initialization
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent,
    CallToolRequest, CallToolResult, 
    ListToolsRequest, ListToolsResult
)

class GoogleDriveServer:
    def __init__(self):
        self.server = Server("google-drive")
        self.logger = logging.getLogger(__name__)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return tools for Google Drive operations"""
            tools = [
                Tool(
                    name="authenticate",
                    description="Authenticate with Google Drive API",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                Tool(
                    name="get_recent_files", 
                    description="Get files modified in the last N hours",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "hours_back": {"type": "integer", "description": "Hours to look back", "default": 24}
                        },
                        "required": []
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "authenticate":
                    return await self._authenticate()
                elif request.name == "get_recent_files":
                    hours_back = request.arguments.get("hours_back", 24) if request.arguments else 24
                    return await self._get_recent_files(hours_back)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _authenticate(self) -> CallToolResult:
        """Simulate Google Drive authentication"""
        result = {
            "status": "authenticated",
            "message": "Google Drive authentication successful (demo mode)",
            "timestamp": datetime.now().isoformat()
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_recent_files(self, hours_back: int) -> CallToolResult:
        """Simulate getting recent files"""
        result = {
            "files": [
                {
                    "id": "demo_file_1",
                    "name": "Sample Document.docx",
                    "modified_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                }
            ],
            "hours_back": hours_back,
            "count": 1,
            "message": "Demo mode - returning sample file"
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = GoogleDriveServer()
    
    # Proper initialization with all required parameters
    initialization_options = InitializationOptions(
        server_name="google-drive",
        server_version="1.0.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            initialization_options  # This was missing!
        )

if __name__ == "__main__":
    asyncio.run(main())
'''
    return content

def create_working_ai_analysis_server():
    """Create properly working AI Analysis server"""
    content = '''#!/usr/bin/env python3
"""
Working AI Analysis Server with proper initialization
"""

import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent,
    CallToolRequest, CallToolResult, 
    ListToolsRequest, ListToolsResult
)

# Optional: Import OpenAI if available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIAnalysisServer:
    def __init__(self):
        self.server = Server("ai-analysis")
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
        
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return tools for AI analysis operations"""
            tools = [
                Tool(
                    name="analyze_document",
                    description="Perform AI analysis of document content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Document content to analyze"},
                            "document_name": {"type": "string", "description": "Name of the document"}
                        },
                        "required": ["content", "document_name"]
                    }
                ),
                Tool(
                    name="generate_summary",
                    description="Generate a summary of document content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Content to summarize"},
                            "max_length": {"type": "integer", "description": "Maximum summary length", "default": 150}
                        },
                        "required": ["content"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "analyze_document":
                    return await self._analyze_document(request.arguments)
                elif request.name == "generate_summary":
                    return await self._generate_summary(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _analyze_document(self, args) -> CallToolResult:
        """Analyze a document"""
        content = args.get("content", "")
        document_name = args.get("document_name", "Unknown Document")
        
        # Basic analysis (can be enhanced with real AI)
        word_count = len(content.split())
        char_count = len(content)
        
        result = {
            "document_name": document_name,
            "analysis": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_reading_time": f"{max(1, word_count // 200)} minutes"
            },
            "summary": f"Document '{document_name}' contains {word_count} words",
            "action_items": ["Review document content", "Extract key points"],
            "priority": "medium" if word_count > 500 else "low",
            "analyzed_at": datetime.now().isoformat(),
            "ai_available": self.openai_client is not None
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _generate_summary(self, args) -> CallToolResult:
        """Generate a summary"""
        content = args.get("content", "")
        max_length = args.get("max_length", 150)
        
        if self.openai_client:
            try:
                # Use real AI if available
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": f"Summarize this in {max_length} words or less: {content[:2000]}"}
                    ],
                    max_tokens=max_length,
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
                method = "OpenAI GPT-3.5"
            except Exception as e:
                # Fallback to simple summary
                summary = f"Summary of {len(content.split())} word document: {content[:max_length]}..."
                method = f"Fallback (OpenAI error: {str(e)})"
        else:
            # Simple extractive summary
            sentences = content.split('. ')
            summary = '. '.join(sentences[:3]) + "..." if len(sentences) > 3 else content
            method = "Simple extractive"
        
        result = {
            "summary": summary,
            "method": method,
            "word_count": len(summary.split()),
            "original_length": len(content.split()),
            "compression_ratio": f"{len(summary.split()) / max(1, len(content.split())):.2f}"
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = AIAnalysisServer()
    
    # Proper initialization
    initialization_options = InitializationOptions(
        server_name="ai-analysis",
        server_version="1.0.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            initialization_options
        )

if __name__ == "__main__":
    asyncio.run(main())
'''
    return content

def create_working_calendar_server():
    """Create properly working Calendar server"""
    content = '''#!/usr/bin/env python3
"""
Working Google Calendar Server with proper initialization
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent,
    CallToolRequest, CallToolResult, 
    ListToolsRequest, ListToolsResult
)

class GoogleCalendarServer:
    def __init__(self):
        self.server = Server("google-calendar")
        self.logger = logging.getLogger(__name__)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return tools for Google Calendar operations"""
            tools = [
                Tool(
                    name="authenticate",
                    description="Authenticate with Google Calendar API",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                ),
                Tool(
                    name="create_event",
                    description="Create a calendar event",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Event title"},
                            "description": {"type": "string", "description": "Event description"},
                            "start_time": {"type": "string", "description": "Start time (ISO format)"},
                            "duration_hours": {"type": "integer", "description": "Duration in hours", "default": 1}
                        },
                        "required": ["title"]
                    }
                ),
                Tool(
                    name="get_calendar_events",
                    description="Get upcoming calendar events",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_ahead": {"type": "integer", "description": "Days to look ahead", "default": 7}
                        },
                        "required": []
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "authenticate":
                    return await self._authenticate()
                elif request.name == "create_event":
                    return await self._create_event(request.arguments)
                elif request.name == "get_calendar_events":
                    days_ahead = request.arguments.get("days_ahead", 7) if request.arguments else 7
                    return await self._get_calendar_events(days_ahead)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _authenticate(self) -> CallToolResult:
        """Simulate Calendar authentication"""
        result = {
            "status": "authenticated",
            "message": "Google Calendar authentication successful (demo mode)",
            "timestamp": datetime.now().isoformat()
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _create_event(self, args) -> CallToolResult:
        """Simulate creating a calendar event"""
        title = args.get("title", "Untitled Event")
        description = args.get("description", "")
        duration_hours = args.get("duration_hours", 1)
        
        # Default to tomorrow at 9 AM if no start time provided
        if "start_time" in args:
            start_time = args["start_time"]
        else:
            start_time = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
            start_time = start_time.isoformat()
        
        result = {
            "event_id": f"demo_event_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "description": description,
            "start_time": start_time,
            "duration_hours": duration_hours,
            "status": "created",
            "message": "Event created successfully (demo mode)",
            "calendar_link": f"https://calendar.google.com/calendar/event?title={title.replace(' ', '+')}"
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_calendar_events(self, days_ahead: int) -> CallToolResult:
        """Simulate getting calendar events"""
        # Generate some sample events
        events = []
        for i in range(min(days_ahead, 3)):  # Max 3 sample events
            event_time = datetime.now() + timedelta(days=i+1, hours=9+i*2)
            events.append({
                "id": f"sample_event_{i+1}",
                "title": f"Sample Meeting {i+1}",
                "start_time": event_time.isoformat(),
                "description": f"Demo event {i+1} for testing"
            })
        
        result = {
            "events": events,
            "count": len(events),
            "days_ahead": days_ahead,
            "message": "Demo mode - returning sample events"
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = GoogleCalendarServer()
    
    # Proper initialization
    initialization_options = InitializationOptions(
        server_name="google-calendar",
        server_version="1.0.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            initialization_options
        )

if __name__ == "__main__":
    asyncio.run(main())
'''
    return content

def create_working_email_server():
    """Create properly working Email server"""
    content = '''#!/usr/bin/env python3
"""
Working Email Server with proper initialization
"""

import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent,
    CallToolRequest, CallToolResult, 
    ListToolsRequest, ListToolsResult
)

class EmailServer:
    def __init__(self):
        self.server = Server("email")
        self.logger = logging.getLogger(__name__)
        self.email_enabled = os.getenv("EMAIL_NOTIFICATIONS", "False").lower() == "true"
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Return tools for email operations"""
            tools = [
                Tool(
                    name="send_summary_email",
                    description="Send a summary email to configured recipients",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "Email subject"},
                            "content": {"type": "string", "description": "Email content"},
                            "recipient_type": {"type": "string", "description": "Type of recipients", "default": "summary"}
                        },
                        "required": ["subject", "content"]
                    }
                ),
                Tool(
                    name="test_email_config",
                    description="Test email configuration and connectivity",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls"""
            try:
                if request.name == "send_summary_email":
                    return await self._send_summary_email(request.arguments)
                elif request.name == "test_email_config":
                    return await self._test_email_config()
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _send_summary_email(self, args) -> CallToolResult:
        """Simulate sending an email"""
        subject = args.get("subject", "No Subject")
        content = args.get("content", "")
        recipient_type = args.get("recipient_type", "summary")
        
        if not self.email_enabled:
            result = {
                "sent": False,
                "reason": "Email notifications are disabled",
                "subject": subject,
                "content_length": len(content),
                "recipient_type": recipient_type
            }
        else:
            # Simulate successful email sending
            result = {
                "sent": True,
                "message": "Email sent successfully (demo mode)",
                "subject": subject,
                "content_length": len(content),
                "recipient_type": recipient_type,
                "timestamp": datetime.now().isoformat(),
                "recipients": ["demo@example.com"]  # Demo recipient
            }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _test_email_config(self) -> CallToolResult:
        """Test email configuration"""
        config_status = {
            "email_enabled": self.email_enabled,
            "smtp_host": os.getenv("EMAIL_HOST", "Not configured"),
            "smtp_port": os.getenv("EMAIL_PORT", "Not configured"),
            "username_configured": bool(os.getenv("EMAIL_USERNAME")),
            "password_configured": bool(os.getenv("EMAIL_PASSWORD")),
            "recipients_configured": bool(os.getenv("EMAIL_RECIPIENTS")),
            "config_valid": self.email_enabled and bool(os.getenv("EMAIL_USERNAME")),
            "message": "Email configuration test completed (demo mode)"
        }
        
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(config_status, indent=2))]
        )

async def main():
    """Main server entry point"""
    logging.basicConfig(level=logging.INFO)
    
    server_instance = EmailServer()
    
    # Proper initialization
    initialization_options = InitializationOptions(
        server_name="email",
        server_version="1.0.0",
        capabilities=server_instance.server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            initialization_options
        )

if __name__ == "__main__":
    asyncio.run(main())
'''
    return content

def fix_all_mcp_servers():
    """Create properly working MCP servers with correct initialization"""
    print("🔧 Creating properly working MCP servers...")
    
    # Create mcp_servers directory if it doesn't exist
    servers_dir = Path("mcp_servers")
    servers_dir.mkdir(exist_ok=True)
    
    # Create all working servers
    servers = {
        "google_drive_server.py": create_working_google_drive_server(),
        "ai_analysis_server.py": create_working_ai_analysis_server(),
        "google_calendar_server.py": create_working_calendar_server(),
        "email_server.py": create_working_email_server()
    }
    
    for filename, content in servers.items():
        file_path = servers_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✅ Created working {filename}")
    
    print("\n🎉 All MCP servers recreated with proper initialization!")
    print("Key fixes:")
    print("  ✅ Added InitializationOptions parameter")
    print("  ✅ Proper error handling") 
    print("  ✅ Better tool schemas")
    print("  ✅ Demo functionality that actually works")
    print("\nNow try: python mcp_main_server.py")

if __name__ == "__main__":
    fix_all_mcp_servers()