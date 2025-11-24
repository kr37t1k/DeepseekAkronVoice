# DeepSeek API
# The deepseek-chat will work if you had to pay for it on their website platform.deepseek.com.
# DEEPSEEK_API_URL = "https://api.deepseek.com"
# DEEPSEEK_API_KEY = "your_api_key_here"
HTTP_METHOD = "POST: /v1/chat/completions"

# Local AI Server Configuration
LOCAL_AI_URL = "http://0.0.0.0:8001/v1/chat/completions"  # Your local AI server URL
USER_LANGUAGE = "ru"  # en, ru, de, fr

# Connection settings
CONNECTION_TIMEOUT = 120  # Timeout for connections in seconds
MAX_RETRIES = 3          # Number of retry attempts for failed requests

# Engine
# You also need to install silero-tts from kr37t1k/stts-python where you can find releases!
VOICE_ENGINE = "silero"  # silero, pyttsx3, espeak, spd - espeak is most compatible with Termux

# Additional voice settings
VOICE_RATE = 200          # Speech rate
VOICE_VOLUME = 0.7        # Volume level (0.0 to 1.0)
VOICE_PITCH = 50          # Pitch level (0 to 100, if supported by engine)

# Vosk
# VOSK_MODEL_PATH = "./en-us-0.22-lgraph"
VOSK_MODEL_PATH = "./small-ru-0.22"
