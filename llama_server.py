#!/usr/bin/env python3
"""
LLaMA Local Server for mobile device
This server can run on your phone and provide AI responses via API
"""

import argparse
import json
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue
import os

# Try to import llama-cpp-python, fallback to mock if not available
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    print("Warning: llama-cpp-python not found. Using mock server.")
    LLAMA_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLlamaModel:
    """Mock model for testing when llama-cpp-python is not available"""
    
    def __init__(self):
        self.model_loaded = True
    
    def create_chat_completion(self, messages, temperature=0.7, max_tokens=500, **kwargs):
        # Mock response based on the last user message
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        # Generate a simple mock response
        if "hello" in last_user_message.lower() or "hi" in last_user_message.lower():
            response = "Hello! How can I help you today?"
        elif "how are you" in last_user_message.lower():
            response = "I'm doing well, thank you for asking!"
        elif "bye" in last_user_message.lower() or "goodbye" in last_user_message.lower():
            response = "Goodbye! Have a great day!"
        else:
            response = f"I received your message: '{last_user_message}'. This is a mock response from the local server."
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop",
                "index": 0
            }],
            "usage": {
                "prompt_tokens": len(last_user_message.split()),
                "completion_tokens": len(response.split()),
                "total_tokens": len(last_user_message.split()) + len(response.split())
            }
        }


class LlamaRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the LLaMA server"""
    
    def __init__(self, model, *args, **kwargs):
        self.model = model
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/v1/chat/completions':
            self.handle_chat_completions()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_chat_completions(self):
        """Handle chat completion requests"""
        try:
            # Get content length and read the body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse the JSON request
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Extract parameters
            messages = request_data.get('messages', [])
            temperature = request_data.get('temperature', 0.7)
            max_tokens = request_data.get('max_tokens', 500)
            
            # Generate response using the model
            response = self.model.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(response, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
            logger.info(f"Generated response for request with {len(messages)} messages")
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON in request")
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.send_error(500, f"Server error: {str(e)}")
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format}" % args)


def run_server(model, host='0.0.0.0', port=8001):
    """Run the LLaMA server"""
    
    def handler_factory(*args, **kwargs):
        return LlamaRequestHandler(model, *args, **kwargs)
    
    server = HTTPServer((host, port), handler_factory)
    logger.info(f"Starting LLaMA server on {host}:{port}")
    logger.info(f"API endpoint: http://{host}:{port}/v1/chat/completions")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(description='LLaMA Local Server for mobile AI')
    parser.add_argument('--model-path', type=str, required=True, 
                       help='Path to the GGUF model file')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8001,
                       help='Port to bind server to (default: 8001)')
    parser.add_argument('--n_ctx', type=int, default=2048,
                       help='Context size for the model (default: 2048)')
    
    args = parser.parse_args()
    
    # Load the model
    if LLAMA_AVAILABLE:
        logger.info(f"Loading model from {args.model_path}")
        try:
            model = Llama(
                model_path=args.model_path,
                n_ctx=args.n_ctx,
                n_threads=4,  # Adjust based on your device
                verbose=False
            )
            logger.info("Model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            logger.info("Using mock model instead...")
            model = MockLlamaModel()
    else:
        model = MockLlamaModel()
        logger.info("Using mock model (llama-cpp-python not available)")
    
    # Run the server
    run_server(model, args.host, args.port)


if __name__ == "__main__":
    main()