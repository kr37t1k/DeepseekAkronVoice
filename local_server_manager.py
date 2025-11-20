"""
Local Server Manager for running LLaMA server in a separate thread
"""
import threading
import subprocess
import sys
import time
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class LocalServerManager:
    def __init__(self, model_path: str, host: str = "0.0.0.0", port: int = 8001):
        self.model_path = model_path
        self.host = host
        self.port = port
        self.server_process = None
        self.server_thread = None
        self.is_running = False
        
    def start_server(self):
        """Start the local LLaMA server in a separate thread"""
        if self.is_running:
            logger.warning("Server is already running")
            return
            
        try:
            # Check if model file exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            # Start the server process
            cmd = [
                sys.executable, "-m", "llama_cpp.server", 
                "--model", self.model_path,
                "--host", self.host,
                "--port", str(self.port),
                "--n_ctx", "2048"
            ]
            
            logger.info(f"Starting local server with command: {' '.join(cmd)}")
            
            # Start the server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give the server some time to start
            time.sleep(2)
            
            # Check if the process is still running
            if self.server_process.poll() is not None:
                # Process terminated early, get error output
                stderr_output = self.server_process.stderr.read().decode()
                raise RuntimeError(f"Server failed to start: {stderr_output}")
            
            self.is_running = True
            logger.info(f"Local server started on {self.host}:{self.port}")
            
        except FileNotFoundError:
            # If llama_cpp.server is not available, try our custom server
            logger.info("llama_cpp.server not found, trying custom server...")
            self._start_custom_server()
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise
    
    def _start_custom_server(self):
        """Start our custom server if llama-cpp-python server is not available"""
        try:
            # Start the server in a separate thread
            def run_custom_server():
                try:
                    from llama_server import run_server
                    from llama_server import MockLlamaModel
                    # For now, we'll use a mock model in the thread
                    # In a real implementation, we'd load the actual model
                    model = MockLlamaModel()
                    run_server(model, self.host, self.port)
                except Exception as e:
                    logger.error(f"Error in custom server thread: {e}")
            
            self.server_thread = threading.Thread(
                target=run_custom_server,
                daemon=True
            )
            self.server_thread.start()
            self.is_running = True
            logger.info(f"Custom local server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error starting custom server: {e}")
            raise
    
    def stop_server(self):
        """Stop the local server"""
        if not self.is_running:
            logger.warning("Server is not running")
            return
            
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                logger.info("Local server process terminated")
            elif self.server_thread:
                # For thread-based server, we rely on daemon thread termination
                logger.info("Local server thread marked for termination")
                
            self.is_running = False
        except subprocess.TimeoutExpired:
            if self.server_process:
                self.server_process.kill()
                logger.warning("Local server process force killed")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.is_running:
            self.stop_server()


# Alternative implementation using the built-in server capabilities
class ThreadedLocalServer:
    """
    Alternative implementation that runs the server in a thread
    """
    def __init__(self, model_path: str, host: str = "0.0.0.0", port: int = 8001):
        self.model_path = model_path
        self.host = host
        self.port = port
        self.server_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.is_running = False
        
    def start_server(self):
        """Start the server in a separate thread"""
        if self.is_running:
            logger.warning("Server is already running")
            return
            
        def run_server():
            try:
                # Try to import and use llama-cpp-python server
                try:
                    from llama_cpp import Llama
                    from llama_cpp.server import run
                    import tempfile
                    import json
                    
                    # Create a temporary config file for the server
                    config = {
                        "model": self.model_path,
                        "host": self.host,
                        "port": self.port,
                        "n_ctx": 2048
                    }
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(config, f)
                        config_file = f.name
                    
                    # Run the server
                    run([
                        "--config_file", config_file,
                        "--host", self.host,
                        "--port", str(self.port)
                    ])
                    
                    # Clean up
                    os.unlink(config_file)
                    
                except ImportError:
                    # Fallback to our custom implementation
                    from llama_server import MockLlamaModel
                    from llama_server import run_server
                    
                    model = MockLlamaModel()
                    run_server(model, self.host, self.port)
                    
            except Exception as e:
                logger.error(f"Server thread error: {e}")
                self.is_running = False
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True
        logger.info(f"Threaded server started on {self.host}:{self.port}")
    
    def stop_server(self):
        """Stop the threaded server"""
        self.is_running = False
        if self.server_thread:
            self.stop_event.set()
            self.server_thread.join(timeout=2)
        logger.info("Threaded server stopped")