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
VOICE_ENGINE = "pyttsx3"  # silero, pyttsx3, espeak, spd

# Vosk
# VOSK_MODEL_PATH = "./en-us-0.22-lgraph"
VOSK_MODEL_PATH = "./small-ru-0.22"
