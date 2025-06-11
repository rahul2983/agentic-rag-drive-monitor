#!/usr/bin/env python3
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
