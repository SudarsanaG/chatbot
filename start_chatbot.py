"""
Startup script for RagaAI Medical Scheduling Agent
"""

import subprocess
import sys
import os
import webbrowser
import time
import threading

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pandas
        import openpyxl
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def initialize_data():
    """Initialize synthetic data if needed"""
    if not os.path.exists("data/patients.csv"):
        print("📊 Initializing synthetic data...")
        try:
            from src.data_generator import MedicalDataGenerator
            generator = MedicalDataGenerator()
            generator.create_data_files()
            print("✅ Data initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize data: {e}")
            return False
    else:
        print("✅ Data files already exist")
    return True

def open_browser():
    """Open browser after a short delay"""
    time.sleep(3)
    webbrowser.open("http://localhost:8000")

def main():
    """Main startup function"""
    print("🏥 RagaAI Medical Scheduling Agent - Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Initialize data
    if not initialize_data():
        return
    
    print("\n🚀 Starting the chatbot web interface...")
    print("📱 The chatbot will open in your browser at: http://localhost:8000")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the FastAPI server
    try:
        import uvicorn
        uvicorn.run(
            "chatbot_ui:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()

