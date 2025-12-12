#!/usr/bin/env python3
"""
Script to download a small test model for the enhanced servers
This downloads a small model that works well for testing purposes
"""

import os
import requests
from pathlib import Path
import argparse

def download_file(url, filename, chunk_size=8192):
    """Download a file with progress indication"""
    print(f"📥 Downloading {filename}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0
    
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
                downloaded_size += len(chunk)
                
                if total_size > 0:
                    percent = (downloaded_size / total_size) * 100
                    print(f"\rProgress: {percent:.1f}% ({downloaded_size:,} / {total_size:,} bytes)", end='', flush=True)
    
    if total_size > 0:
        print()  # New line after progress
    
    print(f"✅ Downloaded {filename} successfully!")

def main():
    parser = argparse.ArgumentParser(description='Download a small test model for enhanced servers')
    parser.add_argument('--model-url', type=str, 
                       default='https://huggingface.co/Qwen/Qwen2-0.5B-Instruct-GGUF/resolve/main/qwen2-0.5b-instruct-q4_k_m.gguf',
                       help='URL to the GGUF model file')
    parser.add_argument('--output-dir', type=str, default='./models',
                       help='Directory to save the model (default: ./models)')
    parser.add_argument('--filename', type=str, default='qwen2-0.5b-instruct-q4_k_m.gguf',
                       help='Filename for the model (default: qwen2-0.5b-instruct-q4_k_m.gguf)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / args.filename
    
    print(f"🎯 Downloading test model...")
    print(f"📦 Model: {args.filename}")
    print(f"📍 Destination: {output_path}")
    print(f"🔗 Source: {args.model_url}")
    
    if output_path.exists():
        print(f"⚠️  File {output_path} already exists. Skipping download.")
        return
    
    try:
        download_file(args.model_url, output_path)
        print(f"🎉 Model downloaded successfully!")
        print(f"💡 You can now run the server with: python unified_server_launcher.py --model-path {output_path}")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())