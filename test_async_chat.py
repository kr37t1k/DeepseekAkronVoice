#!/usr/bin/env python3
"""
Test script to demonstrate the new async chat functionality
"""

import time
import threading
from local_chat import LocalChat

def test_callback(result_type, response):
    """Callback function for async chat"""
    print(f"Callback received: {result_type} - {response}")

def main():
    print("Testing async chat functionality...")
    
    # Initialize the chat client
    chat_client = LocalChat()
    
    # Test synchronous chat
    print("\n1. Testing synchronous chat:")
    start_time = time.time()
    response = chat_client.chat("Hello, how are you?")
    elapsed = time.time() - start_time
    print(f"Response: {response}")
    print(f"Time taken: {elapsed:.2f} seconds")
    
    # Test async chat
    print("\n2. Testing async chat:")
    start_time = time.time()
    result = chat_client.chat_async("What's the weather like today?", callback=test_callback)
    print(f"Async request initiated: {result}")
    print(f"Time taken for initiation: {time.time() - start_time:.2f} seconds")
    
    # Wait a bit to see the callback response
    time.sleep(2)
    
    # Test multiple concurrent requests to demonstrate threading
    print("\n3. Testing multiple concurrent requests:")
    start_time = time.time()
    
    def make_request(req_id):
        response = chat_client.chat(f"Request {req_id}: Tell me something interesting")
        print(f"Request {req_id} response: {response[:50]}...")
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=make_request, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    print(f"All concurrent requests completed in: {total_time:.2f} seconds")
    
    # Test connection state
    print("\n4. Testing connection state:")
    print(f"Connected: {chat_client.connection_state.is_connected}")
    print(f"Server status: {chat_client.connection_state.server_status}")
    print(f"Active requests: {chat_client.connection_state.active_requests}")
    
    print("\nAsync chat functionality test completed!")

if __name__ == "__main__":
    main()