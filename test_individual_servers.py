#!/usr/bin/env python3
"""
Test individual MCP servers to see if they work independently
"""

import asyncio
import subprocess
import sys
import os
from dotenv import load_dotenv

async def test_server_individually(server_name: str, server_script: str):
    """Test if a server can start and respond"""
    print(f"\n🧪 Testing {server_name} server...")
    
    if not os.path.exists(server_script):
        print(f"❌ Server script not found: {server_script}")
        return False
    
    try:
        # Load environment variables
        load_dotenv()
        env = dict(os.environ)
        
        # Start the server process
        process = await asyncio.create_subprocess_exec(
            sys.executable, server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        # Give it a moment to start
        await asyncio.sleep(2)
        
        # Check if process is still running
        if process.returncode is None:
            print(f"✅ {server_name} server started successfully")
            
            # Try to terminate gracefully
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            
            return True
        else:
            # Process exited, check stderr for errors
            stdout, stderr = await process.communicate()
            print(f"❌ {server_name} server exited with code {process.returncode}")
            if stderr:
                print(f"   Error: {stderr.decode()}")
            if stdout:
                print(f"   Output: {stdout.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing {server_name}: {e}")
        return False

async def test_all_servers():
    """Test all MCP servers individually"""
    
    print("🔧 MCP Server Individual Tests")
    print("=" * 40)
    
    # Check environment first
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OpenAI API Key: {openai_key[:10]}...")
    else:
        print("❌ OpenAI API Key: NOT FOUND")
    
    servers = [
        ("Google Drive", "mcp_servers/google_drive_server.py"),
        ("AI Analysis", "mcp_servers/ai_analysis_server.py"),
        ("Google Calendar", "mcp_servers/google_calendar_server.py"),
        ("Email", "mcp_servers/email_server.py")
    ]
    
    working_servers = []
    
    for server_name, server_script in servers:
        success = await test_server_individually(server_name, server_script)
        if success:
            working_servers.append(server_name)
    
    print(f"\n📊 Results:")
    print(f"   Working servers: {len(working_servers)}/{len(servers)}")
    print(f"   Working: {', '.join(working_servers)}")
    
    if len(working_servers) == len(servers):
        print("\n🎉 All servers are working individually!")
        print("   The issue is likely with the MCP client connection protocol.")
    elif len(working_servers) > 0:
        print(f"\n⚠️ Some servers are working. Check the failed ones.")
    else:
        print(f"\n❌ No servers are working. Check your setup.")

async def main():
    await test_all_servers()

if __name__ == "__main__":
    asyncio.run(main())