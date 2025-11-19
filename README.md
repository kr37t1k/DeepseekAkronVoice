# DeepseekAkronVoice
Speech-to-text tool for talking with Deepseek AI assistant.

## Features
- Voice input using Vosk speech recognition
- Integration with DeepSeek API for AI responses
- Text-to-speech output using pyttsx3
- Russian language support

## Setup

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Download a Vosk model for Russian language from https://alphacephei.com/vosk/models and extract it to `vosk-model-small-ru` directory.

3. Set your DeepSeek API key in `config.py`:
```python
DEEPSEEK_API_KEY = "your_actual_api_key_here"
```

## Usage
```bash
python app.py
```

## Configuration
Edit `config.py` to customize:
- API key and URL
- Vosk model path
- Voice settings
