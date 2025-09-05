#!/usr/bin/env python3
"""
Test script for Ollama-based LLM agent
"""

import os
import sys

def test_ollama_connection():
    """Test if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running with {len(models)} models")
            for model in models:
                print(f"   - {model['name']}")
            return True
        else:
            print("❌ Ollama is not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False

def test_ollama_agent():
    """Test the Ollama agent"""
    try:
        print("🤖 Testing Ollama Medical Scheduling Agent...")
        
        from src.ollama_agent import OllamaMedicalSchedulingAgent
        
        # Initialize agent
        agent = OllamaMedicalSchedulingAgent()
        print("✅ Agent initialized successfully")
        
        # Test basic conversation
        response = agent.process_message("Hello, I'd like to book an appointment")
        print(f"✅ Agent response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

def main():
    """Main test function"""
    print("🆓 Testing Free Local LLM (Ollama)")
    print("=" * 40)
    
    # Test Ollama connection
    if not test_ollama_connection():
        print("\n📝 To set up Ollama:")
        print("1. Run: python setup_ollama.py")
        print("2. Or install manually from: https://ollama.ai/download")
        return False
    
    # Test agent
    if test_ollama_agent():
        print("\n🎉 Ollama Agent is working perfectly!")
        print("✅ You can now run: python chatbot_ui.py")
        print("✅ The application will use the free local LLM")
        return True
    else:
        print("\n❌ Agent test failed")
        return False

if __name__ == "__main__":
    main()
