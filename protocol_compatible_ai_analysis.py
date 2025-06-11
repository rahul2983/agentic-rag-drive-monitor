#!/usr/bin/env python3
import sys
sys.path.append('.')
from protocol_compatible_server import run_server
import asyncio

if __name__ == "__main__":
    asyncio.run(run_server("ai_analysis"))
