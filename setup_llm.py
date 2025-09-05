"""
Setup script for LLM integration
Helps users configure OpenAI API key and test the LLM agent
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment variables for LLM integration"""
    
    print("🤖 Setting up LLM Integration for RagaAI Medical Scheduling Agent")
    print("=" * 60)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("# OpenAI Configuration\n")
            f.write("OPENAI_API_KEY=your-openai-api-key-here\n\n")
            f.write("# Email Configuration (Optional)\n")
            f.write("SMTP_SERVER=smtp.gmail.com\n")
            f.write("SMTP_PORT=587\n")
            f.write("EMAIL_ADDRESS=noreply@ragaai-medical.com\n")
            f.write("EMAIL_PASSWORD=your-app-password\n\n")
            f.write("# SMS Configuration (Optional - Twilio)\n")
            f.write("TWILIO_ACCOUNT_SID=your-account-sid\n")
            f.write("TWILIO_AUTH_TOKEN=your-auth-token\n")
            f.write("TWILIO_FROM_NUMBER=+1234567890\n\n")
            f.write("# Application Configuration\n")
            f.write("DEBUG=True\n")
            f.write("LOG_LEVEL=INFO\n")
        print("✅ .env file created!")
    else:
        print("✅ .env file already exists")
    
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("\n🔑 OpenAI API Key Setup")
        print("To use the LLM features, you need an OpenAI API key.")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Copy the key and set it as an environment variable:")
        print("   - Windows: set OPENAI_API_KEY=your-key-here")
        print("   - Linux/Mac: export OPENAI_API_KEY=your-key-here")
        print("   - Or add it to your .env file")
        print("\n⚠️  Without an API key, the system will fall back to rule-based processing.")
    else:
        print(f"✅ OpenAI API key found: {api_key[:8]}...")
    
    print("\n📦 Installing/Updating Dependencies...")
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    return True

def test_llm_integration():
    """Test the LLM integration"""
    
    print("\n🧪 Testing LLM Integration...")
    
    try:
        from src.llm_agent import LLMMedicalSchedulingAgent
        
        # Test agent initialization
        agent = LLMMedicalSchedulingAgent()
        print("✅ LLM Agent initialized successfully!")
        
        # Test basic conversation
        response = agent.process_message("Hello, I'd like to book an appointment")
        print(f"✅ Test conversation successful!")
        print(f"🤖 Agent response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM integration test failed: {e}")
        print("💡 Make sure you have set your OPENAI_API_KEY environment variable")
        return False

def main():
    """Main setup function"""
    
    print("🚀 RagaAI Medical Scheduling Agent - LLM Setup")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Setup failed. Please check the errors above.")
        return
    
    # Test LLM integration
    if test_llm_integration():
        print("\n🎉 LLM Integration Setup Complete!")
        print("\n📋 Next Steps:")
        print("1. Make sure your OPENAI_API_KEY is set")
        print("2. Run: python chatbot_ui.py")
        print("3. Open: http://localhost:8000")
        print("\n✨ Your medical scheduling agent now has LLM-powered natural language understanding!")
    else:
        print("\n⚠️  LLM integration test failed, but setup is complete.")
        print("The system will work with rule-based processing until you configure the API key.")

if __name__ == "__main__":
    main()
