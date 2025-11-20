#!/usr/bin/env python3
"""
Test script to verify the connection handling between client and server
"""
import requests
import json
import time
from config import LOCAL_AI_URL

def test_connection():
    print("Testing connection to local AI server...")
    print(f"Target URL: {LOCAL_AI_URL}")
    
    # Test payload
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, can you respond to this test message?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    }
    
    try:
        print("Sending request...")
        response = requests.post(
            LOCAL_AI_URL,
            headers={
                "Content-Type": "application/json",
                "Connection": "close",
                "User-Agent": "VoiceAssistant/1.0"
            },
            json=payload,
            timeout=60,
            allow_redirects=False
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✓ Successfully received JSON response")
                print(f"Response keys: {list(result.keys())}")
                
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    print(f"✓ Response content: {content[:100]}...")
                    return True
                else:
                    print("⚠ Response doesn't contain expected structure")
                    print(f"Full response: {json.dumps(result, indent=2)[:500]}...")
                    return False
            except json.JSONDecodeError as e:
                print(f"✗ Error parsing JSON response: {e}")
                print(f"Raw response: {response.text[:500]}...")
                return False
        else:
            print(f"✗ Request failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is it running?")
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n✓ Connection test passed!")
    else:
        print("\n✗ Connection test failed!")
        print("Make sure your local AI server is running on the correct port.")