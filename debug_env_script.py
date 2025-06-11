#!/usr/bin/env python3
"""
Debug script to check environment variable access
"""

import os
from dotenv import load_dotenv

def debug_environment():
    """Debug environment variable access"""
    
    print("🔍 Environment Variable Debug")
    print("=" * 40)
    
    # Test 1: Before loading .env
    print("1. Before load_dotenv():")
    print(f"   OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:10] if os.getenv('OPENAI_API_KEY') else 'NOT FOUND'}...")
    
    # Test 2: Load .env explicitly
    print("\n2. Loading .env file...")
    env_loaded = load_dotenv()
    print(f"   .env loaded: {env_loaded}")
    
    # Test 3: After loading .env
    print("\n3. After load_dotenv():")
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"   OPENAI_API_KEY: {openai_key[:10]}...{openai_key[-4:]}")
    else:
        print("   OPENAI_API_KEY: NOT FOUND")
    
    # Test 4: Check .env file existence and content
    print("\n4. .env file check:")
    if os.path.exists('.env'):
        print("   .env file exists")
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        openai_lines = [line for line in lines if 'OPENAI_API_KEY' in line]
        if openai_lines:
            print(f"   Found OPENAI_API_KEY line: {openai_lines[0].strip()[:30]}...")
        else:
            print("   No OPENAI_API_KEY line found in .env")
    else:
        print("   .env file does not exist!")
    
    # Test 5: All environment variables
    print("\n5. All env vars containing 'OPENAI':")
    for key, value in os.environ.items():
        if 'OPENAI' in key.upper():
            print(f"   {key}: {value[:10] if value else 'EMPTY'}...")
    
    return openai_key is not None

if __name__ == "__main__":
    has_key = debug_environment()
    
    if has_key:
        print("\n✅ OpenAI API key is accessible!")
    else:
        print("\n❌ OpenAI API key is not accessible!")
        print("\nQuick fixes to try:")
        print("1. Check if .env file is in the same directory as this script")
        print("2. Make sure the line in .env is: OPENAI_API_KEY=sk-your-key-here")
        print("3. No spaces around the = sign")
        print("4. No quotes around the key unless needed")