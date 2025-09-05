"""
Test script for the Multi-Agent Medical Scheduling System
Demonstrates the new Gemini-powered multi-agent architecture
"""

from src.multi_agent_system import MultiAgentMedicalSchedulingSystem
import time

def test_multi_agent_system():
    """Test the multi-agent system with a sample conversation"""
    
    print("🏥 Testing Multi-Agent Medical Scheduling System")
    print("=" * 60)
    
    # Create the system
    system = MultiAgentMedicalSchedulingSystem()
    
    # Start a new session
    print("\n🤖 Starting new session...")
    response = system.start_new_session("test_session_001")
    print(f"Assistant: {response}")
    
    # Test conversation flow
    test_conversation = [
        "Hi, I'd like to book an appointment",
        "My name is John Smith",
        "My date of birth is 01/15/1985",
        "My phone number is 555-123-4567",
        "My email is john.smith@email.com",
        "I'd like to see Dr. Johnson",
        "I'll take slot 1",
        "My insurance is Blue Cross, member ID 123456789"
    ]
    
    print(f"\n📋 System Status: {system.get_system_status()['conversation_state']}")
    
    for i, message in enumerate(test_conversation, 1):
        print(f"\n--- Step {i} ---")
        print(f"User: {message}")
        
        # Process message
        response = system.process_message(message)
        print(f"Assistant: {response}")
        
        # Show current state
        status = system.get_system_status()
        print(f"State: {status['conversation_state']}")
        
        # Show patient info if available
        patient_info = system.get_patient_info()
        if patient_info.get('first_name'):
            print(f"Patient: {patient_info['first_name']} {patient_info.get('last_name', '')}")
        
        # Show appointment info if available
        appointment_info = system.get_appointment_info()
        if appointment_info:
            print(f"Appointment: {appointment_info.get('doctor', 'N/A')} - {appointment_info.get('date', 'N/A')} at {appointment_info.get('time', 'N/A')}")
        
        # Small delay for readability
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    
    # Final status
    final_status = system.get_system_status()
    print(f"\n📊 Final Status:")
    print(f"   State: {final_status['conversation_state']}")
    print(f"   LLM Provider: {final_status['llm_provider']}")
    print(f"   Patient: {final_status['patient_info']['first_name']} {final_status['patient_info']['last_name']}")
    if final_status['appointment_info']:
        print(f"   Appointment: {final_status['appointment_info']['doctor']} on {final_status['appointment_info']['date']}")
    else:
        print("   Appointment: Not completed")

def test_individual_agents():
    """Test individual agents separately"""
    
    print("\n🔧 Testing Individual Agents")
    print("=" * 40)
    
    from src.gemini_client import GeminiClient
    from src.information_collector_agent import InformationCollectorAgent
    from src.scheduling_agent import SchedulingAgent
    from src.patient_management_agent import PatientManagementAgent
    import pandas as pd
    
    # Initialize Gemini client
    gemini = GeminiClient()
    
    # Test Gemini client
    print("\n1. Testing Gemini Client...")
    response = gemini.generate_content("Hello, how are you?")
    print(f"   Gemini Response: {response.content[:100]}...")
    
    # Test entity extraction
    print("\n2. Testing Entity Extraction...")
    entities = gemini.extract_entities("My name is John Smith, DOB 01/15/1985, phone 555-123-4567")
    print(f"   Extracted Entities: {entities}")
    
    # Test information collector
    print("\n3. Testing Information Collector...")
    info_collector = InformationCollectorAgent(gemini)
    result = info_collector.process_greeting("Hi, I'm John")
    print(f"   Collection Result: {result.message}")
    
    # Test scheduling agent (with dummy data)
    print("\n4. Testing Scheduling Agent...")
    dummy_schedules = pd.DataFrame({
        'Doctor': ['Dr. Johnson', 'Dr. Smith'],
        'Date': ['2024-01-15', '2024-01-16'],
        'Time': ['09:00', '10:00'],
        'Available': ['Yes', 'Yes']
    })
    scheduler = SchedulingAgent(gemini, dummy_schedules)
    print(f"   Available Doctors: {scheduler.available_doctors}")
    
    # Test patient management
    print("\n5. Testing Patient Management...")
    dummy_patients = pd.DataFrame({
        'PatientID': [1, 2],
        'FirstName': ['John', 'Jane'],
        'LastName': ['Smith', 'Doe'],
        'DOB': ['1985-01-15', '1990-05-20'],
        'Phone': ['555-123-4567', '555-987-6543'],
        'Email': ['john@email.com', 'jane@email.com'],
        'PatientType': ['New', 'Returning']
    })
    patient_manager = PatientManagementAgent(gemini, dummy_patients)
    stats = patient_manager.get_patient_statistics()
    print(f"   Patient Statistics: {stats}")

if __name__ == "__main__":
    try:
        # Test the full multi-agent system
        test_multi_agent_system()
        
        # Test individual agents
        test_individual_agents()
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
