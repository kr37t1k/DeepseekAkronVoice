#!/usr/bin/env python3
"""
Server configuration file with additional settings for robust operation
"""

# Server Configuration
SERVER_HOST = "0.0.0.0"  # Bind to all interfaces
SERVER_PORT = 8001       # Default port for local AI
MODEL_PATH = "./models/model.gguf"  # Path to your GGUF model file
CONTEXT_SIZE = 2048      # Context window size
THREADS = 4              # Number of threads for model processing

# Connection settings
CONNECTION_TIMEOUT = 60  # Timeout for connections in seconds
MAX_CONNECTIONS = 10     # Maximum concurrent connections
KEEP_ALIVE = False       # Whether to keep connections alive

# Model parameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500

# Logging
LOG_LEVEL = "INFO"       # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "server.log"  # File to log server activity

# CORS settings
ALLOWED_ORIGINS = ["*"]  # Origins allowed to access the API
ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_HEADERS = ["Content-Type", "Authorization"]

print("Server configuration loaded")