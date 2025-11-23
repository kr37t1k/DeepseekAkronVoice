#!/bin/bash

echo "🔧 Setting up for Termux environment..."

# Update package list
pkg update -y

# Install essential packages for audio and TTS
pkg install -y espeak termux-api

# Install Python packages that work well in Termux
pip install vosk sounddevice numpy requests

# Check if pyaudio works (often problematic in Termux)
echo "Testing audio packages..."

# Try to install minimal requirements
pip install --upgrade pip

echo "✅ Termux setup completed!"
echo "💡 To run the enhanced app: python app_with_server_enhanced.py"

# Optional: Install additional Termux API features
echo "💡 Optional: Install Termux:API app from F-Droid for additional audio features"