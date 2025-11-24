# Local AI Server Setup

This project now supports running a local AI server instead of using ani no-free API's. You can run the AI model on your phone or local machine.

## Components

1. **llama_server.py** - Custom HTTP server that exposes a LLaMA model via API
2. **local_chat.py** - Chat interface that connects to your local AI server
3. **local_server_manager.py** - Manages starting/stopping the local server
4. **app_with_server.py** - Main application that can optionally start the local server

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run on Your Phone

#### Option A: (not working rn) Using existing Django server (kr37t1k/MobileTextGenerationDelta)

If you have your Django server running on your phone at `0.0.0.0:8000`:

1. Update the config to point to your Django server:
   ```python
   # In config.py
   LOCAL_AI_URL = "http://0.0.0.0:8000/v1/chat/completions"  # Your Django server
   ```

#### Option B: Using llama-cpp-python server

1. Download a GGUF model file (e.g., a quantized LLaMA model)
2. Run the server on your phone:
   ```bash
   python llama_server.py --model-path /path/to/your/model.gguf --host 0.0.0.0 --port 8001
   ```

### 3. Run the Voice Assistant

#### On your computer (connected to phone's server):

1. Make sure your phone and computer are on the same network
2. Update the config with your phone's IP address:
   ```python
   # In config.py
   LOCAL_AI_URL = "http://[PHONE_IP]:8001/v1/chat/completions"
   ```
3. Run the assistant:
   ```bash
   python app.py
   ```

#### With local server in the same process:

If running everything on the same (super)machine:
```bash
python app_with_server.py --start-server --model-path /path/to/your/model.gguf
```

## API Compatibility

The local server implements the OpenAI-compatible API endpoint:
- `POST /v1/chat/completions`

This means it can work with any application expecting the OpenAI API format.

## Configuration

Update `config.py` to set your local AI server URL:

```python
LOCAL_AI_URL = "http://0.0.0.0:8001/v1/chat/completions"  # Default local server
# or
LOCAL_AI_URL = "http://[PHONE_IP]:8000/v1/chat/completions"  # Your Django server
```

## Troubleshooting

1. **Connection refused**: Make sure the server is running and the IP/Port is correct
2. **Model loading errors**: Ensure you have enough memory and the model file path is correct
3. **Slow responses**: Consider using a smaller model or a quantized version

## Model Recommendations for Mobile

For mobile devices, consider using smaller models like:
- TinyLlama
- Phi-2
- LLaMA models quantized to 4-bit (Q4, Q5) like Qwen2.5-1.5B-Q4 or Llama-3B-Q4
- Mistral models in GGUF format

These models will run more efficiently on mobile hardware while still providing good responses.