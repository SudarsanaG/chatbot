"""
Test script for the web-based chatbot UI
"""

import requests
import json
import time

def test_web_ui():
    """Test the web UI endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing RagaAI Medical Scheduling Agent Web UI")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the server is running with: python chatbot_ui.py")
        return False
    
    # Test main page
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            if "RagaAI Medical Scheduling Agent" in response.text:
                print("✅ Chat interface is present")
            else:
                print("❌ Chat interface not found")
        else:
            print(f"❌ Main page failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot load main page: {e}")
        return False
    
    print("\n🎉 Web UI is working correctly!")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("💬 You can now chat with the AI agent!")
    
    return True

if __name__ == "__main__":
    test_web_ui()

