#!/usr/bin/env python3
"""
Fixed Google Calendar Server
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
                            "description": {"type": "string", "description": "Event description"}
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
                            "days_ahead": {"type": "integer", "default": 7}
                        },
                        "required": []
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            try:
                if request.name == "authenticate":
                    return await self._authenticate()
                elif request.name == "create_event":
                    return await self._create_event(request.arguments)
                elif request.name == "get_calendar_events":
                    return await self._get_calendar_events(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def _authenticate(self) -> CallToolResult:
        return CallToolResult(
            content=[TextContent(type="text", text="Calendar authentication simulated")]
        )
    
    async def _create_event(self, args) -> CallToolResult:
        event_time = datetime.now() + timedelta(days=1)
        result = {
            "event_id": "demo_event_123",
            "title": args["title"],
            "start_time": event_time.isoformat(),
            "message": "Event created (demo mode)"
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )
    
    async def _get_calendar_events(self, args) -> CallToolResult:
        result = {
            "events": [],
            "count": 0,
            "days_ahead": args.get("days_ahead", 7),
            "message": "No events found (demo mode)"
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, indent=2))]
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    calendar_server = GoogleCalendarServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await calendar_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-calendar",
                server_version="1.0.0",
                capabilities=calendar_server.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
