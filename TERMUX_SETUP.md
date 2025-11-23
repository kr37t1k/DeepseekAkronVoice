# Termux Setup Guide

This guide will help you set up and run the voice assistant on Termux for Android devices.

## Prerequisites

1. Install Termux from F-Droid (recommended) or Google Play Store
2. Install Termux:API app from F-Droid for additional features (optional)

## Installation Steps

1. **Update Termux packages:**
   ```bash
   pkg update && pkg upgrade
   ```

2. **Install the required system packages:**
   ```bash
   pkg install python espeak termux-api git
   ```

3. **Clone or copy this project to your Termux environment**

4. **Install Python requirements:**
   ```bash
   pip install -r requirements_termux.txt
   ```

5. **Run the setup script:**
   ```bash
   bash setup_termux.sh
   ```

## Running the Enhanced App

To run the enhanced application with Termux-compatible TTS:

```bash
python app_with_server_enhanced.py
```

### Optional: With local server
If you have a GGUF model and want to run a local AI server:

```bash
python app_with_server_enhanced.py --start-server --model-path /path/to/your/model.gguf
```

## Features

- **Enhanced TTS for Termux**: Uses espeak which is more compatible with mobile devices
- **Fallback mechanisms**: If one TTS method fails, it tries alternatives
- **Text mode**: If audio input fails, you can switch to text-based interaction
- **Robust error handling**: Handles missing dependencies gracefully

## Troubleshooting

### Audio Issues
- If you get audio errors, the app will automatically switch to text mode
- Make sure your device has proper audio permissions for Termux

### TTS Not Working
- The app will try multiple TTS methods (espeak, termux-tts-speak, text output)
- If all fail, responses will be displayed as text only

### Missing Dependencies
- The enhanced app has fallbacks for missing packages
- It will notify you which components are available and which aren't

## Configuration

You can modify `config.py` to adjust:
- Language settings
- Voice rate and volume
- Model paths

## Notes

- The app is designed to work even if some components fail
- Speech recognition uses Vosk which works offline
- TTS uses espeak which is lightweight and mobile-friendly
- If you don't have audio input capability, you can still use the text-based mode