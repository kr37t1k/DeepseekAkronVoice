# Enhanced Voice Assistant for Termux

This enhanced version of the voice assistant is specifically designed to work on Termux (Android) with improved offline TTS capabilities.

## 🚀 Key Features

- **Termux-Compatible TTS**: Uses espeak which works well on mobile devices
- **Robust Fallback System**: Multiple TTS methods with graceful degradation
- **Audio-Optional Operation**: Works in text mode when audio components aren't available
- **Offline Functionality**: Speech recognition and TTS work offline
- **Enhanced Error Handling**: Gracefully handles missing dependencies

## 📱 Installation in Termux

### 1. Install Termux
- Download from F-Droid (recommended) or Google Play Store

### 2. Set up the environment
```bash
# Update packages
pkg update && pkg upgrade

# Install required system packages
pkg install python espeak termux-api git

# Clone this repository (if not already done)
git clone <repository-url>  # or copy files to your device
cd <repository-directory>
```

### 3. Install Python requirements
```bash
pip install -r requirements_termux.txt
```

### 4. Run the setup script
```bash
bash setup_termux.sh
```

## 🎯 Running the Enhanced App

### Basic usage (text mode):
```bash
python app_with_server_enhanced.py
```

### With local AI server:
```bash
python app_with_server_enhanced.py --start-server --model-path /path/to/your/model.gguf
```

## ⚡ TTS Configuration

The app will attempt multiple TTS methods in this order:
1. **espeak** - Primary method, works offline
2. **termux-tts-speak** - Termux-specific TTS (if Termux:API is installed)
3. **Text output** - As a final fallback

## 🔧 Configuration Options

Edit `config.py` to adjust:
- `USER_LANGUAGE`: Set to "en" or "ru" for language-specific voices
- `VOICE_RATE`: Speech rate (default: 200)
- `VOICE_VOLUME`: Volume level (0.0 to 1.0, default: 0.7)
- `VOSK_MODEL_PATH`: Path to your Vosk language model

## 🛠️ Troubleshooting

### If audio doesn't work:
- The app will automatically switch to text mode
- You can type your messages instead of speaking

### If TTS doesn't work:
- Check if espeak is installed: `pkg install espeak`
- Install Termux:API app for additional TTS options

### Missing dependencies:
- The app handles missing components gracefully
- Core functionality remains available even with limited dependencies

## 📋 What Works in Termux

✅ Text-based chat with AI  
✅ Offline TTS using espeak  
✅ Local AI server integration  
✅ Fallback to text-only mode  
✅ Basic voice recognition (if vosk is available)  

## 🚫 Limitations

❌ Some heavy packages (TTS, torch) may not install on mobile  
❌ Audio input might be limited depending on device  
❌ Performance may be slower than desktop  

## 💡 Tips for Best Experience

1. Use a lightweight GGUF model for better performance
2. Ensure proper permissions for microphone and audio
3. Install Termux:API for enhanced audio features
4. Start with text mode to verify core functionality first

## 🔄 Updates

This enhanced version includes:
- Improved error handling for missing dependencies
- Multiple TTS fallback options
- Text mode as default when audio unavailable
- Better compatibility with mobile environments
- More robust startup and initialization

Enjoy your offline voice assistant on Android!