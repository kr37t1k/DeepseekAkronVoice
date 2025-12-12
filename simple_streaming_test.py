#!/usr/bin/env python3
"""
Simple test for streaming functionality
"""

import requests
import json
import time
import threading
import subprocess
import sys
import os
from pathlib import Path

def start_streaming_server():
    """Start the streaming server in a subprocess"""
    print("🚀 Starting streaming server for testing...")
    
    # Start the server as a subprocess
    server_process = subprocess.Popen([
        sys.executable, "-u", "streaming_llama_server.py",
        "--test",  # Use mock model for testing
        "--host", "127.0.0.1",  # Use localhost for testing
        "--port", "8003"  # Use different port to avoid conflicts
    ])
    
    # Give the server some time to start
    time.sleep(3)
    
    return server_process

def test_streaming_simple():
    """Simple test to see what's happening with streaming"""
    print("\n🌊 Testing streaming functionality (simple)...")
    
    try:
        # Test streaming with a simple message
        stream_payload = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        response = requests.post(
            "http://127.0.0.1:8003/v1/chat/completions",
            json=stream_payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30  # Longer timeout
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("\nReading streaming response:")
            chunks = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"Line: {repr(line_str)}")
                    if line_str.startswith('data: '):
                        data = line_str[6:]  # Remove 'data: ' prefix
                        chunks.append(data)
                        if data.strip() == '[DONE]':
                            print("Found [DONE] marker!")
                            break
                        else:
                            try:
                                chunk_json = json.loads(data)
                                print(f"Chunk: {chunk_json}")
                            except json.JSONDecodeError:
                                print(f"Non-JSON data: {data}")
            
            print(f"\nTotal chunks received: {len(chunks)}")
            if chunks:
                print("First few chunks:")
                for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
                    print(f"  {i+1}: {chunk[:100]}...")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Streaming test timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 8003?")
        return False
    except Exception as e:
        print(f"❌ Streaming test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Simple Streaming Test")
    print("="*50)
    
    # Start the server
    server_process = start_streaming_server()
    
    try:
        # Run test
        success = test_streaming_simple()
        
        if success:
            print("\n✅ Streaming test completed successfully!")
        else:
            print("\n❌ Streaming test failed.")
            
    finally:
        # Stop the server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped.")

if __name__ == "__main__":
    main()