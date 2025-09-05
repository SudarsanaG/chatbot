#!/usr/bin/env python3
"""Quick command line test"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from multi_agent_system import MultiAgentMedicalSchedulingSystem
from config import Config

def quick_test():
    """Quick test of the system"""
    
    print("🧪 Quick System Test")
    print("=" * 30)
    
    # Initialize system
    config = Config.get_llm_config()
    system = MultiAgentMedicalSchedulingSystem(config["gemini_api_key"])
    
    # Test messages
    messages = [
        "Hi I would like to make an appointment",
        "Ishanuj Hazarika and 9th July 1999", 
        "7002477633 and ishanuj99@gmail.com",
        "Yes"
    ]
    
    for msg in messages:
        print(f"\n👤 User: {msg}")
        response = system.process_message(msg)
        print(f"🤖 AI: {response}")
        
        # Show state
        status = system.get_system_status()
        print(f"📊 State: {status['conversation_state']}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    quick_test()
