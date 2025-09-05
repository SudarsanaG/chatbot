"""
Simple demo of the Multi-Agent Medical Scheduling System
"""

from src.multi_agent_system import MultiAgentMedicalSchedulingSystem

def main():
    print("🏥 Multi-Agent Medical Scheduling System Demo")
    print("=" * 50)
    
    # Create system
    system = MultiAgentMedicalSchedulingSystem()
    
    # Start conversation
    print("\n🤖 Starting conversation...")
    response = system.start_new_session()
    print(f"Assistant: {response}")
    
    # Test a few messages
    messages = [
        "Hi, I want to book an appointment",
        "My name is Sarah Johnson", 
        "My DOB is 03/20/1990",
        "My phone is 555-987-6543",
        "My email is sarah.johnson@email.com"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n--- Step {i} ---")
        print(f"User: {msg}")
        response = system.process_message(msg)
        print(f"Assistant: {response[:100]}...")
        
        # Show current state
        state = system.get_conversation_state()
        print(f"State: {state}")
    
    print("\n✅ Demo completed!")
    print("\n🌐 The web interface should be running at: http://localhost:8501")
    print("You can now interact with the multi-agent system through the web UI!")

if __name__ == "__main__":
    main()
