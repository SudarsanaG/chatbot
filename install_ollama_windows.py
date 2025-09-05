#!/usr/bin/env python3
"""
Ollama Installation Script for Windows
This script will guide you through installing Ollama and setting up a free LLM
"""

import subprocess
import sys
import requests
import time
import os

def print_header():
    print("🆓 Ollama Setup for Windows")
    print("=" * 50)
    print("This will install Ollama and set up a free local LLM")
    print()

def check_ollama_installed():
    """Check if Ollama is already installed"""
    try:
        result = subprocess.run(['ollama', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Ollama is already installed!")
            print(f"   Version: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False

def install_ollama():
    """Install Ollama on Windows"""
    print("📥 Installing Ollama...")
    print("   This will download and install Ollama from https://ollama.ai")
    print()
    
    # Check if we're on Windows
    if os.name != 'nt':
        print("❌ This script is for Windows only")
        return False
    
    print("🔗 Please follow these steps:")
    print("   1. Go to: https://ollama.ai/download")
    print("   2. Download the Windows installer")
    print("   3. Run the installer")
    print("   4. Restart your terminal/command prompt")
    print()
    
    input("Press Enter after you've installed Ollama...")
    
    # Test if installation worked
    if check_ollama_installed():
        return True
    else:
        print("❌ Ollama installation not detected. Please restart your terminal and try again.")
        return False

def check_ollama_running():
    """Check if Ollama service is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running!")
            return True
    except:
        pass
    return False

def start_ollama():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    try:
        # Start Ollama in background
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for service to start
        print("   Waiting for Ollama to start...")
        for i in range(10):
            time.sleep(2)
            if check_ollama_running():
                return True
            print(f"   Attempt {i+1}/10...")
        
        print("❌ Ollama service failed to start")
        return False
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False

def download_model():
    """Download a free LLM model"""
    print("📦 Downloading free LLM model...")
    print("   Available models:")
    print("   1. llama3.1:8b (4.7GB) - Best for conversation")
    print("   2. mistral:7b (4.1GB) - Alternative option")
    print()
    
    choice = input("Choose model (1 or 2): ").strip()
    
    if choice == "1":
        model = "llama3.1:8b"
    elif choice == "2":
        model = "mistral:7b"
    else:
        print("Invalid choice, defaulting to llama3.1:8b")
        model = "llama3.1:8b"
    
    print(f"📥 Downloading {model}...")
    print("   This may take several minutes depending on your internet speed...")
    
    try:
        result = subprocess.run(['ollama', 'pull', model], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Successfully downloaded {model}!")
            return True
        else:
            print(f"❌ Error downloading model: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

def test_ollama():
    """Test Ollama with a simple query"""
    print("🧪 Testing Ollama...")
    try:
        result = subprocess.run(['ollama', 'run', 'llama3.1:8b', 'Hello, how are you?'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Ollama is working correctly!")
            print(f"   Response: {result.stdout.strip()[:100]}...")
            return True
        else:
            print(f"❌ Ollama test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Ollama test timed out (this is normal for first run)")
        return True
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

def main():
    print_header()
    
    # Step 1: Check if Ollama is installed
    if not check_ollama_installed():
        if not install_ollama():
            return False
    
    # Step 2: Check if Ollama service is running
    if not check_ollama_running():
        if not start_ollama():
            return False
    
    # Step 3: Download a model
    if not download_model():
        return False
    
    # Step 4: Test Ollama
    if not test_ollama():
        return False
    
    print()
    print("🎉 Ollama setup complete!")
    print("   You can now run your medical scheduling agent with free LLM!")
    print()
    print("🚀 To start your application:")
    print("   venv/Scripts/python.exe chatbot_ui.py")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("❌ Setup failed. Please check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
