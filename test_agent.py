"""
Test script for the Medical Scheduling Agent
"""

from src.agent import MedicalSchedulingAgent, ConversationState
import pandas as pd

def test_agent():
    """Test the AI agent functionality"""
    print("🧪 Testing RagaAI Medical Scheduling Agent")
    print("=" * 50)
    
    # Initialize agent
    agent = MedicalSchedulingAgent()
    
    # Test conversation flow
    test_messages = [
        "Hi, I'd like to book an appointment",
        "My name is John",
        "My DOB is 01/15/1990",
        "I'd like to see Dr. Sarah Johnson",
        "I'll take slot 1",
        "My insurance is Blue Cross Blue Shield",
        "My member ID is BC123456789",
        "My group number is GRP001"
    ]
    
    print(f"Initial state: {agent.conversation_state.value}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"User: {message}")
        response = agent.process_message(message)
        print(f"AI: {response}")
        print(f"State: {agent.conversation_state.value}")
        print("-" * 30)
    
    # Check final state
    if agent.conversation_state == ConversationState.COMPLETED:
        print("✅ Test completed successfully!")
        print(f"Patient: {agent.current_patient.first_name}")
        print(f"Doctor: {agent.current_appointment.doctor}")
        print(f"Date: {agent.current_appointment.date}")
        print(f"Time: {agent.current_appointment.time}")
    else:
        print(f"❌ Test incomplete. Final state: {agent.conversation_state.value}")

def test_data_loading():
    """Test data loading functionality"""
    print("\n📊 Testing Data Loading")
    print("=" * 30)
    
    try:
        # Test patients data
        patients_df = pd.read_csv("data/patients.csv")
        print(f"✅ Loaded {len(patients_df)} patients")
        print(f"   - New patients: {len(patients_df[patients_df['PatientType'] == 'New'])}")
        print(f"   - Returning patients: {len(patients_df[patients_df['PatientType'] == 'Returning'])}")
        
        # Test appointments data
        appointments_df = pd.read_excel("data/appointments.xlsx")
        print(f"✅ Loaded {len(appointments_df)} appointments")
        
        # Test schedules data
        try:
            schedules_df = pd.read_excel("data/schedules.xlsx")
        except PermissionError:
            schedules_df = pd.read_excel("data/schedules_new.xlsx")
        
        print(f"✅ Loaded {len(schedules_df)} schedule entries")
        print(f"   - Available slots: {len(schedules_df[schedules_df['Available'] == 'Yes'])}")
        print(f"   - Doctors: {len(schedules_df['Doctor'].unique())}")
        
    except Exception as e:
        print(f"❌ Data loading error: {str(e)}")

if __name__ == "__main__":
    test_data_loading()
    test_agent()

