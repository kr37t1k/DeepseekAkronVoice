# Enhanced Voice and Llama-cpp Features

This document describes the enhanced features added to provide alternative voice engines and improved error handling for llama-cpp.

## Voice Engine Alternatives

The enhanced voice system now supports multiple offline voice engines:

### 1. pyttsx3 (Default)
- Cross-platform text-to-speech
- Supports multiple voices based on system availability
- Language detection for English and Russian

### 2. espeak
- Lightweight, fast text-to-speech engine
- Good for basic TTS needs
- Installation: `pip install py-espeak`

### 3. speech-dispatcher (spd)
- Advanced speech output system
- Supports multiple speech synthesizers
- Installation: `pip install speechd`

### 4. Silero TTS
- Neural text-to-speech engine
- High-quality voice synthesis
- Installation: `pip install torch silero`

## Llama-cpp Error Handling Improvements

### Enhanced Model Loading
- Retry mechanism with configurable attempts (`MAX_RETRIES` in config)
- Fallback initialization with minimal settings
- Thread-safe model loading

### Enhanced Generation
- Multiple retry attempts for generation failures
- Parameter adjustment for fallback attempts
- Safe fallback responses when all attempts fail

### Health Checks
- Built-in model health verification
- Test generation to verify model functionality

## Configuration Options

### Voice Settings (config.py)
```python
VOICE_ENGINE = "pyttsx3"  # silero, pyttsx3, espeak, spd
VOICE_RATE = 200          # Speech rate
VOICE_VOLUME = 0.7        # Volume level (0.0 to 1.0)
VOICE_PITCH = 50          # Pitch level (0 to 100, if supported)
```

### Llama-cpp Settings (config.py)
```python
CONNECTION_TIMEOUT = 120  # Timeout for connections in seconds
MAX_RETRIES = 3           # Number of retry attempts for failed requests
```

## Usage Examples

### Switching Voice Engines
```python
from voice_enhanced import EnhancedVoice

voice = EnhancedVoice()
print(voice.get_available_engines())  # List available engines
voice.set_engine("espeak")            # Switch to espeak engine
voice.speak("Hello, this is espeak!")
```

### Enhanced Chat with Error Handling
```python
from local_chat_enhanced import EnhancedLocalChat

chat = EnhancedLocalChat()
response = chat.chat("Hello, how are you?")
print(f"Response: {response}")

# Health check
health = chat.health_check()
print(f"Model health: {health}")
```

### Command-line Voice Switching
In the enhanced app, you can say commands like:
- "switch voice to espeak" - changes the voice engine
- "health" - checks model status
- "status" - checks model status

## Installation

To install all required dependencies:
```bash
pip install -r requirements.txt
```

For specific engines:
- For espeak: `pip install py-espeak`
- For speech-dispatcher: `pip install speechd`
- For Silero: `pip install torch silero`

## Benefits

1. **Multiple Voice Options**: No dependency on a single TTS engine
2. **Better Error Handling**: Automatic retries and fallbacks for model loading and generation
3. **Runtime Engine Switching**: Change voice engines without restarting the application
4. **Language Detection**: Automatic voice selection based on text language
5. **Robustness**: Improved stability with comprehensive error handling