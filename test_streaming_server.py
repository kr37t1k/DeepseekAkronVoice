#!/usr/bin/env python3
"""
Test script for streaming LLaMA server
This script tests the streaming functionality of the enhanced LLaMA server
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
        "--port", "8002"  # Use different port to avoid conflicts
    ])
    
    # Give the server some time to start
    time.sleep(3)
    
    return server_process

def test_streaming_functionality():
    """Test the streaming functionality"""
    print("\n🌊 Testing streaming functionality...")
    
    try:
        # Test streaming with a simple message
        stream_payload = {
            "messages": [
                {"role": "user", "content": "Hello, this is a streaming test. Please respond with a short greeting and count from 1 to 3."}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = requests.post(
            "http://127.0.0.1:8002/v1/chat/completions",
            json=stream_payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=15
        )
        
        if response.status_code == 200 and response.headers.get('content-type', '').startswith('text/event-stream'):
            print("✅ Streaming endpoint working (detected Server-Sent Events)")
            
            # Read and display the streamed content
            print("\n💬 Streaming response:")
            full_response = ""
            chunk_count = 0
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        chunk_count += 1
                        data = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data.strip() == '[DONE]':
                            print("Stream ended with [DONE]")
                            break
                            
                        try:
                            chunk_json = json.loads(data)
                            # Extract content from the chunk
                            choices = chunk_json.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    print(content, end='', flush=True)
                                
                                # Check if this is the final chunk
                                finish_reason = choices[0].get('finish_reason')
                                if finish_reason == 'stop':
                                    print("\nStream ended with finish_reason='stop'")
                                    break
                        except json.JSONDecodeError:
                            # Skip invalid JSON lines
                            continue
                    elif line_str.startswith(':'):
                        # This is a comment line, skip it
                        continue
                    else:
                        # This could be other SSE format, just skip
                        continue
            
            print(f"\n\n✅ Received {chunk_count} streaming chunks")
            print(f"💬 Full response: {full_response}")
            return True
        else:
            print(f"❌ Streaming test failed - wrong response type: {response.headers.get('content-type', 'unknown')}")
            print(f"Status code: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Streaming test timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 8002?")
        return False
    except Exception as e:
        print(f"❌ Streaming test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_non_streaming_functionality():
    """Test the non-streaming functionality for comparison"""
    print("\n📦 Testing non-streaming functionality...")
    
    try:
        # Test non-streaming with the same message
        non_stream_payload = {
            "messages": [
                {"role": "user", "content": "Hello, this is a non-streaming test. Please respond with a short greeting."}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        response = requests.post(
            "http://127.0.0.1:8002/v1/chat/completions",
            json=non_stream_payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Non-streaming endpoint working")
            response_data = response.json()
            content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"💬 Response: {content}")
            return True
        else:
            print(f"❌ Non-streaming test failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Non-streaming test error: {e}")
        return False

def test_document_parsing():
    """Test document parsing functionality"""
    print("\n📄 Testing document parsing functionality...")
    
    # Create a temporary test file
    test_file = Path("test_streaming.txt")
    test_content = "This is a test document for streaming server functionality. It contains some text to parse."
    test_file.write_text(test_content)
    
    try:
        # Test document parsing endpoint
        response = requests.get(f"http://127.0.0.1:8002/parse/{test_file.absolute()}", timeout=10)
        
        if response.status_code == 200:
            print("✅ Document parsing endpoint working")
            result = response.json()
            print(f"📄 Parsed {result.get('content_length', 0)} characters")
            print(f"📄 Content preview: {result.get('parsed_content', '')[:100]}...")
            return True
        else:
            print(f"❌ Document parsing failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Document parsing test error: {e}")
        return False
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

def main():
    print("🧪 Testing Streaming LLaMA Server")
    print("="*50)
    
    # Start the server
    server_process = start_streaming_server()
    
    try:
        # Run tests
        streaming_success = test_streaming_functionality()
        non_streaming_success = test_non_streaming_functionality()
        parsing_success = test_document_parsing()
        
        print("\n" + "="*50)
        print("📊 Test Results:")
        print(f"🌊 Streaming: {'✅ PASS' if streaming_success else '❌ FAIL'}")
        print(f"📦 Non-streaming: {'✅ PASS' if non_streaming_success else '❌ FAIL'}")
        print(f"📄 Document parsing: {'✅ PASS' if parsing_success else '❌ FAIL'}")
        
        if streaming_success and non_streaming_success and parsing_success:
            print("\n🎉 All tests passed! Streaming server is working correctly.")
            print("💡 The server is compatible with LM Studio and other streaming clients.")
        else:
            print("\n⚠️  Some tests failed. Check the server implementation.")
            
    finally:
        # Stop the server
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped.")

if __name__ == "__main__":
    main()