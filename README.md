# Voice Assistant with Local AI

Speech-to-text tool for talking with a local AI assistant. Now supports running AI models locally on your device instead of using external APIs.

## Features
- Voice input using Vosk speech recognition
- Integration with local AI server for AI responses (no API key needed)
- Text-to-speech output with multiple engine options (pyttsx3, espeak, speech-dispatcher, Silero)
- Language detection for English and Russian
- Enhanced error handling for robust operation
- Runtime voice engine switching
- Support for running on mobile devices
- OpenAI-compatible API interface
- Model health checks and automatic fallbacks

## Setup

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Download a Vosk model for your preferred language from https://alphacephei.com/vosk/models and extract it to the appropriate directory (update VOSK_MODEL_PATH in config.py if needed).

3. Configure your local AI server URL in `config.py`:
```python
LOCAL_AI_URL = "http://0.0.0.0:8001/v1/chat/completions"  # Your local server
```

## Usage

### Option 1: Connect to existing local server
```bash
python app.py
```

### Option 2: Run with integrated server (if running locally)
```bash
python app_with_server.py --start-server --model-path /path/to/your/model.gguf
```

### Option 3: Run the server separately (for mobile)
```bash
python run_llama_server.py --model-path /path/to/your/model.gguf --host 0.0.0.0 --port 8001
```

## Configuration

Edit `config.py` to customize:
- Local AI server URL
- Vosk model path
- Voice settings

For detailed setup instructions, see LOCAL_AI_SETUP.md
