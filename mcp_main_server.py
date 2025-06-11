#!/usr/bin/env python3
"""
Working MCP Agentic RAG Main Server
Uses proper MCP client connection protocol
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import os
from pathlib import Path

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Core dependencies
from dotenv import load_dotenv

@dataclass
class AgenticTask:
    """Represents an agentic task with context and dependencies"""
    id: str
    task_type: str
    description: str
    priority: str
    dependencies: List[str] = None
    context: Dict[str, Any] = None
    status: str = "pending"
    created_at: str = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class WorkingMCPServerManager:
    """Working MCP server manager using proper stdio_client"""
    
    def __init__(self):
        self.servers: Dict[str, ClientSession] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
    async def connect_to_server(self, server_name: str, server_script: str) -> bool:
        """Connect to an MCP server using proper stdio_client"""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command="python",
                args=[server_script],
                env=dict(os.environ)  # Pass environment variables
            )
            
            # Use stdio_client context manager
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # Store the session (note: this won't persist after context exit)
                    # For a real implementation, we'd need to manage this differently
                    self.servers[server_name] = session
                    
                    self.logger.info(f"Successfully connected to {server_name}")
                    
                    # Test the connection by listing tools
                    try:
                        tools_result = await session.list_tools()
                        tools = [tool.name for tool in tools_result.tools]
                        self.logger.info(f"Server {server_name} tools: {tools}")
                        return True
                    except Exception as e:
                        self.logger.error(f"Error testing {server_name}: {e}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def call_server_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a server (simplified for demo)"""
        # This is a simplified implementation for demonstration
        # In a real app, you'd need persistent connections
        
        try:
            server_script = f"mcp_servers/{server_name}_server.py"
            server_params = StdioServerParameters(
                command="python",
                args=[server_script],
                env=dict(os.environ)
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Call the tool
                    result = await session.call_tool(tool_name, arguments)
                    return result
                    
        except Exception as e:
            self.logger.error(f"Error calling {tool_name} on {server_name}: {e}")
            return None

class SimpleAgenticOrchestrator:
    """Simplified agentic orchestrator"""
    
    def __init__(self, server_manager: WorkingMCPServerManager):
        self.server_manager = server_manager
        self.task_queue: List[AgenticTask] = []
        self.completed_tasks: List[AgenticTask] = []
        self.logger = logging.getLogger(__name__)
        
    async def create_task(self, task_type: str, description: str, priority: str = "medium", 
                         context: Dict[str, Any] = None) -> str:
        """Create a new agentic task"""
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = AgenticTask(
            id=task_id,
            task_type=task_type,
            description=description,
            priority=priority,
            context=context or {}
        )
        
        self.task_queue.append(task)
        self.logger.info(f"Created task: {task_id} - {description}")
        return task_id
    
    async def execute_task(self, task: AgenticTask) -> bool:
        """Execute a single task"""
        try:
            task.status = "in_progress"
            self.logger.info(f"Executing task: {task.id}")
            
            if task.task_type == "drive_monitoring":
                return await self._test_drive_monitoring(task)
            elif task.task_type == "ai_analysis":
                return await self._test_ai_analysis(task)
            elif task.task_type == "calendar_test":
                return await self._test_calendar(task)
            else:
                self.logger.info(f"Task type {task.task_type} completed (no-op)")
                task.status = "completed"
                return True
                
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            task.status = "failed"
            return False
    
    async def _test_drive_monitoring(self, task: AgenticTask) -> bool:
        """Test drive monitoring"""
        try:
            result = await self.server_manager.call_server_tool(
                "google_drive",
                "get_recent_files",
                {"hours_back": 24}
            )
            
            if result:
                self.logger.info("✅ Drive monitoring test successful")
                task.status = "completed"
                return True
            else:
                self.logger.error("❌ Drive monitoring test failed")
                task.status = "failed"
                return False
                
        except Exception as e:
            self.logger.error(f"Drive monitoring error: {e}")
            task.status = "failed"
            return False
    
    async def _test_ai_analysis(self, task: AgenticTask) -> bool:
        """Test AI analysis"""
        try:
            result = await self.server_manager.call_server_tool(
                "ai_analysis",
                "generate_summary",
                {
                    "content": "This is a test document for AI analysis.",
                    "max_length": 50
                }
            )
            
            if result:
                self.logger.info("✅ AI analysis test successful")
                task.status = "completed"
                return True
            else:
                self.logger.error("❌ AI analysis test failed")
                task.status = "failed"
                return False
                
        except Exception as e:
            self.logger.error(f"AI analysis error: {e}")
            task.status = "failed"
            return False
    
    async def _test_calendar(self, task: AgenticTask) -> bool:
        """Test calendar functionality"""
        try:
            result = await self.server_manager.call_server_tool(
                "google_calendar",
                "get_calendar_events",
                {"days_ahead": 7}
            )
            
            if result:
                self.logger.info("✅ Calendar test successful")
                task.status = "completed"
                return True
            else:
                self.logger.error("❌ Calendar test failed")
                task.status = "failed"
                return False
                
        except Exception as e:
            self.logger.error(f"Calendar error: {e}")
            task.status = "failed"
            return False
    
    async def process_task_queue(self):
        """Process all tasks in queue"""
        while self.task_queue:
            task = self.task_queue.pop(0)
            success = await self.execute_task(task)
            self.completed_tasks.append(task)
            
            if success:
                self.logger.info(f"✅ Task completed: {task.id}")
            else:
                self.logger.error(f"❌ Task failed: {task.id}")

class WorkingMCPApplication:
    """Working MCP application"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_manager = WorkingMCPServerManager()
        self.orchestrator = SimpleAgenticOrchestrator(self.server_manager)
        self.logger = logging.getLogger(__name__)
    
    async def test_server_connections(self):
        """Test connections to all MCP servers"""
        servers = [
            ("google_drive", "mcp_servers/google_drive_server.py"),
            ("ai_analysis", "mcp_servers/ai_analysis_server.py"),
            ("google_calendar", "mcp_servers/google_calendar_server.py"),
            ("email", "mcp_servers/email_server.py")
        ]
        
        working_servers = []
        
        for server_name, server_script in servers:
            if os.path.exists(server_script):
                self.logger.info(f"Testing connection to {server_name}...")
                success = await self.server_manager.connect_to_server(server_name, server_script)
                if success:
                    working_servers.append(server_name)
                    self.logger.info(f"✅ {server_name} is working")
                else:
                    self.logger.warning(f"❌ {server_name} failed to connect")
            else:
                self.logger.error(f"❌ {server_script} not found")
        
        self.logger.info(f"Working servers: {working_servers}")
        return working_servers
    
    async def run_comprehensive_test(self):
        """Run a comprehensive test of the system"""
        self.logger.info("🚀 Starting comprehensive MCP test...")
        
        # Test server connections
        working_servers = await self.test_server_connections()
        
        if not working_servers:
            self.logger.error("❌ No servers are working - aborting test")
            return
        
        # Create test tasks based on working servers
        if "google_drive" in working_servers:
            await self.orchestrator.create_task(
                "drive_monitoring",
                "Test Google Drive functionality",
                "high"
            )
        
        if "ai_analysis" in working_servers:
            await self.orchestrator.create_task(
                "ai_analysis",
                "Test AI analysis functionality",
                "medium"
            )
        
        if "google_calendar" in working_servers:
            await self.orchestrator.create_task(
                "calendar_test",
                "Test Calendar functionality",
                "low"
            )
        
        # Execute all tasks
        await self.orchestrator.process_task_queue()
        
        # Report results
        total_tasks = len(self.orchestrator.completed_tasks)
        successful_tasks = len([t for t in self.orchestrator.completed_tasks if t.status == "completed"])
        
        self.logger.info(f"📊 Test Results: {successful_tasks}/{total_tasks} tasks successful")
        
        if successful_tasks > 0:
            self.logger.info("🎉 MCP Agentic RAG system is working!")
        else:
            self.logger.warning("⚠️ Some issues found, but servers are accessible")

async def main():
    """Main entry point"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mcp_working_test.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Load configuration
    load_dotenv()
    
    # Validate environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY environment variable is required!")
        return
    else:
        logger.info(f"✅ OpenAI API key found: {openai_key[:10]}...")
    
    config = {
        "google_credentials_path": os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json"),
        "google_token_path": os.getenv("GOOGLE_TOKEN_PATH", "./token.json"),
        "openai_api_key": openai_key,
        "target_folder_id": os.getenv("TARGET_FOLDER_ID"),
        "email_notifications": os.getenv("EMAIL_NOTIFICATIONS", "false").lower() == "true"
    }
    
    # Create and run application
    app = WorkingMCPApplication(config)
    
    try:
        await app.run_comprehensive_test()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())