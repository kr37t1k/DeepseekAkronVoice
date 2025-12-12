#!/usr/bin/env python3
"""
Enhanced LLaMA Local Server with File Parsing Capabilities
This server can run on your computer and provide AI responses via API with document parsing support
"""

import argparse
import json
import time
import logging
import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue
import concurrent.futures
from datetime import datetime
import platform
from typing import Dict, Any, List, Optional
import mimetypes

# Try to import llama-cpp-python, fallback to mock if not available
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    print("Warning: llama-cpp-python not found. Using mock server.")
    LLAMA_AVAILABLE = False

# Import libraries for file parsing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentParser:
    """Class to handle parsing of various document formats"""
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """Parse PDF file and extract text"""
        if not PDF_AVAILABLE:
            return f"PDF parsing not available. Install PyPDF2 to enable PDF parsing."
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                return text_content
        except Exception as e:
            return f"Error parsing PDF: {str(e)}"
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """Parse DOCX file and extract text"""
        if not DOCX_AVAILABLE:
            return f"DOCX parsing not available. Install python-docx to enable DOCX parsing."
        
        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n".join(paragraphs)
        except Exception as e:
            return f"Error parsing DOCX: {str(e)}"
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """Parse TXT file and extract text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error parsing TXT: {str(e)}"
    
    @staticmethod
    def parse_md(file_path: str) -> str:
        """Parse MD file and extract text (stripping markdown formatting)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Simple markdown stripping - remove headers, bold, italic markers
                lines = content.split('\n')
                clean_lines = []
                for line in lines:
                    # Remove markdown header markers
                    if line.startswith('#'):
                        clean_lines.append(line.lstrip('# ').strip())
                    # Remove bold and italic markers
                    elif line.strip():
                        clean_line = line.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
                        clean_lines.append(clean_line.strip())
                
                return '\n'.join(clean_lines)
        except Exception as e:
            return f"Error parsing MD: {str(e)}"
    
    @classmethod
    def parse_file(cls, file_path: str) -> str:
        """Parse file based on extension"""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.pdf':
            return cls.parse_pdf(file_path)
        elif ext == '.docx':
            return cls.parse_docx(file_path)
        elif ext == '.txt':
            return cls.parse_txt(file_path)
        elif ext == '.md':
            return cls.parse_md(file_path)
        else:
            # Try to read as text if extension is unknown
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except:
                return f"Unsupported file format: {ext}"


class ServerState:
    """Class to manage server state and connections"""
    def __init__(self):
        self.active_connections = 0
        self.total_requests = 0
        self.start_time = datetime.now()
        self.is_running = True
        self.request_queue = queue.Queue()
        self.max_workers = 4  # Limit concurrent processing
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.document_parser = DocumentParser()
    
    def get_stats(self):
        """Get server statistics"""
        uptime = datetime.now() - self.start_time
        return {
            "active_connections": self.active_connections,
            "total_requests": self.total_requests,
            "uptime_seconds": int(uptime.total_seconds()),
            "max_workers": self.max_workers,
            "is_running": self.is_running,
            "document_parsing": True,
            "supported_formats": [".pdf", ".docx", ".txt", ".md"]
        }
    
    def increment_requests(self):
        """Increment request counter"""
        self.total_requests += 1


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
        
        # Check if the message involves document parsing
        if "parse document" in last_user_message.lower() or "read file" in last_user_message.lower():
            # Extract filename if mentioned
            import re
            matches = re.findall(r'([^\s]+\.(\w+))', last_user_message)
            if matches:
                filename = matches[0][0]
                if os.path.exists(filename):
                    # Simulate document parsing
                    parsed_content = f"[Document content preview from {filename}]: This is a simulated parsed document content..."
                    response = f"I've processed the document {filename}. Here's what I found:\n\n{parsed_content}"
                else:
                    response = f"Could not find the file: {filename}. Please make sure it exists in the current directory."
            else:
                response = f"I received your request to parse a document. To use this feature, please specify a file path in your message like 'parse document /path/to/file.pdf'"
        else:
            # Generate a simple mock response
            if "hello" in last_user_message.lower() or "hi" in last_user_message.lower():
                response = "Hello! How can I help you today?"
            elif "how are you" in last_user_message.lower():
                response = "I'm doing well, thank you for asking!"
            elif "bye" in last_user_message.lower() or "goodbye" in last_user_message.lower():
                response = "Goodbye! Have a great day!"
            else:
                response = f"I received your message: '{last_user_message}'. This is a mock response from the local server with document parsing capabilities."
        
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


