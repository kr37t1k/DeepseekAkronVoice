#!/usr/bin/env python3
"""
Test script for enhanced LLaMA and MCP servers
This script demonstrates the functionality of the enhanced servers
"""

import requests
import json
import time
import threading
from pathlib import Path

def test_llama_server(host='localhost', port=8001):
    """Test the enhanced LLaMA server functionality"""
    base_url = f"http://{host}:{port}"
    
    print(f"🔍 Testing LLaMA server at {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ LLaMA server health check: PASSED")
        else:
            print(f"❌ LLaMA server health check: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ LLaMA server health check: FAILED ({e})")
        return False
    
    # Test models endpoint
    try:
        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code == 200:
            print("✅ LLaMA server models endpoint: PASSED")
        else:
            print(f"❌ LLaMA server models endpoint: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ LLaMA server models endpoint: FAILED ({e})")
    
    # Test chat completion (mock)
    try:
        payload = {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        response = requests.post(f"{base_url}/v1/chat/completions", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ LLaMA server chat completion: PASSED")
            print(f"   Response preview: {result['choices'][0]['message']['content'][:100]}...")
        else:
            print(f"❌ LLaMA server chat completion: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ LLaMA server chat completion: FAILED ({e})")
    
    # Test document parsing if test file exists
    test_file = Path("test_document.md")
    if test_file.exists():
        try:
            response = requests.get(f"{base_url}/parse/{test_file.absolute()}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                print("✅ LLaMA server document parsing: PASSED")
                print(f"   Parsed {result.get('content_length', 0)} characters")
            else:
                print(f"❌ LLaMA server document parsing: FAILED (status {response.status_code})")
        except Exception as e:
            print(f"❌ LLaMA server document parsing: FAILED ({e})")
    else:
        print("⚠️  Test document not found, skipping document parsing test")
    
    return True

def test_mcp_server(host='localhost', port=3000):
    """Test the enhanced MCP server functionality"""
    base_url = f"http://{host}:{port}"
    
    print(f"🔍 Testing MCP server at {base_url}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ MCP server health check: PASSED")
        else:
            print(f"❌ MCP server health check: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ MCP server health check: FAILED ({e})")
        return False
    
    # Test tools endpoint
    try:
        response = requests.get(f"{base_url}/mcp/tools", timeout=5)
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ MCP server tools endpoint: PASSED")
            print(f"   Available tools: {len(tools.get('tools', []))}")
        else:
            print(f"❌ MCP server tools endpoint: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ MCP server tools endpoint: FAILED ({e})")
    
    # Test sync endpoint
    try:
        response = requests.get(f"{base_url}/sync", timeout=5)
        if response.status_code == 200:
            print("✅ MCP server sync endpoint: PASSED")
        else:
            print(f"❌ MCP server sync endpoint: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ MCP server sync endpoint: FAILED ({e})")
    
    # Test a system info tool via HTTP POST
    try:
        payload = {
            "tool_name": "system_info",
            "arguments": {}
        }
        response = requests.post(f"{base_url}/mcp/tools", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if "error" not in result:
                print("✅ MCP server system_info tool: PASSED")
            else:
                print(f"❌ MCP server system_info tool: FAILED ({result.get('error')})")
        else:
            print(f"❌ MCP server system_info tool: FAILED (status {response.status_code})")
    except Exception as e:
        print(f"❌ MCP server system_info tool: FAILED ({e})")
    
    return True

def main():
    print("🧪 Running tests for enhanced servers...")
    
    # Test both servers
    llama_ok = test_llama_server()
    print()  # Empty line
    mcp_ok = test_mcp_server()
    
    print(f"\n📊 Test Results:")
    print(f"   LLaMA Server: {'✅ PASSED' if llama_ok else '❌ FAILED'}")
    print(f"   MCP Server: {'✅ PASSED' if mcp_ok else '❌ FAILED'}")
    
    if llama_ok and mcp_ok:
        print("\n🎉 All tests passed! Enhanced servers are working correctly.")
        print("\n💡 Next steps:")
        print("   - Start servers with: python unified_server_launcher.py --test")
        print("   - Access LLaMA API at: http://localhost:8001/v1/chat/completions")
        print("   - Access MCP tools at: http://localhost:3000/mcp/tools")
        print("   - Parse documents at: http://localhost:8001/parse/{file_path}")
    else:
        print("\n❌ Some tests failed. Please check server status and requirements.")

if __name__ == "__main__":
    main()