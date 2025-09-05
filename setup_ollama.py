#!/usr/bin/env python3
"""
Setup script for Ollama (Free Local LLM)
"""

import subprocess
import sys
import os
import requests
import time

def check_ollama_installed():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama is not installed")
            return False
    except FileNotFoundError:
        print("❌ Ollama is not installed")
        return False

def install_ollama():
    """Install Ollama"""
    print("📥 Installing Ollama...")
    print("Please follow these steps:")
    print("1. Go to: https://ollama.ai/download")
    print("2. Download Ollama for Windows")
    print("3. Run the installer")
    print("4. Restart your terminal")
    print("\nAfter installation, run this script again.")
    
    input("Press Enter after you've installed Ollama...")
    return check_ollama_installed()

def download_model(model_name="llama3.1:8b"):
    """Download a model"""
    print(f"📦 Downloading {model_name}...")
    print("This may take a few minutes depending on your internet speed...")
    
    try:
        result = subprocess.run(['ollama', 'pull', model_name], 
                              capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print(f"✅ {model_name} downloaded successfully!")
            return True
        else:
            print(f"❌ Error downloading {model_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Download timed out. Please try again.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model(model_name="llama3.1:8b"):
    """Test the model"""
    print(f"🧪 Testing {model_name}...")
    
    try:
        result = subprocess.run(['ollama', 'run', model_name, 'Hello, how are you?'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Model test successful!")
            print(f"Response: {result.stdout[:100]}...")
            return True
        else:
            print(f"❌ Model test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Model test timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main setup function"""
    print("🆓 Setting up Free Local LLM with Ollama")
    print("=" * 50)
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        if not install_ollama():
            print("❌ Setup failed. Please install Ollama manually.")
            return False
    
    # Choose model
    print("\n🤖 Available Models:")
    print("1. llama3.1:8b (Recommended - 4.7GB)")
    print("2. mistral:7b (Alternative - 4.1GB)")
    print("3. codellama:7b (For technical tasks - 3.8GB)")
    
    choice = input("\nChoose a model (1-3) or press Enter for default (llama3.1:8b): ").strip()
    
    model_map = {
        "1": "llama3.1:8b",
        "2": "mistral:7b", 
        "3": "codellama:7b"
    }
    
    model_name = model_map.get(choice, "llama3.1:8b")
    
    # Download model
    if not download_model(model_name):
        print("❌ Model download failed")
        return False
    
    # Test model
    if not test_model(model_name):
        print("❌ Model test failed")
        return False
    
    print(f"\n🎉 Setup Complete!")
    print(f"✅ Ollama is running with {model_name}")
    print(f"✅ You can now use the free LLM in your application")
    print(f"\n📝 To use in your app, set: OLLAMA_MODEL={model_name}")
    
    return True

if __name__ == "__main__":
    main()
