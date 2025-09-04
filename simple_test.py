"""
Simple Test Script - No Streamlit Required
Tests the core agent functionality
"""

from src.agent import MedicalSchedulingAgent, ConversationState

def test_complete_flow():
    """Test a complete appointment booking flow"""
    print("🧪 Testing Complete Appointment Flow")
    print("=" * 50)
    
    agent = MedicalSchedulingAgent()
    
    # Test messages for a complete flow
    test_messages = [
        "Hi, I'd like to book an appointment",
        "My name is Sarah",
        "My DOB is 03/22/1985", 
        "My email is sarah@example.com",
        "My phone is 555-123-4567",
        "I'd like to see Dr. Michael Chen",
        "I'll take slot 1",
        "My insurance is Aetna",
        "My member ID is AET987654321",
        "My group number is GRP456"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nStep {i}: {message}")
        response = agent.process_message(message)
        print(f"AI: {response}")
        print(f"State: {agent.conversation_state.value}")
        
        if agent.conversation_state == ConversationState.COMPLETED:
            print("\n🎉 SUCCESS! Appointment booking completed!")
            break
    
    # Print final summary
    if agent.current_appointment:
        appointment = agent.current_appointment
        patient = appointment.patient
        
        print(f"\n📋 Final Appointment Details:")
        print(f"Patient: {patient.first_name} {patient.last_name}")
        print(f"Type: {patient.patient_type}")
        print(f"Doctor: {appointment.doctor}")
        print(f"Date: {appointment.date}")
        print(f"Time: {appointment.time}")
        print(f"Duration: {appointment.duration} minutes")
        
        if appointment.insurance:
            print(f"Insurance: {appointment.insurance.carrier}")
            print(f"Member ID: {appointment.insurance.member_id}")
            print(f"Group: {appointment.insurance.group_number}")

def test_data_loading():
    """Test data loading functionality"""
    print("\n📊 Testing Data Loading")
    print("=" * 30)
    
    try:
        import pandas as pd
        
        # Test patients
        patients_df = pd.read_csv("data/patients.csv")
        print(f"✅ Loaded {len(patients_df)} patients")
        print(f"   - New: {len(patients_df[patients_df['PatientType'] == 'New'])}")
        print(f"   - Returning: {len(patients_df[patients_df['PatientType'] == 'Returning'])}")
        
        # Test appointments
        appointments_df = pd.read_excel("data/appointments.xlsx")
        print(f"✅ Loaded {len(appointments_df)} appointments")
        
        # Test schedules
        try:
            schedules_df = pd.read_excel("data/schedules.xlsx")
        except PermissionError:
            schedules_df = pd.read_excel("data/schedules_new.xlsx")
        
        print(f"✅ Loaded {len(schedules_df)} schedule entries")
        print(f"   - Available slots: {len(schedules_df[schedules_df['Available'] == 'Yes'])}")
        print(f"   - Doctors: {len(schedules_df['Doctor'].unique())}")
        
        # Show available doctors
        doctors = schedules_df['Doctor'].unique()
        print(f"   - Available doctors: {', '.join(doctors)}")
        
    except Exception as e:
        print(f"❌ Data loading error: {str(e)}")

def test_entity_extraction():
    """Test NLP entity extraction"""
    print("\n🧠 Testing Entity Extraction")
    print("=" * 35)
    
    agent = MedicalSchedulingAgent()
    
    test_inputs = [
        "My name is John Smith",
        "I was born on 01/15/1990",
        "My email is john@example.com",
        "Call me at 555-123-4567",
        "I want to see Dr. Sarah Johnson"
    ]
    
    for test_input in test_inputs:
        entities = agent._extract_entities(test_input)
        print(f"Input: {test_input}")
        print(f"Entities: {entities}")
        print()

if __name__ == "__main__":
    print("🏥 RagaAI Medical Scheduling Agent - Simple Test")
    print("=" * 60)
    
    # Test data loading
    test_data_loading()
    
    # Test entity extraction
    test_entity_extraction()
    
    # Test complete flow
    test_complete_flow()
    
    print("\n✅ All tests completed!")
    print("\nTo run interactive testing, use: python interactive_test.py")