class ThreadedHTTPServer(HTTPServer):
    """Handle requests in separate threads"""
    daemon_threads = True
    allow_reuse_address = True


class EnhancedLlamaRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the enhanced LLaMA server"""
    
    def __init__(self, model, server_state, *args, **kwargs):
        self.model = model
        self.server_state = server_state
        super().__init__(*args, **kwargs)
    
    def setup(self):
        """Set up the request handler with timeout"""
        super().setup()
        # Set socket timeout to prevent hanging connections
        self.connection.settimeout(180)  # 180 seconds (3 minutes) timeout
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Connection', 'close')  # Close connection after response
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests for server info and health checks"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.handle_health_check()
        elif parsed_path.path == '/stats':
            self.handle_stats()
        elif parsed_path.path == '/models':
            self.handle_models()
        elif parsed_path.path.startswith('/parse/'):
            self.handle_parse_document(parsed_path.path)
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_parse_document(self, path):
        """Handle document parsing endpoint"""
        try:
            # Extract file path from URL
            file_path = path[len('/parse/'):]
            file_path = os.path.abspath(file_path)  # Prevent directory traversal
            
            # Verify file exists and is safe to access
            if not os.path.exists(file_path):
                self.send_error(404, f"File not found: {file_path}")
                return
                
            # Check if it's within allowed directories (current directory)
            base_dir = os.path.abspath('.')
            if not file_path.startswith(base_dir):
                self.send_error(403, "Access denied: File outside allowed directory")
                return
            
            # Parse the document
            parsed_content = self.server_state.document_parser.parse_file(file_path)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            
            response = {
                "file_path": file_path,
                "parsed_content": parsed_content[:5000],  # Limit content length
                "content_length": len(parsed_content),
                "success": True
            }
            
            response_json = json.dumps(response)
            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Document parsing error: {e}")
            self.send_error(500, f"Document parsing failed: {str(e)}")
    
    def handle_health_check(self):
        """Handle health check endpoint"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "model_loaded": getattr(self.model, 'model_loaded', True) if hasattr(self.model, 'model_loaded') else True,
                "document_parsing_available": True
            }
            
            response_json = json.dumps(response)
            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.send_error(500, f"Health check failed: {str(e)}")
    
    def handle_stats(self):
        """Handle stats endpoint"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            
            stats = self.server_state.get_stats()
            stats["timestamp"] = datetime.now().isoformat()
            
            response_json = json.dumps(stats)
            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            self.send_error(500, f"Stats failed: {str(e)}")
    
    def handle_models(self):
        """Handle models endpoint"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            
            response = {
                "object": "list",
                "data": [
                    {
                        "id": "local-model",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "local",
                        "capabilities": ["chat", "document_parsing"]
                    }
                ]
            }
            
            response_json = json.dumps(response)
            self.send_header('Content-Length', str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Models endpoint error: {e}")
            self.send_error(500, f"Models endpoint failed: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/v1/chat/completions':
            self.handle_chat_completions()
        elif parsed_path.path == '/v1/document/process':
            self.handle_document_processing()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_document_processing(self):
        """Handle document processing requests"""
        try:
            # Get content length and read the body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse the JSON request
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Extract file path from request
            file_path = request_data.get('file_path')
            if not file_path:
                self.send_error(400, "Missing file_path in request")
                return
            
            # Parse the document
            parsed_content = self.server_state.document_parser.parse_file(file_path)
            
            # Create a response that includes the parsed content in the chat
            response = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"I've analyzed the document '{file_path}'. Here's what I found:\n\n{parsed_content[:1000]}...\n\nWhat would you like to know about this document?"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }],
                "usage": {
                    "prompt_tokens": len(parsed_content.split()),
                    "completion_tokens": 50,  # Approximate tokens for response
                    "total_tokens": len(parsed_content.split()) + 50
                },
                "document_info": {
                    "file_path": file_path,
                    "content_length": len(parsed_content),
                    "processed": True
                }
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Connection', 'close')
            response_json = json.dumps(response, separators=(',', ':'))
            self.send_header('Content-Length', len(response_json.encode('utf-8')))
            self.end_headers()
            
            try:
                self.wfile.write(response_json.encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError, socket.error) as write_error:
                logger.warning(f"Error writing response: {write_error}")
            
            logger.info(f"Processed document: {file_path}")
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in document processing request")
            try:
                self.send_error(400, "Invalid JSON in request")
            except:
                logger.warning("Could not send error response for JSON decode error")
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            try:
                self.send_error(500, f"Document processing error: {str(e)}")
            except:
                logger.warning("Could not send error response, client may have disconnected")
    
    def handle_chat_completions(self):
        """Handle chat completion requests"""
        try:
            # Increment request counter
            self.server_state.increment_requests()
            
            # Get content length and read the body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse the JSON request
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Extract parameters
            messages = request_data.get('messages', [])
            temperature = request_data.get('temperature', 0.7)
            max_tokens = request_data.get('max_tokens', 200)
            
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
            # Add headers to prevent connection issues
            self.send_header('Connection', 'close')
            response_json = json.dumps(response, separators=(',', ':'))  # Compact JSON to avoid issues
            self.send_header('Content-Length', len(response_json.encode('utf-8')))
            self.end_headers()
            
            # Write response in chunks to handle connection issues better
            try:
                self.wfile.write(response_json.encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError, socket.error) as write_error:
                logger.warning(f"Error writing response: {write_error}")
                # Client disconnected, nothing we can do
            
            logger.info(f"Generated response for request with {len(messages)} messages")
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request")
            try:
                self.send_error(400, "Invalid JSON in request")
            except:
                logger.warning("Could not send error response for JSON decode error")
        except BrokenPipeError:
            logger.warning("Client disconnected before response was sent")
        except ConnectionResetError:
            logger.warning("Connection was reset by client")
        except socket.error as e:
            logger.error(f"Socket error: {e}")
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            try:
                self.send_error(500, f"Server error: {str(e)}")
            except:
                # If we can't send an error response, client may have disconnected
                logger.warning("Could not send error response, client may have disconnected")

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format}" % args)


def run_server(model, host='0.0.0.0', port=8001):
    """Run the enhanced LLaMA server"""
    
    # Create server state
    server_state = ServerState()
    
    def handler_factory(*args, **kwargs):
        return EnhancedLlamaRequestHandler(model, server_state, *args, **kwargs)
    
    server = ThreadedHTTPServer((host, port), handler_factory)
    logger.info(f"Starting enhanced LLaMA server on {host}:{port}")
    logger.info(f"API endpoint: http://{host}:{port}/v1/chat/completions")
    logger.info(f"Document processing: http://{host}:{port}/v1/document/process")
    logger.info(f"Parse endpoint: http://{host}:{port}/parse/{'file_path'}")
    logger.info(f"Health endpoint: http://{host}:{port}/health")
    logger.info(f"Stats endpoint: http://{host}:{port}/stats")
    logger.info("Server supports document parsing (.pdf, .docx, .txt, .md)")
    logger.info("Server is configured with threaded connections and timeout handling")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server_state.is_running = False
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description='Enhanced LLaMA Local Server with document parsing')
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
                n_batch=512,
                seed=-1,
                n_threads_batch=0,
                chat_format=("qwen" if "qwen" in str(args.model_path).lower() else "llama-3"),
                offload_kqv=True,
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